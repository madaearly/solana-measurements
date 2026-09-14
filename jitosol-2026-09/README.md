# jitoSOL — the control

Measured 2026-09-15.

Four measurements in this repository and its companion posts had come back unflattering
in a row. That is a problem whether or not each one is right: a method that only ever
produces one kind of answer stops being evidence of anything. This one was run because
its answer was almost certainly going to be **yes, it does what it says** — and an
account that cannot publish that is not measuring, it is arguing.

## Reproducing this

```
python3 fetch.py      # four daily series -> data/jito_series.json
python3 analyze.py    # every figure below, offline from that file
```

## What is actually being measured

jitoSOL's dollar price moves with SOL, so a dollar series measures SOL and not the
product. The quantity that isolates the staking yield is **jitoSOL denominated in SOL**.

Window: **2025-09-22 to 2026-09-14**, 358 daily closes after the median consumes the
first seven. The pool history starts 2025-09-16, and that — not the token's age — is
what limits the window.

## Result

| | |
|---|---|
| 1 jitoSOL, in SOL | 1.231377 → **1.300429** |
| Over 357 days | **+5.61%** |
| Annualised | **+5.74%** |
| Days the smoothed rate fell | **21 of 356** |
| Worst of those | **−0.234%** (2026-09-01) |

A staking rate cannot pay backwards. This one did not: the twenty-one down days are the
DEX price oscillating around the vault rate, not the vault losing value.

Cross-checked against two independent pools over the same 364 days: **median
disagreement 0.025%** against Raydium JitoSOL/SOL and **0.019%** against Orca
JitoSOL/USDC. For comparison, the same check on sHYUSD in `hylo-2026-09` gave 0.18% —
seven times looser, from a pool holding $4,107 against this one's $6,984,565.

## The noise test, run in the other direction

`analyze.py` runs the same variance-ratio test that withdrew three figures in
`hylo-2026-09`. Daily sigma implied by blocks of 1, 3, 7 and 14 days:

| | 1d | 3d | 7d | 14d |
|---|---|---|---|---|
| SOL | 3.564% | 3.409% | 3.267% | 3.353% |
| jitoSOL | 3.567% | 3.415% | 3.282% | 3.351% |
| **the ratio** | **0.191%** | 0.094% | 0.098% | **0.068%** |

The ratio's series is noise-dominated too, and its lag-1 autocorrelation is −0.479. The
difference from the Hylo case is scale: this noise is **0.19% a day against a 5.7%
annual signal**. Raw, the series appears to fall on 141 of 363 days. Smoothed, it falls
on 21. Reporting the 141 would have been false in the opposite direction from the Hylo
mistake, and the same test catches both.

## What it was worth

$1,000 on 2025-09-22, never touched:

| | |
|---|---|
| Held as SOL | **$465.06** |
| Held as jitoSOL | **$491.14** |
| Difference | **$26.08** |

The product delivered exactly what it advertised for a year. SOL fell 53% over the same
window, so what it delivered came to twenty-six dollars on a thousand.

That is not a criticism of jitoSOL. It is the whole finding: 5.74% of a number that
falls by half is still 5.74%, and it is still small. The yield was never the risk.

## What this does not establish

The advertised APY is not checked here. Jito publishes a figure; this measures what the
exchange rate actually did, and does not claim the two should match — fees, validator
performance and the timing of deposits all sit between them.

One year is not the token's life. The window is set by pool history, not by choice, and
a different year would give a different number.
