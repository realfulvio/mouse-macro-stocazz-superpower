#!/usr/bin/env bash
# Grant only active local-seat users access; do not run the app as root.
set -euo pipefail
if [[ ${EUID} != 0 ]]; then
    exec sudo bash "$0"
fi
target=/etc/udev/rules.d/70-mouse-macro.rules
if [[ -e "$target" ]]; then
    echo "Rule already exists: $target. Review it before replacing it." >&2
    exit 1
fi
cat > "$target" <<'RULES'
# Mouse Macro: mouse recording and global shortcut devices, active seat only.
SUBSYSTEM=="input", KERNEL=="event*", ENV{ID_INPUT_MOUSE}=="1", TAG+="uaccess"
SUBSYSTEM=="input", KERNEL=="event*", ENV{ID_INPUT_KEYBOARD}=="1", TAG+="uaccess"
SUBSYSTEM=="misc", KERNEL=="uinput", TAG+="uaccess"
RULES
udevadm control --reload-rules
udevadm trigger --subsystem-match=input --action=change
udevadm trigger --subsystem-match=misc --action=change
echo 'Rules installed. Log out and back in, then refresh the app device list.'
