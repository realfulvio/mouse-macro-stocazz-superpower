"""Actual Flet UI preview on localhost; recording and playback are disabled."""
import argparse
from pathlib import Path
from unittest.mock import MagicMock

import flet as ft
import uvicorn
import main as app


def disabled(*args, **kwargs):
    raise RuntimeError('Desktop recording and playback are disabled in this UI preview.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--language', choices=['it', 'en'], default='it')
    parser.add_argument('--port', type=int, default=8551)
    args = parser.parse_args()
    app.make_recorder = disabled
    app.make_player = disabled
    if app.current_platform() == 'windows':
        import macro.windows_backend as backend
        backend.GlobalHotkeys = MagicMock()
        backend.GlobalHotkeys.return_value.failed = []
    server = ft.run(lambda page: app.main(page, language=args.language),
                    assets_dir=str(Path(__file__).parent / 'assets'),
                    no_cdn=True, export_asgi_app=True)
    uvicorn.run(server, host='127.0.0.1', port=args.port)
