from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from earnings_pillar_diff.scoring import material_delta, percent_delta
from earnings_pillar_diff.xbrl import is_lease_axis, line_item_label


@dataclass(frozen=True)
class LineItem:
    tag: str
    value: float
    unit: str = "USD millions"
    anchor: str = ""
    # a fact on a dimension axis keeps its axis; lease-axis members of one
    # concept are summed into one line item, so `members` lists what was summed
    axis: str = ""
    members: tuple[str, ...] = ()

    @property
    def key(self) -> tuple[str, str]:
        return (self.tag, self.axis)

    @property
    def label(self) -> str:
        return line_item_label(self.tag, self.axis)

    @classmethod
    def from_mapping(cls, row: dict[str, Any]) -> "LineItem":
        tag = str(row.get("tag", "")).strip()
        if not tag:
            raise ValueError("line item missing tag")
        try:
            value = float(row["value"])
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError(f"{tag} missing numeric value") from exc
        axis = str(row.get("axis") or "").strip()
        member = str(row.get("member") or "").strip()
        if axis and not is_lease_axis(axis):
            raise ValueError(
                f"{tag} on {axis}: only lease-axis members are summed into a line item"
            )
        if axis and not member:
            raise ValueError(f"{tag} on {axis} missing member")
        return cls(
            tag=tag,
            value=value,
            unit=str(row.get("unit", "USD millions")),
            anchor=str(row.get("anchor", "")),
            axis=axis,
            members=(member,) if member else (),
        )


@dataclass(frozen=True)
class DeltaRow:
    tag: str
    prior: float
    current: float
    delta: float
    percent_delta: float | None
    unit: str
    anchor: str
    material: bool
    label: str = ""
    axis: str = ""
    prior_members: tuple[str, ...] = ()
    current_members: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "tag": self.tag,
            "label": self.label or line_item_label(self.tag, self.axis),
            "axis": self.axis,
            "prior_members": list(self.prior_members),
            "current_members": list(self.current_members),
            "prior": self.prior,
            "current": self.current,
            "delta": self.delta,
            "percent_delta": self.percent_delta,
            "unit": self.unit,
            "anchor": self.anchor,
            "material": self.material,
        }


def normalize_line_items(payload: Any) -> dict[tuple[str, str], LineItem]:
    """Line items keyed by (tag, axis).

    Rows for one tag on a lease axis are summed across their members, so a
    period that splits leases by class and one that reports them combined
    both yield the total. A tag listed twice without an axis, or one member
    listed twice, is an input error: keeping either row would drop the other.
    """
    if isinstance(payload, dict) and isinstance(payload.get("line_items"), list):
        rows = payload["line_items"]
    elif isinstance(payload, list):
        rows = payload
    elif isinstance(payload, dict):
        rows = [{"tag": tag, "value": value} for tag, value in payload.items()]
    else:
        raise ValueError("line-item input must be a JSON object or list")

    out: dict[tuple[str, str], LineItem] = {}
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("each line item must be an object")
        item = LineItem.from_mapping(row)
        existing = out.get(item.key)
        if existing is None:
            out[item.key] = item
            continue
        if not item.axis:
            raise ValueError(f"{item.tag} listed twice")
        if set(item.members) & set(existing.members):
            raise ValueError(f"{item.tag} {item.members[0]} listed twice")
        out[item.key] = LineItem(
            tag=item.tag,
            value=existing.value + item.value,
            unit=existing.unit,
            anchor=existing.anchor or item.anchor,
            axis=item.axis,
            members=existing.members + item.members,
        )
    return out


def build_delta_rows(
    prior_items: dict[tuple[str, str], LineItem],
    current_items: dict[tuple[str, str], LineItem],
    fallback_anchor: str = "",
) -> list[DeltaRow]:
    rows: list[DeltaRow] = []
    for key in sorted(set(prior_items) | set(current_items)):
        tag, axis = key
        prior = prior_items.get(key, LineItem(tag=tag, value=0.0, axis=axis))
        current = current_items.get(key, LineItem(tag=tag, value=0.0, unit=prior.unit, axis=axis))
        anchor = current.anchor or prior.anchor or fallback_anchor
        rows.append(
            DeltaRow(
                tag=tag,
                prior=prior.value,
                current=current.value,
                delta=current.value - prior.value,
                percent_delta=percent_delta(prior.value, current.value),
                unit=current.unit or prior.unit,
                anchor=anchor,
                material=material_delta(prior.value, current.value),
                label=line_item_label(tag, axis),
                axis=axis,
                prior_members=prior.members,
                current_members=current.members,
            )
        )
    return rows

