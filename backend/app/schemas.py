from __future__ import annotations
from enum import Enum
from typing import Any, Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator

class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

class PreliminaryStatus(str, Enum):
    PRELIMINARILY_FEASIBLE="preliminarily_feasible"
    CONDITIONALLY_FEASIBLE="conditionally_feasible"
    INSUFFICIENT_INFORMATION="insufficient_information"
    OUTSIDE_VALIDATED_RANGE="outside_validated_range"

class ReviewAction(str, Enum):
    APPROVE="approve_for_concept_review"
    RETURN="return_for_additional_information"
    REJECT="reject_preliminary_configuration"

class Requirements(StrictModel):
    application_id: str = Field(pattern=r"^APP-\d{3}$")
    heat_load_kw: float | None = Field(default=None, gt=0, le=1000)
    coolant_type: Literal["water","propylene_glycol"] | None = None
    coolant_concentration_pct: float | None = Field(default=None, ge=0, le=100)
    coolant_inlet_temp_c: float | None = Field(default=None, ge=-20, le=100)
    max_outlet_temp_c: float | None = Field(default=None, ge=-20, le=120)
    ambient_temp_c: float | None = Field(default=None, ge=-40, le=100)
    available_flow_lpm: float | None = Field(default=None, gt=0, le=2000)
    max_pressure_drop_kpa: float | None = Field(default=None, gt=0, le=500)
    supply_voltage_v: int | None = Field(default=None, ge=100, le=1000)
    frequency_hz: int | None = Field(default=None, ge=40, le=70)
    max_width_mm: float | None = Field(default=None, gt=0, le=10000)
    max_depth_mm: float | None = Field(default=None, gt=0, le=10000)
    max_height_mm: float | None = Field(default=None, gt=0, le=10000)
    redundancy: Literal["none","n+1_pumps","2n"] | None = None
    communication_protocol: Literal["Modbus TCP","BACnet/IP","EtherNet/IP"] | None = None
    environmental_rating: Literal["IP44","IP54"] | None = None
    customer_notes: str = Field(default="", max_length=2000)

    @field_validator("customer_notes")
    @classmethod
    def clean_notes(cls,value: str)->str:
        return " ".join(value.replace("<"," ").replace(">"," ").split())

class ValidationIssue(StrictModel):
    code: str; field: str; severity: Literal["critical","warning"]; message: str; source_ids: list[str]

class ValidationResult(StrictModel):
    requirements: Requirements; issues: list[ValidationIssue]; missing_critical: list[str]; has_contradiction: bool; outside_validated_range: bool

class SearchRequest(StrictModel):
    query: str = Field(min_length=1,max_length=500)
    query_embedding: list[float] | None = None
    architecture: Literal["single_loop","dual_loop","modular_array","all"] | None = None
    limit: int = Field(default=8,ge=1,le=25)

    @field_validator("query_embedding")
    @classmethod
    def vector_shape(cls,value):
        if value is not None and len(value) != 384: raise ValueError("query_embedding must contain 384 values")
        return value

class ScoreComponent(StrictModel):
    name: str; raw: float; weight: float; contribution: float

class SearchHit(StrictModel):
    source_id: str; title: str; document_type: str; revision: str; status: str; locator: str; product_architecture: str; excerpt: str; score: float; score_breakdown: list[ScoreComponent]; recommendation_eligible: bool; disqualification_reasons: list[str]

class SearchResponse(StrictModel):
    retrieval_mode: str; model_id: str; hits: list[SearchHit]

class RankRequest(StrictModel):
    requirements: Requirements; query_embedding: list[float]; limit: int = Field(default=6,ge=1,le=12)

    @field_validator("query_embedding")
    @classmethod
    def rank_vector_shape(cls,value):
        if len(value) != 384: raise ValueError("query_embedding must contain 384 values")
        return value

class RankedProject(SearchHit):
    differences: dict[str,str|float|int|None]

class RankResponse(StrictModel):
    retrieval_mode: str; projects: list[RankedProject]; recommended_source_id: str | None

class Calculation(StrictModel):
    calculation_id: str; label: str; expression: str; result: float | bool | str | None; unit: str | None = None; passed: bool | None = None; source_ids: list[str]

class Claim(StrictModel):
    claim_id: str; category: Literal["customer_requirement","calculation","historical_evidence","engineering_rule","failure","missing_information","system_inference","human_review"]; text: str; source_ids: list[str]

class AnalysisRequest(StrictModel):
    requirements: Requirements; query_embedding: list[float]

    @field_validator("query_embedding")
    @classmethod
    def analysis_vector_shape(cls,value):
        if len(value) != 384: raise ValueError("query_embedding must contain 384 values")
        return value

class AnalysisResponse(StrictModel):
    application_id: str; status: PreliminaryStatus; proposed_architecture: str | None; closest_valid_project_id: str | None; calculations: list[Calculation]; claims: list[Claim]; missing_requirements: list[str]; contradictions: list[str]; evidence_source_ids: list[str]; calculation_version: str; assessment: str; review_required: str

class SchematicRequest(StrictModel):
    requirements: Requirements; architecture: Literal["single_loop","dual_loop","modular_array"]

class SchematicResponse(StrictModel):
    svg: str; architecture: str; drawing_version: str

class ReviewProposalRequest(StrictModel):
    analysis: AnalysisResponse

class ReviewProposal(StrictModel):
    application_id: str; proposed_architecture: str | None; evidence_source_ids: list[str]; calculation_version: str; approval_permitted: bool; prohibited_reasons: list[str]; allowed_actions: list[ReviewAction]

class ReviewDecisionRequest(StrictModel):
    application_id: str; proposal: ReviewProposal; action: ReviewAction; reviewer_note: str = Field(min_length=3,max_length=1000); idempotency_key: str = Field(min_length=8,max_length=100)

class AuditEvent(StrictModel):
    timestamp: str; application_id: str; proposed_architecture: str | None; evidence_source_ids: list[str]; calculation_version: str; reviewer_action: ReviewAction; reviewer_note: str; before_state: str; after_state: str; idempotency_key: str

class ErrorBody(StrictModel):
    code: str; message: str; details: Any = None; request_id: str

class ErrorResponse(StrictModel):
    error: ErrorBody

class ServiceDiscovery(StrictModel):
    service: str; version: str; health_path: str; documentation_path: str; openapi_path: str
