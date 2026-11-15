"""提出APKの証拠収集が原本・既存結果を壊さず、未確認を正しく残すことを確かめる。"""

import hashlib
import importlib.util
import json
import os
from pathlib import Path
from shutil import copy2, which
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from zipfile import ZipFile


SCRIPT = Path(__file__).with_name("student-apk-review.py")


@unittest.skipUnless(which("git"), "検証用リポジトリにはGitが必要です。")
class StudentApkReviewTest(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.parent = Path(temporary.name).resolve()
        self.root = self.parent / "repository"
        (self.root / "scripts").mkdir(parents=True)
        self.script = self.root / "scripts" / SCRIPT.name
        copy2(SCRIPT, self.script)
        (self.root / "config").mkdir()
        config = {"projects": [
            {"name": "F02StampRelease", "root": "F02StampRelease", "kind": "flutter",
             "application_id": "jp.ac.jec.f02_stamp_release",
             "docs": ["docs/stamp-release/index.html", "teacher/stamp-release/index.html"]},
            {"name": "F01StampBoard", "root": "F01StampBoard", "kind": "flutter",
             "application_id": "jp.ac.jec.f01_stamp_board",
             "docs": ["docs/stamp-board/index.html", "teacher/stamp-board/index.html"]},
            {"name": "M01OshiList", "kind": "monaca"},
            {"name": "UnknownKind", "kind": "native"},
            {"name": "MissingKind"},
        ]}
        self.config = self.root / "config/teaching-materials.json"
        self.config.write_text(json.dumps(config), encoding="utf-8")
        self.git("init")
        self.git("add", "scripts/student-apk-review.py", "config/teaching-materials.json")
        self.git("-c", "user.name=Test", "-c", "user.email=test@example.invalid",
                 "commit", "-m", "検証用の教材")
        self.git("tag", "materials-test")
        self.commit = self.git("rev-parse", "HEAD").stdout.strip()
        self.apk = self.parent / "submission.apk"
        with ZipFile(self.apk, "w") as archive:
            archive.writestr("AndroidManifest.xml", "fixture manifest")
            archive.writestr("classes.dex", "fixture dex")
            archive.writestr("lib/arm64-v8a/libapp.so", "fixture Dart AOT")
            archive.writestr("lib/arm64-v8a/libflutter.so", "fixture Flutter engine")
            archive.writestr("lib/x86_64/libapp.so", "fixture Dart AOT")
            archive.writestr("lib/x86_64/libflutter.so", "fixture Flutter engine")
            archive.writestr("assets/flutter_assets/AssetManifest.bin", "fixture assets")
        self.original = self.apk.read_bytes()
        self.output = self.parent / "results"
        self.analyzer = self.parent / "fake-apkanalyzer"
        self.analyzer.write_text(
            f"#!{sys.executable}\n"
            "import sys, time\n"
            "if 'manifest' in sys.argv:\n"
            " print('<manifest xmlns:android=\"http://schemas.android.com/apk/res/android\" '"
            "'package=\"jp.ac.jec.f01_stamp_board\" android:versionCode=\"1\">'"
            "'<uses-sdk android:minSdkVersion=\"24\" android:targetSdkVersion=\"36\"/>'"
            "'</manifest>')\n"
            "elif 'dex' in sys.argv:\n"
            " print('C jp.ac.jec.f01_stamp_board.MainActivity')\n"
            "else:\n"
            " print('<TextView/>')\n",
            encoding="utf-8",
        )
        self.analyzer.chmod(0o755)

    def git(self, *args):
        return subprocess.run(["git", *args], cwd=self.root, check=True,
                              capture_output=True, text=True)

    def run_review(self, *extra, output=None, ref="materials-test", analyzer=None):
        return subprocess.run(
            [sys.executable, str(self.script), "inspect", "--apk", str(self.apk),
             "--project", "F02StampRelease", "--baseline-ref", ref,
             "--output", str(output or self.output), "--apkanalyzer",
             str(analyzer or self.analyzer), *extra],
            cwd=self.root, capture_output=True, text=True,
        )

    def evidence(self):
        return json.loads((self.output / "evidence.json").read_text(encoding="utf-8"))

    def load_module(self):
        spec = importlib.util.spec_from_file_location("student_apk_review", self.script)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_collects_exact_baseline_and_does_not_grade_changed_package(self):
        self.config.write_text('{"projects": []}', encoding="utf-8")
        result = self.run_review("--resource", "/AndroidManifest.xml")
        self.assertEqual(result.returncode, 0, result.stderr)
        data = self.evidence()
        self.assertEqual(data["baseline"]["commit"], self.commit)
        self.assertEqual(data["apk"]["sha256"], hashlib.sha256(self.original).hexdigest())
        self.assertEqual(data["baseline"]["project"]["kind"], "flutter")
        self.assertEqual(data["baseline"]["project"]["application_id"], "jp.ac.jec.f02_stamp_release")
        self.assertEqual(data["manifest"]["application_id"], "jp.ac.jec.f01_stamp_board")
        self.assertEqual(data["manifest"]["target_sdk"], "36")
        self.assertEqual(data["dynamic_review"], "not_run")
        self.assertEqual(data["status"], "complete")
        self.assertEqual(len(data["commands"]), 3)
        self.assertEqual(self.apk.read_bytes(), self.original)
        self.assertTrue((self.output / "report.md").exists())
        self.assertTrue((self.output / "feedback.md").exists())

    def test_both_flutter_projects_are_allowed(self):
        for project in ("F01StampBoard", "F02StampRelease"):
            with self.subTest(project=project):
                output = self.parent / project
                result = self.run_review("--project", project, output=output)
                self.assertEqual(result.returncode, 0, result.stderr)
                data = json.loads((output / "evidence.json").read_text(encoding="utf-8"))
                self.assertEqual(data["baseline"]["project"]["name"], project)

    def test_non_flutter_is_rejected_before_reading_apk_or_creating_output(self):
        self.apk.write_bytes(b"invalid APK: this must not be read")
        for project in ("M01OshiList", "UnknownKind", "MissingKind"):
            with self.subTest(project=project):
                result = self.run_review("--project", project)
                self.assertEqual(result.returncode, 1)
                self.assertIn("kind が flutter", result.stderr)
                self.assertFalse(self.output.exists())

    def test_kind_comes_from_comparison_commit_instead_of_newer_commit(self):
        config = json.loads(self.config.read_text(encoding="utf-8"))
        config["projects"][0]["kind"] = "monaca"
        config["projects"][2]["kind"] = "flutter"
        self.config.write_text(json.dumps(config), encoding="utf-8")
        self.git("add", "config/teaching-materials.json")
        self.git("-c", "user.name=Test", "-c", "user.email=test@example.invalid",
                 "commit", "-m", "新しい版でkindを変える")
        latest = self.git("rev-parse", "HEAD").stdout.strip()
        self.assertNotEqual(latest, self.commit)
        # 過去版ではMonacaなので、現行版がFlutterでも受け付けない。
        result = self.run_review("--project", "M01OshiList")
        self.assertEqual(result.returncode, 1)
        self.assertIn("kind が flutter", result.stderr)
        self.assertFalse(self.output.exists())
        # 過去版ではFlutterなので、現行版がMonacaでも比較できる。
        result = self.run_review()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.evidence()["baseline"]["commit"], self.commit)
        self.assertEqual(self.evidence()["baseline"]["project"]["kind"], "flutter")

    def test_flutter_assets_and_abis_are_recorded_without_android_layout(self):
        result = self.run_review()
        self.assertEqual(result.returncode, 0, result.stderr)
        data = self.evidence()
        self.assertFalse(any(e["path"].startswith("res/layout/") for e in data["apk"]["entries"]))
        self.assertEqual(data["flutter"]["abis"], ["arm64-v8a", "x86_64"])
        self.assertEqual(len(data["flutter"]["native_libraries"]), 4)
        self.assertEqual(data["flutter"]["flutter_libraries"], data["flutter"]["native_libraries"])
        self.assertEqual(data["flutter"]["assets"], ["assets/flutter_assets/AssetManifest.bin"])
        self.assertEqual(data["warnings"], [])
        self.assertEqual(data["dynamic_review"], "not_run")

    def test_absent_flutter_files_are_observations_not_a_grade(self):
        with ZipFile(self.apk, "w") as archive:
            archive.writestr("AndroidManifest.xml", "fixture manifest")
            archive.writestr("classes.dex", "fixture dex")
        result = self.run_review()
        self.assertEqual(result.returncode, 0, result.stderr)
        data = self.evidence()
        self.assertTrue(all(files == [] for files in data["flutter"].values()))
        self.assertEqual(data["dynamic_review"], "not_run")
        report = (self.output / "report.md").read_text(encoding="utf-8")
        feedback = (self.output / "feedback.md").read_text(encoding="utf-8")
        self.assertIn("未評価", report)
        self.assertIn("資源の有無で採点しません", report)
        self.assertIn("教員確認前", feedback)
        self.assertIn("未確認", feedback)

    def test_missing_analyzer_is_partial_not_success(self):
        result = self.run_review(analyzer=self.parent / "missing")
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertEqual(self.evidence()["status"], "partial")
        self.assertNotIn("manifest", self.evidence())

    def test_failed_tool_retains_stderr_and_other_evidence(self):
        self.analyzer.write_text(f"#!{sys.executable}\nimport sys\n"
                                 "print('bad dex', file=sys.stderr)\nsys.exit(7)\n")
        result = self.run_review()
        self.assertEqual(result.returncode, 2)
        data = self.evidence()
        self.assertEqual(data["commands"]["dex-packages"]["exit_code"], 7)
        self.assertIn("bad dex", (self.output / "dex-packages.stderr.txt").read_text())
        self.assertEqual(data["apk"]["sha256"], hashlib.sha256(self.original).hexdigest())

    def test_timeout_is_partial(self):
        self.analyzer.write_text(f"#!{sys.executable}\nimport time\ntime.sleep(2)\n")
        result = self.run_review("--timeout", "0.05")
        self.assertEqual(result.returncode, 2)
        self.assertEqual(self.evidence()["commands"]["manifest"]["status"], "timeout")

    def test_malformed_successful_manifest_is_not_accepted(self):
        self.analyzer.write_text(f"#!{sys.executable}\nprint('not XML')\n")
        result = self.run_review()
        self.assertEqual(result.returncode, 2)
        self.assertEqual(self.evidence()["commands"]["manifest"]["status"], "invalid_output")

    def test_missing_sdk_values_remain_unknown(self):
        self.analyzer.write_text(f"#!{sys.executable}\n"
                                 "print('<manifest package=\"student.app\"/>')\n")
        result = self.run_review()
        self.assertEqual(result.returncode, 0, result.stderr)
        manifest = self.evidence()["manifest"]
        self.assertIsNone(manifest["min_sdk"])
        self.assertIsNone(manifest["target_sdk"])
        self.assertIsNone(manifest["version_name"])

    def test_truncated_tool_output_is_partial_and_preserves_command(self):
        self.analyzer.write_text(f"#!{sys.executable}\nimport sys\n"
                                 "print('x' * 1024)\nprint('y' * 1024, file=sys.stderr)\n")
        module = self.load_module()
        args = module.argparse.Namespace(
            apk=self.apk, baseline_ref="materials-test", project="F02StampRelease",
            provisional=False, resource=[], output=self.output,
            apkanalyzer=str(self.analyzer), timeout=5,
        )
        with patch.object(module, "MAX_TOOL_BYTES", 64):
            self.assertEqual(module.inspect(args), 2)
        data = self.evidence()
        self.assertEqual(data["status"], "partial")
        self.assertNotIn("manifest", data)
        for command in data["commands"].values():
            self.assertEqual(command["status"], "truncated")
            self.assertEqual(command["exit_code"], 0)
            self.assertEqual(command["command"][0], str(self.analyzer))
            self.assertEqual(command["limit_bytes"], 64)
            for stream in ("stdout", "stderr"):
                self.assertEqual((self.output / command[stream]).stat().st_size, 64)

    def test_existing_output_and_input_are_never_overwritten(self):
        self.output.mkdir()
        marker = self.output / "marker.txt"
        marker.write_text("prior review")
        result = self.run_review()
        self.assertEqual(result.returncode, 1)
        self.assertEqual(marker.read_text(), "prior review")
        self.assertEqual(self.apk.read_bytes(), self.original)
        self.assertEqual(self.run_review(output=self.apk).returncode, 1)

    def test_output_inside_repo_or_symlink_to_repo_is_rejected(self):
        self.assertEqual(self.run_review(output=self.root / "results").returncode, 1)
        alias = self.parent / "alias"
        alias.symlink_to(self.root, target_is_directory=True)
        self.assertEqual(self.run_review(output=alias / "results").returncode, 1)
        self.assertFalse((self.root / "results").exists())

    def test_output_inside_another_worktree_is_rejected(self):
        other = self.parent / "another-worktree"
        self.git("worktree", "add", "--detach", str(other), "HEAD")
        result = self.run_review(output=other / "results")
        self.assertEqual(result.returncode, 1)
        self.assertFalse((other / "results").exists())

    def test_output_inside_unrelated_git_repository_is_rejected(self):
        other = self.parent / "other-repository"
        other.mkdir()
        subprocess.run(["git", "init"], cwd=other, check=True, capture_output=True)
        result = self.run_review(output=other / "results")
        self.assertEqual(result.returncode, 1)
        self.assertFalse((other / "results").exists())

    def test_output_dangling_symlink_is_rejected(self):
        target = self.parent / "unused"
        self.output.symlink_to(target, target_is_directory=True)
        result = self.run_review()
        self.assertEqual(result.returncode, 1)
        self.assertTrue(self.output.is_symlink())
        self.assertFalse(target.exists())

    def test_unknown_baseline_and_project_create_no_output(self):
        result = self.run_review(ref="unknown-version")
        self.assertEqual(result.returncode, 1)
        self.assertFalse(self.output.exists())
        result = self.run_review("--project", "F99Unknown")
        self.assertEqual(result.returncode, 1)
        self.assertFalse(self.output.exists())

    def test_head_requires_provisional_and_records_it(self):
        self.assertEqual(self.run_review(ref="HEAD").returncode, 1)
        self.assertFalse(self.output.exists())
        self.assertEqual(self.run_review("--provisional", ref="HEAD").returncode, 0)
        self.assertTrue(self.evidence()["baseline"]["provisional"])

    def test_invalid_apk_creates_no_output(self):
        self.apk.write_bytes(b"not an apk")
        result = self.run_review()
        self.assertEqual(result.returncode, 1)
        self.assertFalse(self.output.exists())

    def test_zip_paths_cannot_escape_output(self):
        for name in ("../escaped.xml", "/absolute.xml", "res\\escaped.xml"):
            with self.subTest(path=name):
                self.apk.write_bytes(self.original)
                with ZipFile(self.apk, "a") as archive:
                    archive.writestr(name, "not allowed")
                result = self.run_review()
                self.assertEqual(result.returncode, 1)
                self.assertFalse(self.output.exists())
                self.assertFalse((self.parent / "escaped.xml").exists())

    def test_missing_manifest_and_duplicate_entries_create_no_output(self):
        with ZipFile(self.apk, "w") as archive:
            archive.writestr("classes.dex", "fixture")
        result = self.run_review()
        self.assertEqual(result.returncode, 1)
        self.assertFalse(self.output.exists())
        self.apk.write_bytes(self.original)
        with self.assertWarns(UserWarning), ZipFile(self.apk, "a") as archive:
            archive.writestr("AndroidManifest.xml", "duplicate")
        result = self.run_review()
        self.assertEqual(result.returncode, 1)
        self.assertFalse(self.output.exists())

    def test_inventory_limits_reject_small_fixtures_without_extracting(self):
        module = self.load_module()
        for limit in ("MAX_APK_BYTES", "MAX_UNCOMPRESSED_BYTES", "MAX_APK_ENTRIES"):
            with self.subTest(limit=limit), patch.object(module, limit, 1):
                with self.assertRaises(ValueError):
                    module.apk_inventory(self.apk)
                self.assertEqual(self.apk.read_bytes(), self.original)
                self.assertFalse(self.output.exists())

    def test_nonexistent_or_non_xml_resource_creates_no_output(self):
        for resource in ("/res/layout/missing.xml", "classes.dex"):
            with self.subTest(resource=resource):
                result = self.run_review("--resource", resource)
                self.assertEqual(result.returncode, 1)
                self.assertFalse(self.output.exists())

    def test_sdk_analyzer_uses_numeric_version_order(self):
        module = self.load_module()
        sdk = self.parent / "sdk"
        for version in ("9.0", "21.0"):
            executable = sdk / "cmdline-tools" / version / "bin/apkanalyzer"
            executable.parent.mkdir(parents=True)
            executable.write_text("fake executable")
            executable.chmod(0o755)
        with patch.object(module.shutil, "which", return_value=None), patch.dict(
                os.environ, {"ANDROID_HOME": str(sdk)}):
            self.assertEqual(module.find_analyzer(None),
                             str(sdk / "cmdline-tools/21.0/bin/apkanalyzer"))


if __name__ == "__main__":
    unittest.main()
