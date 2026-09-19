# Who may change a transfer fee — 2026-09-19

Token-2022 lets a mint carry a transfer fee. Two separate keys govern it:
`withdrawWithheldAuthority` takes what the fee collects, and `transferFeeConfigAuthority`
sets the rate. When the second is `null`, the rate is frozen forever. When it is an
address, that address decides.

On 2026-09-14 this account published seven mints where four had a live authority and it
was the same wallet on all four. On 2026-09-18 it published six more, again the same
wallet. This folder asks the question those two posts left open: **how common is that?**

## Population, and why it is not the whole story

`data/population.txt` — the 18,819 distinct Token-2022 mints that
`5KXDF6QnqhBj72hDtJNkkpFaQVUfbFXNybMsp3DiK6tD` holds a token account for, read with
`getTokenAccountsByOwner` on 2026-09-18.

**This is a convenience population and it is selected.** These are mints that wallet has
touched, so they are weighted toward one platform's output. Nothing here describes
Solana as a whole, or even that platform's full catalogue. Every percentage below is a
percentage *of this population*.

## Sample

`fetch.py --n 3000`, seed 20260919, `random.sample` without replacement. 3,000 of 18,819,
read with `getMultipleAccounts`, `jsonParsed`. Raw result in `data/sample.json` so every
figure re-derives offline with `analyze.py` and no network.

## Result

| who may change the fee | mints | share | 95% (Wilson) |
|---|---:|---:|---|
| a program-derived address, `WLHv2U…JVVh` | 2,043 | 68.10% | 66.41–69.74% |
| `null` — frozen forever | 648 | 21.60% | 20.16–23.11% |
| the keypair `5KXDF6…K6tD` | 265 | 8.83% | 7.87–9.90% |
| no transfer fee at all | 44 | 1.47% | 1.09–1.96% |

**89.7% cannot have the rate changed by any private key.** 8.83% can, and across all
3,000 mints that was the only private key that appeared — the "some other address"
bucket is empty.

Extrapolated to the population: roughly 1,662 mints (1,481–1,863).

Two fee rates exist in the whole sample and no others: 100 bps (48.5%) and 300 bps
(51.5%). Among the 265 under the keypair the split is 161 / 104.

## The seven, re-read

`data/seven_recheck.json` — the mints from the 2026-09-14 thread, read again five days
later. All seven unchanged. The four live ones are LEVERCAT, LEVERDOG, SLO and LAMPORT;
LOOOONG and SOLDIERS are frozen; LEVERPUP has no fee.

## What this does not show

It does not show anyone changing a fee. Every mint read the same on both dates.

It does not show who holds the key.

It does not generalise past the population above, which is the main limitation and is
not fixable by a larger sample of the same list.

## Reproduce

```
python3 fetch.py --n 3000      # only if you want to re-read the chain
python3 analyze.py             # offline, from the committed sample
```
