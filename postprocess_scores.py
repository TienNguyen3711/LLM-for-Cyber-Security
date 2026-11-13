"""Apply deterministic defences offline to cached LLM scores, without calling a model.

    python postprocess_scores.py data/bench_s7.json --scorer qwen/qwen3-32b --defense floor,name
    python postprocess_scores.py data/bench_s7.json --scorer qwen/qwen3-32b --dual qwen/qwen3-4b

`floor` and `name` act only on the LLM output and the reply text, so the result is exactly what a
live run with the same LLM answers would give. `spotlight` changes the prompt and needs a live run
(score_events.py --defense spotlight). `--dual SMALL` combines two cached scorers field by field:
the large scorer's value, or the maximum of the two when they differ by at least --gap.
"""
import argparse
import json
from pathlib import Path

from score_events import config_name, load_scores, out_path
from scorer import DisclosureScorer
from synth import FIELD_WEIGHTS


def dual(large, small, gap):
    if large.get("stage") == "error" or small.get("stage") == "error":
        bad = large if large.get("stage") == "error" else small
        return {**bad, "stage": "error"}
    pl, ps = large["person_id"], small["person_id"]
    out = {"eid": large["eid"], "stage": "dual", "latency_s": large["latency_s"] + small["latency_s"],
           "llm_calls": large["llm_calls"] + small["llm_calls"]}
    if pl and ps and pl != ps:  # different people: fields cannot be mixed, keep the large scorer
        return {**out, "person_id": pl, "fields": dict(large["fields"]), "dual": "person-conflict"}
    f = {k: (max(large["fields"][k], small["fields"][k])
             if abs(large["fields"][k] - small["fields"][k]) >= gap else large["fields"][k])
         for k in FIELD_WEIGHTS}
    return {**out, "person_id": pl or ps, "fields": f}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("bench")
    ap.add_argument("--scorer", required=True, help="cached (large) scorer, e.g. qwen/qwen3-32b")
    ap.add_argument("--dual", help="second cached scorer, e.g. qwen/qwen3-4b")
    ap.add_argument("--gap", type=float, default=0.3)
    ap.add_argument("--defense", default="", help="comma list of floor,name")
    a = ap.parse_args()
    defenses = tuple(sorted(d for d in a.defense.split(",") if d))
    if "spotlight" in defenses:
        raise SystemExit("spotlight changes the prompt: run score_events.py --defense spotlight")
    bench = json.loads(Path(a.bench).read_text())
    ev = {e["eid"]: e for e in bench["events"]}
    scores = load_scores(out_path(a.bench, a.scorer))
    if a.dual:
        small = load_scores(out_path(a.bench, a.dual))
        scores = {k: dual(v, small[k], a.gap) for k, v in scores.items() if k in small}
    scorers = {o: DisclosureScorer(cfg["people"], FIELD_WEIGHTS, mock=True, org=cfg["label"])
               for o, cfg in bench["orgs"].items()}
    name = config_name(a.scorer, dual=a.dual, defenses=defenses)
    path = out_path(a.bench, name)
    changed = 0
    with path.open("w") as fh:
        for k, r in scores.items():
            new = scorers[ev[k]["org"]].postprocess(r, ev[k]["reply"], defenses) if defenses else r
            changed += new["fields"] != r["fields"] or new["person_id"] != r["person_id"]
            fh.write(json.dumps(new) + "\n")
    print(f"{path}: {len(scores)} events, {changed} changed by {name}")


if __name__ == "__main__":
    main()
