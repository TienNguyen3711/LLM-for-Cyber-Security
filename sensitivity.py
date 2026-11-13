"""Sensitivity of the oracle-scored RQ1-RQ3 conclusions to the field weights.

    python sensitivity.py --draws 100 --seeds 7 11 13 17 19 23 29 31 37 41

The field weights are policy parameters, not measured constants. This script re-runs the oracle-scored
measurements of multiseed.py with
  * named weight sets: the baseline (synth.FIELD_WEIGHTS), weights anchored to the Australian 100-point
    identification check (Financial Transaction Reports Regulations 1990, regs 3(2) and 4; see AU100 below),
    and equal weights;
  * `--draws` local perturbations: each baseline weight times U(0.5, 1.5), renormalised to sum 1;
  * `--draws` global draws: Dirichlet(1, ..., 1) weights (any ranking of the fields), sum 1.
For every weight set it checks the claims H1-H7 on the mean over the seeds. The claims and their margins
are fixed here, before the perturbed runs, from the conclusions already reported for the baseline.

The benches are reused unchanged. Only the P1 probes depend on the weights (they ask for one
organisation's fields in ascending baseline weight), so under other weights the probe order is no longer
strictly ascending; RQ3 numbers for those weights measure the same probes under a different ledger.
"""
import argparse
import json
import random
import statistics
from pathlib import Path

import evaluate
import synth
from evaluate import metrics, simulate
from leakage import CONFIGS, evaluate_config, probe_cases
from score_events import oracle_score

BASE = dict(synth.FIELD_WEIGHTS)
assert evaluate.FIELD_WEIGHTS is synth.FIELD_WEIGHTS  # weights are swapped in place below

# Australian 100-point check, Financial Transaction Reports Regulations 1990 (compilation 1 Oct 2005).
# Reg 3(2): a person "is taken to be identified if [they] rate at least 100 points". Weight = points / 100,
# so a coverage of 1.0 is the 100 points that identify a person.
AU100 = {
    "name": 0.10,             # no check scores the name alone (every check verifies the name with something
                              # else): kept at the baseline policy value
    "dob": 0.25,              # reg 4(1)(c): name and date of birth, 25 points
    "address": 0.25,          # reg 4(1)(b): name and address, 25 points
    "phone": 0.25,            # reg 4(1)(d): name, address and telephone number, 25 points
    "medicare_number": 0.25,  # reg 4(1)(g): any other secondary identification document, 25 points
                              # (the Medicare card is not named in the regulation; commonly listed at 25)
    "account_number": 0.10,   # no check scores an account number (4(1)(h) scores known-customer status,
                              # which an account number alone does not give): baseline policy value
}
NAMED = {"baseline (T=0.75)": (BASE, 0.75),
         "AU 100-point, T=0.75 (75 points)": (AU100, 0.75),
         "AU 100-point, T=1.00 (100 points = identified)": (AU100, 1.00),
         "equal weights, T=0.75": ({k: 1 / len(BASE) for k in BASE}, 0.75)}

RQ1 = {"D1": dict(det="D1"), "D_traj": dict(det="D_traj"), "D2": dict(det="D2"), "D3": dict(det="D3", rule="or")}
RQ3 = ["D3 or (visible block)", "D3 or, not sticky", "alert-only: requester sees D2, D3 alerts compliance"]
CROSS = ("S3", "S4", "S5")
OVERLAP = ("overlap-moved", "overlap-kyc")

# Claims (fixed before the perturbed runs). Baseline values over 10 seeds in brackets.
CLAIMS = {
    "H1 D3 prevents >= 20 pp more than D2": lambda m: m["prev_D3"] - m["prev_D2"] >= 0.20,           # [52.4 pp]
    "H2 D3 prevents >= 80% of cross-org campaigns": lambda m: m["cross_D3"] >= 0.80,                  # [97.1%]
    "H3 D_traj benign FP >= 50 pp above D3": lambda m: m["fp_D_traj"] - m["fp_D3"] >= 0.50,           # [86.6 pp]
    "H4 sum blocks >= 50 pp more overlap customers than or": lambda m: m["ovfp_sum"] - m["ovfp_or"] >= 0.50,  # [93 pp]
    "H5 crossing bit leaks >= 0.05 bits (S_other)": lambda m: m["mi_D3"] >= 0.05,                     # [0.238]
    "H6 not sticky leaks less than sticky": lambda m: m["mi_notsticky"] < m["mi_D3"],                  # [0.139 < 0.238]
    "H7 alert-only leaks <= half of D3": lambda m: m["mi_alert"] <= 0.5 * m["mi_D3"],                  # [0.016]
}


def load(seeds):
    out = []
    for seed in seeds:
        p = Path(synth.default_out(seed, 20, 120))
        if not p.exists():
            raise SystemExit(f"{p} missing: run multiseed.py first")
        b = json.loads(p.read_text())
        ev = b["events"]
        out.append((ev, b["orgs"], {e["eid"]: oracle_score(e) for e in ev}, probe_cases(ev),
                    [s for s in b["meta"]["strategies"] if s.startswith(CROSS)]))
    return out


def run(benches, weights, T):
    synth.FIELD_WEIGHTS.clear()
    synth.FIELD_WEIGHTS.update(weights)
    per = []
    for ev, orgs, sc, cases, cross in benches:
        r = {}
        for name, cfg in RQ1.items():
            b = simulate(ev, sc, orgs, T=T, **cfg)
            m = metrics(ev, b)
            r[f"prev_{name}"], r[f"fp_{name}"] = m["prevented"], m["benign_person_fp"]
            if name == "D3":
                r["cross_D3"] = statistics.mean(metrics(ev, b, s)["prevented"] for s in cross)
                r["ovfp_or"] = statistics.mean(m["fp_by_kind"].get(k, 0) for k in OVERLAP)
        m = metrics(ev, simulate(ev, sc, orgs, det="D3", rule="sum", T=T))
        r["prev_sum"], r["ovfp_sum"] = m["prevented"], statistics.mean(m["fp_by_kind"].get(k, 0) for k in OVERLAP)
        for key, name in zip(("mi_D3", "mi_notsticky", "mi_alert"), RQ3):
            vis, alert = CONFIGS[name]
            r[key] = evaluate_config(ev, sc, orgs, cases, T, vis, alert, [0])["S_other"]["MI_corrected"]
        per.append(r)
    synth.FIELD_WEIGHTS.clear()
    synth.FIELD_WEIGHTS.update(BASE)
    mean = {k: statistics.mean(r[k] for r in per) for k in per[0]}
    return mean, {c: bool(f(mean)) for c, f in CLAIMS.items()}


def norm(w):
    s = sum(w.values())
    return {k: v / s for k, v in w.items()}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, nargs="+", default=[7, 11, 13, 17, 19, 23, 29, 31, 37, 41])
    ap.add_argument("--draws", type=int, default=100)
    ap.add_argument("--rng", type=int, default=0)
    ap.add_argument("--out", default="results")
    a = ap.parse_args()
    benches = load(a.seeds)
    rng = random.Random(a.rng)
    sets = [(n, w, T, "named") for n, (w, T) in NAMED.items()]
    sets += [(f"local {i}", norm({k: v * rng.uniform(0.5, 1.5) for k, v in BASE.items()}), 0.75, "local")
             for i in range(a.draws)]
    sets += [(f"global {i}", norm({k: rng.gammavariate(1, 1) for k in BASE}), 0.75, "global")
             for i in range(a.draws)]
    rows = []
    for i, (name, w, T, fam) in enumerate(sets):
        mean, ok = run(benches, w, T)
        rows.append({"name": name, "family": fam, "T": T, "weights": w, "metrics": mean, "claims": ok})
        if fam == "named" or i % 20 == 0:
            print(f"[{i + 1}/{len(sets)}] {name}: {sum(ok.values())}/{len(ok)} claims hold", flush=True)

    pct = lambda x: f"{100 * x:.1f}"
    md = [f"# Field-weight sensitivity (oracle scorer, {len(a.seeds)} seeds: {', '.join(map(str, a.seeds))})\n",
          "Generated by `sensitivity.py`. Each weight set is run on every seed; claims are checked on the mean over "
          "the seeds. Claims and margins were fixed before the perturbed runs.\n",
          "## Named weight sets\n",
          "| weight set | " + " | ".join(BASE) + " | T | D1 | D2 | D3 | D3 cross-org | D3 FP | D_traj FP | "
          "overlap FP or / sum | MI D3 / not sticky / alert-only | claims held |",
          "|---|" + "---|" * (len(BASE) + 9)]
    for r in rows:
        if r["family"] != "named":
            continue
        m, w = r["metrics"], r["weights"]
        md.append(f"| {r['name']} | " + " | ".join(f"{w[k]:.2f}" for k in BASE) + f" | {r['T']:.2f} | "
                  f"{pct(m['prev_D1'])} | {pct(m['prev_D2'])} | {pct(m['prev_D3'])} | {pct(m['cross_D3'])} | "
                  f"{pct(m['fp_D3'])} | {pct(m['fp_D_traj'])} | {pct(m['ovfp_or'])} / {pct(m['ovfp_sum'])} | "
                  f"{m['mi_D3']:.3f} / {m['mi_notsticky']:.3f} / {m['mi_alert']:.3f} | "
                  f"{sum(r['claims'].values())}/{len(CLAIMS)} |")
    md += ["\nClaims failing for a named set: " + "; ".join(
        f"{r['name']}: " + ", ".join(c.split()[0] for c, v in r["claims"].items() if not v)
        for r in rows if r["family"] == "named" and not all(r["claims"].values())) or "none.", ""]
    for fam, desc in (("local", "baseline x U(0.5, 1.5), renormalised to sum 1, T = 0.75"),
                      ("global", "Dirichlet(1, ..., 1), sum 1, T = 0.75")):
        g = [r for r in rows if r["family"] == fam]
        if not g:
            continue
        md += [f"## {fam.capitalize()} draws ({len(g)}): {desc}\n",
               "| claim | holds in | worst draw |", "|---|---|---|"]
        for c in CLAIMS:
            bad = [r for r in g if not r["claims"][c]]
            md.append(f"| {c} | {pct(1 - len(bad) / len(g))}% | {bad[0]['name'] if bad else '-'} |")
        md += ["", "| metric | 5th pct | median | 95th pct |", "|---|---|---|---|"]
        for k in ("prev_D2", "prev_D3", "cross_D3", "fp_D3", "fp_D_traj", "ovfp_or", "ovfp_sum",
                  "mi_D3", "mi_notsticky", "mi_alert"):
            xs = sorted(r["metrics"][k] for r in g)
            q = lambda p: xs[int(p * (len(xs) - 1))]
            f = (lambda x: f"{x:.3f}") if k.startswith("mi") else pct
            md.append(f"| {k} | {f(q(0.05))} | {f(q(0.5))} | {f(q(0.95))} |")
        md.append("")
    out = Path(a.out)
    out.mkdir(exist_ok=True)
    (out / "sensitivity_weights.md").write_text("\n".join(md) + "\n")
    (out / "sensitivity_weights.json").write_text(json.dumps(rows, indent=1))
    print("\n".join(md))


if __name__ == "__main__":
    main()
