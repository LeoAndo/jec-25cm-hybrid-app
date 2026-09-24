"""配布物の境界、リンク切れ、GitHub公開の失敗・再実行を検証する。"""

import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
from shutil import copy2
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from zipfile import ZipFile


SCRIPTS = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("release", SCRIPTS / "release-student-materials.py")
release = importlib.util.module_from_spec(spec)
spec.loader.exec_module(release)
spec = importlib.util.spec_from_file_location("packager", SCRIPTS / "package-student-materials.py")
packager = importlib.util.module_from_spec(spec)
spec.loader.exec_module(packager)

# JSTでは翌日になる時刻。配布物の名前が版タグと同じJSTの日付になることを確かめる。
FIXTURE_COMMITTED = "2026-09-19T15:30:00+00:00"
FIXTURE_STEM = "hybrid-app-student-materials-2026-09-20"

# 仮のリポジトリに置く「教材整合性チェック」。終了コードだけを決められるようにしている。
# 本物の scripts/check-teaching-materials.py の中身は scripts/test_check_teaching_materials.py が
# 受け持つ。ここで確かめたいのは「配布物を作る前に必ず検査を実行し、落ちたらZIPを作らない」ことだけで、
# 配布物のテストはリンク切れなど、整合性チェックも嫌がる壊れ方をわざと作るため、本物は使わない。
INTEGRITY_CHECK = '''"""テスト用：教材整合性チェックの代わり。"""

import sys

print("教材整合性チェック: テスト用", file=sys.stderr)
raise SystemExit({status})
'''

# 単元の一覧は config/teaching-materials.json から読む。M01とM02は同じ M01HelloMonaca を育てる
# （MonacaのFreeプランはプロジェクトを3個までしか持てない）ので、完成プロジェクトZIPを作る組は
# 「M01HelloMonaca」と「F01HelloFlutter」の2つになる。
FIXTURE_PROJECTS = [
    {
        "name": "M01HelloMonaca",
        "kind": "monaca",
        "root": "M01HelloMonaca",
        "app_id": "jp.ac.jec.m01hellomonaca",
        "entry": "M01HelloMonaca/www/index.html",
        "sessions": 2,
        "docs": ["docs/hello-monaca/index.html", "teacher/hello-monaca/index.html"],
        "sources": ["M01HelloMonaca/www/index.html", "M01HelloMonaca/www/js/app.js"],
        "snippets": [],
        "archive": "docs/hello-monaca/downloads/M01HelloMonaca.zip",
    },
    {
        "name": "M02TapCounter",
        "kind": "monaca",
        "root": "M01HelloMonaca",
        "app_id": "jp.ac.jec.m01hellomonaca",
        "entry": "M01HelloMonaca/www/index.html",
        "sessions": 2,
        "docs": ["docs/tap-counter/index.html", "teacher/tap-counter/index.html"],
        "sources": ["M01HelloMonaca/www/js/app.js"],
        "snippets": [],
        "archive": "docs/hello-monaca/downloads/M01HelloMonaca.zip",
    },
    {
        "name": "F01HelloFlutter",
        "kind": "flutter",
        "root": "F01HelloFlutter",
        "package_name": "f01_hello_flutter",
        "application_id": "jp.ac.jec.f01_hello_flutter",
        "entry": "F01HelloFlutter/lib/main.dart",
        "sessions": 2,
        "docs": ["docs/hello-flutter/index.html", "teacher/hello-flutter/index.html"],
        "sources": ["F01HelloFlutter/lib/main.dart"],
        "snippets": [],
        "archive": "docs/hello-flutter/downloads/F01HelloFlutter.zip",
    },
]


def page(title, body):
    """仮の教科書。翻訳したHTMLは<body>の中に導線を差し込むので、断片ではなく1枚の文書にする。"""
    return ('<!doctype html><html lang="ja"><head><meta charset="utf-8">'
            f'<title>{title}</title></head><body><main>{body}</main></body></html>')


class PackageStudentMaterialsTest(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        (self.root / "scripts").mkdir()
        for script in ("package-project.py", "package-student-materials.py", "localize-student-materials.py",
                       "project_files.py"):
            copy2(SCRIPTS / script, self.root / "scripts" / script)
        self.set_integrity_check(0)
        (self.root / "config").mkdir()
        config = json.loads((SCRIPTS.parent / "config/i18n.json").read_text(encoding="utf-8"))
        for language in config["languages"]:
            language["distribute"] = False
        (self.root / "config/i18n.json").write_text(json.dumps(config, ensure_ascii=False), encoding="utf-8")
        self.set_projects(FIXTURE_PROJECTS)
        for name, text in {
            "docs/common/setup.html": page("はじめの準備", '<a href="../hello-monaca/index.html">第1単元へ</a>'),
            "docs/hello-monaca/index.html": page("M01 HelloMonaca",
                                                 '<a href="downloads/M01HelloMonaca.zip">完成プロジェクト</a>'
                                                 '<a href="../common/setup.html">はじめの準備</a>'),
            "docs/hello-monaca/downloads/M01HelloMonaca.zip": "stale ZIP",
            "docs/tap-counter/index.html": page("M02 TapCounter",
                                                '<a href="../hello-monaca/downloads/M01HelloMonaca.zip">完成プロジェクト</a>'),
            "docs/hello-flutter/index.html": page("F01 HelloFlutter",
                                                  '<a href="downloads/F01HelloFlutter.zip">完成プロジェクト</a>'),
            "docs/hello-flutter/downloads/F01HelloFlutter.zip": "stale ZIP",
            "docs/.DS_Store": "finder settings",
            "teacher/hello-monaca/index.html": "teacher only",
            "M01HelloMonaca/config.xml": '<widget xmlns="http://www.w3.org/ns/widgets" id="jp.ac.jec.m01hellomonaca"/>\n',
            "M01HelloMonaca/www/index.html": "<!DOCTYPE html>\n<p id=\"txt_message\"></p>\n",
            "M01HelloMonaca/www/js/app.js": "const txtMessage = document.getElementById('txt_message');\n",
            "M01HelloMonaca/node_modules/cordova/index.js": "local install",
            "M01HelloMonaca/.idea/misc.xml": "IDE settings",
            "F01HelloFlutter/pubspec.yaml": "name: f01_hello_flutter\n",
            "F01HelloFlutter/lib/main.dart": "void main() {}\n",
            # 実行権限のあるファイル。配布物まで権限を引き継ぐことを確かめる。
            "F01HelloFlutter/tool/setup.sh": "#!/bin/sh",
            "F01HelloFlutter/.dart_tool/package_config.json": "build output",
            "F01HelloFlutter/build/app/outputs/app.apk": "build output",
            "F01HelloFlutter/android/local.properties": "local SDK",
        }.items():
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
        (self.root / "F01HelloFlutter/tool/setup.sh").chmod(0o755)
        self.git("init")
        self.git("add", "-f", ".")
        self.git(
            "-c", "user.name=Test", "-c", "user.email=test@example.invalid", "commit", "-m", "fixture",
            env={"GIT_AUTHOR_DATE": FIXTURE_COMMITTED, "GIT_COMMITTER_DATE": FIXTURE_COMMITTED},
        )
        self.archive = self.root / f"dist/{FIXTURE_STEM}.zip"

    def set_integrity_check(self, status):
        """教材整合性チェックの代わりを、指定の終了コードで置き直す。"""
        (self.root / "scripts/check-teaching-materials.py").write_text(
            INTEGRITY_CHECK.format(status=status), encoding="utf-8")

    def set_projects(self, projects):
        (self.root / "config/teaching-materials.json").write_text(
            json.dumps({"course": {"name": "ハイブリッドアプリ開発技法", "total_sessions": 15, "minutes_per_session": 90},
                        "scan_roots": [], "terms": [], "projects": projects}, ensure_ascii=False),
            encoding="utf-8",
        )

    def git(self, *args, env=None):
        return subprocess.run(
            ["git", *args], cwd=self.root, check=True, capture_output=True,
            env={**os.environ, **env} if env else None,
        )

    def package(self):
        return subprocess.run([sys.executable, "scripts/package-student-materials.py"], cwd=self.root, capture_output=True, text=True)

    def enable_translation(self):
        path = self.root / "config/i18n.json"
        config = json.loads(path.read_text(encoding="utf-8"))
        config["languages"][0]["distribute"] = True
        path.write_text(json.dumps(config, ensure_ascii=False), encoding="utf-8")
        (self.root / "docs/assets").mkdir()
        for name in ("textbook.js", "textbook.css"):
            copy2(SCRIPTS.parent / "docs/assets" / name, self.root / "docs/assets" / name)
        source = ('<!doctype html><html lang="ja"><head><title>はじめの準備</title>'
                  '<link rel="stylesheet" href="../assets/textbook.css">'
                  '<script src="../assets/textbook.js" defer></script></head>'
                  '<body data-progress-key="jec-test-v1"><main><section id="step1"><h1>日本語の見出し</h1>'
                  '<p>訳した文</p><p>未翻訳の文<strong>も残す</strong></p>'
                  '<a href="downloads/M01HelloMonaca.zip">完成プロジェクト</a>'
                  '<input type="checkbox" data-check="step1"><pre><code>日本語のコード</code></pre>'
                  '</section></main></body></html>')
        (self.root / "docs/hello-monaca/index.html").write_text(source, encoding="utf-8")
        catalog = self.root / "i18n/en/hello-monaca/index.json"
        catalog.parent.mkdir(parents=True)
        catalog.write_text(json.dumps({"source": "docs/hello-monaca/index.html", "language": "en",
                                      "entries": [{"source": "訳した文", "translation": "Translated sentence"}]}, ensure_ascii=False),
                           encoding="utf-8")
        self.git("add", "docs/assets", "docs/hello-monaca/index.html", "i18n/en/hello-monaca/index.json", "config/i18n.json")

    def test_asset_stem_is_hybrid_app_student_materials(self):
        """配布ZIPの名前は授業ごとに決まっている。リリース側の検査と組で守る。"""
        self.assertEqual(packager.ASSET_STEM, "hybrid-app-student-materials")
        self.assertEqual(self.package().returncode, 0)
        self.assertTrue(self.archive.exists(), self.archive)

    def test_shared_project_is_packaged_once(self):
        """同じ完成プロジェクトを指す単元が複数あっても、ZIPは1回だけ作る。

        M01・M02 が同じ M01HelloMonaca を育てるときは、重複を除かないと
        同じZIPを何度も作り直すことになる。
        """
        calls = []
        run = subprocess.run

        def record(command, *args, **kwargs):
            calls.append([str(part) for part in command])
            return run(command, *args, **kwargs)

        with patch.object(packager, "ROOT", self.root.resolve()), patch.object(packager.subprocess, "run", record):
            packager.build(self.root / "dist")
        packaged = [call for call in calls if any("package-project.py" in part for part in call)]
        self.assertEqual([call[call.index("--project") + 1] for call in packaged],
                         ["M01HelloMonaca", "F01HelloFlutter"])

    def test_instructions_list_every_registered_unit(self):
        """はじめに.txt の単元一覧は config/teaching-materials.json から作る。"""
        self.assertEqual(self.package().returncode, 0)
        with ZipFile(self.archive) as archive:
            instructions = archive.read(f"{FIXTURE_STEM}/はじめに.txt").decode()
        self.assertIn("ハイブリッドアプリ開発技法 学生用教材", instructions)
        self.assertIn("  M01 HelloMonaca：docs/hello-monaca/index.html", instructions)
        self.assertIn("  M02 TapCounter：docs/tap-counter/index.html", instructions)
        self.assertIn("  F01 HelloFlutter：docs/hello-flutter/index.html", instructions)
        self.assertIn("Visual Studio Code", instructions)
        self.assertIn("取り込み用のURL", instructions)
        for word in ("Kotlin", "IntelliJ IDEA", "Android Studio"):
            self.assertNotIn(word, instructions)

    def test_instructions_open_a_flutter_sample_as_the_folder_example(self):
        """「File > Open Folder…」の例は、先頭のMonacaの見本ではなく、最初のFlutterの見本にする。"""
        self.assertEqual(self.package().returncode, 0)
        with ZipFile(self.archive) as archive:
            instructions = archive.read(f"{FIXTURE_STEM}/はじめに.txt").decode()
        self.assertIn("「File > Open Folder…」で samples/F01HelloFlutter のように", instructions)
        self.assertNotIn("samples/M01HelloMonaca のように", instructions)

    def test_sample_example_without_flutter_unit(self):
        """Flutterの単元がまだないうちは、例のフォルダ名を決めつけない。"""
        self.assertEqual(packager.sample_example(FIXTURE_PROJECTS[:2]), "samples/<プロジェクト名>")
        self.assertEqual(packager.sample_example(FIXTURE_PROJECTS), "samples/F01HelloFlutter")

    def test_added_unit_appears_without_touching_the_script(self):
        """単元を設定に足すだけで、配布物の案内にも見本にも反映される。"""
        added = dict(FIXTURE_PROJECTS[0], name="M03Stopwatch",
                     docs=["docs/stopwatch/index.html", "teacher/stopwatch/index.html"])
        self.set_projects([*FIXTURE_PROJECTS[:2], added, FIXTURE_PROJECTS[2]])
        textbook = self.root / "docs/stopwatch/index.html"
        textbook.parent.mkdir(parents=True)
        textbook.write_text(page("M03 Stopwatch",
                                 '<a href="../hello-monaca/downloads/M01HelloMonaca.zip">完成プロジェクト</a>'),
                            encoding="utf-8")
        self.git("add", "config/teaching-materials.json", "docs/stopwatch/index.html")
        self.assertEqual(self.package().returncode, 0)
        with ZipFile(self.archive) as archive:
            instructions = archive.read(f"{FIXTURE_STEM}/はじめに.txt").decode()
        self.assertIn("  M03 Stopwatch：docs/stopwatch/index.html", instructions)

    def test_missing_project_archive_rejects_package(self):
        """教科書を配るのに完成プロジェクトZIPがない単元を見つける。"""
        self.git("rm", "--cached", "docs/hello-flutter/downloads/F01HelloFlutter.zip")
        result = self.package()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("HelloFlutterの完成プロジェクトが見つかりません", result.stderr)
        self.assertFalse(self.archive.exists())

    def test_integrity_check_failure_stops_packaging(self):
        """教材整合性チェックが落ちたら、配布物を書き出さない。"""
        self.set_integrity_check(1)
        result = self.package()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("教材のパッケージ化に失敗しました", result.stderr)
        self.assertFalse(self.archive.exists())

    def test_distributed_language_has_static_navigation_and_shared_assets(self):
        self.enable_translation()
        result = self.package()
        self.assertEqual(result.returncode, 0, result.stderr)
        prefix = f"{FIXTURE_STEM}/"
        with ZipFile(self.archive) as archive:
            names = archive.namelist()
            english = archive.read(prefix + "docs/en/hello-monaca/index.html").decode()
            japanese = archive.read(prefix + "docs/hello-monaca/index.html").decode()
            entrance = archive.read(prefix + "index.html").decode()
            instructions = archive.read(prefix + "はじめに.txt").decode()
            self.assertIn('href="../../hello-monaca/index.html"', english)
            self.assertIn('href="../en/hello-monaca/index.html"', japanese)
            self.assertIn('data-language-link', english)
            self.assertIn('hreflang="ja"', english)
            self.assertIn('translated by AI', english)
            self.assertIn('Japanese version is authoritative', english)
            self.assertIn('ask your teacher', english)
            self.assertIn('data-progress-key="jec-test-v1"', english)
            self.assertIn('"progress": "{count} / {total} steps checked"', english)
            self.assertIn('<p>Translated sentence</p>', english)
            self.assertIn('<span lang="ja">未翻訳の文<strong>も残す</strong></span>', english)
            self.assertIn('<title lang="ja">はじめの準備</title>', english)
            self.assertIn('<pre><code>日本語のコード</code></pre>', english)
            self.assertIn('href="../../hello-monaca/downloads/M01HelloMonaca.zip"', english)
            self.assertIn('src="../../assets/textbook.js"', english)
            # 入口は共通資料。言語を選んだ先が「はじめの準備」になる。
            self.assertIn('href="docs/en/common/setup.html"', entrance)
            self.assertIn('ハイブリッドアプリ開発技法 / Hybrid App Development', entrance)
            self.assertIn('Open index.html in your browser, then choose English.', instructions)
            self.assertFalse(any('/docs/en/' in name and not name.endswith('.html') for name in names))
            self.assertFalse(any('/docs/ko/' in name for name in names))

    def test_all_supported_languages_have_their_own_ui_and_shared_pages(self):
        self.enable_translation()
        path = self.root / "config/i18n.json"
        config = json.loads(path.read_text(encoding="utf-8"))
        for language in config["languages"]:
            language["distribute"] = True
        path.write_text(json.dumps(config, ensure_ascii=False), encoding="utf-8")
        result = self.package()
        self.assertEqual(result.returncode, 0, result.stderr)
        prefix = f"{FIXTURE_STEM}/"
        with ZipFile(self.archive) as archive:
            for language in config["languages"]:
                page = archive.read(prefix + f"docs/{language['code']}/hello-monaca/index.html").decode()
                # 右から左の言語だけ、ページ全体と、日本語のまま残す部分に向きを付ける。
                rtl = language.get("dir") == "rtl"
                page_dir, japanese_dir = (' dir="rtl"', ' dir="ltr"') if rtl else ("", "")
                self.assertIn(f'<html lang="{language["code"]}"{page_dir}>', page)
                # 注記、UIと全言語の導線はカタログの有無に左右されない。
                self.assertIn(language['translation_notice'], page)
                self.assertIn(language['ui']['copy'], page)
                self.assertEqual(page.count('hreflang='), len(config['languages']) + 1)
                self.assertIn(f'<span lang="ja"{japanese_dir}>未翻訳の文', page)
                # 言語の切り替えでは、どのページでも、言語名をその言語の向きで出す。
                nav = page.split('<nav class="language-nav"', 1)[1].split("</nav>", 1)[0]
                for choice in config["languages"]:
                    direction = choice.get("dir", "ltr")
                    self.assertIn(f'lang="{choice["code"]}" dir="{direction}"', nav)
                self.assertIn('lang="ja" dir="ltr"', nav)
            entrance = archive.read(prefix + "index.html").decode()
            self.assertIn('<li lang="ja" dir="ltr">', entrance)
            for language in config["languages"]:
                self.assertIn(f'<li lang="{language["code"]}" dir="{language.get("dir", "ltr")}">', entrance)
        # アラビア語は右から左の言語として設定してある（この検査で右から左の出力を必ず通すため）。
        self.assertIn("rtl", [language.get("dir") for language in config["languages"]])

    def test_translation_does_not_include_untracked_pages(self):
        self.enable_translation()
        (self.root / 'docs/draft.html').write_text('<p>書きかけ', encoding="utf-8")
        result = self.package()
        self.assertEqual(result.returncode, 0, result.stderr)
        with ZipFile(self.archive) as archive:
            self.assertFalse(any('draft.html' in name for name in archive.namelist()))

    def test_localized_links_are_checked(self):
        self.enable_translation()
        generate = packager.add_localized_materials

        def with_broken_link(files):
            languages = generate(files)
            files["docs/en/hello-monaca/index.html"] += b'<a href="missing.html">broken</a>'
            return languages

        # 日本語にはない壊れたリンクが生成されたときも、ZIPを書き出してはいけない。
        with patch.object(packager, "ROOT", self.root.resolve()), patch.object(packager, "add_localized_materials", with_broken_link):
            with self.assertRaisesRegex(ValueError, 'docs/en/hello-monaca/index.html → missing.html'):
                packager.build(self.root / "dist")
        self.assertFalse(self.archive.exists())

    def test_no_distributed_language_preserves_original_html_and_entrypoints(self):
        original = (self.root / "docs/hello-monaca/index.html").read_bytes()
        result = self.package()
        self.assertEqual(result.returncode, 0, result.stderr)
        prefix = f"{FIXTURE_STEM}/"
        with ZipFile(self.archive) as archive:
            self.assertNotIn(prefix + 'index.html', archive.namelist())
            self.assertEqual(archive.read(prefix + 'docs/hello-monaca/index.html'), original)
            self.assertNotIn(b'Language /', archive.read(prefix + 'はじめに.txt'))
            self.assertFalse(any('/docs/en/' in name for name in archive.namelist()))

    def test_student_contents_regeneration_and_repeatable_zip(self):
        (self.root / "docs/untracked.txt").write_text("not for distribution", encoding="utf-8")
        edited = "const txtMessage = document.getElementById('txt_message');\ntxtMessage.textContent = 'こんにちは';\n"
        (self.root / "M01HelloMonaca/www/js/app.js").write_text(edited, encoding="utf-8")
        result = self.package()
        self.assertEqual(result.returncode, 0, result.stderr)
        prefix = f"{FIXTURE_STEM}/"
        with ZipFile(self.archive) as archive:
            names = archive.namelist()
            self.assertFalse(any("teacher" in name or ".DS_Store" in name or "untracked" in name for name in names))
            self.assertIn(prefix + "はじめに.txt", names)
            self.assertIn(prefix + "VERSION.json", names)
            data = archive.read(prefix + "docs/hello-monaca/downloads/M01HelloMonaca.zip")
            with ZipFile(io.BytesIO(data)) as project:
                self.assertEqual(project.read("M01HelloMonaca/www/js/app.js").decode(), edited)
                self.assertFalse(any(".idea" in name or "node_modules" in name for name in project.namelist()))
            data = archive.read(prefix + "docs/hello-flutter/downloads/F01HelloFlutter.zip")
            with ZipFile(io.BytesIO(data)) as project:
                self.assertFalse(any(part in name for name in project.namelist()
                                     for part in (".dart_tool", "/build/", "local.properties")))
                self.assertEqual(project.getinfo("F01HelloFlutter/tool/setup.sh").external_attr >> 16, 0o100755)
        first = self.archive.read_bytes()
        self.assertEqual(self.package().returncode, 0)
        self.assertEqual(self.archive.read_bytes(), first)
        checksum = (self.root / "dist/SHA256SUMS.txt").read_text(encoding="utf-8")
        self.assertEqual(checksum.split()[0], hashlib.sha256(first).hexdigest())

    def test_extracted_samples_match_the_project_zip(self):
        self.assertEqual(self.package().returncode, 0)
        prefix = f"{FIXTURE_STEM}/"
        bundled_total = 0
        with ZipFile(self.archive) as archive:
            for archive_name in ("docs/hello-monaca/downloads/M01HelloMonaca.zip",
                                 "docs/hello-flutter/downloads/F01HelloFlutter.zip"):
                data = archive.read(prefix + archive_name)
                with ZipFile(io.BytesIO(data)) as project:
                    # 展開済みの見本は、教科書からリンクしているZIPと同じ中身。
                    # Flutterの見本は、Visual Studio Code の「File > Open Folder…」で選ぶだけで開ける。
                    for item in project.infolist():
                        sample = archive.getinfo(prefix + "samples/" + item.filename)
                        self.assertEqual(archive.read(sample), project.read(item))
                        self.assertEqual(sample.external_attr >> 16, item.external_attr >> 16)
                    bundled_total += len(project.namelist())
            bundled = [name for name in archive.namelist() if name.startswith(prefix + "samples/")]
            self.assertEqual(len(bundled), bundled_total)
            # 配布物の書き出しは権限を644にそろえるが、実行権限のあるファイルは権限を引き継ぐ。
            self.assertEqual(archive.getinfo(prefix + "samples/F01HelloFlutter/tool/setup.sh").external_attr >> 16, 0o100755)
            self.assertEqual(archive.getinfo(prefix + "samples/M01HelloMonaca/www/js/app.js").external_attr >> 16, 0o100644)
            # Monacaの見本とFlutterの見本が、samples/ の中で別々のフォルダに入る。
            self.assertIn(prefix + "samples/M01HelloMonaca/www/index.html", bundled)
            self.assertIn(prefix + "samples/F01HelloFlutter/lib/main.dart", bundled)

    def test_generated_directory_names_do_not_remove_materials_or_samples(self):
        """完成ZIP・samples・教科書のどこでも、生成物と同名の正規ファイルは残る。"""
        sources = {
            "F01HelloFlutter/lib/build/screen.dart": "// 画面のソース\n",
            "F01HelloFlutter/lib/plugins/helper.dart": "// アプリのソース\n",
            "M01HelloMonaca/www/plugins/app.js": "// アプリのソース\n",
        }
        textbook = "docs/build/index.html"
        for name, content in {**sources, textbook: page("ビルド", "<p>教材</p>")}.items():
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
        self.git("add", "-f", *sources, textbook)
        result = self.package()
        self.assertEqual(result.returncode, 0, result.stderr)
        prefix = f"{FIXTURE_STEM}/"
        with ZipFile(self.archive) as archive:
            self.assertIn(prefix + textbook, archive.namelist())
            for name, content in sources.items():
                self.assertEqual(archive.read(prefix + "samples/" + name).decode(), content)
                archive_name = ("docs/hello-flutter/downloads/F01HelloFlutter.zip"
                                if name.startswith("F") else "docs/hello-monaca/downloads/M01HelloMonaca.zip")
                with ZipFile(io.BytesIO(archive.read(prefix + archive_name))) as project:
                    self.assertEqual(project.read(name).decode(), content)

    def test_asset_name_and_folder_carry_the_release_date(self):
        self.assertEqual(self.package().returncode, 0)
        with ZipFile(self.archive) as archive:
            names = archive.namelist()
        # 別の版を同じ場所に展開しても混ざらないよう、先頭フォルダにも日付を入れる。
        self.assertTrue(all(name.startswith(f"{FIXTURE_STEM}/") for name in names), names)
        checksum = (self.root / "dist/SHA256SUMS.txt").read_text(encoding="utf-8")
        self.assertEqual(checksum.split()[1], self.archive.name)
        metadata = json.loads((self.root / "dist/release-metadata.json").read_text(encoding="utf-8"))
        self.assertEqual(metadata["asset"], self.archive.name)
        # 版タグの日付と、配布物の名前の日付がそろっている。
        self.assertEqual(metadata["version"].rsplit("-", 1)[0], "materials-2026.09.20")

    def test_missing_link_rejects_package(self):
        (self.root / "docs/hello-monaca/index.html").write_text('<a href="../missing.html">資料</a>', encoding="utf-8")
        result = self.package()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("リンク先がありません", result.stderr)
        self.assertFalse(self.archive.exists())

    def test_link_to_teacher_rejects_package(self):
        (self.root / "docs/hello-monaca/index.html").write_text('<a href="../../teacher/hello-monaca/index.html">教員用</a>', encoding="utf-8")
        self.assertNotEqual(self.package().returncode, 0)

    def test_symlink_rejects_package(self):
        (self.root / "docs/private.txt").symlink_to(self.root / "teacher/hello-monaca/index.html")
        self.git("add", "docs/private.txt")
        result = self.package()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("シンボリックリンク", result.stderr)


class StudentReleaseTest(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.dist = Path(temporary.name)
        self.repo = "owner/repo"
        self.asset = "hybrid-app-student-materials-2026-09-15.zip"
        self.metadata = {"version": "materials-2026.09.15-123456789abc", "revision": "123456789abc" * 3 + "1234", "asset": self.asset}
        (self.dist / self.asset).write_bytes(b"student package")
        (self.dist / release.CHECKSUMS).write_text(f"{hashlib.sha256(b'student package').hexdigest()}  {self.asset}\n")
        (self.dist / "release-notes.md").write_text("学生向けノート", encoding="utf-8")
        # リリースノートの単元一覧も設定から作る。ほかの単元の作業と混ざらないよう、仮の設定を使う。
        self.source = self.dist / "source"
        (self.source / "config").mkdir(parents=True)
        (self.source / "config/teaching-materials.json").write_text(
            json.dumps({"projects": FIXTURE_PROJECTS}, ensure_ascii=False), encoding="utf-8")
        self.enterContext(patch.object(release, "ROOT", self.source))
        self.enterContext(patch.object(release, "DIST", self.dist))
        self.enterContext(patch.dict(os.environ, {"GITHUB_EVENT_NAME": "workflow_dispatch", "GITHUB_REF": "refs/heads/main", "STUDENT_NOTES": "STEP 4の説明修正。やり直し不要。", "ALLOW_UNTRANSLATED": "false"}))
        self.summary = self.enterContext(patch.object(release, "summary"))
        self.translations = self.enterContext(patch.object(release, "translation_report", return_value=[]))
        self.gh = self.enterContext(patch.object(release, "gh", return_value=""))
        self.items = self.enterContext(patch.object(release, "releases", return_value=[]))
        self.api = self.enterContext(patch.object(release, "api", side_effect=self.api_response))

    def api_response(self, path, payload=None):
        if path.endswith("/commits/main"):
            return {"sha": self.metadata["revision"]}
        if "/git/matching-refs/" in path:
            return []
        if path.endswith("/generate-notes"):
            return {"body": "* M01HelloMonacaの説明を修正 #2"}
        raise AssertionError(f"Unexpected API: {path}")

    def incomplete_report(self):
        return [{"language": {"code": "en", "name": "English", "distribute": True}, "rows": [
            {"page": "docs/hello-monaca/index.html", "total": 4, "translated": 1},
            {"page": "docs/common/setup.html", "total": 2, "translated": 1},
        ]}]

    def test_asset_pattern_matches_this_course_only(self):
        """配布ZIPの名前が、この授業のものであることを確かめる。"""
        self.assertTrue(release.ASSET_PATTERN.fullmatch(self.asset))
        self.assertFalse(release.ASSET_PATTERN.fullmatch("kotlin-student-materials-2026-09-15.zip"))
        self.assertFalse(release.ASSET_PATTERN.fullmatch("hybrid-app-student-materials-2026-09-15.zip.bak"))

    def test_release_notes_list_units_from_the_configuration(self):
        """リリースノートの単元一覧は config/teaching-materials.json から作る。"""
        with patch.object(release.subprocess, "check_output", return_value="- 修正 (abc123)"):
            release.prepare(self.repo, self.metadata)
        text = (self.dist / "release-notes.md").read_text(encoding="utf-8")
        self.assertIn(f"# ハイブリッドアプリ開発技法 教材 {self.metadata['version']}", text)
        self.assertIn("- `M01 HelloMonaca：docs/hello-monaca/index.html`", text)
        self.assertIn("- `M02 TapCounter：docs/tap-counter/index.html`", text)
        self.assertIn("- `F01 HelloFlutter：docs/hello-flutter/index.html`", text)
        # 「File > Open Folder…」の例は、先頭のMonacaの見本ではなく、最初のFlutterの見本にする。
        self.assertIn("「File > Open Folder…」で `samples/F01HelloFlutter`", text)
        self.assertIn("取り込み用のURL", text)
        for word in ("Kotlin", "IntelliJ IDEA", "Android Studio"):
            self.assertNotIn(word, text)

    def test_release_notes_without_units_say_so(self):
        """単元が1つもないうちも、リリースノートは作れる。"""
        (self.source / "config/teaching-materials.json").write_text(json.dumps({"projects": []}), encoding="utf-8")
        with patch.object(release.subprocess, "check_output", return_value=""):
            release.prepare(self.repo, self.metadata)
        text = (self.dist / "release-notes.md").read_text(encoding="utf-8")
        self.assertIn("   - （教科書はまだありません）", text)
        self.assertIn("`samples/<プロジェクト名>`", text)
        self.assertIn("見本）を含む版には、`samples` フォルダがあります", text)
        self.assertNotIn("見本）は、`samples` フォルダに入っています", text)

    def test_release_notes_follow_in_class_setup_schedule(self):
        """共通準備で全環境と初回実行を一度に済ませる旧案内へ戻さない。"""
        with patch.object(release.subprocess, "check_output", return_value=""):
            release.prepare(self.repo, self.metadata)
        text = (self.dist / "release-notes.md").read_text(encoding="utf-8")
        for instruction in (
            "第1コマにSTEP 1〜3", "第7コマにSTEP 4〜7を開始", "第8コマでも確認を続けます",
            "ダウンロードも授業時間内", "初回実行は単元の教科書",
        ):
            self.assertIn(instruction, text)
        self.assertNotIn("はじめてのアプリが動くまでを説明", text)

    def test_download_guidance_covers_every_configured_language(self):
        """翻訳を配る言語を増やしたときに、公開案内の書き忘れを見つける。"""
        config = json.loads((SCRIPTS.parent / "config/i18n.json").read_text(encoding="utf-8"))
        self.assertEqual(sorted(release.DOWNLOAD_GUIDANCE),
                         sorted(language["code"] for language in config["languages"]))

    def test_untranslated_publish_stops_before_release_mutation(self):
        self.translations.return_value = self.incomplete_report()
        with self.assertRaisesRegex(ValueError, "未翻訳が4文"):
            release.publish(self.repo, self.metadata)
        self.gh.assert_not_called()
        report = self.summary.call_args.args[0]
        self.assertIn("en（English） | `docs/hello-monaca/index.html` | 3", report)
        self.assertIn("en（English） | `docs/common/setup.html` | 1", report)

    def test_emergency_publish_records_actual_counts_without_duplicates(self):
        self.translations.return_value = self.incomplete_report()
        with patch.dict(os.environ, {"ALLOW_UNTRANSLATED": "true"}):
            release.publish(self.repo, self.metadata)
            release.publish(self.repo, self.metadata)
        notes = (self.dist / "release-notes.md").read_text(encoding="utf-8")
        self.assertIn("公開ゲートを解除", notes)
        self.assertIn("**4文**", notes)
        self.assertIn("`docs/hello-monaca/index.html` | 3", notes)
        self.assertEqual(notes.count(release.EXCEPTION_MARKER), 1)
        self.assertIn("--draft=false", self.gh.call_args_list[-1].args)

    def test_emergency_flag_does_not_bypass_invalid_catalog(self):
        self.translations.side_effect = ValueError("対訳カタログの検査に失敗しました")
        with patch.dict(os.environ, {"ALLOW_UNTRANSLATED": "true"}):
            with self.assertRaisesRegex(ValueError, "対訳カタログ"):
                release.publish(self.repo, self.metadata)
        self.gh.assert_not_called()

    def test_false_override_still_rejects_untranslated_content(self):
        self.translations.return_value = self.incomplete_report()
        with patch.dict(os.environ, {"ALLOW_UNTRANSLATED": "false"}):
            with self.assertRaisesRegex(ValueError, "未翻訳"):
                release.publish(self.repo, self.metadata)
        self.gh.assert_not_called()

    def test_prepare_with_untranslated_content_keeps_preparation_available(self):
        self.translations.return_value = self.incomplete_report()
        with patch.object(release.subprocess, "check_output", return_value="- 修正 (abc123)"):
            release.prepare(self.repo, self.metadata)
        notes = (self.dist / "release-notes.md").read_text(encoding="utf-8")
        self.assertIn("### English", notes)
        self.assertIn("Open `index.html`", notes)
        self.assertNotIn(release.EXCEPTION_MARKER, notes)
        self.gh.assert_not_called()

    def test_prepare_emergency_notes_record_counts(self):
        self.translations.return_value = self.incomplete_report()
        with patch.dict(os.environ, {"ALLOW_UNTRANSLATED": "true"}), patch.object(release.subprocess, "check_output", return_value=""):
            release.prepare(self.repo, self.metadata)
        self.assertIn("**4文**", (self.dist / "release-notes.md").read_text(encoding="utf-8"))

    def test_right_to_left_guidance_is_wrapped_with_its_direction(self):
        """GitHubのMarkdownは段落に向きを付けないので、右から左の言語の案内だけを dir で囲む。"""
        report = [{"language": {"code": "ar", "name": "العربية", "dir": "rtl"}, "rows": []},
                  {"language": {"code": "en", "name": "English"}, "rows": []}]
        notes = release.localized_download_guidance(report, self.asset)
        arabic, english = notes.split("### English")
        self.assertTrue(arabic.startswith('<div dir="rtl">\n\n### العربية\n'), arabic)
        self.assertIn(self.asset, arabic)
        self.assertIn("</div>", arabic)
        self.assertNotIn("dir=", english)

    def test_each_distribution_language_has_native_opening_instructions(self):
        report = [{"language": {"code": code, "name": code}, "rows": []} for code in release.DOWNLOAD_GUIDANCE]
        notes = release.localized_download_guidance(report, self.asset)
        self.assertEqual(notes.count("`index.html`"), len(release.DOWNLOAD_GUIDANCE))
        self.assertEqual(notes.count(self.asset), len(release.DOWNLOAD_GUIDANCE))

    def test_first_publish_uploads_before_publication(self):
        release.publish(self.repo, self.metadata)
        commands = [call.args[:2] for call in self.gh.call_args_list]
        self.assertEqual(commands, [("release", "create"), ("release", "upload"), ("release", "edit")])
        self.assertIn("--draft", self.gh.call_args_list[0].args)
        self.assertIn(self.metadata["revision"], self.gh.call_args_list[0].args)
        self.assertIn(f"ハイブリッドアプリ開発技法 教材 {self.metadata['version']}", self.gh.call_args_list[0].args)
        # 添付するのは版の日付が入ったZIP。名前はrelease-metadata.jsonから受け取る。
        self.assertIn(str(self.dist / self.asset), self.gh.call_args_list[1].args)
        self.assertIn("--draft=false", self.gh.call_args_list[-1].args)

    def test_upload_failure_does_not_publish(self):
        def execute(*args, **kwargs):
            if args[:2] == ("release", "upload"):
                raise subprocess.CalledProcessError(1, "upload")
            return ""
        self.gh.side_effect = execute
        with self.assertRaises(subprocess.CalledProcessError):
            release.publish(self.repo, self.metadata)
        self.assertFalse(any("--draft=false" in call.args for call in self.gh.call_args_list))

    def test_existing_draft_resumes_without_creating_another(self):
        self.items.return_value = [{"tag_name": self.metadata["version"], "draft": True, "target_commitish": self.metadata["revision"]}]
        release.publish(self.repo, self.metadata)
        self.assertEqual([call.args[:2] for call in self.gh.call_args_list], [("release", "edit"), ("release", "upload"), ("release", "edit")])

    def test_published_release_is_not_overwritten(self):
        self.items.return_value = [{"tag_name": self.metadata["version"], "draft": False, "html_url": "https://github.com/owner/repo/releases/tag/materials-test"}]
        release.publish(self.repo, self.metadata)
        self.gh.assert_not_called()

    def test_main_changed_stops_before_mutation(self):
        self.api.side_effect = lambda *args: {"sha": "different revision"}
        with self.assertRaisesRegex(ValueError, "mainが更新"):
            release.publish(self.repo, self.metadata)
        self.gh.assert_not_called()

    def test_main_changed_during_upload_keeps_release_as_draft(self):
        def execute(*args, **kwargs):
            if args[:2] == ("release", "upload"):
                self.api.side_effect = lambda *args: {"sha": "updated during upload"}
            return ""
        self.gh.side_effect = execute
        with self.assertRaisesRegex(ValueError, "下書きの公開を中止"):
            release.publish(self.repo, self.metadata)
        self.assertEqual([call.args[:2] for call in self.gh.call_args_list], [("release", "create"), ("release", "upload")])

    def test_automatic_event_cannot_publish(self):
        with patch.dict(os.environ, {"GITHUB_EVENT_NAME": "push"}):
            with self.assertRaisesRegex(ValueError, "Run workflow"):
                release.publish(self.repo, self.metadata)
        self.gh.assert_not_called()

    def test_corrupt_package_cannot_publish(self):
        (self.dist / self.asset).write_bytes(b"corrupt package")
        with self.assertRaisesRegex(ValueError, "チェックサム"):
            release.publish(self.repo, self.metadata)
        self.gh.assert_not_called()

    def test_prepare_first_release_has_student_notes_and_direct_commits(self):
        with patch.object(release.subprocess, "check_output", return_value="- 直接修正 (abc123)"):
            release.prepare(self.repo, self.metadata)
        text = (self.dist / "release-notes.md").read_text(encoding="utf-8")
        self.assertIn(f"**{self.asset}**", text)
        self.assertIn("STEP 4の説明修正。やり直し不要。", text)
        self.assertIn("M01HelloMonacaの説明を修正 #2", text)
        self.assertIn("直接修正", text)
        payload = self.api.call_args.args[1]
        self.assertEqual(payload["target_commitish"], self.metadata["revision"])
        # APIはリポジトリ内のパスを読む。モックでは見逃す設定ファイルの欠落を検出する。
        self.assertTrue((SCRIPTS.parent / payload["configuration_file_path"]).is_file())
        self.assertNotIn("previous_tag_name", payload)
        self.gh.assert_not_called()

    def test_previous_release_ignores_drafts_prereleases_and_other_products(self):
        def item(tag, date, **kwargs):
            return {"tag_name": tag, "published_at": date, "draft": False, "prerelease": False, **kwargs}
        previous = item("materials-previous", "2026-09-14")
        items = [previous, item("other-product", "2026-09-15"), item("materials-draft", None, draft=True), item("materials-preview", "2026-09-15", prerelease=True), item(self.metadata["version"], "2026-09-15")]
        self.assertEqual(release.previous_release(items, self.metadata["version"]), previous)

    def test_notes_compare_against_last_published_materials(self):
        self.items.return_value = [{"tag_name": "materials-previous", "published_at": "2026-09-14", "draft": False, "prerelease": False}]
        base = "a" * 40
        self.api.side_effect = [{"sha": base}, {"body": "前回からのPR一覧"}]
        with patch.object(release.subprocess, "run") as ancestry, patch.object(release.subprocess, "check_output", return_value="- 追加修正 (def456)") as log:
            release.prepare(self.repo, self.metadata)
        payload = self.api.call_args.args[1]
        self.assertEqual(payload["previous_tag_name"], "materials-previous")
        self.assertEqual(log.call_args.args[0][-1], f"{base}..{self.metadata['revision']}")
        self.assertEqual(ancestry.call_args.args[0], ["git", "merge-base", "--is-ancestor", base, self.metadata["revision"]])

    def test_conflicting_tag_stops_before_mutation(self):
        self.api.side_effect = [
            {"sha": self.metadata["revision"]},
            [{"ref": f"refs/tags/{self.metadata['version']}"}],
            {"sha": "different revision"},
        ]
        with self.assertRaisesRegex(ValueError, "タグが別のコミット"):
            release.publish(self.repo, self.metadata)
        self.gh.assert_not_called()


class TranslationReleaseGateTest(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        for directory in ("scripts", "config", "docs", "i18n/en"):
            (self.root / directory).mkdir(parents=True, exist_ok=True)
        copy2(SCRIPTS / "localize-student-materials.py", self.root / "scripts/localize-student-materials.py")
        self.config = {"source_language": "ja", "source_root": "docs", "catalog_root": "i18n", "languages": [
            {"code": "en", "name": "English", "distribute": True},
            {"code": "ko", "name": "한국어", "distribute": False},
        ]}
        (self.root / "config/i18n.json").write_text(json.dumps(self.config, ensure_ascii=False), encoding="utf-8")
        (self.root / "docs/index.html").write_text('<html lang="ja"><p>準備します。</p></html>', encoding="utf-8")
        self.enterContext(patch.object(release, "ROOT", self.root))
        self.enterContext(patch.dict(os.environ, {"ALLOW_UNTRANSLATED": "false"}))

    def test_report_uses_only_languages_included_in_distribution(self):
        report = release.translation_report()
        self.assertEqual([item["language"]["code"] for item in report], ["en"])
        self.assertEqual(release.missing_translations(report), 1)

    def test_translated_distribution_ignores_untranslated_disabled_language(self):
        (self.root / "i18n/en/index.json").write_text(json.dumps({
            "source": "docs/index.html", "language": "en",
            "entries": [{"source": "準備します。", "translation": "Get ready."}],
        }, ensure_ascii=False), encoding="utf-8")
        with patch.object(release, "summary"):
            self.assertEqual(release.missing_translations(release.check_translation_gate()), 0)

    def test_changed_japanese_source_returns_to_untranslated(self):
        (self.root / "i18n/en/index.json").write_text(json.dumps({
            "source": "docs/index.html", "language": "en",
            "entries": [{"source": "準備します。", "translation": "Get ready."}],
        }, ensure_ascii=False), encoding="utf-8")
        (self.root / "docs/index.html").write_text('<html lang="ja"><p>アプリを起動します。</p></html>', encoding="utf-8")
        with patch.object(release, "summary"):
            with self.assertRaisesRegex(ValueError, "未翻訳が1文"):
                release.check_translation_gate()

    def test_missing_counts_are_written_to_github_summary_by_page(self):
        target = self.root / "summary.md"
        with patch.dict(os.environ, {"GITHUB_STEP_SUMMARY": str(target)}):
            with self.assertRaisesRegex(ValueError, "未翻訳が1文"):
                release.check_translation_gate()
        self.assertIn("en（English） | `docs/index.html` | 1", target.read_text(encoding="utf-8"))

    def test_emergency_override_does_not_skip_html_structure_check(self):
        (self.root / "docs/index.html").write_text('<html lang="ja"><p>準備します。</html>', encoding="utf-8")
        with patch.dict(os.environ, {"ALLOW_UNTRANSLATED": "true"}):
            with self.assertRaisesRegex(ValueError, "検査に失敗"):
                release.check_translation_gate()

    def test_emergency_override_does_not_skip_malformed_catalog(self):
        (self.root / "i18n/en/index.json").write_text('{broken', encoding="utf-8")
        with patch.dict(os.environ, {"ALLOW_UNTRANSLATED": "true"}):
            with self.assertRaisesRegex(ValueError, "検査に失敗"):
                release.check_translation_gate()


if __name__ == "__main__":
    unittest.main()
