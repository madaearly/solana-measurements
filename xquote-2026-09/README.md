# xSOL as a quote currency — and what a levered long actually caught

Measured 2026-09-15.

Eleven memecoins on Solana are priced in **xSOL** rather than SOL. xSOL is Hylo's
levered long on SOL, advertised at up to four times, measured in `hylo-2026-09` as
having turned $1,000 into $57 over 309 days.

This directory holds two findings. One survived and one did not, and the second is the
reason the first exists.

## Reproducing this

```
python3 fetch.py      # finds the pools, pulls three series -> data/
python3 analyze.py    # every figure below, offline from data/
```

## The pools

| Opened | Ticker | Liquidity |
|---|---|---|
| 2026-05-20 | PERP | $10,931 |
| 2026-06-07 | USD2 | $83 |
| 2026-08-11 | LOOOONG | $31,853 |
| 2026-08-11 | LONGCAT | $11,408 |
| 2026-08-19 | SOLDIERS | $18,135 |
| 2026-09-06 | SLO | $9,955 |
| 2026-09-07 | LEVERCAT | $145,484 |
| 2026-09-07 | LEVERDOG | $11,964 |
| 2026-09-12 | SJ | $1,244 |
| 2026-09-12 | LBR | $392 |
| 2026-09-13 | LEVERPUP | $0 |

**$241,448 in total. Six of the eleven opened in the ten days before capture, three of
those in the last three.** Creation dates come from the pool endpoint, so this part of
the finding does not depend on any price series at all.

## What survived: the capture rate

The oldest of these pools opened 2026-05-20, which fixes a **116-day window**. It was
not chosen; it is the only window all of this has in common.

| | |
|---|---|
| SOL | **+19.6%** — $1,000 → $1,195.71 |
| xSOL | **+1.4%** — $1,000 → $1,013.81 |
| **Share of SOL's gain that reached the levered holder** | **7.1%** |

That $1,000 in xSOL was worth **$254 on 2026-06-06** and **$1,177 on 2026-08-27**. It
did not underperform because it failed to lever. It underperformed because it levered a
round trip, and a round trip compounds against the holder in both directions.

This is the third window xSOL has been measured across here, and the first in which SOL
rose:

| Window | SOL | xSOL |
|---|---|---|
| 309 days | −36% | −94% |
| 183 days (`hylo-2026-09`) | +13.2% | −29.3% |
| **116 days (here)** | **+19.6%** | **+1.4%** |

Down harder, up softer, every time. Volatility decay is what leverage costs and Hylo
documents it; this is a measurement of a disclosed property.

## What did not survive: the hypothesis

The reason for looking at all was the obvious guess: **if your position is priced in
something that decays, the decay eats you whether the memecoin moves or not.**

Only one of the eleven pools is old enough to test that — PERP, opened 2026-05-20,
holding $10,721. Measured both ways:

| | |
|---|---|
| PERP in dollars | **−64.8%** |
| PERP in xSOL | **−65.3%** |

Those are the same number. **The quote currency contributed nothing. The meme did it
alone, and the hypothesis is dead.**

What survives is narrower: the dollar outcome of holding one of these eleven tokens is
the memecoin multiplied by a line that went to $254 and back. Over this window that
multiplier was approximately one. It will not be one every window.

## Before the price series was used

PERP's pool holds $10,721, and a $4,107 pool produced three withdrawn figures in
`hylo-2026-09`, so `analyze.py` runs the variance ratio before deriving anything:

| | 1d | 3d | 7d | 14d | autocorr |
|---|---|---|---|---|---|
| SOL | 3.03% | 3.16% | 3.61% | 3.91% | +0.093 |
| xSOL | 9.52% | 10.17% | 12.26% | 13.51% | +0.158 |
| PERP usd | 22.30% | 14.74% | 18.60% | 15.65% | +0.003 |
| PERP in xSOL | 18.13% | 12.58% | 14.82% | 12.45% | −0.002 |

Flat across horizons, autocorrelation near zero. Volatile, but not noise-dominated —
unlike sHYUSD, which collapsed from 2.35% to 0.73% and had autocorrelation −0.479.
Usable.

## What this does not establish

**Ten of the eleven pools are too young to measure through.** What their holders have
experienced is not known here, because the data does not exist yet. The pools will have
history in a month and the same test can be run then.

**Nothing here is about what holders understood.** Every one of these pairs names its
quote asset in the pool title. This measures what the quote asset did, not what anyone
knew about it.

**A correction made during writing.** An earlier draft of the accompanying post said
"four opened in the last four days." Three opened in the last four days; six opened in
the last ten. `analyze.py` printing the count is what caught it.
