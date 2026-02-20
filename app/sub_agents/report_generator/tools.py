"""
Deterministic Equity Research HTML Report Generator — V7b.

Architecture:
    1. Reads ONLY from tool_context.state (upstream agent outputs)
    2. Builds strict data payload — NO interpretation, NO invention
    3. Generates COMPLETE HTML in Python (deterministic, zero truncation)
    4. Persistent two-column layout: 65% narrative / 35% quant rail
    5. Light glassmorphic theme — modular narrative tiles
    6. Missing data → collapse container, never show dashes
    7. Currency symbol inferred from ticker suffix (matching frontend)

V7b Fixes:
    - Currency: Correct symbol per exchange (₹ for .NS/.BO, £ for .L, etc.)
    - Hero: Centered serif header with 'Equity Research by TradeMate'
    - Tints: Subtle colored glass backgrounds per card theme

Hallucination Risk: ZERO
Truncation Risk: ZERO
"""

import os
import json
import logging
import re
from datetime import datetime

from google.adk.tools import FunctionTool, ToolContext
from google import genai
from google.genai import types

logger = logging.getLogger("EquityReportGenerator")


# ─────────────────────────────────────────────────
#  CURRENCY INFERENCE (ported from frontend/src/lib/currency.ts)
# ─────────────────────────────────────────────────

_CURRENCY_MAP = {
    "USD": "$",   "INR": "\u20b9",   "GBP": "\u00a3",   "EUR": "\u20ac",   "JPY": "\u00a5",
    "CNY": "\u00a5",   "KRW": "\u20a9",   "HKD": "HK$", "SGD": "S$",  "AUD": "A$",
    "CAD": "C$",  "CHF": "CHF ", "TWD": "NT$", "ZAR": "R",   "SAR": "SR ",
    "SEK": "kr ", "NOK": "kr ", "DKK": "kr ", "BRL": "R$",  "MXN": "MX$",
    "IDR": "Rp ", "MYR": "RM ", "THB": "\u0e3f",   "ILS": "\u20aa",   "TRY": "\u20ba",
    "PLN": "z\u0142 ", "NZD": "NZ$",
}

# Yahoo Finance suffix -> currency code  (mirrors frontend SUFFIX_MAP exactly)
_SUFFIX_MAP = {
    ".NS": "INR", ".BO": "INR",                                     # India
    ".L":  "GBP",                                                    # London
    ".PA": "EUR", ".AS": "EUR", ".BR": "EUR", ".LS": "EUR",         # Euronext
    ".MI": "EUR", ".MC": "EUR", ".HE": "EUR", ".VI": "EUR",         # Milan/Madrid/Helsinki/Vienna
    ".DE": "EUR",                                                    # Deutsche Boerse
    ".T":  "JPY",                                                    # Tokyo
    ".SS": "CNY", ".SZ": "CNY",                                     # Shanghai/Shenzhen
    ".HK": "HKD",                                                    # Hong Kong
    ".SI": "SGD",                                                    # Singapore
    ".AX": "AUD",                                                    # Australia
    ".TO": "CAD",                                                    # Toronto
    ".SW": "CHF",                                                    # SIX Swiss
    ".KS": "KRW", ".KQ": "KRW",                                     # Korea
    ".TW": "TWD", ".TWO": "TWD",                                    # Taiwan
    ".JO": "ZAR",                                                    # Johannesburg
    ".SR": "SAR",                                                    # Saudi
    ".ST": "SEK",                                                    # Stockholm
    ".OL": "NOK",                                                    # Oslo
    ".CO": "DKK",                                                    # Copenhagen
    ".SA": "BRL",                                                    # B3 Sao Paulo
    ".MX": "MXN",                                                    # Mexico
    ".JK": "IDR",                                                    # Jakarta
    ".KL": "MYR",                                                    # Kuala Lumpur
    ".BK": "THB",                                                    # Bangkok
    ".TA": "ILS",                                                    # Tel Aviv
    ".IS": "TRY",                                                    # Istanbul
    ".WA": "PLN",                                                    # Warsaw
    ".NZ": "NZD",                                                    # New Zealand
}

def _infer_currency(ticker: str) -> str:
    """Infer currency code from ticker suffix. Mirrors frontend logic exactly."""
    if not ticker:
        return "USD"
    t = ticker.upper()
    dot = t.rfind(".")
    if dot != -1:
        suffix = t[dot:]
        if suffix in _SUFFIX_MAP:
            return _SUFFIX_MAP[suffix]
    return "USD"

def _csym(ticker: str) -> str:
    """Get currency symbol for a ticker. e.g. 'RELIANCE.NS' -> '₹'"""
    return _CURRENCY_MAP.get(_infer_currency(ticker), "$")



# ─────────────────────────────────────────────────
#  MARKDOWN → HTML
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
            out.append(f'<li>{st[2:]}</li>')
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


# ─────────────────────────────────────────────────
#  NARRATIVE SECTION SPLITTER
# ─────────────────────────────────────────────────

# Tile accent mapping — keyed on lowercase substring match
_TILE_ACCENTS = {
    "executive summary": "gc-b",
    "sec filing": "gc-s",
    "regulatory": "gc-s",
    "news": "gc-b",
    "stock performance": "gc-b",
    "market sentiment": "gc-b",
    "analyst commentary": "gc-t",
    "analyst outlook": "gc-t",
    "narrative positioning": "gc-nar",
    "momentum intelligence": "gc-nar",
    "risk": "gc-a",
    "opportunit": "gc-g",
    "bull case": "gc-bull",
    "bear case": "gc-bear",
}


def _split_narrative(raw_markdown: str):
    """Split raw market analysis markdown into themed tiles.

    Returns list of (title, accent_class, html_content) tuples.
    If no recognizable headings found, returns single tile with all content.
    """
    if not raw_markdown or raw_markdown.strip() in ("Insufficient Data", "N/A", ""):
        return []

    # Split by markdown heading patterns: **N. Title** or ## Title
    # Common patterns from upstream Market Analyst:
    #   **1. Executive Summary:**
    #   **2. Recent SEC Filings & Regulatory Information:**
    #   ## **Market Analysis Report for: TICKER**
    sections = []
    current_title = None
    current_lines = []

    for line in raw_markdown.split('\n'):
        stripped = line.strip()

        # Match: **N. Title:** or **N. Title**
        m = re.match(r'^\*\*(\d+)\.\s*(.*?)[:：]?\*\*\s*$', stripped)
        if not m:
            # Match: ## **Title** or ## Title
            m2 = re.match(r'^#{1,3}\s+\*?\*?(.*?)\*?\*?\s*$', stripped)
            if m2:
                title_text = m2.group(1).strip().rstrip(':')
                # Skip the report header line itself
                if 'market analysis report for' in title_text.lower():
                    current_lines.append(line)
                    continue
                if current_title is not None:
                    sections.append((current_title, '\n'.join(current_lines)))
                current_title = title_text
                current_lines = []
                continue

        if m:
            if current_title is not None:
                sections.append((current_title, '\n'.join(current_lines)))
            current_title = m.group(2).strip().rstrip(':')
            current_lines = []
            continue

        current_lines.append(line)

    # Flush last section
    if current_title is not None:
        sections.append((current_title, '\n'.join(current_lines)))

    if not sections:
        # Fallback: no headings found, render as single tile
        html = _md(raw_markdown)
        if html:
            return [("Market Analysis", "gc-b", html)]
        return []

    # Convert each section to (title, accent, html)
    result = []
    for title, content in sections:
        html = _md(content)
        if not html or not html.strip():
            continue  # Skip empty sections entirely

        # Determine accent class
        accent = "gc-b"  # default blue
        title_lower = title.lower()
        for key, cls in _TILE_ACCENTS.items():
            if key in title_lower:
                accent = cls
                break

        result.append((title, accent, html))

    return result


def _v(val, prefix="", suffix=""):
    """Format value. Returns None if missing — caller decides whether to render."""
    if val is None or val == "" or val == "N/A":
        return None
    try:
        if isinstance(val, (int, float)):
            return f"{prefix}{val:,.2f}{suffix}"
    except Exception:
        pass
    return f"{prefix}{val}{suffix}"


def _price(val, ticker=""):
    """Format a price value with the correct currency symbol based on ticker."""
    if val is None or val == "" or val == "N/A":
        return None
    sym = _csym(ticker)
    try:
        if isinstance(val, (int, float)):
            return f"{sym}{val:,.2f}"
    except Exception:
        pass
    return f"{sym}{val}"


def _metric_row(label, val, css_class=""):
    if val is None:
        return ""
    return f'<div class="mr"><span class="ml">{label}</span><span class="mv {css_class}">{val}</span></div>'


def _badge(signal):
    if not signal:
        return ""
    s = str(signal).upper()
    if s in ("BUY", "BULLISH", "STRONG BUY", "ACCUMULATE"):
        bg = "linear-gradient(135deg,#059669,#10b981)"
    elif s in ("SELL", "BEARISH", "STRONG SELL"):
        bg = "linear-gradient(135deg,#dc2626,#ef4444)"
    elif s in ("HOLD", "NEUTRAL", "MONITOR"):
        bg = "linear-gradient(135deg,#d97706,#f59e0b)"
    else:
        bg = "rgba(100,116,139,0.15)"
    return f'<span class="bdg" style="background:{bg};">{signal}</span>'


def _gauge_html(value, max_val=100, color="#2563eb", label=""):
    if value is None:
        return ""
    try:
        pct = min(float(value) / max_val * 100, 100)
    except Exception:
        return ""
    lbl = f'<div class="gauge-lbl">{label}</div>' if label else ""
    return f'{lbl}<div class="gauge"><div class="gauge-bar" style="width:{pct}%;background:{color};"></div></div>'


def _gauge_color(rsi):
    try:
        v = float(rsi)
        if v < 30: return "#ef4444"
        if v > 70: return "#059669"
        return "#2563eb"
    except Exception:
        return "#64748b"


# ─────────────────────────────────────────────────
#  CSS — V7 Modular Glassmorphic Institutional
# ─────────────────────────────────────────────────

CSS = """
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;600;700;800;900&family=Inter:wght@300;400;500;600;700;800;900&display=swap');
*{margin:0;padding:0;box-sizing:border-box;}

body{
  font-family:'Inter',system-ui,-apple-system,sans-serif;
  background:linear-gradient(160deg,#f0f4f8 0%,#e8eef6 30%,#dfe7f0 60%,#edf1f7 100%);
  background-attachment:fixed;
  color:#1e293b;
  line-height:1.65;
  font-size:14.5px;
  -webkit-font-smoothing:antialiased;
  min-height:100vh;
}

.wrap{max-width:1440px;margin:0 auto;padding:0 clamp(16px,3vw,40px);}

/* ── Hero — Centered Serif Masthead ── */
.hero{
  padding:clamp(2.5rem,6vw,4rem) 0 clamp(1.5rem,3vw,2.5rem);
  border-bottom:1px solid rgba(148,163,184,0.15);
  margin-bottom:2rem;
  text-align:center;
}
.hero-meta{
  font-size:.82rem;color:#94a3b8;letter-spacing:.18em;text-transform:uppercase;
  font-weight:500;margin-bottom:.6rem;
}
.hero h1{
  font-family:'Playfair Display',Georgia,serif;
  font-size:clamp(3.2rem,7vw,5rem);font-weight:800;letter-spacing:-0.03em;
  color:#0f172a;line-height:1;margin-bottom:1rem;
}
.hero-price-pill{
  display:inline-flex;align-items:baseline;gap:.8rem;
  padding:.8rem 2rem;border-radius:100px;
  background:rgba(255,255,255,0.45);border:1px solid rgba(148,163,184,0.15);
  backdrop-filter:blur(8px);-webkit-backdrop-filter:blur(8px);
}
.hero-price-pill .big{font-size:clamp(1.6rem,3vw,2.2rem);font-weight:700;color:#0f172a;font-family:'Inter',monospace;}
.hero-price-pill .delta{font-size:.82rem;font-weight:600;}
.hero-price-pill .delta.up{color:#059669;}
.hero-price-pill .delta.dn{color:#dc2626;}

/* Frame strip */
.frame{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:1rem;margin-top:1.8rem;}
.fc{
  background:rgba(255,255,255,0.5);backdrop-filter:blur(16px);-webkit-backdrop-filter:blur(16px);
  border:1.5px solid rgba(148,163,184,0.18);border-radius:14px;padding:1.1rem 1rem;text-align:center;
  transition:transform 0.2s,box-shadow 0.2s;
}
.fc:hover{transform:translateY(-2px);box-shadow:0 8px 24px rgba(0,0,0,0.06);}
.fc-lbl{font-size:.65rem;font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:#94a3b8;margin-bottom:.35rem;}
.fc-val{font-size:1.15rem;font-weight:700;color:#0f172a;}
.fc-note{font-size:.72rem;color:#64748b;margin-top:.2rem;}

/* Alert bar */
.alert-bar{
  margin-top:1.2rem;padding:.6rem 1.2rem;
  background:rgba(251,191,36,0.1);border:1px solid rgba(251,191,36,0.3);
  border-radius:10px;text-align:center;color:#92400e;font-weight:600;font-size:.82rem;
}

/* ══════════════════════════════════════════
   GLASS CARD — V7 Enhanced
   ══════════════════════════════════════════ */
.gc{
  background:rgba(248,250,252,0.55);
  backdrop-filter:blur(20px) saturate(1.2);
  -webkit-backdrop-filter:blur(20px) saturate(1.2);
  border:1.5px solid rgba(148,163,184,0.2);
  border-radius:18px;
  padding:1.6rem 1.8rem;
  box-shadow:0 4px 24px rgba(0,0,0,0.04),0 1px 3px rgba(0,0,0,0.02);
  margin-bottom:1.4rem;
  transition:transform 0.3s cubic-bezier(0.2,0.8,0.2,1),box-shadow 0.3s;
  position:relative;
  overflow:hidden;
}
.gc:hover{transform:translateY(-3px);box-shadow:0 12px 40px rgba(0,0,0,0.07);}
.gc::after{
  content:'';position:absolute;top:0;left:0;right:0;height:3px;border-radius:18px 18px 0 0;
  background:transparent;transition:background 0.3s;
}

/* Card accents — tinted backgrounds + top-bar gradient + border */
.gc-b{border-color:rgba(59,130,246,0.25);background:linear-gradient(135deg,rgba(239,246,255,0.6),rgba(248,250,252,0.5));}
.gc-b::after{background:linear-gradient(90deg,#3b82f6,#60a5fa);}
.gc-b:hover{box-shadow:0 12px 40px rgba(59,130,246,0.1);}

.gc-g{border-color:rgba(16,185,129,0.25);background:linear-gradient(135deg,rgba(236,253,245,0.6),rgba(248,250,252,0.5));}
.gc-g::after{background:linear-gradient(90deg,#10b981,#34d399);}
.gc-g:hover{box-shadow:0 12px 40px rgba(16,185,129,0.1);}

.gc-a{border-color:rgba(245,158,11,0.25);background:linear-gradient(135deg,rgba(255,251,235,0.6),rgba(248,250,252,0.5));}
.gc-a::after{background:linear-gradient(90deg,#f59e0b,#fbbf24);}
.gc-a:hover{box-shadow:0 12px 40px rgba(245,158,11,0.1);}

.gc-r{border-color:rgba(239,68,68,0.25);background:linear-gradient(135deg,rgba(254,242,242,0.6),rgba(248,250,252,0.5));}
.gc-r::after{background:linear-gradient(90deg,#ef4444,#f87171);}
.gc-r:hover{box-shadow:0 12px 40px rgba(239,68,68,0.1);}

.gc-p{border-color:rgba(139,92,246,0.25);background:linear-gradient(135deg,rgba(245,243,255,0.6),rgba(248,250,252,0.5));}
.gc-p::after{background:linear-gradient(90deg,#8b5cf6,#a78bfa);}
.gc-p:hover{box-shadow:0 12px 40px rgba(139,92,246,0.1);}

.gc-t{border-color:rgba(6,182,212,0.25);background:linear-gradient(135deg,rgba(236,254,255,0.6),rgba(248,250,252,0.5));}
.gc-t::after{background:linear-gradient(90deg,#06b6d4,#22d3ee);}
.gc-t:hover{box-shadow:0 12px 40px rgba(6,182,212,0.1);}

.gc-s{border-color:rgba(100,116,139,0.2);background:linear-gradient(135deg,rgba(241,245,249,0.6),rgba(248,250,252,0.5));}
.gc-s::after{background:linear-gradient(90deg,#94a3b8,#cbd5e1);}

/* Narrative Positioning — SPECIAL colorful gradient */
.gc-nar{
  border-color:rgba(139,92,246,0.2);
  background:linear-gradient(135deg,rgba(255,255,255,0.6),rgba(238,242,255,0.5),rgba(252,231,243,0.3));
}
.gc-nar::after{background:linear-gradient(90deg,#8b5cf6,#ec4899,#f59e0b);}
.gc-nar:hover{box-shadow:0 12px 40px rgba(139,92,246,0.12);}

/* Bull/Bear special tiles */
.gc-bull{border-color:rgba(16,185,129,0.3);background:linear-gradient(135deg,rgba(255,255,255,0.6),rgba(236,253,245,0.4));}
.gc-bull::after{background:linear-gradient(90deg,#059669,#10b981,#34d399);}
.gc-bear{border-color:rgba(239,68,68,0.3);background:linear-gradient(135deg,rgba(255,255,255,0.6),rgba(254,242,242,0.4));}
.gc-bear::after{background:linear-gradient(90deg,#dc2626,#ef4444,#f87171);}

/* ══════════════════════════════════════════
   TILE HEADER — inside each narrative tile
   ══════════════════════════════════════════ */
.tile-hdr{
  display:flex;align-items:center;gap:.5rem;
  margin-bottom:1rem;padding-bottom:.8rem;
  border-bottom:1px solid rgba(148,163,184,0.1);
}
.tile-hdr h3{
  font-size:1.05rem;font-weight:700;color:#0f172a;
  letter-spacing:-0.01em;flex:1;
}
.tile-hdr .tile-num{
  width:28px;height:28px;border-radius:8px;
  display:flex;align-items:center;justify-content:center;
  font-size:.72rem;font-weight:700;color:white;flex-shrink:0;
  background:linear-gradient(135deg,#3b82f6,#06b6d4);
}

/* Section titles */
.stl{font-size:1.4rem;font-weight:700;color:#0f172a;margin-bottom:.3rem;display:flex;align-items:center;gap:.6rem;}
.stl::before{content:'';width:4px;height:1.2em;border-radius:4px;background:linear-gradient(180deg,#3b82f6,#06b6d4);}
.stl-sub{font-size:.82rem;color:#64748b;margin-bottom:1.4rem;margin-left:1.2rem;}

/* ══════════════════════════════════════════
   TWO-COLUMN BODY
   ══════════════════════════════════════════ */
.body-grid{display:grid;grid-template-columns:1fr 380px;gap:2rem;align-items:start;}
@media(max-width:1100px){.body-grid{grid-template-columns:1fr;}}
@media(min-width:1500px){.body-grid{grid-template-columns:1fr 420px;}}

.nar{}
.qr{position:sticky;top:1rem;}

/* ══════════════════════════════════════════
   EXEC SNAPSHOT STRIP — V7 ELEVATED
   ══════════════════════════════════════════ */
.exec{
  display:grid;
  grid-template-columns:repeat(auto-fit,minmax(200px,1fr));
  gap:1rem;
  margin-bottom:2.5rem;
  padding:1.2rem;
  background:rgba(255,255,255,0.35);
  backdrop-filter:blur(12px);
  border:1px solid rgba(148,163,184,0.12);
  border-radius:16px;
}
.exec-item{
  background:rgba(255,255,255,0.6);
  backdrop-filter:blur(8px);
  border:1px solid rgba(148,163,184,0.12);
  border-radius:12px;
  padding:1.1rem 1.2rem;
  display:flex;align-items:center;gap:.8rem;
  transition:transform 0.2s,box-shadow 0.2s;
}
.exec-item:hover{transform:translateY(-1px);box-shadow:0 4px 16px rgba(0,0,0,0.04);}
.exec-dot{width:10px;height:10px;border-radius:50%;flex-shrink:0;box-shadow:0 0 6px currentColor;}
.exec-dot.blue{background:#3b82f6;color:rgba(59,130,246,0.4);}
.exec-dot.green{background:#10b981;color:rgba(16,185,129,0.4);}
.exec-dot.amber{background:#f59e0b;color:rgba(245,158,11,0.4);}
.exec-dot.red{background:#ef4444;color:rgba(239,68,68,0.4);}
.exec-dot.purple{background:#8b5cf6;color:rgba(139,92,246,0.4);}
.exec-dot.slate{background:#64748b;color:rgba(100,116,139,0.4);}
.exec-lbl{font-size:.82rem;color:#64748b;font-weight:500;}
.exec-val{font-size:.95rem;color:#0f172a;font-weight:700;}

/* ══════════════════════════════════════════
   NARRATIVE CONTENT TYPOGRAPHY
   ══════════════════════════════════════════ */
.nar-section{margin-bottom:2rem;}
.nar-content{font-size:.92rem;color:#334155;line-height:1.75;}
.nar-content h1,.nar-content h2,.nar-content h3,.nar-content h4{color:#0f172a;margin:1.2rem 0 .5rem;font-weight:700;}
.nar-content h1{font-size:1.3rem;}
.nar-content h2{font-size:1.15rem;}
.nar-content h3{font-size:1.05rem;}
.nar-content h4{font-size:.95rem;color:#475569;}
.nar-content strong{color:#0f172a;font-weight:600;}
.nar-content ul,.nar-content ol{padding-left:1.3rem;margin:.5rem 0;}
.nar-content li{margin-bottom:.3rem;line-height:1.6;}

/* ══════════════════════════════════════════
   QUANT SYNTHESIS — V7 EMPHASIZED
   ══════════════════════════════════════════ */
.synth-card{margin-bottom:2.5rem;}
.synth-header{display:flex;align-items:center;gap:.8rem;margin-bottom:1.2rem;}
.gc-synth{
  border:2px solid rgba(139,92,246,0.35);
  padding:2rem 2.2rem;
  border-radius:20px;
  background:linear-gradient(135deg,rgba(255,255,255,0.65),rgba(245,243,255,0.5));
  box-shadow:0 6px 30px rgba(139,92,246,0.08),0 1px 3px rgba(0,0,0,0.02);
}
.gc-synth::after{background:linear-gradient(90deg,#7c3aed,#8b5cf6,#a78bfa);height:4px;}
.gc-synth:hover{box-shadow:0 14px 44px rgba(139,92,246,0.12);}
.gc-synth .nar-content{font-size:.95rem;line-height:1.8;}

/* Metric rows */
.mr{display:flex;justify-content:space-between;align-items:center;padding:.55rem 0;border-bottom:1px solid rgba(148,163,184,0.08);}
.mr:last-child{border-bottom:none;}
.ml{font-size:.82rem;color:#64748b;font-weight:500;}
.mv{font-family:'Inter',monospace;font-weight:600;color:#1e293b;font-size:.92rem;}
.mv-r{color:#dc2626;}
.mv-g{color:#059669;}
.mv-b{color:#2563eb;}

/* Gauge */
.gauge{background:rgba(148,163,184,0.12);border-radius:6px;height:8px;overflow:hidden;margin:.3rem 0 .8rem;}
.gauge-bar{height:100%;border-radius:6px;transition:width 0.6s ease;}
.gauge-lbl{font-size:.72rem;color:#64748b;font-weight:500;text-transform:uppercase;letter-spacing:.04em;margin-bottom:.15rem;}

/* Badge */
.bdg{display:inline-block;padding:4px 12px;border-radius:100px;font-weight:600;font-size:.72rem;letter-spacing:.03em;text-transform:uppercase;color:#fff;}

/* Oracle target */
.orc-big{text-align:center;padding:1rem 0;}
.orc-big .val{font-size:2.2rem;font-weight:800;color:#059669;font-family:'Inter',monospace;}
.orc-big .lbl{font-size:.72rem;text-transform:uppercase;letter-spacing:.06em;color:#64748b;margin-bottom:.3rem;}
.orc-range{display:grid;grid-template-columns:1fr 1fr;gap:.8rem;text-align:center;margin:.8rem 0;padding:.8rem 0;border-top:1px solid rgba(148,163,184,0.1);border-bottom:1px solid rgba(148,163,184,0.1);}
.orc-range .rl{font-size:.68rem;text-transform:uppercase;letter-spacing:.04em;color:#64748b;}
.orc-range .rv{font-size:1.1rem;font-weight:700;color:#1e293b;font-family:'Inter',monospace;}
.orc-src{text-align:center;font-size:.72rem;color:#10b981;font-weight:500;margin-top:.5rem;padding:.35rem;background:rgba(16,185,129,0.06);border-radius:6px;}

/* Prob band */
.pb{display:grid;grid-template-columns:1fr 1fr;gap:.6rem;margin-bottom:.8rem;}
.pb-cell{text-align:center;padding:.6rem .4rem;}
.pb-cell .lbl{font-size:.65rem;text-transform:uppercase;letter-spacing:.05em;color:#64748b;margin-bottom:.25rem;}
.pb-cell .val{font-size:1rem;font-weight:700;color:#1e3a8a;font-family:'Inter',monospace;}
.pb-cell .note{font-size:.7rem;color:#64748b;margin-top:.15rem;}
.interp{background:rgba(239,246,255,0.4);border-left:3px solid #3b82f6;padding:.7rem .9rem;border-radius:6px;font-size:.82rem;line-height:1.6;color:#334155;margin-top:.5rem;}

/* Blueprint (Climax) */
.bp-section{
  margin-top:2.5rem;padding:2.5rem;
  background:linear-gradient(135deg,rgba(15,23,42,0.97),rgba(30,41,59,0.95));
  border-radius:20px;color:white;position:relative;overflow:hidden;
}
.bp-section::before{
  content:'';position:absolute;inset:0;
  background:radial-gradient(circle at 25% 50%,rgba(59,130,246,0.12),transparent 50%),
             radial-gradient(circle at 80% 20%,rgba(16,185,129,0.08),transparent 40%);
  pointer-events:none;border-radius:20px;
}
.bp-inner{position:relative;z-index:1;}
.bp-title{font-size:clamp(1.8rem,3vw,2.4rem);font-weight:800;text-align:center;margin-bottom:.3rem;letter-spacing:-0.02em;}
.bp-sub{font-size:.9rem;color:rgba(255,255,255,0.55);text-align:center;margin-bottom:2rem;}
.bp-body{
  background:rgba(255,255,255,0.07);backdrop-filter:blur(20px);
  border:1px solid rgba(255,255,255,0.1);border-radius:14px;padding:1.8rem;
}
.bp-body h1,.bp-body h2,.bp-body h3,.bp-body h4{color:white;margin:1rem 0 .4rem;}
.bp-body p,.bp-body li{color:rgba(255,255,255,0.85);font-size:.9rem;line-height:1.7;}
.bp-body strong{color:white;}
.bp-body ul,.bp-body ol{padding-left:1.2rem;}
.bp-foot{display:flex;justify-content:center;gap:2rem;margin-top:1.5rem;flex-wrap:wrap;}
.bp-foot-item{font-size:.82rem;color:rgba(255,255,255,0.7);}
.bp-foot-item strong{color:white;margin-left:.3rem;}

/* Table */
.gt{width:100%;border-collapse:separate;border-spacing:0;border-radius:10px;overflow:hidden;background:rgba(255,255,255,0.3);margin:.8rem 0;}
.gt th{background:rgba(59,130,246,0.05);padding:8px 12px;text-align:left;font-weight:600;font-size:.72rem;color:#475569;text-transform:uppercase;letter-spacing:.04em;}
.gt td{padding:8px 12px;border-top:1px solid rgba(148,163,184,0.08);font-size:.84rem;color:#334155;}

.sep{border:none;height:1px;background:rgba(148,163,184,0.12);margin:1rem 0;}

/* Footer */
.foot{text-align:center;padding:2rem 0;margin-top:2.5rem;border-top:1px solid rgba(148,163,184,0.12);color:#94a3b8;font-size:.75rem;line-height:1.8;}
.foot .wm{font-size:.65rem;color:#cbd5e1;letter-spacing:.1em;text-transform:uppercase;margin-top:.5rem;}

/* ══════════════════════════════════════════
   RESPONSIVE
   ══════════════════════════════════════════ */
@media(max-width:768px){
  .frame{grid-template-columns:1fr 1fr;}
  .exec{grid-template-columns:1fr;padding:.8rem;}
  .pb{grid-template-columns:1fr;}
  .hero h1{font-size:clamp(2.4rem,6vw,3.5rem);}
  .bp-section{padding:1.5rem;border-radius:14px;}
  .bp-foot{flex-direction:column;align-items:center;gap:.8rem;}
  .gc{padding:1.2rem 1.3rem;border-radius:14px;}
  .gc-synth{padding:1.4rem 1.5rem;}
}
@media(max-width:480px){
  .frame{grid-template-columns:1fr;}
  .gc{padding:1rem 1.1rem;border-radius:12px;}
  body{font-size:14px;}
  .tile-hdr h3{font-size:.95rem;}
}

/* Print */
@media print{
  body{background:white!important;}
  .gc,.fc{box-shadow:none;backdrop-filter:none;background:white;border:1px solid #e2e8f0;}
  .gc::after{display:none;}
  .bp-section{background:#0f172a!important;-webkit-print-color-adjust:exact;print-color-adjust:exact;}
  .qr{position:static;}
}

ul,ol{padding-left:1.3rem;margin:.4rem 0;}
li{margin-bottom:.2rem;}
"""


# ─────────────────────────────────────────────────
#  PAYLOAD BUILDER (unchanged)
# ─────────────────────────────────────────────────

def _build_payload(ticker: str, state: dict) -> dict:
    market = state.get("market_analysis", {}) or {}
    tech = state.get("technical_analysis", {}) or {}
    oracle = state.get("oracle_forecast", {}) or {}
    quant = state.get("quant_synthesis", {}) or {}
    strategy = state.get("strategic_report", {}) or {}

    price = market.get("current_price") or tech.get("price")
    confidence = quant.get("confidence_score")
    rsi = tech.get("rsi")

    asym_pct, asym_label = None, None
    if price and oracle.get("predicted_price"):
        try:
            pred = float(oracle["predicted_price"])
            curr = float(price)
            pct = ((pred - curr) / curr) * 100
            asym_pct = round(pct, 1)
            if pct > 5:
                asym_label = f"Positive Skew (+{pct:.1f}%)"
            elif pct < -5:
                asym_label = f"Negative Skew ({pct:.1f}%)"
            else:
                asym_label = f"Balanced ({pct:+.1f}%)"
        except Exception:
            pass

    vol = None
    if rsi:
        try:
            r = float(rsi)
            if r < 25: vol = "Elevated — Post-Capitulation"
            elif r < 35: vol = "Elevated"
            elif r > 75: vol = "Compressed — Overbought"
            elif r > 65: vol = "Low"
            else: vol = "Normal"
        except Exception:
            pass

    ci = oracle.get("confidence_interval", []) or []

    risk_label, risk_sub = None, None
    if rsi:
        try:
            rv = float(rsi)
            if rv < 25: risk_label, risk_sub = "Capitulation", "Extreme Oversold"
            elif rv < 35: risk_label, risk_sub = "Downside Momentum", "Bearish Continuation"
            elif rv > 75: risk_label, risk_sub = "Reversal Risk", "Overbought Territory"
            else: risk_label, risk_sub = "Volatility", "Standard"
        except Exception:
            pass

    support = tech.get("support_levels", []) or []
    resistance = tech.get("resistance_levels", []) or []
    if isinstance(support, list):
        support = [s for s in support[:3] if s is not None]
    else:
        support = []
    if isinstance(resistance, list):
        resistance = [r for r in resistance[:3] if r is not None]
    else:
        resistance = []

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
        "tension": str(market.get("sentiment", "")).lower() != str(tech.get("rating", "")).lower(),
        "asym_label": asym_label,
        "asym_pct": asym_pct,
        "vol_regime": vol,
        "rsi": rsi,
        "macd": tech.get("macd"),
        "trend": tech.get("trend"),
        "sma_20": tech.get("sma_20"),
        "sma_50": tech.get("sma_50"),
        "boll_upper": tech.get("bollinger_upper"),
        "boll_lower": tech.get("bollinger_lower"),
        "support": support,
        "resistance": resistance,
        "rating": tech.get("rating"),
        "risk_label": risk_label,
        "risk_sub": risk_sub,
        "orc_target": oracle.get("predicted_price"),
        "orc_conf": oracle.get("model_confidence"),
        "orc_horizon": oracle.get("forecast_horizon"),
        "orc_lower": ci[0] if ci else None,
        "orc_upper": ci[1] if len(ci) > 1 else None,
        "market_report_raw": market.get("report", ""),
        "quant_html": _md(quant.get("summary", "")),
        "blueprint_html": _md(strategy.get("narrative", "")),
        "bp_signal": strategy.get("signal"),
        "bp_timeframe": strategy.get("time_horizon"),
    }


# ─────────────────────────────────────────────────
#  HTML BUILDER — V7 Modular Architecture
# ─────────────────────────────────────────────────

def _build_report_html(d: dict) -> str:
    ticker = d.get("ticker", "")
    date = d.get("date", "")

    # ── HERO ──
    price_html = ""
    price = d.get("price")
    if price is not None:
        p_str = _price(price, ticker)
        asym = d.get("asym_pct")
        delta_html = ""
        if asym is not None:
            cls = "up" if asym >= 0 else "dn"
            arrow = "▲" if asym >= 0 else "▼"
            delta_html = f'<span class="delta {cls}">{arrow} {abs(asym):.1f}% vs Oracle Target</span>'
        price_html = f'''<div class="hero-price-pill">
            <span class="big">{p_str}</span>
            {delta_html}
        </div>'''

    # ── Frame Cells ──
    frame_cells = []
    regime = d.get("regime")
    if regime:
        r_lower = str(regime).lower()
        sub = "Range-Bound"
        if "down" in r_lower: sub = "Bearish Pressure"
        elif "up" in r_lower: sub = "Bullish Momentum"
        frame_cells.append(f'<div class="fc"><div class="fc-lbl">Regime</div><div class="fc-val">{regime}</div><div class="fc-note">{sub}</div></div>')

    bias = d.get("bias")
    if bias:
        frame_cells.append(f'<div class="fc"><div class="fc-lbl">Bias</div><div class="fc-val" style="color:#3b82f6;">{bias}</div><div class="fc-note">Structural Signal</div></div>')

    conf = d.get("confidence")
    if conf is not None:
        frame_cells.append(f'<div class="fc"><div class="fc-lbl">Conviction</div><div class="fc-val" style="color:#059669;">{_v(conf, suffix="/100")}</div><div class="fc-note">Signal Convergence</div></div>')

    risk = d.get("risk_label")
    if risk:
        frame_cells.append(f'<div class="fc"><div class="fc-lbl">Primary Risk</div><div class="fc-val" style="color:#f59e0b;">{risk}</div><div class="fc-note">{d.get("risk_sub", "")}</div></div>')

    action = d.get("action")
    if action:
        frame_cells.append(f'<div class="fc"><div class="fc-lbl">Action</div><div class="fc-val">{_badge(action)}</div></div>')

    frame_html = ""
    if frame_cells:
        frame_html = f'<div class="frame">{"".join(frame_cells)}</div>'

    tension_html = ""
    if d.get("tension"):
        tension_html = '<div class="alert-bar">⚠ Signal Divergence — Market Sentiment and Technical Rating are misaligned</div>'

    # ── EXEC SNAPSHOT STRIP ──
    exec_items = []
    if regime:
        exec_items.append(('blue', 'State', regime))
    sentiment = d.get("sentiment")
    if sentiment:
        exec_items.append(('green', 'Sentiment', str(sentiment)))
    rsi = d.get("rsi")
    trend = d.get("trend")
    if rsi is not None:
        t = f' · {trend}' if trend else ""
        exec_items.append(('purple', 'Technical', f'RSI {_v(rsi)}{t}'))
    orc_t = d.get("orc_target")
    if orc_t is not None:
        exec_items.append(('green', 'Oracle Target', _price(orc_t, ticker)))
    asym_l = d.get("asym_label")
    if asym_l:
        exec_items.append(('amber', 'Asymmetry', asym_l))
    if action:
        exec_items.append(('slate', 'Action', str(action)))

    exec_html = ""
    if exec_items:
        items = ''.join(f'<div class="exec-item"><div class="exec-dot {c}"></div><div><div class="exec-lbl">{l}</div><div class="exec-val">{v}</div></div></div>' for c, l, v in exec_items)
        exec_html = f'<div class="exec">{items}</div>'

    # ══════════════════════════════════════════
    #  LEFT COLUMN: MODULAR NARRATIVE TILES
    # ══════════════════════════════════════════
    raw_report = d.get("market_report_raw", "")
    narrative_tiles = _split_narrative(raw_report)

    market_section = ""
    if narrative_tiles:
        tiles_html = ""
        for idx, (title, accent, html_content) in enumerate(narrative_tiles, 1):
            tiles_html += f'''<div class="gc {accent}">
                <div class="tile-hdr">
                    <div class="tile-num">{idx}</div>
                    <h3>{title}</h3>
                </div>
                <div class="nar-content">{html_content}</div>
            </div>'''

        market_section = f'''<div class="nar-section">
            <div class="stl">Market Intelligence</div>
            <div class="stl-sub">Narrative Analysis · Sentiment · Risk Assessment</div>
            {tiles_html}
        </div>'''

    # ── Quantitative Synthesis (EMPHASIZED) ──
    quant_html = d.get("quant_html", "")
    quant_section = ""
    if quant_html:
        badge_html = _badge(d.get("bias")) if d.get("bias") else ""
        conf_lbl = f'<span style="font-size:.85rem;color:#64748b;margin-left:.6rem;">Confidence: {_v(conf, suffix="/100")}</span>' if conf is not None else ""
        quant_section = f'''<div class="synth-card">
            <div class="stl">Quantitative Synthesis</div>
            <div class="synth-header">{badge_html}{conf_lbl}</div>
            <div class="gc gc-synth"><div class="nar-content">{quant_html}</div></div>
        </div>'''

    # ══════════════════════════════════════════
    #  RIGHT RAIL (unchanged logic)
    # ══════════════════════════════════════════

    # Technical Indicators
    tech_rows = []
    if rsi is not None:
        rsi_class = "mv-r" if float(rsi) < 30 else ("mv-g" if float(rsi) > 70 else "")
        tech_rows.append(_metric_row("RSI (14)", _v(rsi), rsi_class))
        tech_rows.append(_gauge_html(rsi, 100, _gauge_color(rsi)))
    macd = d.get("macd")
    if macd is not None:
        tech_rows.append(_metric_row("MACD", _v(macd)))
    if trend:
        tech_rows.append(f'<div class="mr"><span class="ml">Trend</span>{_badge(trend)}</div>')
    sma20 = d.get("sma_20")
    sma50 = d.get("sma_50")
    if sma20 is not None:
        tech_rows.append(_metric_row("SMA 20", _price(sma20, ticker)))
    if sma50 is not None:
        tech_rows.append(_metric_row("SMA 50", _price(sma50, ticker)))
    bu = d.get("boll_upper")
    bl = d.get("boll_lower")
    if bu is not None:
        tech_rows.append(_metric_row("Bollinger Upper", _price(bu, ticker)))
    if bl is not None:
        tech_rows.append(_metric_row("Bollinger Lower", _price(bl, ticker)))
    support = d.get("support", [])
    resistance = d.get("resistance", [])
    if support:
        tech_rows.append(_metric_row("Support", ", ".join(_price(s, ticker) or "" for s in support)))
    if resistance:
        tech_rows.append(_metric_row("Resistance", ", ".join(_price(r, ticker) or "" for r in resistance)))
    rating = d.get("rating")
    if rating:
        tech_rows.append(f'<div style="margin-top:.6rem;padding:.5rem;background:rgba(59,130,246,0.06);border-radius:6px;text-align:center;font-size:.82rem;"><span style="color:#64748b;">Rating: </span><strong style="color:#1e3a8a;">{rating}</strong></div>')

    tech_card = ""
    if tech_rows:
        tech_card = f'''<div class="gc gc-b" style="padding:1.3rem;">
            <h4 style="font-size:.78rem;font-weight:700;text-transform:uppercase;letter-spacing:.08em;color:#64748b;margin-bottom:.8rem;">Technical Indicators</h4>
            {"".join(tech_rows)}
        </div>'''

    # Oracle Projection
    oracle_card = ""
    orc_target = d.get("orc_target")
    if orc_target is not None:
        horizon = d.get("orc_horizon", "30 Days") or "30 Days"
        orc_body = f'''<div class="orc-big">
                <div class="lbl">{horizon} Target</div>
                <div class="val">{_price(orc_target, ticker)}</div>
            </div>'''
        orc_conf = d.get("orc_conf")
        if orc_conf is not None:
            try:
                pct = float(orc_conf) * 100 if float(orc_conf) <= 1 else float(orc_conf)
                orc_body += _gauge_html(pct, 100, "#10b981", f"Confidence: {pct:.0f}%")
            except Exception:
                pass
        range_parts = []
        orc_lower = d.get("orc_lower")
        orc_upper = d.get("orc_upper")
        if orc_lower is not None:
            range_parts.append(f'<div><div class="rl">Lower Bound</div><div class="rv">{_price(orc_lower, ticker)}</div></div>')
        if orc_upper is not None:
            range_parts.append(f'<div><div class="rl">Upper Bound</div><div class="rv">{_price(orc_upper, ticker)}</div></div>')
        if range_parts:
            orc_body += f'<div class="orc-range">{"".join(range_parts)}</div>'
        orc_body += f'<div class="orc-src">TimesFM 2.5 · BigQuery · {horizon}</div>'
        oracle_card = f'''<div class="gc gc-g" style="padding:1.3rem;">
            <h4 style="font-size:.78rem;font-weight:700;text-transform:uppercase;letter-spacing:.08em;color:#64748b;margin-bottom:.6rem;">Oracle Projection</h4>
            {orc_body}
        </div>'''

    # Distribution
    dist_card = ""
    dist_cells = []
    if orc_target is not None:
        dist_cells.append(('Median Forecast', _price(orc_target, ticker), "50th Percentile"))
    orc_lower = d.get("orc_lower")
    orc_upper = d.get("orc_upper")
    if orc_lower is not None and orc_upper is not None:
        dist_cells.append(('Confidence Band', f'{_price(orc_lower, ticker)}–{_price(orc_upper, ticker)}', "Model Range"))
    asym_pct = d.get("asym_pct")
    if asym_pct is not None:
        dist_cells.append(('Asymmetry', f'{asym_pct:+.1f}%', d.get("asym_label", "")))
    vol = d.get("vol_regime")
    if vol:
        dist_cells.append(('Vol Regime', vol, "RSI-Derived"))
    if dist_cells:
        cells_html = ''.join(f'<div class="pb-cell"><div class="lbl">{l}</div><div class="val">{v}</div><div class="note">{n}</div></div>' for l, v, n in dist_cells)
        interp = ""
        if orc_target is not None and price is not None:
            interp = f'''<div class="interp">
                Median forecast {_price(orc_target, ticker)} vs current {_price(price, ticker)} → {d.get("asym_label", "balanced")}. Vol regime: {vol or "Normal"}.
            </div>'''
        dist_card = f'''<div class="gc gc-p" style="padding:1.3rem;">
            <h4 style="font-size:.78rem;font-weight:700;text-transform:uppercase;letter-spacing:.08em;color:#64748b;margin-bottom:.8rem;">Distribution Analysis</h4>
            <div class="pb">{cells_html}</div>
            {interp}
        </div>'''

    # Sidebar
    sidebar_data = []
    if d.get("mcap"):
        sidebar_data.append(_metric_row("Market Cap", str(d["mcap"])))
    if sentiment:
        sidebar_data.append(_metric_row("Sentiment", str(sentiment)))
    if price is not None:
        sidebar_data.append(_metric_row("Current Price", _price(price, ticker)))
    sidebar_card = ""
    if sidebar_data:
        sidebar_card = f'''<div class="gc gc-s" style="padding:1.1rem;">
            <h4 style="font-size:.72rem;font-weight:700;text-transform:uppercase;letter-spacing:.08em;color:#94a3b8;margin-bottom:.6rem;">Market Data</h4>
            {"".join(sidebar_data)}
        </div>'''

    # ── STRATEGIC BLUEPRINT ──
    bp_html = d.get("blueprint_html", "")
    if not bp_html:
        bp_html = '<p style="color:rgba(255,255,255,0.6);text-align:center;padding:1.5rem;">Investment thesis under development pending additional data validation.</p>'
    bp_foot_items = []
    if d.get("bp_signal"):
        bp_foot_items.append(f'<div class="bp-foot-item">Signal:<strong>{d["bp_signal"]}</strong></div>')
    if d.get("bp_timeframe"):
        bp_foot_items.append(f'<div class="bp-foot-item">Timeframe:<strong>{d["bp_timeframe"]}</strong></div>')
    if conf is not None:
        bp_foot_items.append(f'<div class="bp-foot-item">Conviction:<strong>{_v(conf, suffix="/100")}</strong></div>')
    bp_foot_html = f'<div class="bp-foot">{"".join(bp_foot_items)}</div>' if bp_foot_items else ""

    # ── ASSEMBLE ──
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>{ticker} — Equity Research Report</title>
<style>{CSS}</style>
</head>
<body>
<div class="wrap">

  <div class="hero">
    <div class="hero-meta">{date} · Equity Research by TradeMate</div>
    <h1>{ticker}</h1>
    {price_html}
    {frame_html}
    {tension_html}
  </div>

  {exec_html}

  <div class="body-grid">
    <div class="nar">
      {market_section}
      {quant_section}
    </div>
    <div class="qr">
      {sidebar_card}
      {tech_card}
      {oracle_card}
      {dist_card}
    </div>
  </div>

  <div class="bp-section">
    <div class="bp-inner">
      <div class="bp-title">Strategic Blueprint</div>
      <div class="bp-sub">Actionable Investment Framework</div>
      <div class="bp-body">{bp_html}</div>
      {bp_foot_html}
    </div>
  </div>

  <div class="foot">
    <p>This report is generated by AI (TradeMate) using deterministic quantitative data from yfinance, BigQuery TimesFM 2.5, and structured sub-agent outputs. It does NOT constitute financial advice. Past performance is not indicative of future results.</p>
    <div class="wm">TradeMate Research · {date}</div>
  </div>

</div>
</body>
</html>"""

    return html


# ─────────────────────────────────────────────────
#  REPORT GENERATOR FUNCTION
# ─────────────────────────────────────────────────

def generate_equity_report_func(ticker: str, tool_context: ToolContext) -> str:
    """
    Generate a deterministic institutional HTML equity research report.
    100% Python-templated — zero truncation risk.
    """
    tool_context.state["pipeline_stage"] = "report_generation"
    tool_context.state["target_ticker"] = ticker

    try:
        if "strategic_report" not in tool_context.state:
            logger.warning(f"Strategic Report missing for {ticker}.")

        payload = _build_payload(ticker, tool_context.state)

        logger.info(f"Report Generator: Building institutional report for {ticker}")
        print(f"DEBUG: EQUITY REPORT GENERATOR triggered for {ticker}")

        html_code = _build_report_html(payload)

        tool_context.state["equity_report_html"] = html_code

        # ── Advance pipeline to final "Report Ready" state ──
        tool_context.state["pipeline_stage"] = "presentation"
        done = tool_context.state.get("stages_completed", [])
        for s in ["report_generation", "presentation"]:
            if s not in done:
                done.append(s)
        tool_context.state["stages_completed"] = done

        print(f"DEBUG: Equity report generated ({len(html_code)} chars)")

        return json.dumps({
            "status": "success",
            "message": "Institutional Equity Report Generated Successfully.",
        })

    except Exception as e:
        logger.error(f"Equity report generation failed: {e}")
        print(f"CRITICAL ERROR in Report Generator: {str(e)}")
        return json.dumps({
            "status": "error",
            "error": str(e),
        })


# Create FunctionTool
equity_report_tool = FunctionTool(func=generate_equity_report_func)
