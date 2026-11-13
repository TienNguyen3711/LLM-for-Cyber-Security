"""Repeat the oracle-scored RQ1-RQ3 measurements over several generated benches (mean +/- sd).

    python multiseed.py --seeds 7 11 13 17 19 23 29 31 37 41 --overlap 20 --probes 120

The oracle scorer isolates the accounting mechanism from scorer error; LLM-scored numbers for one seed
come from evaluate.py / leakage.py.
"""
import argparse
import json
import statistics
from pathlib import Path

from evaluate import RQ1_CFGS, metrics, simulate
from leakage import CONFIGS, evaluate_config, probe_cases
from score_events import oracle_score
from synth import build_bench, default_out


def ms(xs):
    xs = list(xs)
    sd = statistics.stdev(xs) if len(xs) > 1 else 0.0
    return f"{100 * statistics.mean(xs):5.1f} ± {100 * sd:4.1f}"


def msb(xs):
    xs = list(xs)
    sd = statistics.stdev(xs) if len(xs) > 1 else 0.0
    return f"{statistics.mean(xs):.3f} ± {sd:.3f}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, nargs="+", default=[7, 11, 13, 17, 19, 23, 29, 31, 37, 41])
    ap.add_argument("--overlap", type=int, default=20)
    ap.add_argument("--probes", type=int, default=120)
    ap.add_argument("--T", type=float, default=0.75)
    ap.add_argument("--out", default="results")
    a = ap.parse_args()

    rows = []
    for seed in a.seeds:
        path = Path(default_out(seed, a.overlap, a.probes))
        if path.exists():
            bench = json.loads(path.read_text())
        else:
            bench = build_bench(seed, overlap=a.overlap, probes=a.probes)
            path.parent.mkdir(exist_ok=True)
            path.write_text(json.dumps(bench, indent=1))
        events, orgs = bench["events"], bench["orgs"]
        scores = {e["eid"]: oracle_score(e) for e in events}
        strategies = [s for s in bench["meta"]["strategies"] if not s.startswith("P")]
        r = {"seed": seed, "rq1": {}, "rq2": {}, "rq3": {}}
        for name, cfg in RQ1_CFGS.items():
            b = simulate(events, scores, orgs, T=a.T, **cfg)
            r["rq1"][name] = {"all": metrics(events, b), **{s: metrics(events, b, s) for s in strategies}}
        for rule in ("or", "max", "sum"):
            r["rq2"][rule] = metrics(events, simulate(events, scores, orgs, det="D3", rule=rule, T=a.T))
        cases = probe_cases(events)
        for name, (vis, alert) in CONFIGS.items():
            seeds = range(5) if vis.get("t_noise") else [0]
            r["rq3"][name] = evaluate_config(events, scores, orgs, cases, a.T, vis, alert, seeds)
        rows.append(r)
        print(f"seed {seed}: {len(events)} events done", flush=True)

    strategies = [s for s in rows[0]["rq1"][next(iter(RQ1_CFGS))] if s != "all"]
    md = [f"# Oracle-scored results over {len(rows)} seeds ({', '.join(map(str, a.seeds))})\n",
          f"Each bench: 300 people, 60 base campaigns, --overlap {a.overlap}, --probes {a.probes}; T = {a.T}. "
          "Cells are mean ± sd across seeds, in % unless marked bits.\n",
          "\n## RQ1: prevented by accounting unit\n",
          "| detector | " + " | ".join(strategies) + " | all | benign person FP |",
          "|---|" + "---|" * (len(strategies) + 2)]
    for name in RQ1_CFGS:
        md.append(f"| {name} | " + " | ".join(ms(r["rq1"][name][s]["prevented"] for r in rows) for s in strategies)
                  + f" | {ms(r['rq1'][name]['all']['prevented'] for r in rows)} | "
                  f"{ms(r['rq1'][name]['all']['benign_person_fp'] for r in rows)} |")
    md += ["\n## RQ2: aggregation rule (D3)\n",
           "| rule | prevented | benign person FP | FP overlap-moved | FP overlap-kyc |", "|---|---|---|---|---|"]
    for rule in ("or", "max", "sum"):
        g = lambda k: ms(r["rq2"][rule]["fp_by_kind"].get(k, 0) for r in rows)
        md.append(f"| {rule} | {ms(r['rq2'][rule]['prevented'] for r in rows)} | "
                  f"{ms(r['rq2'][rule]['benign_person_fp'] for r in rows)} | {g('overlap-moved')} | {g('overlap-kyc')} |")
    md += ["\n## RQ3: crossing-bit leakage to a probing requester\n",
           "MI is bias-corrected (minus the shuffled-secret MI), in bits.\n",
           "| configuration | S_other MI | S_health MI | S_health guess − prior (pp) | assembly prevented | alerted | benign person FP |",
           "|---|---|---|---|---|---|---|"]
    for name in CONFIGS:
        g = [r["rq3"][name] for r in rows]
        md.append(f"| {name} | {msb(x['S_other']['MI_corrected'] for x in g)} | "
                  f"{msb(x['S_health']['MI_corrected'] for x in g)} | "
                  f"{ms(x['S_health']['guess_acc'] - x['S_health']['prior_acc'] for x in g)} | "
                  f"{ms(x['prevented'] for x in g)} | {ms(x['alerted'] for x in g)} | "
                  f"{ms(x['benign_person_fp'] for x in g)} |")
    out = Path(a.out)
    out.mkdir(exist_ok=True)
    (out / "multiseed.md").write_text("\n".join(md) + "\n")
    (out / "multiseed.json").write_text(json.dumps(rows, indent=1, default=str))
    print("\n".join(md))


if __name__ == "__main__":
    main()
