"""教材整合性検査の回帰テスト。

このリポジトリの単元は2系統ある。Monaca系（kind: monaca。Monaca クラウドIDEで作る
config.xml＋www/ のプロジェクト）と、Flutter系（kind: flutter。Visual Studio Code で作る
pubspec.yaml＋lib/ のプロジェクト）である。どちらも検査できることを確かめる。

ここで確かめるのは検査そのものの動きで、tempfile で仮のリポジトリを組み立てて試す。
このリポジトリ自身が整合しているかは `python3 scripts/check-teaching-materials.py` が見る
（CIの validate ジョブとREADMEの検証コマンドに入っている）ので、ここでは重ねて見ない。
"""

import html
import importlib.util
import json
from pathlib import Path
from shutil import copy2
import subprocess
import sys
import tempfile
import unittest
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo


SCRIPT = Path(__file__).with_name("check-teaching-materials.py")
SPEC = importlib.util.spec_from_file_location("check_teaching_materials", SCRIPT)
CHECKER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CHECKER)
PACKAGER = Path(__file__).with_name("package-project.py")


class ScriptImportTest(unittest.TestCase):
    def test_project_helper_loads_outside_repository(self):
        """CLIとimportlibのどちらでも、cwdやテスト探索時のsys.pathに依存しない。"""
        loader = (
            "import importlib.util, sys; "
            "spec = importlib.util.spec_from_file_location('under_test', sys.argv[1]); "
            "module = importlib.util.module_from_spec(spec); "
            "spec.loader.exec_module(module)"
        )
        with tempfile.TemporaryDirectory() as outside:
            for script in (SCRIPT, PACKAGER):
                for mode in ("cli", "importlib"):
                    with self.subTest(script=script.name, mode=mode):
                        args = ([str(script.resolve()), "--help"] if mode == "cli"
                                else ["-c", loader, str(script.resolve())])
                        result = subprocess.run(
                            [sys.executable, "-I", *args], cwd=outside,
                            capture_output=True, text=True,
                        )
                        self.assertEqual(result.returncode, 0, result.stderr)


class TeachingMaterialsCheckTest(unittest.TestCase):
    # 系統ごとの正式表記。Monaca系とFlutter系で、使う道具の名前が違う。
    IDE = "Monaca クラウドIDE"
    EDITOR = "Visual Studio Code"
    IMPORT_URL = "https://monaca.mobi/ja/directimport?pid=0123456789abcdef0123456789abcdef"

    MONACA_CONFIG_XML = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<widget xmlns="http://www.w3.org/ns/widgets" id="jp.ac.jec.m01hellomonaca" version="1.0.0">\n'
        "  <name>はじめてのMonaca</name>\n"
        '  <content src="index.html"/>\n'
        "</widget>\n"
    )
    MONACA_PACKAGE_JSON = '{\n  "name": "m01hellomonaca",\n  "version": "1.0.0"\n}\n'
    MONACA_HTML = (
        "<!DOCTYPE html>\n<html>\n<head>\n"
        '  <meta charset="utf-8">\n'
        '  <script src="js/app.js" defer></script>\n'
        "</head>\n<body>\n"
        '  <button id="btn_hello">あいさつ</button>\n'
        '  <p id="txt_message"></p>\n'
        "</body>\n</html>\n"
    )
    MONACA_JS = (
        "// ボタンを押したら、画面の文字を書き換える。\n"
        "const btnHello = document.getElementById('btn_hello');\n"
        "btnHello.addEventListener('click', function () {\n"
        "  document.getElementById('txt_message').textContent = 'こんにちは';\n"
        "});\n"
    )
    PUBSPEC = (
        "name: f01_hello_flutter\n"
        'description: "はじめてのFlutter"\n'
        "publish_to: 'none'\n"
        "version: 1.0.0+1\n\n"
        "environment:\n  sdk: ^3.11.0\n\n"
        "dependencies:\n  flutter:\n    sdk: flutter\n"
    )
    FLUTTER_GRADLE = (
        "android {\n"
        '    namespace = "jp.ac.jec.f01_hello_flutter"\n'
        "    defaultConfig {\n"
        '        applicationId = "jp.ac.jec.f01_hello_flutter"\n'
        "    }\n"
        "}\n"
    )
    APP_DELEGATE = "import Flutter\nimport UIKit\n"
    # < と ' を含む。教科書にはHTMLのエスケープをして載せるので、それでも一致することを確かめる。
    DART_SOURCE = (
        "import 'package:flutter/material.dart';\n\n"
        "const greetings = <String>['こんにちは'];\n\n"
        "void main() {\n  runApp(const MainApp());\n}\n\n"
        "class MainApp extends StatelessWidget {\n"
        "  const MainApp({super.key});\n\n"
        "  @override\n"
        "  Widget build(BuildContext context) {\n"
        "    return MaterialApp(home: Scaffold(body: Center(child: Text(greetings.first))));\n"
        "  }\n"
        "}\n"
    )
    # config/teaching-materials.json と同じ、追跡してはいけないもの。
    UNTRACKED_PARTS = [".idea"]
    UNTRACKED_NAMES = [".DS_Store"]
    MONACA_IGNORE = "node_modules/\nplatforms/\nplugins/\n"
    FLUTTER_IGNORE = ".dart_tool/\nbuild/\n.flutter-plugins-dependencies\n"

    # 仮のリポジトリに置く単元。_repository の kinds で、どちらを置くか選ぶ。
    UNITS = {
        "monaca": {
            "name": "M01HelloMonaca", "folder": "hello-monaca", "tool": IDE,
            "snippet": ("code-final-app", "M01HelloMonaca/www/js/app.js"),
        },
        "flutter": {
            "name": "F01HelloFlutter", "folder": "hello-flutter", "tool": EDITOR,
            "snippet": ("code-final-main", "F01HelloFlutter/lib/main.dart"),
        },
    }

    # ------------------------------------------------------------------
    # 仮のリポジトリを組み立てる道具
    # ------------------------------------------------------------------

    def _write(self, root: Path, name: str, text: str) -> Path:
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def _write_config(self, root: Path, config: dict) -> None:
        """検査に必要な設定ファイルを書き出す。"""
        (root / "config").mkdir(exist_ok=True)
        (root / "config/teaching-materials.json").write_text(
            json.dumps(config, ensure_ascii=False), encoding="utf-8"
        )

    def _read_config(self, root: Path) -> dict:
        return json.loads((root / "config/teaching-materials.json").read_text(encoding="utf-8"))

    def _minimal_config(self, root: Path, projects: list[dict], **extra) -> None:
        """見たい検査だけが動く、最小の設定を書き出す。

        course も registration も project_layout も書かないので、それらの検査は動かない。
        """
        config = {"scan_roots": [], "terms": [], "projects": projects}
        config.update(extra)
        self._write_config(root, config)

    def _project(self, **overrides) -> dict:
        """Monaca系の単元の設定。既定は第1単元（M01HelloMonaca）の形。"""
        project = {
            "name": "M01HelloMonaca",
            "kind": "monaca",
            "root": "M01HelloMonaca",
            "app_id": "jp.ac.jec.m01hellomonaca",
            "entry": "M01HelloMonaca/www/index.html",
            "sessions": 1,
            "docs": ["docs/hello-monaca/index.html", "teacher/hello-monaca/index.html"],
            "sources": ["M01HelloMonaca/www/index.html", "M01HelloMonaca/www/js/app.js"],
            "snippets": [],
            "archive": "docs/hello-monaca/downloads/M01HelloMonaca.zip",
        }
        project.update(overrides)
        return project

    def _flutter_project(self, **overrides) -> dict:
        """Flutter系の単元の設定。既定は F01HelloFlutter の形。

        フォルダ名は単元名、Dartのパッケージ名は小文字とアンダースコア（flutter create --project-name）。
        """
        project = {
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
        }
        project.update(overrides)
        return project

    def _git_add(self, root: Path, *paths: str, force: bool = False) -> None:
        """完成プロジェクトZIPの検査は git ls-files を使うので、Gitの索引を作る。"""
        subprocess.run(["git", "init"], cwd=root, check=True, capture_output=True)
        subprocess.run(["git", "add", *(["-f"] if force else []), *paths],
                       cwd=root, check=True, capture_output=True)

    def _archive(self, root: Path, name: str, members: list[str]) -> Path:
        """完成プロジェクトZIPを、scripts/package-project.py と同じ形で作る。"""
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        with ZipFile(path, "w", compression=ZIP_DEFLATED) as archive:
            for member in members:
                source = root / member
                info = ZipInfo(member, date_time=(1980, 1, 1, 0, 0, 0))
                info.create_system = 3
                executable = bool(source.stat().st_mode & 0o100)
                info.external_attr = (0o100755 if executable else 0o100644) << 16
                info.compress_type = ZIP_DEFLATED
                archive.writestr(info, source.read_bytes())
        return path

    def _textbook(self, name: str, units: list[tuple[str, str]], current: str,
                  snippet: tuple[str, str] | None = None, tool: str = "", extra: str = "") -> str:
        """教科書HTMLのうち、検査に関わる部分だけを持つページを作る。

        units は (フォルダ名, 単元名) の一覧。current はいま開いている単元のフォルダ名。
        """
        entries = []
        for folder, unit_name in units:
            shown = f"{unit_name[:3]}：{unit_name[3:]}"
            if folder == current:
                entries.append(f'<span aria-current="page">{shown}</span>')
            else:
                entries.append(f'<a href="../{folder}/index.html">{shown}</a>')
        code = ""
        if snippet:
            snippet_id, source = snippet
            code = f'<pre id="{snippet_id}"><code>{html.escape(source)}</code></pre>'
        return (
            '<!doctype html><html lang="ja"><body>'
            f"<main><h1>{name}</h1><p>{tool} で開きます。</p>{extra}{code}</main>"
            '<aside class="sidebar"><div class="resources"><a href="#help">困ったとき</a>'
            + "".join(entries)
            + f'<a href="../common/setup.html?from={current}">共通：はじめの準備</a>'
            "</div></aside></body></html>"
        )

    def _teacher_doc(self, name: str, tool: str, extra: str = "") -> str:
        return (
            '<!doctype html><html lang="ja"><body><main>'
            f"<h1>{name} 教員用ガイド</h1>"
            f"<p>{tool} で開きます。</p>{extra}"
            "</main></body></html>"
        )

    def _readme(self, *paths: str) -> str:
        """コマ数の表記と、単元へのリンクを持つREADMEを作る。"""
        body = "".join(f"- {path}\n" for path in paths)
        return (
            "# ハイブリッドアプリ開発技法 — 授業用教材\n\n"
            "1コマ90分・全15コマ（計画は仮）。\n\n" + body
        )

    def _write_monaca(self, root: Path, name: str = "M01HelloMonaca",
                      config_xml: str | None = None) -> list[str]:
        """Monacaの完成プロジェクト（config.xml・package.json・www/）を書き出し、そのパスを返す。"""
        files = {
            f"{name}/config.xml": config_xml or self.MONACA_CONFIG_XML,
            f"{name}/package.json": self.MONACA_PACKAGE_JSON,
            f"{name}/www/index.html": self.MONACA_HTML,
            f"{name}/www/js/app.js": self.MONACA_JS,
        }
        for path, text in files.items():
            self._write(root, path, text)
        return sorted(files)

    def _write_flutter(self, root: Path, name: str = "F01HelloFlutter",
                       pubspec: str | None = None, gradle: str | None = None) -> list[str]:
        """Flutterの完成プロジェクト（pubspec.yaml・android/・ios/・lib/）を書き出し、そのパスを返す。"""
        files = {
            f"{name}/pubspec.yaml": pubspec or self.PUBSPEC,
            f"{name}/android/app/build.gradle.kts": gradle or self.FLUTTER_GRADLE,
            f"{name}/ios/Runner/AppDelegate.swift": self.APP_DELEGATE,
            f"{name}/lib/main.dart": self.DART_SOURCE,
        }
        for path, text in files.items():
            self._write(root, path, text)
        return sorted(files)

    def _unit_textbook(self, kind: str, kinds: tuple[str, ...], extra: str = "") -> str:
        unit = self.UNITS[kind]
        snippet_id, source = unit["snippet"]
        source_text = self.MONACA_JS if kind == "monaca" else self.DART_SOURCE
        return self._textbook(
            unit["name"], [(self.UNITS[item]["folder"], self.UNITS[item]["name"]) for item in kinds],
            unit["folder"], snippet=(snippet_id, source_text), tool=unit["tool"], extra=extra)

    def _repository(self, root: Path, kinds: tuple[str, ...] = ("monaca",),
                    config_xml: str | None = None, pubspec: str | None = None,
                    gradle: str | None = None) -> dict:
        """検査を通る最小のリポジトリを作る。kinds に、置く単元の系統を授業の順に並べる。

        書き出した完成プロジェクトのファイルは self.files[kind] に残す（ZIPを作り直すときに使う）。
        """
        self.files: dict[str, list[str]] = {}
        projects, terms, readme = [], [], []
        scan_roots = ["README.md", "docs", "teacher"]
        for kind in kinds:
            unit = self.UNITS[kind]
            name, folder = unit["name"], unit["folder"]
            if kind == "monaca":
                files = self._write_monaca(root, config_xml=config_xml)
            else:
                files = self._write_flutter(root, pubspec=pubspec, gradle=gradle)
            self.files[kind] = files
            self._git_add(root, name)
            docs = [f"docs/{folder}/index.html", f"teacher/{folder}/index.html"]
            archive = f"docs/{folder}/downloads/{name}.zip"
            self._write(root, docs[0], self._unit_textbook(kind, kinds))
            self._write(root, docs[1], self._teacher_doc(name, unit["tool"]))
            self._archive(root, archive, files)
            readme.extend([*docs, archive])
            scan_roots.append(name)
            snippet_id, source = unit["snippet"]
            snippets = [{"html": docs[0], "id": snippet_id, "source": source}]
            if kind == "monaca":
                projects.append(self._project(snippets=snippets))
                terms.append({"name": "MonacaのクラウドIDE", "canonical": self.IDE,
                              "forbidden": ["Monaca Cloud IDE"], "applies_to": ["monaca"],
                              "required_in": docs})
            else:
                projects.append(self._flutter_project(snippets=snippets))
                terms.append({"name": "Flutterのエディタ", "canonical": self.EDITOR,
                              "forbidden": ["VSCode"], "applies_to": ["flutter"],
                              "required_in": docs})
        self._write(root, "README.md", self._readme(*readme))
        config = {
            "course": {"name": "ハイブリッドアプリ開発技法", "total_sessions": 15, "minutes_per_session": 90},
            "scan_roots": scan_roots,
            "terms": terms,
            "registration": {"targets": [
                {"path": "README.md", "requires": ["student_doc", "teacher_doc", "archive"]},
            ]},
            "project_layout": {
                "gitignore_reference": {"monaca": None, "flutter": None},
                "untracked_parts": self.UNTRACKED_PARTS,
                "untracked_names": self.UNTRACKED_NAMES,
            },
            "projects": projects,
        }
        self._write_config(root, config)
        return config

    def _update_project(self, root: Path, index: int = 0, **changes) -> None:
        """書き出した設定の単元を1つ書き換える。値に None を渡したキーは消す。"""
        config = self._read_config(root)
        for key, value in changes.items():
            if value is None:
                config["projects"][index].pop(key, None)
            else:
                config["projects"][index][key] = value
        self._write_config(root, config)

    # ------------------------------------------------------------------
    # Monaca系（kind: monaca）
    # ------------------------------------------------------------------

    def test_monaca_project_is_accepted(self):
        """Monaca系の単元が、ひと通りそろっていれば何も言わない。"""
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._repository(root)
            self.assertEqual(CHECKER.validate(root), [])

    def test_monaca_app_id_mismatch_is_rejected(self):
        """config.xml の <widget id> が、設定の app_id と違えば検出する。"""
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._repository(root, config_xml=self.MONACA_CONFIG_XML.replace(
                "jp.ac.jec.m01hellomonaca", "com.example.helloworld"))
            errors = CHECKER.validate(root)
            self.assertEqual(len(errors), 1, errors)
            self.assertIn("M01HelloMonaca/config.xml:2", errors[0])
            self.assertIn("<widget>のidが一致しません: 'com.example.helloworld' != "
                          "'jp.ac.jec.m01hellomonaca'", errors[0])

    def test_monaca_config_xml_without_namespace_is_rejected(self):
        """名前空間のない config.xml は、Monacaの形ではないので検出する。"""
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._repository(root, config_xml=self.MONACA_CONFIG_XML.replace(
                ' xmlns="http://www.w3.org/ns/widgets"', ""))
            errors = CHECKER.validate(root)
            self.assertEqual(len(errors), 1, errors)
            self.assertIn("M01HelloMonaca/config.xml:2", errors[0])
            self.assertIn("名前空間 http://www.w3.org/ns/widgets の<widget>ではありません: widget", errors[0])

    def test_broken_config_xml_is_rejected(self):
        """XMLとして読めない config.xml は、トレースバックにせず日本語で報告する。"""
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._repository(root, config_xml='<widget id="jp.ac.jec.m01hellomonaca">\n')
            errors = CHECKER.validate(root)
            self.assertEqual(len(errors), 1, errors)
            self.assertIn("M01HelloMonaca/config.xml:1", errors[0])
            self.assertIn("config.xmlを読み込めません", errors[0])

    def test_missing_config_xml_is_rejected(self):
        """config.xml が無いプロジェクトは、Monacaへ取り込めないので検出する。"""
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._write(root, "M01HelloMonaca/www/index.html", self.MONACA_HTML)
            self._minimal_config(root, [self._project(sources=["M01HelloMonaca/www/index.html"])])
            errors = [error for error in CHECKER.validate(root) if "config.xml" in error]
            self.assertEqual(len(errors), 1, errors)
            self.assertIn("M01HelloMonaca/config.xml:1: config.xmlがありません", errors[0])

    def test_monaca_entry_outside_www_is_rejected(self):
        """entry は www/ の下。Monacaがアプリとして読むのは www/ の中だけ。"""
        for entry in ("M01HelloMonaca/index.html", "M01HelloMonaca/www/../config.xml"):
            with self.subTest(entry=entry), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                self._repository(root)
                self._update_project(root, entry=entry)
                errors = CHECKER.validate(root)
                self.assertEqual(len(errors), 1, errors)
                self.assertIn("config/teaching-materials.json:1", errors[0])
                self.assertIn(f"M01HelloMonacaのentryがM01HelloMonaca/www/の下にありません: {entry}", errors[0])

    def test_monaca_missing_entry_is_rejected(self):
        """entry に書いたファイルが www/ に無ければ検出する。"""
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._repository(root)
            self._update_project(root, entry="M01HelloMonaca/www/start.html")
            errors = CHECKER.validate(root)
            self.assertEqual(len(errors), 1, errors)
            self.assertIn("M01HelloMonaca/www/start.html:1: entryに書いたファイルがありません", errors[0])

    def test_monaca_source_outside_www_is_rejected(self):
        """Monacaの完成コードは www/ の下に置く。config.xml を載せる単元でも sources には入れない。"""
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._repository(root)
            self._update_project(root, sources=[
                "M01HelloMonaca/www/index.html", "M01HelloMonaca/config.xml"])
            errors = CHECKER.validate(root)
            self.assertEqual(len(errors), 1, errors)
            self.assertIn("M01HelloMonaca/config.xml:1", errors[0])
            self.assertIn("Monacaの完成コードがM01HelloMonaca/www/の下にありません", errors[0])

    def test_import_url_in_textbook_is_accepted(self):
        """取り込み用のURLが学生用の教科書に載っていれば、何も言わない。"""
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._repository(root)
            link = f'<p><a href="{html.escape(self.IMPORT_URL)}">見本を取り込む</a></p>'
            self._write(root, "docs/hello-monaca/index.html",
                        self._unit_textbook("monaca", ("monaca",), extra=link))
            self._update_project(root, import_url=self.IMPORT_URL)
            self.assertEqual(CHECKER.validate(root), [])

    def test_import_url_missing_from_textbook_is_rejected(self):
        """設定にだけ書いて教科書に載せ忘れると、学生は見本を取り込めないので検出する。"""
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._repository(root)
            self._update_project(root, import_url=self.IMPORT_URL)
            errors = CHECKER.validate(root)
            self.assertEqual(len(errors), 1, errors)
            self.assertIn("docs/hello-monaca/index.html:1", errors[0])
            self.assertIn(f"取り込み用のURL（import_url）がありません: {self.IMPORT_URL}", errors[0])

    def test_import_url_only_in_teacher_doc_is_rejected(self):
        """URLを見るのは学生なので、教員用ガイドにだけ載っていても通さない。"""
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._repository(root)
            self._write(root, "teacher/hello-monaca/index.html",
                        self._teacher_doc("M01HelloMonaca", self.IDE, extra=f"<p>{self.IMPORT_URL}</p>"))
            self._update_project(root, import_url=self.IMPORT_URL)
            errors = CHECKER.validate(root)
            self.assertEqual(len(errors), 1, errors)
            self.assertIn("docs/hello-monaca/index.html:1", errors[0])

    def test_import_url_must_be_text(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._repository(root)
            self._update_project(root, import_url=123)
            errors = CHECKER.validate(root)
            self.assertEqual(len(errors), 1, errors)
            self.assertIn("M01HelloMonacaのimport_urlは文字列で書いてください: 123", errors[0])

    # ------------------------------------------------------------------
    # Flutter系（kind: flutter）
    # ------------------------------------------------------------------

    def test_flutter_project_is_accepted(self):
        """Flutter系の単元が、ひと通りそろっていれば何も言わない。"""
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._repository(root, kinds=("flutter",))
            self.assertEqual(CHECKER.validate(root), [])

    def test_monaca_and_flutter_units_together_are_accepted(self):
        """M系→F系の2単元がそろったリポジトリ。サイドバーにも両方が並ぶ。"""
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._repository(root, kinds=("monaca", "flutter"))
            self.assertEqual(CHECKER.validate(root), [])

    def test_flutter_pubspec_name_mismatch_is_rejected(self):
        """pubspec.yaml の name が、設定の package_name と違えば検出する。"""
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._repository(root, kinds=("flutter",), pubspec=self.PUBSPEC.replace(
                "name: f01_hello_flutter", "name: hello_flutter"))
            errors = CHECKER.validate(root)
            self.assertEqual(len(errors), 1, errors)
            self.assertIn("F01HelloFlutter/pubspec.yaml:1", errors[0])
            self.assertIn("pubspec.yamlのnameが一致しません: 'hello_flutter' != 'f01_hello_flutter'", errors[0])

    def test_flutter_pubspec_name_with_quotes_and_comment_is_accepted(self):
        """YAMLとして正しい書き方（引用符・行末のコメント）なら、同じ名前として読む。"""
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._repository(root, kinds=("flutter",), pubspec=self.PUBSPEC.replace(
                "name: f01_hello_flutter", "name: 'f01_hello_flutter'  # Dartのパッケージ名"))
            self.assertEqual(CHECKER.validate(root), [])

    def test_flutter_pubspec_reads_only_the_top_level_name(self):
        """字下げした name: は、パッケージ名ではないので読まない。"""
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._repository(root, kinds=("flutter",), pubspec=self.PUBSPEC.replace(
                "name: f01_hello_flutter\n", "app:\n  name: f01_hello_flutter\n"))
            errors = CHECKER.validate(root)
            self.assertEqual(len(errors), 1, errors)
            self.assertIn("pubspec.yamlのnameが一致しません: None != 'f01_hello_flutter'", errors[0])

    def test_flutter_application_id_mismatch_is_rejected(self):
        """namespace と applicationId が設定の application_id と違えば検出する。"""
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._repository(root, kinds=("flutter",), gradle=self.FLUTTER_GRADLE.replace(
                "jp.ac.jec.f01_hello_flutter", "com.example.f01_hello_flutter"))
            errors = CHECKER.validate(root)
            self.assertEqual(len(errors), 2, errors)
            self.assertIn("F01HelloFlutter/android/app/build.gradle.kts:2", errors[0])
            self.assertIn("namespaceが一致しません: 'com.example.f01_hello_flutter' != "
                          "'jp.ac.jec.f01_hello_flutter'", errors[0])
            self.assertIn("F01HelloFlutter/android/app/build.gradle.kts:4", errors[1])
            self.assertIn("applicationIdが一致しません", errors[1])

    def test_flutter_missing_gradle_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._write(root, "F01HelloFlutter/pubspec.yaml", self.PUBSPEC)
            self._minimal_config(root, [self._flutter_project()])
            errors = [error for error in CHECKER.validate(root) if "build.gradle.kts" in error]
            self.assertEqual(len(errors), 1, errors)
            self.assertIn("F01HelloFlutter/android/app/build.gradle.kts:1: "
                          "android/app/build.gradle.ktsがありません", errors[0])

    def test_flutter_missing_pubspec_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._write(root, "F01HelloFlutter/lib/main.dart", self.DART_SOURCE)
            self._minimal_config(root, [self._flutter_project()])
            errors = [error for error in CHECKER.validate(root) if "pubspec.yaml" in error]
            self.assertEqual(len(errors), 1, errors)
            self.assertIn("F01HelloFlutter/pubspec.yaml:1: pubspec.yamlがありません", errors[0])

    def test_flutter_unsupported_platform_folder_is_rejected(self):
        """web/・macos/・linux/・windows/ があれば検出する。授業で扱うのはiOSとAndroidだけ。"""
        for platform in ("web", "macos", "linux", "windows"):
            with self.subTest(platform=platform), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                self._repository(root, kinds=("flutter",))
                # flutter create を --platforms なしで実行すると、ここにフォルダができる。
                self._write(root, f"F01HelloFlutter/{platform}/README.md", "生成されたフォルダ\n")
                errors = CHECKER.validate(root)
                self.assertEqual(len(errors), 1, errors)
                self.assertIn(f"F01HelloFlutter/{platform}:1", errors[0])
                self.assertIn(f"{platform}/があります。この授業のFlutterはiOSとAndroidだけを扱う", errors[0])

    def test_flutter_missing_platform_folder_is_rejected(self):
        """android/ と ios/ は、両方そろっていなければ検出する。"""
        for platform in ("android", "ios"):
            with self.subTest(platform=platform), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                self._write_flutter(root)
                for path in sorted((root / "F01HelloFlutter" / platform).rglob("*"), reverse=True):
                    path.rmdir() if path.is_dir() else path.unlink()
                (root / "F01HelloFlutter" / platform).rmdir()
                self._minimal_config(root, [self._flutter_project()])
                errors = [error for error in CHECKER.validate(root) if f"{platform}/がありません" in error]
                self.assertEqual(len(errors), 1, errors)
                self.assertIn(f"F01HelloFlutter/{platform}:1", errors[0])
                self.assertIn("--platforms=ios,android", errors[0])

    def test_flutter_entry_outside_lib_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._repository(root, kinds=("flutter",))
            self._update_project(root, entry="F01HelloFlutter/main.dart")
            errors = CHECKER.validate(root)
            self.assertEqual(len(errors), 1, errors)
            self.assertIn("F01HelloFlutterのentryがF01HelloFlutter/lib/の下にありません: "
                          "F01HelloFlutter/main.dart", errors[0])

    def test_flutter_dart_source_outside_lib_is_rejected(self):
        """Dartの完成コードは lib/ の下に置く。アプリになるのは lib/ の中だけ。"""
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._repository(root, kinds=("flutter",))
            self._write(root, "F01HelloFlutter/tool/greeting.dart", "void main() {}\n")
            self._update_project(root, sources=[
                "F01HelloFlutter/lib/main.dart", "F01HelloFlutter/tool/greeting.dart"])
            errors = CHECKER.validate(root)
            self.assertEqual(len(errors), 1, errors)
            self.assertIn("F01HelloFlutter/tool/greeting.dart:1", errors[0])
            self.assertIn("Dartの完成コードがF01HelloFlutter/lib/の下にありません", errors[0])

    def test_flutter_source_other_than_dart_may_be_outside_lib(self):
        """pubspec.yaml のような、Dart以外の完成コードは lib/ の外でよい。"""
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._repository(root, kinds=("flutter",))
            self._update_project(root, sources=[
                "F01HelloFlutter/lib/main.dart", "F01HelloFlutter/pubspec.yaml"])
            self.assertEqual(CHECKER.validate(root), [])

    def test_import_url_on_flutter_unit_is_rejected(self):
        """取り込み用のURLはMonacaの仕組み。Flutterの単元に書いても使われないので検出する。"""
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._repository(root, kinds=("flutter",))
            self._update_project(root, import_url=self.IMPORT_URL)
            errors = CHECKER.validate(root)
            self.assertEqual(len(errors), 1, errors)
            self.assertIn("F01HelloFlutterのimport_urlは書けません", errors[0])

    # ------------------------------------------------------------------
    # 両系統に共通の、単元の設定と完成コード
    # ------------------------------------------------------------------

    def test_unknown_kind_is_rejected(self):
        """kind は monaca か flutter のどちらかだけ。前の授業の kind も通さない。"""
        for kind in ("cordova", "android", "kotlin-console"):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                self._minimal_config(root, [self._project(kind=kind)])
                errors = [error for error in CHECKER.validate(root) if "kind" in error]
                self.assertEqual(len(errors), 1, errors)
                self.assertIn("config/teaching-materials.json:1", errors[0])
                self.assertIn(f"M01HelloMonacaのkindが不正です: '{kind}'（monacaかflutterと書いてください）",
                              errors[0])

    def test_kind_specific_setting_must_be_text(self):
        """app_id などを文字列以外で書いたら、トレースバックにせず設定エラーにする。"""
        cases = [(("monaca",), "app_id", 123), (("flutter",), "application_id", "")]
        for kinds, key, value in cases:
            with self.subTest(key=key), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                self._repository(root, kinds=kinds)
                self._update_project(root, **{key: value})
                errors = CHECKER.validate(root)
                self.assertEqual(len(errors), 1, errors)
                self.assertIn(f"の{key}は文字列で書いてください: {value!r}", errors[0])

    def test_missing_project_folder_is_reported_once(self):
        """完成プロジェクトのフォルダごと無いときは、中のファイルを1つずつ挙げない。"""
        for project in (self._project(), self._flutter_project()):
            with self.subTest(kind=project["kind"]), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                self._minimal_config(root, [project])
                errors = CHECKER.validate(root)
                folder = [error for error in errors if "完成プロジェクトのフォルダがありません" in error]
                self.assertEqual(folder, [f"{project['root']}:1: 完成プロジェクトのフォルダがありません"])
                self.assertFalse(any("config.xml" in error or "pubspec.yaml" in error
                                     or "がありません（flutter create" in error for error in errors), errors)

    def test_missing_source_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._repository(root)
            self._update_project(root, sources=[
                "M01HelloMonaca/www/index.html", "M01HelloMonaca/www/js/main.js"])
            errors = CHECKER.validate(root)
            self.assertEqual(len(errors), 1, errors)
            self.assertIn("M01HelloMonaca/www/js/main.js:1: 完成コードのファイルがありません", errors[0])

    def test_empty_sources_is_rejected(self):
        """完成コードを1つも登録していない単元は、何も検査できないので検出する。"""
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._minimal_config(root, [self._project(sources=[])])
            errors = [error for error in CHECKER.validate(root) if "sources" in error]
            self.assertEqual(len(errors), 1, errors)
            self.assertIn("config/teaching-materials.json:1", errors[0])

    def test_source_with_carriage_return_is_rejected(self):
        """完成コードの改行にCRが混ざっていたら、最初に混ざった行を挙げて検出する。

        MonacaTemplate の www/index.html はCRLFなので、そこから複製すると混ざる。
        """
        cases = [("monaca", "M01HelloMonaca/www/js/app.js", self.MONACA_JS),
                 ("flutter", "F01HelloFlutter/lib/main.dart", self.DART_SOURCE)]
        for kind, name, text in cases:
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                self._repository(root, kinds=(kind,))
                first, second, rest = text.split("\n", 2)
                (root / name).write_bytes(f"{first}\n{second}\r\n{rest}".encode("utf-8"))
                errors = [error for error in CHECKER.validate(root) if "CR" in error]
                self.assertEqual(len(errors), 1, errors)
                self.assertIn(f"{name}:2", errors[0])
                self.assertIn("LFだけにそろえてください", errors[0])

    def test_document_requires_unit_name(self):
        """教科書と教員用ガイドには、単元名の表記を求める。"""
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._repository(root)
            self._write(root, "teacher/hello-monaca/index.html", self._teacher_doc("はじめてのMonaca", self.IDE))
            errors = [error for error in CHECKER.validate(root) if "必要な表記" in error]
            self.assertEqual(len(errors), 1, errors)
            self.assertIn("teacher/hello-monaca/index.html:1", errors[0])
            self.assertIn("教材に必要な表記がありません: M01HelloMonaca", errors[0])

    # ------------------------------------------------------------------
    # コマ数（check_course）
    # ------------------------------------------------------------------

    def _course_errors(self, root: Path) -> list[str]:
        return [error for error in CHECKER.validate(root) if "コマ" in error or "sessions" in error]

    def _course_root(self, root: Path, sessions: list[int], readme: str,
                     total=15, minutes=90) -> None:
        self._write(root, "README.md", readme)
        projects = [
            self._project(
                name=f"M0{index}Unit",
                sessions=value,
                docs=[f"docs/u{index}/index.html", f"teacher/u{index}/index.html"],
                archive=f"docs/u{index}/downloads/M01HelloMonaca.zip",
            )
            for index, value in enumerate(sessions, 1)
        ]
        self._minimal_config(root, projects, course={
            "name": "ハイブリッドアプリ開発技法", "total_sessions": total, "minutes_per_session": minutes,
        })

    def test_sessions_within_total_are_accepted(self):
        """合計が全コマ数に足りないのは、まだ単元にしていないだけなので許す。"""
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._course_root(root, [1, 2], self._readme())
            self.assertEqual(self._course_errors(root), [])

    def test_units_spanning_several_sessions_up_to_the_total_are_accepted(self):
        """1つの単元が何コマにもまたがってよい。Monaca 7コマ＋Flutter 8コマでちょうど15コマ。"""
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._course_root(root, [7, 8], self._readme())
            self.assertEqual(self._course_errors(root), [])

    def test_sessions_over_total_are_rejected(self):
        """単元のコマ数の合計が、決めた全コマ数を超えたら検出する。"""
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._course_root(root, [7, 9], self._readme())
            errors = self._course_errors(root)
            self.assertEqual(len(errors), 1, errors)
            self.assertIn("config/teaching-materials.json:1", errors[0])
            self.assertIn("course.total_sessionsの15コマを超えています: 16コマ", errors[0])

    def test_sessions_must_be_positive_integer(self):
        for value in (0, True, "2"):
            with self.subTest(value=value), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                self._course_root(root, [value], self._readme())
                errors = self._course_errors(root)
                self.assertEqual(len(errors), 1, errors)
                self.assertIn(f"M01Unitのsessionsは正の整数で書いてください: {value!r}", errors[0])

    def test_total_sessions_must_be_positive_integer(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._course_root(root, [1], self._readme(), total=0)
            errors = self._course_errors(root)
            self.assertEqual(len(errors), 1, errors)
            self.assertIn("course.total_sessionsは正の整数で書いてください: 0", errors[0])

    def test_readme_without_session_notation_is_rejected(self):
        """設定だけ直して、READMEの「全15コマ」「1コマ90分」を書き換え忘れた状態を検出する。"""
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._course_root(root, [1], "# ハイブリッドアプリ開発技法\n\n授業の分量はここに書く。\n")
            errors = self._course_errors(root)
            self.assertEqual(len(errors), 2, errors)
            self.assertIn("README.md:1", errors[0])
            self.assertIn("授業の分量の表記がありません: 全15コマ", errors[0])
            self.assertIn("授業の分量の表記がありません: 1コマ90分", errors[1])

    def test_readme_notation_follows_the_configured_numbers(self):
        """コマ数を変えたら、READMEに求める表記もそれに合わせて変わる。"""
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._course_root(root, [1], self._readme(), total=30, minutes=45)
            errors = self._course_errors(root)
            self.assertEqual(len(errors), 2, errors)
            self.assertIn("全30コマ", errors[0])
            self.assertIn("1コマ45分", errors[1])

    # ------------------------------------------------------------------
    # 登録（check_registration）と表記揺れ（check_terms）
    # ------------------------------------------------------------------

    def _registration_root(self, root: Path, readme: str, requires: list[str]) -> None:
        self._write(root, "README.md", readme)
        self._minimal_config(
            root,
            [self._project()],
            scan_roots=["README.md", "M01HelloMonaca"],
            terms=[{"name": "t", "canonical": "ハイブリッドアプリ開発技法", "forbidden": [], "required_in": [
                "docs/hello-monaca/index.html", "teacher/hello-monaca/index.html"]}],
            registration={"targets": [{"path": "README.md", "requires": requires}]},
        )

    def test_missing_registration_is_reported(self):
        """READMEから単元のリンクが1つでも抜けたら検出する。"""
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._write_monaca(root)
            # 完成プロジェクトZIPへのリンクだけ書いていない。
            self._registration_root(root, self._readme(
                "docs/hello-monaca/index.html", "teacher/hello-monaca/index.html"),
                ["student_doc", "teacher_doc", "archive"])
            errors = [error for error in CHECKER.validate(root) if "への参照がありません" in error]
            self.assertEqual(len(errors), 1, errors)
            self.assertIn("README.md:1", errors[0])
            self.assertIn("docs/hello-monaca/downloads/M01HelloMonaca.zip", errors[0])

    def test_guidance_line_is_no_longer_required(self):
        """配布スクリプトは単元一覧をconfigから読むので、案内文の1行は求めない。"""
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._write_monaca(root)
            readme = self._readme(
                "docs/hello-monaca/index.html",
                "teacher/hello-monaca/index.html",
                "docs/hello-monaca/downloads/M01HelloMonaca.zip")
            self.assertNotIn("M01 HelloMonaca：", readme)
            self._registration_root(root, readme, ["student_doc", "teacher_doc", "archive"])
            errors = [error for error in CHECKER.validate(root) if "への参照がありません" in error]
            self.assertEqual(errors, [])

    def test_unknown_requires_is_reported(self):
        """requires に、もう無い項目（guidance_line など）を書いたら検出する。"""
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._registration_root(root, self._readme(), ["guidance_line"])
            errors = [error for error in CHECKER.validate(root) if "知らない項目" in error]
            self.assertEqual(len(errors), 1, errors)
            self.assertIn("config/teaching-materials.json:1", errors[0])
            self.assertIn("guidance_line", errors[0])

    def test_project_root_outside_scan_roots_is_rejected(self):
        """完成プロジェクトのフォルダを scan_roots に足し忘れたら検出する。"""
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config = self._repository(root)
            config["scan_roots"].remove("M01HelloMonaca")
            self._write_config(root, config)
            errors = CHECKER.validate(root)
            self.assertEqual(len(errors), 1, errors)
            self.assertIn("M01HelloMonacaがscan_rootsにありません", errors[0])

    def test_document_outside_scan_roots_is_rejected(self):
        """教員用ガイドのフォルダ（teacher）を scan_roots に足し忘れたら検出する。

        teacher/ は、単元が1つもないうちはフォルダごと無い（Gitは空のフォルダを持たない）ので、
        最初の単元を足すときに scan_roots へ足す。足し忘れると、表記揺れの検査から静かに漏れる。
        """
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config = self._repository(root)
            config["scan_roots"].remove("teacher")
            self._write_config(root, config)
            errors = CHECKER.validate(root)
            self.assertEqual(len(errors), 1, errors)
            self.assertIn("config/teaching-materials.json:1", errors[0])
            self.assertIn("M01HelloMonacaのteacher/hello-monaca/index.htmlが、"
                          "scan_rootsのどれの下にもありません", errors[0])

    def test_document_listed_itself_in_scan_roots_is_accepted(self):
        """フォルダでなく、教材ファイルそのものを scan_roots に書いてもよい。"""
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config = self._repository(root)
            config["scan_roots"][config["scan_roots"].index("teacher")] = "teacher/hello-monaca/index.html"
            self._write_config(root, config)
            self.assertEqual(CHECKER.validate(root), [])

    def _spelling_errors(self, root: Path, name: str, text: str, forbidden: str, scan_root: str) -> list[str]:
        self._write(root, name, text)
        self._write_config(root, {
            "scan_roots": [scan_root],
            "terms": [{"name": "表記", "canonical": "正式", "forbidden": [forbidden], "required_in": []}],
            "projects": [],
        })
        return CHECKER.validate(root)

    def test_forbidden_spelling_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            errors = self._spelling_errors(root, "README.md", "Monaca Cloud IDE\n", "Monaca Cloud IDE", "README.md")
            self.assertEqual(len(errors), 1, errors)
            self.assertIn("README.md:1", errors[0])
            self.assertIn("禁止表記", errors[0])

    def test_completed_code_is_scanned_for_spelling(self):
        """表記揺れの検査は、完成コードの .html・.js・.dart も見る。完成コードは scan_roots の中にある。"""
        cases = [
            ("M01HelloMonaca/www/js/app.js", "// Monaca Cloud IDE で動かす\n", "Monaca Cloud IDE", "M01HelloMonaca"),
            ("M01HelloMonaca/www/index.html", "<!-- Monaca Cloud IDE -->\n", "Monaca Cloud IDE", "M01HelloMonaca"),
            ("F01HelloFlutter/lib/main.dart", "// VSCode で開く\nvoid main() {}\n", "VSCode", "F01HelloFlutter"),
        ]
        for name, text, forbidden, scan_root in cases:
            with self.subTest(name=name), tempfile.TemporaryDirectory() as temporary:
                errors = self._spelling_errors(Path(temporary), name, text, forbidden, scan_root)
                self.assertEqual(len(errors), 1, errors)
                self.assertIn(f"{name}:1", errors[0])

    def test_build_outputs_are_not_scanned_for_spelling(self):
        """ビルド出力やローカルの依存は、学生が書いたものではないので表記揺れを見ない。"""
        for name in ("F01HelloFlutter/.dart_tool/package_config.json",
                     "F01HelloFlutter/build/app/outputs/output.json",
                     "F01HelloFlutter/ios/Pods/Manifest.txt",
                     "M01HelloMonaca/node_modules/cordova/README.md",
                     "M01HelloMonaca/platforms/android/config.xml"):
            with self.subTest(name=name), tempfile.TemporaryDirectory() as temporary:
                scan_root = name.split("/")[0]
                errors = self._spelling_errors(Path(temporary), name, "VSCode\n", "VSCode", scan_root)
                self.assertEqual(errors, [])

    def test_source_folders_with_generated_names_are_scanned_for_spelling(self):
        """配布するlib/build/やwww/plugins/も表記検査から抜けない。"""
        for name in ("F01HelloFlutter/lib/build/screen.dart",
                     "F01HelloFlutter/lib/plugins/helper.dart",
                     "M01HelloMonaca/www/plugins/app.js", "docs/build/index.html"):
            with self.subTest(name=name), tempfile.TemporaryDirectory() as temporary:
                errors = self._spelling_errors(Path(temporary), name, "VSCode\n", "VSCode", name.split("/")[0])
                self.assertEqual(len(errors), 1, errors)
                self.assertIn(f"{name}:1", errors[0])

    def test_missing_scan_root_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._write_config(root, {"scan_roots": ["missing"], "terms": [], "projects": []})

            errors = CHECKER.validate(root)

            self.assertEqual(len(errors), 1, errors)
            self.assertIn("missing:1", errors[0])
            self.assertIn("検査対象のパスがありません", errors[0])

    # ------------------------------------------------------------------
    # 完成プロジェクトZIPと、教科書のコード（snippets）
    # ------------------------------------------------------------------

    def test_archive_executable_bit_is_rejected(self):
        """実行権限がZIPとソースで違えば検出する。学生の手元でスクリプトを実行できなくなる。"""
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._repository(root)
            script = self._write(root, "M01HelloMonaca/tools/serve.sh", "#!/bin/sh\n")
            self._git_add(root, "M01HelloMonaca")
            self._archive(root, "docs/hello-monaca/downloads/M01HelloMonaca.zip",
                          [*self.files["monaca"], "M01HelloMonaca/tools/serve.sh"])
            # ZIPを作ったあとで実行権限を付けた。中身は同じでも、権限だけがずれる。
            script.chmod(0o755)
            errors = CHECKER.validate(root)
            self.assertEqual(len(errors), 1, errors)
            self.assertIn("実行権限が一致しません: M01HelloMonaca/tools/serve.sh", errors[0])

    def test_archive_contents_must_match_the_sources(self):
        """ZIPを作り直さずに完成コードを直した状態を検出する。"""
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._repository(root)
            self._write(root, "M01HelloMonaca/www/js/app.js", self.MONACA_JS.replace("こんにちは", "おはよう"))
            errors = [error for error in CHECKER.validate(root) if "ZIP" in error]
            self.assertEqual(len(errors), 1, errors)
            self.assertIn("内容が一致しません: M01HelloMonaca/www/js/app.js", errors[0])

    def test_archive_without_a_tracked_file_is_rejected(self):
        """ファイルを足してGit管理したのに、ZIPを作り直していない状態を検出する。"""
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._repository(root)
            self._write(root, "M01HelloMonaca/www/css/style.css", "body { margin: 0; }\n")
            self._git_add(root, "M01HelloMonaca")
            errors = CHECKER.validate(root)
            self.assertEqual(len(errors), 1, errors)
            self.assertIn("ZIPにソースがありません: M01HelloMonaca/www/css/style.css", errors[0])

    def test_archive_with_an_untracked_file_is_rejected(self):
        """Git管理していないファイルがZIPに入っていたら検出する。"""
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._repository(root)
            self._write(root, "M01HelloMonaca/memo.txt", "下書き\n")
            self._archive(root, "docs/hello-monaca/downloads/M01HelloMonaca.zip",
                          [*self.files["monaca"], "M01HelloMonaca/memo.txt"])
            errors = CHECKER.validate(root)
            self.assertEqual(len(errors), 1, errors)
            self.assertIn("ZIPに配布対象外ファイルがあります: M01HelloMonaca/memo.txt", errors[0])

    def test_archive_requires_sources_with_generated_directory_names(self):
        """ZIPと検査が同じ誤除外をしていても通らないよう、欠落ZIPそのものを検査する。"""
        for kind, name in (("flutter", "F01HelloFlutter/lib/build/screen.dart"),
                           ("flutter", "F01HelloFlutter/lib/plugins/helper.dart"),
                           ("monaca", "M01HelloMonaca/www/plugins/app.js")):
            with self.subTest(name=name), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                self._repository(root, kinds=(kind,))
                self._write(root, name, "// 完成コード\n")
                self._git_add(root, name, force=True)
                errors = CHECKER.validate(root)
                self.assertEqual(len(errors), 1, errors)
                self.assertIn(f"ZIPにソースがありません: {name}", errors[0])

    def test_archive_leaves_out_build_outputs_even_if_tracked(self):
        """ビルド出力を誤ってGit管理していても、ZIPに入れないのが正しい形。"""
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._repository(root, kinds=("flutter",))
            for name in ("F01HelloFlutter/.dart_tool/package_config.json",
                         "F01HelloFlutter/build/app/outputs/app.apk",
                         "F01HelloFlutter/android/.gradle/cache.bin",
                         "F01HelloFlutter/android/local.properties",
                         "F01HelloFlutter/ios/Pods/Manifest.lock",
                         "F01HelloFlutter/ios/.symlinks/plugins/x/pubspec.yaml",
                         "F01HelloFlutter/ios/Flutter/ephemeral/flutter_lldbinit"):
                self._write(root, name, "ローカルで作られたもの\n")
            self._git_add(root, "F01HelloFlutter", force=True)
            errors = [error for error in CHECKER.validate(root) if "ZIP" in error]
            self.assertEqual(errors, [])

    def test_zip_made_by_package_project_passes_the_archive_check(self):
        """scripts/package-project.py が作ったZIPは、そのまま検査を通る（除外の集合が同じ）。"""
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._repository(root, kinds=("monaca", "flutter"))
            for name in ("M01HelloMonaca/node_modules/cordova/index.js",
                         "M01HelloMonaca/platforms/android/build.gradle",
                         "M01HelloMonaca/plugins/fetch.json",
                         "F01HelloFlutter/.dart_tool/package_config.json",
                         "F01HelloFlutter/build/app/outputs/app.apk",
                         "F01HelloFlutter/android/local.properties",
                         "F01HelloFlutter/ios/Pods/Manifest.lock"):
                self._write(root, name, "ローカルで作られたもの\n")
            self._git_add(root, "M01HelloMonaca", "F01HelloFlutter", force=True)
            (root / "scripts").mkdir()
            copy2(PACKAGER, root / "scripts" / PACKAGER.name)
            copy2(PACKAGER.with_name("project_files.py"), root / "scripts/project_files.py")
            for project in self._read_config(root)["projects"]:
                result = subprocess.run(
                    [sys.executable, str(root / "scripts" / PACKAGER.name),
                     "--project", project["root"], "--output", str(root / project["archive"])],
                    cwd=root, capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stderr)
            errors = [error for error in CHECKER.validate(root) if "ZIP" in error]
            self.assertEqual(errors, [])

    def test_snippet_must_match_the_source(self):
        """教科書に貼った完成コードが、実際のファイルと1バイトでも違えば検出する。"""
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._repository(root)
            self._write(root, "docs/hello-monaca/index.html", self._textbook(
                "M01HelloMonaca", [("hello-monaca", "M01HelloMonaca")], "hello-monaca",
                snippet=("code-final-app", self.MONACA_JS.replace("こんにちは", "おはよう")), tool=self.IDE))
            errors = [error for error in CHECKER.validate(root) if "code-final-app" in error]
            self.assertEqual(len(errors), 1, errors)
            self.assertIn("code-final-appとM01HelloMonaca/www/js/app.jsが一致しません", errors[0])

    def test_missing_snippet_is_rejected(self):
        """設定に書いたスニペットが、教科書から消えていたら検出する。"""
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._repository(root, kinds=("flutter",))
            self._write(root, "docs/hello-flutter/index.html", self._textbook(
                "F01HelloFlutter", [("hello-flutter", "F01HelloFlutter")], "hello-flutter", tool=self.EDITOR))
            errors = CHECKER.validate(root)
            self.assertEqual(len(errors), 1, errors)
            self.assertIn("コードスニペットがありません: code-final-main", errors[0])

    # ------------------------------------------------------------------
    # 教材のフォルダから学生がコピーするファイル（check_downloads）
    # ------------------------------------------------------------------

    PNG = b"\x89PNG\r\n\x1a\n" + bytes(range(64))
    # 置き場所とファイル名を、同じSTEP（<section>）に書いた教科書。
    GUIDE = ('<section id="step-2"><ol><li>教材のフォルダの <code>docs → x → downloads</code> を開きます。</li>'
             "<li><code>title.png</code> をコピーします。</li></ol></section>")

    def _download_root(self, root: Path, download: bytes, textbook: str,
                       download_name: str = "title.png") -> None:
        """配布ファイルの検査に必要な最小限のリポジトリを作る。"""
        source = root / "Sample/www/img/title.png"
        source.parent.mkdir(parents=True)
        source.write_bytes(self.PNG)
        (root / "docs/x/downloads").mkdir(parents=True)
        (root / "docs/x/downloads" / download_name).write_bytes(download)
        (root / "docs/x/index.html").write_text(textbook, encoding="utf-8")
        self._git_add(root, "Sample")
        self._minimal_config(root, [self._project(
            name="Sample", root="Sample", app_id="jp.example.sample", entry="Sample/www/index.html",
            docs=["docs/x/index.html", "teacher/x/index.html"],
            sources=["Sample/www/index.html"],
            archive="docs/x/downloads/Sample.zip",
            downloads=[{
                "download": f"docs/x/downloads/{download_name}",
                "source": "Sample/www/img/title.png",
            }],
        )])

    def _download_errors(self, root: Path) -> list[str]:
        return [error for error in CHECKER.validate(root) if "配布ファイル" in error]

    def test_download_identical_to_source_is_accepted(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._download_root(root, self.PNG, self.GUIDE)
            self.assertEqual(self._download_errors(root), [])

    def test_download_folder_written_as_separate_codes_is_accepted(self):
        """置き場所は、フォルダ名を1つずつ <code> で囲んでも、途中で改行しても通る。"""
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._download_root(
                root, self.PNG,
                "<section><p><code>docs</code> →\n  <code>x</code> → <code>downloads</code> の title.png をコピーします。</p></section>")
            self.assertEqual(self._download_errors(root), [])

    def test_download_differing_by_one_byte_is_rejected(self):
        """配布ファイルが、完成プロジェクトのソースと1バイトでも違えば検出する。"""
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            changed = bytearray(self.PNG)
            changed[-1] ^= 0x01
            self._download_root(root, bytes(changed), self.GUIDE)
            errors = self._download_errors(root)
            self.assertEqual(len(errors), 1, errors)
            self.assertIn("docs/x/downloads/title.png:1", errors[0])
            self.assertIn("内容が一致しません: Sample/www/img/title.png", errors[0])

    def test_download_without_folder_guidance_is_rejected(self):
        """置き場所の案内が教科書から消えたら検出する。学生はファイルを見つけられない。"""
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._download_root(root, self.PNG, "<section><p>先生から配られた title.png を使います。</p></section>")
            errors = self._download_errors(root)
            self.assertEqual(len(errors), 1, errors)
            self.assertIn("docs/x/index.html:1", errors[0])
            self.assertIn("置き場所の案内がありません: docs → x → downloads", errors[0])

    def test_download_button_is_not_guidance(self):
        """ダウンロードボタンだけでは通らない。file:// で開いた教科書では、押しても保存されない。"""
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._download_root(
                root, self.PNG,
                '<section><a class="button-link" href="downloads/title.png" download>title.png</a></section>')
            errors = self._download_errors(root)
            self.assertEqual(len(errors), 1, errors)
            self.assertIn("置き場所の案内がありません: docs → x → downloads", errors[0])

    def test_download_without_file_name_is_rejected(self):
        """ファイル名の案内が消えたら検出する。"""
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._download_root(root, self.PNG, "<section><p><code>docs → x → downloads</code> を開きます。</p></section>")
            errors = self._download_errors(root)
            self.assertEqual(len(errors), 1, errors)
            self.assertIn("ファイル名の案内がありません: title.png", errors[0])

    def test_download_guided_only_in_another_step_is_rejected(self):
        """置き場所が別のSTEPにしか書かれていなければ検出する。

        同じフォルダのファイルを別々のSTEPで使うとき、片方のSTEPから置き場所の案内が消えても、
        教科書全体で探すと見つかってしまう。
        """
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._download_root(
                root, self.PNG,
                '<section id="step-2"><p>title.png を www → img に入れます。</p></section>'
                '<section id="step-7"><p><code>docs → x → downloads</code> の other.png をコピーします。</p></section>')
            errors = self._download_errors(root)
            self.assertEqual(len(errors), 1, errors)
            self.assertIn("ファイル名の案内がありません: title.png", errors[0])
            self.assertIn("同じSTEP", errors[0])

    def test_download_renamed_from_source_is_rejected(self):
        """学生はコピーしたファイルをそのまま www/ に入れるので、名前の違いも検出する。"""
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._download_root(root, self.PNG, self.GUIDE.replace("title.png", "Title.png"),
                                download_name="Title.png")
            errors = self._download_errors(root)
            self.assertEqual(len(errors), 1, errors)
            self.assertIn("ファイル名が一致しません", errors[0])

    def test_download_source_outside_archive_is_rejected(self):
        """元ファイルがGit管理されていなければ、完成プロジェクトZIPにも入らない。"""
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._download_root(root, self.PNG, self.GUIDE)
            subprocess.run(["git", "rm", "--cached", "-q", "Sample/www/img/title.png"],
                           cwd=root, check=True, capture_output=True)
            errors = self._download_errors(root)
            self.assertEqual(len(errors), 1, errors)
            self.assertIn("完成プロジェクトZIPに入るファイルではありません", errors[0])

    # ------------------------------------------------------------------
    # サイドバー（check_sidebar_units）
    # ------------------------------------------------------------------

    # Monaca系2単元 → Flutter系1単元。
    SIDEBAR_UNITS = [("M01One", "one"), ("M02Two", "two"), ("F01Three", "three")]

    def _sidebar(self, current: str, order: list[str] | None = None, link_self: bool = False) -> str:
        """3単元ぶんのサイドバーを作る。current はいま開いている単元のフォルダ名。"""
        names = dict((folder, name) for name, folder in self.SIDEBAR_UNITS)
        entries = []
        for folder in order or [folder for _, folder in self.SIDEBAR_UNITS]:
            label = f"{names[folder][:3]}：{names[folder][3:]}"
            if folder == current and not link_self:
                entries.append(f'<span aria-current="page">{label}</span>')
            else:
                entries.append(f'<a href="../{folder}/index.html">{label}</a>')
        return ('<aside class="sidebar"><div class="progress"><span>0 / 3</span></div>\n'
                '<div class="resources"><a href="#help">困ったとき</a>' + "".join(entries)
                + f'<a href="../common/setup.html?from={current}">共通：はじめの準備</a></div></aside>')

    def _sidebar_project(self, name: str, folder: str) -> dict:
        """サイドバーの検査に必要なだけの単元設定を作る。名前の頭の M / F で系統を決める。"""
        docs = [f"docs/{folder}/index.html", f"teacher/{folder}/index.html"]
        archive = f"docs/{folder}/downloads/{name}.zip"
        if name.startswith("M"):
            return self._project(
                name=name, root=name, app_id=f"jp.ac.jec.{name.lower()}",
                entry=f"{name}/www/index.html", sources=[f"{name}/www/index.html"],
                docs=docs, archive=archive)
        return self._flutter_project(
            name=name, root=name, package_name=name.lower(),
            application_id=f"jp.ac.jec.{name.lower()}",
            entry=f"{name}/lib/main.dart", sources=[f"{name}/lib/main.dart"],
            docs=docs, archive=archive)

    def _sidebar_errors(self, root: Path, textbooks: dict[str, str]) -> list[str]:
        """教科書を書き出して検査し、サイドバーについてのエラーだけを返す。"""
        for folder, content in textbooks.items():
            (root / "docs" / folder).mkdir(parents=True)
            (root / "docs" / folder / "index.html").write_text(content, encoding="utf-8")
        self._minimal_config(root, [
            self._sidebar_project(name, folder) for name, folder in self.SIDEBAR_UNITS
        ])
        return [error for error in CHECKER.validate(root) if "サイドバー" in error]

    def test_sidebar_listing_every_unit_is_accepted(self):
        """どの単元でも全単元が並び、いま開いている単元だけが現在地になっている。"""
        with tempfile.TemporaryDirectory() as temporary:
            errors = self._sidebar_errors(Path(temporary), {
                folder: self._sidebar(folder) for _, folder in self.SIDEBAR_UNITS
            })
            self.assertEqual(errors, [])

    def test_sidebar_missing_later_unit_is_rejected(self):
        """単元を足したのに、前の単元のサイドバーを直し忘れた状態を検出する。"""
        with tempfile.TemporaryDirectory() as temporary:
            textbooks = {folder: self._sidebar(folder) for _, folder in self.SIDEBAR_UNITS}
            textbooks["one"] = self._sidebar("one", order=["one", "two"])
            errors = self._sidebar_errors(Path(temporary), textbooks)
            self.assertEqual(len(errors), 1, errors)
            self.assertIn("docs/one/index.html:2", errors[0])
            self.assertIn('単元へのリンクがありません: <a href="../three/index.html">F01：Three</a>', errors[0])

    def test_sidebar_linking_current_unit_is_rejected(self):
        """いま開いている単元は、リンクではなく現在地として示す。"""
        with tempfile.TemporaryDirectory() as temporary:
            textbooks = {folder: self._sidebar(folder) for _, folder in self.SIDEBAR_UNITS}
            textbooks["two"] = self._sidebar("two", link_self=True)
            errors = self._sidebar_errors(Path(temporary), textbooks)
            self.assertEqual(len(errors), 2, errors)
            self.assertIn('現在地がありません: <span aria-current="page">M02：Two</span>', errors[0])
            self.assertIn("いま開いている単元がリンクになっています: M02：Two", errors[1])

    def test_sidebar_in_wrong_order_is_rejected(self):
        """過不足がなくても、projects の順に並んでいなければ検出する。"""
        with tempfile.TemporaryDirectory() as temporary:
            textbooks = {folder: self._sidebar(folder) for _, folder in self.SIDEBAR_UNITS}
            textbooks["three"] = self._sidebar("three", order=["two", "one", "three"])
            errors = self._sidebar_errors(Path(temporary), textbooks)
            self.assertEqual(len(errors), 1, errors)
            self.assertIn("projectsの順に並んでいません: M02：Two、M01：One、F01：Three", errors[0])

    def test_sidebar_with_unregistered_unit_is_rejected(self):
        """projects にない単元へのリンクが残っている状態を検出する。"""
        with tempfile.TemporaryDirectory() as temporary:
            textbooks = {folder: self._sidebar(folder) for _, folder in self.SIDEBAR_UNITS}
            textbooks["one"] = textbooks["one"].replace(
                '<a href="../common/', '<a href="../four/index.html">F02：Four</a><a href="../common/', 1)
            errors = self._sidebar_errors(Path(temporary), textbooks)
            self.assertEqual(len(errors), 1, errors)
            self.assertIn("登録のない単元があります: F02：Four（../four/index.html）", errors[0])

    def test_sidebar_with_duplicated_unit_is_rejected(self):
        """単元を足すときのコピーで、同じ単元が2回並んだ状態を検出する。"""
        with tempfile.TemporaryDirectory() as temporary:
            textbooks = {folder: self._sidebar(folder) for _, folder in self.SIDEBAR_UNITS}
            textbooks["two"] = self._sidebar("two", order=["one", "one", "two", "three"])
            errors = self._sidebar_errors(Path(temporary), textbooks)
            self.assertEqual(len(errors), 1, errors)
            self.assertIn("projectsの順に並んでいません: M01：One、M01：One、M02：Two、F01：Three", errors[0])

    def test_sidebar_with_link_around_current_unit_is_rejected(self):
        """現在地をリンクで包むと、リンクにしない決まりをすり抜けるので検出する。"""
        with tempfile.TemporaryDirectory() as temporary:
            textbooks = {folder: self._sidebar(folder) for _, folder in self.SIDEBAR_UNITS}
            textbooks["two"] = textbooks["two"].replace(
                '<span aria-current="page">M02：Two</span>',
                '<a href="../two/index.html"><span aria-current="page">M02：Two</span></a>', 1)
            errors = self._sidebar_errors(Path(temporary), textbooks)
            self.assertTrue(any("単元の中に、別のタグがあります: <span>" in error for error in errors), errors)
            self.assertTrue(any("いま開いている単元がリンクになっています: M02：Two" in error for error in errors), errors)

    def test_sidebar_ignores_topbar_and_nested_div(self):
        """topbarの単元リンクは検査しない。resources の中の <div> は、サイドバーの終わりと取り違えない。"""
        with tempfile.TemporaryDirectory() as temporary:
            textbooks = {folder: self._sidebar(folder) for _, folder in self.SIDEBAR_UNITS}
            textbooks["two"] = (
                '<header class="topbar"><a href="../one/index.html">M01 One</a></header>\n'
                + textbooks["two"].replace(
                    '<a href="../one/index.html">M01：One</a>',
                    '<div class="group"><a href="../one/index.html">M01：One</a></div>', 1))
            errors = self._sidebar_errors(Path(temporary), textbooks)
            self.assertEqual(errors, [])

    def test_textbook_without_sidebar_is_rejected(self):
        """サイドバーそのものがない教科書は、並びを確かめようがないので検出する。"""
        with tempfile.TemporaryDirectory() as temporary:
            textbooks = {folder: self._sidebar(folder) for _, folder in self.SIDEBAR_UNITS}
            textbooks["two"] = "<main><h1>Two</h1></main>"
            errors = self._sidebar_errors(Path(temporary), textbooks)
            self.assertEqual(len(errors), 1, errors)
            self.assertIn("docs/two/index.html:1", errors[0])
            self.assertIn("サイドバー（<div class=\"resources\">）がありません", errors[0])

    # ------------------------------------------------------------------
    # projects の並び（2系統。M系→F系）
    # ------------------------------------------------------------------

    def _order_errors(self, root: Path, names: list[str]) -> list[str]:
        self._minimal_config(root, [
            self._sidebar_project(name, name.lower()) for name in names
        ])
        return [error for error in CHECKER.validate(root) if "単元番号順" in error]

    def test_projects_in_monaca_then_flutter_order_are_accepted(self):
        """Monaca系をひと通り終えてからFlutter系に入るのが、この授業の進み方。"""
        with tempfile.TemporaryDirectory() as temporary:
            errors = self._order_errors(Path(temporary), ["M01One", "M02Two", "F01Three", "F02Four"])
            self.assertEqual(errors, [])

    def test_projects_out_of_unit_number_order_are_rejected(self):
        """サイドバーは projects の順と照合するので、番号が戻っていたら検出する。"""
        for names, message in ((["M01One", "M03Three", "M02Two"], "M03ThreeのあとにM02Twoがあります"),
                               (["M01One", "F02Two", "F01Three"], "F02TwoのあとにF01Threeがあります")):
            with self.subTest(names=names), tempfile.TemporaryDirectory() as temporary:
                errors = self._order_errors(Path(temporary), names)
                self.assertEqual(len(errors), 1, errors)
                self.assertIn("config/teaching-materials.json:1", errors[0])
                self.assertIn(message, errors[0])

    def test_projects_returning_to_monaca_after_flutter_are_rejected(self):
        """いちどFlutter系に移ったあとでMonaca系に戻る並びは検出する。"""
        with tempfile.TemporaryDirectory() as temporary:
            errors = self._order_errors(Path(temporary), ["M01One", "F01Three", "M02Two"])
            self.assertEqual(len(errors), 1, errors)
            self.assertIn("F01ThreeのあとにM02Twoがあります", errors[0])

    def test_projects_starting_with_flutter_are_rejected(self):
        """Flutter系から始まる並びも検出する。授業はMonaca系（コマ1〜7）から始まる。"""
        with tempfile.TemporaryDirectory() as temporary:
            errors = self._order_errors(Path(temporary), ["F01One", "M01Two"])
            self.assertEqual(len(errors), 1, errors)
            self.assertIn("F01OneのあとにM01Twoがあります", errors[0])

    # ------------------------------------------------------------------
    # .gitignore と追跡してはいけないファイル（check_project_layout）
    # ------------------------------------------------------------------

    def _layout_root(self, root: Path, reference, gitignores: dict[str, str],
                     projects: list[dict], tracked: dict[str, str] | None = None) -> None:
        """.gitignore と、Git管理するファイルを置いて、project_layout だけを書いた設定にする。"""
        files = {f"{project_root}/.gitignore": content for project_root, content in gitignores.items()}
        files.update(tracked or {})
        for name, content in files.items():
            self._write(root, name, content)
        self._git_add(root, *files, force=True)
        self._minimal_config(root, projects, project_layout={
            "gitignore_reference": reference,
            "untracked_parts": self.UNTRACKED_PARTS,
            "untracked_names": self.UNTRACKED_NAMES,
        })

    def _layout_errors(self, root: Path) -> list[str]:
        return [error for error in CHECKER.validate(root)
                if ".gitignore" in error or "Git管理" in error]

    def test_gitignore_reference_dictionary_is_applied_per_kind(self):
        """kind ごとに .gitignore の基準を変えられる。"""
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._layout_root(
                root,
                {"monaca": "M01HelloMonaca/.gitignore", "flutter": "F01HelloFlutter/.gitignore"},
                {"M01HelloMonaca": self.MONACA_IGNORE,
                 "F01HelloFlutter": self.FLUTTER_IGNORE,
                 # Flutter系なのに、Monaca系の .gitignore をコピーしてしまった。
                 "F02CalcGame": self.MONACA_IGNORE},
                [self._project(),
                 self._flutter_project(),
                 self._sidebar_project("F02CalcGame", "calc-game")])
            errors = self._layout_errors(root)
            self.assertEqual(len(errors), 1, errors)
            self.assertIn("F02CalcGame/.gitignore:1", errors[0])
            self.assertIn("F01HelloFlutter/.gitignoreと内容が異なります", errors[0])

    def test_null_gitignore_reference_is_not_compared(self):
        """null にした系統は .gitignore を照合しない。無くても、中身が何でもよい。"""
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._layout_root(
                root,
                {"monaca": None, "flutter": None},
                {"F01HelloFlutter": "# flutter create が生成したもの\n"},
                [self._project(), self._flutter_project()],
                tracked={"M01HelloMonaca/www/index.html": self.MONACA_HTML})
            self.assertEqual(self._layout_errors(root), [])

    def test_null_gitignore_reference_still_reports_untracked_files(self):
        """null でも、Git管理してはいけないファイルは確かめる。"""
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._layout_root(
                root,
                {"monaca": None, "flutter": None},
                {},
                [self._project(), self._flutter_project()],
                tracked={
                    "M01HelloMonaca/www/index.html": self.MONACA_HTML,
                    "M01HelloMonaca/node_modules/cordova/index.js": "ローカルの依存\n",
                    "F01HelloFlutter/lib/main.dart": self.DART_SOURCE,
                    "F01HelloFlutter/.dart_tool/package_config.json": "{}\n",
                    "F01HelloFlutter/android/local.properties": "sdk.dir=/dev/null\n",
                })
            errors = self._layout_errors(root)
            self.assertEqual(len(errors), 3, errors)
            self.assertIn("F01HelloFlutter/.dart_tool/package_config.json:1: Git管理してはいけないファイルです", errors)
            self.assertIn("F01HelloFlutter/android/local.properties:1: Git管理してはいけないファイルです", errors)
            self.assertIn("M01HelloMonaca/node_modules/cordova/index.js:1: Git管理してはいけないファイルです", errors)

    def test_gitignore_reference_string_is_common_to_every_kind(self):
        """文字列で書かれていたら、参照リポジトリと同じく全kind共通の基準とみなす。"""
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._layout_root(
                root,
                "F01HelloFlutter/.gitignore",
                {"M01HelloMonaca": self.MONACA_IGNORE,
                 "F01HelloFlutter": self.FLUTTER_IGNORE},
                [self._project(), self._flutter_project()])
            errors = self._layout_errors(root)
            self.assertEqual(len(errors), 1, errors)
            self.assertIn("M01HelloMonaca/.gitignore:1", errors[0])
            self.assertIn("F01HelloFlutter/.gitignoreと内容が異なります", errors[0])

    def test_missing_gitignore_reference_for_kind_is_rejected(self):
        """使っている kind の基準を書き忘れたら検出する。照合しないなら null と明示させる。"""
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._layout_root(
                root,
                {"flutter": None},
                {"F01HelloFlutter": self.FLUTTER_IGNORE},
                [self._project(), self._flutter_project()],
                tracked={"M01HelloMonaca/www/index.html": self.MONACA_HTML})
            errors = self._layout_errors(root)
            self.assertEqual(len(errors), 1, errors)
            self.assertIn("config/teaching-materials.json:1", errors[0])
            self.assertIn("monacaの基準がありません", errors[0])

    def test_missing_gitignore_reference_file_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._layout_root(
                root,
                {"monaca": None, "flutter": "F01HelloFlutter/.gitignore"},
                {},
                [self._flutter_project()],
                tracked={"F01HelloFlutter/lib/main.dart": self.DART_SOURCE})
            errors = self._layout_errors(root)
            self.assertIn("F01HelloFlutter/.gitignore:1: .gitignoreの基準ファイルがありません", errors)

    def test_project_without_gitignore_is_rejected(self):
        """基準を決めた系統の単元に .gitignore が無ければ検出する。"""
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._layout_root(
                root,
                {"monaca": None, "flutter": "F01HelloFlutter/.gitignore"},
                {"F01HelloFlutter": self.FLUTTER_IGNORE},
                [self._flutter_project(), self._sidebar_project("F02CalcGame", "calc-game")],
                tracked={"F02CalcGame/lib/main.dart": self.DART_SOURCE})
            errors = self._layout_errors(root)
            self.assertEqual(errors, ["F02CalcGame/.gitignore:1: .gitignoreがありません"])

    def test_untracked_file_is_reported_once_per_project(self):
        """1つのプロジェクトを複数の単元で育てるとき、同じ指摘を単元の数だけ出さない。"""
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._layout_root(
                root,
                {"monaca": None, "flutter": None},
                {},
                [self._project(name="M01One"), self._project(name="M02Two")],
                tracked={"M01HelloMonaca/www/index.html": self.MONACA_HTML,
                         "M01HelloMonaca/platforms/android/build.gradle": "生成物\n"})
            errors = self._layout_errors(root)
            self.assertEqual(len(errors), 1, errors)
            self.assertIn("M01HelloMonaca/platforms/android/build.gradle:1", errors[0])
            self.assertIn("Git管理してはいけないファイルです", errors[0])

    # ------------------------------------------------------------------
    # 用語をどの系統に求めるか（terms[].applies_to）
    #
    # 「Monaca クラウドIDE」のように、Monaca系でしか使わない用語がある。それをFlutter系の
    # 教科書にまで required_in で求めると、書きようのない表記を迫ることになる。
    # applies_to を書かない用語は、これまでどおり両方の系統に求める。
    # ------------------------------------------------------------------

    MONACA_DOCS = ["docs/hello-monaca/index.html", "teacher/hello-monaca/index.html"]
    FLUTTER_DOCS = ["docs/hello-flutter/index.html", "teacher/hello-flutter/index.html"]

    def _term(self, required_in: list[str], **extra) -> dict:
        term = {"name": "MonacaのクラウドIDE", "canonical": self.IDE, "forbidden": [],
                "required_in": required_in}
        term.update(extra)
        return term

    def _applies_to_errors(self, root: Path, terms: list[dict]) -> list[str]:
        """Monaca系とFlutter系を1単元ずつ置いて、required_in の不足だけを返す。"""
        self._minimal_config(
            root,
            [self._project(), self._flutter_project()],
            terms=terms,
            registration={"targets": []},
        )
        return [error for error in CHECKER.validate(root)
                if "terms.required_inにありません" in error]

    def test_term_for_monaca_requires_monaca_documents(self):
        """applies_to がMonaca系なら、Monaca単元の教材を required_in に求める。"""
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            errors = self._applies_to_errors(
                root, [self._term(self.FLUTTER_DOCS, applies_to=["monaca"])])
            self.assertEqual(len(errors), 2, errors)
            self.assertIn("config/teaching-materials.json:1", errors[0])
            self.assertIn("M01HelloMonacaのdocs/hello-monaca/index.htmlが", errors[0])
            self.assertIn("M01HelloMonacaのteacher/hello-monaca/index.htmlが", errors[1])

    def test_term_for_monaca_does_not_require_flutter_documents(self):
        """同じ設定でも、Flutter系の教材は required_in に無くてよい。"""
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            errors = self._applies_to_errors(
                root, [self._term(self.MONACA_DOCS, applies_to=["monaca"])])
            self.assertEqual(errors, [])

    def test_term_without_applies_to_requires_every_kind(self):
        """applies_to を書かない用語は、両方の系統に求める（後方互換）。"""
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            errors = self._applies_to_errors(root, [self._term(self.MONACA_DOCS)])
            self.assertEqual(len(errors), 2, errors)
            self.assertIn("F01HelloFlutterのdocs/hello-flutter/index.htmlが", errors[0])
            self.assertIn("F01HelloFlutterのteacher/hello-flutter/index.htmlが", errors[1])

    def test_term_with_empty_applies_to_requires_no_kind(self):
        """applies_to が空配列なら、どの系統にも求めない。"""
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            errors = self._applies_to_errors(root, [self._term([], applies_to=[])])
            self.assertEqual(errors, [])

    def test_terms_are_judged_one_by_one(self):
        """用語が2つあるとき、applies_to は用語ごとに効く。"""
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            errors = self._applies_to_errors(root, [
                # Monaca系にだけ求める用語。Monaca単元の教材は required_in にある。
                self._term(self.MONACA_DOCS, applies_to=["monaca"]),
                # 両方の系統に求める用語。Flutter系の教材が required_in にない。
                self._term(self.MONACA_DOCS, name="授業名"),
            ])
            self.assertEqual(len(errors), 2, errors)
            self.assertTrue(all("F01HelloFlutter" in error for error in errors), errors)

    # ------------------------------------------------------------------
    # 教材に置いた複製コード（check_mirrors）
    #
    # teacher/<スラッグ>/code/ は完成プロジェクトのソースの複製。完成コードだけを
    # 直すと複製が古いまま静かに残るので、バイト単位で照合する。
    # ------------------------------------------------------------------

    MIRROR = [{"source": "M01HelloMonaca/www/js/app.js",
               "copy": "teacher/hello-monaca/code/02-app.js"}]

    def _mirror_errors(self, root: Path, **overrides) -> list[str]:
        """複製コードについてのエラーだけを返す。"""
        self._minimal_config(root, [self._project(**overrides)])
        return [error for error in CHECKER.validate(root) if "複製コード" in error]

    def test_mirror_identical_to_the_source_is_accepted(self):
        """複製コードが元ファイルと1バイトも違わなければ、何も言わない。"""
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._write(root, "M01HelloMonaca/www/js/app.js", self.MONACA_JS)
            self._write(root, "teacher/hello-monaca/code/02-app.js", self.MONACA_JS)
            self.assertEqual(self._mirror_errors(root, mirrors=self.MIRROR), [])

    def test_mirror_differing_by_one_byte_is_rejected(self):
        """完成コードだけ直して、複製コードが古いまま残った状態を検出する。"""
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._write(root, "M01HelloMonaca/www/js/app.js", self.MONACA_JS)
            self._write(root, "teacher/hello-monaca/code/02-app.js",
                        self.MONACA_JS.replace("こんにちは", "おはよう"))
            errors = self._mirror_errors(root, mirrors=self.MIRROR)
            self.assertEqual(len(errors), 1, errors)
            self.assertIn("teacher/hello-monaca/code/02-app.js:1", errors[0])
            self.assertIn("内容が一致しません: M01HelloMonaca/www/js/app.js", errors[0])

    def test_mirror_without_copy_is_rejected(self):
        """複製コードを置き忘れた状態を検出する。"""
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._write(root, "M01HelloMonaca/www/js/app.js", self.MONACA_JS)
            errors = self._mirror_errors(root, mirrors=self.MIRROR)
            self.assertEqual(len(errors), 1, errors)
            self.assertIn("teacher/hello-monaca/code/02-app.js:1", errors[0])
            self.assertIn("複製コードがありません", errors[0])

    def test_mirror_without_source_is_rejected(self):
        """元ファイルのパスを書き間違えた状態を検出する。"""
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._write(root, "teacher/hello-monaca/code/02-app.js", self.MONACA_JS)
            errors = self._mirror_errors(root, mirrors=self.MIRROR)
            self.assertEqual(len(errors), 1, errors)
            self.assertIn("M01HelloMonaca/www/js/app.js:1", errors[0])
            self.assertIn("複製コードの元ファイルがありません", errors[0])

    def test_project_without_mirrors_is_accepted(self):
        """mirrors を書かない単元では、何も照合しない（後方互換）。"""
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._write(root, "M01HelloMonaca/www/js/app.js", self.MONACA_JS)
            # 複製の置き場所には、わざと中身の違うファイルを置いてある。
            self._write(root, "teacher/hello-monaca/code/02-app.js", "// 古い複製\n")
            self.assertEqual(self._mirror_errors(root), [])

    # ------------------------------------------------------------------
    # 設定の必須キー（check_config）
    #
    # キーを書き忘れたときに、Pythonのトレースバックではなく日本語のエラーを出す。
    # トレースバックのままだと、設定のどこを直せばよいか分からない。
    # ------------------------------------------------------------------

    def _full_config(self, project: dict | None = None) -> dict:
        """必須キーがそろった設定。ここから1つずつ落として試す。"""
        return {
            "scan_roots": [],
            "terms": [],
            "registration": {"targets": [{"path": "README.md", "requires": []}]},
            "projects": [project or self._project()],
        }

    def test_missing_top_level_key_is_reported_in_japanese(self):
        """scan_roots・terms・projects の書き忘れを、日本語のエラーにする。"""
        for key in ("scan_roots", "terms", "projects"):
            with self.subTest(key=key), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                config = self._full_config()
                del config[key]
                self._write_config(root, config)
                self.assertEqual(
                    CHECKER.validate(root),
                    [f"config/teaching-materials.json:1: 設定に{key}がありません"])

    def test_missing_project_key_is_reported_in_japanese(self):
        """単元の設定のキーの書き忘れを、日本語のエラーにする。"""
        for key in ("name", "root", "docs", "snippets", "archive"):
            with self.subTest(key=key), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                config = self._full_config()
                del config["projects"][0][key]
                self._write_config(root, config)
                errors = CHECKER.validate(root)
                self.assertEqual(len(errors), 1, errors)
                self.assertIn("config/teaching-materials.json:1", errors[0])
                self.assertIn(f"に{key}がありません", errors[0])

    def test_missing_kind_specific_key_is_reported_in_japanese(self):
        """kind ごとに要るキー（Monacaの app_id、Flutterの package_name など）の書き忘れも、日本語で言う。"""
        cases = [
            (self._project(), "app_id"),
            (self._project(), "entry"),
            (self._flutter_project(), "package_name"),
            (self._flutter_project(), "application_id"),
            (self._flutter_project(), "entry"),
        ]
        for project, key in cases:
            with self.subTest(kind=project["kind"], key=key), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                config = self._full_config(project)
                del config["projects"][0][key]
                self._write_config(root, config)
                self.assertEqual(CHECKER.validate(root), [
                    f"config/teaching-materials.json:1: projects[0]（{project['name']}）に"
                    f"{key}がありません（{project['kind']}の単元に必要です）"])

    def test_missing_registration_target_key_is_reported_in_japanese(self):
        """registration.targets の項目のキーの書き忘れを、日本語のエラーにする。"""
        for key in ("path", "requires"):
            with self.subTest(key=key), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                config = self._full_config()
                del config["registration"]["targets"][0][key]
                self._write_config(root, config)
                self.assertEqual(CHECKER.validate(root), [
                    "config/teaching-materials.json:1: "
                    f"registration.targets[0]に{key}がありません"])

    def test_missing_mirror_key_is_reported_in_japanese(self):
        """mirrors の項目のキーの書き忘れを、日本語のエラーにする。"""
        for key in ("source", "copy"):
            with self.subTest(key=key), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                config = self._full_config()
                config["projects"][0]["mirrors"] = [
                    {name: value for name, value in self.MIRROR[0].items() if name != key}]
                self._write_config(root, config)
                errors = CHECKER.validate(root)
                self.assertEqual(len(errors), 1, errors)
                self.assertIn(f"のmirrors[0]に{key}がありません", errors[0])

    def test_missing_nested_setting_key_is_reported_in_japanese(self):
        """registration と project_layout の中のキーの書き忘れも、日本語のエラーにする。"""
        cases = [
            ("registration", "registrationにtargetsがありません"),
            ("project_layout", "project_layoutにgitignore_referenceがありません"),
        ]
        for key, message in cases:
            with self.subTest(key=key), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                config = self._full_config()
                config[key] = {"メモ": "キーを書き忘れた設定"}
                self._write_config(root, config)
                self.assertEqual(CHECKER.validate(root),
                                 [f"config/teaching-materials.json:1: {message}"])

    def test_project_without_teacher_document_is_reported_in_japanese(self):
        """docs は学生向けと教員用の2つ。1つしか書かなくてもトレースバックにしない。"""
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config = self._full_config()
            config["projects"][0]["docs"] = ["docs/hello-monaca/index.html"]
            self._write_config(root, config)
            errors = CHECKER.validate(root)
            self.assertEqual(len(errors), 1, errors)
            self.assertIn("config/teaching-materials.json:1", errors[0])
            self.assertIn("学生向けの教科書と教員用ガイドを2つ書いてください", errors[0])

    def test_complete_config_reaches_the_other_checks(self):
        """必須キーがそろっていれば、入口で引き返さずに本体の検査へ進む。"""
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._write_config(root, self._full_config())
            errors = CHECKER.validate(root)
            # 教材の実体が1つも無いので、本体の検査が言う。入口の検査は何も言わない。
            self.assertTrue(
                any("完成プロジェクトZIPがありません" in error for error in errors), errors)
            self.assertEqual([error for error in errors if "設定に" in error], [])

    def test_empty_projects_is_accepted(self):
        """単元が1つもない、いまのリポジトリの形。README と docs だけで検査が通る。"""
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._write(root, "README.md", self._readme())
            self._write(root, "docs/assets/textbook.css", "body { margin: 0; }\n")
            self._write_config(root, {
                "course": {"name": "ハイブリッドアプリ開発技法", "total_sessions": 15, "minutes_per_session": 90},
                "scan_roots": ["README.md", "docs"],
                "terms": [],
                "registration": {"targets": [
                    {"path": "README.md", "requires": ["student_doc", "teacher_doc", "archive"]}]},
                "project_layout": {
                    "gitignore_reference": {"monaca": None, "flutter": None},
                    "untracked_parts": self.UNTRACKED_PARTS,
                    "untracked_names": self.UNTRACKED_NAMES,
                },
                "projects": [],
            })
            self.assertEqual(CHECKER.validate(root), [])


class ProgressKeyTest(unittest.TestCase):
    """チェック欄のあるページが、自分用の記録キーを持っているかの検査。

    docs/assets/textbook.js は、そのページで見つかった data-check だけを
    localStorage へ書き戻す。2つのページが同じキーを使うと、あとから開いた側が
    もう一方の記録を消す。キーは jec-hybrid-<スラッグ>-v<版> の形にする。
    """

    def _write(self, root: Path, name: str, text: str) -> Path:
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def _page(self, key: str | None, checks: int) -> str:
        body = "<body>" if key is None else f'<body data-progress-key="{key}">'
        boxes = "".join(f'<input type="checkbox" data-check="step-{i}">' for i in range(checks))
        return f'<!doctype html><html lang="ja">{body}<main>{boxes}</main></body></html>'

    def _check(self, root: Path) -> list[str]:
        errors: list[str] = []
        CHECKER.check_progress_keys(root, errors)
        return errors

    def test_page_with_checks_needs_a_key(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            self._write(root, "docs/hello-monaca/index.html", self._page(None, 2))
            errors = self._check(root)
            self.assertEqual(len(errors), 1, errors)
            self.assertIn('data-progress-key="jec-hybrid-…-v1"', errors[0])

    def test_page_without_checks_needs_no_key(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            self._write(root, "docs/common/submit.html", self._page(None, 0))
            self.assertEqual(self._check(root), [])

    def test_two_pages_must_not_share_a_key(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            self._write(root, "docs/hello-monaca/index.html", self._page("jec-hybrid-hello-monaca-v1", 2))
            self._write(root, "docs/common/setup.html", self._page("jec-hybrid-hello-monaca-v1", 1))
            errors = self._check(root)
            self.assertEqual(len(errors), 1, errors)
            self.assertIn("docs/hello-monaca/index.html", errors[0])

    def test_distinct_keys_pass(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            self._write(root, "docs/hello-monaca/index.html", self._page("jec-hybrid-hello-monaca-v1", 2))
            self._write(root, "docs/hello-flutter/index.html", self._page("jec-hybrid-hello-flutter-v2", 2))
            self._write(root, "docs/common/setup.html", self._page("jec-hybrid-common-setup-v1", 1))
            self.assertEqual(self._check(root), [])

    def test_key_of_the_wrong_form_is_rejected(self):
        """別の授業のキー（jec-kotlin-…）や、版のないキーは通さない。

        教科書は file:// で開くので、同じパソコンで開いたほかの授業の教材と保存場所が同じになる。
        docs/common/setup.html のように同じパスのページがあると、先頭が同じなら記録が混ざる。
        """
        for key in ("jec-kotlin-common-setup-v1", "jec-hybrid-hello-monaca", "jec-hybrid-Hello-Monaca-v1",
                    "jec-hybrid--v1", "hello-monaca-v1"):
            with self.subTest(key=key), tempfile.TemporaryDirectory() as name:
                root = Path(name)
                self._write(root, "docs/common/setup.html", self._page(key, 1))
                errors = self._check(root)
                self.assertEqual(len(errors), 1, errors)
                self.assertIn(f"data-progress-keyの形が違います: {key}", errors[0])


if __name__ == "__main__":
    unittest.main()
