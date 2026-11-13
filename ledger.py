from collections import defaultdict

from data import FIELD_WEIGHTS


class Ledger:
    def __init__(self, threshold):
        self.threshold = threshold
        # person_id -> field -> highest probability revealed so far
        self.revealed = defaultdict(lambda: {f: 0.0 for f in FIELD_WEIGHTS})

    @staticmethod
    def coverage(fields):
        return sum(FIELD_WEIGHTS[f] * p for f, p in fields.items())

    def current(self, pid):
        return self.coverage(self.revealed[pid]) if pid else 0.0

    def projected(self, pid, fields):
        """Score if this reply were released (max-composition per field)."""
        merged = {f: max(self.revealed[pid][f], fields[f]) for f in FIELD_WEIGHTS}
        return self.coverage(merged)

    def decide(self, pid, fields):
        """Check BEFORE release: block the reply that would cross the threshold."""
        if pid is None:
            return "allow", 0.0
        proj = self.projected(pid, fields)
        if proj >= self.threshold:
            return "block", proj
        for f in FIELD_WEIGHTS:
            self.revealed[pid][f] = max(self.revealed[pid][f], fields[f])
        return "allow", proj
