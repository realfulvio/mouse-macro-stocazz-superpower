import csv, json, random, sys, tempfile, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import analyze, reference_macro

THR = json.loads((Path(__file__).resolve().parents[1] / "thresholds.json").read_text())


def fake_run(path, spec, jitter_ms=0.0, pos=0.0, drop=None, extra=False, seed=1):
    r = random.Random(seed); rows = []
    for i, e in enumerate(spec["events"]):
        if i == drop: continue
        rows.append([f"{1000 + e['t']*1000 + r.uniform(-jitter_ms, jitter_ms):.3f}", e["kind"],
                     e["x"] + (round(r.uniform(-pos, pos))), e["y"], e.get("data", 0), 1])
    if extra: rows.append(["99999", "ldown", 1, 1, 0, 1])
    with open(path, "w", newline="") as f:
        w = csv.writer(f); w.writerow(["t_ms", "event", "x", "y", "data", "injected"]); w.writerows(rows)


class T(unittest.TestCase):
    def setUp(self):
        self.d = Path(tempfile.mkdtemp()); self.spec = {"events": reference_macro.build(1920, 1080)}

    def runs(self, n=30, **kw):
        ps = []
        for i in range(n):
            p = self.d / f"r{i}.csv"; fake_run(p, self.spec, seed=i, **kw); ps.append(p)
        return ps

    def test_perfect_passes(self):
        self.assertEqual(analyze.evaluate(self.spec, self.runs(), THR)["verdict"], "PASSA")

    def test_small_jitter_passes(self):
        self.assertEqual(analyze.evaluate(self.spec, self.runs(jitter_ms=2), THR)["verdict"], "PASSA")

    def test_big_jitter_fails(self):
        r = analyze.evaluate(self.spec, self.runs(jitter_ms=40), THR)
        self.assertEqual(r["verdict"], "NON PASSA"); self.assertFalse(r["checks"]["interval_p95"])

    def test_position_error_fails(self):
        self.assertFalse(analyze.evaluate(self.spec, self.runs(pos=8), THR)["checks"]["pos_p95"])

    def test_missing_and_extra(self):
        self.assertFalse(analyze.evaluate(self.spec, self.runs(drop=3), THR)["checks"]["missing"])
        self.assertFalse(analyze.evaluate(self.spec, self.runs(extra=True), THR)["checks"]["extra"])

    def test_too_few_runs(self):
        self.assertFalse(analyze.evaluate(self.spec, self.runs(n=5), THR)["checks"]["repetitions>=min"])

    def test_percentile(self):
        self.assertAlmostEqual(analyze.pctl(list(range(101)), 95), 95)

    def test_mmr_loads(self):
        sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
        from macro.events import Macro
        p = self.d / "r.mmr"; p.write_text(json.dumps(reference_macro.to_mmr(self.spec["events"], 1920, 1080, 0, 0)))
        self.assertEqual(Macro.load(str(p)).screen, [0, 0, 1920, 1080])


if __name__ == "__main__":
    unittest.main()


class TestEndurance(unittest.TestCase):
    def test_cycles_and_slope(self):
        import analyze_endurance as ae
        d = Path(tempfile.mkdtemp()); lg, rs = d / "l.csv", d / "r.csv"
        with open(lg, "w", newline="") as f:
            w = csv.writer(f); w.writerow(["t_ms", "event", "x", "y", "data", "injected"])
            for c in range(100):
                for k, off in enumerate((0, 1, 2)): w.writerow([f"{(c*17.3+off)*1000:.1f}", "ldown", 0, 0, 0, 1])
        with open(rs, "w", newline="") as f:
            w = csv.writer(f); w.writerow(["t_s", "private_mb"])
            for t in range(0, 7200, 60): w.writerow([t, 50 + t / 3600 * 0.5])
        r = ae.evaluate(lg, rs, 17.3, THR, 4.0)
        self.assertEqual(r["cycles"], 100); self.assertAlmostEqual(r["private_mb_per_hour"], 0.5, places=2)
        self.assertEqual(r["verdict"], "PASSA")


class TestUsability(unittest.TestCase):
    def test_sus(self):
        import usability_analyze as ua
        best = {f"sus{i}": (5 if i % 2 else 1) for i in range(1, 11)}
        worst = {f"sus{i}": (1 if i % 2 else 5) for i in range(1, 11)}
        self.assertEqual(ua.sus(best), 100.0); self.assertEqual(ua.sus(worst), 0.0)

    def test_insufficient(self):
        import usability_analyze as ua
        row = {"tool": "x", "success": "1", "time_s": "50", "errors": "0", **{f"sus{i}": (5 if i % 2 else 1) for i in range(1, 11)}}
        self.assertEqual(ua.evaluate([row] * 3, THR)["x"]["verdict"], "INSUFFICIENTE")
        self.assertEqual(ua.evaluate([row] * 5, THR)["x"]["verdict"], "PASSA")
