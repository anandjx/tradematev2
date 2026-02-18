"""
Deterministic Equity Research HTML Report Generator — V6 "Versailles".

Visual Architecture:
    1.  **Theme:** "Ethereal Institutional" — Light glassmorphism with iridescent undertones.
    2.  **Typography:** 
        - Headings: 'Playfair Display' (Serif) for high-fashion/elite feel.
        - Body: 'Inter' for readability.
        - Data: 'JetBrains Mono' for technical precision.
    3.  **Layout:** Modular "Masonry" grid for metrics (Random Tiles concept).
    4.  **Texture:** CSS-generated noise and subtle mesh gradients (The "Versailles" touch).
    5.  **Motion:** Subtle entry animations.

Logic:
    - Identical to V5 (Deterministic, No LLM).
"""

import os
import json
import logging
import re
from datetime import datetime

from google.adk.tools import FunctionTool, ToolContext
from google import genai
from google.genai import types

logger = logging.getLogger("EquityReportGenerator_V6")


# ─────────────────────────────────────────────────
#  MARKDOWN → HTML (Identical to V5)
# ─────────────────────────────────────────────────

def _md(text: str) -> str:
    """Convert upstream markdown to clean HTML."""
    if not text or text.strip() in ("Insufficient Data", "N/A", ""):
        return ""

    # Tables
    tbl, res, in_t = [], [], False
    for raw in text.split('\n'):
        s = raw.strip()
        if '|' in s and s.startswith('|') and s.endswith('|'):
            cells = [c.strip() for c in s.strip('|').split('|')]
            if all(set(c) <= {'-', ':', ' '} for c in cells):
                in_t = True
                continue
            if not in_t and not tbl:
                tbl.append('<table class="gt"><thead><tr>' + ''.join(f'<th>{c}</th>' for c in cells) + '</tr></thead><tbody>')
                in_t = True
            else:
                tbl.append('<tr>' + ''.join(f'<td>{c}</td>' for c in cells) + '</tr>')
        else:
            if in_t:
                tbl.append('</tbody></table>')
                res.extend(tbl)
                tbl, in_t = [], False
            res.append(raw)
    if in_t:
        tbl.append('</tbody></table>')
        res.extend(tbl)
    text = '\n'.join(res)

    text = re.sub(r'^#### (.*?)$', r'<h4>\1</h4>', text, flags=re.MULTILINE)
    text = re.sub(r'^### (.*?)$', r'<h3>\1</h3>', text, flags=re.MULTILINE)
    text = re.sub(r'^## (.*?)$', r'<h2>\1</h2>', text, flags=re.MULTILINE)
    text = re.sub(r'^# (.*?)$', r'<h1>\1</h1>', text, flags=re.MULTILINE)
    text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'^---+$', '<hr class="sep">', text, flags=re.MULTILINE)

    lines = text.split('\n')
    out, in_l = [], False
    for ln in lines:
        st = ln.strip()
        if st.startswith('- ') or st.startswith('• '):
            if not in_l:
                out.append('<ul>')
                in_l = True
            li_text = re.sub(r"^[0-9]+[.]\s*", "", st)
            out.append(f'<li>{li_text}</li>')
        elif re.match(r'^\d+\.\s', st):
            if not in_l:
                out.append('<ol>')
                in_l = True
            li_text = re.sub(r"^[0-9]+[.]\s*", "", st)
            out.append(f'<li>{li_text}</li>')
        else:
            if in_l:
                out.append('</ul>')
                in_l = False
            out.append(ln)
    if in_l:
        out.append('</ul>')
    text = '\n'.join(out)
    text = re.sub(r'\n\n+', '</p><p>', text)
    text = text.replace('\n', '<br/>')
    return text


def _v(val, prefix="", suffix=""):
    if val is None or val == "" or val == "N/A":
        return None
    try:
        if isinstance(val, (int, float)):
            return f"{prefix}{val:,.2f}{suffix}"
    except Exception:
        pass
    return f"{prefix}{val}{suffix}"


def _badge(signal):
    if not signal: return ""
    s = str(signal).upper()
    if s in ("BUY", "BULLISH", "STRONG BUY", "ACCUMULATE"):
        cls = "b-grn"
    elif s in ("SELL", "BEARISH", "STRONG SELL"):
        cls = "b-red"
    elif s in ("HOLD", "NEUTRAL", "MONITOR"):
        cls = "b-amb"
    else:
        cls = "b-neu"
    return f'<span class="bdg {cls}">{signal}</span>'


def _gauge_html(value, max_val=100, color="var(--a1)", label=""):
    if value is None: return ""
    try:
        pct = min(float(value) / max_val * 100, 100)
    except Exception:
        return ""
    lbl = f'<div class="gx-l">{label}</div>' if label else ""
    return f'{lbl}<div class="gx"><div class="gx-b" style="width:{pct}%;background:{color};"></div></div>'


# ─────────────────────────────────────────────────
#  CSS — V6 "VERSAILLES"
# ─────────────────────────────────────────────────

CSS = """
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,600;0,700;1,400&family=Inter:wght@300;400;500;600&family=JetBrains+Mono:wght@400;500&display=swap');

:root {
    --bg-base: #f8fafc;
    --glass: rgba(255, 255, 255, 0.65);
    --glass-str: rgba(255, 255, 255, 0.85);
    --bord: rgba(255,255,255,0.4);
    --shd: 0 10px 40px -10px rgba(0,0,0,0.05);
    --txt: #0f172a;
    --txt-mut: #64748b;
    --a1: #4f46e5; /* Indigo */
    --a2: #059669; /* Emerald */
    --a3: #d97706; /* Amber */
    --a4: #db2777; /* Pink */
}

* {margin:0; padding:0; box-sizing:border-box;}

body {
    font-family: 'Inter', sans-serif;
    color: var(--txt);
    background-color: var(--bg-base);
    background-image: 
        radial-gradient(at 0% 0%, rgba(79, 70, 229, 0.08) 0px, transparent 50%),
        radial-gradient(at 100% 0%, rgba(219, 39, 119, 0.08) 0px, transparent 50%),
        radial-gradient(at 100% 100%, rgba(5, 150, 105, 0.08) 0px, transparent 50%),
        url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%2394a3b8' fill-opacity='0.05'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E");
    min-height: 100vh;
    font-size: 14px;
    line-height: 1.6;
    overflow-x: hidden;
}

.wrap {
    max-width: 1300px;
    margin: 0 auto;
    padding: 4rem 2rem;
    position: relative;
}

/* ── Typography ── */
h1, h2, h3, .serif { font-family: 'Playfair Display', serif; }
.mono { font-family: 'JetBrains Mono', monospace; }

/* ── Hero ── */
.hero {
    text-align: center;
    margin-bottom: 4rem;
    position: relative;
    z-index: 2;
}
.hero h1 {
    font-size: clamp(4rem, 8vw, 6rem);
    font-weight: 400;
    letter-spacing: -0.03em;
    background: linear-gradient(135deg, #0f172a 0%, #334155 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 0.5rem;
    line-height: 1;
}
.hero-meta {
    font-size: 1rem;
    color: var(--txt-mut);
    letter-spacing: 0.2em;
    text-transform: uppercase;
    font-weight: 500;
}
.hero-price {
    margin-top: 1.5rem;
    display: inline-flex;
    align-items: baseline;
    gap: 1rem;
    padding: 1rem 2rem;
    background: rgba(255,255,255,0.4);
    border: 1px solid rgba(255,255,255,0.6);
    border-radius: 100px;
    backdrop-filter: blur(8px);
}
.hp-val { font-size: 2.5rem; font-weight: 600; color: var(--txt); }
.hp-d { font-size: 1rem; font-weight: 500; }
.hp-up { color: var(--a2); }
.hp-dn { color: var(--a4); }

/* ── Glass Tile Architecture ── */
.grid {
    display: grid;
    grid-template-columns: repeat(12, 1fr);
    gap: 1.5rem;
    margin-bottom: 3rem;
}
.tile {
    background: var(--glass);
    backdrop-filter: blur(20px) saturate(180%);
    -webkit-backdrop-filter: blur(20px) saturate(180%);
    border: 1px solid rgba(255,255,255,0.5);
    border-radius: 20px;
    padding: 2rem;
    box-shadow: var(--shd);
    position: relative;
    overflow: hidden;
    transition: transform 0.4s cubic-bezier(0.2, 0.8, 0.2, 1), box-shadow 0.4s;
}
.tile:hover {
    transform: translateY(-5px);
    box-shadow: 0 20px 50px -10px rgba(0,0,0,0.08);
    background: var(--glass-str);
}
.tile::before {
    content:''; position:absolute; inset:0;
    box-shadow: inset 0 0 0 1px rgba(255,255,255,0.4);
    border-radius: 20px; pointer-events: none;
}

/* ── Spans ── */
.s-12 { grid-column: span 12; }
.s-8 { grid-column: span 8; }
.s-6 { grid-column: span 6; }
.s-4 { grid-column: span 4; }
.s-3 { grid-column: span 3; }

@media(max-width: 1024px) { .s-8, .s-4, .s-3 { grid-column: span 6; } }
@media(max-width: 768px) { .s-8, .s-6, .s-4, .s-3 { grid-column: span 12; } }

/* ── Tile Content ── */
.t-head {
    display: flex; justify-content: space-between; align-items: flex-end;
    margin-bottom: 1.5rem; border-bottom: 1px solid rgba(0,0,0,0.05); padding-bottom: 1rem;
}
.t-ttl { font-family: 'Playfair Display', serif; font-size: 1.4rem; font-weight: 600; font-style: italic; color: var(--txt); }
.t-sub { font-family: 'Inter', sans-serif; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.1em; color: var(--txt-mut); }

/* ── Metric Tiles (The "Random Tiles" look) ── */
.mt-val { font-size: 2.2rem; font-weight: 500; color: var(--txt); letter-spacing: -0.03em; }
.mt-lbl { font-size: 0.8rem; color: var(--txt-mut); text-transform: uppercase; letter-spacing: 0.05em; margin-top: 0.5rem; }

/* ── Badges ── */
.bdg { padding: 6px 14px; border-radius: 50px; font-size: 0.75rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; }
.b-grn { background: rgba(16, 185, 129, 0.1); color: #059669; border: 1px solid rgba(16, 185, 129, 0.2); }
.b-red { background: rgba(239, 68, 68, 0.1); color: #dc2626; border: 1px solid rgba(239, 68, 68, 0.2); }
.b-amb { background: rgba(245, 158, 11, 0.1); color: #d97706; border: 1px solid rgba(245, 158, 11, 0.2); }
.b-neu { background: rgba(148, 163, 184, 0.1); color: #64748b; border: 1px solid rgba(148, 163, 184, 0.2); }

/* ── Narrative Typography ── */
.prose { font-size: 1rem; color: #334155; line-height: 1.8; }
.prose h3 { font-size: 1.2rem; margin-top: 1.5rem; margin-bottom: 0.5rem; color: var(--txt); }
.prose ul { padding-left: 1.2rem; margin-bottom: 1rem; }
.prose li { margin-bottom: 0.4rem; }
.prose strong { color: var(--txt); font-weight: 600; }

/* ── Gauges & Bars ── */
.gx { height: 6px; background: rgba(0,0,0,0.05); border-radius: 10px; overflow: hidden; }
.gx-b { height: 100%; border-radius: 10px; }
.gx-l { font-size: 0.7rem; color: var(--txt-mut); margin-bottom: 0.3rem; display: flex; justify-content: space-between; }

/* ── Specialized Cards ── */
.card-oracle {
    background: linear-gradient(135deg, rgba(255,255,255,0.7), rgba(240, 253, 244, 0.6));
    border-color: rgba(16, 185, 129, 0.3);
}
.card-climax {
    background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
    color: white;
}
.card-climax .t-ttl { color: white; }
.card-climax .t-sub { color: rgba(255,255,255,0.5); }
.card-climax .prose { color: rgba(255,255,255,0.8); }
.card-climax .prose h3, .card-climax .prose strong { color: white; }
.card-climax .prose li::marker { color: var(--a1); }

/* ── Footer ── */
.foot { text-align: center; margin-top: 4rem; padding-top: 2rem; border-top: 1px solid rgba(0,0,0,0.05); color: var(--txt-mut); font-size: 0.8rem; }
.logo { font-family: 'Playfair Display', serif; font-weight: 700; font-style: italic; font-size: 1.2rem; color: var(--txt); margin-bottom: 0.5rem; }

/* ── Animations ── */
@keyframes fadeUp { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }
.tile { animation: fadeUp 0.8s ease-out backwards; }
.tile:nth-child(1) { animation-delay: 0.1s; }
.tile:nth-child(2) { animation-delay: 0.2s; }
.tile:nth-child(3) { animation-delay: 0.3s; }
"""


# ─────────────────────────────────────────────────
#  PAYLOAD BUILDER (State → Dict)
# ─────────────────────────────────────────────────

def _build_payload(ticker: str, state: dict) -> dict:
    """Extract deterministic fields from agent state."""
    market = state.get("market_analysis", {}) or {}
    tech = state.get("technical_analysis", {}) or {}
    oracle = state.get("oracle_forecast", {}) or {}
    quant = state.get("quant_synthesis", {}) or {}
    strategy = state.get("strategic_report", {}) or {}

    price = market.get("current_price") or tech.get("price")
    confidence = quant.get("confidence_score")
    rsi = tech.get("rsi")

    asym_pct = None
    if price and oracle.get("predicted_price"):
        try:
            pred = float(oracle["predicted_price"])
            curr = float(price)
            pct = ((pred - curr) / curr) * 100
            asym_pct = round(pct, 1)
        except: pass

    # Support/Resistance
    support = tech.get("support_levels", []) or []
    resistance = tech.get("resistance_levels", []) or []
    if isinstance(support, list): support = [s for s in support[:3] if s is not None]
    if isinstance(resistance, list): resistance = [r for r in resistance[:3] if r is not None]

    return {
        "ticker": ticker,
        "date": datetime.now().strftime("%B %d, %Y"),
        "price": price,
        "mcap": market.get("market_cap"),
        "sentiment": market.get("sentiment"),
        "regime": tech.get("trend"),
        "bias": quant.get("overall_signal"),
        "confidence": confidence,
        "action": strategy.get("signal"),
        "asym_pct": asym_pct,
        "rsi": rsi,
        "macd": tech.get("macd"),
        "trend": tech.get("trend"),
        "support": support,
        "resistance": resistance,
        "rating": tech.get("rating"),
        "orc_target": oracle.get("predicted_price"),
        "orc_conf": oracle.get("model_confidence"),
        "orc_horizon": oracle.get("forecast_horizon"),
        "market_html": _md(market.get("report", "")),
        "quant_html": _md(quant.get("summary", "")),
        "blueprint_html": _md(strategy.get("narrative", "")),
        "bp_signal": strategy.get("signal"),
        "bp_timeframe": strategy.get("time_horizon"),
    }


# ─────────────────────────────────────────────────
#  HTML BUILDER — V6 "VERSAILLES"
# ─────────────────────────────────────────────────

def _build_report_html(d: dict) -> str:
    ticker = d.get("ticker", "")
    date = d.get("date", "")
    
    # Price Block
    price_html = ""
    price = d.get("price")
    if price is not None:
        p_str = _v(price, prefix="$")
        asym = d.get("asym_pct")
        cls, arrow, txt = "", "", ""
        if asym is not None:
            cls = "hp-up" if asym >= 0 else "hp-dn"
            arrow = "▲" if asym >= 0 else "▼"
            txt = f"{abs(asym):.1f}% Target"
        price_html = f'''<div class="hero-price mono"><span class="hp-val">{p_str}</span><span class="hp-d {cls}">{arrow} {txt}</span></div>'''

    # Metrics for Tiles
    metrics_html = ""
    
    # 1. Oracle Card (Span 4)
    orc_t = d.get("orc_target")
    if orc_t:
        metrics_html += f'''
        <div class="tile s-4 card-oracle">
            <div class="t-head"><div class="t-ttl">Oracle Horizon</div><div class="t-sub">AI Projection</div></div>
            <div class="mt-val mono" style="color:#059669;">{_v(orc_t, prefix="$")}</div>
            <div class="mt-lbl">Target ({d.get("orc_horizon", "30d")})</div>
            <br>
            {_gauge_html(float(d.get("orc_conf", 0))*100, 100, "#059669", "Model Confidence")}
        </div>'''
    
    # 2. Key Action (Span 4)
    if d.get("action"):
        metrics_html += f'''
        <div class="tile s-4">
            <div class="t-head"><div class="t-ttl">Strategic Bias</div><div class="t-sub">Conviction</div></div>
            <div style="font-size:2rem; margin-bottom:0.5rem;">{_badge(d.get("action"))}</div>
            {_gauge_html(d.get("confidence", 0), 100, "var(--a1)", "Quant Confidence")}
        </div>'''

    # 3. Technical (Span 4)
    if d.get("rsi"):
        metrics_html += f'''
        <div class="tile s-4">
            <div class="t-head"><div class="t-ttl">Technical Health</div><div class="t-sub">Momentum</div></div>
            <div class="mt-val mono">{_v(d.get("rsi"))}</div>
            <div class="mt-lbl">RSI (14)</div>
            <br>
            {_gauge_html(d.get("rsi"), 100, "var(--a4)", "Oscillator")}
        </div>'''

    # 4. Market Narrative (Span 6)
    if d.get("market_html"):
        metrics_html += f'''
        <div class="tile s-6">
            <div class="t-head"><div class="t-ttl">Market Intelligence</div><div class="t-sub">Qualitative Data</div></div>
            <div class="prose">{d.get("market_html")}</div>
        </div>'''
        
    # 5. Quant Synthesis (Span 6)
    if d.get("quant_html"):
        metrics_html += f'''
        <div class="tile s-6">
            <div class="t-head"><div class="t-ttl">Quantitative Synthesis</div><div class="t-sub">Data Fusion</div></div>
            <div class="prose">{d.get("quant_html")}</div>
        </div>'''

    # 6. Climax Blueprint (Span 12)
    metrics_html += f'''
        <div class="tile s-12 card-climax">
            <div class="t-head" style="border-color:rgba(255,255,255,0.1);"><div class="t-ttl">Strategic Blueprint</div><div class="t-sub">The Thesis</div></div>
            <div class="prose">{d.get("blueprint_html", "<p>Thesis pending generation...</p>")}</div>
            <div style="margin-top:2rem; display:flex; gap:2rem; opacity:0.7; font-family:'JetBrains Mono'; font-size:0.8rem;">
                <span>SIGNAL: {d.get("bp_signal", "N/A")}</span>
                <span>TIMEFRAME: {d.get("bp_timeframe", "N/A")}</span>
            </div>
        </div>'''

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>{ticker} — Private Client Note</title>
<style>{CSS}</style>
</head>
<body>
<div class="wrap">
    <div class="hero">
        <div class="hero-meta">{date} · Equity Research</div>
        <h1>{ticker}</h1>
        {price_html}
    </div>
    
    <div class="grid">
        {metrics_html}
    </div>

    <div class="foot">
        <div class="logo">TradeMate</div>
        Generated via Deterministic AI Pipeline · Not Financial Advice
    </div>
</div>
</body>
</html>"""


# ─────────────────────────────────────────────────
#  TOOL ENTRY POINT
# ─────────────────────────────────────────────────

def generate_equity_report_v6(ticker: str, tool_context: ToolContext) -> str:
    """
    Generate the V6 'Versailles' Aesthetic Report.
    """
    tool_context.state["pipeline_stage"] = "report_generation"
    payload = _build_payload(ticker, tool_context.state)
    html_code = _build_report_html(payload)
    tool_context.state["equity_report_html"] = html_code # Overwrite state with V6 html
    return json.dumps({"status": "success", "message": "V6 Report Generated."})

# To use this, you'd need to import 'generate_equity_report_v6' in agent.py
equity_report_v6_tool = FunctionTool(func=generate_equity_report_v6)
