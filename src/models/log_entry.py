"""
Log entry data model
"""
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class LogLevel(str, Enum):
    """Log level enumeration"""
    DEBUG = "debug"
    INFO = "info"
    WARN = "warn"
    ERROR = "error"
    FATAL = "fatal"


class LogEntry(BaseModel):
    """Log entry data model"""
    
    id: str = Field(..., description="Unique log entry identifier")
    timestamp: datetime = Field(..., description="Log timestamp")
    level: LogLevel = Field(..., description="Log level")
    message: str = Field(..., description="Log message")
    
    # Source information
    source: str = Field(..., description="Log source (service, application, etc.)")
    hostname: Optional[str] = None
    service_name: Optional[str] = None
    
    # Structured data
    fields: Dict[str, Any] = Field(default_factory=dict)
    
    # Error details (if applicable)
    exception: Optional[str] = None
    stack_trace: Optional[str] = None
    
    # Processing metadata
    parsed_at: datetime = Field(default_factory=datetime.utcnow)
    processed: bool = Field(default=False)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
    
    def mark_processed(self):
        """Mark log entry as processed"""
        self.processed = True
    
    def is_error_level(self) -> bool:
        """Check if log entry is error level or higher"""
        return self.level in [LogLevel.ERROR, LogLevel.FATAL]
    
    def extract_keywords(self) -> list:
        """Extract potential keywords for analysis"""
        keywords = []
        
        # Common error indicators
        error_keywords = [
            "exception", "error", "failed", "timeout", "connection refused",
            "out of memory", "disk full", "permission denied", "not found",
            "unauthorized", "forbidden", "service unavailable"
        ]
        
        message_lower = str(self.message).lower()
        for keyword in error_keywords:
            if keyword in message_lower:
                keywords.append(keyword)
        
        return keywords