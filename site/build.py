"""Build the GitHub Pages site into _site/ with the current release links.

Versions and download URLs come from the GitHub releases API at build time, so
the page needs no JavaScript or network request to stay current. Without network
(local preview) the fallback values below are used.

Usage: python site/build.py [--out _site] [--offline]
"""
import argparse
import json
import os
import re
import shutil
import urllib.request
from pathlib import Path

REPO = 'realfulvio/mouse-macro-stocazz-superpower'
BASE = f'https://github.com/{REPO}/releases'
FALLBACK = {'windows': 'v1.2.5', 'linux': 'linux-v1.2.0'}
SITE = Path(__file__).resolve().parent


def fetch_releases():
    request = urllib.request.Request(f'https://api.github.com/repos/{REPO}/releases?per_page=50',
                                     headers={'Accept': 'application/vnd.github+json'})
    token = os.environ.get('GITHUB_TOKEN')
    if token:
        request.add_header('Authorization', f'Bearer {token}')
    with urllib.request.urlopen(request, timeout=20) as response:
        return json.load(response)


def newest(releases, prefix):
    pattern = re.compile(rf'^{prefix}(\d+)\.(\d+)\.(\d+)$')
    found = [r for r in releases if not r['draft'] and not r['prerelease'] and pattern.match(r['tag_name'])]
    return max(found, key=lambda r: tuple(map(int, pattern.match(r['tag_name']).groups())), default=None)


def asset(release, pattern, fallback):
    for item in (release or {}).get('assets', []):
        if re.fullmatch(pattern, item['name']):
            return item['browser_download_url']
    return fallback


def values(releases):
    win = newest(releases, 'v')
    lnx = newest(releases, 'linux-v')
    win_tag = win['tag_name'] if win else FALLBACK['windows']
    lnx_tag = lnx['tag_name'] if lnx else FALLBACK['linux']
    win_url, lnx_url = f'{BASE}/tag/{win_tag}', f'{BASE}/tag/{lnx_tag}'
    win_ver, lnx_ver = win_tag[1:], lnx_tag[len('linux-v'):]
    dl_win, dl_lnx = f'{BASE}/download/{win_tag}', f'{BASE}/download/{lnx_tag}'
    return {
        'WIN_TAG': win_tag, 'WIN_VER': win_ver, 'WIN_URL': win_url,
        'WIN_ZIP_URL': asset(win, rf'MouseMacroStocazzSuperpower-Windows-{re.escape(win_tag)}\.zip',
                             f'{dl_win}/MouseMacroStocazzSuperpower-Windows-{win_tag}.zip'),
        'LNX_TAG': lnx_tag, 'LNX_VER': lnx_ver, 'LNX_URL': lnx_url,
        'LNX_APPIMAGE_URL': asset(lnx, r'.*\.AppImage', f'{dl_lnx}/MouseMacroStocazzSuperpower-Linux-v{lnx_ver}-x86_64.AppImage'),
        'LNX_FLATPAK_URL': asset(lnx, r'.*\.flatpak', f'{dl_lnx}/MouseMacroStocazzSuperpower-Linux-v{lnx_ver}.flatpak'),
        'LNX_TAR_URL': asset(lnx, r'.*\.tar\.gz', f'{dl_lnx}/MouseMacroStocazzSuperpower-Linux-v{lnx_ver}.tar.gz'),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--out', type=Path, default=Path('_site'))
    parser.add_argument('--offline', action='store_true')
    args = parser.parse_args()
    releases = []
    if not args.offline:
        try:
            releases = fetch_releases()
        except OSError as error:
            if os.environ.get('CI'):
                raise
            print(f'releases API unavailable ({error}); using fallback versions')
    filled = values(releases)
    html = (SITE / 'index.html').read_text(encoding='utf-8')
    for key, value in filled.items():
        html = html.replace(f'%%{key}%%', value)
    left = re.findall(r'%%[A-Z_]+%%', html)
    if left:
        raise SystemExit(f'unfilled placeholders: {sorted(set(left))}')
    if args.out.exists():
        shutil.rmtree(args.out)
    shutil.copytree(SITE / 'assets', args.out / 'assets')
    (args.out / 'index.html').write_text(html, encoding='utf-8')
    (args.out / '.nojekyll').write_text('')
    for key, value in filled.items():
        print(f'{key} = {value}')


if __name__ == '__main__':
    main()
