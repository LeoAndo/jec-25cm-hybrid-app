"""完成版ZIPの生成条件と、配布対象の選別を検証する。"""

from pathlib import Path
import os
from shutil import copy2, which
import subprocess
import sys
import tempfile
import unittest
from zipfile import ZipFile


SCRIPT = Path(__file__).with_name("package-project.py")
GIT = which("git")


@unittest.skipUnless(GIT, "テスト用リポジトリの作成にはGitが必要です。")
class PackageProjectTest(unittest.TestCase):
    """実際のGitと一時フォルダで、配布用スクリプトを実行する。"""

    def setUp(self):
        """各テスト専用のソースと既存ZIPを用意する。"""
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.parent = Path(temporary.name)
        self.root = self.parent / "source"
        (self.root / "scripts").mkdir(parents=True)
        copy2(SCRIPT, self.root / "scripts" / SCRIPT.name)
        copy2(SCRIPT.with_name("project_files.py"), self.root / "scripts/project_files.py")
        self.output = self.root / "docs/hello-monaca/downloads/M01HelloMonaca.zip"
        self.output.parent.mkdir(parents=True)
        self.output.write_bytes(b"previous archive")

    def git(self, *args, cwd=None):
        """指定フォルダでGitを実行し、失敗はテストエラーにする。"""
        return subprocess.run(
            [GIT, *args], cwd=cwd or self.root, check=True,
            capture_output=True, text=True,
        )

    def run_package(self, *args, env=None):
        """独立したPythonプロセスで配布スクリプトを実行する。"""
        if not args:
            args = ("--project", "M01HelloMonaca", "--output", str(self.output))
        return subprocess.run(
            [sys.executable, str(self.root / "scripts" / SCRIPT.name), *args],
            cwd=self.root, env=env, capture_output=True, text=True,
        )

    def assert_rejected(self, result, message):
        """日本語の案内を返し、既存ZIPを保持することを確認する。"""
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(message, result.stderr)
        self.assertNotIn("Traceback", result.stderr)
        self.assertEqual(self.output.read_bytes(), b"previous archive")

    def test_no_git_metadata(self):
        """GitHubのDownload ZIPに相当するフォルダを拒否する。"""
        self.assert_rejected(self.run_package(), "git clone")

    def test_source_inside_another_repository(self):
        """上位フォルダのGit管理情報を誤って使用しない。"""
        self.git("init", cwd=self.parent)
        self.assert_rejected(self.run_package(), "ルートではありません")

    def test_git_not_installed(self):
        """Gitが見つからない場合にインストールを案内する。"""
        env = dict(os.environ, PATH="")
        self.assert_rejected(self.run_package(env=env), "Gitが見つかりません")

    def test_no_tracked_project_files(self):
        """配布対象がない場合に既存ZIPを維持する。"""
        self.git("init")
        self.assert_rejected(self.run_package(), "プロジェクトが見つかりません")

    def test_project_and_output_are_required(self):
        """既定の単元を持たない。引数なしでは何も作り直さない。

        単元が増えたときに、既定の単元だけを静かに作り直す事故を防ぐための確認。
        """
        self.git("init")
        result = self.run_package("--project", "M01HelloMonaca")
        self.assert_rejected(result, "--output")
        self.assert_rejected(self.run_package("--output", str(self.output)), "--project")

    def write_project(self, project, names):
        """プロジェクトのフォルダに、中身が "original" のファイルを並べる。"""
        for name in names:
            path = self.root / project / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("original")
        return self.root / project

    def test_tracked_sources_only_and_repeatable_archive(self):
        """編集済みの管理対象と実行権限を保持し、ローカル状態を除外する。

        Monacaのプロジェクトを、Monaca CLI などでローカルに展開したときにできる
        node_modules・platforms・plugins も配らない。
        """
        self.git("init")
        project = self.write_project("M01HelloMonaca", [
            "config.xml", "www/index.html", "www/js/app.js", "tools/serve.sh",
            "node_modules/cordova/index.js", "platforms/android/build.gradle",
            "plugins/fetch.json", ".idea/misc.xml",
        ])
        (project / "tools/serve.sh").chmod(0o744)
        (project / "www/js/app.js").chmod(0o600)
        self.git("add", "M01HelloMonaca")
        (project / "www/js/app.js").write_text("edited")
        (project / "www/untracked.html").write_text("not for distribution")
        result = self.run_package()
        self.assertEqual(result.returncode, 0, result.stderr)
        with ZipFile(self.output) as archive:
            self.assertEqual(archive.namelist(), [
                "M01HelloMonaca/config.xml",
                "M01HelloMonaca/tools/serve.sh",
                "M01HelloMonaca/www/index.html",
                "M01HelloMonaca/www/js/app.js",
            ])
            self.assertEqual(archive.read("M01HelloMonaca/www/js/app.js"), b"edited")
            mode = archive.getinfo("M01HelloMonaca/tools/serve.sh").external_attr >> 16
            self.assertEqual(mode, 0o100755)
            source_mode = archive.getinfo("M01HelloMonaca/www/js/app.js").external_attr >> 16
            self.assertEqual(source_mode, 0o100644)
        first = self.output.read_bytes()
        self.assertEqual(self.run_package().returncode, 0)
        self.assertEqual(self.output.read_bytes(), first)

    def test_flutter_build_outputs_are_excluded(self):
        """Flutterのビルド出力とローカルSDK設定が誤ってcommitされていても配らない。

        build は Gradle と Xcode の出力、.dart_tool は Flutter の作業フォルダ、
        Pods・.symlinks・ephemeral は iOS のビルドで、local.properties は Android のSDKの場所。
        """
        self.git("init")
        self.write_project("F01HelloFlutter", [
            "pubspec.yaml", "lib/main.dart",
            ".dart_tool/package_config.json", "build/app/outputs/app.apk",
            "android/.gradle/cache.bin", "android/local.properties",
            "android/build/cache.bin", "android/app/build/app.apk", "ios/build/app.bin",
            ".flutter-plugins", ".flutter-plugins-dependencies", ".DS_Store",
            "ios/Pods/Manifest.lock", "ios/.symlinks/plugins/x/pubspec.yaml",
            "ios/Flutter/ephemeral/flutter_lldbinit",
        ])
        self.git("add", "-f", "F01HelloFlutter")
        output = self.root / "docs/hello-flutter/downloads/F01HelloFlutter.zip"
        result = self.run_package("--project", "F01HelloFlutter", "--output", str(output))
        self.assertEqual(result.returncode, 0, result.stderr)
        with ZipFile(output) as archive:
            self.assertEqual(archive.namelist(), [
                "F01HelloFlutter/lib/main.dart",
                "F01HelloFlutter/pubspec.yaml",
            ])

    def test_source_folders_with_generated_names_are_preserved(self):
        """生成物と同名でも、Flutterのlib/やMonacaのwww/のソースは配布する。"""
        self.git("init")
        for project, source_root, marker, suffix in (
                ("F01HelloFlutter", "lib", "pubspec.yaml", "dart"),
                ("M01HelloMonaca", "www", "config.xml", "js")):
            with self.subTest(project=project):
                files = [marker, *[
                    f"{source_root}/{folder}/source.{suffix}"
                    for folder in ("plugins", "platforms", "build", "Pods", "ephemeral", "node_modules")
                ], f"{source_root}/local.properties"]
                self.write_project(project, files)
                self.git("add", "-f", project)
                output = self.parent / f"{project}.zip"
                result = self.run_package("--project", project, "--output", str(output))
                self.assertEqual(result.returncode, 0, result.stderr)
                with ZipFile(output) as archive:
                    self.assertEqual(archive.namelist(), sorted(f"{project}/{name}" for name in files))

    def test_generated_directories_are_specific_to_the_project_kind(self):
        """Flutter直下のplugins/やMonaca直下のbuild/を、別系統の生成物と混同しない。"""
        self.git("init")
        for project, files in (
                ("F01HelloFlutter", ["pubspec.yaml", "plugins/helper.dart", "platforms/note.txt"]),
                ("M01HelloMonaca", ["config.xml", "build/note.txt", "ios/Pods/note.txt"])):
            with self.subTest(project=project):
                self.write_project(project, files)
                self.git("add", "-f", project)
                output = self.parent / f"{project}.zip"
                result = self.run_package("--project", project, "--output", str(output))
                self.assertEqual(result.returncode, 0, result.stderr)
                with ZipFile(output) as archive:
                    self.assertEqual(archive.namelist(), sorted(f"{project}/{name}" for name in files))

    def test_only_the_named_project_is_packaged(self):
        """--project に渡したフォルダだけをZIPにする。ほかの単元やテンプレートは混ぜない。"""
        self.git("init")
        self.write_project("M01HelloMonaca", ["www/index.html"])
        self.write_project("MonacaTemplate", ["www/index.html"])
        self.write_project("F01HelloFlutter", ["lib/main.dart"])
        self.git("add", "M01HelloMonaca", "MonacaTemplate", "F01HelloFlutter")
        self.assertEqual(self.run_package().returncode, 0)
        with ZipFile(self.output) as archive:
            self.assertEqual(archive.namelist(), ["M01HelloMonaca/www/index.html"])


if __name__ == "__main__":
    unittest.main()
