import argparse

from data import SCENARIO
from ledger import Ledger
import llm
import scorer

PER_REQUEST_LIMIT = 0.6   # baseline: a classic DLP that judges each reply alone
LEDGER_THRESHOLD = 0.75   # cumulative threshold per person


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mock", action="store_true", help="run without LM Studio")
    ap.add_argument("--small", help="Stage 2 model id (default: first loaded model)")
    ap.add_argument("--large", help="Stage 3 model id (optional)")
    args = ap.parse_args()

    small = args.small
    if not args.mock and not small:
        small = llm.list_models()[0]
    print(f"Mode: {'mock' if args.mock else 'LM Studio'} | stage 2: {small} | stage 3: {args.large}\n")

    ledger = Ledger(LEDGER_THRESHOLD)
    header = f"{'day':>3} {'account':8} {'stage':12} {'person':6} {'reply score':>11} " \
             f"{'per-request DLP':16} {'ledger':>6} {'ledger decision':15}"
    print(header)
    print("-" * len(header))

    for ev in SCENARIO:
        stage, res = scorer.score(ev, small, args.large, mock=args.mock)
        pid, fields = res["person_id"], res["fields"]
        reply_score = ledger.coverage(fields)
        baseline = "BLOCK" if reply_score >= PER_REQUEST_LIMIT else "pass"
        decision, proj = ledger.decide(pid, fields)
        print(f"{ev['day']:>3} {ev['account']:8} {stage:12} {str(pid):6} {reply_score:>11.2f} "
              f"{baseline:16} {proj:>6.2f} {decision.upper():15}")

    print("\nLedger per person (highest probability revealed per field):")
    for pid, fields in ledger.revealed.items():
        shown = ", ".join(f"{f}={p:.2f}" for f, p in fields.items() if p > 0)
        print(f"  {pid}: score {ledger.current(pid):.2f} | {shown}")


if __name__ == "__main__":
    main()
