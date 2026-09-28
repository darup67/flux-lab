#!/usr/bin/env python3
"""Flux Lab agent — scans a watchlist with the SMC engine (read-only, no orders).

  python3 agent.py scan                      # watchlist.json, table + JSON report
  python3 agent.py scan --html               # also write out/<SYM>.html charts
  python3 agent.py chart NVDA --interval 15m --range 5d
"""
import argparse
import json
import os
import time

from flux.smc import fetch_bars, analyze, backtest
from flux.chart import render

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "out")


def run(sym, interval, rng, html):
    bars = fetch_bars(sym, interval, rng)
    ev = analyze(bars)
    bt = backtest(bars, ev["signals"])
    last = bars[-1]
    recent = [s for s in ev["signals"] if s["i"] >= len(bars) - 3]
    struct = ev["structure"][-1] if ev["structure"] else None
    if html:
        render(os.path.join(OUT, "%s.html" % sym.replace("=", "_")), sym, interval, bars, ev, bt)
    return {"symbol": sym, "close": round(last["close"], 4), "trend": ev["trend"],
            "last_structure": struct and "%s %s" % (struct["side"], struct["kind"]),
            "active_obs": len(ev["order_blocks"]),
            "signal_now": recent[-1]["side"] if recent else None,
            "premium" if last["close"] > ev["equilibrium"] else "discount": True,
            "backtest": bt}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["scan", "chart"])
    ap.add_argument("symbol", nargs="?")
    ap.add_argument("--interval", default=None)
    ap.add_argument("--range", default=None)
    ap.add_argument("--html", action="store_true")
    a = ap.parse_args()
    cfg = json.load(open(os.path.join(ROOT, "watchlist.json")))
    interval, rng = a.interval or cfg["interval"], a.range or cfg["range"]
    os.makedirs(OUT, exist_ok=True)

    syms = [a.symbol] if a.cmd == "chart" else cfg["symbols"]
    rows = []
    for s in syms:
        try:
            rows.append(run(s, interval, rng, a.html or a.cmd == "chart"))
        except Exception as e:
            rows.append({"symbol": s, "error": str(e)})
    print("%-10s %10s %-8s %-14s %-6s %s" % ("SYMBOL", "CLOSE", "TREND", "STRUCTURE", "SIGNAL", "BACKTEST"))
    for r in rows:
        if "error" in r:
            print("%-10s ERROR %s" % (r["symbol"], r["error"])); continue
        bt = r["backtest"]
        print("%-10s %10s %-8s %-14s %-6s %s trades, win %s, %sR" % (
            r["symbol"], r["close"], r["trend"], r["last_structure"] or "-", r["signal_now"] or "-",
            bt["trades"], bt["win_rate"], bt["net_R"]))
    with open(os.path.join(OUT, "report.json"), "w") as f:
        json.dump({"generated": time.strftime("%Y-%m-%d %H:%M"), "interval": interval, "rows": rows}, f, indent=1)
    if a.cmd == "chart":
        print("chart -> out/%s.html" % a.symbol.replace("=", "_"))


if __name__ == "__main__":
    main()
