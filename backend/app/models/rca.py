from pydantic import BaseModel, field_validator
from datetime import datetime
from typing import Optional

class RCAModel(BaseModel):
    """RCA schema with validation as required in the guide"""
    incident_start: datetime
    incident_end: datetime
    root_cause_category: str  # INFRA, CODE, CONFIG, NETWORK
    fix_applied: str
    prevention_steps: str
    impact_description: Optional[str] = None
    
    @field_validator("fix_applied")
    @classmethod
    def fix_not_empty(cls, v: str) -> str:
        if len(v.strip()) < 20:
            raise ValueError("Fix description must be at least 20 characters (required for proper root cause analysis)")
        return v
    
    @field_validator("prevention_steps")
    @classmethod
    def prevention_not_empty(cls, v: str) -> str:
        if len(v.strip()) < 20:
            raise ValueError("Prevention steps must be at least 20 characters")
        return v
    
    @field_validator("incident_end")
    @classmethod
    def end_after_start(cls, v: datetime, info) -> datetime:
        if "incident_start" in info.data and v <= info.data["incident_start"]:
            raise ValueError("End time must be after start time")
        return v
    
    @field_validator("root_cause_category")
    @classmethod
    def valid_category(cls, v: str) -> str:
        valid_categories = ["INFRA", "CODE", "CONFIG", "NETWORK"]
        if v not in valid_categories:
            raise ValueError(f"Category must be one of {valid_categories}")
        return v
    
    @property
    def mttr_minutes(self) -> float:
        """Calculate MTTR in minutes as required in guide"""
        return round((self.incident_end - self.incident_start).total_seconds() / 60, 2)
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "incident_start": "2026-05-01T10:00:00",
                "incident_end": "2026-05-01T11:30:00",
                "root_cause_category": "INFRA",
                "fix_applied": "Restarted the database connection pool and increased max_connections from 100 to 500",
                "prevention_steps": "Implement connection pool monitoring, add auto-scaling for connection limits",
                "impact_description": "API was unavailable for 90 minutes"
            }
        }
    }