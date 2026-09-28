# Flux Lab

A Smart Money Concepts toolkit modeled on FluxCharts, with TradingView as the reference platform.

- `pine/flux_smc.pine`: TradingView indicator (Pine v5). It marks BOS/CHoCH, order blocks (removed once broken), fair value gaps, EQH/EQL, the premium/discount equilibrium line, BUY/SELL signals and alert conditions.
- `flux/smc.py`: a Python version of the same logic, plus a simple R-multiple backtest (1.5×ATR stop, 2R target).
- `agent.py`: read-only watchlist scanner. It never places orders.

```
python3 agent.py scan            # scan watchlist.json -> table + out/report.json
python3 agent.py scan --html     # + out/<SYM>.html lightweight-charts pages
python3 agent.py chart NVDA --interval 15m --range 5d
```

It uses only the Python standard library (3.7+). Data comes from Yahoo's chart endpoint.
Signal rule: trend (last BOS/CHoCH) + a retest of an order block + price in the discount zone (premium for sells) + a candle closing in the signal's direction.
