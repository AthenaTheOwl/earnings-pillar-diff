"""Read numeric facts out of a cached inline XBRL filing.

A tag name alone does not say what a number is. Microsoft files its
datacenter leases that have not yet commenced under
``us-gaap:UnrecordedUnconditionalPurchaseObligationBalanceSheetAmount``, but
on ``us-gaap:LeaseContractualTermAxis`` with issuer members
(``msft:OperatingLeaseMember``, ``msft:FinanceLeaseMember``). Read by tag
name, that fact looks like a purchase obligation. Read with its context, it
is a lease commitment.

So every fact keeps its dimensions, and a fact on a lease axis is labelled a
lease commitment whatever its concept is called. Lease-axis facts for one
concept and period are summed across members: the issuer splits the figure
by lease class in one filing and reports one combined figure under a single
member in the next, so only the sum compares like with like.

Facts on any other axis are left out of the line items: their members are
breakdowns of a total that is reported separately, and a line item built
from them would not match the undimensioned figure in the prior filing.
"""
from __future__ import annotations

import datetime as dt
import html
import re
from dataclasses import dataclass
from typing import Any

LEASE_AXES = frozenset({"us-gaap:LeaseContractualTermAxis"})
LEASE_COMMITMENT_LABEL = "lease commitments not yet commenced"

_CONTEXT_RE = re.compile(r"<xbrli:context\b[^>]*\bid=\"([^\"]+)\"[^>]*>(.*?)</xbrli:context>", re.S)
_MEMBER_RE = re.compile(
    r"<xbrldi:explicitMember\b[^>]*\bdimension=\"([^\"]+)\"[^>]*>\s*([^<\s]+)\s*</xbrldi:explicitMember>"
)
# a nil fact is self-closing; a value never spans into the next fact
_FACT_RE = re.compile(
    r"<ix:nonFraction\b([^>]*?)(?:/>|>((?:(?!<ix:nonFraction\b).)*?)</ix:nonFraction>)", re.S
)
_ATTR_RE = re.compile(r"([\w:.-]+)=\"([^\"]*)\"")


def is_lease_axis(axis: str | None) -> bool:
    return bool(axis) and axis in LEASE_AXES


def is_lease_commitment(tag: str, axis: str | None) -> bool:
    """A purchase-obligation concept on a lease axis is a lease commitment."""
    return is_lease_axis(axis) and "PurchaseObligation" in str(tag)


def line_item_label(tag: str, axis: str | None = None) -> str:
    """What a line item is, read from its tag and its dimension axis.

    A purchase-obligation fact on a lease axis is a lease commitment: an
    unrecorded lease is one that has not commenced. Any other fact on a lease
    axis keeps its concept name, marked as summed over lease classes.
    """
    local = str(tag).split(":", 1)[-1]
    if is_lease_commitment(tag, axis):
        return LEASE_COMMITMENT_LABEL
    if is_lease_axis(axis):
        return f"{local} (lease classes)"
    return local


@dataclass(frozen=True)
class Context:
    instant: str | None
    start: str | None
    end: str
    dimensions: tuple[tuple[str, str], ...]


@dataclass(frozen=True)
class Fact:
    concept: str
    value: float
    unit: str
    context_id: str
    context: Context

    @property
    def axes(self) -> tuple[str, ...]:
        return tuple(axis for axis, _ in self.context.dimensions)

    @property
    def lease_axis(self) -> str | None:
        return next((axis for axis in self.axes if is_lease_axis(axis)), None)

    @property
    def label(self) -> str:
        return line_item_label(self.concept, self.lease_axis)


def _tag_text(block: str, tag: str) -> str | None:
    match = re.search(rf"<xbrli:{tag}>\s*([^<\s]+)\s*</xbrli:{tag}>", block)
    return match.group(1) if match else None


def parse_contexts(text: str) -> dict[str, Context]:
    contexts: dict[str, Context] = {}
    for context_id, block in _CONTEXT_RE.findall(text):
        instant = _tag_text(block, "instant")
        start = _tag_text(block, "startDate")
        end = instant or _tag_text(block, "endDate")
        if not end:
            continue
        contexts[context_id] = Context(
            instant=instant,
            start=None if instant else start,
            end=end,
            dimensions=tuple(_MEMBER_RE.findall(block)),
        )
    return contexts


def _number(raw: str, attrs: dict[str, str]) -> float:
    text = html.unescape(re.sub(r"<[^>]+>", "", raw)).strip()
    if attrs.get("format", "").endswith(("fixed-zero", "zerodash")) or text in {"-", "—", "–"}:
        value = 0.0
    else:
        cleaned = text.replace(",", "").replace(" ", "")
        if attrs.get("format", "").endswith("num-comma-decimal"):
            cleaned = text.replace(".", "").replace(" ", "").replace(",", ".")
        value = float(cleaned)
    value *= 10 ** int(attrs.get("scale", "0") or 0)
    if attrs.get("sign") == "-":
        value = -value
    return value


def extract_facts(text: str) -> list[Fact]:
    """Numeric facts in USD, reported in USD millions, with their contexts.

    The same fact can appear more than once in a filing (a table and a
    sentence); repeats of one concept in one context count once.
    """
    contexts = parse_contexts(text)
    facts: list[Fact] = []
    seen: set[tuple[str, str]] = set()
    for raw_attrs, raw_value in _FACT_RE.findall(text):
        attrs = dict(_ATTR_RE.findall(raw_attrs))
        concept = attrs.get("name", "")
        context_id = attrs.get("contextRef", "")
        unit = attrs.get("unitRef", "")
        if not concept or context_id not in contexts or unit.upper().split("_")[-1] != "USD":
            continue
        key = (concept, context_id)
        if key in seen or attrs.get("xsi:nil") == "true":
            continue
        try:
            value = _number(raw_value, attrs)
        except ValueError:
            continue
        seen.add(key)
        facts.append(
            Fact(
                concept=concept,
                value=round(value / 1_000_000, 6),
                unit="USD millions",
                context_id=context_id,
                context=contexts[context_id],
            )
        )
    return facts


def _duration_months(context: Context) -> int | None:
    if context.instant or not context.start:
        return None
    start = dt.date.fromisoformat(context.start)
    end = dt.date.fromisoformat(context.end)
    return round(((end - start).days + 1) / 30.44)


def line_items_for_period(
    facts: list[Fact], period_end: str, duration_months: int = 12, anchor: str = ""
) -> list[dict[str, Any]]:
    """Line-item rows for `epd diff`, one per fact, for one balance date.

    Instant facts must sit at `period_end`; duration facts must end there and
    run `duration_months` (12 for a 10-K year, 3 for a single quarter).
    Lease-axis facts keep their axis and member so `diff` can sum them.
    """
    rows: list[dict[str, Any]] = []
    for fact in facts:
        context = fact.context
        if context.end != period_end:
            continue
        if not context.instant and _duration_months(context) != duration_months:
            continue
        row: dict[str, Any] = {"tag": fact.concept, "value": fact.value, "unit": fact.unit}
        if anchor:
            row["anchor"] = anchor
        if context.dimensions:
            lease_axis = fact.lease_axis
            if lease_axis is None or len(context.dimensions) != 1:
                continue
            row["axis"] = lease_axis
            row["member"] = context.dimensions[0][1]
        rows.append(row)
    return rows
