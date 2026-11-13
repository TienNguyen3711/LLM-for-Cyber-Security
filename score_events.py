import argparse
import hashlib
import json
import random
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from scorer import DEFENSES, DisclosureScorer
from synth import FIELD_WEIGHTS


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def config_name(scorer, large=None, defenses=(), dual=None):
    """One name per scorer configuration, so runs with and without defences never share a cache."""
    name = scorer + (f"+{large}" if large else "") + (f"+dual-{dual}" if dual else "")
    return name + (f"+def-{'-'.join(sorted(defenses))}" if defenses else "")


def out_path(bench_path, scorer):
    return Path(bench_path).with_name(f"scores_{Path(bench_path).stem}_{slug(scorer)}.jsonl")


def load_scores(path):
    return {r["eid"]: r for r in (json.loads(l) for l in Path(path).read_text().splitlines())}


def event_hash(e):
    """Content fingerprint stored with every score, so a regenerated bench never reuses a stale score."""
    return hashlib.sha256(json.dumps([e["org"], e["request"], e["reply"]]).encode()).hexdigest()[:12]


def oracle_score(e):
    f = {k: float(k in e["truth_fields"]) for k in FIELD_WEIGHTS}
    return {"eid": e["eid"], "person_id": e["local_id"] if e["truth_fields"] else None, "fields": f,
            "stage": "oracle", "latency_s": 0.0, "llm_calls": 0}


def error_record(e, err, scorer=None):
    """A failed score is flagged, never silently turned into 'nothing disclosed'. The detector
    decides what an error means (evaluate.py --on-error, default closed = block)."""
    r = {"eid": e["eid"], "person_id": None, "fields": {k: 0.0 for k in FIELD_WEIGHTS},
         "stage": "error", "error": True, "latency_s": 0.0, "llm_calls": 0, "rationale": err}
    if scorer is not None:  # deterministic defences still apply when the LLM failed
        r.update(scorer.postprocess(r, e["reply"]))
    return r


def stratified_sample(events, n, seed=0):
    """Keep all strata represented: attacker by strategy, benign by kind."""
    rng = random.Random(seed)
    strata = {}
    for e in events:
        strata.setdefault((e["actor"], e.get("strategy") or e.get("benign_kind")), []).append(e)
    frac = n / len(events)
    keep = []
    for group in strata.values():
        keep += rng.sample(group, max(1, round(len(group) * frac)))
    return sorted(keep, key=lambda e: e["eid"])


def reuse_cache(bench_path, events, name, other_bench):
    """Copy scores of the same configuration from another bench for events with identical
    eid, organisation, request and reply (e.g. bench_s7 -> bench_s7x)."""
    src = out_path(other_bench, name)
    if not src.exists():
        return {}
    other = {e["eid"]: e for e in json.loads(Path(other_bench).read_text())["events"]}
    cached = load_scores(src)
    same = lambda e, o: all(e[k] == o[k] for k in ("org", "request", "reply"))
    return {e["eid"]: cached[e["eid"]] for e in events
            if e["eid"] in cached and e["eid"] in other and same(e, other[e["eid"]])}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("bench")
    ap.add_argument("--scorer", default="oracle", help="'oracle' or an LM Studio model id")
    ap.add_argument("--large", help="optional Stage 3 judge model")
    ap.add_argument("--defense", default="", help=f"comma list of {','.join(DEFENSES)}")
    ap.add_argument("--sample", type=int, help="score a stratified subset of N events")
    ap.add_argument("--only", choices=["injection", "new"], help="score only injection events, or only X.. events")
    ap.add_argument("--reuse", help="another bench whose cached scores (same configuration) are copied")
    ap.add_argument("--retry-errors", action="store_true", help="re-score cached events that failed")
    ap.add_argument("--workers", type=int, default=2)
    a = ap.parse_args()

    defenses = tuple(sorted(d for d in a.defense.split(",") if d))
    bench = json.loads(Path(a.bench).read_text())
    events = bench["events"]
    if a.sample:
        events = stratified_sample(events, a.sample)
    if a.only == "injection":
        events = [e for e in events if e.get("injection")]
    elif a.only == "new":
        events = [e for e in events if e["eid"].startswith("X")]
    name = config_name(a.scorer, a.large, defenses)
    path = out_path(a.bench, name)
    done = load_scores(path) if path.exists() else {}
    by_eid = {e["eid"]: e for e in bench["events"]}
    stale = {k for k, r in done.items() if "h" in r and (k not in by_eid or r["h"] != event_hash(by_eid[k]))}
    if stale:
        raise SystemExit(f"{path}: {len(stale)} cached scores do not match the bench content "
                         f"(bench regenerated?). Delete the file and score again.")
    if a.reuse:
        copied = {k: v for k, v in reuse_cache(a.bench, bench["events"], name, a.reuse).items() if k not in done}
        with path.open("a") as fh:
            for r in copied.values():
                fh.write(json.dumps(r) + "\n")
        done.update(copied)
        print(f"reused {len(copied)} scores from {out_path(a.reuse, name)}")
    if a.retry_errors:
        bad = {k for k, r in done.items() if r.get("stage") == "error"}
        if bad:  # rewrite the cache without the failures, then score them again
            done = {k: r for k, r in done.items() if k not in bad}
            path.write_text("".join(json.dumps(r) + "\n" for r in done.values()))
            print(f"retrying {len(bad)} failed events")
    todo = [e for e in events if e["eid"] not in done]
    print(f"{path}: {len(done)} cached, {len(todo)} to score with {name}")

    if a.scorer == "oracle":
        if defenses:
            raise SystemExit("the oracle takes no defences")
        with path.open("a") as fh:
            for e in todo:
                fh.write(json.dumps({**oracle_score(e), "h": event_hash(e)}) + "\n")
        return

    scorers = {o: DisclosureScorer(cfg["people"], FIELD_WEIGHTS, a.scorer, a.large, False, cfg["label"],
                                   defenses=defenses)
               for o, cfg in bench["orgs"].items()}

    def run(e):
        err = ""
        for attempt in range(3):
            try:
                r = scorers[e["org"]].score(e["request"], e["reply"])
                return {"eid": e["eid"], **{k: r[k] for k in
                        ("person_id", "fields", "stage", "latency_s", "llm_calls", "rationale")},
                        **({"floor": r["floor"]} if "floor" in r else {})}
            except Exception as exc:  # malformed JSON or server hiccup: retry, then flag the failure
                err = str(exc)
                time.sleep(2)
        return error_record(e, err, scorers[e["org"]])

    t0, n = time.time(), 0
    with path.open("a") as fh, ThreadPoolExecutor(a.workers) as pool:
        for fut in as_completed([pool.submit(run, e) for e in todo]):
            r, e = fut.result(), by_eid[fut.result()["eid"]]
            fh.write(json.dumps({**r, "h": event_hash(e)}) + "\n")
            fh.flush()
            n += 1
            if n % 25 == 0 or n == len(todo):
                rate = (time.time() - t0) / n
                print(f"  {n}/{len(todo)}  {rate:.1f} s/event  eta {rate * (len(todo) - n) / 60:.0f} min",
                      flush=True)


if __name__ == "__main__":
    main()
