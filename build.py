"""Build script – packages Luci2US into a standalone .exe using PyInstaller."""

from __future__ import annotations

import os
import subprocess
import sys


def main() -> None:
    root = os.path.dirname(os.path.abspath(__file__))
    sep = ";" if sys.platform == "win32" else ":"

    cmd: list[str] = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--windowed",
        "--name", "SW Rune Bot",
    ]

    # Icon (optional)
    icon = os.path.join(root, "assets", "icon.ico")
    if os.path.isfile(icon):
        cmd += ["--icon", icon]

    # Bundle data files (assets/monsters/ excluded – downloaded at runtime)
    data_files: list[tuple[str, str]] = [
        ("swex_plugin", "swex_plugin"),
    ]
    for fname in ("placeholder.png", "logo.png", "icon.ico"):
        path = os.path.join(root, "assets", fname)
        if os.path.isfile(path):
            data_files.append((os.path.join("assets", fname), "assets"))
    config_json = os.path.join(root, "config.json")
    if os.path.isfile(config_json):
        data_files.append(("config.json", "."))

    for src, dst in data_files:
        cmd += ["--add-data", f"{src}{sep}{dst}"]

    # Hidden imports
    cmd += [
        "--hidden-import", "customtkinter",
        "--hidden-import", "PIL",
    ]

    # Entry point
    cmd.append("app.py")

    print("Running:", " ".join(cmd))
    subprocess.run(cmd, cwd=root, check=True)
    print(f"\nDone! Executable is in: {os.path.join(root, 'dist')}")


if __name__ == "__main__":
    main()
