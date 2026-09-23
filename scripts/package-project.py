"""教員用：学生に配布する完成プロジェクトを作成する。

単元のプロジェクトは、Monaca系（Monaca クラウドIDE）とFlutter系（Visual Studio Code）の
2系統がある。どちらも「Git管理下のファイルだけを、IDEの設定とビルド出力を除いてZIPにする」で
同じなので、プロジェクト名を引数で受け取る1つのスクリプトにしている。

  python3 scripts/package-project.py --project M01HelloMonaca \\
      --output docs/hello-monaca/downloads/M01HelloMonaca.zip
"""

import argparse
from pathlib import Path
from shutil import which
import subprocess
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo


# ZIPに入れないフォルダとファイル。scripts/check-teaching-materials.py の
# IGNORED_ARCHIVE_PARTS・IGNORED_ARCHIVE_NAMES と同じにしておく（違うと、作ったZIPが検査で落ちる）。
# build は Flutter（Gradle と Xcode）のビルド出力、.dart_tool は Flutter の作業フォルダ、
# Pods・.symlinks・ephemeral は iOS のビルドで作られるもの、
# node_modules・platforms・plugins は Monaca をローカルで扱ったときの残り。どれも配らない。
EXCLUDED_PARTS = {".dart_tool", ".gradle", ".idea", ".symlinks", "Pods", "build", "ephemeral",
                  "node_modules", "platforms", "plugins"}
# 学生のパソコンのSDKの場所を書いたファイル。配ると、学生の環境で読み違える。
EXCLUDED_NAMES = {"local.properties"}

root = Path(__file__).resolve().parents[1]
git = which("git")
if git is None:
    raise SystemExit("Gitが見つかりません。Gitをインストールしてから再実行してください。")

try:
    git_root = subprocess.check_output(
        [git, "rev-parse", "--show-toplevel"], cwd=root, stderr=subprocess.PIPE
    ).decode().strip()
    if Path(git_root).resolve() != root:
        raise SystemExit(
            "このフォルダはGitリポジトリのルートではありません。"
            "READMEの手順でgit cloneした教材を使ってください。"
        )
except (OSError, subprocess.CalledProcessError):
    raise SystemExit(
        "Git管理情報を読み取れません。"
        "ZIPの再生成には、READMEの手順でgit cloneした教材が必要です。"
    ) from None


def package(project, output):
    """Gitで管理されたプロジェクトだけを、IDE設定を除外してZIPにする。"""
    try:
        tracked = subprocess.check_output(
            [git, "ls-files", "-z", "--", project], cwd=root
        ).decode().split("\0")
    except (OSError, subprocess.CalledProcessError):
        raise SystemExit("Git管理情報を読み取れません。ZIPを再生成できません。") from None
    files = [
        name for name in tracked
        if name and not EXCLUDED_PARTS.intersection(Path(name).parts)
        and Path(name).name not in EXCLUDED_NAMES
    ]
    if not files:
        raise SystemExit("配布対象のプロジェクトが見つかりません。")

    output.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(output, "w", compression=ZIP_DEFLATED) as archive:
        for name in sorted(files):
            source = root / name
            info = ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.create_system = 3
            # Gitで保持されないグループ・他ユーザーの権限差をZIPへ持ち込まない。
            mode = 0o100755 if source.stat().st_mode & 0o100 else 0o100644
            info.external_attr = mode << 16
            info.compress_type = ZIP_DEFLATED
            archive.writestr(info, source.read_bytes())
    try:
        shown = output.relative_to(root)
    except ValueError:
        # リポジトリの外へ出力したときは、絶対パスのまま表示する。
        shown = output
    print(f"作成しました：{shown}（{len(files)}ファイル）")


def main():
    # 既定値は持たせない。単元が増えたときに、既定の単元だけ静かに作り直す事故を防ぐ。
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", required=True, help="ZIPにするプロジェクトのフォルダ（例：M01HelloMonaca）")
    parser.add_argument("--output", type=Path, required=True, help="書き出すZIPのパス")
    args = parser.parse_args()
    package(args.project, args.output.resolve())


if __name__ == "__main__":
    main()
