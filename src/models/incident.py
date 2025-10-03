"""
Incident data model
"""
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class IncidentSeverity(str, Enum):
    """Incident severity levels"""
    CRITICAL = "critical"
    HIGH = "high" 
    MEDIUM = "medium"
    LOW = "low"


class IncidentStatus(str, Enum):
    """Incident status states"""
    NEW = "new"
    IN_PROGRESS = "in_progress"
    INVESTIGATING = "investigating"
    RESOLVED = "resolved"
    CLOSED = "closed"


class Incident(BaseModel):
    """Incident data model"""
    
    id: str = Field(..., description="Unique incident identifier")
    title: str = Field(..., description="Brief incident title")
    description: str = Field(..., description="Detailed incident description")
    severity: IncidentSeverity = Field(..., description="Incident severity level")
    status: IncidentStatus = Field(default=IncidentStatus.NEW, description="Current status")
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    resolved_at: Optional[datetime] = None
    
    # Assignment and ownership
    assigned_to: Optional[str] = None
    reporter: Optional[str] = None
    
    # Service/system affected
    affected_service: Optional[str] = None
    affected_components: List[str] = Field(default_factory=list)
    
    # Integration data
    jira_ticket_id: Optional[str] = None
    slack_thread_id: Optional[str] = None
    
    # Analysis data
    root_cause: Optional[str] = None
    resolution_summary: Optional[str] = None
    
    # Metadata
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

    def update_status(self, status: IncidentStatus, resolved_at: Optional[datetime] = None):
        """Update incident status with timestamp"""
        self.status = status
        self.updated_at = datetime.utcnow()
        if status == IncidentStatus.RESOLVED and resolved_at:
            self.resolved_at = resolved_at
    
    def add_tag(self, tag: str):
        """Add a tag to the incident"""
        if tag not in self.tags:
            self.tags.append(tag)
            self.updated_at = datetime.utcnow()
    
    def set_jira_ticket(self, ticket_id: str):
        """Associate JIRA ticket with incident"""
        self.jira_ticket_id = ticket_id
        self.updated_at = datetime.utcnow()
    
    def set_slack_thread(self, thread_id: str):
        """Associate Slack thread with incident"""
        self.slack_thread_id = thread_id
        self.updated_at = datetime.utcnow()