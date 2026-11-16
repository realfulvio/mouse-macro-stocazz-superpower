#!/usr/bin/env python3
"""Prova 'finestre elevate' (UIPI) su runner Windows.
Una finestra obiettivo a integrita' ALTA (come un programma avviato come amministratore) conta gli eventi che le ARRIVANO davvero.
Chi inietta gira a integrita' alta (controllo) oppure MEDIA (token duplicato con livello 0x2000, come un utente normale):
  A) iniettore di riferimento (SendInput + QPC), alto -> alto        (controllo: deve arrivare tutto)
  B) iniettore di riferimento, medio -> alto                         (UIPI: ci si aspetta che non arrivi nulla)
  C) Mouse Macro (dal sorgente) che riproduce reference.mmr, alto -> alto   (controllo)
  D) Mouse Macro, medio -> alto                                      (cosa dice il pannello quando l'input non arriva?)
  python bench/ci/uipi_test.py --out results/uipi
Se il runner non e' davvero ad integrita' alta il test lo dichiara e non conclude nulla."""
import argparse, csv, ctypes, json, subprocess, sys, time
from ctypes import wintypes as W
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PY = sys.executable
adv, k = ctypes.windll.advapi32, ctypes.windll.kernel32
for fn, res in ((k.GetCurrentProcess, ctypes.c_void_p), (k.CloseHandle, W.BOOL), (k.WaitForSingleObject, W.DWORD)):
    fn.restype = res
k.CloseHandle.argtypes = [ctypes.c_void_p]; k.WaitForSingleObject.argtypes = [ctypes.c_void_p, W.DWORD]
k.GetExitCodeProcess.argtypes = [ctypes.c_void_p, ctypes.POINTER(W.DWORD)]
adv.OpenProcessToken.argtypes = [ctypes.c_void_p, W.DWORD, ctypes.POINTER(ctypes.c_void_p)]
adv.CreateRestrictedToken.argtypes = [ctypes.c_void_p, W.DWORD, W.DWORD, ctypes.c_void_p, W.DWORD, ctypes.c_void_p, W.DWORD, ctypes.c_void_p, ctypes.POINTER(ctypes.c_void_p)]
adv.SetTokenInformation.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_void_p, W.DWORD]
adv.ConvertStringSidToSidW.argtypes = [W.LPCWSTR, ctypes.POINTER(ctypes.c_void_p)]
adv.GetLengthSid.argtypes = [ctypes.c_void_p]


class SIDAT(ctypes.Structure): _fields_ = [("Sid", ctypes.c_void_p), ("Attributes", W.DWORD)]
class STARTUPINFO(ctypes.Structure):
    _fields_ = [(n, t) for n, t in (("cb", W.DWORD), ("r", W.LPWSTR), ("desktop", W.LPWSTR), ("title", W.LPWSTR), ("x", W.DWORD), ("y", W.DWORD), ("xs", W.DWORD), ("ys", W.DWORD),
                ("xc", W.DWORD), ("yc", W.DWORD), ("fill", W.DWORD), ("flags", W.DWORD), ("show", W.WORD), ("r2", W.WORD), ("r3", ctypes.c_void_p),
                ("si", ctypes.c_void_p), ("so", ctypes.c_void_p), ("se", ctypes.c_void_p))]
class PROCINFO(ctypes.Structure): _fields_ = [("hProcess", ctypes.c_void_p), ("hThread", ctypes.c_void_p), ("pid", W.DWORD), ("tid", W.DWORD)]
adv.CreateProcessAsUserW.argtypes = [ctypes.c_void_p, W.LPCWSTR, W.LPWSTR, ctypes.c_void_p, ctypes.c_void_p, W.BOOL, W.DWORD, ctypes.c_void_p, W.LPCWSTR, ctypes.POINTER(STARTUPINFO), ctypes.POINTER(PROCINFO)]


def integrity_of_this_process():
    out = subprocess.run(["whoami", "/groups"], capture_output=True, text=True).stdout
    return next((l.split()[0:4] for l in out.splitlines() if "Mandatory Label" in l), None), out


def run_medium(cmd, timeout):
    """Avvia 'cmd' (stringa) con una copia del token corrente abbassata a integrita' MEDIA (S-1-16-8192). Ritorna il codice di uscita."""
    tok = ctypes.c_void_p(); ok = adv.OpenProcessToken(k.GetCurrentProcess(), 0x0002 | 0x0008 | 0x0001 | 0x0080, ctypes.byref(tok))   # DUPLICATE|QUERY|ASSIGN_PRIMARY|ADJUST_DEFAULT
    if not ok: raise ctypes.WinError()
    new = ctypes.c_void_p()
    if not adv.CreateRestrictedToken(tok, 0x1, 0, None, 0, None, 0, None, ctypes.byref(new)): raise ctypes.WinError()
    sid = ctypes.c_void_p()
    if not adv.ConvertStringSidToSidW("S-1-16-8192", ctypes.byref(sid)): raise ctypes.WinError()
    lab = SIDAT(sid, 0x20)   # SE_GROUP_INTEGRITY
    if not adv.SetTokenInformation(new, 25, ctypes.byref(lab), ctypes.sizeof(SIDAT) + adv.GetLengthSid(sid)): raise ctypes.WinError()   # TokenIntegrityLevel
    si = STARTUPINFO(); si.cb = ctypes.sizeof(si); si.desktop = "winsta0\\default"; pi = PROCINFO()
    if not adv.CreateProcessAsUserW(new, None, ctypes.create_unicode_buffer(cmd), None, None, False, 0, None, str(ROOT), ctypes.byref(si), ctypes.byref(pi)): raise ctypes.WinError()
    k.WaitForSingleObject(pi.hProcess, int(timeout * 1000))
    code = W.DWORD(); k.GetExitCodeProcess(pi.hProcess, ctypes.byref(code))
    for h in (pi.hProcess, pi.hThread, new, tok): k.CloseHandle(h)
    return code.value   # 259 = ancora in esecuzione allo scadere del tempo


def counts(path):
    c = {"ldown": 0, "lup": 0, "wheel": 0}
    try:
        for r in csv.DictReader(open(path, encoding="utf-8")):
            if r["event"] in c: c[r["event"]] += 1
    except FileNotFoundError: pass
    return c


def case(name, out, launcher, expected_note=""):
    target_csv = out / f"{name}_target.csv"
    t = subprocess.Popen([PY, str(ROOT / "bench" / "tools" / "target_window.py"), "--out", str(target_csv), "--duration", "55"])
    time.sleep(5)    # avvio della finestra (alta)
    t0 = time.time(); info = launcher(); dt = time.time() - t0
    t.wait(timeout=90)
    r = {"caso": name, "arrivati": counts(target_csv), "durata_s": round(dt, 1)}; r.update(info or {})
    print("CASO", json.dumps(r, ensure_ascii=False), flush=True)
    return r


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--out", default="results/uipi"); a = ap.parse_args()
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    il, raw = integrity_of_this_process()
    spec = json.load(open(ROOT / "bench" / "macros" / "reference.spec.json"))
    exp = {"ldown": 0, "lup": 0, "wheel": 0}
    for e in spec["events"]: exp[e["kind"]] += 1
    print("INTEGRITA' di questo processo:", il, flush=True)
    res = {"integrita_orchestratore": il, "attesi": exp, "casi": []}
    inj = f'"{PY}" "{ROOT / "bench" / "ci" / "injector.py"}" "{ROOT / "bench" / "macros" / "reference.spec.json"}"'
    mm = f'"{PY}" "{ROOT / "bench" / "ci" / "profile_idle.py"}" --mode uipi --warm 4'
    def high(cmd_args): return lambda: {"uscita": subprocess.run(cmd_args, capture_output=True, text=True, timeout=120).returncode}
    def mmss(runner):
        def go():
            if runner == "alto":
                p = subprocess.run([PY, str(ROOT / "bench" / "ci" / "profile_idle.py"), "--mode", "uipi", "--warm", "4"], capture_output=True, text=True, timeout=150)
                txt, code = p.stdout + p.stderr, p.returncode
            else:
                f = out / f"mmss_{runner}.txt"
                code = run_medium(f'cmd /c "{mm} > "{f}" 2>&1"', 150); txt = f.read_text(encoding="utf-8", errors="replace") if f.exists() else ""
            line = next((l for l in txt.splitlines() if l.startswith("RISULTATO")), "")
            return {"uscita": code, "pannello": json.loads(line[len("RISULTATO"):]) if line else {"errore": txt[-600:]}}
        return go
    res["casi"].append(case("A_iniettore_alto_verso_alto", out, high([PY, str(ROOT / "bench" / "ci" / "injector.py"), str(ROOT / "bench" / "macros" / "reference.spec.json")])))
    res["casi"].append(case("B_iniettore_medio_verso_alto", out, lambda: {"uscita": run_medium(f"{inj}", 120)}))
    res["casi"].append(case("C_mmss_alto_verso_alto", out, mmss("alto")))
    res["casi"].append(case("D_mmss_medio_verso_alto", out, mmss("medio")))
    (out / "uipi.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    print("UIPI", json.dumps(res, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
