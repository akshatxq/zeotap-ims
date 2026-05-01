from pydantic import BaseModel, Field, validator
from datetime import datetime
from typing import Optional
import time

class Signal(BaseModel):
    """Incoming signal schema matching the assignment requirements"""
    component_id: str = Field(..., description="Component that generated the signal")
    error_type: str = Field(..., description="Type of error (CONNECTION_REFUSED, TIMEOUT, etc)")
    severity: str = Field(..., description="P0, P1, or P2")
    timestamp: Optional[float] = Field(default_factory=time.time, description="Unix timestamp")
    message: Optional[str] = Field(None, description="Optional error message")
    
    @validator('severity')
    def validate_severity(cls, v):
        if v not in ['P0', 'P1', 'P2']:
            raise ValueError(f'Severity must be P0, P1, or P2, got {v}')
        return v
    
    @validator('component_id')
    def component_not_empty(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Component ID cannot be empty')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "component_id": "RDBMS_PRIMARY",
                "error_type": "CONNECTION_REFUSED",
                "severity": "P0",
                "message": "Database connection pool exhausted"
            }
        }