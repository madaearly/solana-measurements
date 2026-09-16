# xsol-desk-2026-09

Taken 2026-09-16. Subject: xSOL on Solana, `4sWNB8zGWHkh6UnmwiEtzNxL4XrN7uK9tosbESbJFfVs`.

A per-wallet read of one token's order flow, and the figure that did not survive
checking.

## What was measured

413 trades by 226 wallets across three pools, in a
3.29-hour window from 2026-09-16 07:46 to
2026-09-16 11:04 UTC.

| | |
|---|---|
| Wallets that traded exactly once | 126 of 226 (55%) |
| Share of volume held by the top 10 wallets | 48.7% |
| Share held by the top 50 | 87.9% |
| Median trade | ${:,.0f}".format(dd['median']) if False else f"$22" |
| Mean trade | $103 |
| Trades under one dollar | 60 |
| Buy / sell across the window | $21,300 / $21,209 (imbalance +0.002) |

## The figure that was withdrawn

The first reading of this data reported a trend: buy/sell imbalance travelling
from −0.52 to −0.08 across a twenty-hour window, described as selling that was
front-loaded and then closed.

**It was an artefact of the sample, not a movement in the market.**

The `/trades` endpoint returns the last 300 trades per pool and nothing more, so
each pool reaches back a different distance. On that run:

| pool | trades | depth |
|---|---:|---:|
| xSOL / SOL | 344 | 20.1h |
| xSOL / USDC | 300 | 15.2h |
| xSOL / LEVERCAT | 300 | 8.4h |

Merged naively, the first quarter of the window contained two pools, the second
quarter one, and the last two quarters three. The apparent convergence came from
which venues happened to be present, not from the flow. Inside the deepest pool
alone, 300 of its 344 trades sat in the final quarter: at the 25% and 50% marks
there were 29 trades.

`fetch.py` now trims the merged window to the **intersection** of every sampled
pool's coverage, so no pool is truncated inside it. The validity test is
containment — a covered pool that went quiet is data, not a gap.

The cost is reach: 16.1 hours became 3.29, and 487 trades outside
the intersection were dropped rather than merged.

## Coverage of this run

| pool | trades | range (UTC) | hours |
|---|---:|---|---:|
| `xSOL / LEVERCAT` | 300 | 02:34 – 11:05 | 8.52 |
| `xSOL / SOL` | 300 | 07:46 – 11:07 | 3.35 |
| `xSOL / USDC` | 300 | 19:01 – 11:04 | 16.04 |

Window: 07:46 – 11:04 UTC, 3.29h, axis valid: True.

## Reproducing

```
python3 fetch.py <mint> --out data/<id>.json --pools 3
python3 render_desk.py data/<id>.json --out desk.mp4 --seconds 24
```

Sources: GeckoTerminal public API (`/tokens/{mint}/pools`,
`/pools/{addr}/trades`, `/pools/{addr}/ohlcv`) and DexScreener
(`/tokens/{mint}`). The trades endpoint carries `tx_from_address`, which is the
only reason a per-wallet read is possible without an indexer.

No key, no wallet, nothing signed. The free tier limits to roughly 30 requests a
minute; every call sleeps 2.2s.

Requires `pillow` for the renderer. Fonts are loaded from a system monospace path.
