"""
Pydantic schemas for the Legal Strategy Council application.
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from datetime import datetime
import uuid


def generate_uuid() -> str:
    return str(uuid.uuid4())


# Request/Response Models
class CaseCreate(BaseModel):
    title: str
    facts: str
    jurisdiction: str
    stakes: str


class CaseResponse(BaseModel):
    case_id: str
    title: str
    facts: str
    jurisdiction: str
    stakes: str
    created_at: datetime


# Database Models
class Case(BaseModel):
    case_id: str = Field(default_factory=generate_uuid)
    title: str
    facts: str
    jurisdiction: str
    stakes: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict:
        return {
            "case_id": self.case_id,
            "title": self.title,
            "facts": self.facts,
            "jurisdiction": self.jurisdiction,
            "stakes": self.stakes,
            "created_at": self.created_at
        }


class Argument(BaseModel):
    argument_id: str = Field(default_factory=generate_uuid)
    case_id: str
    agent: str
    type: Literal["primary", "precedent"]
    content: str
    reasoning: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict:
        return {
            "argument_id": self.argument_id,
            "case_id": self.case_id,
            "agent": self.agent,
            "type": self.type,
            "content": self.content,
            "reasoning": self.reasoning,
            "created_at": self.created_at
        }


class Counterargument(BaseModel):
    counterargument_id: str = Field(default_factory=generate_uuid)
    case_id: str
    agent: str
    target_argument_id: str
    content: str
    attack_vectors: List[str]
    created_at: datetime = Field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict:
        return {
            "counterargument_id": self.counterargument_id,
            "case_id": self.case_id,
            "agent": self.agent,
            "target_argument_id": self.target_argument_id,
            "content": self.content,
            "attack_vectors": self.attack_vectors,
            "created_at": self.created_at
        }


class Conflict(BaseModel):
    conflict_id: str = Field(default_factory=generate_uuid)
    case_id: str
    agents_involved: List[str]
    issue: str
    description: str
    status: Literal["unresolved", "resolved"] = "unresolved"
    created_at: datetime = Field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict:
        return {
            "conflict_id": self.conflict_id,
            "case_id": self.case_id,
            "agents_involved": self.agents_involved,
            "issue": self.issue,
            "description": self.description,
            "status": self.status,
            "created_at": self.created_at
        }


class Strategy(BaseModel):
    strategy_id: str = Field(default_factory=generate_uuid)
    case_id: str
    version: int = 1
    final_strategy: str
    rationale: str
    rejected_alternatives: List[str]
    created_at: datetime = Field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict:
        return {
            "strategy_id": self.strategy_id,
            "case_id": self.case_id,
            "version": self.version,
            "final_strategy": self.final_strategy,
            "rationale": self.rationale,
            "rejected_alternatives": self.rejected_alternatives,
            "created_at": self.created_at
        }


# SSE Event Models
class SSEEvent(BaseModel):
    event: str
    data: dict


class AgentStartedEvent(BaseModel):
    agent: str
    case_id: str


class AgentCompletedEvent(BaseModel):
    agent: str
    case_id: str
    content: str


class ConflictDetectedEvent(BaseModel):
    case_id: str
    conflicts: List[dict]


class StrategyReadyEvent(BaseModel):
    case_id: str
    strategy: dict
