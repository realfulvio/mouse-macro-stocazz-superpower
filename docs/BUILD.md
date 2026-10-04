# Build from source

For the current native Windows panel, use [v0.16 build instructions](../BUILD-v0.16-by-codex.md). The portable ZIP includes its Python runtime and needs no first-run download.

Linux retains the historical Flet interface. Install `requirements.txt`, run `python -m unittest discover -v`, then use `build_release.py` or `build_linux.sh` on Linux. These historical builders do not build the native Windows v0.16 package.

Acceptance outcomes are tied to the exact release ZIP hash, not to arbitrary later rebuilds.
