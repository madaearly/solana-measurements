# solana-measurements

One-off measurements of Solana tokens, taken from public pools and published with the
raw data, the script that produced every figure, and the figures that did not survive
checking.

Each directory is one measurement, dated by when it was taken. Nothing here is a
prediction, a backtest, or a recommendation. Every number is a measurement of something
that has already happened, and every measurement states the window it applies to.

The pre-registered experiment lives in its own repository:
[experiment-001-volume-vs-price](https://github.com/madaearly/experiment-001-volume-vs-price).

## Measurements

| Directory | Taken | Subject | Headline |
|---|---|---|---|
| [`hylo-2026-09`](hylo-2026-09) | 2026-09-14 | Hylo — hyUSD, sHYUSD, xSOL | $1,000 in each over the same 183 days: SOL $1,132, xSOL $707, hyUSD $999, sHYUSD $1,185 |
| [`tickerwash-2026-09`](tickerwash-2026-09) | 2026-09-14 | 31 pumpswap pools named after real companies | $1,850,861,290 claimed in 24h against reserves of millionths of a cent; round-trips carry a median 99.8% of sampled volume |
| [`jitosol-2026-09`](jitosol-2026-09) | 2026-09-15 | jitoSOL — the control | +5.74% a year in SOL terms, delivered as advertised; worth $26.08 on a thousand dollars |
| [`xquote-2026-09`](xquote-2026-09) | 2026-09-15 | eleven memecoins priced in xSOL | over 116 days SOL rose 19.6% and xSOL 1.4% — 7.1% of the gain reached the levered holder; the hypothesis that the quote currency ate these positions did not survive |

## How to read anything in here

Start with [METHOD.md](METHOD.md). It is short, and it is the part that makes the
numbers worth anything.

Each measurement's README carries a section called **What had to be withdrawn**. If it
is empty, nothing was. It usually is not empty.
