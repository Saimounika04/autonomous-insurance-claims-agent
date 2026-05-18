"""Generate a human-readable explanation for the routing decision."""
from __future__ import annotations

from typing import List

from .schemas import ExtractedFields


def build_reasoning(
    fields: ExtractedFields,
    missing: List[str],
    route: str,
    triggers: List[str],
) -> str:
    parts: List[str] = []
    parts.append(f"Recommended route: {route}.")
    if triggers:
        parts.append("Decision drivers: " + "; ".join(triggers) + ".")

    damage = fields.asset.estimated_damage
    if damage is not None:
        parts.append(f"Reported estimated damage is ${damage:,.2f}.")

    if fields.claim_type:
        parts.append(f"Claim type identified as '{fields.claim_type}'.")

    if missing:
        parts.append(
            f"{len(missing)} mandatory field(s) missing: {', '.join(missing)}. "
            "These should be collected before the claim can advance."
        )
    else:
        parts.append("All mandatory fields are present.")

    return " ".join(parts)
