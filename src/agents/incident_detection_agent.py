"""
Incident Detection Agent - Analyzes logs and metrics to detect potential incidents
"""
import json
from typing import Any, Dict, List, Optional
from datetime import datetime

from langchain.schema import HumanMessage, SystemMessage
from langchain.prompts import PromptTemplate

from .base_agent import BaseAgent
from src.models.incident import Incident, IncidentSeverity, IncidentStatus
from src.models.log_entry import LogEntry
from src.models.alert import Alert


class IncidentDetectionAgent(BaseAgent):
    """Agent specialized in detecting incidents from operational data"""
    
    def __init__(self, config):
        super().__init__(config, "IncidentDetectionAgent")
        
        self.detection_prompt = PromptTemplate(
            input_variables=["data", "context"],
            template="""
Analyze the following operational data for potential incidents.

{context}

Data to analyze:
{data}

Your task:
1. Identify if there are any incidents that require immediate attention
2. Classify the severity level (critical, high, medium, low)
3. Determine the affected service/component
4. Suggest initial response actions

Respond in JSON format:
{{
    "incident_detected": boolean,
    "confidence_score": float (0.0-1.0),
    "severity": "critical|high|medium|low",
    "title": "Brief incident title",
    "description": "Detailed description of the issue",
    "affected_service": "Service or component name",
    "affected_components": ["component1", "component2"],
    "recommended_actions": ["action1", "action2"],
    "urgency_reasons": ["reason1", "reason2"],
    "tags": ["tag1", "tag2"]
}}

Focus on:
- Error patterns and anomalies
- Service availability issues  
- Performance degradation
- Security concerns
- Resource exhaustion
"""
        )
    
    async def process(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Analyze input data for incident detection
        
        Args:
            input_data: Can be logs (str/list), alerts (Alert/list), or mixed data
            context: Additional context like service health, recent changes
            
        Returns:
            Incident detection results
        """
        self.log_processing_start(input_data)
        
        try:
            # Normalize input data
            processed_data = self._normalize_input_data(input_data)
            
            # Create context summary
            context_str = self._create_context_summary(context)
            
            # Generate detection prompt
            prompt_content = self.detection_prompt.format(
                data=processed_data,
                context=context_str
            )
            
            # Analyze with LLM
            messages = [
                SystemMessage(content=self.get_system_prompt()),
                HumanMessage(content=prompt_content)
            ]
            
            response = await self._invoke_llm(messages)
            
            # Parse and validate response
            detection_result = self._parse_detection_result(response)
            
            # Create incident if detected
            incident = None
            if detection_result.get("incident_detected", False):
                incident = self._create_incident_from_detection(detection_result)
            
            result = {
                "detection_result": detection_result,
                "incident": incident.model_dump() if incident else None,
                "processed_at": datetime.utcnow().isoformat(),
                "agent": self.name
            }
            
            self.log_processing_complete(result)
            return result
            
        except Exception as e:
            self.logger.error("Incident detection failed", error=str(e))
            return {
                "error": str(e),
                "detection_result": {"incident_detected": False, "confidence_score": 0.0},
                "incident": None,
                "processed_at": datetime.utcnow().isoformat(),
                "agent": self.name
            }
    
    def _normalize_input_data(self, input_data: Any) -> str:
        """Normalize various input data types into a string for analysis"""
        
        if isinstance(input_data, str):
            return input_data
        
        elif isinstance(input_data, LogEntry):
            return f"""LOG ENTRY:
Timestamp: {input_data.timestamp}
Level: {input_data.level}
Source: {input_data.source}
Message: {input_data.message}
Fields: {json.dumps(input_data.fields, default=str)}
Exception: {input_data.exception or 'None'}
"""
        
        elif isinstance(input_data, Alert):
            return f"""ALERT:
Title: {input_data.title}
Severity: {input_data.severity}
Message: {input_data.message}
Source: {input_data.source}
Timestamp: {input_data.timestamp}
Labels: {json.dumps(input_data.labels)}
"""
        
        elif isinstance(input_data, list):
            normalized_items = []
            for item in input_data[:50]:  # Limit to first 50 items
                normalized_items.append(self._normalize_input_data(item))
            return "\n\n---\n\n".join(normalized_items)
        
        elif isinstance(input_data, dict):
            return json.dumps(input_data, default=str, indent=2)
        
        else:
            return str(input_data)
    
    def _parse_detection_result(self, response: str) -> Dict[str, Any]:
        """Parse and validate the LLM response"""
        try:
            # Try to extract JSON from response
            response = response.strip()
            if response.startswith("```json"):
                response = response[7:]
            if response.endswith("```"):
                response = response[:-3]
            
            result = json.loads(response.strip())
            
            # Validate required fields
            required_fields = ["incident_detected", "confidence_score"]
            for field in required_fields:
                if field not in result:
                    result[field] = False if field == "incident_detected" else 0.0
            
            # Ensure confidence score is in valid range
            result["confidence_score"] = max(0.0, min(1.0, float(result.get("confidence_score", 0.0))))
            
            return result
            
        except (json.JSONDecodeError, ValueError) as e:
            self.logger.warning("Failed to parse detection result", error=str(e), response=response)
            return {
                "incident_detected": False,
                "confidence_score": 0.0,
                "parse_error": str(e),
                "raw_response": response
            }
    
    def _create_incident_from_detection(self, detection_result: Dict[str, Any]) -> Incident:
        """Create an Incident object from detection results"""
        
        # Generate incident ID
        incident_id = f"INC-{datetime.utcnow().strftime('%Y%m%d')}-{datetime.utcnow().microsecond:06d}"
        
        # Map severity
        severity_map = {
            "critical": IncidentSeverity.CRITICAL,
            "high": IncidentSeverity.HIGH,
            "medium": IncidentSeverity.MEDIUM,
            "low": IncidentSeverity.LOW
        }
        severity = severity_map.get(detection_result.get("severity", "medium"), IncidentSeverity.MEDIUM)
        
        # Create incident
        incident = Incident(
            id=incident_id,
            title=detection_result.get("title", "Detected Incident"),
            description=detection_result.get("description", "Incident detected by AI analysis"),
            severity=severity,
            status=IncidentStatus.NEW,
            affected_service=detection_result.get("affected_service"),
            affected_components=detection_result.get("affected_components", []),
            tags=detection_result.get("tags", []),
            metadata={
                "detection_confidence": detection_result.get("confidence_score", 0.0),
                "recommended_actions": detection_result.get("recommended_actions", []),
                "urgency_reasons": detection_result.get("urgency_reasons", []),
                "detected_by": self.name
            }
        )
        
        return incident


# Convenience functions for common use cases
async def detect_incident_from_logs(logs: List[LogEntry], config, context: Optional[Dict] = None) -> Dict[str, Any]:
    """Convenience function to detect incidents from log entries"""
    agent = IncidentDetectionAgent(config)
    return await agent.process(logs, context)

async def detect_incident_from_text(log_text: str, config, context: Optional[Dict] = None) -> Dict[str, Any]:
    """Convenience function to detect incidents from raw log text"""
    agent = IncidentDetectionAgent(config)
    return await agent.process(log_text, context)