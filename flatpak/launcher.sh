#!/bin/sh
# Flatpak launcher: Italian interface for Italian locales, English otherwise.
case "${MMSS_LANG:-${LC_ALL:-${LC_MESSAGES:-${LANG:-}}}}" in
    it*|IT*) LANGUAGE=IT ;;
    *) LANGUAGE=EN ;;
esac
exec /app/lib/mmss/MouseMacroStocazzSuperpower-Linux-$LANGUAGE "$@"
