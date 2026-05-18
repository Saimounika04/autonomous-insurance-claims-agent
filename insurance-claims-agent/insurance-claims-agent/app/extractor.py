"""Field extraction using regex + (optional) spaCy NER."""
from __future__ import annotations

import logging
import re
from typing import List, Optional

from .schemas import (
    AssetDetails,
    ExtractedFields,
    IncidentInfo,
    Party,
    PolicyInfo,
)

logger = logging.getLogger(__name__)

# Lazy-loaded spaCy model (optional — fine if not installed)
_NLP = None


def _get_nlp():
    global _NLP
    if _NLP is not None:
        return _NLP
    try:
        import spacy

        try:
            _NLP = spacy.load("en_core_web_sm")
        except OSError:
            logger.info("spaCy model en_core_web_sm not installed; using blank pipeline.")
            _NLP = spacy.blank("en")
    except Exception as exc:  # pragma: no cover
        logger.warning("spaCy unavailable: %s", exc)
        _NLP = None
    return _NLP


# ---------- regex helpers ----------
def _search(pattern: str, text: str, group: int = 1, flags=re.IGNORECASE) -> Optional[str]:
    m = re.search(pattern, text, flags)
    return m.group(group).strip() if m else None


def _to_float(s: Optional[str]) -> Optional[float]:
    if not s:
        return None
    try:
        return float(re.sub(r"[^\d.]", "", s))
    except ValueError:
        return None


# ---------- field extractors ----------
def extract_policy(text: str) -> PolicyInfo:
    return PolicyInfo(
        policy_number=_search(r"policy\s*(?:number|no\.?|#)\s*[:\-]?\s*([A-Z0-9\-]{4,})", text),
        policyholder_name=_search(
            r"(?:policy\s*holder|insured(?:\s*name)?)\s*[:\-]?\s*([A-Z][A-Za-z .,'\-]{2,60})",
            text,
        ),
        effective_date_from=_search(
            r"effective\s*(?:date)?\s*(?:from)?\s*[:\-]?\s*([0-9]{1,2}[/\-][0-9]{1,2}[/\-][0-9]{2,4})",
            text,
        ),
        effective_date_to=_search(
            r"(?:to|expir(?:y|ation))\s*[:\-]?\s*([0-9]{1,2}[/\-][0-9]{1,2}[/\-][0-9]{2,4})",
            text,
        ),
    )


def extract_incident(text: str) -> IncidentInfo:
    desc = _search(
        r"(?:loss\s*description|description\s*of\s*(?:loss|accident|incident))\s*[:\-]?\s*(.{20,600}?)(?:\n\s*\n|$)",
        text,
        flags=re.IGNORECASE | re.DOTALL,
    )
    return IncidentInfo(
        date=_search(
            r"(?:date\s*of\s*(?:loss|accident|incident))\s*[:\-]?\s*([0-9]{1,2}[/\-][0-9]{1,2}[/\-][0-9]{2,4})",
            text,
        ),
        time=_search(r"time\s*(?:of\s*loss)?\s*[:\-]?\s*([0-9]{1,2}:[0-9]{2}\s*(?:AM|PM)?)", text),
        location=_search(
            r"(?:location|place|where)\s*(?:of\s*(?:loss|accident))?\s*[:\-]?\s*([A-Za-z0-9 ,.\-/]{5,120})",
            text,
        ),
        description=desc,
    )


def extract_parties(text: str) -> List[Party]:
    parties: List[Party] = []

    claimant = _search(r"claimant\s*(?:name)?\s*[:\-]?\s*([A-Z][A-Za-z .,'\-]{2,60})", text)
    if claimant:
        contact = _search(
            r"claimant.*?(?:phone|tel|contact)\s*[:\-]?\s*([\d\-\(\)\s\+]{7,20})",
            text,
            flags=re.IGNORECASE | re.DOTALL,
        )
        parties.append(Party(name=claimant, role="claimant", contact=contact))

    third = _search(r"third\s*party\s*(?:name)?\s*[:\-]?\s*([A-Z][A-Za-z .,'\-]{2,60})", text)
    if third:
        parties.append(Party(name=third, role="third_party"))

    witness = _search(r"witness\s*(?:name)?\s*[:\-]?\s*([A-Z][A-Za-z .,'\-]{2,60})", text)
    if witness:
        parties.append(Party(name=witness, role="witness"))

    # spaCy NER fallback for PERSON entities if nothing was found
    if not parties:
        nlp = _get_nlp()
        if nlp and nlp.has_pipe("ner"):
            doc = nlp(text[:5000])
            for ent in doc.ents:
                if ent.label_ == "PERSON" and len(parties) < 3:
                    parties.append(Party(name=ent.text, role="claimant" if not parties else "third_party"))
    return parties


def extract_asset(text: str) -> AssetDetails:
    asset_type = None
    if re.search(r"\b(vehicle|auto|car|truck|motorcycle)\b", text, re.IGNORECASE):
        asset_type = "vehicle"
    elif re.search(r"\b(property|home|house|building)\b", text, re.IGNORECASE):
        asset_type = "property"
    elif re.search(r"\b(injury|injured|bodily)\b", text, re.IGNORECASE):
        asset_type = "person"

    asset_id = _search(r"(?:VIN|vehicle\s*id)\s*[:\-]?\s*([A-HJ-NPR-Z0-9]{11,17})", text) or _search(
        r"(?:license\s*plate|plate\s*(?:no|number)?)\s*[:\-]?\s*([A-Z0-9\-]{4,10})", text
    )

    damage = _to_float(
        _search(
            r"(?:estimated\s*damage|damage\s*estimate|loss\s*amount|estimated\s*loss)\s*[:\-]?\s*\$?\s*([\d,]+(?:\.\d+)?)",
            text,
        )
    )

    return AssetDetails(asset_type=asset_type, asset_id=asset_id, estimated_damage=damage)


def extract_claim_type(text: str, asset_type: Optional[str]) -> Optional[str]:
    explicit = _search(r"claim\s*type\s*[:\-]?\s*([A-Za-z ]{3,30})", text)
    if explicit:
        return explicit.strip().lower()
    if re.search(r"\b(injury|injured|bodily\s*injury)\b", text, re.IGNORECASE):
        return "injury"
    if re.search(r"\b(theft|stolen|burglary)\b", text, re.IGNORECASE):
        return "theft"
    if re.search(r"\b(collision|accident|crash)\b", text, re.IGNORECASE):
        return "collision"
    if asset_type == "property":
        return "property"
    return None


def extract_attachments(text: str) -> List[str]:
    section = _search(r"attachments?\s*[:\-]\s*(.{5,300})", text, flags=re.IGNORECASE | re.DOTALL)
    if not section:
        return []
    items = re.split(r"[,\n;]", section)
    return [i.strip(" -•\t") for i in items if i.strip()]


def extract_initial_estimate(text: str) -> Optional[float]:
    return _to_float(
        _search(r"initial\s*estimate\s*[:\-]?\s*\$?\s*([\d,]+(?:\.\d+)?)", text)
    )


def extract_fields(text: str) -> ExtractedFields:
    """Run all extractors and return a structured ExtractedFields object."""
    asset = extract_asset(text)
    return ExtractedFields(
        policy=extract_policy(text),
        incident=extract_incident(text),
        parties=extract_parties(text),
        asset=asset,
        claim_type=extract_claim_type(text, asset.asset_type),
        attachments=extract_attachments(text),
        initial_estimate=extract_initial_estimate(text),
    )
