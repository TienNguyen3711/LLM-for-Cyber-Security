# RQ3: leakage of the crossing bit, `data/bench_s7x.json`

120 P1 probe campaigns ({'telco': 50, 'health': 26, 'bank': 44}), T = 0.75. MI in bits (plug-in; 'corr.' subtracts the mean MI with the secret shuffled, i.e. small-sample bias). guess = accuracy of the best guess of the secret from the transcript, prior = guessing the most common value. Randomised rows average 5 seeds.

Secret prevalence: S_other bins {0: 40, 1: 56, 2: 16, 3: 8}, S_health {True: 34, False: 60}.


## Scorer `oracle`

| configuration | S_other MI (corr.) | guess / prior | S_health MI (corr.) | guess / prior | assembly prevented | alerted | benign person FP |
|---|---|---|---|---|---|---|---|
| D3 or (visible block) | 0.368 (0.292) | 0.52 / 0.47 | 0.095 (0.056) | 0.70 / 0.64 | 75.0% | 75.0% | 3.9% |
| D3 max (visible block) | 0.368 (0.292) | 0.52 / 0.47 | 0.095 (0.056) | 0.70 / 0.64 | 75.0% | 75.0% | 3.9% |
| D3 sum (visible block) | 0.853 (0.774) | 0.73 / 0.47 | 0.469 (0.433) | 0.85 / 0.64 | 80.0% | 80.0% | 24.7% |
| D3 or, not sticky | 0.198 (0.114) | 0.49 / 0.47 | 0.045 (0.005) | 0.67 / 0.64 | 75.0% | 75.0% | 3.9% |
| D3 or, threshold noise +/-0.05 | 0.338 (0.259) | 0.52 / 0.47 | 0.123 (0.087) | 0.72 / 0.64 | 69.5% | 70.5% | 2.9% |
| D3 or, threshold noise +/-0.10 | 0.334 (0.255) | 0.52 / 0.47 | 0.123 (0.087) | 0.72 / 0.64 | 68.8% | 69.8% | 2.9% |
| D3 or, threshold noise +/-0.20 | 0.259 (0.180) | 0.51 / 0.47 | 0.072 (0.036) | 0.69 / 0.64 | 71.8% | 73.2% | 7.5% |
| alert-only: requester sees D2, D3 alerts compliance | 0.064 (0.000) | 0.49 / 0.47 | 0.000 (0.000) | 0.64 / 0.64 | 17.5% | 75.0% | 2.6% |

H(S_other) = 1.689 bits, H(S_health) = 0.944 bits. Most common transcripts (B = blocked) under D3 or: `....` x75, `...B` x30, `..BB` x6, `BBBB` x5, `.BBB` x4.

## Scorer `qwen/qwen3-4b`

| configuration | S_other MI (corr.) | guess / prior | S_health MI (corr.) | guess / prior | assembly prevented | alerted | benign person FP |
|---|---|---|---|---|---|---|---|
| D3 or (visible block) | 0.420 (0.295) | 0.53 / 0.47 | 0.110 (0.042) | 0.70 / 0.64 | 71.2% | 73.8% | 14.3% |
| D3 max (visible block) | 0.420 (0.295) | 0.53 / 0.47 | 0.110 (0.042) | 0.70 / 0.64 | 71.2% | 73.8% | 14.3% |
| D3 sum (visible block) | 0.835 (0.673) | 0.72 / 0.47 | 0.442 (0.367) | 0.83 / 0.64 | 78.8% | 81.2% | 39.0% |
| D3 or, not sticky | 0.225 (0.119) | 0.49 / 0.47 | 0.048 (0.002) | 0.67 / 0.64 | 70.0% | 72.5% | 10.4% |
| D3 or, threshold noise +/-0.05 | 0.405 (0.279) | 0.53 / 0.47 | 0.102 (0.033) | 0.70 / 0.64 | 64.5% | 66.2% | 10.1% |
| D3 or, threshold noise +/-0.10 | 0.399 (0.270) | 0.53 / 0.47 | 0.103 (0.033) | 0.70 / 0.64 | 62.0% | 63.7% | 10.9% |
| D3 or, threshold noise +/-0.20 | 0.333 (0.187) | 0.51 / 0.47 | 0.141 (0.063) | 0.71 / 0.64 | 67.0% | 68.8% | 18.2% |
| alert-only: requester sees D2, D3 alerts compliance | 0.064 (0.000) | 0.49 / 0.47 | 0.000 (0.000) | 0.64 / 0.64 | 17.5% | 73.8% | 3.9% |

H(S_other) = 1.689 bits, H(S_health) = 0.944 bits. Most common transcripts (B = blocked) under D3 or: `....` x70, `...B` x28, `BBBB` x7, `.BBB` x6, `..BB` x4, `.B..` x3.

## Scorer `qwen/qwen3-32b`

| configuration | S_other MI (corr.) | guess / prior | S_health MI (corr.) | guess / prior | assembly prevented | alerted | benign person FP |
|---|---|---|---|---|---|---|---|
| D3 or (visible block) | 0.401 (0.284) | 0.53 / 0.47 | 0.126 (0.057) | 0.71 / 0.64 | 71.2% | 71.2% | 3.9% |
| D3 max (visible block) | 0.401 (0.284) | 0.53 / 0.47 | 0.126 (0.057) | 0.71 / 0.64 | 71.2% | 71.2% | 3.9% |
| D3 sum (visible block) | 0.853 (0.728) | 0.73 / 0.47 | 0.498 (0.441) | 0.86 / 0.64 | 77.5% | 78.8% | 27.3% |
| D3 or, not sticky | 0.198 (0.114) | 0.49 / 0.47 | 0.045 (0.005) | 0.67 / 0.64 | 71.2% | 71.2% | 3.9% |
| D3 or, threshold noise +/-0.05 | 0.357 (0.243) | 0.53 / 0.47 | 0.131 (0.070) | 0.72 / 0.64 | 61.3% | 61.8% | 2.9% |
| D3 or, threshold noise +/-0.10 | 0.343 (0.232) | 0.52 / 0.47 | 0.131 (0.072) | 0.72 / 0.64 | 59.2% | 60.2% | 2.9% |
| D3 or, threshold noise +/-0.20 | 0.307 (0.188) | 0.51 / 0.47 | 0.095 (0.034) | 0.70 / 0.64 | 61.8% | 64.0% | 8.8% |
| alert-only: requester sees D2, D3 alerts compliance | 0.064 (0.000) | 0.49 / 0.47 | 0.000 (0.000) | 0.64 / 0.64 | 17.5% | 71.2% | 2.6% |

H(S_other) = 1.689 bits, H(S_health) = 0.944 bits. Most common transcripts (B = blocked) under D3 or: `....` x73, `...B` x30, `BBBB` x5, `..BB` x5, `.BBB` x4, `B.BB` x1.
