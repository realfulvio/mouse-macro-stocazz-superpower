"""Risorse dei rivali: pacchetti ufficiali, nessuna prova di fedeltà implicita."""
import csv
import ctypes
from ctypes import wintypes as W
import json
import os
from pathlib import Path
import shutil
import subprocess
import time
import zipfile

ROOT = Path(__file__).resolve().parents[2]


def read_csv(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def summarize_resources(rows):
    """A vanished process is missing data, never a zero-CPU result."""
    if len(rows) < 2 or any(int(r["procs"]) < 1 for r in rows):
        raise ValueError("processo assente durante la misura: risorse non valide")
    weighted, duration = 0.0, 0.0
    for before, after in zip(rows, rows[1:]):
        dt = float(after["t_s"]) - float(before["t_s"])
        cpu = float(after["cpu_pct_of_core"])
        if dt <= 0 or cpu < 0:
            raise ValueError("campioni CPU non validi")
        weighted += cpu * dt
        duration += dt
    return {"samples": len(rows) - 1, "observed_seconds": duration,
            "cpu_core_pct_mean": weighted / duration,
            "private_mib_max": max(float(r["private_mb"]) for r in rows)}


def metadata(exe):
    # Environment value avoids shell interpolation of a path into PowerShell.
    env = {**os.environ, "BENCH_EXE_PATH": str(exe)}
    cmd = "$v=(Get-Item -LiteralPath $env:BENCH_EXE_PATH).VersionInfo; @{file_version=$v.FileVersion; product_version=$v.ProductVersion; product=$v.ProductName; company=$v.CompanyName} | ConvertTo-Json -Compress"
    p = subprocess.run(["pwsh", "-NoProfile", "-Command", cmd], env=env, text=True, capture_output=True, check=True)
    return json.loads(p.stdout)


def windows_for(pid):
    u = ctypes.windll.user32
    callback_type = ctypes.WINFUNCTYPE(W.BOOL, W.HWND, W.LPARAM)
    u.EnumWindows.argtypes = [callback_type, W.LPARAM]
    u.GetWindowThreadProcessId.argtypes = [W.HWND, ctypes.POINTER(W.DWORD)]
    u.IsWindowVisible.argtypes = [W.HWND]
    u.GetWindowTextW.argtypes = [W.HWND, W.LPWSTR, ctypes.c_int]
    found = []
    @callback_type
    def visit(hwnd, _):
        owner = W.DWORD()
        u.GetWindowThreadProcessId(hwnd, ctypes.byref(owner))
        if owner.value == pid and u.IsWindowVisible(hwnd):
            buf = ctypes.create_unicode_buffer(1024)
            u.GetWindowTextW(hwnd, buf, len(buf))
            found.append(buf.value)
        return True
    u.EnumWindows(visit, 0)
    return found


def install(cfg, package, dest, out):
    dest.mkdir(parents=True, exist_ok=True)
    method = cfg["install"]
    cmd = None
    if method == "zip":
        with zipfile.ZipFile(package) as z:
            z.extractall(dest)
    elif method == "exe":
        shutil.copy2(package, dest / package.name)
    elif method == "inno":
        cmd = [str(package), "/VERYSILENT", "/SUPPRESSMSGBOXES", "/NORESTART", "/SP-",
               "/DIR=" + str(dest), "/LOG=" + str((out / "install.log").resolve())]
    elif method == "nsis":
        cmd = [str(package), "/S", "/D=" + str(dest)]  # /D must be last
    elif method == "msi":
        cmd = ["msiexec.exe", "/i", str(package), "/qn", "/norestart",
               "INSTALLDIR=" + str(dest), "/L*v", str((out / "install.log").resolve())]
    else:
        raise ValueError("metodo installazione sconosciuto")
    info = {"method": method, "command": cmd}
    (out / "install.json").write_text(json.dumps(info, indent=2), encoding="utf-8")
    if cmd:
        result = subprocess.run(cmd, timeout=180, capture_output=True, text=True, errors="replace")
        info.update(exit_code=result.returncode, stdout=result.stdout, stderr=result.stderr)
        (out / "install.json").write_text(json.dumps(info, indent=2), encoding="utf-8")
        if result.returncode not in (0, 3010):
            raise RuntimeError("installazione fallita, codice " + str(result.returncode))
    exact = dest / cfg["exe"]
    if exact.is_file():
        return exact
    roots = [dest]
    if method == "msi":  # INSTALLDIR may be ignored by the package
        roots += [Path(os.environ[n]) for n in ("ProgramFiles", "ProgramFiles(x86)") if n in os.environ]
        roots += [Path(os.environ["LOCALAPPDATA"]) / "Programs"]
    matches = [p for root in roots if root.exists() for p in root.rglob(cfg["exe"])]
    if len(matches) != 1:
        raise RuntimeError("eseguibile non identificato univocamente: " + repr([str(p) for p in matches]))
    return matches[0]


def run_resources(args, cfg, package, work, out, inv):
    import analyze
    result = {"tool": args.tool, "fidelity": "non misurato", "source": cfg["source"],
              "version_declared": cfg["version_declared"], "inventory": inv,
              "run_id": os.environ.get("GITHUB_RUN_ID"), "commit": os.environ.get("GITHUB_SHA"),
              "status": "in corso"}
    pr = None
    try:
        exe = install(cfg, package, work / "installed", out)
        result.update(exe=str(exe), binary=metadata(exe))
        ps = lambda *c: subprocess.run(["pwsh", "-NoProfile", "-File", *map(str, c)], check=True, timeout=600)
        ps(ROOT / "bench/tools/measure_startup.ps1", "-Exe", exe, "-ProcName", exe.stem,
           "-Runs", args.startups, "-TimeoutS", 15, "-Out", out / "avvio.csv")
        starts = read_csv(out / "avvio.csv")
        warm = [float(r["startup_s"]) for r in starts if r["ok"] == "1" and r["cold"] == "0"]
        result["startup"] = {"successful": sum(r["ok"] == "1" for r in starts), "total": len(starts),
                             "warm_s": analyze.summary(warm),
                             "note": "prima finestra visibile e reattiva, anche se dialogo iniziale; cold=1 indica solo il primo della serie"}
        pr = subprocess.Popen([str(exe)], cwd=exe.parent)
        time.sleep(10)
        result["visible_windows"] = windows_for(pr.pid)
        result["launcher_exit"] = pr.poll()
        ps(ROOT / "bench/tools/measure_resources.ps1", "-Name", exe.stem,
           "-Seconds", args.idle_s, "-Out", out / "risorse_riposo.csv")
        result["idle"] = summarize_resources(read_csv(out / "risorse_riposo.csv"))
        thr = json.loads((ROOT / "bench/thresholds.json").read_text())["resources"]
        result["checks"] = {
            "package": inv["bytes"] / 1e6 <= thr["package_mb_max"],
            "idle_cpu": result["idle"]["cpu_core_pct_mean"] <= thr["idle_cpu_pct_of_core_avg_max"],
            "idle_memory": result["idle"]["private_mib_max"] <= thr["idle_private_mb_max"],
            "startup": (result["startup"]["successful"] == len(starts)
                        and len(warm) == args.startups - 1 and bool(warm)
                        and result["startup"]["warm_s"]["median"] <= thr["startup_s_median_max"]
                        and result["startup"]["warm_s"]["p95"] <= thr["startup_s_p95_max"]),
        }
        result["status"] = "misurato"
    except Exception as error:
        result.update(status="misura incompleta", error=f"{type(error).__name__}: {error}")
        raise
    finally:
        if pr is not None and pr.poll() is None:
            subprocess.run(["taskkill", "/PID", str(pr.pid), "/T", "/F"], capture_output=True)
        (out / "risorse_sommario.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        print("RISORSE_RIVALE", json.dumps(result, ensure_ascii=False), flush=True)
