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

## Preliminary: who

`fleets.py` clusters the pools by the wallets that round-trip in them: two pools are
joined when five or more of the same wallets round-trip in both, and the connected
components are the fleets.

**Fleet size is 20.** Twenty-two of the thirty pools have exactly twenty round-trip
wallets; the rest have 10, 15, 16, 19 and one has 49. Of 260 round-trip wallets, **160
appear in more than one pool.**

| Fleet | Pools | Tickers | Wallets | Claimed 24h volume |
|---|---|---|---|---|
| 1 | 4 | $MSFT, AAPL, NIKE | 20 | $228,088,618 |
| 2 | 4 | GOOGL, GOOGLE | 20 | $214,849,387 |
| 3 | 4 | AAPL | 20 | $213,443,782 |
| 4 | 3 | HOOD | 20 | $211,155,730 |
| 5 | 1 | NVIDA | 20 | $153,213,665 |
| 6 | 2 | LV, SPCX | 20 | $149,536,183 |
| 7 | 2 | Anthropic, ClaudeAI | 20 | $139,620,496 |
| 8 | 3 | OpenAI | 20 | $136,819,508 |
| 9 | 1 | HOOD | 49 | $100,086,912 |
| 10 | 2 | NVDA, TSLA | 10 | $84,892,294 |
| 11 | 2 | Gemini AI, 牛来 | 15 | $75,190,426 |
| 12 | 1 | TSLA | 10 | $45,307,116 |
| 13 | 1 | b-money | 16 | $43,533,798 |

So this is **not one operator**. It is thirteen separate fleets that do not share
wallets with each other — and twenty-two of them are the same size to the wallet. Same
tool, different hands, is the reading the data supports; it is not established here.

Note that fleet 7 ran Anthropic and ClaudeAI together, and fleet 2 ran GOOGL and the
misspelled GOOGLE together: one fleet takes a theme, not a ticker.

## Limits, stated before anyone asks

**Fleet size is measured in the sampled window.** A fleet larger than the sample could
not be fully resolved. One pool does resolve 49 distinct round-trip wallets, so the
sample is not capped at 20, and twenty appearing in twenty-two separate samples is a
property of the fleets rather than of the method — but it is a floor, not a ceiling.

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

1. Whether the thirteen fleets are independent operators or one operator running
   thirteen wallet sets. They share no wallets, but shared funding would settle it, and
   the per-token fee accounts have not been traced to a source. Not done.
2. What those two fee accounts are in pumpswap's mechanics. **VERIFY CURRENTLY** —
   not checked, not assumed.
3. Whether the sampled composition holds across the full 24 hours. It cannot be
   established from this capture.
