from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime


class Episode(BaseModel):
    episode_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    user_id: str
    prompt: str
    thoughts: List[str] = []
    actions: List[Dict[str, Any]] = []
    results: List[str] = []
    reward: Optional[float] = None


class SemanticFact(BaseModel):
    fact_id: str
    content: str
    source: str
    confidence: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class Skill(BaseModel):
    skill_id: str
    name: str
    parameters: Dict[str, Any] = {}
    preconditions: List[str] = []
    postconditions: List[str] = []
    usage_count: int = 0
    last_used: Optional[datetime] = None
