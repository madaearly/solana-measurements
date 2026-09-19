#!/usr/bin/env python3
"""
Who is allowed to change the transfer fee, across one platform's Token-2022 mints.

Population: every distinct Token-2022 mint that wallet 5KXDF6...K6tD holds a token
account for, read from getTokenAccountsByOwner on 2026-09-18 (18,819 of them). That is
a convenience population, not the platform's full catalogue, and the README says so.

For each sampled mint we read transferFeeConfig and record who holds
transferFeeConfigAuthority. Nothing here is derived; every field is on the mint.

    python3 fetch.py --n 3000
"""
import argparse, json, os, random, time, urllib.request

RPC = "https://api.mainnet-beta.solana.com"
AUTH = "5KXDF6QnqhBj72hDtJNkkpFaQVUfbFXNybMsp3DiK6tD"


def rpc(method, params, tries=8, wait=6):
    for _ in range(tries):
        try:
            req = urllib.request.Request(
                RPC, data=json.dumps({"jsonrpc": "2.0", "id": 1,
                                      "method": method, "params": params}).encode(),
                headers={"Content-Type": "application/json"})
            d = json.load(urllib.request.urlopen(req, timeout=60))
            if "result" in d:
                return d["result"]
        except Exception:
            pass
        time.sleep(wait)
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=3000)
    ap.add_argument("--mints", default="data/population.txt")
    ap.add_argument("--seed", type=int, default=20260919)
    a = ap.parse_args()
    pop = [l.strip() for l in open(a.mints) if l.strip()]
    random.seed(a.seed)
    sample = random.sample(pop, min(a.n, len(pop)))
    out = {}
    path = "data/sample.json"
    if os.path.exists(path):
        out = json.load(open(path))
    todo = [m for m in sample if m not in out]
    print(f"population {len(pop):,} · sample {len(sample):,} · already have {len(out):,} · to fetch {len(todo):,}")
    for i in range(0, len(todo), 100):
        chunk = todo[i:i + 100]
        r = rpc("getMultipleAccounts", [chunk, {"encoding": "jsonParsed"}])
        if not r:
            print(f"  batch {i} unreadable, skipped")
            continue
        for mint, acc in zip(chunk, r["value"]):
            if not acc:
                continue
            info = acc["data"]["parsed"]["info"]
            rec = {"decimals": info.get("decimals"), "supply": info.get("supply"),
                   "mintAuthority": info.get("mintAuthority"),
                   "freezeAuthority": info.get("freezeAuthority"),
                   "fee_bps": None, "fee_authority": None, "withdraw_authority": None,
                   "withheld": None, "symbol": None}
            for e in info.get("extensions", []):
                if e["extension"] == "transferFeeConfig":
                    s = e["state"]
                    rec["fee_bps"] = s["newerTransferFee"]["transferFeeBasisPoints"]
                    rec["fee_authority"] = s["transferFeeConfigAuthority"]
                    rec["withdraw_authority"] = s["withdrawWithheldAuthority"]
                    rec["withheld"] = s.get("withheldAmount")
                if e["extension"] == "tokenMetadata":
                    rec["symbol"] = e["state"].get("symbol")
            out[mint] = rec
        json.dump(out, open(path, "w"))
        print(f"  {len(out):,}/{len(sample):,}", flush=True)
        time.sleep(2)
    json.dump(out, open(path, "w"))
    print("wrote", path)


if __name__ == "__main__":
    main()
