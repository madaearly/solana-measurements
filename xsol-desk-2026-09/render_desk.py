#!/usr/bin/env python3
"""
The desk: many small panels on one clock, every number fetched rather than invented.

The format is borrowed from a genre of simulated trading-desk clips; the contents
are not. In those, the cast is fictional, the balance curve is drawn and the
confidence figure exists to look like a confidence figure. Here the cast is real
wallet addresses, the curve is real OHLCV, and any panel we could not source
honestly was dropped instead of filled.

One clock drives everything, exactly as in the reference: the run replays a real
capture window at a stated compression, and each panel shows what had happened by
the current instant. Nothing on screen runs ahead of the data.

    .venv/bin/python lib/huddesk.py data/<id>-desk.json --out out/<id>.mp4 [--probe 12]
"""
import argparse, json, math, os, subprocess, sys, tempfile
from datetime import datetime

from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from draw import SS, Pen, F, palette

W, H, M = 1080, 1350, 40


def iso(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def human(v, dollar=True):
    if v is None:
        return "—"
    p = "$" if dollar else ""
    a = abs(v)
    if a >= 1e9: return f"{p}{v/1e9:.2f}bn"
    if a >= 1e6: return f"{p}{v/1e6:.2f}m"
    if a >= 1e3: return f"{p}{v/1e3:.1f}k"
    return f"{p}{v:,.0f}"


def short(w, n=5):
    return f"{w[:n]}…{w[-4:]}" if w else "—"


class Desk:
    def __init__(self, data, P):
        self.d = data
        self.P = P
        self.trades = data["trades"]
        self.t0 = iso(self.trades[0]["ts"])
        self.t1 = iso(self.trades[-1]["ts"])
        self.span = max(1.0, (self.t1 - self.t0).total_seconds())
        # wallets ranked over the whole window; the roster keeps a stable order so
        # a viewer can watch one cell rather than a list reshuffling every frame
        self.roster = data["wallets"][:10]
        self.roster_idx = {w["w"]: i for i, w in enumerate(self.roster)}
        self.ohlcv = data.get("ohlcv") or []
        if self.ohlcv:
            cs = [c[4] for c in self.ohlcv]
            self.lo, self.hi = min(cs), max(cs)
            self.ospan = max(1e-12, self.hi - self.lo)

    # -- state at a given point of the replay ---------------------------------
    def at(self, frac):
        now = self.t0.timestamp() + self.span * frac
        seen = [t for t in self.trades if iso(t["ts"]).timestamp() <= now]
        buy = sum(t["usd"] for t in seen if t["side"] == "buy")
        sell = sum(t["usd"] for t in seen if t["side"] == "sell")
        wallets = {}
        for t in seen:
            a = wallets.setdefault(t["wallet"], {"n": 0, "buy": 0.0, "sell": 0.0})
            a["n"] += 1
            a["buy" if t["side"] == "buy" else "sell"] += t["usd"]
        return {"now": now, "seen": seen, "buy": buy, "sell": sell, "wallets": wallets,
                "last": seen[-1] if seen else None}

    # -- panels ---------------------------------------------------------------
    def _card(self, p, box, title, right=None):
        x0, y0, x1, y1 = box
        p.rect((x0, y0, x1, y1), outline=self.P["HAIR"])
        p.text((x0 + 12, y0 + 9), title, F(11, True), self.P["DIM"])
        if right:
            p.text((x1 - 12, y0 + 9), right, F(10), self.P["BORDER"], anchor="rt")

    def bignums(self, p, y, s):
        P = self.P
        cells = [
            ("TRADES REPLAYED", f"{len(s['seen'])}", "SECOND", f"OF {len(self.trades)}"),
            ("WALLETS SEEN", f"{len(s['wallets'])}", "COUNTER", f"OF {self.d['totals']['wallets']}"),
            ("BOUGHT", human(s["buy"]), "COUNTER", "USD, THIS WINDOW"),
            ("SOLD", human(s["sell"]), "ACCENT", "USD, THIS WINDOW"),
        ]
        cw = (W - 2 * M - 3 * 8) / 4
        for i, (lab, val, col, sub) in enumerate(cells):
            x = M + i * (cw + 8)
            p.rect((x, y, x + cw, y + 92), outline=P["HAIR"])
            p.text((x + 12, y + 10), lab, F(10), P["DIM"])
            p.text((x + 12, y + 30), val, F(30, True), P[col])
            p.text((x + 12, y + 70), sub, F(9), P["BORDER"])

    def chart(self, p, box, frac):
        P = self.P
        x0, y0, x1, y1 = box
        self._card(p, box, "PRICE / 5m CANDLES", self.d.get("ohlcv_pool", ""))
        if not self.ohlcv:
            return
        gx0, gx1 = x0 + 46, x1 - 14
        gy0, gy1 = y0 + 34, y1 - 24
        n = len(self.ohlcv)
        k = max(2, int(n * frac))
        pts = []
        for i in range(k):
            c = self.ohlcv[i][4]
            pts.append((gx0 + (gx1 - gx0) * i / (n - 1),
                        gy1 - (c - self.lo) / self.ospan * (gy1 - gy0)))
        for gv, lab in ((self.hi, f"{self.hi:.5f}"), (self.lo, f"{self.lo:.5f}")):
            yy = gy1 - (gv - self.lo) / self.ospan * (gy1 - gy0)
            p.dashed((gx0, yy), (gx1, yy), P["HAIR"], 1, 7, 6)
            p.text((gx0 - 8, yy - 7), lab, F(9), P["BORDER"], anchor="rt")
        if len(pts) > 1:
            p.line(pts, P["COUNTER"], 2)
            p.dot(pts[-1], 3.5, P["BRIGHT"])
            p.text((pts[-1][0] + 8, pts[-1][1] - 8), f"{self.ohlcv[k-1][4]:.5f}",
                   F(11, True), P["BRIGHT"])

    def log(self, p, box, s):
        P = self.P
        x0, y0, x1, y1 = box
        self._card(p, box, "TRADE LOG", f"{len(self.trades)} OBSERVED")
        # rows are fitted to the panel rather than fixed: a count that outgrew its
        # box was writing the last line over the panel below it
        cap = max(3, int((y1 - y0 - 44) // 18))
        rows = s["seen"][-cap:][::-1]
        y = y0 + 34
        for i, t in enumerate(rows):
            col = P["COUNTER"] if t["side"] == "buy" else P["ACCENT"]
            fade = 1.0 if i == 0 else 0.55
            mix = lambda c: tuple(int(P["BG"][j] + (c[j] - P["BG"][j]) * fade) for j in range(3))
            p.text((x0 + 12, y), iso(t["ts"]).strftime("%H:%M"), F(10), mix(P["DIM"]))
            p.text((x0 + 58, y), t["side"].upper(), F(10, True), mix(col))
            p.text((x0 + 104, y), f"${t['usd']:,.0f}", F(10, True), mix(P["SECOND"]))
            p.text((x0 + 186, y), short(t["wallet"], 4), F(10), mix(P["DIM"]))
            p.text((x1 - 12, y), t["pool"].split(" / ")[-1], F(9), mix(P["BORDER"]), anchor="rt")
            y += 18

    def roster_panel(self, p, box, s):
        """The cast. Ten real addresses instead of ten invented names."""
        P = self.P
        x0, y0, x1, y1 = box
        self._card(p, box, "MOST ACTIVE WALLETS",
                   f"{self.d['totals']['wallets']} SEEN IN WINDOW")
        cols, rows = 5, 2
        cw = (x1 - x0 - 24 - (cols - 1) * 8) / cols
        ch = (y1 - y0 - 44 - 8) / rows
        for i, w in enumerate(self.roster):
            cx = x0 + 12 + (i % cols) * (cw + 8)
            cy = y0 + 34 + (i // cols) * (ch + 8)
            live = s["wallets"].get(w["w"])
            net = (live["buy"] - live["sell"]) if live else 0.0
            acting = live is not None
            edge = P["BORDER"] if not acting else (P["COUNTER_DIM"] if net >= 0 else P["ACCENT_DIM"])
            p.rect((cx, cy, cx + cw, cy + ch), outline=edge)
            p.text((cx + 8, cy + 7), short(w["w"], 4), F(11, True),
                   P["SECOND"] if acting else P["BORDER"])
            if acting:
                p.text((cx + 8, cy + 27), f"{live['n']}",
                       F(22, True), P["COUNTER"] if net >= 0 else P["ACCENT"])
                p.text((cx + 8, cy + 55), "TRADES", F(8), P["BORDER"])
                p.text((cx + cw - 8, cy + 30), human(net), F(11, True),
                       P["COUNTER"] if net >= 0 else P["ACCENT"], anchor="rt")
                p.text((cx + cw - 8, cy + 48),
                       "ACCUMULATING" if net > 0 else "DISTRIBUTING", F(8),
                       P["DIM"], anchor="rt")
            else:
                p.text((cx + 8, cy + 30), "—", F(22, True), P["BORDER"])
                p.text((cx + 8, cy + 56), "NOT YET", F(8), P["BORDER"])

    def pools(self, p, box):
        P = self.P
        x0, y0, x1, y1 = box
        t = self.d["totals"]
        self._card(p, box, "POOLS THE FLOW IS SPREAD ACROSS",
                   f"{t['poolsTraded']} OF {t['poolsTotal']} TRADED")
        rows = sorted(self.d["pools"], key=lambda q: -(q["volume24"] or 0))[:6]
        vmax = max(q["volume24"] or 0 for q in rows) or 1
        y = y0 + 36
        for q in rows:
            p.text((x0 + 12, y), q["name"][:22], F(11, True), P["SECOND"])
            bx0, bx1 = x0 + 200, x1 - 150
            bw = (bx1 - bx0) * math.sqrt((q["volume24"] or 0) / vmax)
            p.rect((bx0, y + 2, bx0 + max(1, bw), y + 11), fill=P["COUNTER_DIM"])
            p.text((x1 - 12, y - 1), human(q["volume24"]), F(11, True), P["COUNTER"], anchor="rt")
            p.text((x1 - 96, y + 1), f"{q['buyers'] or 0}/{q['sellers'] or 0}", F(9),
                   P["DIM"], anchor="rt")
            y += 22

    def sizes(self, p, box, s):
        """Trade size distribution, log-binned. The honest stand-in for the
        reference's decorative probability ridge: same visual job, real counts."""
        P = self.P
        x0, y0, x1, y1 = box
        dd = self.d.get("distribution")
        self._card(p, box, "TRADE SIZE / LOG BINS",
                   f"MEDIAN ${dd['median']:,.0f}  ·  MEAN ${dd['mean']:,.0f}")
        if not dd:
            return
        b = dd["buckets"]
        nmax = max(q["n"] for q in b) or 1
        bw = (x1 - x0 - 28) / len(b)
        base = y1 - 46
        for i, q in enumerate(b):
            hgt = (base - y0 - 52) * (q["n"] / nmax)
            bx = x0 + 14 + i * bw
            col = P["ACCENT"] if q["hi"] <= 1 else P["COUNTER_DIM"]
            p.rect((bx + 2, base - hgt, bx + bw - 4, base), fill=col)
            p.text((bx + bw / 2, base + 4), f"{q['lo']:g}", F(8), P["BORDER"], anchor="mt")
            if q["n"]:
                p.text((bx + bw / 2, base - hgt - 13), str(q["n"]), F(9, True),
                       P["SECOND"], anchor="mt")
        p.text((x0 + 14, y1 - 17),
               f"{dd['under1']} TRADES UNDER $1  ·  TOP 1% CARRY {dd['top_share']['1']}% OF VOLUME",
               F(10, True), P["ACCENT"])

    def concentration(self, p, box):
        """Who the volume actually belongs to. This replaces the reference's
        confidence score, which was a number shaped like evidence."""
        P = self.P
        c = self.d.get("concentration")
        x0, y0, x1, y1 = box
        self._card(p, box, "VOLUME BY WALLET RANK", f"{c['wallets']} WALLETS")
        if not c:
            return
        ks = [1, 5, 10, 25, 50]
        y = y0 + 36
        for k in ks:
            share = c["top"][str(k)]
            p.text((x0 + 14, y), f"TOP {k}", F(11, True), P["DIM"])
            bx0, bx1 = x0 + 90, x1 - 78
            p.rect((bx0, y + 1, bx0 + (bx1 - bx0) * share / 100, y + 11), fill=P["COUNTER_DIM"])
            p.rect((bx0, y + 1, bx1, y + 11), outline=P["HAIR"])
            p.text((x1 - 14, y - 2), f"{share:.1f}%", F(12, True), P["COUNTER"], anchor="rt")
            y += 22
        pc = 100 * c["once"] / max(1, c["wallets"])
        p.text((x0 + 14, y1 - 13), f"{c['once']} OF {c['wallets']} WALLETS TRADED ONCE  ({pc:.0f}%)",
               F(10, True), P["ACCENT"])

    def turnover(self, p, box):
        """Volume against the depth behind it, per pool. A pool that turns over a
        fraction of a percent in a day is reporting arithmetic, not money."""
        P = self.P
        x0, y0, x1, y1 = box
        self._card(p, box, "TURNOVER / 24h VOLUME OVER POOL DEPTH", "ALL POOLS")
        rows = sorted([q for q in self.d["pools"] if q["turnover"] is not None],
                      key=lambda q: -q["turnover"])[:6]
        tmax = max(q["turnover"] for q in rows) or 1
        y = y0 + 36
        for q in rows:
            hot = q["turnover"] > 10
            p.text((x0 + 12, y), q["name"][:20], F(11, True),
                   P["ACCENT"] if hot else P["SECOND"])
            bx0, bx1 = x0 + 190, x1 - 160
            bw = (bx1 - bx0) * math.sqrt(q["turnover"] / tmax)
            p.rect((bx0, y + 2, bx0 + max(1, bw), y + 11), fill=P["ACCENT_DIM"] if hot else P["COUNTER_DIM"])
            p.text((x1 - 100, y), f"{human(q['liquidity'])}", F(10), P["DIM"], anchor="rt")
            p.text((x1 - 12, y - 1), f"{q['turnover']:.1f}x", F(12, True),
                   P["ACCENT"] if hot else P["COUNTER"], anchor="rt")
            y += 22

    def flow(self, p, box, s):
        """Buy against sell, at this instant of the replay, on one shared bar."""
        P = self.P
        x0, y0, x1, y1 = box
        tot = s["buy"] + s["sell"]
        imb = (s["buy"] - s["sell"]) / tot if tot else 0
        p.text((x0, y0), "FLOW BALANCE, SO FAR", F(11, True), P["DIM"])
        bx0, bx1 = x0, x1
        mid = bx0 + (bx1 - bx0) * (s["buy"] / tot if tot else 0.5)
        p.rect((bx0, y0 + 22, mid, y0 + 38), fill=P["COUNTER_DIM"])
        p.rect((mid, y0 + 22, bx1, y0 + 38), fill=P["ACCENT_DIM"])
        p.line([(mid, y0 + 16), (mid, y0 + 44)], P["BRIGHT"], 2)
        p.text((bx0, y0 + 46), f"BUY {human(s['buy'])}", F(10, True), P["COUNTER"])
        p.text((bx1, y0 + 46), f"SELL {human(s['sell'])}", F(10, True), P["ACCENT"], anchor="rt")
        p.text(((bx0 + bx1) / 2, y0 + 46), f"{imb:+.3f}", F(11, True),
               P["BRIGHT"], anchor="mt")

    # -- the frame ------------------------------------------------------------
    def frame(self, frac):
        P = self.P
        d = self.d
        img = Image.new("RGB", (W * SS, H * SS), P["BG"])
        p = Pen(ImageDraw.Draw(img))
        s = self.at(frac)
        now = datetime.fromtimestamp(s["now"], tz=self.t0.tzinfo)

        p.text((M, 26), d["eyebrow"], F(13), P["DIM"])
        bw = p.d.textlength(d["badge"], font=F(13, True)) / SS + 24
        p.rect((W - M - bw, 20, W - M, 46), outline=P["ACCENT_DIM"])
        p.text((W - M - bw / 2, 26), d["badge"], F(13, True), P["ACCENT"], anchor="mt")

        sym = d["token"]["symbol"] or "—"
        p.text((M, 58), f"{sym} DESK", F(34, True), P["BRIGHT"])
        tw = p.d.textlength(f"{sym} DESK", font=F(34, True)) / SS
        p.text((M + tw + 16, 72), d["token"]["address"], F(11), P["BORDER"])
        p.text((W - M, 62), now.strftime("%H:%M UTC"), F(24, True), P["COUNTER"], anchor="rt")
        wd = d.get("window", {})
        axis = "COMMON WINDOW" if wd.get("axis_valid") else "AXIS NOT VALID"
        p.text((W - M, 92), f"{axis} {wd.get('hours', '?')}h ACROSS {wd.get('pools','?')} POOLS"
                            f"  ·  CAPTURED {d['captured_at'][:16].replace('T',' ')}Z",
               F(9), P["DIM"] if wd.get("axis_valid") else P["ACCENT"], anchor="rt")
        p.rect((M, 116, W - M, 118), fill=P["HAIR"])

        self.bignums(p, 130, s)
        self.chart(p, (M, 236, 640, 424), frac)
        self.log(p, (652, 236, W - M, 424), s)
        self.roster_panel(p, (M, 438, W - M, 636), s)
        self.sizes(p, (M, 650, 556, 818), s)
        self.concentration(p, (568, 650, W - M, 818))
        self.turnover(p, (M, 832, W - M, 990))
        self.flow(p, (M, 1004, W - M, 1060), s)

        pb = d["punch"]
        top = d.get("punch_y", 1090)
        p.line([(M + 18, top), (M + 18, top + 30 * len(pb))], P["ACCENT_DIM"], 2)
        for i, ln in enumerate(pb):
            p.text((M + 40, top + 2 + i * 30), ln["text"], F(ln["size"], True),
                   P[ln.get("color", "BRIGHT")])

        py = H - 62
        p.rect((M, py, W - M, py + 3), fill=P["HAIR"])
        p.rect((M, py, M + (W - 2 * M) * frac, py + 3), fill=P["ACCENT"])
        p.text((M, H - 34), d["handle"], F(17, True), P["BRIGHT"])
        p.text((W - M, H - 28), d["footer_right"], F(9), P["DIM"], anchor="rt")
        return img.resize((W, H), Image.LANCZOS)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("data")
    ap.add_argument("--out")
    ap.add_argument("--probe", type=float)
    ap.add_argument("--seconds", type=float, default=24.0)
    ap.add_argument("--fps", type=int, default=30)
    a = ap.parse_args()
    d = json.load(open(a.data))
    desk = Desk(d, palette(d.get("palette")))
    if a.probe is not None:
        desk.frame(a.probe).save(a.out)
        print("wrote", a.out)
        return
    n = int(a.seconds * a.fps)
    tmp = tempfile.mkdtemp(prefix="huddesk-")
    for i in range(n):
        desk.frame(i / (n - 1)).save(f"{tmp}/{i:05d}.png")
        if i % 120 == 0:
            print(f"  {i}/{n}", flush=True)
    os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-framerate", str(a.fps),
                    "-i", f"{tmp}/%05d.png", "-c:v", "libx264", "-profile:v", "high",
                    "-pix_fmt", "yuv420p", "-crf", "18", "-map_metadata", "-1",
                    "-fflags", "+bitexact", "-flags:v", "+bitexact",
                    "-bsf:v", "filter_units=remove_types=6",
                    "-movflags", "+faststart", a.out], check=True)
    print("wrote", a.out)


if __name__ == "__main__":
    main()
