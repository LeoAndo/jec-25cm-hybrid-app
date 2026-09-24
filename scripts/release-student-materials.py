"""GitHubの変更履歴を準備し、明示された場合だけ学生用教材を公開する。"""

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from urllib.parse import quote


ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
CHECKSUMS = "SHA256SUMS.txt"
# 配布ZIPの名前は版ごとに変わるので、release-metadata.jsonから受け取る。
ASSET_PATTERN = re.compile(r"hybrid-app-student-materials-\d{4}-\d{2}-\d{2}\.zip")
MATERIALS_CONFIG = "config/teaching-materials.json"


def split_unit(name):
    """M01HelloMonaca を ("M01", "HelloMonaca") に分ける。"""
    match = re.match(r"^([MF]\d+)(.*)$", name)
    return (match.group(1), match.group(2)) if match else (name, name)


def load_projects():
    """単元の一覧は config/teaching-materials.json から読む。

    単元をこのスクリプトに直書きすると、単元を足すたびにリリースノートも直すことになり、
    片方だけ直し忘れる。設定を1か所にして、リリーススクリプトは触らずに済むようにしている。
    """
    path = ROOT / MATERIALS_CONFIG
    if not path.is_file():
        raise ValueError(f"設定ファイルがありません：{MATERIALS_CONFIG}")
    return json.loads(path.read_text(encoding="utf-8")).get("projects", [])


def sample_example(projects):
    """リリースノートの「File > Open Folder…」の例に挙げる見本。

    フォルダーを開いて使うのはFlutterの単元の見本だけ（Monacaの見本は取り込み用のURLから取り込む）。
    projects の先頭はMonacaの単元なので、先頭を挙げるとFlutterの案内にMonacaの見本が出てしまう。
    """
    roots = [project["root"] for project in projects if project.get("kind") == "flutter"]
    return f"samples/{roots[0]}" if roots else "samples/<プロジェクト名>"


def unit_list(projects):
    """リリースノートに載せる単元一覧を作る。"""
    lines = []
    for project in projects:
        number, label = split_unit(project["name"])
        lines.append(f"   - `{number} {label}：{project['docs'][0]}`")
    return "\n".join(lines) if lines else "   - （教科書はまだありません）"


def gh(*args, payload=None):
    command = ["gh", *args]
    if payload is not None:
        command.extend(["--input", "-"])
    return subprocess.check_output(
        command, input=json.dumps(payload) if payload is not None else None,
        text=True, cwd=ROOT,
    )


def api(path, payload=None):
    return json.loads(gh("api", path, payload=payload))


def releases(repo):
    pages = json.loads(gh("api", "--paginate", "--slurp", f"repos/{repo}/releases?per_page=100"))
    return [release for page in pages for release in page]


def previous_release(items, version):
    candidates = [
        item for item in items
        if not item["draft"] and not item["prerelease"]
        and item["tag_name"].startswith("materials-") and item["tag_name"] != version
    ]
    return max(candidates, key=lambda item: item["published_at"], default=None)


def summary(text):
    print(text)
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as output:
            output.write(text + "\n")


# 言語の有効・無効は config/i18n.json の distribute だけで決める。
# ここには、同じZIPを開くための短い定型案内を置く。
DOWNLOAD_GUIDANCE = {
    "en": "Download **{asset}** from Assets and extract it. Open `index.html` in your browser, choose English, and start with the setup guide. Classes are taught in Japanese; translations help you understand the textbook.",
    "zh-Hans": "从 Assets 下载 **{asset}** 并解压。在浏览器中打开 `index.html`，选择简体中文，然后从课前准备指南开始。课程使用日语授课，译文用于帮助理解教材。",
    "zh-Hant-HK": "從 Assets 下載 **{asset}** 並解壓縮。在瀏覽器開啟 `index.html`，選擇繁體中文（香港），再從課前準備指南開始。課堂以日語授課，譯文用來協助理解教材。",
    "zh-Hant-TW": "從 Assets 下載 **{asset}** 並解壓縮。在瀏覽器開啟 `index.html`，選擇繁體中文（台灣），再從課前準備指南開始。課程以日語授課，譯文是用來幫助你理解教材。",
    "ko": "Assets에서 **{asset}** 을 내려받아 압축을 풉니다. 브라우저에서 `index.html` 을 열고 한국어를 선택한 뒤, 수업 준비 안내부터 시작하세요. 수업은 일본어로 진행하며, 번역은 교재를 이해하는 데 도움을 주기 위한 것입니다.",
    "my": "Assets မှ **{asset}** ကို ဒေါင်းလုဒ်လုပ်ပြီး ZIP ဖိုင်ကို ဖြည်ပါ။ ဘရောက်ဇာတွင် `index.html` ကိုဖွင့်၍ မြန်မာဘာသာကို ရွေးပြီး သင်တန်းအတွက် ပြင်ဆင်ခြင်းလမ်းညွှန်မှ စတင်ပါ။ သင်တန်းကို ဂျပန်ဘာသာဖြင့် သင်ကြားပြီး ဘာသာပြန်သည် စာအုပ်ကို နားလည်ရန် အထောက်အကူပြုပါသည်။",
    "es": "Descarga **{asset}** desde Assets y descomprímelo. Abre `index.html` en tu navegador, elige Español y empieza por la guía de preparación. Las clases son en japonés; las traducciones te ayudan a entender el libro de texto.",
}
EXCEPTION_MARKER = "<!-- translation-release-exception -->"


def translation_report():
    """生成元と同じカタログを検査し、配布対象だけの進み具合を返す。"""
    spec = importlib.util.spec_from_file_location("release_localize", ROOT / "scripts/localize-student-materials.py")
    localize = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = localize
    spec.loader.exec_module(localize)
    settings = localize.load_settings(ROOT)
    errors = localize.check(settings)
    if errors:
        # 緊急公開でも、構造不正や壊れた訳を公開してはいけない。
        raise ValueError("対訳カタログの検査に失敗しました：\n" + "\n".join(errors))
    return localize.progress(settings, [language["code"] for language in settings.languages if language.get("distribute")])


def missing_translations(report):
    return sum(row["total"] - row["translated"] for item in report for row in item["rows"])


def translation_table(report):
    lines = ["| 言語 | ページ | 未翻訳 |", "| --- | --- | ---: |"]
    for item in report:
        language = item["language"]
        total = sum(row["total"] - row["translated"] for row in item["rows"])
        lines.append(f"| {language['code']}（{language['name']}） | **言語合計** | **{total}** |")
        for row in item["rows"]:
            lines.append(f"| {language['code']}（{language['name']}） | `{row['page']}` | {row['total'] - row['translated']} |")
    if not report:
        return "配布対象の翻訳言語はありません。"
    return "\n".join(lines)


def exception_notes(report):
    if os.environ.get("ALLOW_UNTRANSLATED") != "true":
        return ""
    return (
        f"{EXCEPTION_MARKER}\n## 未翻訳を含む緊急公開\n\n"
        "公開ゲートを解除しています。未翻訳の文は日本語のまま表示されます。\n\n"
        f"未翻訳の合計：**{missing_translations(report)}文**（同じ文が別ページにある場合はページごとに数えます）。\n\n"
        f"{translation_table(report)}\n"
    )


def localized_download_guidance(report, asset):
    lines = []
    for item in report:
        language = item["language"]
        code = language["code"]
        if code not in DOWNLOAD_GUIDANCE:
            raise ValueError(f"公開案内がない配布言語です：{code}")
        lines.extend([f"### {language['name']}", "", DOWNLOAD_GUIDANCE[code].format(asset=asset), ""])
    return "\n".join(lines) + "\n" if lines else ""


def check_translation_gate():
    report = translation_report()
    summary("## 公開前の翻訳確認\n\n" + translation_table(report))
    missing = missing_translations(report)
    if missing and os.environ.get("ALLOW_UNTRANSLATED") != "true":
        raise ValueError(f"配布対象の言語に未翻訳が{missing}文あります。翻訳PRを反映してから公開してください。")
    return report


def prepare(repo, metadata):
    version, revision, asset = metadata["version"], metadata["revision"], metadata["asset"]
    report = translation_report()
    previous = previous_release(releases(repo), version)
    payload = {"tag_name": version, "target_commitish": revision, "configuration_file_path": ".github/release.yml"}
    commit_range = revision
    if previous:
        payload["previous_tag_name"] = previous["tag_name"]
        base = api(f"repos/{repo}/commits/{quote(previous['tag_name'], safe='')}")["sha"]
        # 過去のrunを再実行した場合、最新の配布版より古い変更履歴を作らない。
        subprocess.run(["git", "merge-base", "--is-ancestor", base, revision], cwd=ROOT, check=True)
        commit_range = f"{base}..{revision}"
    generated = api(f"repos/{repo}/releases/generate-notes", payload)["body"]
    commits = subprocess.check_output(
        ["git", "log", "--no-merges", "--format=- %s (%h)", commit_range], cwd=ROOT, text=True,
    ).strip()
    student_notes = os.environ.get("STUDENT_NOTES", "").strip()
    projects = load_projects()
    body = (
        f"# ハイブリッドアプリ開発技法 教材 {version}\n\n"
        "## ダウンロードと開き方\n\n"
        f"1. Assetsの **{asset}** をダウンロードして展開します。\n"
        "2. `docs/common/setup.html` をブラウザで開きます。第1コマにSTEP 1〜3、第7コマにSTEP 4〜7を開始し、第8コマでも確認を続けます。\n"
        "   Flutterのダウンロードも授業時間内に行います。Flutterの初回実行は単元の教科書で行います。\n"
        "3. 授業で使う単元の教科書をブラウザで開きます。\n\n"
        f"{unit_list(projects)}\n\n"
        "4. 完成プロジェクト（先生が作った見本）を含む版には、`samples` フォルダがあります。\n"
        f"   Flutterの単元は、Visual Studio Code の「File > Open Folder…」で `{sample_example(projects)}` のように選ぶだけで開けます。\n"
        "   Monacaの単元は、教科書に載っている取り込み用のURLからMonacaへ取り込みます。\n"
        "   `samples` フォルダの中身は、コードを読み比べるための写しです。\n\n"
        "教材を更新するときは別フォルダに展開し、自分で作ったプロジェクトを上書きしないでください。\n"
        "授業中は先生が指定した版を使ってください。\n\n"
        f"{localized_download_guidance(report, asset)}"
        f"## 学生向けの補足\n\n{student_notes or '対象単元・作業のやり直しの要否は、先生の案内を確認してください。'}\n\n"
        f"## 変更履歴\n\n{generated}\n\n"
        f"<details>\n<summary>コミット一覧（直接mainに入った修正を含む）</summary>\n\n{commits or '追加のコミットはありません。'}\n\n</details>\n\n"
        f"教材の版：`{version}`  \nソース：`{revision}`\n"
    )
    body += exception_notes(report)
    (DIST / "release-notes.md").write_text(body, encoding="utf-8")
    summary(f"## 教材の準備完了\n\n版：`{version}`\n\n`student-materials-ready`で始まる成果物にZIPとリリースノートを保存します。\n\n{body}")


def publish(repo, metadata):
    version, revision, asset = metadata["version"], metadata["revision"], metadata["asset"]
    # 公開処理はActionsのmainからの明示的な手動実行に限定する。
    if os.environ.get("GITHUB_EVENT_NAME") != "workflow_dispatch" or os.environ.get("GITHUB_REF") != "refs/heads/main":
        raise ValueError("公開はmainを選んだRun workflowから実行してください。")
    checksum = (DIST / CHECKSUMS).read_text(encoding="utf-8").strip()
    actual = hashlib.sha256((DIST / asset).read_bytes()).hexdigest()
    if checksum != f"{actual}  {asset}":
        raise ValueError("教材ZIPのチェックサムが一致しません。")

    current = next((item for item in releases(repo) if item["tag_name"] == version), None)
    if current and not current["draft"]:
        # 再実行で公開済みZIPやノートを上書きしない。
        summary(f"公開済みのため変更しません：{current['html_url']}")
        return
    if api(f"repos/{repo}/commits/main")["sha"] != revision:
        raise ValueError("実行開始後にmainが更新されています。mainから新しくRun workflowを実行してください。")
    refs = api(f"repos/{repo}/git/matching-refs/tags/{quote(version, safe='')}")
    if any(ref["ref"] == f"refs/tags/{version}" for ref in refs):
        if api(f"repos/{repo}/commits/{quote(version, safe='')}")["sha"] != revision:
            raise ValueError("同じタグが別のコミットを指しています。公開を中止しました。")
    if current and current["target_commitish"] != revision:
        raise ValueError("既存の下書きが別のコミットを指しています。公開を中止しました。")

    report = check_translation_gate()
    notes = DIST / "release-notes.md"
    # prepare と publish の入力が違っていても、実際の公開判断と件数をノートに残す。
    # 同じrunの再実行で追記を繰り返さない。
    body = notes.read_text(encoding="utf-8").split(EXCEPTION_MARKER, 1)[0].rstrip() + "\n"
    notes.write_text(body + exception_notes(report), encoding="utf-8")
    if current:
        gh("release", "edit", version, "--repo", repo, "--notes-file", str(notes))
    else:
        gh("release", "create", version, "--repo", repo, "--target", revision,
           "--title", f"ハイブリッドアプリ開発技法 教材 {version}", "--draft", "--notes-file", str(notes))
    # 添付が揃ってから公開する。失敗時は下書きに留まり、同じrunの再実行で再開できる。
    gh("release", "upload", version, *(str(DIST / name) for name in (asset, CHECKSUMS)), "--repo", repo, "--clobber")
    if api(f"repos/{repo}/commits/main")["sha"] != revision:
        raise ValueError("実行中にmainが更新されています。下書きの公開を中止しました。mainから新しくRun workflowを実行してください。")
    gh("release", "edit", version, "--repo", repo, "--draft=false", "--latest")
    summary(f"## 学生向けに公開しました\n\nhttps://github.com/{repo}/releases/tag/{version}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("prepare", "publish"))
    args = parser.parse_args()
    try:
        repo = os.environ["GH_REPO"]
        metadata = json.loads((DIST / "release-metadata.json").read_text(encoding="utf-8"))
        revision = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
        if metadata["revision"] != revision:
            raise ValueError("教材の生成元とワークフローのコミットが一致しません。")
        if not ASSET_PATTERN.fullmatch(metadata["asset"]):
            raise ValueError(f"配布ZIPの名前が想定の形式ではありません：{metadata['asset']}")
        {"prepare": prepare, "publish": publish}[args.action](repo, metadata)
    except (KeyError, OSError, ValueError, subprocess.CalledProcessError) as error:
        raise SystemExit(f"リリース処理に失敗しました：{error}") from None


if __name__ == "__main__":
    main()
