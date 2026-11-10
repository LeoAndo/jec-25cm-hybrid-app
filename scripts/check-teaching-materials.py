"""教材・完成プロジェクト・配布物の整合性を検査する。"""

from __future__ import annotations

import argparse
import difflib
import html
from html.parser import HTMLParser
import itertools
import json
from pathlib import Path
import posixpath
import re
import subprocess
import sys
from xml.etree import ElementTree
from zipfile import BadZipFile, ZipFile

# importlibから読み込まれる場合も、同じフォルダのヘルパーを探せるようにする。
sys.path.insert(0, str(Path(__file__).resolve().parent))
from project_files import LOCAL_PARTS, LOCAL_NAMES, excluded_project_path, project_kind

CONFIG = Path("config/teaching-materials.json")
# Flutterのプロジェクトには、android/ の Kotlin と Gradle（.kt・.kts）と、ios/ の Swift も入っている。
TEXT_SUFFIXES = {
    ".bat", ".css", ".dart", ".gradle", ".html", ".java", ".js", ".json", ".kt", ".kts",
    ".md", ".properties", ".py", ".sh", ".swift", ".toml", ".txt", ".xml", ".yml",
    ".yaml",
}
IGNORED_PARTS = LOCAL_PARTS
# 単元の種類。Monaca系はブラウザ上の Monaca クラウドIDE、Flutter系は Visual Studio Code で作る。
KINDS = ("monaca", "flutter")
# 設定に無いまま検査へ進むと、日本語のエラーではなくPythonのトレースバックになるキー。
REQUIRED_CONFIG_KEYS = ("scan_roots", "terms", "projects")
REQUIRED_PROJECT_KEYS = ("name", "root", "docs", "snippets", "archive")
REQUIRED_KIND_KEYS = {
    "monaca": ("app_id", "entry"),
    "flutter": ("package_name", "application_id", "entry"),
}
REQUIRED_MIRROR_KEYS = ("source", "copy")
REQUIRED_DIFF_KEYS = ("html", "ids", "before", "after")
REQUIRED_TARGET_KEYS = ("path", "requires")
# 教科書のコード（snippets）の照合のしかた。exact はファイル全体、contains は前のSTEPからの
# 追加・置き換えの断片で、source のファイルの連続した行としてそのまま含まれていればよい。
SNIPPET_MATCHES = ("exact", "contains")
# 差分ブロック（<pre class="diff">）の中の印。足す行は <ins>、消す行は <del>、
# あいだの変えない行を省いた目印は <span class="diff-gap">。印のない行は、すでにある行。
DIFF_MARK = re.compile(r'<(ins|del)>(.*?)</\1>|<span class="diff-gap">(.*?)</span>', re.DOTALL)
DIFF_GAP = '<span class="diff-gap">⋮\n</span>'
DIFF_PRE = re.compile(r"<pre\b([^>]*)>")
# --print-diff で、まとまりどうしのあいだがこの行数以下なら、省かずに1つにつなげる。
DIFF_MERGE_GAP = 3
# 足すだけ・消すだけのまとまりをずらす位置を選ぶときに見る、行の形（_block_shape_score）。
# 閉じる側は、かっこ・HTMLの終了タグで始まる行。開く側は、かっこで終わる行。
DIFF_CLOSING_LINE = re.compile(r"^\s*(?:[)}\]]|</)")
DIFF_OPENING_LINE = re.compile(r"[({\[]\s*$")
# Monacaの config.xml は、既定の名前空間を持つ。名前空間なしで探すと、どの要素も見つからない。
WIDGET_NAMESPACE = "http://www.w3.org/ns/widgets"
WIDGET_TAG = f"{{{WIDGET_NAMESPACE}}}widget"
# pubspec.yaml の最上位の name: 行。YAMLのパーサは入れず、字下げのない行だけを読む。
PUBSPEC_NAME = re.compile(r"""^name:[ \t]*["']?([^"'\s#]+)["']?[ \t]*(?:#.*)?$""", re.MULTILINE)
# Flutterで扱うのは iOS と Android だけ（AGENTS.md §10）。
FLUTTER_PLATFORMS = ("android", "ios")
UNSUPPORTED_FLUTTER_PLATFORMS = ("linux", "macos", "web", "windows")
# 単元名は「接頭辞＋番号＋名前」。M はMonaca系、F はFlutter系で、授業ではこの順に進む。
UNIT_NAME = re.compile(r"^([MF])(\d+)(.*)$")
UNIT_PREFIXES = "MF"
# チェック欄の記録キー。docs/assets/textbook.js が既定値を作るときの形と同じにする。
PROGRESS_KEY = re.compile(r"^jec-hybrid-[a-z0-9]+(?:-[a-z0-9]+)*-v[0-9]+$")


def display(root: Path, path: Path) -> str:
    return path.relative_to(root).as_posix()


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def line_of(text: str, needle: str) -> int:
    position = text.find(needle)
    return text.count("\n", 0, position) + 1 if position >= 0 else 1


def positive_int(value) -> bool:
    """正の整数かどうか。JSONのtrue/falseはintの仲間なので、別に弾く。"""
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def inside(name: str, folder: str) -> bool:
    """リポジトリの直下から見たパス name が、folder の下にあるか。../ で外へ出る書き方も外とみなす。"""
    return posixpath.normpath(name).startswith(folder.rstrip("/") + "/")


def text_files(root: Path, scan_roots: list[str], projects=()):
    seen = set()
    for item in scan_roots:
        path = root / item
        if not path.exists():
            continue
        candidates = [path] if path.is_file() else path.rglob("*")
        for candidate in candidates:
            if not candidate.is_file() or candidate.suffix.lower() not in TEXT_SUFFIXES:
                continue
            relative = candidate.relative_to(root)
            if (IGNORED_PARTS.intersection(relative.parts) or relative.name in LOCAL_NAMES
                    or relative.parts[0] == "dist"):
                continue
            # 登録済みのrootを優先し、登録前の単元もマーカーと名前から検査する。
            project = next((item for item in projects if inside(relative.as_posix(), item["root"])), None)
            folder = Path(project["root"]) if project else Path(relative.parts[0])
            kind = project.get("kind") if project else project_kind(root / folder)
            if kind and excluded_project_path(relative.relative_to(folder), kind):
                continue
            key = candidate.resolve()
            if key not in seen:
                seen.add(key)
                yield candidate


def tracked_files(root: Path, project_root: str) -> list[str]:
    result = subprocess.run(
        ["git", "ls-files", "-z", "--", project_root],
        cwd=root,
        check=False,
        capture_output=True,
    )
    if result.returncode != 0:
        raise RuntimeError("git ls-filesを実行できません。Git cloneしたリポジトリで実行してください。")
    return [name for name in result.stdout.decode().split("\0") if name]


def archive_sources(root: Path, project_root: str, kind: str | None = None) -> set[str]:
    """完成プロジェクトZIPに入れるファイル。Git管理下で、IDE設定やビルド出力でないもの。"""
    kind = kind or project_kind(root / project_root)
    return {
        name for name in tracked_files(root, project_root)
        if not excluded_project_path(Path(name).relative_to(project_root), kind)
    }


def add(errors: list[str], root: Path, path: Path | str, line: int, message: str) -> None:
    shown = path if isinstance(path, str) else display(root, path)
    errors.append(f"{shown}:{line}: {message}")


def contains_lines(source: str, fragment: str) -> bool:
    """fragment の行が、source の中に同じ順で連続して並んでいるか。

    前のSTEPからの追加・置き換えの断片（snippets の match: contains）を照合する。
    行の途中から始まる一致は認めない。字下げも照合したいので、行頭の空白は残し、
    行末の空白だけをそろえる。
    """
    lines = [line.rstrip() for line in source.split("\n")]
    part = [line.rstrip() for line in fragment.split("\n")]
    return any(lines[start:start + len(part)] == part
               for start in range(len(lines) - len(part) + 1))


def check_config(config: dict) -> list[str]:
    """検査に必ず要る設定のキーがそろっているか確かめる。

    書き忘れたまま検査へ進むと、日本語のエラーではなくPythonのトレースバックが出て、
    設定のどこを直せばよいか分からなくなる。入口で日本語にして引き返すための検査。
    書かなくてよいキー（course・registration・project_layout・mirrors・diffs など）は求めない。
    kind ごとに要るキー（Monacaの app_id、Flutterの package_name など）も、ここで確かめる。
    kind そのものの誤りは check_project が報告する。
    """
    shown = CONFIG.as_posix()
    errors = [f"{shown}:1: 設定に{key}がありません"
              for key in REQUIRED_CONFIG_KEYS if key not in config]
    if errors:
        return errors  # 以降の検査は、この3つがそろっている前提で書いてある。
    registration = config.get("registration")
    if registration:
        if "targets" not in registration:
            errors.append(f"{shown}:1: registrationにtargetsがありません")
        else:
            for index, target in enumerate(registration["targets"]):
                for key in REQUIRED_TARGET_KEYS:
                    if key not in target:
                        errors.append(
                            f"{shown}:1: registration.targets[{index}]に{key}がありません")
    layout = config.get("project_layout")
    if layout and "gitignore_reference" not in layout:
        errors.append(f"{shown}:1: project_layoutにgitignore_referenceがありません")
    for index, project in enumerate(config["projects"]):
        label = f"projects[{index}]"
        if isinstance(project.get("name"), str) and project["name"]:
            label += f"（{project['name']}）"
        for key in REQUIRED_PROJECT_KEYS:
            if key not in project:
                errors.append(f"{shown}:1: {label}に{key}がありません")
        kind = project.get("kind")
        for key in REQUIRED_KIND_KEYS.get(kind, ()):
            if key not in project:
                errors.append(f"{shown}:1: {label}に{key}がありません（{kind}の単元に必要です）")
        # docs は「学生向け・教員用」の順に2つ。あとで docs[1] まで読むので、ここで数も確かめる。
        docs = project.get("docs")
        if isinstance(docs, list) and len(docs) < 2:
            errors.append(f"{shown}:1: {label}のdocsには、"
                          f"学生向けの教科書と教員用ガイドを2つ書いてください: {docs!r}")
        for mirror_index, mirror in enumerate(project.get("mirrors", [])):
            for key in REQUIRED_MIRROR_KEYS:
                if key not in mirror:
                    errors.append(
                        f"{shown}:1: {label}のmirrors[{mirror_index}]に{key}がありません")
        for diff_index, diff in enumerate(project.get("diffs", [])):
            where = f"{label}のdiffs[{diff_index}]"
            for key in REQUIRED_DIFF_KEYS:
                if key not in diff:
                    errors.append(f"{shown}:1: {where}に{key}がありません")
                elif key != "ids" and (not isinstance(diff[key], str) or not diff[key]):
                    errors.append(f"{shown}:1: {where}の{key}は、ファイルのパスを文字列で書いてください: {diff[key]!r}")
            ids = diff.get("ids")
            if "ids" in diff and (not isinstance(ids, list) or not ids
                                  or not all(isinstance(item, str) and item for item in ids)):
                errors.append(f"{shown}:1: {where}のidsは、<pre>のidを1つ以上並べた配列で書いてください: {ids!r}")
            # 見出しに出すファイルのパスは、ふつうは sources から決まる（diff_label）。label は、
            # sources にないファイル（pubspec.yaml など）のパスを書くときだけ使う。
            label_text = diff.get("label")
            if "label" in diff and (not isinstance(label_text, str) or not label_text):
                errors.append(f"{shown}:1: {where}のlabelは文字列で書いてください: {label_text!r}")
    return errors


def check_course(root: Path, config: dict, errors: list[str]) -> None:
    """授業のコマ数の整合を確かめる。

    単元を足していくうちに、決めた全コマ数を超えてしまう事故を捕まえる。
    1つの単元が何コマにもまたがってよい（sessions に2以上を書く）。
    合計が全コマ数に足りないのは、まだ単元にしていないだけなので許す。
    """
    course = config.get("course")
    if not course:
        return
    total = course.get("total_sessions")
    if not positive_int(total):
        add(errors, root, CONFIG.as_posix(), 1,
            f"course.total_sessionsは正の整数で書いてください: {total!r}")
        return
    used = 0
    for project in config["projects"]:
        sessions = project.get("sessions")
        if not positive_int(sessions):
            add(errors, root, CONFIG.as_posix(), 1,
                f"{project['name']}のsessionsは正の整数で書いてください: {sessions!r}")
            continue
        used += sessions
    if used > total:
        add(errors, root, CONFIG.as_posix(), 1,
            f"projectsのsessionsの合計が、course.total_sessionsの{total}コマを超えています: {used}コマ")
    # 授業の分量は、READMEを読んだ人に最初に伝わる。設定だけ直して書き換え忘れるのを捕まえる。
    readme_path = root / "README.md"
    if not readme_path.is_file():
        add(errors, root, "README.md", 1, "コマ数の表記を確かめるREADME.mdがありません")
        return
    readme = read(readme_path)
    needed = [f"全{total}コマ"]
    minutes = course.get("minutes_per_session")
    if not positive_int(minutes):
        add(errors, root, CONFIG.as_posix(), 1,
            f"course.minutes_per_sessionは正の整数で書いてください: {minutes!r}")
    else:
        needed.append(f"1コマ{minutes}分")
    for word in needed:
        if word not in readme:
            add(errors, root, "README.md", 1, f"READMEに授業の分量の表記がありません: {word}")


def check_terms(root: Path, config: dict, errors: list[str]) -> None:
    for item in config["scan_roots"]:
        if not (root / item).exists():
            add(errors, root, item, 1, "表記揺れ検査対象のパスがありません")
    files = list(text_files(root, config["scan_roots"], config["projects"]))
    contents = {path: read(path) for path in files}
    for term in config["terms"]:
        for path, content in contents.items():
            for line_number, line in enumerate(content.splitlines(), 1):
                for forbidden in term.get("forbidden", []):
                    if forbidden in line:
                        add(errors, root, path, line_number, f"{term['name']}は{term['canonical']}を使用してください（禁止表記: {forbidden}）")
        for required in term.get("required_in", []):
            path = root / required
            if not path.is_file():
                add(errors, root, required, 1, "正式表記を確認する対象ファイルがありません")
                continue
            content = read(path)
            if term["canonical"] not in content:
                add(errors, root, path, 1, f"{term['name']}の正式表記がありません: {term['canonical']}")


def value_from_gradle(text: str, key: str) -> str | None:
    match = re.search(rf'^\s*{re.escape(key)}\s*=\s*"([^"]+)"', text, re.MULTILINE)
    return match.group(1) if match else None


def setting_text(root: Path, project: dict, key: str, errors: list[str]) -> str | None:
    """単元の設定のうち、文字列で書くキーを読む。書き方が正しくなければ報告してNoneを返す。

    キーが無いことは check_config が先に報告しているので、ここに来るのは型を誤ったときだけ。
    """
    value = project.get(key)
    if not isinstance(value, str) or not value:
        add(errors, root, CONFIG.as_posix(), 1,
            f"{project['name']}の{key}は文字列で書いてください: {value!r}")
        return None
    return value


def check_entry(root: Path, project: dict, entry: str, folder: str, errors: list[str]) -> None:
    """アプリが最初に読むファイル（entry）が、決まったフォルダの下に実在するか確かめる。"""
    if not inside(entry, folder):
        add(errors, root, CONFIG.as_posix(), 1,
            f"{project['name']}のentryが{folder}/の下にありません: {entry}")
    elif not (root / entry).is_file():
        add(errors, root, entry, 1, "entryに書いたファイルがありません")


def check_monaca(root: Path, project: dict, errors: list[str]) -> None:
    """Monaca系の完成プロジェクトが、設定と同じアプリIDで、www/ から始まるか確かめる。

    Monacaへは「インポート」で取り込むので、取り込んでから違いに気付くと、
    Freeプランで3個までのプロジェクトの枠を1つ無駄にする。ローカルで分かることはここで捕まえる。
    """
    app_id = setting_text(root, project, "app_id", errors)
    entry = setting_text(root, project, "entry", errors)
    config_path = root / project["root"] / "config.xml"
    if not config_path.is_file():
        add(errors, root, config_path, 1, "config.xmlがありません（Monacaのプロジェクトの直下に置きます）")
    else:
        try:
            text = read(config_path)
            widget = ElementTree.fromstring(text.encode("utf-8"))
        except (OSError, UnicodeDecodeError, ElementTree.ParseError) as error:
            add(errors, root, config_path, 1, f"config.xmlを読み込めません: {error}")
        else:
            line = line_of(text, "<widget")
            if widget.tag != WIDGET_TAG:
                add(errors, root, config_path, line,
                    f"config.xmlの最上位の要素が、名前空間 {WIDGET_NAMESPACE} の<widget>ではありません: {widget.tag}")
            elif app_id is not None and widget.get("id") != app_id:
                add(errors, root, config_path, line,
                    f"config.xmlの<widget>のidが一致しません: {widget.get('id')!r} != {app_id!r}")
    if entry is not None:
        check_entry(root, project, entry, posixpath.join(project["root"], "www"), errors)


def check_flutter(root: Path, project: dict, errors: list[str]) -> None:
    """Flutter系の完成プロジェクトが、設定と同じ名前で、iOSとAndroidだけを持つか確かめる。

    Dartのパッケージ名（pubspec.yaml の name）は、import 'package:<名前>/…' に使われる。
    applicationId は、flutter create --org で決まり、学生の端末でアプリを見分ける名前になる。
    """
    package_name = setting_text(root, project, "package_name", errors)
    application_id = setting_text(root, project, "application_id", errors)
    entry = setting_text(root, project, "entry", errors)
    project_root = root / project["root"]

    pubspec_path = project_root / "pubspec.yaml"
    if not pubspec_path.is_file():
        add(errors, root, pubspec_path, 1, "pubspec.yamlがありません")
    else:
        text = read(pubspec_path)
        match = PUBSPEC_NAME.search(text)
        actual = match.group(1) if match else None
        line = text.count("\n", 0, match.start()) + 1 if match else 1
        if package_name is not None and actual != package_name:
            add(errors, root, pubspec_path, line,
                f"pubspec.yamlのnameが一致しません: {actual!r} != {package_name!r}")

    gradle_path = project_root / "android/app/build.gradle.kts"
    if not gradle_path.is_file():
        add(errors, root, gradle_path, 1, "android/app/build.gradle.ktsがありません")
    elif application_id is not None:
        gradle = read(gradle_path)
        for key in ("namespace", "applicationId"):
            actual = value_from_gradle(gradle, key)
            if actual != application_id:
                add(errors, root, gradle_path, line_of(gradle, key),
                    f"{key}が一致しません: {actual!r} != {application_id!r}")

    for platform in FLUTTER_PLATFORMS:
        if not (project_root / platform).is_dir():
            add(errors, root, project_root / platform, 1,
                f"{platform}/がありません（flutter create に --platforms=ios,android を付けて作ります）")
    for platform in UNSUPPORTED_FLUTTER_PLATFORMS:
        if (project_root / platform).exists():
            add(errors, root, project_root / platform, 1,
                f"{platform}/があります。この授業のFlutterはiOSとAndroidだけを扱うので、消してください")

    if entry is not None:
        check_entry(root, project, entry, posixpath.join(project["root"], "lib"), errors)


def check_sources(root: Path, project: dict, errors: list[str]) -> None:
    """完成コード（sources）が実在し、決まったフォルダの下にあり、改行がLFだけか確かめる。

    Monaca系は www/ の下だけがアプリとして動くので、sources はすべて www/ の下に置く。
    Flutter系は lib/ の下のDartだけがアプリになるので、.dart は lib/ の下に置く
    （pubspec.yaml のようなDart以外のファイルは、どこにあってもよい）。
    CR（\\r）を禁じるのは、教科書に載せるコード（snippets）がLFだから。MonacaTemplate の
    www/index.html などはCRLFなので、そこから複製すると、配る見本（ZIP・samples/）と教科書の
    コードで改行が食い違い、見比べたり差分を取ったりすると全行が違って見える。
    snippets の照合は、Pythonがファイルを読むときに改行を読み替えるので、この食い違いを見逃す。
    """
    sources = project.get("sources")
    if not sources:
        add(errors, root, CONFIG.as_posix(), 1,
            f"{project['name']}のsourcesに、完成コードのパスを1つ以上書いてください")
        return
    kind = project["kind"]
    www = posixpath.join(project["root"], "www")
    lib = posixpath.join(project["root"], "lib")
    for name in sources:
        path = root / name
        if not path.is_file():
            add(errors, root, name, 1, "完成コードのファイルがありません")
            continue
        if kind == "monaca" and not inside(name, www):
            add(errors, root, name, 1,
                f"Monacaの完成コードが{www}/の下にありません（アプリとして動くのは www/ の中だけです）")
        if kind == "flutter" and name.endswith(".dart") and not inside(name, lib):
            add(errors, root, name, 1,
                f"Dartの完成コードが{lib}/の下にありません（アプリになるのは lib/ の中のDartだけです）")
        data = path.read_bytes()
        if b"\r" in data:
            line = data.count(b"\n", 0, data.index(b"\r")) + 1
            add(errors, root, name, line,
                "改行にCR（\\r）が含まれています。LFだけにそろえてください（教科書に載せるコードはLFなので、見本と改行が食い違います）")


def check_import_url(root: Path, project: dict, errors: list[str]) -> None:
    """Monacaの取り込み用URL（import_url）の書き方を確かめる。

    import_url は、先生が完成プロジェクトをMonacaで「公開」して発行したURL
    （https://monaca.mobi/ja/directimport?pid=…）。2026-10-06 に、このURLから学生へ見本を
    取り込ませる仕組みを廃止した（#168）。いまは、取り込めることを確かめた教員用の記録として残し、
    教科書（docs/）に載っていないことを check_no_sample_guidance が確かめる。
    書いていない単元では何もしない。
    """
    if "import_url" not in project:
        return
    url = project["import_url"]
    if project["kind"] != "monaca":
        add(errors, root, CONFIG.as_posix(), 1,
            f"{project['name']}のimport_urlは書けません（Monacaの単元にだけ書きます）")
        return
    if not isinstance(url, str) or not url:
        add(errors, root, CONFIG.as_posix(), 1,
            f"{project['name']}のimport_urlは文字列で書いてください: {url!r}")


def check_project(root: Path, project: dict, errors: list[str]) -> None:
    kind = project.get("kind")
    if kind not in KINDS:
        add(errors, root, CONFIG.as_posix(), 1,
            f"{project['name']}のkindが不正です: {kind!r}（{'か'.join(KINDS)}と書いてください）")
        return

    if not (root / project["root"]).is_dir():
        # フォルダごと無いときは、中のファイルを1つずつ挙げても直す場所は1つなので、まとめて1回だけ言う。
        add(errors, root, project["root"], 1, "完成プロジェクトのフォルダがありません")
    elif kind == "monaca":
        check_monaca(root, project, errors)
    else:
        check_flutter(root, project, errors)
    check_sources(root, project, errors)
    check_import_url(root, project, errors)

    for doc_name in project["docs"]:
        path = root / doc_name
        if not path.is_file():
            add(errors, root, path, 1, "教材ファイルがありません")
            continue
        content = read(path)
        if project["name"] not in content:
            add(errors, root, path, 1, f"教材に必要な表記がありません: {project['name']}")

    for snippet in project["snippets"]:
        html_path = root / snippet["html"]
        source_path = root / snippet["source"]
        if not html_path.is_file() or not source_path.is_file():
            continue
        document = read(html_path)
        match = re.search(rf'<pre\s+id="{re.escape(snippet["id"])}"[^>]*><code>(.*?)</code></pre>', document, re.DOTALL)
        if not match:
            add(errors, root, html_path, 1, f"コードスニペットがありません: {snippet['id']}")
            continue
        line = line_of(document, f'id="{snippet["id"]}"')
        mode = snippet.get("match", "exact")
        if mode not in SNIPPET_MATCHES:
            add(errors, root, CONFIG.as_posix(), 1,
                f"snippetsの{snippet['id']}のmatchは{'・'.join(SNIPPET_MATCHES)}のどちらかで書いてください: {mode!r}")
            continue
        expected = read(source_path).rstrip()
        actual = html.unescape(match.group(1)).rstrip()
        if mode == "exact":
            if actual != expected:
                add(errors, root, html_path, line, f"{snippet['id']}と{snippet['source']}が一致しません")
        elif not actual.strip():
            add(errors, root, html_path, line, f"{snippet['id']}のコードが空です")
        elif not contains_lines(expected, actual):
            add(errors, root, html_path, line,
                f"{snippet['id']}が{snippet['source']}の連続した行として見つかりません")

    archive_path = root / project["archive"]
    if not archive_path.is_file():
        add(errors, root, archive_path, 1, "完成プロジェクトZIPがありません")
        return
    try:
        expected_names = archive_sources(root, project["root"], project.get("kind"))
        with ZipFile(archive_path) as archive:
            actual_names = set(archive.namelist())
            for name in sorted(expected_names - actual_names):
                add(errors, root, archive_path, 1, f"ZIPにソースがありません: {name}")
            for name in sorted(actual_names - expected_names):
                add(errors, root, archive_path, 1, f"ZIPに配布対象外ファイルがあります: {name}")
            for name in sorted(expected_names & actual_names):
                source = root / name
                if archive.read(name) != source.read_bytes():
                    add(errors, root, archive_path, 1, f"ZIPとソースの内容が一致しません: {name}")
                source_executable = bool(source.stat().st_mode & 0o100)
                archive_executable = bool((archive.getinfo(name).external_attr >> 16) & 0o100)
                if archive_executable != source_executable:
                    add(errors, root, archive_path, 1, f"ZIPとソースの実行権限が一致しません: {name}")
    except (BadZipFile, OSError) as error:
        add(errors, root, archive_path, 1, f"ZIPを読み込めません: {error}")



def check_mirrors(root: Path, project: dict, errors: list[str]) -> None:
    """教材に置いた複製コードが、完成プロジェクトのソースと1バイトも違わないか確かめる。

    教員用ガイドの teacher/<スラッグ>/code/ は、完成プロジェクトを開かなくても
    授業中にコードを見せられるように置いた複製である。
    完成コードだけを直すと、複製が古いまま静かに残るので、ここで捕まえる。
    照合するのは mirrors を書いた単元だけで、書かない単元では何もしない。
    """
    for mirror in project.get("mirrors", []):
        source_path = root / mirror["source"]
        copy_path = root / mirror["copy"]
        if not source_path.is_file():
            add(errors, root, mirror["source"], 1, "複製コードの元ファイルがありません")
            continue
        if not copy_path.is_file():
            add(errors, root, mirror["copy"], 1, "複製コードがありません")
            continue
        try:
            if copy_path.read_bytes() != source_path.read_bytes():
                add(errors, root, copy_path, 1,
                    f"複製コードと元ファイルの内容が一致しません: {mirror['source']}"
                    "（元ファイルからコピーし直してください）")
        except OSError as error:
            add(errors, root, copy_path, 1, f"複製コードを読み込めません: {error}")


# ---------------------------------------------------------------------------
# 差分ブロック（README「授業用教科書の基本方針」14）
#
# すでにあるファイルを直すSTEPでは、直す場所だけを載せる。
# 足す行は <ins>、消す行は <del>、印のない行は、すでにファイルにある行（学生は入力しない）。
# あいだの変えない行は <span class="diff-gap">⋮</span> で省く。
# ここで確かめるのは「直す前のファイルに、教科書の差分ブロックを上から順に当てると、
# 直したあとのファイルと1文字も違わない」こと。全文のスニペットのバイト照合と同じ役目を持つ。
# しくみは、同じ学生が受ける Kotlin演習（jec-25cm-kotlin）の検査を移したもの。
# ---------------------------------------------------------------------------

def code_lines(text: str) -> list[str]:
    """ファイルの中身を行に分ける。末尾の改行と空行の違いは見ない（スニペットの照合と同じ扱い）。"""
    return text.rstrip().split("\n")


def _shorten(line: str, limit: int = 70) -> str:
    """エラーに行を引用するときの形。字下げや末尾の空白の違いも見えるように、repr で囲む。"""
    return repr(line if len(line) <= limit else line[:limit] + "…")


def diff_block_hunks(inner: str) -> list[list[tuple[str, str]]]:
    """差分ブロックの中身（<code> の内側）を、省略の目印（⋮）で区切った「まとまり」に分ける。

    まとまりは (種類, 行) の並び。種類は " "（すでにある行）・"+"（足す行）・"-"（消す行）。
    学生は行ごとに「足す・消す・そのまま」を読むので、印は必ず行の単位で付ける。
    行の途中で始まる・終わる印は、どの行のことか決まらないので ValueError にする。
    """
    pieces: list[tuple[str, str]] = []  # (種類, 文字)。種類は上の3つと、省略の目印の "gap"
    position = 0
    for match in DIFF_MARK.finditer(inner):
        if match.start() > position:
            pieces.append((" ", inner[position:match.start()]))
        if match.group(1):
            pieces.append(("+" if match.group(1) == "ins" else "-", match.group(2)))
        else:
            pieces.append(("gap", match.group(3)))
        position = match.end()
    if position < len(inner):
        pieces.append((" ", inner[position:]))
    hunks: list[list[tuple[str, str]]] = []
    current: list[tuple[str, str]] = []
    for index, (kind, raw) in enumerate(pieces):
        if re.search(r"<[A-Za-z/!]", raw):
            raise ValueError('<ins>・<del>・<span class="diff-gap"> 以外のタグは使えません'
                             "（印を入れ子にもできません）")
        text = html.unescape(raw)
        if not text.endswith("\n") and index < len(pieces) - 1:
            raise ValueError("印は行の単位で付けてください（<ins>・<del>・省略の目印は、"
                             f"行の先頭で始め、改行の直後で閉じます）: {_shorten(text)}")
        if kind == "gap":
            if not current:
                raise ValueError("省略の目印（⋮）の前に、行がありません")
            hunks.append(current)
            current = []
            continue
        lines = text.split("\n")
        if text.endswith("\n"):
            lines.pop()
        current.extend((kind, line) for line in lines)
    if not current:
        raise ValueError("省略の目印（⋮）のあとに、行がありません" if hunks else "差分ブロックが空です")
    hunks.append(current)
    return hunks


def _closest_mismatch(lines: list[str], old: list[str]) -> str:
    """当てる場所が見つからないとき、いちばん長く一致した場所と、最初に違った行を返す。"""
    best = (-1, 0)  # (一致した行数, 開始位置)
    for start in range(len(lines)):
        matched = 0
        while (matched < len(old) and start + matched < len(lines)
               and lines[start + matched] == old[matched]):
            matched += 1
        if matched > best[0]:
            best = (matched, start)
    matched, start = best
    if matched <= 0:
        return f"最初の行が、直す前のファイルにありません: {_shorten(old[0])}"
    actual = lines[start + matched] if start + matched < len(lines) else "（ファイルの終わり）"
    return (f"{matched}行目までは直す前のファイルの{start + 1}行目からと一致し、次の行が違います。"
            f"教科書: {_shorten(old[matched])}／ファイル: {_shorten(actual)}")


def apply_diff_hunks(lines: list[str], hunks: list[list[tuple[str, str]]]) -> list[str]:
    """直す前の行に、差分ブロックのまとまりを上から順に当てた結果を返す。当てられなければ ValueError。

    学生は、すでにある行（印のない行と消す行）を目印にして場所を探す。
    その並びがファイルに無い、または2か所以上あると、どこを直すのか決まらない。
    """
    position = 0  # 直前のまとまりを当て終えた位置
    for number, hunk in enumerate(hunks, 1):
        label = f"{number}つ目のまとまり" if len(hunks) > 1 else "このブロック"
        old = [line for kind, line in hunk if kind != "+"]
        new = [line for kind, line in hunk if kind != "-"]
        if not old:
            raise ValueError(f"{label}に、すでにある行（印のない行か消す行）がありません。足す場所を決められません")
        found = [start for start in range(len(lines) - len(old) + 1) if lines[start:start + len(old)] == old]
        if not found:
            raise ValueError(f"{label}を当てる場所がありません。{_closest_mismatch(lines, old)}")
        if len(found) > 1:
            places = "・".join(f"{start + 1}行目" for start in found)
            raise ValueError(f"{label}の場所が1つに決まりません（同じ並びが{places}にあります）。"
                             "前後のすでにある行を足してください")
        start = found[0]
        if start < position:
            raise ValueError(f"{label}が、前のまとまりと重なっているか、それより上の行を指しています。"
                             "ファイルの上から下の順に並べてください")
        lines = lines[:start] + new + lines[start + len(old):]
        position = start + len(new)
    return lines


def check_diffs(root: Path, project: dict, errors: list[str]) -> None:
    """教科書の差分ブロックを当てると、直したあとのファイルになるか確かめる。

    diffs の1件は「直す前のファイル → 直したあとのファイル」の1回の変更で、ids に並べた
    <pre> を順に当てる。1つのSTEPで同じファイルの差分を複数の枠に分けて載せられる。
    当てた結果が直したあとのファイルと1行でも違えば、教科書の差分が足りないか、古い。
    直す前・直したあとのファイルは、ふつうは隣り合うSTEPの照合コード（teacher/<スラッグ>/code/）。
    """
    for diff in project.get("diffs", []):
        html_path = root / diff["html"]
        before_path = root / diff["before"]
        after_path = root / diff["after"]
        if not html_path.is_file():
            add(errors, root, diff["html"], 1, "差分ブロックを載せる教材ファイルがありません")
            continue
        if not before_path.is_file():
            add(errors, root, diff["before"], 1, "差分ブロックの、直す前のファイルがありません")
            continue
        if not after_path.is_file():
            add(errors, root, diff["after"], 1, "差分ブロックの、直したあとのファイルがありません")
            continue
        document = read(html_path)
        lines = code_lines(read(before_path))
        first_line = 1
        applied = True
        for number, block_id in enumerate(diff["ids"]):
            match = re.search(rf'<pre\s+id="{re.escape(block_id)}"[^>]*><code>(.*?)</code></pre>',
                              document, re.DOTALL)
            if not match:
                add(errors, root, html_path, 1, f"差分ブロックがありません: {block_id}")
                applied = False
                break
            line = line_of(document, f'id="{block_id}"')
            if number == 0:
                first_line = line
            try:
                lines = apply_diff_hunks(lines, diff_block_hunks(match.group(1)))
            except ValueError as error:
                add(errors, root, html_path, line, f"{block_id}: {error}（直す前のファイル: {diff['before']}）")
                applied = False
                break
        if not applied:
            continue
        expected = code_lines(read(after_path))
        if lines == expected:
            continue
        for number, (actual, wanted) in enumerate(itertools.zip_longest(lines, expected), 1):
            if actual != wanted:
                shown_actual = "（行がありません）" if actual is None else _shorten(actual)
                shown_wanted = "（行がありません）" if wanted is None else _shorten(wanted)
                add(errors, root, html_path, first_line,
                    f"{'・'.join(diff['ids'])}を{diff['before']}に当てても、{diff['after']}と一致しません"
                    f"（{number}行目。当てた結果: {shown_actual}／{diff['after']}: {shown_wanted}）")
                break


def check_diff_registration(root: Path, config: dict, errors: list[str]) -> None:
    """教科書にある差分ブロック（<pre class="diff">）が、すべて diffs に登録されているか確かめる。

    登録のない差分ブロックは、当てた結果を誰も確かめていない。照合コードを直したときに、
    古い差分が教科書に静かに残るので、ここで捕まえる。
    1つの枠を2件の diffs に書くことも落とす。枠は1回の変更にしか当てられない。
    """
    docs = root / "docs"
    if not docs.is_dir():
        return
    registered: dict[tuple[str, str], int] = {}
    for project in config["projects"]:
        for diff in project.get("diffs", []):
            for block_id in diff.get("ids", []):
                key = (diff.get("html"), block_id)
                registered[key] = registered.get(key, 0) + 1
    for (name, block_id), count in sorted(registered.items(), key=lambda item: (str(item[0][0]), item[0][1])):
        if count > 1:
            add(errors, root, CONFIG.as_posix(), 1,
                f"差分ブロックが、diffsに{count}回書いてあります: {name} の {block_id}"
                "（1つの枠は、1回の変更にだけ当てます）")
    for path in sorted(docs.rglob("*.html")):
        if IGNORED_PARTS.intersection(path.relative_to(root).parts):
            continue
        try:
            text = read(path)
        except (OSError, UnicodeDecodeError):
            continue
        name = display(root, path)
        for match in DIFF_PRE.finditer(text):
            attributes = dict(re.findall(r'([\w-]+)="([^"]*)"', match.group(1)))
            if "diff" not in attributes.get("class", "").split():
                continue
            line = text.count("\n", 0, match.start()) + 1
            block_id = attributes.get("id")
            if not block_id:
                add(errors, root, path, line, '差分ブロック（<pre class="diff">）にidがありません')
            elif (name, block_id) not in registered:
                add(errors, root, path, line,
                    f"差分ブロックが{CONFIG.as_posix()}のdiffsにありません: {block_id}"
                    "（直す前と直したあとのファイルを登録してください）")


def _block_shape_score(block: list[str]) -> int:
    """足すだけ・消すだけのまとまりの、読みやすさの点。大きいほどよい。

    関数を1つ足すと、機械的な差分は「前の関数の閉じかっこ・空行・新しい関数（閉じかっこの手前まで）」
    を足す行にすることがある。当てた結果は同じでも、学生には、閉じかっこを打つ場所が分かりにくい。
    まとまりが、閉じる行から始まる・開く行で終わる位置を避け、空行で区切れる位置を選ぶ。
    """
    score = 0
    if not block[-1].strip():
        score += 2  # 「足すもの＋空行」。次のまとまりとの区切りまでを足す形で、いちばん読みやすい。
    if not block[0].strip():
        score += 1  # 「空行＋足すもの」
    if DIFF_CLOSING_LINE.search(block[0]):
        score -= 2
    if DIFF_OPENING_LINE.search(block[-1]):
        score -= 2
    return score


def _slide_changes(opcodes: list[tuple], before: list[str], after: list[str]) -> list[tuple]:
    """足すだけ・消すだけの変更を、同じ結果になる範囲で上下にずらし、読みやすい位置にそろえる。

    difflib は、同じ行が続くところ（閉じかっこ・空行）で、どこからを変更とみなすかを機械的に決める。
    足す（消す）行の先頭が、すぐ下のすでにある行と同じなら、1行下へずらしても結果は変わらない
    （末尾が、すぐ上の行と同じなら、1行上へ）。ずらせる位置のうち、_block_shape_score が
    いちばん大きい位置を選ぶ。同じ点なら、difflib が決めた位置に近いほうにする。
    前後の変更とのあいだには、すでにある行を1行は残す（となりの変更とつながらないようにする）。
    """
    changes = [list(opcode) for opcode in opcodes if opcode[0] != "equal"]
    for index, (tag, i1, i2, j1, j2) in enumerate(changes):
        if tag not in ("insert", "delete"):
            continue
        # 行を持っている側（足すなら直したあと、消すなら直す前）の並びで考える。
        lines, start, end = (after, j1, j2) if tag == "insert" else (before, i1, i2)
        # ずらせるのは、前後の、すでにある行のあいだだけ。前の変更は、もうずらし終えた位置で見る。
        up_limit = i1 - changes[index - 1][2] - 1 if index > 0 else i1
        down_limit = changes[index + 1][1] - i2 - 1 if index + 1 < len(changes) else len(before) - i2
        candidates = [0]
        shift = 0
        while -shift < up_limit and lines[start + shift - 1] == lines[end + shift - 1]:
            shift -= 1
            candidates.append(shift)
        shift = 0
        while shift < down_limit and lines[start + shift] == lines[end + shift]:
            shift += 1
            candidates.append(shift)
        best = max(candidates, key=lambda move: (_block_shape_score(lines[start + move:end + move]), -abs(move), move))
        changes[index] = [tag, i1 + best, i2 + best, j1 + best, j2 + best]
    # 変更のあいだを、すでにある行（equal）で埋め直す。ずらしても、あいだの行数は両方の側で同じ。
    result: list[tuple] = []
    i = j = 0
    for tag, i1, i2, j1, j2 in changes:
        if i1 > i:
            result.append(("equal", i, i1, j, j1))
        result.append((tag, i1, i2, j1, j2))
        i, j = i2, j2
    if i < len(before):
        result.append(("equal", i, len(before), j, len(after)))
    return result


def _diff_hunk(opcodes: list, before: list[str], after: list[str], start: int, end: int) -> list[tuple[str, str]]:
    """直す前の start 行目から end 行目の手前までを、1つのまとまりにする。"""
    hunk: list[tuple[str, str]] = []
    for tag, i1, i2, j1, j2 in opcodes:
        if tag == "equal":
            hunk.extend((" ", line) for line in before[max(i1, start):min(i2, end)])
        elif start <= i1 and i2 <= end:
            hunk.extend(("-", line) for line in before[i1:i2])
            hunk.extend(("+", line) for line in after[j1:j2])
    # 端の空行は、場所を探す目印にならないので落とす。ただし、すでにある行（消す行を含む）が
    # ほかに1行もなければ残す。空のファイルに書き足すときは、その空行だけが、足す場所の目印になる。
    def has_landmark(lines: list[tuple[str, str]]) -> bool:
        return any(kind != "+" for kind, _ in lines)
    while hunk[0] == (" ", "") and has_landmark(hunk[1:]):
        hunk.pop(0)
    while hunk[-1] == (" ", "") and has_landmark(hunk[:-1]):
        hunk.pop()
    return hunk


def diff_hunks_between(before: list[str], after: list[str], context: int = 3) -> list[list[tuple[str, str]]]:
    """直す前と直したあとの行から、差分ブロックのまとまりを作る（--print-diff 用）。

    変わる行の前後に、すでにある行を context 行ずつ付ける。それだけでは場所が1つに
    決まらないまとまりは、決まるまで前後の行を1行ずつ足す。
    あいだが DIFF_MERGE_GAP 行以下のまとまりは、1つにまとめる（2〜3行だけを ⋮ で省いても、
    読む量は減らず、つながりが見えなくなるだけなので）。
    """
    opcodes = _slide_changes(
        difflib.SequenceMatcher(None, before, after, autojunk=False).get_opcodes(), before, after)
    changes = [index for index, opcode in enumerate(opcodes) if opcode[0] != "equal"]
    margins = {index: max(context, 1) for index in changes}
    hunks: list[list[tuple[str, str]]] = []
    for _ in range(len(before) * max(len(changes), 1) + 2):
        spans: list[list] = []  # [直す前の開始位置, 終了位置, そこに入る変更の番号]
        for index in changes:
            _, i1, i2, _, _ = opcodes[index]
            start, end = max(0, i1 - margins[index]), min(len(before), i2 + margins[index])
            if spans and start <= spans[-1][1] + DIFF_MERGE_GAP:
                spans[-1][1] = max(spans[-1][1], end)
                spans[-1][2].append(index)
            else:
                spans.append([start, end, [index]])
        hunks = [_diff_hunk(opcodes, before, after, start, end) for start, end, _ in spans]
        lines, failed = list(before), None
        for index, hunk in enumerate(hunks):
            try:
                lines = apply_diff_hunks(lines, [hunk])
            except ValueError:
                failed = index
                break
        if failed is None:
            break
        for index in spans[failed][2]:
            margins[index] += 1
    return hunks


def render_diff_block(hunks: list[list[tuple[str, str]]], block_id: str) -> str:
    """まとまりを、教科書に貼る差分ブロックのHTMLにする。"""
    parts = []
    for number, hunk in enumerate(hunks):
        if number:
            parts.append(DIFF_GAP)
        for kind, group in itertools.groupby(hunk, key=lambda item: item[0]):
            text = "".join(html.escape(line, quote=False) + "\n" for _, line in group)
            parts.append({"+": f"<ins>{text}</ins>", "-": f"<del>{text}</del>", " ": text}[kind])
    return f'<pre id="{block_id}" class="diff" tabindex="0"><code>{"".join(parts)}</code></pre>'


def render_diff_head(label: str, hunks: list[list[tuple[str, str]]]) -> str:
    """差分ブロックの見出し。終わり側に、その枠に出てくる行の種類だけを凡例として並べる。"""
    kinds = {kind for hunk in hunks for kind, _ in hunk}
    legend = "".join(chip for kind, chip in (
        ("+", '<span class="diff-add">足す行</span>'),
        ("-", '<span class="diff-del">消す行</span>'),
        (" ", '<span class="diff-keep">すでにある行</span>'),
    ) if kind in kinds)
    return (f'<div class="code-head diff-head"><span>{html.escape(label, quote=False)}</span>'
            f'<span class="diff-legend">{legend}</span></div>')


def diff_label(project: dict, diff: dict) -> str:
    """差分ブロックの見出しに出す、ファイルのパス（プロジェクトの中での位置）。

    直したあとのファイルは teacher/<スラッグ>/code/11-main.dart のような照合コードなので、
    番号を外した名前（main.dart）と同じ名前の完成コードを sources から探し、プロジェクトの中での
    パス（lib/main.dart）にする。学生がエディタで開くファイルと、同じ書き方になる。
    sources に同じ名前がない、または2つ以上あるときは、番号を外した名前をそのまま使う。
    見出しを別の書き方にしたいときは、diffs に label を書く。
    """
    if diff.get("label"):
        return diff["label"]
    name = re.sub(r"^\d+-", "", posixpath.basename(diff["after"]))
    prefix = project["root"].rstrip("/") + "/"
    found = [source[len(prefix):] for source in project.get("sources") or []
             if isinstance(source, str) and source.startswith(prefix) and posixpath.basename(source) == name]
    return found[0] if len(found) == 1 else name


def print_diff(root: Path, html_name: str, block_id: str, context: int) -> int:
    """diffs に登録した1件の差分ブロックを、直す前後のファイルから作って表示する。

    教科書のコードは手で写さない。先に diffs へ登録してから、これで作った枠を貼る。
    ids を2つ以上並べた登録は、まとまりの数が ids の数と同じなら、まとまりごとに1つの枠にして、
    ids の順に id を付ける（説明をはさんで載せる形）。数が合わなければ、全部を1つの枠で出す。
    すでにある行を増やしたいとき、枠の分け方を変えたいときは、貼ったあとで直す。
    直した結果が正しいかどうかは、いつもの検査が確かめる。
    """
    try:
        config = json.loads(read(root / CONFIG))
    except (OSError, json.JSONDecodeError) as error:
        print(f"{CONFIG}:1: 設定ファイルを読み込めません: {error}", file=sys.stderr)
        return 1
    problems = check_config(config)
    if problems:
        print("\n".join(problems), file=sys.stderr)
        return 1
    for project in config["projects"]:
        for diff in project.get("diffs", []):
            if diff["html"] != html_name or block_id not in diff["ids"]:
                continue
            before_path, after_path = root / diff["before"], root / diff["after"]
            if not before_path.is_file() or not after_path.is_file():
                print(f"直す前後のファイルがありません: {diff['before']} → {diff['after']}", file=sys.stderr)
                return 1
            before, after = code_lines(read(before_path)), code_lines(read(after_path))
            hunks = diff_hunks_between(before, after, context)
            if not hunks:
                print(f"差分がありません: {diff['before']} → {diff['after']}", file=sys.stderr)
                return 1
            # 作った枠を当てて、直したあとのファイルになることを確かめてから出す。黙って違う枠を出さない。
            try:
                applied = apply_diff_hunks(before, hunks)
            except ValueError as error:
                print(f"差分ブロックを作れません: {error}（直す前のファイル: {diff['before']}）", file=sys.stderr)
                return 1
            if applied != after:
                print(f"作った枠を当てても、{diff['after']}になりません。スクリプトの不具合です", file=sys.stderr)
                return 1
            label = diff_label(project, diff)
            ids = diff["ids"]
            if len(ids) > 1 and len(hunks) == len(ids):
                for hunk, hunk_id in zip(hunks, ids):
                    print(render_diff_head(label, [hunk]) + render_diff_block([hunk], hunk_id))
                return 0
            if len(ids) > 1:
                print(f"まとまりは{len(hunks)}つ、idsは{len(ids)}つです。全部を1つの枠（{block_id}）で出します。"
                      "⋮ の位置で分けて、それぞれに見出しと id を付けてください", file=sys.stderr)
            print(render_diff_head(label, hunks) + render_diff_block(hunks, block_id))
            return 0
    print(f"{CONFIG.as_posix()}のdiffsに登録がありません: {html_name} の {block_id}", file=sys.stderr)
    return 1


class SectionTexts(HTMLParser):
    """<section> ごとに、中に書かれた文字を集める。入れ子の <section> は外側にまとめる。"""

    def __init__(self):
        super().__init__()
        self.texts: list[str] = []
        self._depth = 0
        self._parts: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag == "section":
            self._depth += 1

    def handle_data(self, data):
        if self._depth:
            self._parts.append(data)

    def handle_endtag(self, tag):
        if tag != "section" or not self._depth:
            return
        self._depth -= 1
        if not self._depth:
            # 改行や字下げの違いで照合が外れないよう、空白は1つにまとめる。
            self.texts.append(" ".join("".join(self._parts).split()))
            self._parts = []


def check_downloads(root: Path, project: dict, errors: list[str]) -> None:
    """教材のフォルダから学生が自分でコピーするファイルが、完成プロジェクトのソースと同じか確かめる。

    ZIPの検査が「ZIPの中身＝ソース」を保証するので、ここで「配布ファイル＝ソース」を確かめれば、
    学生がどこから取っても同じ中身になる。
    学生は、教材のフォルダをFinderで開いてコピーする。ダウンロードボタンにはしない。
    教科書をファイルとして開いていると（file://）ブラウザが download 属性を無視し、
    押しても保存されずに中身が表示されるだけだからである。
    教科書から置き場所やファイル名の案内が消えたら、ここで検出する。
    """
    downloads = project.get("downloads", [])
    if not downloads:
        return
    sources = archive_sources(root, project["root"], project.get("kind"))
    textbook_path = root / project["docs"][0]
    sections = SectionTexts()
    if textbook_path.is_file():
        sections.feed(read(textbook_path))
    unguided_folders: set[str] = set()
    for item in downloads:
        download_path = root / item["download"]
        source_path = root / item["source"]
        name = Path(item["download"]).name
        if name != Path(item["source"]).name:
            # 学生は手に入れたファイルを、そのまま www/ や assets/ に入れる。
            # 名前が違うと、HTMLの src や pubspec.yaml のアセット登録から見つからない。
            add(errors, root, item["download"], 1, f"配布ファイルとソースのファイル名が一致しません: {item['source']}")
        if item["source"] not in sources:
            add(errors, root, item["source"], 1, "配布ファイルの元ファイルが、完成プロジェクトZIPに入るファイルではありません")
        elif not download_path.is_file():
            add(errors, root, item["download"], 1, "配布ファイルがありません")
        else:
            try:
                if download_path.read_bytes() != source_path.read_bytes():
                    add(errors, root, download_path, 1, f"配布ファイルとソースの内容が一致しません: {item['source']}（ソースからコピーし直してください）")
            except OSError as error:
                add(errors, root, download_path, 1, f"配布ファイルを読み込めません: {error}")
        if not textbook_path.is_file():
            continue
        # Finderで開かせるので、置き場所のフォルダとファイル名が、同じSTEP（<section>）に書いてあること。
        # 教科書のどこかにあればよい、とはしない。同じフォルダのファイルを別々のSTEPで使うときに、
        # 片方のSTEPから案内が消えても、もう片方の案内で通ってしまう。
        # 置き場所は配布物の中での場所なので、リポジトリのパスをそのまま矢印でつないだ形で照合する。
        folder = " → ".join(Path(item["download"]).parent.parts)
        guided = [text for text in sections.texts if folder in text]
        if not guided:
            # 同じフォルダのファイルが何枚あっても、直す場所は1つなので1回だけ出す。
            if folder not in unguided_folders:
                unguided_folders.add(folder)
                add(errors, root, textbook_path, 1, f"配布ファイルの置き場所の案内がありません: {folder}")
        elif not any(name in text for text in guided):
            add(errors, root, textbook_path, 1, f"配布ファイルのファイル名の案内がありません: {name}（置き場所 {folder} と同じSTEPに書いてください）")


def _split_unit(name: str) -> tuple[str, str]:
    """M01HelloMonaca を ("M01", "HelloMonaca") に分ける。

    単元は2系統ある。M は Monaca系（Monaca クラウドIDE）、F は Flutter系（Visual Studio Code）。
    """
    match = UNIT_NAME.match(name)
    return (match.group(1) + match.group(2), match.group(3)) if match else (name, name)


def check_registration(root: Path, config: dict, errors: list[str]) -> None:
    """単元が設定とREADMEの両方に登録されているか確かめる。

    配布スクリプトは単元一覧を config から読むので、ここでは確かめない。
    """
    setting = config.get("registration")
    if not setting:
        return
    scan_roots = config["scan_roots"]
    # 用語ごとに、どの系統の単元へ求めるかを持つ。applies_to を書かなければ全系統に求める。
    # 「Monaca クラウドIDE」のようにMonaca系でしか使わない用語を、Flutter系の教科書にまで求めないため。
    term_requirements = [
        (term.get("applies_to"), {name for name in term.get("required_in", [])})
        for term in config["terms"]
    ]
    targets = []
    for target in setting["targets"]:
        path = root / target["path"]
        if not path.is_file():
            add(errors, root, target["path"], 1, "登録確認の対象ファイルがありません")
            continue
        targets.append((target["path"], read(path), target["requires"]))
    for project in config["projects"]:
        name = project["name"]
        if project["root"] not in scan_roots:
            add(errors, root, CONFIG.as_posix(), 1, f"{name}がscan_rootsにありません")
        # 教科書と教員用ガイドも、表記揺れの検査から漏れないようにする。
        # teacher/ は、単元が1つもないうちはフォルダごと無いので、最初の単元を足すときに scan_roots へ足す。
        for doc in project["docs"]:
            if not any(doc == item or inside(doc, item) for item in scan_roots):
                add(errors, root, CONFIG.as_posix(), 1,
                    f"{name}の{doc}が、scan_rootsのどれの下にもありません（表記揺れの検査から漏れます）")
        for applies_to, required_in in term_requirements:
            if applies_to is not None and project.get("kind") not in applies_to:
                continue
            for doc in project["docs"]:
                if doc not in required_in:
                    add(errors, root, CONFIG.as_posix(), 1, f"{name}の{doc}がterms.required_inにありません")
        paths = {
            "student_doc": project["docs"][0],
            "teacher_doc": project["docs"][1],
            "archive": project["archive"],
        }
        for shown, content, requires in targets:
            for key in requires:
                needed = paths.get(key)
                if needed is None:
                    add(errors, root, CONFIG.as_posix(), 1,
                        f"registration.targetsのrequiresに、知らない項目があります: {key}")
                elif needed not in content:
                    add(errors, root, shown, 1, f"{name}の{needed}への参照がありません")


class SidebarUnits(HTMLParser):
    """教科書のサイドバー <div class="resources"> に並ぶ単元を、出てきた順に集める。

    ほかの単元は <a href="../<単元>/index.html">、いま開いている単元は
    <span aria-current="page"> で書く。「困ったとき」や共通資料へのリンクは集めない。
    resources の外（topbarの直前の単元へのリンクなど）も集めない。
    """

    UNIT_HREF = re.compile(r"\.\./[^/?#]+/index\.html")

    def __init__(self):
        super().__init__()
        self.found = False
        self.line = 1  # <div class="resources"> の行
        self.units: list[tuple[str | None, str]] = []  # (リンク先。現在地は None, 表示名)
        self.nested: list[str] = []  # 単元の項目の中に入っていたタグ
        self._depth = 0  # resources の中にいるあいだの <div> の深さ
        self._tag: str | None = None  # いま集めている単元を開いたタグ
        self._href: str | None = None
        self._text: list[str] | None = None

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if tag == "div":
            if self._depth:
                self._depth += 1
            elif "resources" in (values.get("class") or "").split():
                if not self.found:
                    self.line = self.getpos()[0]
                self.found = True
                self._depth = 1
            return
        if not self._depth:
            return
        if self._text is not None:
            # 単元の項目は、文字だけの <a> か <span>。入れ子にすると、リンクと現在地を取り違える。
            self.nested.append(tag)
        elif tag == "a" and self.UNIT_HREF.fullmatch(values.get("href") or ""):
            self._tag, self._href, self._text = tag, values["href"], []
        elif tag == "span" and values.get("aria-current") == "page":
            self._tag, self._href, self._text = tag, None, []

    def handle_data(self, data):
        if self._text is not None:
            self._text.append(data)

    def handle_endtag(self, tag):
        if tag == "div" and self._depth:
            self._depth -= 1
        elif tag == self._tag and self._text is not None:
            self.units.append((self._href, "".join(self._text).strip()))
            self._tag = self._text = None


def check_sidebar_units(root: Path, config: dict, errors: list[str]) -> None:
    """どの教科書のサイドバーにも、全単元が projects の順で並んでいるか確かめる。

    単元を足したのに、ほかの単元のサイドバーを直し忘れる事故を捕まえる。
    いま開いている単元はリンクにせず、現在地（aria-current="page"）として示す。
    見るのは単元の並び・リンク先・表示名で、共通資料へのリンクとの位置関係は見ない。
    topbar（直前の単元へのリンク）も見ない。
    """
    projects = config["projects"]
    # サイドバーは projects の順と照合するので、projects そのものが単元番号順でなければならない。
    # 授業はMonaca系（M）を終えてからFlutter系（F）に入るので、M系→F系の順に固まって並ぶ。
    # 同じ系統の中は番号の昇順。いちどF系に移ったあとでM系に戻る並びや、F系から始まる並びは誤り。
    numbered = []
    for project in projects:
        match = UNIT_NAME.match(project["name"])
        if match:
            numbered.append((match.group(1), int(match.group(2)), project["name"]))
    for (previous_prefix, previous_number, previous_name), (prefix, number, name) in zip(numbered, numbered[1:]):
        if prefix == previous_prefix:
            out_of_order = number <= previous_number
        else:
            out_of_order = UNIT_PREFIXES.index(prefix) < UNIT_PREFIXES.index(previous_prefix)
        if out_of_order:
            add(errors, root, CONFIG.as_posix(), 1, f"projectsが単元番号順に並んでいません: {previous_name}のあとに{name}があります")
    for current in projects:
        textbook_name = current["docs"][0]
        path = root / textbook_name
        if not path.is_file():
            continue  # 教科書がないことは check_project が報告する。
        text = read(path)
        sidebar = SidebarUnits()
        sidebar.feed(text)
        if not sidebar.found:
            add(errors, root, path, 1, 'サイドバー（<div class="resources">）がありません')
            continue
        line = sidebar.line
        for tag in sidebar.nested:
            add(errors, root, path, line, f"サイドバーの単元の中に、別のタグがあります: <{tag}>")
        expected: list[tuple[str | None, str]] = []
        for unit in projects:
            number, label = _split_unit(unit["name"])
            href = None if unit is current else posixpath.relpath(
                unit["docs"][0], posixpath.dirname(textbook_name))
            expected.append((href, f"{number}：{label}"))
        if sidebar.units == expected:
            continue
        before = len(errors)
        for href, shown in expected:
            if (href, shown) in sidebar.units:
                continue
            if href is None:
                add(errors, root, path, line, f'サイドバーに現在地がありません: <span aria-current="page">{shown}</span>')
            else:
                add(errors, root, path, line, f'サイドバーに単元へのリンクがありません: <a href="{href}">{shown}</a>')
        for href, shown in sidebar.units:
            if (href, shown) in expected:
                continue
            if href and posixpath.normpath(posixpath.join(posixpath.dirname(textbook_name), href)) == textbook_name:
                add(errors, root, path, line, f"サイドバーで、いま開いている単元がリンクになっています: {shown}")
            else:
                add(errors, root, path, line, f"サイドバーに、登録のない単元があります: {shown}（{href or '現在地'}）")
        if len(errors) == before:
            # 過不足はないのに一致しない。順番が違うか、同じ単元が2回出ている。
            actual = "、".join(shown for _, shown in sidebar.units)
            add(errors, root, path, line, f"サイドバーの単元が、{CONFIG.as_posix()}のprojectsの順に並んでいません: {actual}")


def check_project_layout(root: Path, config: dict, errors: list[str]) -> None:
    """単元プロジェクトの.gitignoreと、追跡してはいけないファイルを確かめる。

    .gitignoreの基準は kind ごとに違う（Flutterは flutter create が生成したものを使い、
    Monacaはプロジェクトの直下に置かない）ので、kind → パス の辞書で書く。
    値が null の kind は、.gitignore を照合しない。基準がまだ無い系統（単元が1つもない系統）と、
    直下に .gitignore を置かない系統に使う。追跡してはいけないファイルは、null でも確かめる。
    既知の生成物は共通の除外判定で検出する。untracked_parts・untracked_names は、
    それに加えて全階層で禁止する名前だけを指定する。
    """
    setting = config.get("project_layout")
    if not setting:
        return
    reference_setting = setting["gitignore_reference"]
    if not isinstance(reference_setting, dict):
        # 文字列で書かれていたら、全kind共通の基準とみなす（参照リポジトリの書き方との後方互換）。
        reference_setting = {kind: reference_setting for kind in KINDS}
    references: dict[str, str] = {}  # kind → 基準ファイルの中身
    for kind, reference_name in sorted(reference_setting.items()):
        if reference_name is None:
            continue
        reference_path = root / reference_name
        if reference_path.is_file():
            references[kind] = read(reference_path)
        else:
            add(errors, root, reference_name, 1, ".gitignoreの基準ファイルがありません")
    parts = set(setting.get("untracked_parts", []))
    names = set(setting.get("untracked_names", []))
    checked: set[str] = set()
    for project in config["projects"]:
        kind = project.get("kind")
        if kind not in KINDS:
            continue  # kindの誤りは check_project が報告する。
        project_root = project["root"]
        if project_root in checked:
            continue  # 1つのプロジェクトを、複数の単元で育てることがある。同じ指摘を単元の数だけ出さない。
        checked.add(project_root)
        path = root / project_root / ".gitignore"
        if kind not in reference_setting:
            add(errors, root, CONFIG.as_posix(), 1,
                f"project_layout.gitignore_referenceに{kind}の基準がありません（照合しないならnullと書きます）")
        elif reference_setting[kind] is None:
            pass  # この系統は照合しない。
        elif not path.is_file():
            add(errors, root, path, 1, ".gitignoreがありません")
        elif kind in references and read(path) != references[kind]:
            add(errors, root, path, 1, f"{reference_setting[kind]}と内容が異なります")
        for name in tracked_files(root, project_root):
            tracked = Path(name)
            relative = tracked.relative_to(project_root)
            if (excluded_project_path(relative, kind)
                    or parts.intersection(relative.parts) or tracked.name in names):
                add(errors, root, name, 1, "Git管理してはいけないファイルです")


# 教科書の本文に出してはいけない語。完成プロジェクトの存在や置き場所を知らせることになる。
# release-student-materials.py の SAMPLE_GUIDANCE_WORDS も同じ語にする。
SAMPLE_GUIDANCE_WORDS = ("完成プロジェクト", "samples")
SAMPLE_GUIDANCE_RULE = "README「授業用教科書の基本方針」13"
# href・src の値。二重引用符でも単一引用符でも拾う。
LINK_ATTRIBUTE = re.compile(r"""\b(?:href|src)\s*=\s*(?:"([^"]*)"|'([^']*)')""")
TAG = re.compile(r"<[^>]*>")


def check_no_sample_guidance(root: Path, config: dict, errors: list[str]) -> None:
    """教科書（docs/ のHTML）から完成プロジェクトへ案内していないか確かめる（#168）。

    完成プロジェクトは学生用ZIPに同梱する（samples/ と docs/<スラッグ>/downloads/ のZIP）が、
    教科書からは案内しない（README「授業用教科書の基本方針」13）。次のどれかがあれば落とす。
    - 本文（タグの外）の SAMPLE_GUIDANCE_WORDS。属性の中（画像のファイル名など）は本文ではないので見ない。
    - 完成プロジェクトZIP（projects[].archive）へのリンク。文言にかかわらず落とす。
    - 教員が公開した取り込み用URL（projects[].import_url）。リンクでも本文でも落とす。
      学生が自分で発行する提出用のURLの形（directimport?pid=…）は、説明に要るので落とさない。
    タグが2行にまたがっても行番号がずれないよう、タグはその中の改行だけを残して消す。
    """
    docs = root / "docs"
    if not docs.is_dir():
        return
    archives = {project["archive"] for project in config["projects"]
                if isinstance(project.get("archive"), str) and project["archive"]}
    import_urls = sorted({project["import_url"] for project in config["projects"]
                          if isinstance(project.get("import_url"), str) and project["import_url"]})
    for path in sorted(docs.rglob("*.html")):
        if any(part in IGNORED_PARTS for part in path.relative_to(root).parts):
            continue
        name = display(root, path)
        try:
            text = read(path)
        except (OSError, UnicodeDecodeError):
            continue
        body = TAG.sub(lambda match: "\n" * match.group(0).count("\n"), text)
        for line_number, line in enumerate(body.splitlines(), 1):
            line = html.unescape(line)
            for word in SAMPLE_GUIDANCE_WORDS:
                if word in line:
                    add(errors, root, path, line_number,
                        f"教科書から完成プロジェクトへは案内しません（{SAMPLE_GUIDANCE_RULE}）: {word}")
        for match in LINK_ATTRIBUTE.finditer(text):
            value = match.group(1) if match.group(1) is not None else match.group(2)
            target = re.split(r"[?#]", html.unescape(value), maxsplit=1)[0]
            if not target:
                continue
            if "://" in target:
                archive_names = {posixpath.basename(a) for a in archives}
                if posixpath.basename(target) in archive_names:
                    add(errors, root, path, text.count("\n", 0, match.start()) + 1,
                        f"教科書から完成プロジェクトZIPへリンクしています（{SAMPLE_GUIDANCE_RULE}）: {value}")
                continue
            resolved = posixpath.normpath(posixpath.join(posixpath.dirname(name), target))
            if resolved in archives:
                add(errors, root, path, text.count("\n", 0, match.start()) + 1,
                    f"教科書から完成プロジェクトZIPへリンクしています（{SAMPLE_GUIDANCE_RULE}）: {value}")
        unescaped = html.unescape(text)
        for url in import_urls:
            if url in text or url in unescaped:
                found = text if url in text else unescaped
                add(errors, root, path, found.count("\n", 0, found.index(url)) + 1,
                    f"教科書に、先生が公開した取り込み用のURL（import_url）があります（{SAMPLE_GUIDANCE_RULE}）: {url}")


class ProgressKey(HTMLParser):
    """<body> の data-progress-key と、ページ内の data-check の数を数える。"""

    def __init__(self):
        super().__init__()
        self.key: str | None = None
        self.checks = 0
        self.body_line = 1

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if tag == "body":
            self.key = values.get("data-progress-key")
            self.body_line = self.getpos()[0]
        if "data-check" in values:
            self.checks += 1


def check_progress_keys(root: Path, errors: list[str]) -> None:
    """チェック欄のあるページが、自分用の記録キーを持っているか確かめる。

    キーの形は PROGRESS_KEY の正規表現 ^jec-hybrid-[a-z0-9]+(?:-[a-z0-9]+)*-v[0-9]+$
    （例 jec-hybrid-hello-monaca-v1、jec-hybrid-common-setup-v1）。
    docs/assets/textbook.js がキーを書き忘れたページの既定値を作るときも、同じ jec-hybrid- で始める。

    記録は localStorage に、ページごとのキーで入れる。docs/assets/textbook.js は、
    そのページで見つかった data-check だけを書き戻す。2つのページが同じキーを使うと、
    あとから開いたページが、もう一方のページの記録を消してしまう。
    教科書はファイルとして開く（file://）ので、Chromeでは、同じパソコンで開いたほかの授業の
    教材とも保存場所が同じになる。先頭を jec-hybrid- に決めておくのは、ほかの授業の教材の
    docs/common/setup.html などと記録が混ざらないようにするためである。
    キーを書き忘れると textbook.js がパスから既定値を作るので消えはしないが、
    教材の置き場所が変わると記録も変わる。チェック欄を置くなら明示させる。
    """
    pages = sorted((root / "docs").rglob("*.html")) if (root / "docs").is_dir() else []
    seen: dict[str, str] = {}
    for path in pages:
        if any(part in IGNORED_PARTS for part in path.relative_to(root).parts):
            continue
        parser = ProgressKey()
        try:
            parser.feed(read(path))
        except (OSError, UnicodeDecodeError):
            continue
        if not parser.checks:
            continue
        if not parser.key:
            add(errors, root, path, parser.body_line,
                'チェック欄のあるページには、<body data-progress-key="jec-hybrid-…-v1"> を書いてください')
            continue
        if not PROGRESS_KEY.fullmatch(parser.key):
            add(errors, root, path, parser.body_line,
                f"data-progress-keyの形が違います: {parser.key}"
                "（jec-hybrid-<スラッグ>-v1 のように、小文字の英数字とハイフンで書いてください）")
            continue
        shown = display(root, path)
        if parser.key in seen:
            add(errors, root, path, parser.body_line,
                f"data-progress-keyが{seen[parser.key]}と同じです: {parser.key}（ページごとに変えてください）")
        else:
            seen[parser.key] = shown


def validate(root: Path) -> list[str]:
    config_path = root / CONFIG
    if not config_path.is_file():
        return [f"{CONFIG}:1: 設定ファイルがありません"]
    try:
        config = json.loads(read(config_path))
    except (OSError, json.JSONDecodeError) as error:
        return [f"{CONFIG}:1: 設定ファイルを読み込めません: {error}"]
    # 必須のキーが無いまま先へ進むとトレースバックになる。日本語のエラーにして引き返す。
    missing = check_config(config)
    if missing:
        return missing
    errors: list[str] = []
    check_course(root, config, errors)
    check_terms(root, config, errors)
    check_registration(root, config, errors)
    check_sidebar_units(root, config, errors)
    check_project_layout(root, config, errors)
    check_progress_keys(root, errors)
    check_no_sample_guidance(root, config, errors)
    check_diff_registration(root, config, errors)
    for project in config["projects"]:
        check_project(root, project, errors)
        check_mirrors(root, project, errors)
        check_diffs(root, project, errors)
        check_downloads(root, project, errors)
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument(
        "--print-diff", nargs=2, metavar=("HTML", "ID"),
        help="検査の代わりに、diffsに登録した差分ブロックのHTMLを、直す前後のファイルから作って表示する"
             "（例: --print-diff docs/stamp-board/index.html diff-02-main-dart）")
    parser.add_argument("--context", type=int, default=3,
                        help="--print-diff で、変わる行の前後に付ける、すでにある行の数（既定は3）")
    args = parser.parse_args()
    if args.print_diff:
        return print_diff(args.root.resolve(), args.print_diff[0], args.print_diff[1], args.context)
    errors = validate(args.root.resolve())
    if errors:
        print("教材整合性チェック: NG", file=sys.stderr)
        print("\n".join(errors), file=sys.stderr)
        return 1
    print("教材整合性チェック: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
