import argparse, json, statistics, time
from pathlib import Path
from scorer import DisclosureScorer
from score_events import stratified_sample
from synth import FIELD_WEIGHTS

ap = argparse.ArgumentParser()
ap.add_argument("bench"); ap.add_argument("models", nargs="+"); ap.add_argument("--n", type=int, default=20)
a = ap.parse_args()
bench = json.loads(Path(a.bench).read_text())
ev = [e for e in stratified_sample(bench["events"], a.n * 2, seed=1) if e["person"]][:a.n]
res = {}
for m in a.models:
    sc = {o: DisclosureScorer(c["people"], FIELD_WEIGHTS, m, None, False, c["label"]) for o, c in bench["orgs"].items()}
    sc[ev[0]["org"]].score(ev[0]["request"], ev[0]["reply"])  # warm-up
    lat = []
    for e in ev:
        t = time.time(); sc[e["org"]].score(e["request"], e["reply"]); lat.append(time.time() - t)
    res[m] = {"n": len(lat), "mean_s": round(statistics.mean(lat), 2), "median_s": round(statistics.median(lat), 2),
              "max_s": round(max(lat), 2)}
    print(m, res[m], flush=True)
Path("results").mkdir(exist_ok=True)
Path(f"results/latency_{Path(a.bench).stem}.json").write_text(json.dumps(res, indent=1))
