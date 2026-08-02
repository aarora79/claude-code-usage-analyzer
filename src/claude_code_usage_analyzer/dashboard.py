"""Generate a self-contained HTML tokenomics dashboard from an analysis result.

The output is a single HTML file with inline CSS and JavaScript and no external
dependencies (no CDN, web fonts, or chart libraries), so it opens anywhere and
can be emailed or archived as-is. Charts are hand-drawn SVG built in the browser
from a small JSON blob embedded in the page.

The visual design follows the data-viz method: a validated categorical palette,
mean baselines with mean +/- 2 sigma control limits, anomaly flagging, a table
view behind every chart (the relief rule), and a selected dark mode.
"""

import json
import logging
import statistics
from datetime import datetime
from typing import Any

from . import __version__

logger = logging.getLogger(__name__)


def _json_for_script_block(
    payload: Any,
) -> str:
    """Serialize a value as JSON that is safe to embed in an HTML script block.

    Escapes ``<``, ``>``, and ``&`` so the JSON cannot terminate the surrounding
    ``<script>`` element or start a comment, even if a value (for example a model
    name from ccusage) contained markup. The result is still valid JSON that
    ``JSON.parse`` reads back unchanged.

    Args:
        payload: Any JSON-serializable value.

    Returns:
        A JSON string with HTML-sensitive characters escaped.
    """
    text = json.dumps(payload, separators=(",", ":"))
    return text.replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")


def _population_stddev(
    values: list[float],
) -> float:
    """Return the population standard deviation, or 0.0 for short input.

    Args:
        values: The values to summarize.

    Returns:
        The population standard deviation.
    """
    if len(values) < 2:
        return 0.0
    return statistics.pstdev(values)


def _build_model_split(
    model_stats: dict[str, Any],
    total_cost: float,
) -> list[dict[str, Any]]:
    """Build a per-model cost breakdown sorted from most to least expensive.

    Args:
        model_stats: The ``model_statistics`` block from the analysis.
        total_cost: The total cost across all models, used for the share.

    Returns:
        A list of rows, each with the model name, its total cost, its share of
        total cost as a percentage, the number of days it was used, and its
        cache efficiency. Empty when no model statistics are present.
    """
    rows: list[dict[str, Any]] = []
    for name, stats in model_stats.items():
        model_cost = stats["statistics"]["total_cost"]["total"]
        rows.append(
            {
                "name": name,
                "cost": model_cost,
                "pct": (model_cost / total_cost * 100) if total_cost else 0,
                "days_used": stats["days_used"],
                "cache_efficiency": stats["cache_efficiency"],
            }
        )
    rows.sort(key=lambda row: row["cost"], reverse=True)
    return rows


def _compute_dashboard_context(
    analysis: dict[str, Any],
) -> dict[str, Any]:
    """Derive every value the dashboard template needs from the analysis.

    Args:
        analysis: The complete analysis dictionary (must include daily_series).

    Returns:
        A context dictionary of primitives ready to inject into the template.
    """
    meta = analysis["metadata"]
    summary = analysis["summary"]
    daily_stats = analysis["daily_statistics"]
    series = analysis.get("daily_series", [])
    model_stats = analysis["model_statistics"]

    costs = [row["total_cost"] for row in series]
    effs = [row["cache_efficiency"] for row in series]
    cost_mean = statistics.mean(costs) if costs else 0.0
    cost_std = _population_stddev(costs)
    eff_mean = statistics.mean(effs) if effs else 0.0
    eff_std = _population_stddev(effs)

    total_cost = summary["total_cost"]
    total_tokens = summary["total_tokens"]
    fresh_cost = daily_stats["cost_input"]["total"] + daily_stats["cost_output"]["total"]
    fresh_pct = (fresh_cost / total_cost * 100) if total_cost else 0

    # Per-model cost split, sorted most to least expensive. The first row is the
    # primary model, so the hero and insight cards reuse it instead of re-sorting.
    model_split = _build_model_split(model_stats, total_cost)
    if model_split:
        primary_name = model_split[0]["name"]
        primary_pct = model_split[0]["pct"]
    else:
        primary_name, primary_pct = "n/a", 0

    period = meta["analysis_period"]
    return {
        "version": __version__,
        "start_date": period["start_date"],
        "end_date": period["end_date"],
        "total_days": period["total_days"],
        "series": series,
        "total_cost": total_cost,
        "total_tokens": total_tokens,
        "cost_mean": cost_mean,
        "cost_std": cost_std,
        "eff_mean": eff_mean,
        "eff_std": eff_std,
        "overall_efficiency": summary["overall_cache_efficiency"],
        "monthly_projection": cost_mean * 30,
        "fresh_pct": fresh_pct,
        "cache_pct": 100 - fresh_pct,
        "primary_model": primary_name,
        "primary_pct": primary_pct,
        "model_split": model_split,
    }


def generate_dashboard_html(
    analysis: dict[str, Any],
) -> str:
    """Generate the self-contained HTML dashboard.

    Args:
        analysis: The complete analysis dictionary (must include daily_series).

    Returns:
        The dashboard as a single HTML document string.
    """
    logger.info("Generating HTML tokenomics dashboard...")
    ctx = _compute_dashboard_context(analysis)

    # The browser recomputes baselines and anomaly bands from this series, so the
    # page stays correct if it is ever re-saved with edited data. Both blobs are
    # escaped so a value cannot break out of the surrounding <script> element.
    series_json = _json_for_script_block(ctx["series"])
    context_json = _json_for_script_block(
        {
            "version": ctx["version"],
            "startDate": ctx["start_date"],
            "endDate": ctx["end_date"],
            "totalDays": ctx["total_days"],
            "totalCost": ctx["total_cost"],
            "totalTokens": ctx["total_tokens"],
            "overallEfficiency": ctx["overall_efficiency"],
            "monthlyProjection": ctx["monthly_projection"],
            "freshPct": ctx["fresh_pct"],
            "cachePct": ctx["cache_pct"],
            "primaryModel": ctx["primary_model"],
            "primaryPct": ctx["primary_pct"],
            "modelSplit": ctx["model_split"],
        }
    )

    generated = datetime.fromisoformat(analysis["metadata"]["generated_at"]).strftime(
        "%Y-%m-%d %H:%M"
    )

    return (
        _HTML_TEMPLATE.replace("__SERIES_JSON__", series_json)
        .replace("__CONTEXT_JSON__", context_json)
        .replace("__GENERATED__", generated)
    )


# The template is a single f-string-free document; data is injected via three
# placeholder tokens above so no user value is ever interpolated into markup.
_HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en" data-theme="light">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Claude Code Tokenomics Dashboard</title>
<style>
  :root {
    color-scheme: light;
    --page: #f9f9f7; --surface-1: #fcfcfb;
    --text-primary: #0b0b0b; --text-secondary: #52514e; --text-muted: #898781;
    --grid: #e1e0d9; --baseline: #c3c2b7; --border: rgba(11,11,11,0.10);
    --series-1: #2a78d6; --series-2: #eb6834; --series-3: #1baf7a; --series-4: #eda100;
    --emphasis: #2a78d6; --critical: #d03b3b; --good-text: #006300;
  }
  :root[data-theme="dark"] {
    color-scheme: dark;
    --page: #0d0d0d; --surface-1: #1a1a19;
    --text-primary: #ffffff; --text-secondary: #c3c2b7; --text-muted: #898781;
    --grid: #2c2c2a; --baseline: #383835; --border: rgba(255,255,255,0.10);
    --series-1: #3987e5; --series-2: #d95926; --series-3: #199e70; --series-4: #c98500;
    --emphasis: #3987e5; --critical: #d03b3b; --good-text: #0ca30c;
  }
  * { box-sizing: border-box; }
  html, body { margin: 0; }
  body { background: var(--page); color: var(--text-primary);
    font-family: system-ui, -apple-system, "Segoe UI", sans-serif; line-height: 1.5;
    -webkit-font-smoothing: antialiased; }
  .wrap { max-width: 1160px; margin: 0 auto; padding: 32px 24px 64px; }
  header.masthead { display: flex; align-items: flex-start; justify-content: space-between;
    gap: 16px; flex-wrap: wrap; margin-bottom: 8px; }
  .eyebrow { font-size: 12px; letter-spacing: 0.08em; text-transform: uppercase;
    color: var(--text-muted); font-weight: 600; margin: 0 0 6px; }
  h1 { font-size: 26px; font-weight: 650; margin: 0 0 4px; letter-spacing: -0.01em; }
  .subtitle { color: var(--text-secondary); font-size: 14px; margin: 0; }
  .theme-toggle { border: 1px solid var(--border); background: var(--surface-1);
    color: var(--text-secondary); border-radius: 8px; padding: 7px 12px; font: inherit;
    font-size: 13px; cursor: pointer; }
  .theme-toggle:hover { color: var(--text-primary); }
  .hero { background: var(--surface-1); border: 1px solid var(--border); border-radius: 14px;
    padding: 24px 26px; margin: 24px 0; display: flex; align-items: baseline; gap: 28px; flex-wrap: wrap; }
  .hero .figure { font-size: 54px; font-weight: 680; letter-spacing: -0.02em; line-height: 1; }
  .hero .figure-label { font-size: 13px; color: var(--text-secondary); margin-top: 8px; }
  .hero .context { color: var(--text-secondary); font-size: 14px; max-width: 440px; }
  .hero .context strong { color: var(--text-primary); font-weight: 620; }
  .kpi-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin: 16px 0 32px; }
  .tile { background: var(--surface-1); border: 1px solid var(--border); border-radius: 12px; padding: 16px 18px; }
  .tile .label { font-size: 12.5px; color: var(--text-secondary); margin-bottom: 8px; }
  .tile .value { font-size: 27px; font-weight: 640; letter-spacing: -0.01em; }
  .tile .sub { font-size: 12.5px; color: var(--text-muted); margin-top: 6px; }
  .tile .sub.good { color: var(--good-text); font-weight: 600; }
  .card { background: var(--surface-1); border: 1px solid var(--border); border-radius: 14px;
    padding: 22px 24px 20px; margin-bottom: 24px; }
  .card h2 { font-size: 16px; font-weight: 640; margin: 0 0 2px; }
  .card .desc { font-size: 13px; color: var(--text-secondary); margin: 0 0 6px; }
  .card-head { display: flex; justify-content: space-between; align-items: flex-start; gap: 16px; flex-wrap: wrap; }
  .legend { display: flex; gap: 18px; flex-wrap: wrap; margin: 10px 0 2px; }
  .legend .item { display: inline-flex; align-items: center; gap: 7px; font-size: 12.5px; color: var(--text-secondary); }
  .legend .swatch { width: 11px; height: 11px; border-radius: 3px; flex: none; }
  .legend .line-key { width: 16px; height: 2px; border-radius: 2px; flex: none; }
  .legend .dash-key { width: 16px; height: 0; border-top: 2px dashed var(--baseline); flex: none; }
  svg { display: block; width: 100%; height: auto; overflow: visible; }
  .grid-line { stroke: var(--grid); stroke-width: 1; }
  .axis-line { stroke: var(--baseline); stroke-width: 1; }
  .tick-text { fill: var(--text-muted); font-size: 11px; font-variant-numeric: tabular-nums; }
  .baseline-line { stroke: var(--baseline); stroke-width: 1.5; stroke-dasharray: 5 4; }
  .limit-line { stroke: var(--critical); stroke-width: 1.25; stroke-dasharray: 3 3; opacity: .7; }
  .baseline-label { font-size: 10.5px; fill: var(--text-muted); }
  .limit-label { font-size: 10.5px; fill: var(--critical); }
  .series-line { fill: none; stroke-width: 2; stroke-linejoin: round; stroke-linecap: round; }
  .end-dot-ring { fill: var(--surface-1); }
  .anom-halo { fill: none; stroke: var(--critical); stroke-width: 1.5; opacity: .5; }
  .anom-dot { fill: var(--critical); }
  .anom-flag { font-size: 10.5px; fill: var(--critical); font-weight: 600; }
  .hitbox { fill: transparent; cursor: crosshair; }
  .crosshair { stroke: var(--text-muted); stroke-width: 1; stroke-dasharray: 3 3; opacity: 0; }
  .tooltip { position: fixed; pointer-events: none; z-index: 20; opacity: 0; transition: opacity .08s;
    background: var(--surface-1); border: 1px solid var(--border); border-radius: 9px;
    box-shadow: 0 6px 24px rgba(0,0,0,.14); padding: 10px 12px; font-size: 12.5px; min-width: 160px; }
  .tooltip .tt-date { font-weight: 640; margin-bottom: 6px; }
  .tooltip .tt-row { display: flex; justify-content: space-between; gap: 16px; color: var(--text-secondary); }
  .tooltip .tt-row .v { color: var(--text-primary); font-variant-numeric: tabular-nums; }
  .tooltip .tt-row .k { display: inline-flex; align-items: center; gap: 6px; }
  .tooltip .tt-dot { width: 9px; height: 9px; border-radius: 2px; flex: none; }
  .tooltip .tt-total { border-top: 1px solid var(--border); margin-top: 6px; padding-top: 6px; font-weight: 620; }
  .tooltip .tt-anom { color: var(--critical); font-weight: 600; margin-top: 6px; }
  .table-toggle { border: 1px solid var(--border); background: transparent; color: var(--text-secondary);
    border-radius: 7px; padding: 5px 10px; font: inherit; font-size: 12px; cursor: pointer; }
  .table-toggle:hover { color: var(--text-primary); }
  table { border-collapse: collapse; width: 100%; margin-top: 14px; font-size: 12.5px; display: none; }
  table.show { display: table; }
  th, td { text-align: right; padding: 6px 10px; border-bottom: 1px solid var(--grid); font-variant-numeric: tabular-nums; }
  th:first-child, td:first-child { text-align: left; font-variant-numeric: normal; }
  th { color: var(--text-muted); font-weight: 600; font-size: 11.5px; }
  tr.anom td { color: var(--critical); }
  .insights { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
  .insight { background: var(--surface-1); border: 1px solid var(--border); border-radius: 12px; padding: 16px 18px; }
  .insight h3 { margin: 0 0 6px; font-size: 14px; font-weight: 640; }
  .insight p { margin: 0; font-size: 13px; color: var(--text-secondary); }
  .insight .num { color: var(--text-primary); font-weight: 640; }
  .tag { display: inline-block; font-size: 11px; font-weight: 600; padding: 2px 8px; border-radius: 20px; margin-bottom: 8px; }
  .tag.watch { background: rgba(208,59,59,.12); color: var(--critical); }
  .tag.ok { background: rgba(0,99,0,.12); color: var(--good-text); }
  footer { color: var(--text-muted); font-size: 12px; margin-top: 32px; text-align: center; }
  @media (max-width: 720px) {
    .kpi-row { grid-template-columns: repeat(2, 1fr); }
    .insights { grid-template-columns: 1fr; }
    .hero .figure { font-size: 44px; }
  }
</style>
</head>
<body>
<div class="wrap">
  <header class="masthead">
    <div>
      <p class="eyebrow">Tokenomics Review &middot; Claude Code</p>
      <h1>Daily Spend &amp; Token Economics</h1>
      <p class="subtitle" id="periodLine"></p>
    </div>
    <button class="theme-toggle" id="themeToggle">Dark mode</button>
  </header>

  <section class="hero">
    <div>
      <div class="figure" id="heroFigure"></div>
      <div class="figure-label" id="heroLabel"></div>
    </div>
    <div class="context" id="heroContext"></div>
  </section>

  <div class="kpi-row" id="kpiRow"></div>

  <section class="card">
    <div class="card-head">
      <div>
        <h2>Daily spend vs. baseline</h2>
        <p class="desc">Mean daily spend is the baseline; the red control limit is mean + 2&sigma;. Days beyond it are flagged as cost anomalies.</p>
      </div>
      <button class="table-toggle" data-table="tblSpend">Table view</button>
    </div>
    <div class="legend">
      <span class="item"><span class="line-key" style="background:var(--emphasis)"></span>Daily spend</span>
      <span class="item"><span class="dash-key"></span>Baseline (mean)</span>
      <span class="item"><span class="dash-key" style="border-top-color:var(--critical)"></span>Control limit (+2&sigma;)</span>
      <span class="item"><span class="swatch" style="background:var(--critical);border-radius:50%"></span>Anomaly</span>
    </div>
    <div id="spendChart"></div>
    <table id="tblSpend"><thead><tr><th>Date</th><th>Daily spend</th><th>vs. mean</th></tr></thead><tbody></tbody></table>
  </section>

  <section class="card">
    <div class="card-head">
      <div>
        <h2>What drives the cost each day</h2>
        <p class="desc">Daily spend split by token type. Cache read and cache creation typically dominate; input and output are usually a rounding error.</p>
      </div>
      <button class="table-toggle" data-table="tblComp">Table view</button>
    </div>
    <div class="legend">
      <span class="item"><span class="swatch" style="background:var(--series-4)"></span>Cache read</span>
      <span class="item"><span class="swatch" style="background:var(--series-3)"></span>Cache creation</span>
      <span class="item"><span class="swatch" style="background:var(--series-2)"></span>Output</span>
      <span class="item"><span class="swatch" style="background:var(--series-1)"></span>Input</span>
    </div>
    <div id="compChart"></div>
    <table id="tblComp"><thead><tr><th>Date</th><th>Input</th><th>Output</th><th>Cache creation</th><th>Cache read</th><th>Total</th></tr></thead><tbody></tbody></table>
  </section>

  <section class="card">
    <div class="card-head">
      <div>
        <h2>Cache efficiency vs. baseline</h2>
        <p class="desc">Share of tokens served from cache. Baseline is the mean; the red limit is mean &minus; 2&sigma;. Dips below it are efficiency anomalies worth a look.</p>
      </div>
      <button class="table-toggle" data-table="tblEff">Table view</button>
    </div>
    <div class="legend">
      <span class="item"><span class="line-key" style="background:var(--series-3)"></span>Cache efficiency</span>
      <span class="item"><span class="dash-key"></span>Baseline (mean)</span>
      <span class="item"><span class="dash-key" style="border-top-color:var(--critical)"></span>Lower limit (&minus;2&sigma;)</span>
      <span class="item"><span class="swatch" style="background:var(--critical);border-radius:50%"></span>Anomaly</span>
    </div>
    <div id="effChart"></div>
    <table id="tblEff"><thead><tr><th>Date</th><th>Cache efficiency</th><th>vs. mean</th></tr></thead><tbody></tbody></table>
  </section>

  <section class="card">
    <div class="card-head">
      <div>
        <h2>Spend by model</h2>
        <p class="desc">How the total cost splits across the models used in this window. A single model carrying most of the spend is a concentration risk worth naming.</p>
      </div>
      <button class="table-toggle" data-table="tblModel">Table view</button>
    </div>
    <div id="modelChart"></div>
    <table id="tblModel"><thead><tr><th>Model</th><th>Total cost</th><th>Share</th><th>Days used</th><th>Cache efficiency</th></tr></thead><tbody></tbody></table>
  </section>

  <section class="card" style="background:transparent;border:none;padding:0">
    <div class="insights" id="insights"></div>
  </section>

  <footer id="footer"></footer>
</div>

<div class="tooltip" id="tooltip"></div>

<script type="application/json" id="seriesData">__SERIES_JSON__</script>
<script type="application/json" id="contextData">__CONTEXT_JSON__</script>
<script type="module">
const DATA = JSON.parse(document.getElementById("seriesData").textContent);
const CTX = JSON.parse(document.getElementById("contextData").textContent);
const GENERATED = "__GENERATED__";

const costs = DATA.map(d => d.total_cost);
const effs = DATA.map(d => d.cache_efficiency);
const mean = a => a.length ? a.reduce((s,x)=>s+x,0)/a.length : 0;
const pstd = a => { if (a.length < 2) return 0; const m = mean(a); return Math.sqrt(mean(a.map(x=>(x-m)**2))); };
const costMean = mean(costs), costStd = pstd(costs);
const effMean = mean(effs), effStd = pstd(effs);
const costLimit = costMean + 2*costStd;
const effLimit = effMean - 2*effStd;
DATA.forEach(d => { d.costAnom = costStd > 0 && d.total_cost > costLimit; d.effAnom = effStd > 0 && d.cache_efficiency < effLimit; });

const $ = s => document.querySelector(s);
const fmtUSD = v => "$" + Math.round(v).toLocaleString("en-US");
const fmtUSD2 = v => "$" + v.toLocaleString("en-US", {minimumFractionDigits:2, maximumFractionDigits:2});
const M = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"];
const shortDate = s => { const p = s.split("-"); return (+p[2]) + " " + M[(+p[1])-1]; };
const yearOf = s => s.split("-")[0];
const escapeHtml = s => String(s).replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const MODEL = escapeHtml(CTX.primaryModel);
const SVGNS = "http://www.w3.org/2000/svg";
const el = (tag, attrs={}, parent=null) => { const n = document.createElementNS(SVGNS, tag); for (const k in attrs) n.setAttribute(k, attrs[k]); if (parent) parent.appendChild(n); return n; };
const tooltip = $("#tooltip");
function showTip(html, evt){ tooltip.innerHTML = html; tooltip.style.opacity = 1; moveTip(evt); }
function moveTip(evt){ const pad=14, w=tooltip.offsetWidth, h=tooltip.offsetHeight;
  let x=evt.clientX+pad, y=evt.clientY+pad;
  if (x+w>window.innerWidth) x=evt.clientX-w-pad;
  if (y+h>window.innerHeight) y=evt.clientY-h-pad;
  tooltip.style.left=x+"px"; tooltip.style.top=y+"px"; }
function hideTip(){ tooltip.style.opacity = 0; }

// header + hero
$("#periodLine").textContent = "Analysis period: " + shortDate(CTX.startDate) + " " + yearOf(CTX.startDate)
  + " – " + shortDate(CTX.endDate) + " " + yearOf(CTX.endDate) + " (" + CTX.totalDays + " active days)";
$("#heroFigure").textContent = fmtUSD(CTX.totalCost);
$("#heroLabel").textContent = "Total spend, " + CTX.totalDays + " active days";
$("#heroContext").innerHTML = "Run-rate implies a <strong>~" + fmtUSD(CTX.monthlyProjection) + "/month</strong> projection. "
  + "Spend is almost entirely a caching story: <strong>" + CTX.cachePct.toFixed(0) + "%</strong> of cost is cache read + cache creation, and "
  + "<strong>" + MODEL + "</strong> drives <strong>" + CTX.primaryPct.toFixed(0) + "%</strong> of it.";

// KPI tiles
const totalTokens = CTX.totalTokens;
const sortedCosts = costs.slice().sort((a,b)=>a-b);
const median = sortedCosts.length ? sortedCosts[Math.floor(sortedCosts.length/2)] : 0;
const kpis = [
  { label: "Total spend", value: fmtUSD(CTX.totalCost), sub: CTX.totalDays + " active days" },
  { label: "Mean daily spend", value: fmtUSD(costMean), sub: "median " + fmtUSD(median) },
  { label: "Cost / million tokens", value: fmtUSD2(totalTokens ? CTX.totalCost/(totalTokens/1e6) : 0), sub: (totalTokens/1e9).toFixed(2) + "B tokens total" },
  { label: "Mean cache efficiency", value: CTX.overallEfficiency.toFixed(1) + "%", sub: CTX.overallEfficiency > 90 ? "excellent" : "review", good: CTX.overallEfficiency > 90 },
];
kpis.forEach(k => { const t = document.createElement("div"); t.className = "tile";
  t.innerHTML = '<div class="label">'+k.label+'</div><div class="value">'+k.value+'</div><div class="sub '+(k.good?'good':'')+'">'+k.sub+'</div>';
  $("#kpiRow").appendChild(t); });

function lineChart({ mount, accessor, valueFmt, baseline, limit, limitLabel, limitSide, anomKey, color, unit, yMax, yMin }) {
  const W=1080, H=320, m={t:24,r:60,b:40,l:60}, iw=W-m.l-m.r, ih=H-m.t-m.b;
  const svg = el("svg", { viewBox:`0 0 ${W} ${H}`, role:"img" });
  const vals = DATA.map(accessor);
  const dataMax = yMax != null ? yMax : Math.max(...vals, baseline, limit ?? -Infinity)*1.08;
  const dataMin = yMin != null ? yMin : 0;
  const x = i => m.l + (DATA.length===1 ? iw/2 : iw*i/(DATA.length-1));
  const y = v => m.t + ih*(1-(v-dataMin)/(dataMax-dataMin));
  const ticks=5;
  for (let i=0;i<=ticks;i++){ const v=dataMin+(dataMax-dataMin)*i/ticks, yy=y(v);
    el("line",{class:"grid-line",x1:m.l,y1:yy,x2:m.l+iw,y2:yy},svg);
    const tt=el("text",{class:"tick-text",x:m.l-8,y:yy+4,"text-anchor":"end"},svg);
    tt.textContent = unit==="$" ? "$"+Math.round(v).toLocaleString() : Math.round(v)+"%"; }
  el("line",{class:"axis-line",x1:m.l,y1:m.t+ih,x2:m.l+iw,y2:m.t+ih},svg);
  DATA.forEach((d,i)=>{ if (i%4===0||i===DATA.length-1){ const tx=el("text",{class:"tick-text",x:x(i),y:m.t+ih+18,"text-anchor":"middle"},svg); tx.textContent=shortDate(d.date);} });
  const yb=y(baseline); el("line",{class:"baseline-line",x1:m.l,y1:yb,x2:m.l+iw,y2:yb},svg);
  const bl=el("text",{class:"baseline-label",x:m.l+iw+6,y:yb+4},svg); bl.textContent="mean";
  if (limit!=null && isFinite(limit)) { const yl=y(limit);
    el("line",{class:"limit-line",x1:m.l,y1:yl,x2:m.l+iw,y2:yl},svg);
    const ll=el("text",{class:"limit-label",x:m.l+iw+6,y:yl+4},svg); ll.textContent=limitLabel; }
  const dPath = DATA.map((d,i)=>`${i?"L":"M"}${x(i).toFixed(1)},${y(accessor(d)).toFixed(1)}`).join(" ");
  el("path",{class:"series-line",d:dPath,stroke:color},svg);
  DATA.forEach((d,i)=>{ if(d[anomKey]){ const cx=x(i), cy=y(accessor(d));
    el("circle",{class:"anom-halo",cx,cy,r:8},svg); el("circle",{class:"anom-dot",cx,cy,r:4.5},svg);
    const fl=el("text",{class:"anom-flag",x:cx,y:(limitSide==="bottom"?cy+22:cy-14),"text-anchor":"middle"},svg); fl.textContent=valueFmt(accessor(d)); } });
  const li=DATA.length-1;
  el("circle",{class:"end-dot-ring",cx:x(li),cy:y(accessor(DATA[li])),r:5.5},svg);
  el("circle",{cx:x(li),cy:y(accessor(DATA[li])),r:4,fill:color},svg);
  const cross=el("line",{class:"crosshair",y1:m.t,y2:m.t+ih},svg);
  const focus=el("circle",{r:5,fill:color,opacity:0},svg);
  const focusRing=el("circle",{r:6.5,class:"end-dot-ring",opacity:0},svg);
  const hit=el("rect",{class:"hitbox",x:m.l,y:m.t,width:iw,height:ih},svg);
  const nearest=px=>{let bi=0,bd=Infinity;DATA.forEach((d,i)=>{const dd=Math.abs(x(i)-px);if(dd<bd){bd=dd;bi=i;}});return bi;};
  hit.addEventListener("mousemove",e=>{ const r=svg.getBoundingClientRect(); const px=(e.clientX-r.left)*(W/r.width);
    const i=nearest(px), d=DATA[i], cx=x(i), cy=y(accessor(d));
    cross.setAttribute("x1",cx);cross.setAttribute("x2",cx);cross.setAttribute("opacity",1);
    focus.setAttribute("cx",cx);focus.setAttribute("cy",cy);focus.setAttribute("opacity",1);
    focusRing.setAttribute("cx",cx);focusRing.setAttribute("cy",cy);focusRing.setAttribute("opacity",1);
    svg.appendChild(focusRing);svg.appendChild(focus);
    const anom=d[anomKey]?`<div class="tt-anom">Anomaly (beyond ${limitSide==="bottom"?"−":"+"}2σ)</div>`:"";
    const delta = unit==="$" ? fmtUSD(accessor(d)-baseline) : ((accessor(d)-baseline>=0?"+":"")+(accessor(d)-baseline).toFixed(1)+" pts");
    showTip(`<div class="tt-date">${shortDate(d.date)} ${yearOf(d.date)}</div>
      <div class="tt-row"><span class="k"><span class="tt-dot" style="background:${color}"></span>${unit==="$"?"Spend":"Efficiency"}</span><span class="v">${valueFmt(accessor(d))}</span></div>
      <div class="tt-row"><span class="k">vs. mean</span><span class="v">${delta}</span></div>${anom}`, e); });
  hit.addEventListener("mouseleave",()=>{cross.setAttribute("opacity",0);focus.setAttribute("opacity",0);focusRing.setAttribute("opacity",0);hideTip();});
  mount.appendChild(svg);
}

function stackedChart({ mount }) {
  const W=1080, H=340, m={t:24,r:16,b:40,l:60}, iw=W-m.l-m.r, ih=H-m.t-m.b;
  const svg=el("svg",{viewBox:`0 0 ${W} ${H}`,role:"img"});
  const keys=[{k:"cost_input",c:"var(--series-1)"},{k:"cost_output",c:"var(--series-2)"},{k:"cost_cache_create",c:"var(--series-3)"},{k:"cost_cache_read",c:"var(--series-4)"}];
  const dataMax=Math.max(...DATA.map(d=>d.total_cost),1)*1.08;
  const band=iw/DATA.length, barW=Math.min(24,band*0.62);
  const x=i=>m.l+band*i+band/2, y=v=>m.t+ih*(1-v/dataMax);
  const ticks=5;
  for(let i=0;i<=ticks;i++){const v=dataMax*i/ticks,yy=y(v);
    el("line",{class:"grid-line",x1:m.l,y1:yy,x2:m.l+iw,y2:yy},svg);
    const tt=el("text",{class:"tick-text",x:m.l-8,y:yy+4,"text-anchor":"end"},svg); tt.textContent="$"+Math.round(v).toLocaleString();}
  el("line",{class:"axis-line",x1:m.l,y1:m.t+ih,x2:m.l+iw,y2:m.t+ih},svg);
  DATA.forEach((d,i)=>{if(i%4===0||i===DATA.length-1){const tx=el("text",{class:"tick-text",x:x(i),y:m.t+ih+18,"text-anchor":"middle"},svg);tx.textContent=shortDate(d.date);}});
  const GAP=2;
  DATA.forEach((d,i)=>{ let acc=0; const bx=x(i)-barW/2;
    keys.forEach(({k,c})=>{ const v=d[k]; if(v<=0){acc+=v;return;} const y0=y(acc),y1=y(acc+v),h=Math.max(0,(y0-y1)-GAP);
      if(h>0) el("rect",{x:bx,y:y1,width:barW,height:h,rx:1.5,fill:c},svg); acc+=v; });
    const hb=el("rect",{class:"hitbox",x:x(i)-band/2,y:m.t,width:band,height:ih},svg);
    hb.addEventListener("mousemove",e=>{ showTip(`<div class="tt-date">${shortDate(d.date)} ${yearOf(d.date)}</div>
      <div class="tt-row"><span class="k"><span class="tt-dot" style="background:var(--series-4)"></span>Cache read</span><span class="v">${fmtUSD2(d.cost_cache_read)}</span></div>
      <div class="tt-row"><span class="k"><span class="tt-dot" style="background:var(--series-3)"></span>Cache creation</span><span class="v">${fmtUSD2(d.cost_cache_create)}</span></div>
      <div class="tt-row"><span class="k"><span class="tt-dot" style="background:var(--series-2)"></span>Output</span><span class="v">${fmtUSD2(d.cost_output)}</span></div>
      <div class="tt-row"><span class="k"><span class="tt-dot" style="background:var(--series-1)"></span>Input</span><span class="v">${fmtUSD2(d.cost_input)}</span></div>
      <div class="tt-row tt-total"><span class="k">Total</span><span class="v">${fmtUSD2(d.total_cost)}</span></div>`, e); });
    hb.addEventListener("mouseleave",hideTip); });
  mount.appendChild(svg);
}

const MODEL_COLORS = ["var(--series-1)","var(--series-2)","var(--series-3)","var(--series-4)"];

function modelBarChart({ mount }) {
  const rows = CTX.modelSplit || [];
  if (!rows.length) return;
  const W=1080, rowH=46, m={t:8,r:16,b:8,l:8}, labelW=200, valW=150;
  const H = m.t + m.b + rows.length*rowH;
  const barX = m.l + labelW, barMax = W - m.r - valW - barX;
  const maxCost = Math.max(...rows.map(r=>r.cost), 1);
  const svg = el("svg", { viewBox:`0 0 ${W} ${H}`, role:"img" });
  rows.forEach((r,i)=>{ const cy = m.t + i*rowH, mid = cy + rowH/2, color = MODEL_COLORS[i % MODEL_COLORS.length];
    const w = Math.max(2, barMax * (r.cost/maxCost));
    const name = el("text",{class:"tick-text",x:m.l,y:mid+4},svg);
    name.style.fill = "var(--text-primary)"; name.style.fontSize = "13px"; name.textContent = r.name;
    el("rect",{x:barX,y:mid-11,width:barMax,height:22,rx:4,fill:"var(--grid)"},svg);
    el("rect",{x:barX,y:mid-11,width:w,height:22,rx:4,fill:color},svg);
    const val = el("text",{class:"tick-text",x:W-m.r,y:mid+4,"text-anchor":"end"},svg);
    val.style.fill = "var(--text-primary)"; val.style.fontSize = "13px";
    val.textContent = fmtUSD2(r.cost) + "  (" + r.pct.toFixed(1) + "%)";
    const hb = el("rect",{class:"hitbox",x:0,y:cy,width:W,height:rowH},svg);
    hb.addEventListener("mousemove",e=>{ showTip(`<div class="tt-date">${escapeHtml(r.name)}</div>
      <div class="tt-row"><span class="k"><span class="tt-dot" style="background:${color}"></span>Total cost</span><span class="v">${fmtUSD2(r.cost)}</span></div>
      <div class="tt-row"><span class="k">Share of spend</span><span class="v">${r.pct.toFixed(1)}%</span></div>
      <div class="tt-row"><span class="k">Days used</span><span class="v">${r.days_used}</span></div>
      <div class="tt-row"><span class="k">Cache efficiency</span><span class="v">${r.cache_efficiency.toFixed(1)}%</span></div>`, e); });
    hb.addEventListener("mouseleave",hideTip); });
  mount.appendChild(svg);
}

lineChart({ mount:$("#spendChart"), accessor:d=>d.total_cost, valueFmt:v=>fmtUSD(v),
  baseline:costMean, limit:costLimit, limitLabel:"+2σ", limitSide:"top", anomKey:"costAnom", color:"var(--emphasis)", unit:"$" });
stackedChart({ mount:$("#compChart") });
lineChart({ mount:$("#effChart"), accessor:d=>d.cache_efficiency, valueFmt:v=>v.toFixed(1)+"%",
  baseline:effMean, limit:effLimit, limitLabel:"−2σ", limitSide:"bottom", anomKey:"effAnom", color:"var(--series-3)", unit:"%", yMax:100, yMin:70 });
modelBarChart({ mount:$("#modelChart") });

function fillTable(id, rows){ $("#"+id+" tbody").innerHTML = rows; }
fillTable("tblSpend", DATA.map(d=>`<tr class="${d.costAnom?'anom':''}"><td>${shortDate(d.date)}</td><td>${fmtUSD2(d.total_cost)}</td><td>${(d.total_cost-costMean>=0?'+':'')+fmtUSD2(d.total_cost-costMean)}</td></tr>`).join(""));
fillTable("tblComp", DATA.map(d=>`<tr><td>${shortDate(d.date)}</td><td>${fmtUSD2(d.cost_input)}</td><td>${fmtUSD2(d.cost_output)}</td><td>${fmtUSD2(d.cost_cache_create)}</td><td>${fmtUSD2(d.cost_cache_read)}</td><td>${fmtUSD2(d.total_cost)}</td></tr>`).join(""));
fillTable("tblEff", DATA.map(d=>`<tr class="${d.effAnom?'anom':''}"><td>${shortDate(d.date)}</td><td>${d.cache_efficiency.toFixed(2)}%</td><td>${(d.cache_efficiency-effMean>=0?'+':'')+(d.cache_efficiency-effMean).toFixed(1)} pts</td></tr>`).join(""));
fillTable("tblModel", (CTX.modelSplit||[]).map(r=>`<tr><td>${escapeHtml(r.name)}</td><td>${fmtUSD2(r.cost)}</td><td>${r.pct.toFixed(1)}%</td><td>${r.days_used}</td><td>${r.cache_efficiency.toFixed(1)}%</td></tr>`).join(""));
document.querySelectorAll(".table-toggle").forEach(btn=>btn.addEventListener("click",()=>{ const t=$("#"+btn.dataset.table); const shown=t.classList.toggle("show"); btn.textContent=shown?"Hide table":"Table view"; }));

// insights (data-driven)
const costAnoms = DATA.filter(d=>d.costAnom);
const effAnoms = DATA.filter(d=>d.effAnom);
const insights = [];
insights.push({ tag:"watch", title:"Cost concentration risk",
  html:`<span class="num">${MODEL}</span> accounts for <span class="num">${CTX.primaryPct.toFixed(0)}%</span> of spend. A single-model mix means any price change on it flows straight to the bill.` });
insights.push({ tag: CTX.overallEfficiency>90?"ok":"watch", title:"Cache is doing the work",
  html:`At <span class="num">${CTX.overallEfficiency.toFixed(1)}%</span> efficiency, cache reads absorb the volume. Fresh input+output is only <span class="num">${CTX.freshPct.toFixed(1)}%</span> of cost, so prompt volume is not the main lever.` });
if (costAnoms.length){ const w=costAnoms.reduce((a,b)=>b.total_cost>a.total_cost?b:a);
  insights.push({ tag:"watch", title:"Cost anomaly: "+shortDate(w.date),
    html:`<span class="num">${fmtUSD(w.total_cost)}</span> in one day (beyond mean + 2σ), driven by <span class="num">${fmtUSD(w.cost_cache_read)}</span> of cache reads. Tie this to a specific initiative to confirm it was intended.` }); }
if (effAnoms.length){ const w=effAnoms.reduce((a,b)=>b.cache_efficiency<a.cache_efficiency?b:a);
  insights.push({ tag:"watch", title:"Efficiency anomaly: "+shortDate(w.date),
    html:`Efficiency fell to <span class="num">${w.cache_efficiency.toFixed(1)}%</span> (below mean − 2σ). Low reuse means more full-price creation tokens per unit of work.` }); }
$("#insights").innerHTML = insights.map(i=>`<div class="insight"><span class="tag ${i.tag}">${i.tag==="ok"?"Healthy":"Watch"}</span><h3>${i.title}</h3><p>${i.html}</p></div>`).join("");

$("#footer").innerHTML = "Generated " + GENERATED + " from ccusage data &middot; pricing from LiteLLM &middot; anomaly bands are mean &plusmn; 2&sigma; &middot; analyzer v" + CTX.version;

const root=document.documentElement, tbtn=$("#themeToggle");
tbtn.addEventListener("click",()=>{ const dark=root.getAttribute("data-theme")==="dark"; root.setAttribute("data-theme",dark?"light":"dark"); tbtn.textContent=dark?"Dark mode":"Light mode"; });
window.addEventListener("scroll",()=>{ if(tooltip.style.opacity!=="0") hideTip(); });
</script>
</body>
</html>
"""
