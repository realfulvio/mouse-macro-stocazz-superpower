#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
if [[ "$(uname -s)" != Linux ]]; then
    echo 'Run this script on Linux.' >&2
    exit 1
fi
python3 -m venv .venv_linux
.venv_linux/bin/python -m pip install -r requirements.txt 'pyinstaller==6.22.3'
.venv_linux/bin/python -m unittest discover -v
.venv_linux/bin/python build_release.py
