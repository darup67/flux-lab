"""Smart Money Concepts engine — mirrors pine/flux_smc.pine."""
import json
import urllib.request


def fetch_bars(symbol, interval="1h", rng="1mo"):
    url = ("https://query1.finance.yahoo.com/v8/finance/chart/%s?interval=%s&range=%s"
           % (symbol, interval, rng))
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    res = json.load(urllib.request.urlopen(req, timeout=20))["chart"]["result"][0]
    q = res["indicators"]["quote"][0]
    bars = []
    for i, t in enumerate(res.get("timestamp", [])):
        o, h, l, c = q["open"][i], q["high"][i], q["low"][i], q["close"][i]
        if None in (o, h, l, c):
            continue
        bars.append({"time": t, "open": o, "high": h, "low": l, "close": c})
    return bars


def atr(bars, n=14):
    out, prev = [], None
    for i, b in enumerate(bars):
        pc = bars[i - 1]["close"] if i else b["close"]
        tr = max(b["high"] - b["low"], abs(b["high"] - pc), abs(b["low"] - pc))
        prev = tr if prev is None else (prev * (n - 1) + tr) / n
        out.append(prev)
    return out


def analyze(bars, swing=5, fvg_min_atr=0.2, eq_tol_atr=0.1, ob_max=5):
    a = atr(bars)
    ev = {"structure": [], "fvg": [], "eq": [], "signals": []}
    bull_obs, bear_obs = [], []
    last_hi = last_lo = None
    hi_broken = lo_broken = True
    trend = 0
    for i in range(len(bars)):
        b = bars[i]
        p = i - swing  # confirmed pivot index
        if p >= swing:
            win = bars[p - swing:i + 1]
            if bars[p]["high"] == max(x["high"] for x in win):
                if last_hi and abs(bars[p]["high"] - last_hi[1]) <= eq_tol_atr * a[i]:
                    ev["eq"].append({"time": bars[p]["time"], "price": bars[p]["high"], "kind": "EQH"})
                last_hi, hi_broken = (p, bars[p]["high"]), False
            if bars[p]["low"] == min(x["low"] for x in win):
                if last_lo and abs(bars[p]["low"] - last_lo[1]) <= eq_tol_atr * a[i]:
                    ev["eq"].append({"time": bars[p]["time"], "price": bars[p]["low"], "kind": "EQL"})
                last_lo, lo_broken = (p, bars[p]["low"]), False

        for side, lvl, broken in (("bull", last_hi, hi_broken), ("bear", last_lo, lo_broken)):
            if broken or not lvl:
                continue
            if (side == "bull" and b["close"] > lvl[1]) or (side == "bear" and b["close"] < lvl[1]):
                want = 1 if side == "bull" else -1
                ev["structure"].append({"time": b["time"], "price": lvl[1], "side": side,
                                        "kind": "CHoCH" if trend == -want else "BOS",
                                        "from": bars[lvl[0]]["time"]})
                trend = want
                obs = bull_obs if side == "bull" else bear_obs
                for k in range(i - 1, lvl[0] - 1, -1):  # last opposite candle
                    c = bars[k]
                    if (side == "bull" and c["close"] < c["open"]) or (side == "bear" and c["close"] > c["open"]):
                        obs.append({"time": c["time"], "top": c["high"], "bottom": c["low"], "side": side})
                        del obs[:-ob_max]
                        break
                if side == "bull":
                    hi_broken = True
                else:
                    lo_broken = True

        bull_obs[:] = [o for o in bull_obs if b["close"] >= o["bottom"]]
        bear_obs[:] = [o for o in bear_obs if b["close"] <= o["top"]]
        bull_touch = any(b["low"] <= o["top"] for o in bull_obs)
        bear_touch = any(b["high"] >= o["bottom"] for o in bear_obs)

        if i >= 2:
            if b["low"] > bars[i - 2]["high"] and b["low"] - bars[i - 2]["high"] >= fvg_min_atr * a[i]:
                ev["fvg"].append({"time": bars[i - 2]["time"], "top": b["low"], "bottom": bars[i - 2]["high"], "side": "bull"})
            if b["high"] < bars[i - 2]["low"] and bars[i - 2]["low"] - b["high"] >= fvg_min_atr * a[i]:
                ev["fvg"].append({"time": bars[i - 2]["time"], "top": bars[i - 2]["low"], "bottom": b["high"], "side": "bear"})

        win = bars[max(0, i - 99):i + 1]
        eq = (max(x["high"] for x in win) + min(x["low"] for x in win)) / 2
        if trend == 1 and bull_touch and b["close"] < eq and b["close"] > b["open"]:
            ev["signals"].append({"time": b["time"], "price": b["close"], "side": "BUY", "i": i})
        if trend == -1 and bear_touch and b["close"] > eq and b["close"] < b["open"]:
            ev["signals"].append({"time": b["time"], "price": b["close"], "side": "SELL", "i": i})

    ev["order_blocks"] = bull_obs + bear_obs
    ev["trend"] = {1: "bullish", -1: "bearish", 0: "neutral"}[trend]
    ev["equilibrium"] = eq if bars else None
    return ev


def backtest(bars, signals, rr=2.0, atr_stop=1.5):
    """Each signal: stop = atr_stop*ATR, target = rr*stop. Returns stats."""
    a = atr(bars)
    wins = losses = 0
    pnl_r = 0.0
    for s in signals:
        i, entry = s["i"], s["price"]
        risk = atr_stop * a[i]
        d = 1 if s["side"] == "BUY" else -1
        stop, tgt = entry - d * risk, entry + d * rr * risk
        for b in bars[i + 1:]:
            if (d == 1 and b["low"] <= stop) or (d == -1 and b["high"] >= stop):
                losses += 1; pnl_r -= 1; break
            if (d == 1 and b["high"] >= tgt) or (d == -1 and b["low"] <= tgt):
                wins += 1; pnl_r += rr; break
    n = wins + losses
    return {"trades": n, "wins": wins, "win_rate": round(wins / n, 3) if n else None,
            "net_R": round(pnl_r, 2)}
