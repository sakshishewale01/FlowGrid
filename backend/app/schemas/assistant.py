"""
FlowGrid - Grounded Logistics Assistant Schemas
================================================
Pydantic schemas defining structured query requests, retrieved facts,
and transparently labeled assistant responses.
"""

from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class AssistantQueryRequest(BaseModel):
    """
    Incoming question payload sent to the Logistics Assistant.
    """
    query: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="User natural language question about FlowGrid workflows or live shipments",
        examples=["How do I use the Shipment Rescue Center?"],
    )

    model_config = ConfigDict(from_attributes=True)


class AssistantSource(BaseModel):
    """
    Itemized transparency citation backing the assistant's answer.
    Distinguishes real database facts, heuristic rules, ML prototype disclosures,
    and sandbox simulation explanations.
    """
    source_type: str = Field(
        ...,
        description="Classification: RETRIEVED_FACT | OPERATIONAL_RULE | ML_DISCLAIMER | SIMULATOR_SANDBOX | SYSTEM_GUIDANCE",
    )
    title: str = Field(..., description="Human-readable citation label")
    content: str = Field(..., description="Grounded factual details or policy explanation")
    reference_id: Optional[str] = Field(
        default=None,
        description="Database primary key or rule code if applicable",
    )

    model_config = ConfigDict(from_attributes=True)


class AssistantQueryResponse(BaseModel):
    """
    Structured grounded assistant answer returned to the operator.
    """
    query: str = Field(..., description="Echoed input query")
    intent: str = Field(
        ...,
        description="Recognized operational intent category",
    )
    answer: str = Field(..., description="Grounded, explainable response text")
    sources: List[AssistantSource] = Field(
        default_factory=list,
        description="Itemized citations and transparency notices",
    )
    suggested_chips: List[str] = Field(
        default_factory=list,
        description="Follow-up suggested questions grounded in real system capabilities",
    )
    timestamp: str = Field(..., description="ISO 8601 evaluation timestamp")

    model_config = ConfigDict(from_attributes=True)
