"""earnings-pillar-diff - live demo (Streamlit Community Cloud).

Reads the committed report under reports/*.jsonl and shows the filing
line-item deltas against the comparable prior period for a hyperscaler print,
ranked by absolute change, with the affected thesis pillar and the committed
action. No network, no secrets - runs entirely off the committed fixture report.

Deploy: Streamlit Community Cloud -> New app -> repo AthenaTheOwl/earnings-pillar-diff,
branch main, main file streamlit_app.py.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import streamlit as st

from earnings_pillar_diff.scoring import comparison_basis, filing_form
from earnings_pillar_diff.xbrl import is_lease_commitment, line_item_label

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


def row_label(row: dict) -> str:
    # a purchase-obligation tag on a lease axis is a lease commitment
    return line_item_label(str(row.get("tag", "?")), row.get("axis"))


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


st.set_page_config(page_title="earnings-pillar-diff - filing delta memo", layout="wide")
st.title("earnings-pillar-diff")
st.caption(
    "filing capex and lease-commitment deltas against the comparable prior "
    "period for a hyperscaler print, mapped onto a named thesis pillar with a "
    "committed action. a fact on a lease axis is read as a lease, whatever its "
    "tag is called, and its lease classes are summed."
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
form = filing_form(str(quarter))

st.subheader(f"{ticker} {quarter} {form} - line-item deltas vs {comparison_basis(form)}")

ranked = sorted(deltas, key=lambda d: abs(parse_usd(d.get("delta"))), reverse=True)
top = ranked[0]

c1, c2, c3 = st.columns(3)
c1.metric("material deltas", len(deltas))
c2.metric("biggest move", top.get("delta", "?"), help=row_label(top))
c3.metric("action", action, help="committed thesis action for this print")

table = [
    {
        "line item": row_label(r),
        "XBRL tag": short_tag(r.get("tag", "?")),
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
    f"**biggest move:** {row_label(top)} "
    f"{top.get('prior')} -> {top.get('current')} "
    f"({top.get('delta')}, {top.get('percent_delta')}). "
    f"pillar(s): {pillars}. action on {ticker} {quarter}: **{action}**."
)

for r in ranked:
    if not is_lease_commitment(str(r.get("tag", "")), r.get("axis")):
        continue
    st.caption(
        f"{row_label(r)}: {r.get('tag')} on {r.get('axis')} is a lease commitment, "
        f"not a purchase obligation. members summed: prior "
        f"{' + '.join(r.get('prior_members') or []) or 'none'}; current "
        f"{' + '.join(r.get('current_members') or []) or 'none'}."
    )
    first = r.get("as_first_reported")
    if isinstance(first, dict):
        st.caption(
            f"corrected {r.get('corrected', '?')}: first reported as {first.get('prior')} "
            f"-> {first.get('current')} ({first.get('delta')}, {first.get('percent_delta')}), "
            f"{first.get('basis', 'a different basis')}."
        )

if header.get("revert_threshold"):
    st.caption(f"revert threshold: {header['revert_threshold']}")
for note in header.get("corrections") or []:
    st.caption(f"correction: {note}")

# -------------------------------------------------------------------------
# interactive: drive the real diff engine on your own line items
# -------------------------------------------------------------------------
from earnings_pillar_diff.model import build_delta_rows, normalize_line_items

st.divider()
st.subheader("diff it yourself")
st.caption(
    "the section above is a committed report. below, you drive the repo's real "
    "engine: edit prior-period and current-period line-item values and "
    "`earnings_pillar_diff.model.build_delta_rows` recomputes every delta, "
    "percent change, and materiality flag live — the same code the `diff` CLI "
    "verb runs. materiality uses `scoring.material_delta` (delta >= "
    "min(5% of prior, USD 500M), or pct >= 5%)."
)

# pre-fill from the committed report so there is real data to edit.
prefill = [
    {
        "tag": short_tag(r.get("tag", "")),
        "prior (USD M)": parse_usd(r.get("prior")),
        "current (USD M)": parse_usd(r.get("current")),
    }
    for r in ranked
]
if not prefill:
    prefill = [{"tag": "PaymentsToAcquirePropertyPlantAndEquipment",
                "prior (USD M)": 44477.0, "current (USD M)": 64551.0}]

edited = st.data_editor(
    prefill,
    num_rows="dynamic",
    use_container_width=True,
    hide_index=True,
    key="line_item_editor",
    column_config={
        "tag": st.column_config.TextColumn("line item (XBRL tag)", required=True),
        "prior (USD M)": st.column_config.NumberColumn("prior (USD M)", format="%.1f"),
        "current (USD M)": st.column_config.NumberColumn("current (USD M)", format="%.1f"),
    },
)

# build the two line-item payloads the engine expects, then call it for real.
prior_payload = [
    {"tag": row["tag"], "value": row["prior (USD M)"]}
    for row in edited
    if str(row.get("tag", "")).strip() != ""
]
current_payload = [
    {"tag": row["tag"], "value": row["current (USD M)"]}
    for row in edited
    if str(row.get("tag", "")).strip() != ""
]

if not prior_payload:
    st.warning("add at least one line item (with a tag) to run the diff.")
else:
    try:
        prior_items = normalize_line_items(prior_payload)
        current_items = normalize_line_items(current_payload)
        rows = build_delta_rows(prior_items, current_items)
    except ValueError as exc:
        st.error(f"engine rejected the input: {exc}")
    else:
        ranked_live = sorted(rows, key=lambda r: abs(r.delta), reverse=True)
        material = [r for r in ranked_live if r.material]

        m1, m2, m3 = st.columns(3)
        m1.metric("line items", len(ranked_live))
        m2.metric("material moves", len(material), help="flagged by scoring.material_delta")
        if ranked_live:
            big = ranked_live[0]
            m3.metric(
                "biggest move",
                f"{big.delta:+,.1f}",
                help=f"{big.tag}: {big.prior:,.1f} -> {big.current:,.1f}",
            )

        out_table = [
            {
                "line item": r.tag,
                "prior": r.prior,
                "current": r.current,
                "delta": r.delta,
                "pct": "n/a" if r.percent_delta is None else f"{r.percent_delta * 100:+.1f}%",
                "material": "yes" if r.material else "no",
            }
            for r in ranked_live
        ]
        st.dataframe(out_table, use_container_width=True, hide_index=True)

        if material:
            top = ranked_live[0]
            pct = "n/a" if top.percent_delta is None else f"{top.percent_delta * 100:+.1f}%"
            st.success(
                f"engine flags **{len(material)}** material delta(s). biggest: "
                f"**{top.tag}** {top.prior:,.1f} -> {top.current:,.1f} "
                f"({top.delta:+,.1f}, {pct}) — this is the kind of move that would "
                f"trigger a memo + pillar re-check."
            )
        else:
            st.info(
                "no material deltas: every change is below the materiality "
                "threshold, so the engine would not raise a memo this quarter."
            )

st.caption(
    "v0.1 ships one MSFT fixture report. the committed view reads "
    "`reports/*.jsonl`; the interactive view above drives the real engine in "
    "`earnings_pillar_diff/model.py`. repo: github.com/AthenaTheOwl/earnings-pillar-diff"
)
