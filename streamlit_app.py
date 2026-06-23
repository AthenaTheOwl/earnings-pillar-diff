"""earnings-pillar-diff - live demo (Streamlit Community Cloud).

Reads the committed report under reports/*.jsonl and shows the quarter-over-
quarter 10-Q line-item deltas for a hyperscaler print, ranked by absolute
change, with the affected thesis pillar and the committed action. No network,
no secrets - runs entirely off the committed fixture report.

Deploy: Streamlit Community Cloud -> New app -> repo AthenaTheOwl/earnings-pillar-diff,
branch main, main file streamlit_app.py.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import streamlit as st

REPO = Path(__file__).resolve().parent
REPORTS = REPO / "reports"


def parse_usd(text) -> float:
    if isinstance(text, (int, float)):
        return float(text)
    cleaned = re.sub(r"[^\d.\-+]", "", str(text).replace(",", ""))
    if cleaned in {"", "-", "+", "."}:
        return 0.0
    try:
        return float(cleaned)
    except ValueError:
        return 0.0


def short_tag(tag: str) -> str:
    return str(tag).split(":", 1)[-1]


def load_report(path: Path) -> tuple[dict, list[dict]]:
    rows = [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    header: dict = {}
    deltas: list[dict] = []
    for row in rows:
        if row.get("type") == "report":
            header = row
        elif row.get("type") == "delta":
            deltas.append(row)
    return header, deltas


st.set_page_config(page_title="earnings-pillar-diff - 10-Q delta memo", layout="wide")
st.title("earnings-pillar-diff")
st.caption(
    "quarter-over-quarter 10-Q capex and purchase-obligation deltas for a "
    "hyperscaler print, mapped onto a named thesis pillar with a committed action."
)

files = sorted(REPORTS.glob("*.jsonl"))
if not files:
    st.warning("no report found under reports/*.jsonl")
    st.stop()

labels = {f.stem: f for f in files}
choice = st.selectbox("report", list(labels.keys()), index=len(labels) - 1)
header, deltas = load_report(labels[choice])

if not deltas:
    st.warning(f"{choice} has no delta rows")
    st.stop()

ticker = header.get("ticker", choice.split("-")[0])
quarter = header.get("quarter", "?")
action = header.get("action", "?")
pillars = ", ".join(header.get("pillars_affected", [])) or "none"

st.subheader(f"{ticker} {quarter} - line-item deltas vs prior quarter")

ranked = sorted(deltas, key=lambda d: abs(parse_usd(d.get("delta"))), reverse=True)
top = ranked[0]

c1, c2, c3 = st.columns(3)
c1.metric("material deltas", len(deltas))
c2.metric("biggest move", top.get("delta", "?"), help=short_tag(top.get("tag", "?")))
c3.metric("action", action, help="committed thesis action for this print")

table = [
    {
        "line item": short_tag(r.get("tag", "?")),
        "prior": r.get("prior"),
        "current": r.get("current"),
        "delta": r.get("delta"),
        "pct": r.get("percent_delta"),
        "|delta| (USD M)": abs(parse_usd(r.get("delta"))),
    }
    for r in ranked
]
st.dataframe(table, use_container_width=True, hide_index=True)

st.info(
    f"**biggest move:** {short_tag(top.get('tag', '?'))} "
    f"{top.get('prior')} -> {top.get('current')} "
    f"({top.get('delta')}, {top.get('percent_delta')}). "
    f"pillar(s): {pillars}. action on {ticker} {quarter}: **{action}**."
)

if header.get("revert_threshold"):
    st.caption(f"revert threshold: {header['revert_threshold']}")

st.caption(
    "v0.1 ships one MSFT fixture report. the data model + scoring live in "
    "`earnings_pillar_diff/`; this page reads the committed `reports/*.jsonl`. "
    "repo: github.com/AthenaTheOwl/earnings-pillar-diff"
)
