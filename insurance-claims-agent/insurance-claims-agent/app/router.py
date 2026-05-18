"""Routing engine: decide which workflow handles the claim."""
from __future__ import annotations

from typing import List, Tuple

from .schemas import ExtractedFields

FRAUD_KEYWORDS = ("fraud", "inconsistent", "staged")

ROUTES = {
    "FAST_TRACK": "Fast-track",
    "MANUAL_REVIEW": "Manual Review",
    "INVESTIGATION": "Investigation Flag",
    "SPECIALIST": "Specialist Queue",
}


def decide_route(fields: ExtractedFields, missing: List[str]) -> Tuple[str, List[str]]:
    """Return (route, list_of_triggered_rules).

    Priority order (highest wins):
      1. Investigation Flag (fraud keywords)
      2. Specialist Queue (injury claims)
      3. Manual Review (any mandatory field missing)
      4. Fast-track (estimated damage < 25,000)
      5. Manual Review (default fallback)
    """
    triggered: List[str] = []

    description = (fields.incident.description or "").lower()
    fraud_hits = [k for k in FRAUD_KEYWORDS if k in description]
    if fraud_hits:
        triggered.append(f"Fraud keywords detected: {', '.join(fraud_hits)}")
        return ROUTES["INVESTIGATION"], triggered

    if (fields.claim_type or "").lower() == "injury":
        triggered.append("Claim type is 'injury'")
        return ROUTES["SPECIALIST"], triggered

    if missing:
        triggered.append(f"Missing mandatory fields: {', '.join(missing)}")
        return ROUTES["MANUAL_REVIEW"], triggered

    damage = fields.asset.estimated_damage
    if damage is not None and damage < 25000:
        triggered.append(f"Estimated damage ${damage:,.2f} is below $25,000 threshold")
        return ROUTES["FAST_TRACK"], triggered

    triggered.append("No fast-track conditions met; defaulting to manual review")
    return ROUTES["MANUAL_REVIEW"], triggered
