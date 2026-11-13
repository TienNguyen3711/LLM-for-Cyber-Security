# Topic 3 benchmark results: `data/bench_s7.json`

300 people, 1245 events, strategies: S1 one-org one-account, S2 one-org sybil, S3 cross-org, S4 cross-org sybil slow; seed 7. Scoring errors are handled fail-closed.


## Scorer: `qwen/qwen3-4b` (1245 events scored)

Field detection (p >= 0.5): person linkage  97.8%, stage-1 exit  12.1%, **scoring errors 0**, latency mean 6.32 s, p95 13.60 s

| group | precision | recall | F1 | true fields |
|---|---|---|---|---|
| actor:attacker | 0.785 | 0.978 | 0.871 | 400 |
| actor:benign | 0.651 | 1.000 | 0.788 | 847 |
| all | 0.688 | 0.993 | 0.813 | 1247 |
| all excl. name | 0.906 | 1.000 | 0.950 | 796 |
| injection | 0.917 | 0.550 | 0.687 | 20 |
| name only | 0.480 | 0.980 | 0.644 | 451 |
| style:direct | 0.653 | 0.994 | 0.788 | 618 |
| style:inferable | 0.768 | 0.995 | 0.867 | 196 |
| style:none | nan | nan | nan | 0 |
| style:paraphrase | 0.708 | 0.991 | 0.826 | 433 |

### RQ1: which accounting unit stops assembly? (T = 0.75, no window, sticky)

Cell = prevented (attacker never got every targeted field) / mean share of the targeted record leaked. P1 probes are excluded here (see leakage.py).

| detector | S1 one-org one-account | S2 one-org sybil | S3 cross-org | S4 cross-org sybil slow | all | benign person FP | victim's own requests blocked |
|---|---|---|---|---|---|---|---|
| D0 per-request (limit 0.6) |   6.7% /  97.9% |   0.0% / 100.0% |   6.7% /  98.7% |   6.7% /  99.0% |   5.0% /  98.9% |   1.0% |   0.0% |
| D_session per-session |   0.0% / 100.0% |   0.0% / 100.0% |   0.0% / 100.0% |   0.0% / 100.0% |   0.0% / 100.0% |   0.0% |   0.0% |
| D1 per-account |  26.7% /  92.4% |   0.0% / 100.0% |  13.3% /  97.3% |   0.0% / 100.0% |  10.0% /  97.4% |   0.0% |   0.0% |
| D_traj per-account trajectory (30 d) |  26.7% /  92.4% |   0.0% / 100.0% |  13.3% /  97.3% |   0.0% / 100.0% |  10.0% /  97.4% |  95.9% |  81.0% |
| D2 per-org |  26.7% /  92.4% |  33.3% /  90.7% |  13.3% /  97.3% |  13.3% /  94.9% |  21.7% /  93.8% |   2.0% |   8.0% |
| D3 federated (or) |  26.7% /  92.4% |  46.7% /  85.8% | 100.0% /  61.2% | 100.0% /  53.8% |  68.3% /  73.3% |   8.7% |  49.4% |
| D3c centralised (or) |  26.7% /  92.4% |  46.7% /  85.8% | 100.0% /  61.2% | 100.0% /  53.8% |  68.3% /  73.3% |   8.7% |  49.4% |

### RQ1 (sweep): threshold, window and sticky step-up (all assembly strategies)

Cell = prevented / benign person FP.

| variant | T=0.4 | T=0.5 | T=0.6 | T=0.65 | T=0.7 | T=0.75 | T=0.8 | T=0.85 | T=0.9 | T=0.95 |
|---|---|---|---|---|---|---|---|---|---|---|
| D1 per-account |  76.7% /  19.9% |  58.3% /   7.1% |  31.7% /   2.6% |  25.0% /   2.6% |  10.0% /   0.0% |  10.0% /   0.0% |   0.0% /   0.0% |   0.0% /   0.0% |   0.0% /   0.0% |   0.0% /   0.0% |
| D2 per-org |  96.7% /  44.4% |  83.3% /  27.0% |  56.7% /  10.7% |  40.0% /   7.7% |  21.7% /   2.0% |  21.7% /   2.0% |   0.0% /   0.0% |   0.0% /   0.0% |   0.0% /   0.0% |   0.0% /   0.0% |
| D3 or |  96.7% /  55.6% |  95.0% /  42.3% |  90.0% /  26.5% |  78.3% /  19.4% |  68.3% /  11.2% |  68.3% /   8.7% |  51.7% /   2.0% |  43.3% /   2.0% |  40.0% /   1.5% |  36.7% /   0.0% |
| D3 or, 90-day window |  96.7% /  53.1% |  95.0% /  38.3% |  90.0% /  23.0% |  78.3% /  17.3% |  68.3% /  10.2% |  68.3% /   7.7% |  51.7% /   2.0% |  41.7% /   2.0% |  38.3% /   1.5% |  35.0% /   0.0% |
| D3 or, 30-day window |  96.7% /  41.8% |  95.0% /  30.6% |  81.7% /  16.8% |  68.3% /  13.3% |  55.0% /   7.7% |  51.7% /   6.1% |  33.3% /   2.0% |  28.3% /   2.0% |  26.7% /   1.5% |  20.0% /   0.0% |
| D3 or, not sticky |  96.7% /  55.1% |  95.0% /  41.3% |  90.0% /  25.5% |  78.3% /  18.9% |  68.3% /  10.2% |  68.3% /   7.7% |  50.0% /   2.0% |  43.3% /   2.0% |  40.0% /   1.5% |  36.7% /   0.0% |
| D0 per-request (limit = T) |  13.3% /   9.2% |   8.3% /   1.5% |   5.0% /   1.0% |   5.0% /   1.0% |   0.0% /   0.0% |   0.0% /   0.0% |   0.0% /   0.0% |   0.0% /   0.0% |   0.0% /   0.0% |   0.0% /   0.0% |

### RQ2: cross-organisation aggregation (union vs naive sum)

`or`/`max` count a field disclosed by two organisations once; `sum` adds the organisations' own scores, so it counts it twice. Cell = prevented / benign person FP.

| rule | T=0.6 | T=0.7 | T=0.75 | T=0.8 | T=0.9 | T=1.0 | T=1.2 |
|---|---|---|---|---|---|---|---|
| D3 or |  90.0% /  26.5% |  68.3% /  11.2% |  68.3% /   8.7% |  51.7% /   2.0% |  40.0% /   1.5% |  36.7% /   0.0% |   0.0% /   0.0% |
| D3 max |  90.0% /  26.5% |  68.3% /  11.2% |  68.3% /   8.7% |  51.7% /   2.0% |  40.0% /   1.5% |  36.7% /   0.0% |   0.0% /   0.0% |
| D3 sum |  93.3% /  42.3% |  75.0% /  28.1% |  75.0% /  26.0% |  61.7% /  18.9% |  58.3% /   8.7% |  56.7% /   6.1% |  40.0% /   2.6% |

Benign person FP by kind at T = 0.75:

| rule | life-event | quiet | typical |
|---|---|---|---|
| D3 or |  36.7% |   0.0% |   7.2% |
| D3 max |  36.7% |   0.0% |   7.2% |
| D3 sum |  83.3% |   2.4% |  28.9% |

## Scorer: `qwen/qwen3-4b+def-floor` (1245 events scored)

Field detection (p >= 0.5): person linkage  97.8%, stage-1 exit  12.1%, **scoring errors 0**, latency mean 6.32 s, p95 13.60 s

| group | precision | recall | F1 | true fields |
|---|---|---|---|---|
| actor:attacker | 0.789 | 1.000 | 0.882 | 400 |
| actor:benign | 0.651 | 1.000 | 0.788 | 847 |
| all | 0.689 | 1.000 | 0.816 | 1247 |
| all excl. name | 0.906 | 1.000 | 0.950 | 796 |
| injection | 0.952 | 1.000 | 0.976 | 20 |
| name only | 0.485 | 1.000 | 0.653 | 451 |
| style:direct | 0.655 | 1.000 | 0.791 | 618 |
| style:inferable | 0.769 | 1.000 | 0.869 | 196 |
| style:none | nan | nan | nan | 0 |
| style:paraphrase | 0.710 | 1.000 | 0.830 | 433 |

### RQ1: which accounting unit stops assembly? (T = 0.75, no window, sticky)

Cell = prevented (attacker never got every targeted field) / mean share of the targeted record leaked. P1 probes are excluded here (see leakage.py).

| detector | S1 one-org one-account | S2 one-org sybil | S3 cross-org | S4 cross-org sybil slow | all | benign person FP | victim's own requests blocked |
|---|---|---|---|---|---|---|---|
| D0 per-request (limit 0.6) |   6.7% /  97.9% |   0.0% / 100.0% |   6.7% /  98.7% |   6.7% /  99.0% |   5.0% /  98.9% |   1.0% |   0.0% |
| D_session per-session |   0.0% / 100.0% |   0.0% / 100.0% |   0.0% / 100.0% |   0.0% / 100.0% |   0.0% / 100.0% |   0.0% |   0.0% |
| D1 per-account |  26.7% /  92.4% |   0.0% / 100.0% |  13.3% /  97.3% |   0.0% / 100.0% |  10.0% /  97.4% |   0.0% |   0.0% |
| D_traj per-account trajectory (30 d) |  26.7% /  92.4% |   0.0% / 100.0% |  13.3% /  97.3% |   0.0% / 100.0% |  10.0% /  97.4% |  95.9% |  81.0% |
| D2 per-org |  26.7% /  92.4% |  33.3% /  90.7% |  13.3% /  97.3% |  13.3% /  94.9% |  21.7% /  93.8% |   2.0% |   8.0% |
| D3 federated (or) |  26.7% /  92.4% |  46.7% /  85.8% | 100.0% /  61.2% | 100.0% /  53.8% |  68.3% /  73.3% |   8.7% |  49.4% |
| D3c centralised (or) |  26.7% /  92.4% |  46.7% /  85.8% | 100.0% /  61.2% | 100.0% /  53.8% |  68.3% /  73.3% |   8.7% |  49.4% |

### RQ1 (sweep): threshold, window and sticky step-up (all assembly strategies)

Cell = prevented / benign person FP.

| variant | T=0.4 | T=0.5 | T=0.6 | T=0.65 | T=0.7 | T=0.75 | T=0.8 | T=0.85 | T=0.9 | T=0.95 |
|---|---|---|---|---|---|---|---|---|---|---|
| D1 per-account |  76.7% /  19.9% |  58.3% /   7.1% |  31.7% /   2.6% |  25.0% /   2.6% |  10.0% /   0.0% |  10.0% /   0.0% |   0.0% /   0.0% |   0.0% /   0.0% |   0.0% /   0.0% |   0.0% /   0.0% |
| D2 per-org |  96.7% /  44.4% |  83.3% /  27.0% |  56.7% /  10.7% |  40.0% /   7.7% |  21.7% /   2.0% |  21.7% /   2.0% |   0.0% /   0.0% |   0.0% /   0.0% |   0.0% /   0.0% |   0.0% /   0.0% |
| D3 or |  96.7% /  55.6% |  95.0% /  42.3% |  90.0% /  26.5% |  78.3% /  19.4% |  68.3% /  11.2% |  68.3% /   8.7% |  51.7% /   2.0% |  43.3% /   2.0% |  40.0% /   1.5% |  36.7% /   0.0% |
| D3 or, 90-day window |  96.7% /  53.1% |  95.0% /  38.3% |  90.0% /  23.0% |  78.3% /  17.3% |  68.3% /  10.2% |  68.3% /   7.7% |  51.7% /   2.0% |  41.7% /   2.0% |  38.3% /   1.5% |  35.0% /   0.0% |
| D3 or, 30-day window |  96.7% /  41.8% |  95.0% /  30.6% |  81.7% /  16.8% |  68.3% /  13.3% |  55.0% /   7.7% |  51.7% /   6.1% |  33.3% /   2.0% |  28.3% /   2.0% |  26.7% /   1.5% |  20.0% /   0.0% |
| D3 or, not sticky |  96.7% /  55.1% |  95.0% /  41.3% |  90.0% /  25.5% |  78.3% /  18.9% |  68.3% /  10.2% |  68.3% /   7.7% |  50.0% /   2.0% |  43.3% /   2.0% |  40.0% /   1.5% |  36.7% /   0.0% |
| D0 per-request (limit = T) |  13.3% /   9.2% |   8.3% /   1.5% |   5.0% /   1.0% |   5.0% /   1.0% |   0.0% /   0.0% |   0.0% /   0.0% |   0.0% /   0.0% |   0.0% /   0.0% |   0.0% /   0.0% |   0.0% /   0.0% |

### RQ2: cross-organisation aggregation (union vs naive sum)

`or`/`max` count a field disclosed by two organisations once; `sum` adds the organisations' own scores, so it counts it twice. Cell = prevented / benign person FP.

| rule | T=0.6 | T=0.7 | T=0.75 | T=0.8 | T=0.9 | T=1.0 | T=1.2 |
|---|---|---|---|---|---|---|---|
| D3 or |  90.0% /  26.5% |  68.3% /  11.2% |  68.3% /   8.7% |  51.7% /   2.0% |  40.0% /   1.5% |  36.7% /   0.0% |   0.0% /   0.0% |
| D3 max |  90.0% /  26.5% |  68.3% /  11.2% |  68.3% /   8.7% |  51.7% /   2.0% |  40.0% /   1.5% |  36.7% /   0.0% |   0.0% /   0.0% |
| D3 sum |  93.3% /  42.3% |  75.0% /  28.1% |  75.0% /  26.0% |  61.7% /  18.9% |  58.3% /   8.7% |  56.7% /   6.1% |  41.7% /   2.6% |

Benign person FP by kind at T = 0.75:

| rule | life-event | quiet | typical |
|---|---|---|---|
| D3 or |  36.7% |   0.0% |   7.2% |
| D3 max |  36.7% |   0.0% |   7.2% |
| D3 sum |  83.3% |   2.4% |  28.9% |

## Scorer: `qwen/qwen3-4b+def-name` (1245 events scored)

Field detection (p >= 0.5): person linkage  97.8%, stage-1 exit  12.1%, **scoring errors 0**, latency mean 6.32 s, p95 13.60 s

| group | precision | recall | F1 | true fields |
|---|---|---|---|---|
| actor:attacker | 0.952 | 1.000 | 0.976 | 400 |
| actor:benign | 0.931 | 1.000 | 0.964 | 847 |
| all | 0.938 | 1.000 | 0.968 | 1247 |
| all excl. name | 0.906 | 1.000 | 0.950 | 796 |
| injection | 0.952 | 1.000 | 0.976 | 20 |
| name only | 1.000 | 1.000 | 1.000 | 451 |
| style:direct | 0.935 | 1.000 | 0.966 | 618 |
| style:inferable | 0.942 | 1.000 | 0.970 | 196 |
| style:none | nan | nan | nan | 0 |
| style:paraphrase | 0.939 | 1.000 | 0.969 | 433 |

### RQ1: which accounting unit stops assembly? (T = 0.75, no window, sticky)

Cell = prevented (attacker never got every targeted field) / mean share of the targeted record leaked. P1 probes are excluded here (see leakage.py).

| detector | S1 one-org one-account | S2 one-org sybil | S3 cross-org | S4 cross-org sybil slow | all | benign person FP | victim's own requests blocked |
|---|---|---|---|---|---|---|---|
| D0 per-request (limit 0.6) |   6.7% /  97.9% |   0.0% / 100.0% |   6.7% /  98.7% |   6.7% /  99.0% |   5.0% /  98.9% |   0.0% |   0.0% |
| D_session per-session |   0.0% / 100.0% |   0.0% / 100.0% |   0.0% / 100.0% |   0.0% / 100.0% |   0.0% / 100.0% |   0.0% |   0.0% |
| D1 per-account |  26.7% /  92.4% |   0.0% / 100.0% |  13.3% /  97.3% |   0.0% / 100.0% |  10.0% /  97.4% |   0.0% |   0.0% |
| D_traj per-account trajectory (30 d) |  26.7% /  92.4% |   0.0% / 100.0% |  13.3% /  97.3% |   0.0% / 100.0% |  10.0% /  97.4% |  91.3% |  73.0% |
| D2 per-org |  26.7% /  92.4% |  33.3% /  90.7% |  13.3% /  97.3% |  13.3% /  94.9% |  21.7% /  93.8% |   2.0% |   7.5% |
| D3 federated (or) |  26.7% /  92.4% |  46.7% /  85.8% | 100.0% /  61.2% | 100.0% /  53.8% |  68.3% /  73.3% |   8.2% |  46.6% |
| D3c centralised (or) |  26.7% /  92.4% |  46.7% /  85.8% | 100.0% /  61.2% | 100.0% /  53.8% |  68.3% /  73.3% |   8.2% |  46.6% |

### RQ1 (sweep): threshold, window and sticky step-up (all assembly strategies)

Cell = prevented / benign person FP.

| variant | T=0.4 | T=0.5 | T=0.6 | T=0.65 | T=0.7 | T=0.75 | T=0.8 | T=0.85 | T=0.9 | T=0.95 |
|---|---|---|---|---|---|---|---|---|---|---|
| D1 per-account |  73.3% /   9.2% |  53.3% /   6.1% |  31.7% /   1.5% |  25.0% /   1.5% |  10.0% /   0.0% |  10.0% /   0.0% |   0.0% /   0.0% |   0.0% /   0.0% |   0.0% /   0.0% |   0.0% /   0.0% |
| D2 per-org |  95.0% /  35.7% |  78.3% /  23.5% |  55.0% /   9.7% |  38.3% /   6.6% |  21.7% /   2.0% |  21.7% /   2.0% |   0.0% /   0.0% |   0.0% /   0.0% |   0.0% /   0.0% |   0.0% /   0.0% |
| D3 or |  96.7% /  51.0% |  95.0% /  40.8% |  90.0% /  24.5% |  78.3% /  16.3% |  68.3% /   9.2% |  68.3% /   8.2% |  51.7% /   2.0% |  43.3% /   2.0% |  40.0% /   1.5% |  36.7% /   0.0% |
| D3 or, 90-day window |  96.7% /  48.0% |  95.0% /  36.2% |  90.0% /  21.4% |  78.3% /  14.8% |  68.3% /   8.2% |  68.3% /   7.1% |  51.7% /   2.0% |  41.7% /   2.0% |  38.3% /   1.5% |  33.3% /   0.0% |
| D3 or, 30-day window |  96.7% /  35.2% |  91.7% /  28.6% |  81.7% /  15.8% |  68.3% /  11.2% |  55.0% /   6.1% |  51.7% /   5.6% |  33.3% /   2.0% |  26.7% /   2.0% |  25.0% /   1.5% |  20.0% /   0.0% |
| D3 or, not sticky |  96.7% /  50.0% |  95.0% /  39.8% |  90.0% /  24.0% |  78.3% /  15.8% |  68.3% /   8.2% |  68.3% /   7.1% |  50.0% /   2.0% |  43.3% /   2.0% |  40.0% /   1.5% |  36.7% /   0.0% |
| D0 per-request (limit = T) |  10.0% /   1.5% |   6.7% /   1.0% |   5.0% /   0.0% |   5.0% /   0.0% |   0.0% /   0.0% |   0.0% /   0.0% |   0.0% /   0.0% |   0.0% /   0.0% |   0.0% /   0.0% |   0.0% /   0.0% |

### RQ2: cross-organisation aggregation (union vs naive sum)

`or`/`max` count a field disclosed by two organisations once; `sum` adds the organisations' own scores, so it counts it twice. Cell = prevented / benign person FP.

| rule | T=0.6 | T=0.7 | T=0.75 | T=0.8 | T=0.9 | T=1.0 | T=1.2 |
|---|---|---|---|---|---|---|---|
| D3 or |  90.0% /  24.5% |  68.3% /   9.2% |  68.3% /   8.2% |  51.7% /   2.0% |  40.0% /   1.5% |  36.7% /   0.0% |   0.0% /   0.0% |
| D3 max |  90.0% /  24.5% |  68.3% /   9.2% |  68.3% /   8.2% |  51.7% /   2.0% |  40.0% /   1.5% |  36.7% /   0.0% |   0.0% /   0.0% |
| D3 sum |  93.3% /  32.7% |  75.0% /  20.4% |  75.0% /  18.9% |  61.7% /  13.3% |  56.7% /   5.6% |  48.3% /   4.1% |  35.0% /   1.5% |

Benign person FP by kind at T = 0.75:

| rule | life-event | quiet | typical |
|---|---|---|---|
| D3 or |  33.3% |   0.0% |   7.2% |
| D3 max |  33.3% |   0.0% |   7.2% |
| D3 sum |  63.3% |   2.4% |  19.3% |

## Scorer: `qwen/qwen3-4b+def-floor-name` (1245 events scored)

Field detection (p >= 0.5): person linkage  97.8%, stage-1 exit  12.1%, **scoring errors 0**, latency mean 6.32 s, p95 13.60 s

| group | precision | recall | F1 | true fields |
|---|---|---|---|---|
| actor:attacker | 0.952 | 1.000 | 0.976 | 400 |
| actor:benign | 0.931 | 1.000 | 0.964 | 847 |
| all | 0.938 | 1.000 | 0.968 | 1247 |
| all excl. name | 0.906 | 1.000 | 0.950 | 796 |
| injection | 0.952 | 1.000 | 0.976 | 20 |
| name only | 1.000 | 1.000 | 1.000 | 451 |
| style:direct | 0.935 | 1.000 | 0.966 | 618 |
| style:inferable | 0.942 | 1.000 | 0.970 | 196 |
| style:none | nan | nan | nan | 0 |
| style:paraphrase | 0.939 | 1.000 | 0.969 | 433 |

### RQ1: which accounting unit stops assembly? (T = 0.75, no window, sticky)

Cell = prevented (attacker never got every targeted field) / mean share of the targeted record leaked. P1 probes are excluded here (see leakage.py).

| detector | S1 one-org one-account | S2 one-org sybil | S3 cross-org | S4 cross-org sybil slow | all | benign person FP | victim's own requests blocked |
|---|---|---|---|---|---|---|---|
| D0 per-request (limit 0.6) |   6.7% /  97.9% |   0.0% / 100.0% |   6.7% /  98.7% |   6.7% /  99.0% |   5.0% /  98.9% |   0.0% |   0.0% |
| D_session per-session |   0.0% / 100.0% |   0.0% / 100.0% |   0.0% / 100.0% |   0.0% / 100.0% |   0.0% / 100.0% |   0.0% |   0.0% |
| D1 per-account |  26.7% /  92.4% |   0.0% / 100.0% |  13.3% /  97.3% |   0.0% / 100.0% |  10.0% /  97.4% |   0.0% |   0.0% |
| D_traj per-account trajectory (30 d) |  26.7% /  92.4% |   0.0% / 100.0% |  13.3% /  97.3% |   0.0% / 100.0% |  10.0% /  97.4% |  91.3% |  73.0% |
| D2 per-org |  26.7% /  92.4% |  33.3% /  90.7% |  13.3% /  97.3% |  13.3% /  94.9% |  21.7% /  93.8% |   2.0% |   7.5% |
| D3 federated (or) |  26.7% /  92.4% |  46.7% /  85.8% | 100.0% /  61.2% | 100.0% /  53.8% |  68.3% /  73.3% |   8.2% |  46.6% |
| D3c centralised (or) |  26.7% /  92.4% |  46.7% /  85.8% | 100.0% /  61.2% | 100.0% /  53.8% |  68.3% /  73.3% |   8.2% |  46.6% |

### RQ1 (sweep): threshold, window and sticky step-up (all assembly strategies)

Cell = prevented / benign person FP.

| variant | T=0.4 | T=0.5 | T=0.6 | T=0.65 | T=0.7 | T=0.75 | T=0.8 | T=0.85 | T=0.9 | T=0.95 |
|---|---|---|---|---|---|---|---|---|---|---|
| D1 per-account |  73.3% /   9.2% |  53.3% /   6.1% |  31.7% /   1.5% |  25.0% /   1.5% |  10.0% /   0.0% |  10.0% /   0.0% |   0.0% /   0.0% |   0.0% /   0.0% |   0.0% /   0.0% |   0.0% /   0.0% |
| D2 per-org |  95.0% /  35.7% |  78.3% /  23.5% |  55.0% /   9.7% |  38.3% /   6.6% |  21.7% /   2.0% |  21.7% /   2.0% |   0.0% /   0.0% |   0.0% /   0.0% |   0.0% /   0.0% |   0.0% /   0.0% |
| D3 or |  96.7% /  51.0% |  95.0% /  40.8% |  90.0% /  24.5% |  78.3% /  16.3% |  68.3% /   9.2% |  68.3% /   8.2% |  51.7% /   2.0% |  43.3% /   2.0% |  40.0% /   1.5% |  36.7% /   0.0% |
| D3 or, 90-day window |  96.7% /  48.0% |  95.0% /  36.2% |  90.0% /  21.4% |  78.3% /  14.8% |  68.3% /   8.2% |  68.3% /   7.1% |  51.7% /   2.0% |  41.7% /   2.0% |  38.3% /   1.5% |  33.3% /   0.0% |
| D3 or, 30-day window |  96.7% /  35.2% |  91.7% /  28.6% |  81.7% /  15.8% |  68.3% /  11.2% |  55.0% /   6.1% |  51.7% /   5.6% |  33.3% /   2.0% |  26.7% /   2.0% |  25.0% /   1.5% |  20.0% /   0.0% |
| D3 or, not sticky |  96.7% /  50.0% |  95.0% /  39.8% |  90.0% /  24.0% |  78.3% /  15.8% |  68.3% /   8.2% |  68.3% /   7.1% |  50.0% /   2.0% |  43.3% /   2.0% |  40.0% /   1.5% |  36.7% /   0.0% |
| D0 per-request (limit = T) |  10.0% /   1.5% |   6.7% /   1.0% |   5.0% /   0.0% |   5.0% /   0.0% |   0.0% /   0.0% |   0.0% /   0.0% |   0.0% /   0.0% |   0.0% /   0.0% |   0.0% /   0.0% |   0.0% /   0.0% |

### RQ2: cross-organisation aggregation (union vs naive sum)

`or`/`max` count a field disclosed by two organisations once; `sum` adds the organisations' own scores, so it counts it twice. Cell = prevented / benign person FP.

| rule | T=0.6 | T=0.7 | T=0.75 | T=0.8 | T=0.9 | T=1.0 | T=1.2 |
|---|---|---|---|---|---|---|---|
| D3 or |  90.0% /  24.5% |  68.3% /   9.2% |  68.3% /   8.2% |  51.7% /   2.0% |  40.0% /   1.5% |  36.7% /   0.0% |   0.0% /   0.0% |
| D3 max |  90.0% /  24.5% |  68.3% /   9.2% |  68.3% /   8.2% |  51.7% /   2.0% |  40.0% /   1.5% |  36.7% /   0.0% |   0.0% /   0.0% |
| D3 sum |  93.3% /  32.7% |  75.0% /  20.4% |  75.0% /  18.9% |  61.7% /  13.3% |  56.7% /   5.6% |  48.3% /   4.1% |  35.0% /   1.5% |

Benign person FP by kind at T = 0.75:

| rule | life-event | quiet | typical |
|---|---|---|---|
| D3 or |  33.3% |   0.0% |   7.2% |
| D3 max |  33.3% |   0.0% |   7.2% |
| D3 sum |  63.3% |   2.4% |  19.3% |

## Scorer: `qwen/qwen3-32b` (1245 events scored)

Field detection (p >= 0.5): person linkage  97.5%, stage-1 exit  12.1%, **scoring errors 0**, latency mean 16.52 s, p95 25.20 s

| group | precision | recall | F1 | true fields |
|---|---|---|---|---|
| actor:attacker | 0.946 | 0.955 | 0.950 | 400 |
| actor:benign | 0.826 | 0.999 | 0.904 | 847 |
| all | 0.860 | 0.985 | 0.918 | 1247 |
| all excl. name | 0.992 | 0.994 | 0.993 | 796 |
| injection | 1.000 | 0.250 | 0.400 | 20 |
| name only | 0.693 | 0.969 | 0.808 | 451 |
| style:direct | 0.804 | 0.987 | 0.886 | 618 |
| style:inferable | 0.941 | 0.980 | 0.960 | 196 |
| style:none | nan | nan | nan | 0 |
| style:paraphrase | 0.916 | 0.984 | 0.949 | 433 |

### RQ1: which accounting unit stops assembly? (T = 0.75, no window, sticky)

Cell = prevented (attacker never got every targeted field) / mean share of the targeted record leaked. P1 probes are excluded here (see leakage.py).

| detector | S1 one-org one-account | S2 one-org sybil | S3 cross-org | S4 cross-org sybil slow | all | benign person FP | victim's own requests blocked |
|---|---|---|---|---|---|---|---|
| D0 per-request (limit 0.6) |   0.0% / 100.0% |   0.0% / 100.0% |   0.0% / 100.0% |   0.0% / 100.0% |   0.0% / 100.0% |   0.5% |   0.0% |
| D_session per-session |   0.0% / 100.0% |   0.0% / 100.0% |   0.0% / 100.0% |   0.0% / 100.0% |   0.0% / 100.0% |   0.0% |   0.0% |
| D1 per-account |  26.7% /  92.4% |   0.0% / 100.0% |  13.3% /  97.3% |   0.0% / 100.0% |  10.0% /  97.4% |   0.0% |   0.0% |
| D_traj per-account trajectory (30 d) |  26.7% /  92.4% |   0.0% / 100.0% |  13.3% /  97.3% |   0.0% / 100.0% |  10.0% /  97.4% |  89.3% |  71.8% |
| D2 per-org |  26.7% /  92.4% |  40.0% /  88.9% |  13.3% /  97.3% |   6.7% /  96.5% |  21.7% /  93.8% |   2.0% |   8.0% |
| D3 federated (or) |  26.7% /  92.4% |  46.7% /  86.2% |  93.3% /  63.9% | 100.0% /  61.7% |  66.7% /  76.1% |   5.1% |  46.0% |
| D3c centralised (or) |  26.7% /  92.4% |  46.7% /  86.2% |  93.3% /  63.9% | 100.0% /  61.7% |  66.7% /  76.1% |   5.1% |  46.0% |

### RQ1 (sweep): threshold, window and sticky step-up (all assembly strategies)

Cell = prevented / benign person FP.

| variant | T=0.4 | T=0.5 | T=0.6 | T=0.65 | T=0.7 | T=0.75 | T=0.8 | T=0.85 | T=0.9 | T=0.95 |
|---|---|---|---|---|---|---|---|---|---|---|
| D1 per-account |  71.7% /  10.7% |  53.3% /   4.1% |  30.0% /   1.0% |  21.7% /   1.0% |  10.0% /   0.0% |  10.0% /   0.0% |   0.0% /   0.0% |   0.0% /   0.0% |   0.0% /   0.0% |   0.0% /   0.0% |
| D2 per-org |  95.0% /  35.2% |  75.0% /  19.9% |  51.7% /   6.6% |  36.7% /   4.1% |  21.7% /   2.0% |  21.7% /   2.0% |   0.0% /   0.0% |   0.0% /   0.0% |   0.0% /   0.0% |   0.0% /   0.0% |
| D3 or |  96.7% /  51.0% |  93.3% /  34.2% |  88.3% /  19.9% |  75.0% /  13.8% |  66.7% /   6.6% |  66.7% /   5.1% |  46.7% /   1.5% |  38.3% /   1.5% |  36.7% /   1.0% |  33.3% /   0.0% |
| D3 or, 90-day window |  96.7% /  48.5% |  93.3% /  31.1% |  88.3% /  17.3% |  75.0% /  12.2% |  66.7% /   6.1% |  66.7% /   4.6% |  46.7% /   1.5% |  35.0% /   1.5% |  33.3% /   1.0% |  31.7% /   0.0% |
| D3 or, 30-day window |  96.7% /  32.7% |  90.0% /  23.0% |  78.3% /  13.8% |  60.0% /  10.2% |  48.3% /   5.1% |  46.7% /   3.6% |  28.3% /   1.0% |  23.3% /   1.0% |  21.7% /   0.5% |  18.3% /   0.0% |
| D3 or, not sticky |  96.7% /  51.0% |  93.3% /  34.2% |  88.3% /  19.9% |  75.0% /  13.8% |  66.7% /   6.6% |  66.7% /   5.1% |  46.7% /   1.5% |  38.3% /   1.5% |  36.7% /   1.0% |  33.3% /   0.0% |
| D0 per-request (limit = T) |   0.0% /   0.5% |   0.0% /   0.5% |   0.0% /   0.5% |   0.0% /   0.5% |   0.0% /   0.0% |   0.0% /   0.0% |   0.0% /   0.0% |   0.0% /   0.0% |   0.0% /   0.0% |   0.0% /   0.0% |

### RQ2: cross-organisation aggregation (union vs naive sum)

`or`/`max` count a field disclosed by two organisations once; `sum` adds the organisations' own scores, so it counts it twice. Cell = prevented / benign person FP.

| rule | T=0.6 | T=0.7 | T=0.75 | T=0.8 | T=0.9 | T=1.0 | T=1.2 |
|---|---|---|---|---|---|---|---|
| D3 or |  88.3% /  19.9% |  66.7% /   6.6% |  66.7% /   5.1% |  46.7% /   1.5% |  36.7% /   1.0% |  33.3% /   0.0% |   0.0% /   0.0% |
| D3 max |  88.3% /  19.9% |  66.7% /   6.6% |  66.7% /   5.1% |  46.7% /   1.5% |  36.7% /   1.0% |  33.3% /   0.0% |   0.0% /   0.0% |
| D3 sum |  90.0% /  32.1% |  73.3% /  19.4% |  71.7% /  17.3% |  61.7% /  12.2% |  53.3% /   5.6% |  50.0% /   3.6% |  28.3% /   0.5% |

Benign person FP by kind at T = 0.75:

| rule | life-event | quiet | typical |
|---|---|---|---|
| D3 or |  23.3% |   0.0% |   3.6% |
| D3 max |  23.3% |   0.0% |   3.6% |
| D3 sum |  70.0% |   0.0% |  15.7% |

## Scorer: `qwen/qwen3-32b+def-floor` (1245 events scored)

Field detection (p >= 0.5): person linkage  98.6%, stage-1 exit  12.1%, **scoring errors 0**, latency mean 16.52 s, p95 25.20 s

| group | precision | recall | F1 | true fields |
|---|---|---|---|---|
| actor:attacker | 0.948 | 0.998 | 0.972 | 400 |
| actor:benign | 0.826 | 1.000 | 0.905 | 847 |
| all | 0.862 | 0.999 | 0.925 | 1247 |
| all excl. name | 0.993 | 0.999 | 0.996 | 796 |
| injection | 1.000 | 0.950 | 0.974 | 20 |
| name only | 0.699 | 1.000 | 0.823 | 451 |
| style:direct | 0.806 | 1.000 | 0.892 | 618 |
| style:inferable | 0.942 | 0.995 | 0.968 | 196 |
| style:none | nan | nan | nan | 0 |
| style:paraphrase | 0.917 | 1.000 | 0.957 | 433 |

### RQ1: which accounting unit stops assembly? (T = 0.75, no window, sticky)

Cell = prevented (attacker never got every targeted field) / mean share of the targeted record leaked. P1 probes are excluded here (see leakage.py).

| detector | S1 one-org one-account | S2 one-org sybil | S3 cross-org | S4 cross-org sybil slow | all | benign person FP | victim's own requests blocked |
|---|---|---|---|---|---|---|---|
| D0 per-request (limit 0.6) |   0.0% / 100.0% |   0.0% / 100.0% |   0.0% / 100.0% |   0.0% / 100.0% |   0.0% / 100.0% |   0.5% |   0.0% |
| D_session per-session |   0.0% / 100.0% |   0.0% / 100.0% |   0.0% / 100.0% |   0.0% / 100.0% |   0.0% / 100.0% |   0.0% |   0.0% |
| D1 per-account |  26.7% /  92.4% |   0.0% / 100.0% |  13.3% /  97.3% |   0.0% / 100.0% |  10.0% /  97.4% |   0.0% |   0.0% |
| D_traj per-account trajectory (30 d) |  26.7% /  92.4% |   0.0% / 100.0% |  13.3% /  97.3% |   0.0% / 100.0% |  10.0% /  97.4% |  89.3% |  71.8% |
| D2 per-org |  26.7% /  92.4% |  40.0% /  88.9% |  13.3% /  97.3% |   6.7% /  96.5% |  21.7% /  93.8% |   2.0% |   8.0% |
| D3 federated (or) |  26.7% /  92.4% |  46.7% /  86.2% | 100.0% /  62.2% | 100.0% /  57.8% |  68.3% /  74.7% |   5.1% |  46.0% |
| D3c centralised (or) |  26.7% /  92.4% |  46.7% /  86.2% | 100.0% /  62.2% | 100.0% /  57.8% |  68.3% /  74.7% |   5.1% |  46.0% |

### RQ1 (sweep): threshold, window and sticky step-up (all assembly strategies)

Cell = prevented / benign person FP.

| variant | T=0.4 | T=0.5 | T=0.6 | T=0.65 | T=0.7 | T=0.75 | T=0.8 | T=0.85 | T=0.9 | T=0.95 |
|---|---|---|---|---|---|---|---|---|---|---|
| D1 per-account |  73.3% /  10.7% |  53.3% /   4.1% |  31.7% /   1.0% |  23.3% /   1.0% |  10.0% /   0.0% |  10.0% /   0.0% |   0.0% /   0.0% |   0.0% /   0.0% |   0.0% /   0.0% |   0.0% /   0.0% |
| D2 per-org |  96.7% /  35.2% |  76.7% /  19.9% |  53.3% /   6.6% |  38.3% /   4.1% |  21.7% /   2.0% |  21.7% /   2.0% |   0.0% /   0.0% |   0.0% /   0.0% |   0.0% /   0.0% |   0.0% /   0.0% |
| D3 or |  96.7% /  51.0% |  93.3% /  34.2% |  90.0% /  19.9% |  78.3% /  13.8% |  68.3% /   6.6% |  68.3% /   5.1% |  50.0% /   1.5% |  40.0% /   1.5% |  38.3% /   1.0% |  36.7% /   0.0% |
| D3 or, 90-day window |  96.7% /  48.5% |  93.3% /  31.1% |  90.0% /  17.3% |  78.3% /  12.2% |  68.3% /   6.1% |  68.3% /   4.6% |  50.0% /   1.5% |  38.3% /   1.5% |  36.7% /   1.0% |  33.3% /   0.0% |
| D3 or, 30-day window |  96.7% /  32.7% |  90.0% /  23.0% |  80.0% /  13.8% |  63.3% /  10.2% |  51.7% /   5.1% |  50.0% /   3.6% |  30.0% /   1.0% |  23.3% /   1.0% |  21.7% /   0.5% |  18.3% /   0.0% |
| D3 or, not sticky |  96.7% /  51.0% |  93.3% /  34.2% |  90.0% /  19.9% |  78.3% /  13.8% |  68.3% /   6.6% |  68.3% /   5.1% |  50.0% /   1.5% |  40.0% /   1.5% |  38.3% /   1.0% |  36.7% /   0.0% |
| D0 per-request (limit = T) |   0.0% /   0.5% |   0.0% /   0.5% |   0.0% /   0.5% |   0.0% /   0.5% |   0.0% /   0.0% |   0.0% /   0.0% |   0.0% /   0.0% |   0.0% /   0.0% |   0.0% /   0.0% |   0.0% /   0.0% |

### RQ2: cross-organisation aggregation (union vs naive sum)

`or`/`max` count a field disclosed by two organisations once; `sum` adds the organisations' own scores, so it counts it twice. Cell = prevented / benign person FP.

| rule | T=0.6 | T=0.7 | T=0.75 | T=0.8 | T=0.9 | T=1.0 | T=1.2 |
|---|---|---|---|---|---|---|---|
| D3 or |  90.0% /  19.9% |  68.3% /   6.6% |  68.3% /   5.1% |  50.0% /   1.5% |  38.3% /   1.0% |  36.7% /   0.0% |   0.0% /   0.0% |
| D3 max |  90.0% /  19.9% |  68.3% /   6.6% |  68.3% /   5.1% |  50.0% /   1.5% |  38.3% /   1.0% |  36.7% /   0.0% |   0.0% /   0.0% |
| D3 sum |  91.7% /  32.1% |  73.3% /  19.4% |  73.3% /  17.3% |  63.3% /  12.2% |  55.0% /   5.6% |  50.0% /   3.6% |  35.0% /   0.5% |

Benign person FP by kind at T = 0.75:

| rule | life-event | quiet | typical |
|---|---|---|---|
| D3 or |  23.3% |   0.0% |   3.6% |
| D3 max |  23.3% |   0.0% |   3.6% |
| D3 sum |  70.0% |   0.0% |  15.7% |

## Scorer: `qwen/qwen3-32b+def-name` (1245 events scored)

Field detection (p >= 0.5): person linkage  97.5%, stage-1 exit  12.1%, **scoring errors 0**, latency mean 16.52 s, p95 25.20 s

| group | precision | recall | F1 | true fields |
|---|---|---|---|---|
| actor:attacker | 1.000 | 0.963 | 0.981 | 400 |
| actor:benign | 0.993 | 1.000 | 0.996 | 847 |
| all | 0.995 | 0.988 | 0.992 | 1247 |
| all excl. name | 0.992 | 0.994 | 0.993 | 796 |
| injection | 1.000 | 0.250 | 0.400 | 20 |
| name only | 1.000 | 0.978 | 0.989 | 451 |
| style:direct | 0.994 | 0.992 | 0.993 | 618 |
| style:inferable | 0.995 | 0.980 | 0.987 | 196 |
| style:none | nan | nan | nan | 0 |
| style:paraphrase | 0.998 | 0.986 | 0.992 | 433 |

### RQ1: which accounting unit stops assembly? (T = 0.75, no window, sticky)

Cell = prevented (attacker never got every targeted field) / mean share of the targeted record leaked. P1 probes are excluded here (see leakage.py).

| detector | S1 one-org one-account | S2 one-org sybil | S3 cross-org | S4 cross-org sybil slow | all | benign person FP | victim's own requests blocked |
|---|---|---|---|---|---|---|---|
| D0 per-request (limit 0.6) |   0.0% / 100.0% |   0.0% / 100.0% |   0.0% / 100.0% |   0.0% / 100.0% |   0.0% / 100.0% |   0.0% |   0.0% |
| D_session per-session |   0.0% / 100.0% |   0.0% / 100.0% |   0.0% / 100.0% |   0.0% / 100.0% |   0.0% / 100.0% |   0.0% |   0.0% |
| D1 per-account |  26.7% /  92.4% |   0.0% / 100.0% |  13.3% /  97.3% |   0.0% / 100.0% |  10.0% /  97.4% |   0.0% |   0.0% |
| D_traj per-account trajectory (30 d) |  26.7% /  92.4% |   0.0% / 100.0% |  13.3% /  97.3% |   0.0% / 100.0% |  10.0% /  97.4% |  88.3% |  70.1% |
| D2 per-org |  26.7% /  92.4% |  40.0% /  88.9% |  13.3% /  97.3% |   6.7% /  96.5% |  21.7% /  93.8% |   2.0% |   8.0% |
| D3 federated (or) |  26.7% /  92.4% |  46.7% /  86.2% |  93.3% /  63.9% | 100.0% /  61.7% |  66.7% /  76.1% |   5.1% |  46.0% |
| D3c centralised (or) |  26.7% /  92.4% |  46.7% /  86.2% |  93.3% /  63.9% | 100.0% /  61.7% |  66.7% /  76.1% |   5.1% |  46.0% |

### RQ1 (sweep): threshold, window and sticky step-up (all assembly strategies)

Cell = prevented / benign person FP.

| variant | T=0.4 | T=0.5 | T=0.6 | T=0.65 | T=0.7 | T=0.75 | T=0.8 | T=0.85 | T=0.9 | T=0.95 |
|---|---|---|---|---|---|---|---|---|---|---|
| D1 per-account |  70.0% /   7.1% |  51.7% /   3.6% |  30.0% /   0.5% |  21.7% /   0.5% |  10.0% /   0.0% |  10.0% /   0.0% |   0.0% /   0.0% |   0.0% /   0.0% |   0.0% /   0.0% |   0.0% /   0.0% |
| D2 per-org |  93.3% /  31.1% |  75.0% /  18.4% |  50.0% /   6.1% |  35.0% /   3.6% |  21.7% /   2.0% |  21.7% /   2.0% |   0.0% /   0.0% |   0.0% /   0.0% |   0.0% /   0.0% |   0.0% /   0.0% |
| D3 or |  96.7% /  46.9% |  93.3% /  33.2% |  88.3% /  18.9% |  75.0% /  12.2% |  66.7% /   6.1% |  66.7% /   5.1% |  46.7% /   1.5% |  38.3% /   1.5% |  36.7% /   1.0% |  33.3% /   0.0% |
| D3 or, 90-day window |  96.7% /  44.4% |  93.3% /  29.6% |  88.3% /  16.8% |  75.0% /  11.2% |  66.7% /   5.6% |  66.7% /   4.6% |  46.7% /   1.5% |  35.0% /   1.5% |  33.3% /   1.0% |  31.7% /   0.0% |
| D3 or, 30-day window |  96.7% /  29.1% |  90.0% /  21.9% |  78.3% /  13.3% |  60.0% /   9.7% |  50.0% /   5.1% |  48.3% /   3.6% |  28.3% /   1.0% |  21.7% /   1.0% |  20.0% /   0.5% |  18.3% /   0.0% |
| D3 or, not sticky |  96.7% /  46.9% |  93.3% /  33.2% |  88.3% /  18.9% |  75.0% /  12.2% |  66.7% /   6.1% |  66.7% /   5.1% |  46.7% /   1.5% |  38.3% /   1.5% |  36.7% /   1.0% |  33.3% /   0.0% |
| D0 per-request (limit = T) |   0.0% /   0.5% |   0.0% /   0.5% |   0.0% /   0.0% |   0.0% /   0.0% |   0.0% /   0.0% |   0.0% /   0.0% |   0.0% /   0.0% |   0.0% /   0.0% |   0.0% /   0.0% |   0.0% /   0.0% |

### RQ2: cross-organisation aggregation (union vs naive sum)

`or`/`max` count a field disclosed by two organisations once; `sum` adds the organisations' own scores, so it counts it twice. Cell = prevented / benign person FP.

| rule | T=0.6 | T=0.7 | T=0.75 | T=0.8 | T=0.9 | T=1.0 | T=1.2 |
|---|---|---|---|---|---|---|---|
| D3 or |  88.3% /  18.9% |  66.7% /   6.1% |  66.7% /   5.1% |  46.7% /   1.5% |  36.7% /   1.0% |  33.3% /   0.0% |   0.0% /   0.0% |
| D3 max |  88.3% /  18.9% |  66.7% /   6.1% |  66.7% /   5.1% |  46.7% /   1.5% |  36.7% /   1.0% |  33.3% /   0.0% |   0.0% /   0.0% |
| D3 sum |  90.0% /  27.0% |  73.3% /  15.3% |  71.7% /  13.8% |  58.3% /  10.2% |  53.3% /   4.1% |  45.0% /   2.6% |  28.3% /   0.5% |

Benign person FP by kind at T = 0.75:

| rule | life-event | quiet | typical |
|---|---|---|---|
| D3 or |  23.3% |   0.0% |   3.6% |
| D3 max |  23.3% |   0.0% |   3.6% |
| D3 sum |  60.0% |   0.0% |  10.8% |

## Scorer: `qwen/qwen3-32b+def-floor-name` (1245 events scored)

Field detection (p >= 0.5): person linkage  98.6%, stage-1 exit  12.1%, **scoring errors 0**, latency mean 16.52 s, p95 25.20 s

| group | precision | recall | F1 | true fields |
|---|---|---|---|---|
| actor:attacker | 1.000 | 0.998 | 0.999 | 400 |
| actor:benign | 0.993 | 1.000 | 0.996 | 847 |
| all | 0.995 | 0.999 | 0.997 | 1247 |
| all excl. name | 0.993 | 0.999 | 0.996 | 796 |
| injection | 1.000 | 0.950 | 0.974 | 20 |
| name only | 1.000 | 1.000 | 1.000 | 451 |
| style:direct | 0.994 | 1.000 | 0.997 | 618 |
| style:inferable | 0.995 | 0.995 | 0.995 | 196 |
| style:none | nan | nan | nan | 0 |
| style:paraphrase | 0.998 | 1.000 | 0.999 | 433 |

### RQ1: which accounting unit stops assembly? (T = 0.75, no window, sticky)

Cell = prevented (attacker never got every targeted field) / mean share of the targeted record leaked. P1 probes are excluded here (see leakage.py).

| detector | S1 one-org one-account | S2 one-org sybil | S3 cross-org | S4 cross-org sybil slow | all | benign person FP | victim's own requests blocked |
|---|---|---|---|---|---|---|---|
| D0 per-request (limit 0.6) |   0.0% / 100.0% |   0.0% / 100.0% |   0.0% / 100.0% |   0.0% / 100.0% |   0.0% / 100.0% |   0.0% |   0.0% |
| D_session per-session |   0.0% / 100.0% |   0.0% / 100.0% |   0.0% / 100.0% |   0.0% / 100.0% |   0.0% / 100.0% |   0.0% |   0.0% |
| D1 per-account |  26.7% /  92.4% |   0.0% / 100.0% |  13.3% /  97.3% |   0.0% / 100.0% |  10.0% /  97.4% |   0.0% |   0.0% |
| D_traj per-account trajectory (30 d) |  26.7% /  92.4% |   0.0% / 100.0% |  13.3% /  97.3% |   0.0% / 100.0% |  10.0% /  97.4% |  88.3% |  70.1% |
| D2 per-org |  26.7% /  92.4% |  40.0% /  88.9% |  13.3% /  97.3% |   6.7% /  96.5% |  21.7% /  93.8% |   2.0% |   8.0% |
| D3 federated (or) |  26.7% /  92.4% |  46.7% /  86.2% | 100.0% /  62.2% | 100.0% /  57.8% |  68.3% /  74.7% |   5.1% |  46.0% |
| D3c centralised (or) |  26.7% /  92.4% |  46.7% /  86.2% | 100.0% /  62.2% | 100.0% /  57.8% |  68.3% /  74.7% |   5.1% |  46.0% |

### RQ1 (sweep): threshold, window and sticky step-up (all assembly strategies)

Cell = prevented / benign person FP.

| variant | T=0.4 | T=0.5 | T=0.6 | T=0.65 | T=0.7 | T=0.75 | T=0.8 | T=0.85 | T=0.9 | T=0.95 |
|---|---|---|---|---|---|---|---|---|---|---|
| D1 per-account |  71.7% /   7.1% |  51.7% /   3.6% |  31.7% /   0.5% |  23.3% /   0.5% |  10.0% /   0.0% |  10.0% /   0.0% |   0.0% /   0.0% |   0.0% /   0.0% |   0.0% /   0.0% |   0.0% /   0.0% |
| D2 per-org |  95.0% /  31.1% |  76.7% /  18.4% |  51.7% /   6.1% |  36.7% /   3.6% |  21.7% /   2.0% |  21.7% /   2.0% |   0.0% /   0.0% |   0.0% /   0.0% |   0.0% /   0.0% |   0.0% /   0.0% |
| D3 or |  96.7% /  46.9% |  93.3% /  33.2% |  90.0% /  18.9% |  78.3% /  12.2% |  68.3% /   6.1% |  68.3% /   5.1% |  50.0% /   1.5% |  40.0% /   1.5% |  38.3% /   1.0% |  36.7% /   0.0% |
| D3 or, 90-day window |  96.7% /  44.4% |  93.3% /  29.6% |  90.0% /  16.8% |  78.3% /  11.2% |  68.3% /   5.6% |  68.3% /   4.6% |  50.0% /   1.5% |  38.3% /   1.5% |  36.7% /   1.0% |  33.3% /   0.0% |
| D3 or, 30-day window |  96.7% /  29.1% |  90.0% /  21.9% |  80.0% /  13.3% |  63.3% /   9.7% |  51.7% /   5.1% |  50.0% /   3.6% |  30.0% /   1.0% |  21.7% /   1.0% |  20.0% /   0.5% |  18.3% /   0.0% |
| D3 or, not sticky |  96.7% /  46.9% |  93.3% /  33.2% |  90.0% /  18.9% |  78.3% /  12.2% |  68.3% /   6.1% |  68.3% /   5.1% |  50.0% /   1.5% |  40.0% /   1.5% |  38.3% /   1.0% |  36.7% /   0.0% |
| D0 per-request (limit = T) |   0.0% /   0.5% |   0.0% /   0.5% |   0.0% /   0.0% |   0.0% /   0.0% |   0.0% /   0.0% |   0.0% /   0.0% |   0.0% /   0.0% |   0.0% /   0.0% |   0.0% /   0.0% |   0.0% /   0.0% |

### RQ2: cross-organisation aggregation (union vs naive sum)

`or`/`max` count a field disclosed by two organisations once; `sum` adds the organisations' own scores, so it counts it twice. Cell = prevented / benign person FP.

| rule | T=0.6 | T=0.7 | T=0.75 | T=0.8 | T=0.9 | T=1.0 | T=1.2 |
|---|---|---|---|---|---|---|---|
| D3 or |  90.0% /  18.9% |  68.3% /   6.1% |  68.3% /   5.1% |  50.0% /   1.5% |  38.3% /   1.0% |  36.7% /   0.0% |   0.0% /   0.0% |
| D3 max |  90.0% /  18.9% |  68.3% /   6.1% |  68.3% /   5.1% |  50.0% /   1.5% |  38.3% /   1.0% |  36.7% /   0.0% |   0.0% /   0.0% |
| D3 sum |  91.7% /  27.0% |  73.3% /  15.3% |  73.3% /  13.8% |  60.0% /  10.2% |  55.0% /   4.1% |  46.7% /   2.6% |  33.3% /   0.5% |

Benign person FP by kind at T = 0.75:

| rule | life-event | quiet | typical |
|---|---|---|---|
| D3 or |  23.3% |   0.0% |   3.6% |
| D3 max |  23.3% |   0.0% |   3.6% |
| D3 sum |  60.0% |   0.0% |  10.8% |

## Scorer: `qwen/qwen3-32b+dual-qwen/qwen3-4b` (1245 events scored)

Field detection (p >= 0.5): person linkage  98.6%, stage-1 exit   0.0%, **scoring errors 0**, latency mean 22.84 s, p95 32.21 s

| group | precision | recall | F1 | true fields |
|---|---|---|---|---|
| actor:attacker | 0.784 | 0.980 | 0.871 | 400 |
| actor:benign | 0.639 | 1.000 | 0.780 | 847 |
| all | 0.679 | 0.994 | 0.806 | 1247 |
| all excl. name | 0.905 | 1.000 | 0.950 | 796 |
| injection | 0.923 | 0.600 | 0.727 | 20 |
| name only | 0.468 | 0.982 | 0.634 | 451 |
| style:direct | 0.642 | 0.994 | 0.780 | 618 |
| style:inferable | 0.756 | 0.995 | 0.859 | 196 |
| style:none | nan | nan | nan | 0 |
| style:paraphrase | 0.703 | 0.993 | 0.823 | 433 |

### RQ1: which accounting unit stops assembly? (T = 0.75, no window, sticky)

Cell = prevented (attacker never got every targeted field) / mean share of the targeted record leaked. P1 probes are excluded here (see leakage.py).

| detector | S1 one-org one-account | S2 one-org sybil | S3 cross-org | S4 cross-org sybil slow | all | benign person FP | victim's own requests blocked |
|---|---|---|---|---|---|---|---|
| D0 per-request (limit 0.6) |   6.7% /  97.9% |   0.0% / 100.0% |   6.7% /  98.7% |   6.7% /  99.0% |   5.0% /  98.9% |   1.5% |   0.0% |
| D_session per-session |   0.0% / 100.0% |   0.0% / 100.0% |   0.0% / 100.0% |   0.0% / 100.0% |   0.0% / 100.0% |   0.0% |   0.0% |
| D1 per-account |  26.7% /  92.4% |   0.0% / 100.0% |  13.3% /  97.3% |   0.0% / 100.0% |  10.0% /  97.4% |   0.0% |   0.0% |
| D_traj per-account trajectory (30 d) |  26.7% /  92.4% |   0.0% / 100.0% |  13.3% /  97.3% |   0.0% / 100.0% |  10.0% /  97.4% |  95.9% |  81.0% |
| D2 per-org |  26.7% /  92.4% |  40.0% /  88.9% |  13.3% /  97.3% |  13.3% /  94.9% |  23.3% /  93.4% |   2.0% |   8.6% |
| D3 federated (or) |  26.7% /  92.4% |  53.3% /  84.0% | 100.0% /  60.6% | 100.0% /  53.1% |  70.0% /  72.5% |   8.7% |  51.7% |
| D3c centralised (or) |  26.7% /  92.4% |  53.3% /  84.0% | 100.0% /  60.6% | 100.0% /  53.1% |  70.0% /  72.5% |   8.7% |  51.7% |

### RQ1 (sweep): threshold, window and sticky step-up (all assembly strategies)

Cell = prevented / benign person FP.

| variant | T=0.4 | T=0.5 | T=0.6 | T=0.65 | T=0.7 | T=0.75 | T=0.8 | T=0.85 | T=0.9 | T=0.95 |
|---|---|---|---|---|---|---|---|---|---|---|
| D1 per-account |  78.3% /  20.4% |  60.0% /   7.7% |  33.3% /   3.1% |  25.0% /   3.1% |  10.0% /   0.0% |  10.0% /   0.0% |   0.0% /   0.0% |   0.0% /   0.0% |   0.0% /   0.0% |   0.0% /   0.0% |
| D2 per-org |  96.7% /  44.4% |  83.3% /  27.6% |  60.0% /  11.2% |  41.7% /   8.2% |  23.3% /   2.0% |  23.3% /   2.0% |   0.0% /   0.0% |   0.0% /   0.0% |   0.0% /   0.0% |   0.0% /   0.0% |
| D3 or |  96.7% /  55.6% |  95.0% /  40.8% |  91.7% /  26.0% |  80.0% /  19.9% |  70.0% /  11.2% |  70.0% /   8.7% |  51.7% /   2.0% |  43.3% /   2.0% |  41.7% /   1.5% |  40.0% /   0.0% |
| D3 or, 90-day window |  96.7% /  53.1% |  95.0% /  37.2% |  91.7% /  23.0% |  80.0% /  17.9% |  70.0% /  10.2% |  70.0% /   7.7% |  51.7% /   2.0% |  41.7% /   2.0% |  40.0% /   1.5% |  38.3% /   0.0% |
| D3 or, 30-day window |  96.7% /  40.8% |  95.0% /  30.6% |  83.3% /  17.3% |  68.3% /  13.8% |  56.7% /   7.7% |  53.3% /   6.1% |  33.3% /   2.0% |  28.3% /   2.0% |  26.7% /   1.5% |  21.7% /   0.0% |
| D3 or, not sticky |  96.7% /  55.6% |  95.0% /  40.8% |  91.7% /  25.5% |  80.0% /  19.4% |  70.0% /  10.2% |  70.0% /   7.7% |  50.0% /   2.0% |  43.3% /   2.0% |  41.7% /   1.5% |  40.0% /   0.0% |
| D0 per-request (limit = T) |  13.3% /   9.7% |   8.3% /   2.0% |   5.0% /   1.5% |   5.0% /   1.5% |   0.0% /   0.0% |   0.0% /   0.0% |   0.0% /   0.0% |   0.0% /   0.0% |   0.0% /   0.0% |   0.0% /   0.0% |

### RQ2: cross-organisation aggregation (union vs naive sum)

`or`/`max` count a field disclosed by two organisations once; `sum` adds the organisations' own scores, so it counts it twice. Cell = prevented / benign person FP.

| rule | T=0.6 | T=0.7 | T=0.75 | T=0.8 | T=0.9 | T=1.0 | T=1.2 |
|---|---|---|---|---|---|---|---|
| D3 or |  91.7% /  26.0% |  70.0% /  11.2% |  70.0% /   8.7% |  51.7% /   2.0% |  41.7% /   1.5% |  40.0% /   0.0% |   0.0% /   0.0% |
| D3 max |  91.7% /  26.0% |  70.0% /  11.2% |  70.0% /   8.7% |  51.7% /   2.0% |  41.7% /   1.5% |  40.0% /   0.0% |   0.0% /   0.0% |
| D3 sum |  93.3% /  40.8% |  75.0% /  27.0% |  75.0% /  25.5% |  65.0% /  18.9% |  60.0% /   8.7% |  58.3% /   6.1% |  45.0% /   2.6% |

Benign person FP by kind at T = 0.75:

| rule | life-event | quiet | typical |
|---|---|---|---|
| D3 or |  36.7% |   0.0% |   7.2% |
| D3 max |  36.7% |   0.0% |   7.2% |
| D3 sum |  83.3% |   1.2% |  28.9% |

## Scorer: `qwen/qwen3-32b+dual-qwen/qwen3-4b+def-floor-name` (1245 events scored)

Field detection (p >= 0.5): person linkage  98.6%, stage-1 exit   0.0%, **scoring errors 0**, latency mean 22.84 s, p95 32.21 s

| group | precision | recall | F1 | true fields |
|---|---|---|---|---|
| actor:attacker | 0.952 | 1.000 | 0.976 | 400 |
| actor:benign | 0.930 | 1.000 | 0.964 | 847 |
| all | 0.937 | 1.000 | 0.967 | 1247 |
| all excl. name | 0.905 | 1.000 | 0.950 | 796 |
| injection | 0.952 | 1.000 | 0.976 | 20 |
| name only | 1.000 | 1.000 | 1.000 | 451 |
| style:direct | 0.932 | 1.000 | 0.965 | 618 |
| style:inferable | 0.947 | 1.000 | 0.973 | 196 |
| style:none | nan | nan | nan | 0 |
| style:paraphrase | 0.939 | 1.000 | 0.969 | 433 |

### RQ1: which accounting unit stops assembly? (T = 0.75, no window, sticky)

Cell = prevented (attacker never got every targeted field) / mean share of the targeted record leaked. P1 probes are excluded here (see leakage.py).

| detector | S1 one-org one-account | S2 one-org sybil | S3 cross-org | S4 cross-org sybil slow | all | benign person FP | victim's own requests blocked |
|---|---|---|---|---|---|---|---|
| D0 per-request (limit 0.6) |   6.7% /  97.9% |   0.0% / 100.0% |   6.7% /  98.7% |   6.7% /  99.0% |   5.0% /  98.9% |   0.0% |   0.0% |
| D_session per-session |   0.0% / 100.0% |   0.0% / 100.0% |   0.0% / 100.0% |   0.0% / 100.0% |   0.0% / 100.0% |   0.0% |   0.0% |
| D1 per-account |  26.7% /  92.4% |   0.0% / 100.0% |  13.3% /  97.3% |   0.0% / 100.0% |  10.0% /  97.4% |   0.0% |   0.0% |
| D_traj per-account trajectory (30 d) |  26.7% /  92.4% |   0.0% / 100.0% |  13.3% /  97.3% |   0.0% / 100.0% |  10.0% /  97.4% |  90.8% |  73.0% |
| D2 per-org |  26.7% /  92.4% |  40.0% /  88.9% |  13.3% /  97.3% |  13.3% /  94.9% |  23.3% /  93.4% |   2.0% |   8.0% |
| D3 federated (or) |  26.7% /  92.4% |  53.3% /  84.0% | 100.0% /  60.6% | 100.0% /  53.1% |  70.0% /  72.5% |   8.2% |  48.9% |
| D3c centralised (or) |  26.7% /  92.4% |  53.3% /  84.0% | 100.0% /  60.6% | 100.0% /  53.1% |  70.0% /  72.5% |   8.2% |  48.9% |

### RQ1 (sweep): threshold, window and sticky step-up (all assembly strategies)

Cell = prevented / benign person FP.

| variant | T=0.4 | T=0.5 | T=0.6 | T=0.65 | T=0.7 | T=0.75 | T=0.8 | T=0.85 | T=0.9 | T=0.95 |
|---|---|---|---|---|---|---|---|---|---|---|
| D1 per-account |  75.0% /   9.7% |  55.0% /   6.6% |  33.3% /   1.5% |  25.0% /   1.5% |  10.0% /   0.0% |  10.0% /   0.0% |   0.0% /   0.0% |   0.0% /   0.0% |   0.0% /   0.0% |   0.0% /   0.0% |
| D2 per-org |  95.0% /  35.7% |  78.3% /  24.0% |  58.3% /   9.7% |  40.0% /   6.6% |  23.3% /   2.0% |  23.3% /   2.0% |   0.0% /   0.0% |   0.0% /   0.0% |   0.0% /   0.0% |   0.0% /   0.0% |
| D3 or |  96.7% /  50.5% |  95.0% /  39.3% |  91.7% /  24.0% |  80.0% /  16.3% |  70.0% /   9.2% |  70.0% /   8.2% |  51.7% /   2.0% |  43.3% /   2.0% |  41.7% /   1.5% |  40.0% /   0.0% |
| D3 or, 90-day window |  96.7% /  47.4% |  95.0% /  35.2% |  91.7% /  21.4% |  80.0% /  14.8% |  70.0% /   8.2% |  70.0% /   7.1% |  51.7% /   2.0% |  41.7% /   2.0% |  40.0% /   1.5% |  36.7% /   0.0% |
| D3 or, 30-day window |  96.7% /  34.7% |  91.7% /  28.6% |  83.3% /  15.8% |  68.3% /  11.2% |  56.7% /   6.1% |  53.3% /   5.6% |  33.3% /   2.0% |  26.7% /   2.0% |  25.0% /   1.5% |  21.7% /   0.0% |
| D3 or, not sticky |  96.7% /  50.5% |  95.0% /  39.3% |  91.7% /  23.5% |  80.0% /  15.8% |  70.0% /   8.2% |  70.0% /   7.1% |  50.0% /   2.0% |  43.3% /   2.0% |  41.7% /   1.5% |  40.0% /   0.0% |
| D0 per-request (limit = T) |  10.0% /   2.0% |   6.7% /   1.5% |   5.0% /   0.0% |   5.0% /   0.0% |   0.0% /   0.0% |   0.0% /   0.0% |   0.0% /   0.0% |   0.0% /   0.0% |   0.0% /   0.0% |   0.0% /   0.0% |

### RQ2: cross-organisation aggregation (union vs naive sum)

`or`/`max` count a field disclosed by two organisations once; `sum` adds the organisations' own scores, so it counts it twice. Cell = prevented / benign person FP.

| rule | T=0.6 | T=0.7 | T=0.75 | T=0.8 | T=0.9 | T=1.0 | T=1.2 |
|---|---|---|---|---|---|---|---|
| D3 or |  91.7% /  24.0% |  70.0% /   9.2% |  70.0% /   8.2% |  51.7% /   2.0% |  41.7% /   1.5% |  40.0% /   0.0% |   0.0% /   0.0% |
| D3 max |  91.7% /  24.0% |  70.0% /   9.2% |  70.0% /   8.2% |  51.7% /   2.0% |  41.7% /   1.5% |  40.0% /   0.0% |   0.0% /   0.0% |
| D3 sum |  93.3% /  31.1% |  75.0% /  19.9% |  75.0% /  18.4% |  61.7% /  12.8% |  58.3% /   5.6% |  50.0% /   4.1% |  35.0% /   1.5% |

Benign person FP by kind at T = 0.75:

| rule | life-event | quiet | typical |
|---|---|---|---|
| D3 or |  33.3% |   0.0% |   7.2% |
| D3 max |  33.3% |   0.0% |   7.2% |
| D3 sum |  63.3% |   1.2% |  19.3% |

## RQ4: scorers and defences on the same 1245 events

| scorer | F1 all | F1 all excl. name | F1 name only | F1 style:direct | F1 style:paraphrase | F1 style:inferable | F1 injection | injection recall | linkage | errors | mean latency (s) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| qwen/qwen3-4b | 0.813 | 0.950 | 0.644 | 0.788 | 0.826 | 0.867 | 0.687 | 0.550 |  97.8% | 0 | 6.32 |
| qwen/qwen3-4b+def-floor | 0.816 | 0.950 | 0.653 | 0.791 | 0.830 | 0.869 | 0.976 | 1.000 |  97.8% | 0 | 6.32 |
| qwen/qwen3-4b+def-name | 0.968 | 0.950 | 1.000 | 0.966 | 0.969 | 0.970 | 0.976 | 1.000 |  97.8% | 0 | 6.32 |
| qwen/qwen3-4b+def-floor-name | 0.968 | 0.950 | 1.000 | 0.966 | 0.969 | 0.970 | 0.976 | 1.000 |  97.8% | 0 | 6.32 |
| qwen/qwen3-32b | 0.918 | 0.993 | 0.808 | 0.886 | 0.949 | 0.960 | 0.400 | 0.250 |  97.5% | 0 | 16.52 |
| qwen/qwen3-32b+def-floor | 0.925 | 0.996 | 0.823 | 0.892 | 0.957 | 0.968 | 0.974 | 0.950 |  98.6% | 0 | 16.52 |
| qwen/qwen3-32b+def-name | 0.992 | 0.993 | 0.989 | 0.993 | 0.992 | 0.987 | 0.400 | 0.250 |  97.5% | 0 | 16.52 |
| qwen/qwen3-32b+def-floor-name | 0.997 | 0.996 | 1.000 | 0.997 | 0.999 | 0.995 | 0.974 | 0.950 |  98.6% | 0 | 16.52 |
| qwen/qwen3-32b+dual-qwen/qwen3-4b | 0.806 | 0.950 | 0.634 | 0.780 | 0.823 | 0.859 | 0.727 | 0.600 |  98.6% | 0 | 22.84 |
| qwen/qwen3-32b+dual-qwen/qwen3-4b+def-floor-name | 0.967 | 0.950 | 1.000 | 0.965 | 0.969 | 0.973 | 0.976 | 1.000 |  98.6% | 0 | 22.84 |
