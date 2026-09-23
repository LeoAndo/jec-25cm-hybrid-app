"""完成プロジェクトの生成物を、系統とプロジェクト内の位置で見分ける。"""

from pathlib import Path
import re


LOCAL_PARTS = {".git", ".idea", "__pycache__"}
LOCAL_NAMES = {".DS_Store"}
GENERATED_DIRECTORIES = {
    "monaca": ("node_modules", "platforms", "plugins"),
    "flutter": (
        ".dart_tool", "build", "android/.gradle", "android/build", "android/app/build",
        "ios/build", "ios/Pods", "ios/.symlinks", "ios/Flutter/ephemeral",
    ),
}
GENERATED_FILES = {
    "monaca": (),
    "flutter": ("android/local.properties", ".flutter-plugins", ".flutter-plugins-dependencies"),
}


def project_kind(project: Path) -> str | None:
    """設定の登録前にもZIPを作れるよう、実物のマーカーと単元名から系統を選ぶ。"""
    if (project / "pubspec.yaml").is_file():
        return "flutter"
    if (project / "config.xml").is_file():
        return "monaca"
    match = re.match(r"^([MF])\d+", project.name)
    return {"M": "monaca", "F": "flutter"}.get(match[1]) if match else None


def excluded_project_path(relative: Path, kind: str | None) -> bool:
    """lib/build/ や www/plugins/ など、生成物と同名のソースは残す。"""
    if LOCAL_PARTS.intersection(relative.parts) or relative.name in LOCAL_NAMES:
        return True
    kinds = (kind,) if kind in GENERATED_DIRECTORIES else GENERATED_DIRECTORIES
    name = relative.as_posix()
    return any(
        name in GENERATED_FILES[item]
        or any(name.startswith(folder + "/") for folder in GENERATED_DIRECTORIES[item])
        for item in kinds
    )
