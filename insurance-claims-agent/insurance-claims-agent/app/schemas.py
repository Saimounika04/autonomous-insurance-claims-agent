"""Pydantic models for the Insurance Claims Agent."""
from __future__ import annotations

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class PolicyInfo(BaseModel):
    policy_number: Optional[str] = None
    policyholder_name: Optional[str] = None
    effective_date_from: Optional[str] = None
    effective_date_to: Optional[str] = None


class IncidentInfo(BaseModel):
    date: Optional[str] = None
    time: Optional[str] = None
    location: Optional[str] = None
    description: Optional[str] = None


class Party(BaseModel):
    name: Optional[str] = None
    role: Optional[str] = None  # claimant / third_party / witness
    contact: Optional[str] = None


class AssetDetails(BaseModel):
    asset_type: Optional[str] = None  # vehicle / property / person
    asset_id: Optional[str] = None    # VIN, plate, etc.
    estimated_damage: Optional[float] = None


class ExtractedFields(BaseModel):
    policy: PolicyInfo = Field(default_factory=PolicyInfo)
    incident: IncidentInfo = Field(default_factory=IncidentInfo)
    parties: List[Party] = Field(default_factory=list)
    asset: AssetDetails = Field(default_factory=AssetDetails)
    claim_type: Optional[str] = None
    attachments: List[str] = Field(default_factory=list)
    initial_estimate: Optional[float] = None


class ClaimResponse(BaseModel):
    extractedFields: Dict[str, Any]
    missingFields: List[str]
    recommendedRoute: str
    reasoning: str
