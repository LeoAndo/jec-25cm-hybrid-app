"""学生向けのdocs一式と、展開済みの完成プロジェクト（samples）をZIPにまとめる。完成プロジェクトのZIPは再生成する。"""

import argparse
from datetime import datetime, timedelta, timezone
import hashlib
import html
import importlib.util
from html.parser import HTMLParser
import io
import json
from pathlib import Path
import posixpath
import re
import subprocess
import sys
from urllib.parse import unquote, urlsplit
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo


ROOT = Path(__file__).resolve().parents[1]
ASSET_STEM = "hybrid-app-student-materials"
MATERIALS_CONFIG = "config/teaching-materials.json"
EXCLUDED = {".git", ".idea", ".DS_Store", "__pycache__"}


def split_unit(name):
    """M01HelloMonaca を ("M01", "HelloMonaca") に分ける。"""
    match = re.match(r"^([MF]\d+)(.*)$", name)
    return (match.group(1), match.group(2)) if match else (name, name)


def load_projects():
    """単元の一覧は config/teaching-materials.json から読む。

    単元をこのスクリプトに直書きすると、単元を足すたびに配布スクリプトも直すことになり、
    片方だけ直し忘れる。設定を1か所にして、配布スクリプトは触らずに済むようにしている。
    """
    path = ROOT / MATERIALS_CONFIG
    if not path.is_file():
        raise ValueError(f"設定ファイルがありません：{MATERIALS_CONFIG}")
    return json.loads(path.read_text(encoding="utf-8")).get("projects", [])


def archive_targets(projects):
    """完成プロジェクトZIPを作る (プロジェクト, 出力先) の組を、重複なく返す。

    1つのプロジェクトを複数の単元で育てるとき（MonacaのFreeプランはプロジェクトを3個までしか
    持てない）は、複数の単元が同じ root と archive を指すので、そのままでは同じZIPを何度も作ってしまう。
    """
    targets = []
    for project in projects:
        target = (project["root"], project["archive"])
        if target not in targets:
            targets.append(target)
    return targets


def sample_example(projects):
    """はじめに.txt の「File > Open Folder…」の例に挙げる見本。

    フォルダーを開いて使うのはFlutterの単元の見本だけ（Monacaの見本は取り込み用のURLから取り込む）。
    projects の先頭はMonacaの単元なので、先頭を挙げるとFlutterの案内にMonacaの見本が出てしまう。
    """
    roots = [project["root"] for project in projects if project.get("kind") == "flutter"]
    return f"samples/{roots[0]}" if roots else "samples/<プロジェクト名>"


class LocalLinks(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []

    def handle_starttag(self, tag, attrs):
        self.links.extend(value for key, value in attrs if key in {"href", "src"} and value)


def check_links(files):
    """収録したHTMLの相対リンク先が、配布物の中にも存在するか確認する。"""
    for name, data in files.items():
        if not name.endswith(".html"):
            continue
        parser = LocalLinks()
        parser.feed(data.decode("utf-8"))
        for link in parser.links:
            url = urlsplit(link)
            if url.scheme or url.netloc or not url.path:
                continue
            target = posixpath.normpath(posixpath.join(posixpath.dirname(name), unquote(url.path)))
            if target not in files:
                raise ValueError(f"配布物内にリンク先がありません：{name} → {link}")


def add_localized_materials(files):
    """配布対象の言語だけを生成し、本文と導線を静的HTMLとして収録する。"""
    spec = importlib.util.spec_from_file_location("package_localizer", ROOT / "scripts/localize-student-materials.py")
    localizer = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = localizer
    spec.loader.exec_module(localizer)
    settings = localizer.load_settings(ROOT)
    languages = [item for item in settings.languages if item.get("distribute")]
    if not languages:
        return []
    # UI文言の確かめ方と渡し方は、確認用ページ（localize の build）と共通にする。
    ui = {code: localizer.ui_messages(settings, code)
          for code in [settings.source_language, *(item["code"] for item in languages)]}
    for item in languages:
        for key in ("name", "language_label", "translation_notice", "japanese_version", "open_instructions", "start_here"):
            if not isinstance(item.get(key), str) or not item[key].strip():
                raise ValueError(f"config/i18n.json: {item['code']} の {key} がありません")
    # 翻訳でも配布物の境界は同じ。Git未管理の確認用HTMLは生成しない。
    names = sorted(name for name in files if name.endswith(".html"))
    choices = [{"code": "ja", "name": "日本語"}, *languages]
    # 言語名は、どのページに置いても、その言語の書字方向で表示する。dir がないと、
    # 右から左のページに置いた「繁體中文（香港）」の閉じかっこが、名前の反対側（左端）へ回り込む。
    directions = {choice["code"]: settings.direction(choice["code"]) for choice in choices}
    for language in languages:
        for name, text in localizer.localized_pages(
                settings, language["code"], mark_untranslated=True, page_names=names).items():
            files[name] = text.encode("utf-8")
    for source in names:
        for language in choices:
            code = language["code"]
            name = source if code == "ja" else localizer.output_name(source, code, settings.source_root)
            links = []
            for choice in choices:
                target_code = choice["code"]
                label = html.escape(choice["name"])
                if code == target_code:
                    links.append(f'<span lang="{code}" dir="{directions[code]}" aria-current="page">{label}</span>')
                else:
                    target = source if target_code == "ja" else localizer.output_name(source, target_code, settings.source_root)
                    href = html.escape(posixpath.relpath(target, posixpath.dirname(name)), quote=True)
                    links.append(f'<a href="{href}" lang="{target_code}" dir="{directions[target_code]}" '
                                 f'hreflang="{target_code}" data-language-link>{label}</a>')
            label = "言語" if code == "ja" else language["language_label"]
            nav = f'<nav class="language-nav" aria-label="{html.escape(label, quote=True)}">' + " | ".join(links) + "</nav>"
            if code != "ja":
                original = html.escape(posixpath.relpath(source, posixpath.dirname(name)), quote=True)
                nav += ('<aside class="translation-note"><p>' + html.escape(language["translation_notice"])
                        + f'</p><a href="{original}" data-language-link hreflang="ja">'
                        + html.escape(language["japanese_version"]) + '</a></aside>')
            addition = f"\n{nav}\n{localizer.textbook_i18n_script(ui[code])}\n"
            files[name] = localizer.insert_into_body(files[name].decode("utf-8"), addition, name).encode("utf-8")
    # 翻訳された共通資料を入口にする。共通資料がないときは、最初の単元の教科書を入口にする。
    start = "docs/common/setup.html"
    if start not in files:
        projects = load_projects()
        if not projects:
            raise ValueError("配布物の入口にするページがありません。")
        start = projects[0]["docs"][0]
    items = [f'<li lang="ja" dir="ltr"><a href="{start}">日本語 — ここから始める</a></li>']
    for item in languages:
        target = localizer.output_name(start, item["code"], settings.source_root)
        items.append(f'<li lang="{item["code"]}" dir="{directions[item["code"]]}"><a href="{html.escape(target, quote=True)}">'
                     + html.escape(item["name"] + " — " + item["start_here"]) + '</a></li>')
    files["index.html"] = ('<!doctype html>\n<html lang="ja"><head><meta charset="utf-8">'
                           '<meta name="viewport" content="width=device-width, initial-scale=1">'
                           '<title>ハイブリッドアプリ開発技法 / Hybrid App Development — Language / 言語</title>'
                           '<link rel="stylesheet" href="docs/assets/textbook.css"></head>'
                           '<body class="plain"><main><h1>ハイブリッドアプリ開発技法 / Hybrid App Development</h1>'
                           '<p>Language / 言語</p><ul>' + ''.join(items) + '</ul></main></body></html>\n').encode("utf-8")
    return languages


def build(output_dir):
    revision = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    timestamp = subprocess.check_output(["git", "show", "-s", "--format=%ct", "HEAD"], cwd=ROOT, text=True).strip()
    published = datetime.fromtimestamp(int(timestamp), timezone(timedelta(hours=9)))
    version = f"materials-{published:%Y.%m.%d}-{revision[:12]}"
    # 学生のダウンロードフォルダで版を見分けられるよう、版タグと同じ日付を名前に入れる。
    stem = f"{ASSET_STEM}-{published:%Y-%m-%d}"
    asset_name = f"{stem}.zip"

    # リポジトリ内の古いZIPをそのまま配布せず、現在の完成コードを反映する。
    # 作る単元は config/teaching-materials.json の projects から決める。ここに単元を書き足さない。
    projects = load_projects()
    for project_root, output in archive_targets(projects):
        subprocess.run(
            [sys.executable, str(ROOT / "scripts/package-project.py"),
             "--project", project_root, "--output", str(ROOT / output)],
            cwd=ROOT, check=True,
        )
    subprocess.run(
        [sys.executable, str(ROOT / "scripts/check-teaching-materials.py")],
        cwd=ROOT,
        check=True,
    )
    tracked = subprocess.check_output(["git", "ls-files", "-z", "--", "docs"], cwd=ROOT).decode().split("\0")
    files = {}
    for name in sorted(filter(None, tracked)):
        source = ROOT / name
        if EXCLUDED.intersection(Path(name).parts):
            continue
        if source.is_symlink() or not source.resolve().is_relative_to(ROOT / "docs"):
            raise ValueError(f"配布対象にシンボリックリンクは使えません：{name}")
        files[name] = source.read_bytes()
    if projects and projects[0]["docs"][0] not in files:
        # 最初の単元の教科書は、配布物の骨格。ここが抜けているときは作り方を間違えている。
        raise ValueError(f"{split_unit(projects[0]['name'])[1]}の教科書が見つかりません。")
    for project in projects:
        # 教科書を配るのにZIPを配らない、という組み合わせだけを落とす。
        # 教科書をまだ書いていない単元は、ZIPも配らないので対象外。
        if project["docs"][0] in files and project["archive"] not in files:
            raise ValueError(f"{split_unit(project['name'])[1]}の完成プロジェクトが見つかりません。")
    languages = add_localized_materials(files)
    check_links(files)

    # 完成プロジェクトを、展開済みの見本として samples/ にも収録する。Flutterの単元は、学生がダウンロードも
    # 展開もせず、Visual Studio Code の「File > Open Folder…」で選ぶだけになる。Monacaの単元の見本は、
    # 取り込み用のURLから取り込むので、samples/ の中身はコードを読み比べるための写しになる。
    # 中身は配布物に入れるZIPと同じなので、新たにcommitするファイルはない。
    # リンク検査のあとで足すので、検査の対象は教科書と多言語の入口で、samples の中は検査しない。
    executables = set()
    for _, archive_name in archive_targets(projects):
        if archive_name not in files:
            # 教科書をまだ足していない単元。ZIPを配らないので、見本も配らない。
            continue
        with ZipFile(io.BytesIO(files[archive_name])) as sample:
            for item in sample.infolist():
                name = f"samples/{item.filename}"
                files[name] = sample.read(item)
                # 実行権限のあるファイル（シェルスクリプトなど）は、その権限を配布物まで引き継ぐ。
                if (item.external_attr >> 16) & 0o100:
                    executables.add(name)

    metadata = {"version": version, "revision": revision, "asset": asset_name}
    metadata_text = json.dumps(metadata, ensure_ascii=False, indent=2) + "\n"
    files["VERSION.json"] = metadata_text.encode()
    # 単元の一覧は projects から作る。単元を足したときに、ここを直し忘れて案内が欠ける事故を防ぐ。
    unit_lines = ""
    for project in projects:
        number, label = split_unit(project["name"])
        unit_lines += f"  {number} {label}：{project['docs'][0]}\n"
    files["はじめに.txt"] = (
        "ハイブリッドアプリ開発技法 学生用教材\n\n"
        f"教材の版：{version}\n\n"
        "1. ZIPを展開します。\n"
        "2. docs/common/setup.html をブラウザで開きます。第1コマにSTEP 1〜3、第7コマにSTEP 4〜7を進めます。\n"
        "   教材の置き場所とMonacaアカウントを準備し、Flutterのダウンロードも授業時間内に行います。\n"
        "   Flutterの初回実行は単元の教科書で行います。準備済みの項目は確認してから次へ進みます。\n"
        "3. 授業で使う単元の教科書をブラウザで開きます。\n"
        f"{unit_lines}"
        "4. 完成プロジェクト（先生が作った見本）を含む版には、samples フォルダがあります。\n"
        f"   Flutterの単元は、Visual Studio Code の「File > Open Folder…」で {sample_example(projects)} のように選ぶだけで開けます。\n"
        "   Monacaの単元は、教科書に載っている取り込み用のURLからMonacaへ取り込みます。\n"
        "   samples フォルダの中身は、コードを読み比べるための写しです。\n\n"
        "教科書はオフラインで利用できます。Monacaはブラウザから使うサービスなので、ネット接続が必要です。\n"
        "Flutterの準備とビルドにもネット接続が必要です。\n"
        "教材を更新するときは別のフォルダに展開し、自分で作ったプロジェクトを上書きしないでください。\n"
        "授業中は先生が指定した版を使ってください。質問時には教材の版とSTEP番号を伝えてください。\n"
    ).encode()

    if languages:
        instructions = "\nLanguage / 言語\n日本語：index.html をブラウザで開き、言語を選んでください。\n"
        for language in languages:
            instructions += f"{language['name']}: {language['open_instructions']}\n"
        files["はじめに.txt"] += instructions.encode("utf-8")

    output_dir.mkdir(parents=True, exist_ok=True)
    archive_path = output_dir / asset_name
    with ZipFile(archive_path, "w", compression=ZIP_DEFLATED) as archive:
        for name, data in sorted(files.items()):
            info = ZipInfo(f"{stem}/{name}", date_time=(1980, 1, 1, 0, 0, 0))
            info.create_system = 3
            info.external_attr = (0o100755 if name in executables else 0o100644) << 16
            info.compress_type = ZIP_DEFLATED
            archive.writestr(info, data)
    digest = hashlib.sha256(archive_path.read_bytes()).hexdigest()
    (output_dir / "SHA256SUMS.txt").write_text(f"{digest}  {asset_name}\n", encoding="utf-8")
    (output_dir / "release-metadata.json").write_text(metadata_text, encoding="utf-8")
    print(f"作成しました：{archive_path}（{len(files)}ファイル、{version}）")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "dist")
    args = parser.parse_args()
    try:
        build(args.output_dir.resolve())
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        raise SystemExit(f"教材のパッケージ化に失敗しました：{error}") from None


if __name__ == "__main__":
    main()
