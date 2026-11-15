"""Flutter提出APKの静的な根拠を収集する。採点・インストール・学生への送信は行わない。"""

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from zipfile import BadZipFile, ZipFile


ROOT = Path(__file__).resolve().parents[1]
MAX_APK_BYTES = 1024 * 1024 * 1024
MAX_UNCOMPRESSED_BYTES = 2 * MAX_APK_BYTES
MAX_APK_ENTRIES = 100000
MAX_TOOL_BYTES = 10 * 1024 * 1024
ANDROID = "{http://schemas.android.com/apk/res/android}"


def git(*args):
    return subprocess.check_output(
        ["git", *args], cwd=ROOT, stderr=subprocess.PIPE, text=True,
    ).strip()


def baseline(ref, project_name, provisional):
    if ref == "HEAD" and not provisional:
        raise ValueError("版が不明でHEADを使う場合は --provisional を付けてください。")
    commit = git("rev-parse", "--verify", "--end-of-options", f"{ref}^{{commit}}")
    config = json.loads(git("show", f"{commit}:config/teaching-materials.json"))
    project = next((p for p in config["projects"] if p["name"] == project_name), None)
    if project is None:
        raise ValueError("指定の教材版に --project と一致する単元がありません。")
    if project.get("kind") != "flutter":
        raise ValueError("比較版configの kind が flutter の単元だけを確認できます。Monacaは人間が確認します。")
    return {
        "requested_ref": ref, "commit": commit, "provisional": provisional,
        "project": project,
    }


def reserve_output(path):
    output = path.expanduser().resolve()
    # 別worktreeも含め、どのGit作業ツリーにも個別の提出物を出力しない。
    roots = [ROOT]
    for field in git("worktree", "list", "--porcelain", "-z").split("\0"):
        if field.startswith("worktree "):
            roots.append(Path(field[len("worktree "):]).resolve())
    if any(output == root or root in output.parents for root in roots):
        raise ValueError("出力先はリポジトリ・worktreeの外にしてください。")
    if any((parent / ".git").exists() for parent in (output, *output.parents)):
        raise ValueError("出力先はGit管理されたフォルダの外にしてください。")
    if path.expanduser().is_symlink() or output.exists():
        raise ValueError("出力先は存在しない新しいフォルダを指定してください。")
    output.mkdir(parents=True, exist_ok=False)
    return output


def apk_inventory(apk):
    if not apk.is_file() or apk.suffix.lower() != ".apk":
        raise ValueError("--apk には既存のAPKファイルを指定してください。")
    size = apk.stat().st_size
    if size > MAX_APK_BYTES:
        raise ValueError("APKが1 GiBを超えています。個別に確認してください。")
    digest = hashlib.sha256()
    with apk.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    with ZipFile(apk) as archive:
        entries = archive.infolist()
        names = [entry.filename for entry in entries]
        if "AndroidManifest.xml" not in names:
            raise ValueError("APK内にAndroidManifest.xmlがありません。")
        if len(entries) > MAX_APK_ENTRIES or sum(e.file_size for e in entries) > MAX_UNCOMPRESSED_BYTES:
            raise ValueError("APKの展開サイズまたは項目数が上限を超えています。")
        if len(set(names)) != len(names):
            raise ValueError("APK内に重複したファイル名があります。")
        for name in names:
            if name.startswith("/") or ".." in PurePosixPath(name).parts or "\\" in name:
                raise ValueError("APK内に安全に参照できないファイル名があります。")
        inventory = [{"path": e.filename, "size": e.file_size,
                      "compressed_size": e.compress_size, "crc32": f"{e.CRC:08x}"}
                     for e in entries]
    return {"path": str(apk), "size": size, "sha256": digest.hexdigest(),
            "entries": inventory}


def flutter_inventory(entries):
    """ZIP内で観測したファイルを分類する。Dartコードや変更内容は復元しない。"""
    native_libraries = sorted(
        entry["path"] for entry in entries
        if re.fullmatch(r"lib/[^/]+/[^/]+\.so", entry["path"])
    )
    return {
        "abis": sorted({path.split("/")[1] for path in native_libraries}),
        "native_libraries": native_libraries,
        "flutter_libraries": [path for path in native_libraries
                              if PurePosixPath(path).name in ("libapp.so", "libflutter.so")],
        "assets": sorted(entry["path"] for entry in entries
                         if entry["path"].startswith("assets/flutter_assets/")
                         and not entry["path"].endswith("/")),
    }


def find_analyzer(explicit):
    if explicit:
        path = Path(explicit).expanduser().resolve()
        return str(path) if path.is_file() and os.access(path, os.X_OK) else None
    executable = shutil.which("apkanalyzer")
    if executable:
        return executable
    sdk = Path(os.environ.get("ANDROID_HOME") or os.environ.get("ANDROID_SDK_ROOT")
               or Path.home() / "Library/Android/sdk")
    candidates = [sdk / "cmdline-tools/latest/bin/apkanalyzer"]
    candidates.extend(sorted(
        sdk.glob("cmdline-tools/*/bin/apkanalyzer"),
        key=lambda p: tuple(int(n) for n in re.findall(r"\d+", p.parents[1].name)),
        reverse=True,
    ))
    return next((str(p) for p in candidates if p.is_file() and os.access(p, os.X_OK)), None)


def collect(command, output, name, timeout):
    stdout_path, stderr_path = output / f"{name}.txt", output / f"{name}.stderr.txt"
    result = {"command": command, "stdout": stdout_path.name, "stderr": stderr_path.name}
    with stdout_path.open("wb") as stdout, stderr_path.open("wb") as stderr:
        try:
            completed = subprocess.run(command, stdout=stdout, stderr=stderr, timeout=timeout)
            result.update(status="ok" if completed.returncode == 0 else "failed",
                          exit_code=completed.returncode)
        except subprocess.TimeoutExpired:
            result.update(status="timeout", exit_code=None)
        except OSError as exc:
            stderr.write(str(exc).encode("utf-8"))
            result.update(status="failed", exit_code=None)
    for path in (stdout_path, stderr_path):
        # 保存する証拠の上限。実行中のディスク使用量を制限する処理ではない。
        if path.stat().st_size > MAX_TOOL_BYTES:
            with path.open("r+b") as stream:
                stream.truncate(MAX_TOOL_BYTES)
            result.update(status="truncated", limit_bytes=MAX_TOOL_BYTES)
    return result


def manifest_details(path):
    manifest = ET.fromstring(path.read_text(encoding="utf-8"))
    if manifest.tag != "manifest" or not manifest.get("package"):
        raise ValueError("manifestのpackageを読み取れません。")
    sdk = manifest.find("uses-sdk")
    return {
        "application_id": manifest.get("package"),
        "version_code": manifest.get(ANDROID + "versionCode"),
        "version_name": manifest.get(ANDROID + "versionName"),
        "min_sdk": sdk.get(ANDROID + "minSdkVersion") if sdk is not None else None,
        "target_sdk": sdk.get(ANDROID + "targetSdkVersion") if sdk is not None else None,
        "permissions": [p.get(ANDROID + "name") for p in manifest.findall("uses-permission")],
    }


def write_reports(output, data):
    base = data["baseline"]
    project = base["project"]
    mode = "暫定比較（学生が使った教材版は未確認）" if base["provisional"] else "指定版との比較"
    report = f"""# 提出APKの確認記録（教員用・未評価）

- APK SHA-256：`{data['apk']['sha256']}`
- 単元：{project['name']}
- 比較基準：`{base['commit']}`（{mode}）
- 教材：{', '.join(project['docs'])}
- 比較元ソース：`{project['root']}`
- 収集状態：{data['status']}（詳細は evidence.json の commands と warnings）
- 動作確認：未確認。静的情報の取得は、起動・正常動作を保証しません。

## 教材からの変更

| 確度（確認できた変更／変更の可能性／未確認） | 教材の内容 | 提出物の内容 | 根拠のファイル・位置 |
| --- | --- | --- | --- |
| 未確認 | 教材を読む | 提出物と比べる | 未記入 |

APKのビルド差・署名・ライブラリの差を学生の工夫として数えません。
変更した本人、元ソースの全内容や行番号はAPKだけでは確定できません。
releaseのDart本体は機械語です。DEXやAndroidのlayout XMLだけでは変更を復元できません。
Flutter関連資源・ABIの一覧は evidence.json の flutter にあります。資源の有無で採点しません。
Androidのlayout XMLがないことは、不足とは扱いません。実画面・操作と比較版教材を照合します。
applicationIdが教材と異なることだけでは、誤提出や不具合と判断しません。

## 動作・クラッシュ・その他の実行エラー

| 操作と期待結果 | 状態 | 実際の結果 | 根拠・時刻・環境 |
| --- | --- | --- | --- |
| 未実施 | 未確認 | 未確認 | 未記入 |

クラッシュは対象プロセスと実行区間を照合し、例外の連鎖（Caused by）を読む。
Flutterのフレームワークエラー、未処理Dart例外、灰色のエラー画面、Android側例外、
native crash、ANR、通信失敗を分けて記録します。プロセス存続やFATAL EXCEPTIONがないことだけで正常としません。
Dartの難読化スタックには同一ビルド・ABIのsymbolsと flutter symbolize が必要な場合があります。
Android R8のmapping.txtとは別物です。元Dartソースなしで修正行番号を作りません。
修正場所は確定と候補を分け、再現できない場合は次に必要な操作・ソースを記す。

## 講評前に残っている確認

- 対象の教科書、教員用ガイドの教材方針、提出課題の条件を読む。
- 提出APKそのものをAndroidで動かし、画面・操作・Flutterログを確認する（iOSや教材ソースの実行で代用しない）。
- 根拠と照合し、feedback.md の未記入部分を埋める。採点・送信はしていません。
- 未評価テンプレートのまま返却しない。必須修正と任意改善を分け、教員が確認してから返却する。
"""
    feedback = """# 学生への返却文案（未評価・教員確認前）

## 確認できた工夫

未記入。文字の色を変えるだけでも課題のアレンジとして扱います。
変更量・機能追加の多さによる評価はしません。

## 直す必要がある点

未確認。不具合があれば、再現操作・起きること・修正候補を記入します。

## 次に試せるアレンジ（任意）

未記入。どの画面・操作をどう変えると何が良くなるかを短く書きます。

## 確認できなかった点

画面・動作・クラッシュ・その他の実行エラーは未確認です。
この文案は未評価の記録用紙です。根拠を確認して記入し、教員が確認するまで返却しません。
"""
    (output / "report.md").write_text(report, encoding="utf-8")
    (output / "feedback.md").write_text(feedback, encoding="utf-8")


def inspect(args):
    apk = args.apk.expanduser().resolve()
    base = baseline(args.baseline_ref, args.project, args.provisional)
    inventory = apk_inventory(apk)
    resources = []
    known_paths = {entry["path"] for entry in inventory["entries"]}
    for resource in args.resource:
        path = resource.lstrip("/")
        if path not in known_paths or not path.endswith(".xml"):
            raise ValueError("--resource はAPK内にあるXMLのパスを指定してください。")
        resources.append("/" + path)
    output = reserve_output(args.output)
    data = {"schema_version": 1, "created_at": datetime.now(timezone.utc).isoformat(),
            "apk": inventory, "baseline": base, "status": "complete",
            "flutter": flutter_inventory(inventory["entries"]),
            "dynamic_review": "not_run", "commands": {}, "warnings": []}
    analyzer = find_analyzer(args.apkanalyzer)
    if analyzer is None:
        data["warnings"].append("apkanalyzerが見つかりません。Manifest・DEXは未確認です。")
        data["status"] = "partial"
    else:
        commands = [("manifest", ["manifest", "print"]),
                    ("dex-packages", ["dex", "packages", "--defined-only"])]
        commands.extend((f"resource-{i:03}", ["resources", "xml", "--file", resource])
                        for i, resource in enumerate(resources, 1))
        for name, arguments in commands:
            data["commands"][name] = collect(
                [analyzer, *arguments, str(apk)], output, name, args.timeout,
            )
        if data["commands"]["manifest"]["status"] == "ok":
            try:
                data["manifest"] = manifest_details(output / "manifest.txt")
            except (ET.ParseError, UnicodeError, ValueError) as exc:
                data["commands"]["manifest"]["status"] = "invalid_output"
                data["warnings"].append(str(exc))
        if any(c["status"] != "ok" for c in data["commands"].values()):
            data["status"] = "partial"
            data["warnings"].append("収集に失敗した項目があります。commandsと標準エラーを確認してください。")
    (output / "evidence.json").write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8",
    )
    write_reports(output, data)
    print(f"静的情報を保存しました：{output}（{data['status']}、評価・動作確認は未実施）")
    return 0 if data["status"] == "complete" else 2


def positive_timeout(value):
    timeout = float(value)
    if not 0 < timeout <= 300:
        raise argparse.ArgumentTypeError("timeoutは0より大きく300秒以下にしてください。")
    return timeout


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    command = commands.add_parser("inspect", help="APKの静的な証拠と未評価の記録用紙を作る")
    command.add_argument("--apk", type=Path, required=True)
    command.add_argument("--project", required=True)
    command.add_argument("--baseline-ref", required=True, help="学生が使った教材のtagまたはcommit")
    command.add_argument("--output", type=Path, required=True, help="リポジトリ外の新規フォルダ")
    command.add_argument("--provisional", action="store_true", help="教材版不明の暫定比較と記録する")
    command.add_argument("--apkanalyzer", help="APK Analyzer実行ファイルのパス")
    command.add_argument("--resource", action="append", default=[], help="収集するAPK内XML（繰り返し可）")
    command.add_argument("--timeout", type=positive_timeout, default=60, help="コマンドごとの上限秒（既定60）")
    args = parser.parse_args()
    try:
        return inspect(args)
    except (OSError, ValueError, KeyError, BadZipFile, subprocess.CalledProcessError) as exc:
        print(f"収集できませんでした：{exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
