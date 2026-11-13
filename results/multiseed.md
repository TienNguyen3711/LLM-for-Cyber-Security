# Oracle-scored results over 10 seeds (7, 11, 13, 17, 19, 23, 29, 31, 37, 41)

Each bench: 300 people, 60 base campaigns, --overlap 20, --probes 120; T = 0.75. Cells are mean ± sd across seeds, in % unless marked bits.


## RQ1: prevented by accounting unit

| detector | S1 one-org one-account | S2 one-org sybil | S3 cross-org | S4 cross-org sybil slow | S5 cross-org redundant | all | benign person FP |
|---|---|---|---|---|---|---|---|
| D0 per-request (limit 0.6) |   0.0 ±  0.0 |   0.0 ±  0.0 |   0.0 ±  0.0 |   0.0 ±  0.0 |   0.0 ±  0.0 |   0.0 ±  0.0 |   0.0 ±  0.0 |
| D_session per-session |   0.0 ±  0.0 |   0.0 ±  0.0 |   0.0 ±  0.0 |   0.0 ±  0.0 |   0.0 ±  0.0 |   0.0 ±  0.0 |   0.0 ±  0.0 |
| D1 per-account |  24.0 ±  6.4 |   3.3 ±  4.7 |   8.7 ±  6.3 |   4.0 ±  4.7 |  13.0 ±  8.9 |  10.8 ±  3.4 |   0.0 ±  0.0 |
| D_traj per-account trajectory (30 d) |  24.0 ±  6.4 |   3.3 ±  4.7 |   8.7 ±  6.3 |   1.3 ±  2.8 |  13.0 ±  8.9 |  10.2 ±  3.5 |  94.5 ±  1.6 |
| D2 per-org |  24.0 ±  6.4 |  26.0 ± 11.1 |  10.7 ±  7.8 |  21.3 ± 15.7 |  16.0 ±  8.8 |  19.4 ±  2.7 |   3.2 ±  2.5 |
| D3 federated (or) |  28.7 ± 10.0 |  30.0 ± 11.9 |  96.7 ±  7.2 |  96.0 ±  4.7 |  98.5 ±  2.4 |  71.8 ±  3.4 |   7.9 ±  3.7 |
| D3c centralised (or) |  28.7 ± 10.0 |  30.0 ± 11.9 |  96.7 ±  7.2 |  96.0 ±  4.7 |  98.5 ±  2.4 |  71.8 ±  3.4 |   7.9 ±  3.7 |

## RQ2: aggregation rule (D3)

| rule | prevented | benign person FP | FP overlap-moved | FP overlap-kyc |
|---|---|---|---|---|
| or |  71.8 ±  3.4 |   7.9 ±  3.7 |  10.0 ± 12.1 |   3.3 ±  7.0 |
| max |  71.8 ±  3.4 |   7.9 ±  3.7 |  10.0 ± 12.1 |   3.3 ±  7.0 |
| sum |  75.0 ±  3.8 |  28.6 ±  4.9 | 100.0 ±  0.0 | 100.0 ±  0.0 |

## RQ3: crossing-bit leakage to a probing requester

MI is bias-corrected (minus the shuffled-secret MI), in bits.

| configuration | S_other MI | S_health MI | S_health guess − prior (pp) | assembly prevented | alerted | benign person FP |
|---|---|---|---|---|---|---|
| D3 or (visible block) | 0.238 ± 0.067 | 0.035 ± 0.044 |   4.1 ±  3.5 |  71.8 ±  3.4 |  71.8 ±  3.4 |   7.9 ±  3.7 |
| D3 max (visible block) | 0.238 ± 0.067 | 0.035 ± 0.044 |   4.1 ±  3.5 |  71.8 ±  3.4 |  71.8 ±  3.4 |   7.9 ±  3.7 |
| D3 sum (visible block) | 0.757 ± 0.056 | 0.369 ± 0.058 |  15.5 ±  4.6 |  75.0 ±  3.8 |  75.0 ±  3.8 |  28.6 ±  4.9 |
| D3 or, not sticky | 0.139 ± 0.040 | 0.028 ± 0.026 |   3.7 ±  2.7 |  71.6 ±  3.3 |  71.6 ±  3.3 |   7.9 ±  3.7 |
| D3 or, threshold noise +/-0.05 | 0.251 ± 0.058 | 0.053 ± 0.043 |   5.3 ±  3.4 |  65.5 ±  2.6 |  66.0 ±  2.5 |   6.0 ±  3.0 |
| D3 or, threshold noise +/-0.10 | 0.255 ± 0.055 | 0.055 ± 0.046 |   5.4 ±  3.3 |  64.8 ±  2.7 |  65.3 ±  2.7 |   6.3 ±  3.2 |
| D3 or, threshold noise +/-0.20 | 0.258 ± 0.057 | 0.058 ± 0.030 |   5.2 ±  2.3 |  68.1 ±  2.6 |  68.8 ±  2.7 |  11.0 ±  3.3 |
| alert-only: requester sees D2, D3 alerts compliance | 0.016 ± 0.019 | 0.000 ± 0.000 |   0.0 ±  0.0 |  19.4 ±  2.7 |  71.8 ±  3.4 |   3.2 ±  2.5 |
