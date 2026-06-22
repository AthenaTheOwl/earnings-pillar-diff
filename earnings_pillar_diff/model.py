from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from earnings_pillar_diff.scoring import material_delta, percent_delta


@dataclass(frozen=True)
class LineItem:
    tag: str
    value: float
    unit: str = "USD millions"
    anchor: str = ""

    @classmethod
    def from_mapping(cls, row: dict[str, Any]) -> "LineItem":
        tag = str(row.get("tag", "")).strip()
        if not tag:
            raise ValueError("line item missing tag")
        try:
            value = float(row["value"])
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError(f"{tag} missing numeric value") from exc
        return cls(
            tag=tag,
            value=value,
            unit=str(row.get("unit", "USD millions")),
            anchor=str(row.get("anchor", "")),
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

    def to_dict(self) -> dict[str, Any]:
        return {
            "tag": self.tag,
            "prior": self.prior,
            "current": self.current,
            "delta": self.delta,
            "percent_delta": self.percent_delta,
            "unit": self.unit,
            "anchor": self.anchor,
            "material": self.material,
        }


def normalize_line_items(payload: Any) -> dict[str, LineItem]:
    if isinstance(payload, dict) and isinstance(payload.get("line_items"), list):
        rows = payload["line_items"]
    elif isinstance(payload, list):
        rows = payload
    elif isinstance(payload, dict):
        rows = [{"tag": tag, "value": value} for tag, value in payload.items()]
    else:
        raise ValueError("line-item input must be a JSON object or list")

    out: dict[str, LineItem] = {}
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("each line item must be an object")
        item = LineItem.from_mapping(row)
        out[item.tag] = item
    return out


def build_delta_rows(
    prior_items: dict[str, LineItem],
    current_items: dict[str, LineItem],
    fallback_anchor: str = "",
) -> list[DeltaRow]:
    rows: list[DeltaRow] = []
    for tag in sorted(set(prior_items) | set(current_items)):
        prior = prior_items.get(tag, LineItem(tag=tag, value=0.0))
        current = current_items.get(tag, LineItem(tag=tag, value=0.0, unit=prior.unit))
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
            )
        )
    return rows

