"""
Alert data model
"""
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class AlertSeverity(str, Enum):
    """Alert severity levels"""
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"


class Alert(BaseModel):
    """Alert data model"""
    
    id: str = Field(..., description="Unique alert identifier")
    title: str = Field(..., description="Alert title")
    message: str = Field(..., description="Alert message content")
    severity: AlertSeverity = Field(..., description="Alert severity")
    
    # Source information
    source: str = Field(..., description="Source system (e.g., 'prometheus', 'datadog')")
    source_id: Optional[str] = Field(None, description="Source-specific identifier")
    
    # Timestamps
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    resolved_at: Optional[datetime] = None
    
    # Classification
    category: Optional[str] = None  # e.g., 'infrastructure', 'application', 'security'
    component: Optional[str] = None  # e.g., 'database', 'web-server', 'load-balancer'
    
    # Status
    is_resolved: bool = Field(default=False)
    is_acknowledged: bool = Field(default=False)
    
    # Metadata
    labels: Dict[str, str] = Field(default_factory=dict)
    annotations: Dict[str, str] = Field(default_factory=dict)
    
    # Related incident
    incident_id: Optional[str] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
    
    def acknowledge(self):
        """Mark alert as acknowledged"""
        self.is_acknowledged = True
    
    def resolve(self, resolved_at: Optional[datetime] = None):
        """Mark alert as resolved"""
        self.is_resolved = True
        self.resolved_at = resolved_at or datetime.utcnow()
    
    def associate_incident(self, incident_id: str):
        """Associate alert with an incident"""
        self.incident_id = incident_id