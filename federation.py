import hashlib
import hmac
import math
import secrets

MOD = 2 ** 61 - 1          # arithmetic modulus for masked values
SCALE = 10 ** 6            # fixed-point scale
P_CAP = 0.999              # avoid infinite log for p = 1


def pseudonym(key: bytes, name: str, dob: str) -> str:
    msg = f"{' '.join(name.lower().split())}|{dob}".encode()
    return hmac.new(key, msg, hashlib.sha256).hexdigest()[:16]


def encode(p):
    return int(round(-math.log(1 - min(p, P_CAP)) * SCALE)) % MOD


def decode_sum(v):
    return 1 - math.exp(-v / SCALE)


def masked_contributions(vectors, fields):
    """vectors: {org: {field: p}} -> {org: {field: masked int}} (masks cancel in the sum)."""
    orgs = sorted(vectors)
    masked = {o: {f: encode(vectors[o].get(f, 0.0)) for f in fields} for o in orgs}
    for i, a in enumerate(orgs):
        for b in orgs[i + 1:]:
            for f in fields:
                r = secrets.randbelow(MOD)
                masked[a][f] = (masked[a][f] + r) % MOD
                masked[b][f] = (masked[b][f] - r) % MOD
    return masked


class Coordinator:
    """Sees only masked contributions; returns only 'crossed' to the organisations."""

    def __init__(self, weights, threshold, sticky=True):
        self.weights, self.threshold, self.sticky = weights, threshold, sticky
        self.flagged = set()   # pseudonyms that crossed once (sticky mode: step-up from then on)
        self.last_view = None  # what the coordinator actually observed, kept for the audit print

    def query(self, pseudo, masked):
        fields = list(self.weights)
        sums = {f: sum(m[f] for m in masked.values()) % MOD for f in fields}
        combined = {f: decode_sum(sums[f]) for f in fields}
        score = sum(self.weights[f] * combined[f] for f in fields)
        self.last_view = {"pseudonym": pseudo, "masked": masked,
                          "combined_fields": combined, "score": score}
        crossed = score >= self.threshold or (self.sticky and pseudo in self.flagged)
        if crossed:
            self.flagged.add(pseudo)
        return crossed, score


class Organisation:
    """Local scorer + local per-person ledger; shares only masked vectors under a pseudonym."""

    def __init__(self, key, name, cfg, weights, scorer):
        self.name, self.label, self.people = name, cfg["label"], cfg["people"]
        self.weights, self.scorer = weights, scorer
        self.pseudo = {pid: pseudonym(key, p["name"], p["dob"]) for pid, p in self.people.items()}
        self.by_pseudo = {v: k for k, v in self.pseudo.items()}
        self.ledger = {pid: {f: 0.0 for f in weights} for pid in self.people}  # federated state

    def vector_for(self, pseudo, candidate=None):
        pid = self.by_pseudo.get(pseudo)
        base = self.ledger[pid] if pid else {f: 0.0 for f in self.weights}
        if candidate:
            return {f: max(base[f], candidate[f]) for f in self.weights}
        return dict(base)

    def commit(self, pid, fields):
        for f in self.weights:
            self.ledger[pid][f] = max(self.ledger[pid][f], fields[f])
