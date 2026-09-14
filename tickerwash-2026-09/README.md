# Company-ticker tokens on pumpswap — raw capture

Captured 2026-09-14T22:29:46Z. **Analysis in progress; the figures below are what the
capture contains, not a finished measurement.** Conclusions are marked as preliminary
and have not been published anywhere.

## Why this was captured in a hurry

On 2026-09-14, 31 of the 40 highest-volume Solana pools were pumpswap pools created in
the previous 48 hours, named after real companies — NVIDA, NVDA, HOOD, SPCX, NIKE,
AAPL, GOOGL, GOOGLE, TSLA, $MSFT, XL, LV, OpenAI, Anthropic, ClaudeAI, Gemini AI,
b-money, 牛来 — several with multiple pools per ticker (AAPL five, HOOD four, GOOGL and
OpenAI three each).

Together they claimed **$1,850,861,290** of 24-hour volume while holding reserves of
millionths of a cent.

By the time of capture most had already stopped trading. The 24-hour counters still
showed the volume; the pools were empty. Those counters roll off within a day, so the
evidence was captured before the analysis was finished rather than after.

## What is in `data/`

| File | Contents |
|---|---|
| `top_pools.json` | The two raw API pages the pool list came from, unmodified |
| `pool_index.json` | Flattened index: reserves, 24h volume, creation time, dex, mint |
| `trades.json` | The last 300 trades of each of 33 pools — 9,900 trades |

`analyze.py` reproduces the table below from `trades.json` alone, offline.

## Preliminary: what the sample shows

A **round-trip transaction** contains both a sell and a buy of the same token in the
same pool. On-chain these carry two signers: one wallet sells, the other buys,
atomically, in a transaction both authorise. There is no price difference to capture
and the fee is paid twice, so the only product of such a transaction is volume.

Across 31 pumpswap pools and 9,300 sampled trades:

- round-trip share of transactions: **median 75%**
- round-trip share of sampled volume: **median 99.8%**
- pools where round-trips carry over 99% of sampled volume: **28 of 31**

One transaction verified directly against mainnet (slot 446983064, NVIDA pool
`4ynjBnDoFaFqG18rzHAb4qUWHvLDYRcQu2Vcw4f4kJov`): instructions `Sell` then `Buy` on
pumpswap `pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA`, two signers,
`DQL6Q5Bf1msvG4cR43Qf51hE7T9k4VVdyM7nEDJ97mhf` selling 11,824,262.83 and
`GH628cLJ8Ms8GX9zyrktGmsdCPamMxGGPzhaybezq8e5` buying 12,327,076.66. Measured cost of
the round-trips in that sample: **8.095 SOL to print $228,088 of volume** — about one
dollar spent for every $278 printed.

Two accounts per token receive a fee split exactly in half. They differ for every
token, so they are not a shared protocol vault.

## Limits, stated before anyone asks

**The samples cover 0.39% of the claimed volume.** Each is the last 300 trades, usually
30–180 seconds. The round-trip share is therefore measured *on that window*, and this
capture does not establish that the whole $1.85 billion has the same composition.

What does span the full window, and comes from the platform's own 24-hour counters
rather than the sample: **1,497 sellers against 2,504,187 transactions** across these
pools — 1,673 transactions per selling wallet per day, one every 52 seconds around the
clock — against 4,305 sellers and 12 transactions each in SOL/USDC over the same day.
And reserves near zero for the whole period.

Two pools caught by the reserve filter were **excluded, not counted**: `USDT/USDC` and
`USDG/USDC` on manifest. Manifest is an order book, not an AMM, so a zero
`reserve_in_usd` is expected there, and both pools date from April. This is why the
total reads $1.85bn and not $1.94bn.

## Open

1. Whether one operator is behind all of them. The per-token fee accounts would have to
   be traced to a funding source. Not done.
2. What those two fee accounts are in pumpswap's mechanics. **VERIFY CURRENTLY** —
   not checked, not assumed.
3. Whether the sampled composition holds across the full 24 hours. It cannot be
   established from this capture.
