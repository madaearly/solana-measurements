# Where the real-world-asset perps actually are — 2026-09-21

On 2026-09-21 an account with 558,000 followers posted that open interest on perpetual
DEXs had hit an all-time high: 19 billion dollars of crypto, 25 billion in total, with
real-world assets up from 6% of the total in January to 24% today.

**The claim holds up.** RWA perps are real and they come to about 3.96 billion dollars.
This folder is what is underneath that number.

## Result

**One venue is 97.9% of it.**

| venue | open interest | markets carrying any |
|---|---:|---|
| XYZ | $3,873,867,536 | 108 / 123 |
| EntropyIO | $57,939,888 | 8 / 10 |
| Paragon | $18,363,030 | 27 / 36 |
| Markets By Kinetiq | $6,575,109 | 4 / 24 |
| Felix Exchange | **$0** | 0 / 16 |
| Ventuals | **$0** | 0 / 15 |
| HyENA | **$0** | 0 / 25 |
| Markets by Kinetiq *(second listing)* | **$0** | 0 / 23 |
| dreamcash | **$0** | 0 / 17 |
| ABCDEx | **$0** | 0 / 1 |

**Six venues, 97 markets, zero open interest and zero 24-hour volume.** Both fields,
every market, not a rounding.

Those six are where the names are. Ventuals lists SPACEX, OPENAI, ANTHROPIC, MAG7,
NUCLEAR, DEFENSE, BIOTECH, WHEAT. Felix lists TSLA, NVDA, COIN, CRCL, PALLADIUM,
PLATINUM. dreamcash lists TSLA, NVDA, HOOD, GOOGL, AMZN, MSFT, META. Kinetiq lists
BABA, TENCENT, XIAOMI, JPN225, USBOND, RTX, PLTR.

You can open a position on any of them. You would be the first.

XYZ, the one that works, runs a real book: SP500 11.2%, GOLD 7.6%, crude oil, silver,
NVDA, INTC — an index, a semiconductor, two metals and two grades of oil in the top nine.

## The aggregator disagrees with itself

`api.llama.fi/overview/open-interest` returns a headline of **$16,430,331,184**. Summing
the 129 protocols in the same response gives **$20,772,007,072** — a gap of $4.34bn.

By the provider's own `category` field:

| category | open interest | protocols |
|---|---:|---|
| Derivatives | $14,621,699,345 | 104 |
| Interface | $4,015,080,225 | 15 |
| Prediction Market | $1,951,578,267 | 7 |
| Interest Rate Derivatives | $183,649,235 | 2 |

The headline is everything except `Interface`. Those ten Hyperliquid venues are most of
what `Interface` is, and they are not interfaces — they are separate markets with their
own books. That single classification is most of the difference between $16bn and the
$19bn in the post.

Going the other way: **$1.95bn of the headline, 11.9%, is prediction markets** — Kalshi,
Polymarket US, Polymarket International. Election and sports contracts inside a figure
described as perpetual DEX open interest. And 36 of the 129 protocols report zero.

## What had to be withdrawn

**The first version of this measurement was wrong and said the claim was false.**

`{"type":"metaAndAssetCtxs"}` returns Hyperliquid's core market list: 234 markets, and
the only real-world asset in any of them is $20,334,433 of tokenised gold — 0.147%. The
one ticker that looks like an index, SPX, marks at $0.52, because it is SPX6900, a
memecoin.

All true, and all beside the point. That call does not return markets other people
deploy on the same chain. `{"type":"perpDexs"}` does, and there are ten of them holding
$3.96bn. Ask a venue what venues exist before assuming the first list is the last.

## What this does not establish

It does not show the six empty venues are abandoned. Several are new, and this is one
reading on one day.

It does not explain why XYZ has all of it. Concentration is measured; its cause is not.

The 6% figure for January 2026 is not checked. Every figure here is 2026-09-21.

Every non-Hyperliquid venue is taken from DefiLlama as reported and not independently
verified. Whether each venue counts open interest one-sided or two-sided is not checked
either — the concentration figures are ratios inside one venue's own reporting, so that
question does not touch them.

## Reproduce

```
python3 fetch.py      # only to re-read the venues; open interest moves by the minute
python3 analyze.py    # offline, from the committed capture
```
