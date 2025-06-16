#!/usr/bin/env python3
"""
GigNova: Base data models
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum
from dataclasses import dataclass
from pydantic import BaseModel, Field


class JobStatus(Enum):
    POSTED = "posted"
    MATCHED = "matched"
    NEGOTIATING = "negotiating"
    ACTIVE = "active"
    IN_QA = "in_qa"
    COMPLETED = "completed"
    DISPUTED = "disputed"
    CANCELLED = "cancelled"


class AgentType(Enum):
    MATCHING = "matching"
    NEGOTIATION = "negotiation"
    QA = "qa"
    PAYMENT = "payment"


@dataclass
class AgentConfig:
    confidence_threshold: float = 0.85
    negotiation_rounds: int = 5
    qa_similarity_threshold: float = 0.7
    learning_rate: float = 0.01
    memory_window: int = 100


class JobPost(BaseModel):
    title: str
    description: str
    skills: List[str]
    budget_min: float
    budget_max: float
    deadline: datetime
    client_id: str
    requirements: List[str] = []


class FreelancerProfile(BaseModel):
    user_id: str
    skills: List[str]
    hourly_rate: float
    portfolio: List[str] = []
    rating: float = 0.0
    completed_jobs: int = 0


class JobMatch(BaseModel):
    job_id: str
    freelancer_id: str
    confidence_score: float
    match_reasons: List[str]
    
    
class NegotiationRound(BaseModel):
    job_id: str
    client_offer: float
    freelancer_ask: float
    round_number: int
    timestamp: datetime


class QAResult(BaseModel):
    job_id: str
    deliverable_hash: str
    similarity_score: float
    passed: bool
    feedback: str
