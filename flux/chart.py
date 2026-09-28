"""Render an interactive TradingView lightweight-charts HTML page."""
import json

TEMPLATE = """<!doctype html><html><head><meta charset="utf-8"><title>Flux Lab %(sym)s</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<script src="https://cdn.jsdelivr.net/npm/lightweight-charts@4.2.0/dist/lightweight-charts.standalone.production.js"></script>
<style>body{margin:0;background:#131722;color:#d1d4dc;font:14px system-ui}#h{padding:10px 16px}#c{height:calc(100vh - 50px)}</style>
</head><body><div id="h"><b>%(sym)s</b> %(interval)s · trend <b>%(trend)s</b> · %(bt)s</div><div id="c"></div>
<script>
const bars=%(bars)s, ev=%(ev)s;
const chart=LightweightCharts.createChart(document.getElementById('c'),{layout:{background:{color:'#131722'},textColor:'#d1d4dc'},
 grid:{vertLines:{color:'#1e222d'},horzLines:{color:'#1e222d'}},timeScale:{timeVisible:true}});
const s=chart.addCandlestickSeries({upColor:'#089981',downColor:'#f23645',wickUpColor:'#089981',wickDownColor:'#f23645',borderVisible:false});
s.setData(bars);
const last=bars[bars.length-1].time;
function zone(z,col){[z.top,z.bottom].forEach(p=>{const l=chart.addLineSeries({color:col,lineWidth:1,priceLineVisible:false,lastValueVisible:false});
 l.setData([{time:z.time,value:p},{time:last,value:p}]);});}
ev.order_blocks.forEach(o=>zone(o,o.side=='bull'?'#089981':'#f23645'));
ev.fvg.slice(-6).forEach(f=>zone(f,f.side=='bull'?'rgba(8,153,129,.5)':'rgba(242,54,69,.5)'));
const m=[];
ev.structure.forEach(x=>m.push({time:x.time,position:x.side=='bull'?'aboveBar':'belowBar',color:x.side=='bull'?'#089981':'#f23645',shape:'circle',text:x.kind}));
ev.eq.forEach(x=>m.push({time:x.time,position:x.kind=='EQH'?'aboveBar':'belowBar',color:'#787b86',shape:'square',text:x.kind}));
ev.signals.forEach(x=>m.push({time:x.time,position:x.side=='BUY'?'belowBar':'aboveBar',color:x.side=='BUY'?'#089981':'#f23645',shape:x.side=='BUY'?'arrowUp':'arrowDown',text:x.side}));
m.sort((a,b)=>a.time-b.time);s.setMarkers(m);
if(ev.equilibrium)s.createPriceLine({price:ev.equilibrium,color:'#787b86',lineStyle:2,title:'EQ'});
chart.timeScale().fitContent();
</script></body></html>"""


def render(path, sym, interval, bars, ev, bt):
    bt_txt = "backtest: %s trades, win %s, %sR" % (bt["trades"], bt["win_rate"], bt["net_R"])
    with open(path, "w") as f:
        f.write(TEMPLATE % {"sym": sym, "interval": interval, "trend": ev["trend"], "bt": bt_txt,
                            "bars": json.dumps(bars), "ev": json.dumps(ev)})
