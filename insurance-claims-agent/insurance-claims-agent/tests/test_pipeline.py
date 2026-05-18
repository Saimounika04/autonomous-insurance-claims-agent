"""Unit tests for extractor → validator → router pipeline."""
from pathlib import Path

from app.extractor import extract_fields
from app.router import decide_route
from app.validator import validate

SAMPLES = Path(__file__).resolve().parent.parent / "sample_documents"


def _load(name: str) -> str:
    return (SAMPLES / name).read_text(encoding="utf-8")


def test_fast_track_collision():
    text = _load("sample_claim.txt")
    fields = extract_fields(text)
    missing = validate(fields)
    route, _ = decide_route(fields, missing)

    assert fields.policy.policy_number == "AUTO-998877-21"
    assert fields.asset.estimated_damage == 4500.0
    assert route == "Fast-track"


def test_injury_routes_to_specialist():
    text = _load("sample_injury_claim.txt")
    fields = extract_fields(text)
    missing = validate(fields)
    route, _ = decide_route(fields, missing)
    # "inconsistent" appears in description → Investigation Flag wins (priority 1)
    assert route == "Investigation Flag"


def test_missing_fields_route_to_manual_review():
    text = "Some unrelated text with no claim details."
    fields = extract_fields(text)
    missing = validate(fields)
    route, _ = decide_route(fields, missing)
    assert missing  # should be many
    assert route == "Manual Review"
