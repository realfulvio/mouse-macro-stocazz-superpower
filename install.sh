#!/usr/bin/env bash
# Mouse Macro Stocazz Superpower - installazione e avvio su Linux
#   curl -fsSL https://raw.githubusercontent.com/realfulvio/mouse-macro-stocazz-superpower/main/install.sh | bash
# Cerca l'ultima release Linux (tag linux-v*) su GitHub, scarica il pacchetto,
# verifica lo SHA-256 con il file SHA256SUMS della stessa release, lo estrae in
# ~/.local/share/MouseMacroStocazzSuperpower e avvia il programma.
# Se e' gia' installata una versione uguale o piu' recente (anche aggiornata
# dall'app) avvia quella senza scaricare nulla. Non usa sudo e non crea servizi
# o avvii automatici: aggiunge solo un'icona nel menu delle applicazioni.
#
# Opzioni: --en (interfaccia inglese)  --permessi (configura l'accesso al mouse,
#          chiede la password di sudo)  --no-start (installa senza avviare)
set -euo pipefail

REPO='realfulvio/mouse-macro-stocazz-superpower'
API="${MMSS_API_URL:-https://api.github.com/repos/$REPO/releases?per_page=50}"
DOWNLOAD="${MMSS_DOWNLOAD_BASE:-https://github.com/$REPO/releases/download}"
DATA="${XDG_DATA_HOME:-$HOME/.local/share}"
ROOT="$DATA/MouseMacroStocazzSuperpower"
PREFIX='MouseMacroStocazzSuperpower-Linux-v'
LANGUAGE=IT
PERMISSIONS=0
START=1
for arg in "$@"; do
    case "$arg" in
        --en) LANGUAGE=EN ;;
        --permessi|--permissions) PERMISSIONS=1 ;;
        --no-start) START=0 ;;
        *) echo "Opzione sconosciuta: $arg" >&2; exit 2 ;;
    esac
done

say() { printf '%s\n' "$*"; }
fail() { printf 'Errore: %s\n' "$*" >&2; exit 1; }
[[ "$(uname -s)" == Linux ]] || fail 'questo script e'"'"' per Linux.'
[[ "$(uname -m)" == x86_64 ]] || fail 'il pacchetto e'"'"' disponibile solo per x86_64.'
command -v sha256sum >/dev/null || fail 'manca sha256sum (coreutils).'
command -v tar >/dev/null || fail 'manca tar.'

fetch() {  # fetch URL FILE
    if command -v curl >/dev/null; then
        curl -fsSL --retry 2 -o "$2" "$1"
    elif command -v wget >/dev/null; then
        wget -q -O "$2" "$1"
    else
        fail 'serve curl o wget.'
    fi
}

newer() {  # newer A B: true if version A > version B
    [[ "$1" != "$2" && "$(printf '%s\n%s\n' "$1" "$2" | sort -V | tail -n1)" == "$1" ]]
}

installed_version() {
    local best='' dir version
    for dir in "$ROOT/$PREFIX"*; do
        [[ -x "$dir/MouseMacroStocazzSuperpower-Linux-IT" && -x "$dir/MouseMacroStocazzSuperpower-Linux-EN" ]] || continue
        version="${dir##*/$PREFIX}"
        if [[ -z "$best" ]] || newer "$version" "$best"; then best="$version"; fi
    done
    printf '%s' "$best"
}

latest_tag() {  # newest published, non-prerelease linux-v* tag from the releases list
    if command -v python3 >/dev/null; then
        python3 -I -c '
import json, re, sys
best = None
for r in json.load(sys.stdin):
    tag = str(r.get("tag_name", ""))
    m = re.fullmatch(r"linux-v(\d+)\.(\d+)\.(\d+)", tag)
    if m and not r.get("draft") and not r.get("prerelease"):
        key = tuple(map(int, m.groups()))
        if best is None or key > best[0]:
            best = (key, tag)
print(best[1] if best else "")' < "$1"
    else
        grep -o '"tag_name": *"linux-v[0-9][0-9.]*"' "$1" | grep -o 'linux-v[0-9.]*' | sort -V | tail -n1
    fi
}

WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT
CURRENT="$(installed_version)"
TAG=''
if fetch "$API" "$WORK/releases.json" 2>/dev/null; then
    TAG="$(latest_tag "$WORK/releases.json")"
fi
if [[ -z "$TAG" ]]; then
    [[ -n "$CURRENT" ]] || fail 'non trovo una release Linux su GitHub (connessione?).'
    say "Controllo online non riuscito: avvio la versione installata $CURRENT."
    VERSION="$CURRENT"
else
    VERSION="${TAG#linux-v}"
fi

if [[ -z "$CURRENT" ]] || newer "$VERSION" "$CURRENT"; then
    PACKAGE="$PREFIX$VERSION"
    ARCHIVE="$PACKAGE.tar.gz"
    SUMS="SHA256SUMS-linux-v$VERSION.txt"
    say "Scarico Mouse Macro Linux $VERSION ..."
    fetch "$DOWNLOAD/$TAG/$SUMS" "$WORK/$SUMS"
    fetch "$DOWNLOAD/$TAG/$ARCHIVE" "$WORK/$ARCHIVE"
    expected="$(awk -v name="$ARCHIVE" '$2 == name || $2 == "*" name { print tolower($1); exit }' "$WORK/$SUMS")"
    [[ -n "$expected" ]] || fail "hash di $ARCHIVE non trovato in $SUMS."
    actual="$(sha256sum "$WORK/$ARCHIVE" | awk '{ print $1 }')"
    [[ "$actual" == "$expected" ]] || fail "SHA-256 diverso dall'atteso ($actual). Download scartato."
    say "SHA-256 verificato: $actual"
    while IFS= read -r entry; do
        [[ "$entry" == "$PACKAGE" || "$entry" == "$PACKAGE/"* ]] || fail "percorso non previsto nel pacchetto: $entry"
        [[ "$entry" != *..* ]] || fail "percorso non sicuro nel pacchetto: $entry"
    done < <(tar -tzf "$WORK/$ARCHIVE")
    mkdir -p "$ROOT"
    STAGE="$(mktemp -d "$ROOT/.install-XXXXXX")"
    tar -xzf "$WORK/$ARCHIVE" -C "$STAGE" --no-same-owner
    [[ -x "$STAGE/$PACKAGE/MouseMacroStocazzSuperpower-Linux-IT" ]] || { rm -rf "$STAGE"; fail 'pacchetto incompleto.'; }
    rm -rf "${ROOT:?}/$PACKAGE"
    mv "$STAGE/$PACKAGE" "$ROOT/$PACKAGE"
    rm -rf "$STAGE"
    CURRENT="$VERSION"
fi

PACKAGE_DIR="$ROOT/$PREFIX$CURRENT"
ln -sfn "$PREFIX$CURRENT" "$ROOT/current"
BINARY="$ROOT/current/MouseMacroStocazzSuperpower-Linux-$LANGUAGE"

# Launcher in the applications menu (no autostart).
APPS="$DATA/applications"
mkdir -p "$APPS"
cat > "$APPS/mouse-macro-stocazz-superpower.desktop" <<DESKTOP
[Desktop Entry]
Type=Application
Name=Mouse Macro Stocazz Superpower
Comment=Registra e riproduce i gesti del mouse
Exec="$BINARY"
Icon=$ROOT/current/icon.png
Terminal=false
Categories=Utility;
DESKTOP

readable=0
for device in /dev/input/event*; do
    [[ -r "$device" ]] && readable=1 && break
done
if [[ "$PERMISSIONS" == 1 ]]; then
    bash "$PACKAGE_DIR/setup-linux-input.sh" || say 'Configurazione dei permessi non completata.'
elif [[ "$readable" == 0 ]]; then
    say 'Attenzione: il programma non puo'"'"' ancora leggere il mouse.'
    say "Configura i permessi una volta sola (chiede la password di sudo):"
    say "  bash \"$PACKAGE_DIR/setup-linux-input.sh\""
    say 'poi esci e rientra nella sessione.'
fi

say "Mouse Macro Linux $CURRENT installato in $PACKAGE_DIR"
if [[ "$START" == 1 ]]; then
    say 'Avvio...'
    setsid -f "$BINARY" >/dev/null 2>&1 < /dev/null || nohup "$BINARY" >/dev/null 2>&1 &
fi
