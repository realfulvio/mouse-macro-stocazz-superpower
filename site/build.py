"""Build the GitHub Pages site into _site/ with the current release links.

`index.html` is the single source of the page: every text exists twice, tagged
lang="it" / lang="en". The build turns it into two real static pages, Italian
at `/` and English at `/en/`, each one with its own title, description, canonical,
hreflang, Open Graph and JSON-LD, so search engines index one language per URL.
It also writes sitemap.xml, robots.txt and 404.html.

Versions and download URLs come from the GitHub releases API at build time, so
the page needs no JavaScript or network request to stay current. Without network
(local preview) the fallback values below are used.

Files dropped in `site/root/` are copied verbatim to the site root (for example
the Google Search Console verification file).

Usage: python site/build.py [--out _site] [--offline]
       python site/build.py --check _site
"""
import argparse
import html
import json
import os
import re
import shutil
import sys
import urllib.request
from html.parser import HTMLParser
from pathlib import Path

REPO = 'realfulvio/mouse-macro-stocazz-superpower'
BASE = f'https://github.com/{REPO}/releases'
SITE_URL = 'https://realfulvio.github.io/mouse-macro-stocazz-superpower/'
FALLBACK = {'windows': 'v1.2.5', 'linux': 'linux-v1.2.0'}
SITE = Path(__file__).resolve().parent
LANGS = ('it', 'en')
VOID = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link', 'meta', 'source', 'track', 'wbr'}

NAME = 'Mouse Macro Stocazz Superpower'
LICENSE_URL = 'https://polyformproject.org/licenses/noncommercial/1.0.0'

PAGES = {
    'it': {
        'path': '',
        'out': 'index.html',
        'title': f'{NAME} – Registra e ripeti il mouse',
        'desc': "Registratore di macro per il mouse su Windows e Linux: premi F9, fai i clic, premi F10 e ripetili da 1 a 999 volte o all'infinito. Gratis per uso personale.",
        'og_title': f'{NAME} – Registra il mouse. Ripeti quanto vuoi.',
        'og_desc': 'Registratore di macro per il mouse, per Windows e Linux. Un pannello piccolo e sempre in primo piano. Gratis per uso personale.',
        'og_image_alt': 'Mouse Macro Stocazz Superpower: registra il mouse, ripeti quanto vuoi. Windows e Linux.',
        'og_locale': 'it_IT',
        'og_locale_alt': 'en_US',
        'web_desc': 'Sito ufficiale di Mouse Macro Stocazz Superpower, il registratore di macro per il mouse per Windows e Linux.',
        'app_desc': "Registratore di macro per il mouse per Windows e Linux. Registra movimenti, clic, doppi clic, trascinamenti e rotella e li ripete da 1 a 999 volte o all'infinito, da un piccolo pannello sempre in primo piano.",
        'offer_desc': 'Gratis per uso personale (PolyForm Noncommercial 1.0.0).',
        'features': [
            'Registra movimenti, clic, doppi clic, trascinamenti e rotella',
            'Ripetizione da 1 a 999 volte o infinita, a velocità Normale o Rapida 2×',
            'Movimento umano facoltativo',
            'Ctrl+Tab tra un giro e l’altro',
            'Macro salvabili come .mmr, .cmd (Windows) o .sh (Linux)',
            'Aggiornamenti verificati con SHA-256',
        ],
        'faq_title': 'Domande frequenti su Mouse Macro Stocazz Superpower',
    },
    'en': {
        'path': 'en/',
        'out': 'en/index.html',
        'title': f'{NAME} – Record & Replay Mouse Clicks',
        'desc': 'Mouse macro recorder for Windows and Linux: press F9, do your clicks, press F10 and replay them 1 to 999 times or forever. Free for personal use.',
        'og_title': f'{NAME} – Record your mouse. Replay it all day.',
        'og_desc': 'Mouse macro recorder for Windows and Linux. A small always-on-top panel. Free for personal use.',
        'og_image_alt': 'Mouse Macro Stocazz Superpower: record your mouse, replay it as much as you like. Windows and Linux.',
        'og_locale': 'en_US',
        'og_locale_alt': 'it_IT',
        'web_desc': 'Official website of Mouse Macro Stocazz Superpower, the mouse macro recorder for Windows and Linux.',
        'app_desc': 'Mouse macro recorder for Windows and Linux. It records moves, clicks, double clicks, drags and wheel and replays them 1 to 999 times or forever, from a small always-on-top panel.',
        'offer_desc': 'Free for personal use (PolyForm Noncommercial 1.0.0).',
        'features': [
            'Records moves, clicks, double clicks, drags and wheel',
            'Replays 1 to 999 times or forever, at Normal or Fast 2× speed',
            'Optional human-like movement',
            'Ctrl+Tab between loops',
            'Macros saved as .mmr, .cmd (Windows) or .sh (Linux)',
            'Updates verified with SHA-256',
        ],
        'faq_title': 'Frequently asked questions about Mouse Macro Stocazz Superpower',
    },
}

# (domanda, risposta) per lingua. Le risposte possono avere <kbd>/<code>; nel JSON-LD diventano testo.
FAQ = {
    'it': [
        ('Cos’è Mouse Macro Stocazz Superpower?',
         'È un registratore di macro per il mouse, per Windows e Linux. Registra movimenti, clic, doppi clic, trascinamenti e rotella e li ripete quante volte vuoi, da un piccolo pannello sempre in primo piano.'),
        ('È gratis?',
         'Sì, è gratuito per uso personale. La licenza è PolyForm Noncommercial 1.0.0: l’uso commerciale non è incluso.'),
        ('Su quali sistemi funziona?',
         'Su Windows 10 e 11 a 64 bit e su Linux x86_64, con X11 o Wayland. Python è incluso: non devi installare altro.'),
        ('Come registro e ripeto una sequenza di clic?',
         'Premi <kbd>F9</kbd>, esegui i tuoi clic e premi di nuovo <kbd>F9</kbd> per fermare la registrazione. Poi scegli quante volte ripetere e premi <kbd>F10</kbd> per avviare la riproduzione.'),
        ('Quante volte può ripetere una macro?',
         'Da 1 a 999 volte oppure all’infinito, a velocità Normale o Rapida 2×.'),
        ('Come fermo la riproduzione?',
         'Premi <kbd>F10</kbd>, oppure <kbd>Ctrl</kbd>+<kbd>Alt</kbd>+<kbd>F11</kbd> per l’arresto d’emergenza.'),
        ('Posso salvare una macro e lanciarla con un doppio clic?',
         'Sì: salvala come <code>.mmr</code> oppure come <code>.cmd</code> (Windows) o <code>.sh</code> (Linux) da aprire con un doppio clic.'),
        ('Registra anche la tastiera?',
         'Solo se la accendi tu: è spenta a ogni avvio. Se la attivi, i tasti finiscono nel file in chiaro, password comprese.'),
        ('Raccoglie dati o fa screenshot?',
         'Non fa screenshot. L’unico accesso alla rete è il controllo degli aggiornamenti, anonimo e disattivabile.'),
        ('Perché su Linux devo riportare il mouse al punto di partenza?',
         'Su Linux registra spostamenti relativi, perché su Wayland nessun programma può leggere la posizione del cursore: riporta il mouse al punto di partenza prima di ogni replay. Su Windows usa invece coordinate assolute: tieni uguali posizione delle finestre, risoluzione e scala dello schermo.'),
    ],
    'en': [
        ('What is Mouse Macro Stocazz Superpower?',
         'It is a mouse macro recorder for Windows and Linux. It records moves, clicks, double clicks, drags and wheel and replays them as many times as you like, from a small always-on-top panel.'),
        ('Is it free?',
         'Yes, it is free for personal use. The license is PolyForm Noncommercial 1.0.0: commercial use is not included.'),
        ('Which systems does it run on?',
         'Windows 10 and 11 (64-bit) and Linux x86_64, on X11 or Wayland. Python is bundled: there is nothing else to install.'),
        ('How do I record and replay a sequence of clicks?',
         'Press <kbd>F9</kbd>, do your clicks and press <kbd>F9</kbd> again to stop recording. Then pick how many times to repeat and press <kbd>F10</kbd> to start the replay.'),
        ('How many times can a macro repeat?',
         '1 to 999 times or forever, at Normal or Fast 2× speed.'),
        ('How do I stop a replay?',
         'Press <kbd>F10</kbd>, or <kbd>Ctrl</kbd>+<kbd>Alt</kbd>+<kbd>F11</kbd> for the emergency stop.'),
        ('Can I save a macro and launch it with a double click?',
         'Yes: save it as <code>.mmr</code>, or as a <code>.cmd</code> (Windows) or <code>.sh</code> (Linux) file you open with a double click.'),
        ('Does it record the keyboard too?',
         'Only if you turn it on: it is off at every start. When on, keys are saved in plain text, passwords included.'),
        ('Does it collect data or take screenshots?',
         'It takes no screenshots. The only network access is the update check, anonymous and switchable off.'),
        ('Why do I have to bring the pointer back to the start on Linux?',
         'On Linux it records relative moves, because on Wayland no app can read the cursor position: bring the pointer back to the start before each replay. On Windows it uses absolute coordinates instead: keep window positions, resolution and display scaling the same.'),
    ],
}


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


def last_release_date(releases):
    """Data (AAAA-MM-GG) dell'ultima release pubblicata: serve a <lastmod>, che deve essere vera."""
    dates = [r['published_at'][:10] for r in releases if not r['draft'] and not r['prerelease'] and r.get('published_at')]
    return max(dates, default=None)


class LangFilter(HTMLParser):
    """Keeps the elements of one language and drops the other, leaving the rest untouched."""

    def __init__(self, keep):
        super().__init__(convert_charrefs=False)
        self.keep, self.out = keep, []
        self.skip_tag, self.skip_depth = None, 0

    def _lang(self, attrs):
        value = dict(attrs).get('lang')
        return value if value in LANGS else None

    def handle_starttag(self, tag, attrs, closed=False):
        if self.skip_tag:
            if tag == self.skip_tag and tag not in VOID and not closed:
                self.skip_depth += 1
            return
        raw = self.get_starttag_text()
        lang = self._lang(attrs) if tag != 'html' else None
        if lang and lang != self.keep:
            if tag not in VOID and not closed:
                self.skip_tag, self.skip_depth = tag, 1
            return
        if lang:
            raw = re.sub(r'\slang="%s"' % lang, '', raw, count=1)
        self.out.append(raw)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs, closed=True)

    def handle_endtag(self, tag):
        if self.skip_tag:
            if tag == self.skip_tag:
                self.skip_depth -= 1
                if not self.skip_depth:
                    self.skip_tag = None
            return
        self.out.append(f'</{tag}>')

    def _emit(self, text):
        if not self.skip_tag:
            self.out.append(text)

    def handle_data(self, data):
        self._emit(data)

    def handle_entityref(self, name):
        self._emit(f'&{name};')

    def handle_charref(self, name):
        self._emit(f'&#{name};')

    def handle_comment(self, data):
        self._emit(f'<!--{data}-->')

    def handle_decl(self, decl):
        self._emit(f'<!{decl}>')


def keep_language(source, lang):
    parser = LangFilter(lang)
    parser.feed(source)
    parser.close()
    return ''.join(parser.out)


def strip_tags(text):
    return html.unescape(re.sub(r'<[^>]+>', '', text))


def faq_html(lang):
    rows = []
    for question, answer in FAQ[lang]:
        rows.append(f'      <details><summary><h3>{html.escape(question, quote=False)}</h3></summary><p>{answer}</p></details>')
    return '\n'.join(rows)


def page_url(lang):
    return SITE_URL + PAGES[lang]['path']


def json_ld(lang, filled):
    page = PAGES[lang]
    url = page_url(lang)
    shots = [f'{SITE_URL}assets/panel-ready-{lang}.webp', f'{SITE_URL}assets/panel-options-{lang}.webp']
    graph = [
        {'@type': 'WebSite', '@id': f'{SITE_URL}#website', 'url': SITE_URL, 'name': NAME,
         'inLanguage': ['it', 'en']},
        {'@type': 'WebPage', '@id': f'{url}#webpage', 'url': url, 'name': page['title'],
         'description': page['web_desc'], 'inLanguage': lang, 'isPartOf': {'@id': f'{SITE_URL}#website'},
         'about': {'@id': f'{SITE_URL}#app'}, 'primaryImageOfPage': {'@type': 'ImageObject', 'url': f'{SITE_URL}assets/og.jpg', 'width': 1200, 'height': 630}},
        {'@type': 'SoftwareApplication', '@id': f'{SITE_URL}#app', 'name': NAME,
         'description': page['app_desc'], 'url': url,
         'applicationCategory': 'UtilitiesApplication',
         'operatingSystem': 'Windows 10, Windows 11, Linux',
         'softwareHelp': {'@type': 'WebPage', 'url': f'https://github.com/{REPO}/blob/main/' + ('GUIDA-ITALIANA.md' if lang == 'it' else 'README.en.md')},
         'downloadUrl': filled['WIN_ZIP_URL'],
         'releaseNotes': filled['WIN_URL'],
         'license': LICENSE_URL,
         'isAccessibleForFree': True,
         'offers': {'@type': 'Offer', 'price': '0', 'priceCurrency': 'EUR', 'description': page['offer_desc'],
                    'url': f'{BASE}/latest'},
         'featureList': page['features'],
         'screenshot': shots,
         'image': f'{SITE_URL}assets/og.jpg',
         'inLanguage': ['it', 'en'],
         'sameAs': [f'https://github.com/{REPO}']},
        {'@type': 'FAQPage', '@id': f'{url}#faq', 'name': page['faq_title'], 'inLanguage': lang,
         'mainEntity': [{'@type': 'Question', 'name': q,
                         'acceptedAnswer': {'@type': 'Answer', 'text': strip_tags(a)}} for q, a in FAQ[lang]]},
    ]
    text = json.dumps({'@context': 'https://schema.org', '@graph': graph}, ensure_ascii=False, separators=(',', ':'))
    return text.replace('</', '<\\/')


def render(template, lang, filled):
    page = PAGES[lang]
    esc = lambda value: html.escape(value, quote=True)
    depth = '../' if page['path'] else ''
    mapping = dict(filled)
    mapping.update({
        'LANG': lang, 'TITLE': esc(page['title']), 'DESC': esc(page['desc']),
        'URL': page_url(lang), 'URL_IT': page_url('it'), 'URL_EN': page_url('en'),
        'OG_TITLE': esc(page['og_title']), 'OG_DESC': esc(page['og_desc']),
        'OG_LOCALE': page['og_locale'], 'OG_LOCALE_ALT': page['og_locale_alt'],
        'OG_IMAGE': f'{SITE_URL}assets/og.jpg', 'OG_IMAGE_ALT': esc(page['og_image_alt']),
        'HREF_IT': '../' if lang == 'en' else './', 'HREF_EN': 'en/' if lang == 'it' else './',
        'CUR_IT': ' aria-current="true"' if lang == 'it' else '', 'CUR_EN': ' aria-current="true"' if lang == 'en' else '',
        'JSONLD': json_ld(lang, filled), 'FAQ': faq_html(lang),
    })
    out = template
    for key, value in mapping.items():
        out = out.replace(f'%%{key}%%', value)
    out = keep_language(out, lang)
    if depth:
        out = re.sub(r'(["(])assets/', r'\1' + depth + 'assets/', out)
    left = re.findall(r'%%[A-Z_]+%%', out)
    if left:
        raise SystemExit(f'unfilled placeholders: {sorted(set(left))}')
    return out


def sitemap(lastmod):
    alt = ''.join(f'<xhtml:link rel="alternate" hreflang="{code}" href="{page_url(lang)}"/>'
                  for code, lang in (('it', 'it'), ('en', 'en'), ('x-default', 'en')))
    mod = f'<lastmod>{lastmod}</lastmod>' if lastmod else ''
    urls = ''.join(f'<url><loc>{page_url(lang)}</loc>{mod}{alt}</url>\n' for lang in LANGS)
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">\n'
            f'{urls}</urlset>\n')


def robots():
    return f'User-agent: *\nAllow: /\n\nSitemap: {SITE_URL}sitemap.xml\n'


class Collect(HTMLParser):
    """Gathers what the checks need from a built page."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.tags, self.refs, self.imgs, self.meta, self.links = [], [], [], {}, []
        self.in_title, self.title, self.jsonld, self._in_ld, self.html_lang = False, '', [], False, None
        self.lang_attrs = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        self.tags.append(tag)
        if tag == 'html':
            self.html_lang = a.get('lang')
        elif 'lang' in a:
            self.lang_attrs.append((tag, a['lang']))
        if tag == 'title':
            self.in_title = True
        if tag == 'meta':
            self.meta[a.get('name') or a.get('property')] = a.get('content')
        if tag == 'link':
            self.links.append(a)
        if tag == 'img':
            self.imgs.append(a)
        if tag == 'script' and a.get('type') == 'application/ld+json':
            self._in_ld = True
        for key in ('src', 'href'):
            if key in a:
                self.refs.append(a[key])

    def handle_endtag(self, tag):
        if tag == 'title':
            self.in_title = False
        if tag == 'script':
            self._in_ld = False

    def handle_data(self, data):
        if self.in_title:
            self.title += data
        if self._in_ld:
            self.jsonld.append(data)


def check(out):
    """Fails the build on the SEO and structure mistakes that are easy to reintroduce."""
    errors = []
    sitemap_text = (out / 'sitemap.xml').read_text(encoding='utf-8')
    for name in ('robots.txt', '404.html', '.nojekyll'):
        if not (out / name).is_file():
            errors.append(f'missing {name}')
    summary = []
    for lang in LANGS:
        page = PAGES[lang]
        path = out / page['out']
        text = path.read_text(encoding='utf-8')
        c = Collect()
        c.feed(text)
        tag = f'[{lang}]'
        if c.html_lang != lang:
            errors.append(f'{tag} <html lang> is {c.html_lang!r}')
        if c.lang_attrs:
            errors.append(f'{tag} leftover lang attributes: {sorted(set(c.lang_attrs))[:5]}')
        if not 20 <= len(c.title.strip()) <= 65:
            errors.append(f'{tag} title length {len(c.title.strip())}')
        desc = c.meta.get('description') or ''
        if not 100 <= len(desc) <= 160:
            errors.append(f'{tag} description length {len(desc)}')
        if c.tags.count('h1') != 1:
            errors.append(f'{tag} h1 count {c.tags.count("h1")}')
        canonical = [l['href'] for l in c.links if l.get('rel') == 'canonical']
        if canonical != [page_url(lang)]:
            errors.append(f'{tag} canonical {canonical}')
        hreflangs = {l.get('hreflang'): l['href'] for l in c.links if l.get('rel') == 'alternate'}
        if hreflangs != {'it': page_url('it'), 'en': page_url('en'), 'x-default': page_url('en')}:
            errors.append(f'{tag} hreflang {hreflangs}')
        for key in ('og:title', 'og:description', 'og:url', 'og:image', 'og:image:alt', 'twitter:card', 'twitter:image'):
            if not c.meta.get(key):
                errors.append(f'{tag} missing {key}')
        missing_alt = [i.get('src') for i in c.imgs if 'alt' not in i]
        if missing_alt:
            errors.append(f'{tag} images without alt: {missing_alt}')
        try:
            graph = json.loads(''.join(c.jsonld))['@graph']
            kinds = {item['@type'] for item in graph}
            if kinds != {'WebSite', 'WebPage', 'SoftwareApplication', 'FAQPage'}:
                errors.append(f'{tag} json-ld types {kinds}')
        except (ValueError, KeyError) as error:
            errors.append(f'{tag} json-ld invalid: {error}')
        missing = []
        for ref in set(c.refs):
            if re.match(r'^(https?:|#|mailto:)', ref):
                continue
            target = (path.parent / ref.split('#')[0].split('?')[0]).resolve()
            if not (target.is_file() or target.is_dir()):
                missing.append(ref)
        if missing:
            errors.append(f'{tag} missing local files: {sorted(missing)}')
        if page_url(lang) not in sitemap_text:
            errors.append(f'{tag} not in sitemap')
        summary.append(f'{lang}: title {len(c.title.strip())} chars, description {len(desc)} chars, {len(c.imgs)} images, {len(set(c.refs))} refs')
    if errors:
        print('\n'.join(errors))
        raise SystemExit(f'{len(errors)} site check(s) failed')
    size = sum(p.stat().st_size for p in out.rglob('*') if p.is_file())
    print('site checks ok · ' + ' · '.join(summary) + f' · {size / 1024:.0f} KiB')


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--out', type=Path, default=Path('_site'))
    parser.add_argument('--offline', action='store_true')
    parser.add_argument('--check', type=Path, metavar='DIR', help='only check an already built site')
    args = parser.parse_args()
    if args.check:
        check(args.check)
        return
    releases = []
    if not args.offline:
        try:
            releases = fetch_releases()
        except OSError as error:
            if os.environ.get('CI'):
                raise
            print(f'releases API unavailable ({error}); using fallback versions')
    filled = values(releases)
    template = (SITE / 'index.html').read_text(encoding='utf-8')
    it, en = template.count('lang="it"'), template.count('lang="en"')
    if it != en:
        raise SystemExit(f'IT/EN blocks differ in index.html: {it} vs {en}')
    if args.out.exists():
        shutil.rmtree(args.out)
    shutil.copytree(SITE / 'assets', args.out / 'assets')
    root = SITE / 'root'
    if root.is_dir():
        for item in root.iterdir():
            if item.is_file() and item.name != 'README.md':
                shutil.copy2(item, args.out / item.name)
    for lang in LANGS:
        target = args.out / PAGES[lang]['out']
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(render(template, lang, filled), encoding='utf-8')
    shutil.copy2(SITE / '404.html', args.out / '404.html')
    (args.out / 'sitemap.xml').write_text(sitemap(last_release_date(releases)), encoding='utf-8')
    (args.out / 'robots.txt').write_text(robots(), encoding='utf-8')
    (args.out / '.nojekyll').write_text('')
    for key, value in filled.items():
        print(f'{key} = {value}')
    check(args.out)


if __name__ == '__main__':
    sys.exit(main())
