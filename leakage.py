"""RQ3: what the crossing bit reveals to a probing requester, and what mitigations cost.

A P1 campaign (synth.py --probes) is one account at organisation A asking A's own fields about one
customer, one per day, in ascending weight. The requester sees only allowed/blocked. Under a federated
ledger the first block can come earlier than A's own disclosures explain, which tells the requester
something about the customer's activity at OTHER organisations. We measure that with:

  secret S_other  = coverage of the fields other organisations disclosed about the customer before the
                    probe started (ground truth), in 4 bins: 0, (0, .3], (.3, .5], > .5
  secret S_health = the clinic disclosed something about the customer before the probe (A != clinic):
                    reveals that the person is a patient there and was recently served
  transcript O    = the tuple of allowed/blocked bits the probing account observed

and report the plug-in mutual information I(S; O) in bits, the same estimate with S shuffled (the
small-sample bias; the corrected value is MI minus it), H(S), and the accuracy of the best guess of S
from O against guessing the most common value. Mitigations are evaluated on the same bench together
with the prevention and false-positive cost they carry for the assembly campaigns.

    python leakage.py data/bench_s7x.json --scores oracle qwen/qwen3-32b
"""
import argparse
import json
import math
import random
import statistics
from collections import Counter, defaultdict
from pathlib import Path

from evaluate import FIELDS, coverage, is_probe, metrics, simulate
from score_events import load_scores, out_path

CONFIGS = {  # name -> (visible detector config, alerting detector config or None)
    "D3 or (visible block)": (dict(det="D3", rule="or"), None),
    "D3 max (visible block)": (dict(det="D3", rule="max"), None),
    "D3 sum (visible block)": (dict(det="D3", rule="sum"), None),
    "D3 or, not sticky": (dict(det="D3", rule="or", sticky=False), None),
    "D3 or, threshold noise +/-0.05": (dict(det="D3", rule="or", t_noise=0.05), None),
    "D3 or, threshold noise +/-0.10": (dict(det="D3", rule="or", t_noise=0.10), None),
    "D3 or, threshold noise +/-0.20": (dict(det="D3", rule="or", t_noise=0.20), None),
    "alert-only: requester sees D2, D3 alerts compliance": (dict(det="D2"), dict(det="D3", rule="or")),
}
NOISY = 5  # seeds averaged for randomised configurations


def bins(c):
    return 0 if c == 0 else 1 if c <= 0.3 else 2 if c <= 0.5 else 3


def probe_cases(events):
    by = defaultdict(list)
    for e in events:
        if e["actor"] == "attacker" and is_probe(e["strategy"]):
            by[e["campaign"]].append(e)
    cases = []
    for cid, evs in sorted(by.items()):
        evs.sort(key=lambda e: e["day"])
        a, gid, d0 = evs[0]["org"], evs[0]["person"], evs[0]["day"]
        other = {k: 0.0 for k in FIELDS}
        health = False
        for e in events:  # ground truth: what the customer had disclosed elsewhere before the probe
            if e["person"] == gid and e["org"] != a and e["day"] < d0 and e.get("campaign") != cid:
                for k in e["truth_fields"]:
                    other[k] = 1.0
                health |= e["org"] == "health" and bool(e["truth_fields"])
        cases.append({"campaign": cid, "org": a, "eids": [e["eid"] for e in evs],
                      "S_other": bins(coverage(other)), "S_health": health if a != "health" else None})
    return cases


def mutual_info(pairs):
    n = len(pairs)
    if not n:
        return 0.0
    ps, po, pso = Counter(s for s, _ in pairs), Counter(o for _, o in pairs), Counter(pairs)
    return sum(c / n * math.log2(c * n / (ps[s] * po[o])) for (s, o), c in pso.items())


def entropy(xs):
    n = len(xs)
    return -sum(c / n * math.log2(c / n) for c in Counter(xs).values()) if n else 0.0


def leak_stats(pairs, shuffles=200, seed=0):
    if not pairs:
        return None
    rng = random.Random(seed)
    s, o = [p[0] for p in pairs], [p[1] for p in pairs]
    mi = mutual_info(pairs)
    perm = []
    for _ in range(shuffles):
        rng.shuffle(s)
        perm.append(mutual_info(list(zip(s, o))))
    s = [p[0] for p in pairs]
    best = defaultdict(Counter)
    for si, oi in pairs:
        best[oi][si] += 1
    acc = sum(c.most_common(1)[0][1] for c in best.values()) / len(pairs)
    return {"n": len(pairs), "H_S": entropy(s), "MI": mi, "MI_shuffled": statistics.mean(perm),
            "MI_corrected": max(0.0, mi - statistics.mean(perm)),
            "guess_acc": acc, "prior_acc": Counter(s).most_common(1)[0][1] / len(s)}


def transcript(blocked, case):
    return "".join("B" if blocked[e] else "." for e in case["eids"])


def evaluate_config(events, scores, orgs, cases, T, visible, alert, seeds):
    runs = []
    for seed in seeds:
        vb = simulate(events, scores, orgs, T=T, seed=seed, **visible)
        ab = simulate(events, scores, orgs, T=T, seed=seed, **alert) if alert else vb
        obs = [(c, transcript(vb, c)) for c in cases]
        mv, ma = metrics(events, vb), metrics(events, ab)
        runs.append({"S_other": leak_stats([(c["S_other"], o) for c, o in obs], seed=seed),
                     "S_health": leak_stats([(c["S_health"], o) for c, o in obs if c["S_health"] is not None],
                                            seed=seed),
                     "prevented": mv["prevented"], "alerted": ma["detected"],
                     "benign_person_fp": mv["benign_person_fp"],
                     "transcripts": Counter(o for _, o in obs)})
    avg = lambda f: statistics.mean(f(r) for r in runs)
    out = {k: avg(lambda r: r[k]) for k in ("prevented", "alerted", "benign_person_fp")}
    for sec in ("S_other", "S_health"):
        out[sec] = {k: avg(lambda r: r[sec][k]) for k in runs[0][sec]} if runs[0][sec] else None
    out["transcripts"] = dict(runs[0]["transcripts"].most_common(6))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("bench")
    ap.add_argument("--scores", nargs="+", default=["oracle"])
    ap.add_argument("--T", type=float, default=0.75)
    ap.add_argument("--out", default="results")
    a = ap.parse_args()
    bench = json.loads(Path(a.bench).read_text())
    events, orgs = bench["events"], bench["orgs"]
    cases = probe_cases(events)
    if not cases:
        raise SystemExit("no P1 probe campaigns in this bench: generate it with synth.py --probes N")
    md = [f"# RQ3: leakage of the crossing bit, `{a.bench}`\n",
          f"{len(cases)} P1 probe campaigns ({dict(Counter(c['org'] for c in cases))}), T = {a.T}. "
          f"MI in bits (plug-in; 'corr.' subtracts the mean MI with the secret shuffled, i.e. small-sample "
          f"bias). guess = accuracy of the best guess of the secret from the transcript, prior = guessing "
          f"the most common value. Randomised rows average {NOISY} seeds.\n",
          f"Secret prevalence: S_other bins {dict(sorted(Counter(c['S_other'] for c in cases).items()))}, "
          f"S_health {dict(Counter(c['S_health'] for c in cases if c['S_health'] is not None))}.\n"]
    js = {}
    for sc in a.scores:
        p = out_path(a.bench, sc)
        if not p.exists():
            print(f"skip {sc}: {p} not found")
            continue
        scores = load_scores(p)
        if not all(e["eid"] in scores for e in events):
            print(f"skip {sc}: not every event scored")
            continue
        md.append(f"\n## Scorer `{sc}`\n")
        md.append("| configuration | S_other MI (corr.) | guess / prior | S_health MI (corr.) | guess / prior "
                  "| assembly prevented | alerted | benign person FP |")
        md.append("|---|---|---|---|---|---|---|---|")
        js[sc] = {}
        for name, (vis, alert) in CONFIGS.items():
            seeds = range(NOISY) if vis.get("t_noise") else [0]
            r = evaluate_config(events, scores, orgs, cases, a.T, vis, alert, seeds)
            js[sc][name] = r
            so, sh = r["S_other"], r["S_health"]
            fmt = lambda s: (f"{s['MI']:.3f} ({s['MI_corrected']:.3f})", f"{s['guess_acc']:.2f} / {s['prior_acc']:.2f}") if s else ("-", "-")
            (a1, a2), (b1, b2) = fmt(so), fmt(sh)
            md.append(f"| {name} | {a1} | {a2} | {b1} | {b2} | {100 * r['prevented']:.1f}% | "
                      f"{100 * r['alerted']:.1f}% | {100 * r['benign_person_fp']:.1f}% |")
        md.append(f"\nH(S_other) = {js[sc][next(iter(CONFIGS))]['S_other']['H_S']:.3f} bits, "
                  f"H(S_health) = {js[sc][next(iter(CONFIGS))]['S_health']['H_S']:.3f} bits. "
                  "Most common transcripts (B = blocked) under D3 or: "
                  + ", ".join(f"`{t}` x{n}" for t, n in js[sc][next(iter(CONFIGS))]["transcripts"].items()) + ".")
    out = Path(a.out)
    out.mkdir(exist_ok=True)
    stem = Path(a.bench).stem
    (out / f"leakage_{stem}.md").write_text("\n".join(md) + "\n")
    (out / f"leakage_{stem}.json").write_text(json.dumps(js, indent=1, default=str))
    print("\n".join(md))
    print(f"\nWritten: {out}/leakage_{stem}.md and .json")


if __name__ == "__main__":
    main()
