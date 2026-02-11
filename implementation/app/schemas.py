from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional
from uuid import UUID

from pydantic import BaseModel, Field


AxisName = Literal['money', 'time', 'energy', 'asset', 'reliability', 'identity']
ConfidenceLevel = Literal['high', 'medium', 'low']
ValidityLevel = Literal['long', 'medium', 'short']
ObjectType = Literal['shell', 'success_path']


class ImpactVector(BaseModel):
    delta_money: float = 0.0
    delta_time: float = 0.0
    delta_energy: float = 0.0
    delta_asset: float = 0.0
    delta_reliability: float = 0.0
    delta_identity: float = 0.0


class AxisConfidence(BaseModel):
    money: float = 0.0
    time: float = 0.0
    energy: float = 0.0
    asset: float = 0.0
    reliability: float = 0.0
    identity: float = 0.0


class EvidenceSpan(BaseModel):
    text: str
    start: int
    end: int
    signal_type: str


class EventImpactResult(BaseModel):
    schema_version: str = 'event_impact_v2.1'
    event_summary: str
    event_class: str
    impact_vector: ImpactVector
    axis_confidence: AxisConfidence
    missing_axes: List[AxisName] = Field(default_factory=list)
    irreversible: bool = False
    system_caused: bool = False
    analysis_confidence: float = 0.0
    baseline_used: Dict[str, Any] = Field(default_factory=dict)
    evidence_spans: List[EvidenceSpan] = Field(default_factory=list)
    reasoning: Dict[str, Any] = Field(default_factory=dict)


class UserState(BaseModel):
    user_id: str
    money_value: float = 0.5
    money_confidence: float = 0.3
    time_value: float = 0.5
    time_confidence: float = 0.3
    energy_value: float = 0.5
    energy_confidence: float = 0.3
    asset_value: float = 0.5
    asset_confidence: float = 0.3
    reliability_value: float = 0.8
    reliability_confidence: float = 0.5
    identity_value: float = 0.5
    identity_confidence: float = 0.3
    main_constraint: Optional[AxisName] = None
    uncertainty_meta: float = 0.0


class CandidateAction(BaseModel):
    name: str
    description: str
    payload: Dict[str, Any] = Field(default_factory=dict)


class DecisionScore(BaseModel):
    score: float
    predicted_gain: float
    predicted_risk: float
    memory_penalty: float
    uncertainty_penalty: float


class ConstraintIntakeResult(BaseModel):
    required_slots: List[str] = Field(default_factory=list)
    missing_slots: List[str] = Field(default_factory=list)
    questions: List[str] = Field(default_factory=list)


class ChatRequest(BaseModel):
    user_id: str
    message: str
    session_id: Optional[UUID] = None
    idempotency_key: str


class ChatResponse(BaseModel):
    session_id: UUID
    response: str
    asked_questions: List[str] = Field(default_factory=list)
    decision: Optional[DecisionScore] = None
    user_state: Optional[UserState] = None
    trace: Dict[str, Any] = Field(default_factory=dict)


class ShellWriteRequest(BaseModel):
    social_interface: Dict[str, Any] = Field(default_factory=dict)
    narratives: Dict[str, Any] = Field(default_factory=dict)
    confidence: ConfidenceLevel = 'high'
    validity: ValidityLevel = 'long'
    source: Literal['user', 'inferred'] = 'user'


class SuccessPathWriteRequest(BaseModel):
    name: str
    intent: str
    required_slots: List[str] = Field(default_factory=list)
    slot_definitions: Dict[str, str] = Field(default_factory=dict)
    procedure: str
    success_criteria: str
    confidence: ConfidenceLevel = 'high'
    validity: ValidityLevel = 'long'
    tags: List[str] = Field(default_factory=list)


class MemoryObjectRecord(BaseModel):
    object_id: UUID
    object_type: ObjectType
    name: Optional[str] = None
    payload_json: Dict[str, Any]
    confidence: ConfidenceLevel
    validity: ValidityLevel
    updated_at: str


class OutcomeUpdateRequest(BaseModel):
    actual_impact_vector: Dict[str, float]
    actual_cost: float
    continuity_failure: bool = False
    failure_type: Optional[str] = None
    user_visible_cost: Optional[str] = None
    preventable: Optional[bool] = None


class OutcomeRecord(BaseModel):
    outcome_id: UUID
    decision_id: int
    user_id: str
    predicted_impact_vector: Dict[str, Any]
    actual_impact_vector: Optional[Dict[str, Any]] = None
    predicted_cost: Optional[float] = None
    actual_cost: Optional[float] = None
    cost_error: Optional[float] = None
    continuity_failure: bool = False
    failure_type: Optional[str] = None
    created_at: str


class HighRiskConfirmRequest(BaseModel):
    user_id: str
    confirm_token: str


class HighRiskConfirmResponse(BaseModel):
    ok: bool
    decision_id: int
    user_id: str
    confirmed: bool
    message: str
