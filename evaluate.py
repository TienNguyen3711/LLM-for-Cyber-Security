import argparse
import json
import random
import statistics
from collections import defaultdict
from pathlib import Path

from score_events import load_scores, out_path
from synth import FIELD_WEIGHTS

FIELDS = list(FIELD_WEIGHTS)
DETECTORS = {  # name -> what it stands for
    "D0": "per-request DLP",
    "D_session": "per-session ledger (same account, same day)",
    "D1": "per-account, per-person ledger",
    "D_traj": "per-account trajectory budget over all persons (requester-centric)",
    "D2": "per-organisation, per-person ledger",
    "D3": "federated per-person ledger (HMAC pseudonym of name|dob)",
    "D3c": "centralised per-person ledger (true identity, no privacy): upper bound",
}


def coverage(f):
    return round(sum(FIELD_WEIGHTS[k] * f[k] for k in FIELDS), 6)  # avoid 0.7499999 vs 0.75


def combine(per_org, rule):
    """Cross-organisation combination. 'or' and 'max' are unions per field (a field leaked twice
    counts once); 'sum' adds each organisation's own coverage score and so counts it twice."""
    if rule == "sum":
        return sum(coverage(m) for m in per_org)
    comb = {}
    for k in FIELDS:
        ps = [m[k] for m in per_org]
        if rule == "or":
            prod = 1.0
            for p in ps:
                prod *= 1 - p
            comb[k] = 1 - prod
        elif rule == "max":
            comb[k] = max(ps)
        else:
            raise ValueError(rule)
    return coverage(comb)


class Ledger:
    def __init__(self, window):
        self.window, self.entries = window, defaultdict(list)  # key -> [(day, fields)]

    def merged(self, key, day, extra=None):
        out = {k: 0.0 for k in FIELDS}
        for d, f in self.entries.get(key, []) + ([(day, extra)] if extra else []):
            if self.window is None or day - d < self.window:
                for k in FIELDS:
                    out[k] = max(out[k], f[k])
        return out

    def add(self, key, day, f):
        self.entries[key].append((day, f))


def simulate(events, scores, orgs, det, T=0.75, window=None, sticky=True, rule="or", limit=0.6,
             on_error="closed", t_noise=0.0, seed=0, traj_window=30, trace=None):
    """Returns {eid: True if blocked} for one detector configuration.
    on_error: 'closed' blocks an event whose score failed, 'open' treats it as nothing disclosed.
    t_noise: the threshold of each decision is drawn from T +/- t_noise (RQ3 mitigation).
    trace: optional dict filled with {eid: score} for the decisions that used a ledger."""
    rng = random.Random(seed)
    pseudo = {(o, lid): (r["name"], r["dob"]) for o, cfg in orgs.items() for lid, r in cfg["people"].items()}
    glob = {(o, lid): g for o, cfg in orgs.items() for lid, g in cfg["global"].items()}
    led = Ledger(traj_window if det == "D_traj" else window)
    flagged, blocked, session, traj = {}, {}, {}, defaultdict(set)
    for e in events:
        s = scores[e["eid"]]
        if s.get("stage") == "error":
            blocked[e["eid"]] = on_error == "closed"
            continue
        pid, f, day = s["person_id"], s["fields"], e["day"]
        if det == "D0":
            blocked[e["eid"]] = coverage(f) >= limit
            continue
        if pid is None or (e["org"], pid) not in pseudo or not any(f.values()):
            blocked[e["eid"]] = False
            continue
        o, acct = e["org"], e["account"]
        commit = None
        if det == "D_session":
            last = session.get((o, acct))
            idx = last[1] + (day != last[0]) if last else 0
            session[(o, acct)] = (day, idx)
            key = (o, acct, idx, pid)
            score = coverage(led.merged(key, day, f))
        elif det == "D1":
            key = (o, acct, pid)
            score = coverage(led.merged(key, day, f))
        elif det == "D_traj":
            key, commit = (o, acct), (o, acct, pid)
            score = sum(coverage(led.merged((o, acct, q), day, f if q == pid else None))
                        for q in traj[key] | {pid})
        elif det == "D2":
            key = (o, pid)
            score = coverage(led.merged(key, day, f))
        elif det in ("D3", "D3c"):
            key = pseudo[(o, pid)] if det == "D3" else glob[(o, pid)]
            commit = (o, key)
            score = combine([led.merged((q, key), day, f if q == o else None) for q in orgs], rule)
        else:
            raise ValueError(det)
        if trace is not None:
            trace[e["eid"]] = score
        thr = T + (rng.uniform(-t_noise, t_noise) if t_noise else 0.0)
        flag_on = sticky and key in flagged and (window is None or day - flagged[key] < window)
        if score >= thr or flag_on:
            blocked[e["eid"]] = True
            if score >= thr:
                flagged[key] = day  # (re)start the step-up period
        else:
            blocked[e["eid"]] = False
            led.add(commit or key, day, f)
            if det == "D_traj":
                traj[key].add(pid)
    return blocked


def is_probe(strategy):
    return strategy.startswith("P")


def metrics(events, blocked, strategy=None):
    """Assembly campaigns only (P1 probes are measured by leakage.py, not here)."""
    camps = defaultdict(lambda: {"target": set(), "leaked": set(), "blocks": 0})
    victims = set()
    for e in events:
        if e["actor"] != "attacker":
            continue
        victims.add(e["person"])
        if is_probe(e["strategy"]) or (strategy and e["strategy"] != strategy):
            continue
        c = camps[e["campaign"]]
        c["target"] |= set(e["truth_fields"])
        if blocked[e["eid"]]:
            c["blocks"] += 1
        else:
            c["leaked"] |= set(e["truth_fields"])
    n = len(camps) or 1
    w = lambda s: sum(FIELD_WEIGHTS[k] for k in s)
    prevented = sum(not c["target"] <= c["leaked"] for c in camps.values())
    detected = sum(c["blocks"] > 0 for c in camps.values())
    shares = [w(c["leaked"]) / w(c["target"]) for c in camps.values() if c["target"]]
    ben = [e for e in events if e["actor"] == "benign" and e["person"] and e["person"] not in victims]
    persons = {e["person"] for e in ben}
    fp_persons = {e["person"] for e in ben if blocked[e["eid"]]}
    by_kind = defaultdict(lambda: [set(), set()])  # kind -> [persons, persons blocked on this kind]
    for e in ben:
        by_kind[e["benign_kind"]][0].add(e["person"])
        if blocked[e["eid"]]:
            by_kind[e["benign_kind"]][1].add(e["person"])
    col = [e for e in events if e["actor"] == "benign" and e["person"] in victims]
    return {"campaigns": len(camps), "prevented": prevented / n, "detected": detected / n,
            "leaked_share": statistics.mean(shares) if shares else 0.0,
            "benign_event_fp": sum(blocked[e["eid"]] for e in ben) / max(1, len(ben)),
            "benign_person_fp": len(fp_persons) / max(1, len(persons)),
            "fp_by_kind": {k: len(b) / max(1, len(a)) for k, (a, b) in sorted(by_kind.items())},
            "victim_benign_blocked": sum(blocked[e["eid"]] for e in col) / max(1, len(col))}


def scorer_metrics(events, scores):
    ev = [e for e in events if e["eid"] in scores]
    by = defaultdict(lambda: [0, 0, 0])  # tp, fp, fn
    link_ok = link_n = 0
    for e in ev:
        s = scores[e["eid"]]
        pred = {k for k, p in s["fields"].items() if p >= 0.5}
        true = set(e["truth_fields"])
        inj = ("injection", f"inj:{e.get('injection_kind', 'auditor-note')}") if e.get("injection") else ()
        for grp in ("all", f"style:{e['style']}", f"actor:{e['actor']}") + inj:
            by[grp][0] += len(pred & true)
            by[grp][1] += len(pred - true)
            by[grp][2] += len(true - pred)
        pn, tn = pred - {"name"}, true - {"name"}
        by["all excl. name"][0] += len(pn & tn)
        by["all excl. name"][1] += len(pn - tn)
        by["all excl. name"][2] += len(tn - pn)
        by["name only"][0] += len(pred & true & {"name"})
        by["name only"][1] += len((pred - true) & {"name"})
        by["name only"][2] += len((true - pred) & {"name"})
        if true:
            link_n += 1
            link_ok += s["person_id"] == e["local_id"]
    out = {}
    for g, (tp, fp, fn) in sorted(by.items()):
        p = tp / (tp + fp) if tp + fp else float("nan")
        r = tp / (tp + fn) if tp + fn else float("nan")
        out[g] = {"precision": p, "recall": r, "f1": 2 * p * r / (p + r) if p + r else float("nan"),
                  "support": tp + fn}
    lat = [scores[e["eid"]]["latency_s"] for e in ev if scores[e["eid"]]["llm_calls"]]
    return {"events": len(ev), "fields": out, "linkage": link_ok / max(1, link_n),
            "stage1_exit": sum(scores[e["eid"]]["stage"] == "stage1-exit" for e in ev) / max(1, len(ev)),
            "errors": sum(scores[e["eid"]]["stage"] == "error" for e in ev),
            "latency_mean": statistics.mean(lat) if lat else 0.0,
            "latency_p95": sorted(lat)[int(0.95 * (len(lat) - 1))] if lat else 0.0}


def pct(x):
    return f"{100 * x:5.1f}%"


RQ1_CFGS = {"D0 per-request (limit 0.6)": dict(det="D0"),
            "D_session per-session": dict(det="D_session"),
            "D1 per-account": dict(det="D1"),
            "D_traj per-account trajectory (30 d)": dict(det="D_traj"),
            "D2 per-org": dict(det="D2"),
            "D3 federated (or)": dict(det="D3", rule="or"),
            "D3c centralised (or)": dict(det="D3c", rule="or")}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("bench")
    ap.add_argument("--scores", nargs="+", default=["oracle"])
    ap.add_argument("--T", type=float, default=0.75)
    ap.add_argument("--on-error", choices=["closed", "open"], default="closed")
    ap.add_argument("--out", default="results")
    ap.add_argument("--tag", default="", help="suffix for the output file names")
    a = ap.parse_args()
    bench = json.loads(Path(a.bench).read_text())
    events, orgs = bench["events"], bench["orgs"]
    strategies = [s for s in bench["meta"]["strategies"] if not is_probe(s)]
    md, js = [f"# Topic 3 benchmark results: `{a.bench}`\n",
              f"{bench['meta']['people']} people, {len(events)} events, strategies: {', '.join(bench['meta']['strategies'])}; "
              f"seed {bench['meta']['seed']}. Scoring errors are handled fail-{a.on_error}.\n"], {}

    for sc in a.scores:
        p = out_path(a.bench, sc)
        if not p.exists():
            print(f"skip {sc}: {p} not found")
            continue
        scores = load_scores(p)
        full = all(e["eid"] in scores for e in events)
        js[sc] = {"scorer": scorer_metrics(events, scores) if sc != "oracle" else None}
        md.append(f"\n## Scorer: `{sc}` ({len(scores)} events scored{'' if full else ', subset'})\n")

        if sc != "oracle":
            m = js[sc]["scorer"]
            md.append(f"Field detection (p >= 0.5): person linkage {pct(m['linkage'])}, "
                      f"stage-1 exit {pct(m['stage1_exit'])}, **scoring errors {m['errors']}**, "
                      f"latency mean {m['latency_mean']:.2f} s, p95 {m['latency_p95']:.2f} s\n")
            md.append("| group | precision | recall | F1 | true fields |\n|---|---|---|---|---|")
            for g, v in m["fields"].items():
                md.append(f"| {g} | {v['precision']:.3f} | {v['recall']:.3f} | {v['f1']:.3f} | {v['support']} |")

        if not full:
            md.append("\n(Detector metrics need every event scored; skipped for this subset.)")
            continue
        sim = lambda **kw: simulate(events, scores, orgs, on_error=a.on_error, **kw)

        # RQ1: which accounting unit stops assembly?
        md.append(f"\n### RQ1: which accounting unit stops assembly? (T = {a.T}, no window, sticky)\n")
        md.append("Cell = prevented (attacker never got every targeted field) / mean share of the targeted "
                  "record leaked. P1 probes are excluded here (see leakage.py).\n")
        md.append("| detector | " + " | ".join(strategies) + " | all | benign person FP | victim's own requests blocked |")
        md.append("|---|" + "---|" * (len(strategies) + 3))
        js[sc]["rq1"] = {}
        for name, cfg in RQ1_CFGS.items():
            b = sim(T=a.T, **cfg)
            row, allm = [], metrics(events, b)
            js[sc]["rq1"][name] = {"all": allm}
            for st in strategies:
                m = metrics(events, b, st)
                js[sc]["rq1"][name][st] = m
                row.append(f"{pct(m['prevented'])} / {pct(m['leaked_share'])}")
            md.append(f"| {name} | " + " | ".join(row) +
                      f" | {pct(allm['prevented'])} / {pct(allm['leaked_share'])} | "
                      f"{pct(allm['benign_person_fp'])} | {pct(allm['victim_benign_blocked'])} |")

        Ts = [0.4, 0.5, 0.6, 0.65, 0.7, 0.75, 0.8, 0.85, 0.9, 0.95]
        md.append("\n### RQ1 (sweep): threshold, window and sticky step-up (all assembly strategies)\n")
        md.append("Cell = prevented / benign person FP.\n")
        variants = {"D1 per-account": dict(det="D1"),
                    "D2 per-org": dict(det="D2"),
                    "D3 or": dict(det="D3", rule="or"),
                    "D3 or, 90-day window": dict(det="D3", rule="or", window=90),
                    "D3 or, 30-day window": dict(det="D3", rule="or", window=30),
                    "D3 or, not sticky": dict(det="D3", rule="or", sticky=False)}
        md.append("| variant | " + " | ".join(f"T={t}" for t in Ts) + " |")
        md.append("|---|" + "---|" * len(Ts))
        js[sc]["rq1_sweep"] = {}
        for name, cfg in variants.items():
            cells = []
            for t in Ts:
                m = metrics(events, sim(T=t, **cfg))
                js[sc]["rq1_sweep"].setdefault(name, {})[t] = m
                cells.append(f"{pct(m['prevented'])} / {pct(m['benign_person_fp'])}")
            md.append(f"| {name} | " + " | ".join(cells) + " |")
        cells = []
        for lim in Ts:
            m = metrics(events, sim(det="D0", limit=lim))
            cells.append(f"{pct(m['prevented'])} / {pct(m['benign_person_fp'])}")
        md.append("| D0 per-request (limit = T) | " + " | ".join(cells) + " |")

        # RQ2: aggregation semantics
        kinds = sorted({e["benign_kind"] for e in events if e["actor"] == "benign" and e["person"]})
        ov = [k for k in kinds if k.startswith("overlap")]
        md.append("\n### RQ2: cross-organisation aggregation (union vs naive sum)\n")
        md.append("`or`/`max` count a field disclosed by two organisations once; `sum` adds the organisations' "
                  "own scores, so it counts it twice. Cell = prevented / benign person FP"
                  + (" / FP among overlap customers (" + ", ".join(ov) + ")" if ov else "") + ".\n")
        Ts2 = [0.6, 0.7, 0.75, 0.8, 0.9, 1.0, 1.2]
        md.append("| rule | " + " | ".join(f"T={t}" for t in Ts2) + " |")
        md.append("|---|" + "---|" * len(Ts2))
        js[sc]["rq2"] = {}
        for rule in ("or", "max", "sum"):
            cells = []
            for t in Ts2:
                m = metrics(events, sim(det="D3", rule=rule, T=t))
                js[sc]["rq2"].setdefault(rule, {})[t] = m
                cell = f"{pct(m['prevented'])} / {pct(m['benign_person_fp'])}"
                if ov:
                    cell += " / " + pct(statistics.mean(m["fp_by_kind"].get(k, 0) for k in ov))
                cells.append(cell)
            md.append(f"| D3 {rule} | " + " | ".join(cells) + " |")
        s5 = next((s for s in strategies if s.startswith("S5")), None)
        if s5:
            md.append(f"\nAt T = {a.T}, {s5}: " + "; ".join(
                f"{rule} prevented {pct(metrics(events, sim(det='D3', rule=rule, T=a.T), s5)['prevented'])}"
                for rule in ("or", "max", "sum")) + ".")
        md.append(f"\nBenign person FP by kind at T = {a.T}:\n")
        md.append("| rule | " + " | ".join(kinds) + " |\n|---|" + "---|" * len(kinds))
        for rule in ("or", "max", "sum"):
            fk = js[sc]["rq2"][rule][a.T]["fp_by_kind"] if a.T in Ts2 else metrics(events, sim(det="D3", rule=rule, T=a.T))["fp_by_kind"]
            md.append(f"| D3 {rule} | " + " | ".join(pct(fk.get(k, 0)) for k in kinds) + " |")

    # RQ4: LLM scorers compared on the events every one of them scored
    llms = [sc for sc in a.scores if sc != "oracle" and out_path(a.bench, sc).exists()]
    if len(llms) > 1:
        loaded = {sc: load_scores(out_path(a.bench, sc)) for sc in llms}
        common = set.intersection(*(set(v) for v in loaded.values()))
        sub = [e for e in events if e["eid"] in common]
        md.append(f"\n## RQ4: scorers and defences on the same {len(sub)} events\n")
        groups = ["all", "all excl. name", "name only", "style:direct", "style:paraphrase", "style:inferable",
                  "injection"]
        md.append("| scorer | " + " | ".join(f"F1 {g}" for g in groups) +
                  " | injection recall | linkage | errors | mean latency (s) |")
        md.append("|---|" + "---|" * (len(groups) + 4))
        js["rq4_common"] = {}
        for sc in llms:
            m = scorer_metrics(sub, {k: v for k, v in loaded[sc].items() if k in common})
            js["rq4_common"][sc] = m
            f1 = [f"{m['fields'][g]['f1']:.3f}" if g in m["fields"] else "-" for g in groups]
            inj = m["fields"].get("injection", {}).get("recall", float("nan"))
            md.append(f"| {sc} | " + " | ".join(f1) +
                      f" | {inj:.3f} | {pct(m['linkage'])} | {m['errors']} | {m['latency_mean']:.2f} |")

    out = Path(a.out)
    out.mkdir(exist_ok=True)
    stem = Path(a.bench).stem + (f"_{a.tag}" if a.tag else "")
    (out / f"eval_{stem}.md").write_text("\n".join(md) + "\n")
    (out / f"eval_{stem}.json").write_text(json.dumps(js, indent=1, default=str))
    print("\n".join(md))
    print(f"\nWritten: {out}/eval_{stem}.md and .json")


if __name__ == "__main__":
    main()
