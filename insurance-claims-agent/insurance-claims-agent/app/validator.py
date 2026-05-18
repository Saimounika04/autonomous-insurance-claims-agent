"""Validate extracted claim fields and report missing mandatory ones."""
from __future__ import annotations

from typing import List

from .schemas import ExtractedFields

# Mandatory fields (dotted paths into the ExtractedFields model)
MANDATORY_FIELDS = [
    "policy.policy_number",
    "policy.policyholder_name",
    "incident.date",
    "incident.location",
    "incident.description",
    "asset.asset_type",
    "asset.estimated_damage",
    "claim_type",
]


def _get(obj, path: str):
    cur = obj
    for part in path.split("."):
        cur = getattr(cur, part, None)
        if cur is None:
            return None
    return cur


def validate(fields: ExtractedFields) -> List[str]:
    """Return a list of missing mandatory field paths."""
    missing: List[str] = []
    for path in MANDATORY_FIELDS:
        value = _get(fields, path)
        if value is None or (isinstance(value, str) and not value.strip()):
            missing.append(path)

    # At least one party (claimant) is required
    if not fields.parties:
        missing.append("parties.claimant")

    return missing
