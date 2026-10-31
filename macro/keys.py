"""Tastiera nelle macro: nomi dei tasti e flag di SendInput, senza dipendere da Windows.

I tasti sono salvati come codici virtuali ("vk:65" = A). Così la macro non dipende dal
layout della tastiera con cui è stata registrata e Ctrl, Maiusc, frecce e F1..F24 si
riproducono come tasti veri. Questo modulo è puro: i test girano anche su Linux.
"""
from __future__ import annotations

VK_F9, VK_F10, VK_F11 = 0x78, 0x79, 0x7A
# Tasti usati dal programma stesso (registra, riproduci, emergenza): non finiscono mai nella macro.
RESERVED_VKS = frozenset({VK_F9, VK_F10, VK_F11})

KEYEVENTF_EXTENDEDKEY = 0x0001
KEYEVENTF_KEYUP = 0x0002

# Tasti "estesi": senza il flag, Windows li scambia con i corrispondenti del tastierino numerico.
EXTENDED_VKS = frozenset({
    0x21, 0x22, 0x23, 0x24,        # PgUp, PgDn, End, Home
    0x25, 0x26, 0x27, 0x28,        # frecce
    0x2C, 0x2D, 0x2E,              # Stamp, Ins, Canc
    0x5B, 0x5C, 0x5D,              # Win sinistro/destro, menu contestuale
    0x6F,                          # / del tastierino
    0x90,                          # Bloc Num
    0xA3, 0xA5,                    # Ctrl destro, Alt Gr / Alt destro
})


def key_name(vk: int) -> str:
    return f"vk:{int(vk)}"


def vk_of_name(name: str) -> int:
    if not isinstance(name, str) or not name.startswith("vk:") or not name[3:].isdigit():
        raise ValueError("Tasto della macro non valido.")
    vk = int(name[3:])
    if not 1 <= vk <= 254:
        raise ValueError("Tasto della macro non valido.")
    return vk


def vk_of_pynput_key(key) -> int | None:
    """Codice virtuale di un tasto pynput (KeyCode o Key), oppure None se sconosciuto."""
    vk = getattr(key, "vk", None)
    if vk is None:
        vk = getattr(getattr(key, "value", None), "vk", None)
    if isinstance(vk, int) and not isinstance(vk, bool) and 1 <= vk <= 254:
        return vk
    return None


def key_flags(vk: int, up: bool) -> int:
    flags = KEYEVENTF_EXTENDEDKEY if vk in EXTENDED_VKS else 0
    return flags | (KEYEVENTF_KEYUP if up else 0)
