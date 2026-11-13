import argparse
import json
import secrets
import time
from collections import defaultdict
from pathlib import Path

import federation
import llm
from scorer import DisclosureScorer
from xinst_data import FIELD_WEIGHTS, ORGS, SCENARIO

PER_REQUEST_LIMIT = 0.6
DETECTORS = ["D0 per-request", "D1 per-account", "D2 per-org", "D3 federated"]


def coverage(fields):
    return sum(FIELD_WEIGHTS[f] * p for f, p in fields.items())


def merge(a, b):
    return {f: max(a[f], b[f]) for f in FIELD_WEIGHTS}


class LocalLedger:
    """Max-composition ledger keyed by an arbitrary scope (account+person, or org+person)."""

    def __init__(self, threshold):
        self.t, self.s = threshold, defaultdict(lambda: {f: 0.0 for f in FIELD_WEIGHTS})

    def decide(self, key, fields):
        proj = coverage(merge(self.s[key], fields))
        if proj >= self.t:
            return "BLOCK", proj
        self.s[key] = merge(self.s[key], fields)
        return "allow", proj


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mock", action="store_true")
    ap.add_argument("--small", help="Stage 2 model id (default: first loaded LLM)")
    ap.add_argument("--large", help="Stage 3 judge model id (optional)")
    ap.add_argument("--threshold", type=float, default=0.75)
    ap.add_argument("--no-sticky", action="store_true",
                    help="after a crossing, judge later releases by score only (no step-up state)")
    ap.add_argument("--out", default="results")
    args = ap.parse_args()

    small = args.small
    if not args.mock and not small:
        small = next(m for m in llm.list_models() if "embed" not in m)
    print(f"Mode: {'mock' if args.mock else 'LM Studio'} | stage 2: {small} | "
          f"stage 3: {args.large} | threshold: {args.threshold} | sticky: {not args.no_sticky}\n")

    key = secrets.token_bytes(32)  # shared by the organisations, never by the coordinator
    orgs = {name: federation.Organisation(
                key, name, cfg, FIELD_WEIGHTS,
                DisclosureScorer(cfg["people"], FIELD_WEIGHTS, small, args.large, args.mock, cfg["label"]))
            for name, cfg in ORGS.items()}
    coord = federation.Coordinator(FIELD_WEIGHTS, args.threshold, sticky=not args.no_sticky)
    d1, d2 = LocalLedger(args.threshold), LocalLedger(args.threshold)
    audit_view = None

    rows = []
    hdr = (f"{'day':>3} {'org':6} {'account':14} {'stage':11} {'person':7} {'reply':>5} | "
           f"{'D0':>5} {'D1':>11} {'D2':>11} {'D3':>11} | actor")
    print(hdr + "\n" + "-" * len(hdr))
    for ev in SCENARIO:
        org = orgs[ev["org"]]
        r = org.scorer.score(ev["request"], ev["reply"])
        pid, fields = r["person_id"], r["fields"]
        rs = coverage(fields)
        dec = {"D0 per-request": ("BLOCK" if rs >= PER_REQUEST_LIMIT else "allow", rs)}
        if pid is None:
            for d in DETECTORS[1:]:
                dec[d] = ("allow", 0.0)
        else:
            dec["D1 per-account"] = d1.decide((ev["account"], pid), fields)
            dec["D2 per-org"] = d2.decide((ev["org"], pid), fields)
            pseudo = org.pseudo[pid]
            vectors = {n: o.vector_for(pseudo, fields if n == ev["org"] else None)
                       for n, o in orgs.items()}
            crossed, score = coord.query(pseudo, federation.masked_contributions(vectors, list(FIELD_WEIGHTS)))
            if crossed:
                audit_view = audit_view or coord.last_view
                dec["D3 federated"] = ("BLOCK", score)
            else:
                org.commit(pid, fields)
                dec["D3 federated"] = ("allow", score)
        cell = lambda d: f"{dec[d][0]} {dec[d][1]:.2f}"
        print(f"{ev['day']:>3} {ev['org']:6} {ev['account']:14} {r['stage']:11} {str(pid):7} {rs:>5.2f} | "
              f"{dec['D0 per-request'][0]:>5} {cell('D1 per-account'):>11} {cell('D2 per-org'):>11} "
              f"{cell('D3 federated'):>11} | {ev['actor']}")
        rows.append({**ev, "score": r, "reply_score": rs,
                     "decisions": {d: {"decision": v[0], "score": round(v[1], 4)} for d, v in dec.items()}})

    summary = evaluate(rows, orgs)
    print_summary(summary, audit_view)

    out = Path(args.out)
    out.mkdir(exist_ok=True)
    stamp = time.strftime("%Y%m%d_%H%M%S")
    path = out / f"xinst_{'mock' if args.mock else 'lmstudio'}{'_nosticky' if args.no_sticky else ''}_{stamp}.json"
    path.write_text(json.dumps({"config": {"small": small, "large": args.large, "mock": args.mock,
                                           "threshold": args.threshold, "sticky": not args.no_sticky, "per_request_limit": PER_REQUEST_LIMIT,
                                           "weights": FIELD_WEIGHTS},
                                "events": rows, "summary": summary,
                                "coordinator_view_at_first_block": audit_view},
                               indent=2, default=str))
    print(f"\nFull log: {path}")


def evaluate(rows, orgs):
    s = {"detectors": {}, "scorer": {}}
    for d in DETECTORS:
        att = [r for r in rows if r["actor"] == "attacker"]
        ben = [r for r in rows if r["actor"] == "benign"]
        first = next((r["day"] for r in att if r["decisions"][d]["decision"] == "BLOCK"), None)
        leaked = sorted({f for r in att if r["decisions"][d]["decision"] == "allow"
                         for f in r["truth"]["fields"]})
        s["detectors"][d] = {
            "first_attacker_block_day": first,
            "attacker_events_blocked": sum(r["decisions"][d]["decision"] == "BLOCK" for r in att),
            "attacker_events": len(att),
            "benign_blocked": sum(r["decisions"][d]["decision"] == "BLOCK" for r in ben),
            "benign_events": len(ben),
            "fields_leaked_to_attacker": leaked,
            "attacker_profile_coverage": round(sum(FIELD_WEIGHTS[f] for f in leaked), 2),
        }
    # Scorer accuracy against ground truth (field level, p >= 0.5 counts as revealed)
    tp = fp = fn = 0
    link_ok = 0
    errors = []
    for r in rows:
        org = orgs[r["org"]]
        truth_pid = next((pid for pid, p in org.people.items() if p["name"] == r["truth"]["person"]), None)
        link_ok += r["score"]["person_id"] == truth_pid
        pred = {f for f, p in r["score"]["fields"].items() if p >= 0.5}
        true = set(r["truth"]["fields"])
        tp, fp, fn = tp + len(pred & true), fp + len(pred - true), fn + len(true - pred)
        if pred != true:
            errors.append({"day": r["day"], "missed": sorted(true - pred), "extra": sorted(pred - true)})
    s["scorer"] = {
        "field_precision": round(tp / (tp + fp), 3) if tp + fp else None,
        "field_recall": round(tp / (tp + fn), 3) if tp + fn else None,
        "person_linkage_accuracy": f"{link_ok}/{len(rows)}",
        "field_errors": errors,
        "stage_counts": {st: sum(r["score"]["stage"] == st for r in rows)
                         for st in sorted({r["score"]["stage"] for r in rows})},
        "llm_calls": sum(r["score"]["llm_calls"] for r in rows),
        "mean_latency_s_llm_events": round(
            sum(r["score"]["latency_s"] for r in rows if r["score"]["llm_calls"]) /
            max(1, sum(1 for r in rows if r["score"]["llm_calls"])), 2),
    }
    return s


def print_summary(s, view):
    print("\nDetector comparison (blocked / events; 'profile leaked' = weighted share of the record the attacker got)")
    print(f"{'detector':16} {'first block':>11} {'att. blocked':>12} {'benign FP':>9} "
          f"{'profile leaked':>14}  fields leaked")
    for d, v in s["detectors"].items():
        print(f"{d:16} {str(v['first_attacker_block_day'] or '-'):>11} "
              f"{v['attacker_events_blocked']:>5}/{v['attacker_events']:<6} "
              f"{v['benign_blocked']:>5}/{v['benign_events']:<3} {v['attacker_profile_coverage']:>14.2f}  "
              f"{', '.join(v['fields_leaked_to_attacker'])}")
    sc = s["scorer"]
    print(f"\nScorer: field precision {sc['field_precision']}, recall {sc['field_recall']}, "
          f"person linkage {sc['person_linkage_accuracy']}, stages {sc['stage_counts']}, "
          f"LLM calls {sc['llm_calls']}, mean latency {sc['mean_latency_s_llm_events']} s")
    for e in sc["field_errors"]:
        print(f"  day {e['day']}: missed {e['missed']} extra {e['extra']}")
    if view:
        print(f"\nCoordinator view at the first federated block (pseudonym {view['pseudonym']}):")
        for o, m in view["masked"].items():
            print(f"  {o:6} sends masked name={m['name']:>19} dob={m['dob']:>19} ...")
        print(f"  -> unmasked only in the sum: score {view['score']:.2f}; organisations receive only 'crossed'")


if __name__ == "__main__":
    main()
