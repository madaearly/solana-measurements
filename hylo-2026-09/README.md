# Hylo — hyUSD, sHYUSD and xSOL

Measured 2026-09-14.

Hylo runs three tokens against one balance sheet: **hyUSD**, a stablecoin; **xSOL**, a
levered long on SOL with no liquidations; and **sHYUSD**, hyUSD staked into the
stability pool, which absorbs what the levered side loses and is paid for doing so.

The question: over one window, with no trading and no timing, what did each of them
actually return.

## Reproducing this

```
python3 fetch.py        # five daily series -> data/final_series.json
python3 analyze.py      # peg statistics, cross-pool check, point-to-point returns
python3 noise_test.py   # are sHYUSD's daily moves real? autocorrelation + variance ratio
python3 robust.py       # the published figures: 7-day-median endpoints
python3 series.py       # the day-by-day table -> data/ledger_series.json
```

`data/final_series.json` is the raw fetch, committed, so steps 2–5 run offline.

## The window

**2026-03-12 to 2026-09-14, 183 shared daily closes.**

The start is not a choice. 2026-03-12 is sHYUSD's first traded price in any pool. Every
sHYUSD pool begins then, and the second-deepest pool returns an empty second page rather
than older bars, so this is an absence of trades and not a pagination limit. The first
traded price is already 1.1922, not 1.0000, so the return below **understates** total
accrual since the vault opened.

The trailing median consumes the first seven days, so the published table starts
2026-03-18.

## Result

$1,000 into each on 2026-03-18, untouched until 2026-09-14. Trailing 7-day median,
the same method on all four.

| | 7-day median | point to point | max drawdown |
|---|---|---|---|
| SOL | **$1,131.84** | $1,194.41 | −30.22% |
| xSOL | **$707.35** | $840.58 | −78.40% (low $216.03, 2026-06-10) |
| hyUSD | **$999.12** | $997.71 | −0.61% |
| sHYUSD | **$1,185.14** | $1,244.82 | −8.12% (2026-03-30) |

**The levered long lost money in a window where the asset it levers gained 13%.** This
is volatility decay, it is disclosed by Hylo in their own materials, and it is not a
defect. It is also not something anyone had put in dollars.

**The passive side that absorbs those losses returned more than the asset itself**, at
roughly a quarter of the drawdown. sHYUSD spent 22 of 177 days below $1,000; xSOL spent
173 of 177.

### hyUSD held the peg

319 daily closes from 2025-10-29. Median $1.0005, worst $0.9885. **One day** beyond 1%
off the dollar, **none** beyond 2%. hyUSD carries $2,263,982 of DEX liquidity across
nine pools.

## What had to be withdrawn

The first pass reported, for sHYUSD, a beta to SOL of 0.415, a maximum drawdown of
15.71% and a worst day of −9.02%. **All three were artefacts and none are published.**

sHYUSD's deepest pool holds **$4,107**. The variance-ratio test (`noise_test.py`) gives
daily sigma implied by blocks of 1, 3, 7 and 14 days:

| | 1d | 3d | 7d | 14d |
|---|---|---|---|---|
| SOL | 3.57% | 3.41% | 3.27% | 3.35% |
| xSOL | 10.20% | 9.89% | 10.31% | 9.92% |
| **sHYUSD** | **2.35%** | **2.06%** | **1.25%** | **0.73%** |

Two controls from the same window, the same provider and the same code path do not
move. sHYUSD falls by 69%. That is microstructure noise in the prints of a token nobody
trades, not risk in the token. A beta estimated on such a series is attenuated toward
zero, and a drawdown measured on it is mostly a bad print followed by a good one.

What survives is the trend, which is an order of magnitude larger than the noise, and
the 8.12% drawdown measured on the median series — a real loss, bottoming 2026-03-30.

This is the fourth error of one kind inside two days: **confirming that data exists
without confirming what it measures.** The first multiplied a USD series by the SOL
price. The second read the wrong side of a base-first pool. The third accepted bars
that predated the observation window. This one accepted movement that was not movement.
Rule 5 in [METHOD.md](../METHOD.md) exists because of it.

## Cross-check

sHYUSD against the independent sHYUSD/ONe pool: **180 overlapping days, median
disagreement 0.18%, maximum 1.92%**, and all 18 daily drops beyond 2% are present in
both. Spot price agrees to the cent across six pools. The two pools agree on what the
market printed; they do not, and cannot, establish that the print tracked the vault.

## Sources

All Solana, all public, daily closes from GeckoTerminal, all already denominated in USD.

| Asset | Venue | Pool |
|---|---|---|
| SOL | Raydium SOL/USDC | `58oQChx4yWmvKdwLLZzBi4ChoCc2fqCUWBkwMihLYQo2` |
| xSOL | Orca | `coj59LYbLc6DhMwnxxfPc9mUiknjFSsW4XcuYw4DMPk` |
| hyUSD | Orca hyUSD/USDC | `4tJW2axbTxtT6nKbjB5pZwePtW84cB7E1B6tdCCLGfrC` |
| sHYUSD | Orca sHYUSD/hyUSD | `FsayKGwMGDmfXZrXPWrnzWGLAHLPfQRug28kVL1JT6wR` |
| sHYUSD (check) | Orca sHYUSD/ONe | `8CA9zadmbpQqoXPXN9Xsk33RVv171sidc8KK1NzVVZbz` |

sHYUSD requires `token=HnnGv3HrSqjRpgdFmx7vQGjntNEoex1SU4e9Lxcxuihz` on the OHLCV
request. Its deepest pool is named "hyUSD / sHYUSD" and the base side is hyUSD, so
without the parameter the endpoint returns hyUSD's series, which looks entirely
plausible and is wrong by 48%.

Read from Solana mainnet RPC on 2026-09-14: hyUSD supply 17,901,675.92, sHYUSD supply
10,136,662.78, both six decimals. Both are owned by the original SPL Token program, not
Token-2022, and both report no extensions — so sHYUSD's yield accrues in the exchange
rate and not by rebase. Supply moves continuously; these are one read, not a constant.

## Credit

Hylo document volatility decay in their own materials. This measures a disclosed
property; it does not uncover a hidden one.
