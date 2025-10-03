"""
Incident Analysis Agent - Performs deep analysis of existing incidents
"""
import json
from typing import Any, Dict, List, Optional
from datetime import datetime

from langchain.schema import HumanMessage, SystemMessage
from langchain.prompts import PromptTemplate

from .base_agent import BaseAgent
from src.models.incident import Incident


class IncidentAnalysisAgent(BaseAgent):
    """Agent specialized in analyzing and investigating incidents"""
    
    def __init__(self, config):
        super().__init__(config, "IncidentAnalysisAgent")
        
        self.analysis_prompt = PromptTemplate(
            input_variables=["incident", "additional_data", "context"],
            template="""
Perform a comprehensive analysis of the following incident:

INCIDENT DETAILS:
{incident}

ADDITIONAL DATA:
{additional_data}

CONTEXT:
{context}

Your analysis should include:
1. Root cause analysis
2. Impact assessment
3. Recommended remediation steps
4. Prevention measures
5. Escalation recommendations

Respond in JSON format:
{{
    "root_cause_analysis": {{
        "primary_cause": "Main root cause identified",
        "contributing_factors": ["factor1", "factor2"],
        "confidence_level": float (0.0-1.0),
        "evidence": ["evidence1", "evidence2"]
    }},
    "impact_assessment": {{
        "affected_users": "estimated number or description",
        "business_impact": "high|medium|low",
        "service_degradation": "percentage or description",
        "estimated_downtime": "time estimate"
    }},
    "remediation_plan": {{
        "immediate_actions": ["action1", "action2"],
        "short_term_fixes": ["fix1", "fix2"],
        "long_term_solutions": ["solution1", "solution2"],
        "estimated_resolution_time": "time estimate"
    }},
    "prevention_measures": {{
        "monitoring_improvements": ["improvement1", "improvement2"],
        "process_changes": ["change1", "change2"],
        "infrastructure_updates": ["update1", "update2"]
    }},
    "escalation_recommendation": {{
        "should_escalate": boolean,
        "escalation_reason": "reason if should_escalate is true",
        "stakeholders_to_notify": ["stakeholder1", "stakeholder2"],
        "communication_priority": "urgent|high|normal|low"
    }},
    "next_steps": ["step1", "step2"],
    "confidence_score": float (0.0-1.0)
}}
"""
        )
    
    async def process(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Analyze an incident
        
        Args:
            input_data: Incident object or incident data dict
            context: Additional context like logs, metrics, historical data
            
        Returns:
            Comprehensive incident analysis
        """
        self.log_processing_start(input_data)
        
        try:
            # Normalize incident data
            incident_data = self._normalize_incident_data(input_data)
            
            # Process additional context data
            additional_data = self._process_additional_data(context)
            
            # Create context summary
            context_str = self._create_context_summary(context)
            
            # Generate analysis prompt
            prompt_content = self.analysis_prompt.format(
                incident=incident_data,
                additional_data=additional_data,
                context=context_str
            )
            
            # Analyze with LLM
            messages = [
                SystemMessage(content=self.get_system_prompt() + 
                            "\n\nYou are performing detailed incident analysis. Be thorough and provide actionable insights."),
                HumanMessage(content=prompt_content)
            ]
            
            response = await self._invoke_llm(messages)
            
            # Parse and validate response
            analysis_result = self._parse_analysis_result(response)
            
            result = {
                "analysis": analysis_result,
                "analyzed_at": datetime.utcnow().isoformat(),
                "agent": self.name,
                "incident_id": self._extract_incident_id(input_data)
            }
            
            self.log_processing_complete(result)
            return result
            
        except Exception as e:
            self.logger.error("Incident analysis failed", error=str(e))
            return {
                "error": str(e),
                "analysis": None,
                "analyzed_at": datetime.utcnow().isoformat(),
                "agent": self.name,
                "incident_id": self._extract_incident_id(input_data)
            }
    
    def _normalize_incident_data(self, input_data: Any) -> str:
        """Convert incident data to string format for analysis"""
        
        if isinstance(input_data, Incident):
            return f"""
ID: {input_data.id}
Title: {input_data.title}
Description: {input_data.description}
Severity: {input_data.severity}
Status: {input_data.status}
Created: {input_data.created_at}
Updated: {input_data.updated_at}
Affected Service: {input_data.affected_service or 'Unknown'}
Affected Components: {', '.join(input_data.affected_components) if input_data.affected_components else 'None'}
Assigned To: {input_data.assigned_to or 'Unassigned'}
Tags: {', '.join(input_data.tags) if input_data.tags else 'None'}
JIRA Ticket: {input_data.jira_ticket_id or 'None'}
Metadata: {json.dumps(input_data.metadata, default=str, indent=2)}
"""
        
        elif isinstance(input_data, dict):
            return json.dumps(input_data, default=str, indent=2)
        
        else:
            return str(input_data)
    
    def _process_additional_data(self, context: Optional[Dict[str, Any]]) -> str:
        """Process additional data from context for analysis"""
        if not context:
            return "No additional data provided."
        
        data_sections = []
        
        # Process logs
        if "logs" in context:
            logs = context["logs"]
            if isinstance(logs, list):
                data_sections.append(f"RECENT LOGS ({len(logs)} entries):")
                for i, log in enumerate(logs[:10]):  # Limit to 10 most recent
                    if isinstance(log, dict):
                        data_sections.append(f"  {i+1}. [{log.get('level', 'INFO')}] {log.get('message', str(log))}")
                    else:
                        data_sections.append(f"  {i+1}. {str(log)[:200]}")
        
        # Process metrics
        if "metrics" in context:
            metrics = context["metrics"]
            data_sections.append(f"METRICS: {json.dumps(metrics, default=str)}")
        
        # Process alerts
        if "alerts" in context:
            alerts = context["alerts"]
            if isinstance(alerts, list):
                data_sections.append(f"RELATED ALERTS ({len(alerts)} alerts):")
                for i, alert in enumerate(alerts[:5]):  # Limit to 5 most recent
                    if isinstance(alert, dict):
                        data_sections.append(f"  {i+1}. [{alert.get('severity', 'INFO')}] {alert.get('title', str(alert))}")
                    else:
                        data_sections.append(f"  {i+1}. {str(alert)[:200]}")
        
        # Process service health
        if "service_health" in context:
            health = context["service_health"]
            data_sections.append(f"SERVICE HEALTH: {json.dumps(health, default=str)}")
        
        return "\n\n".join(data_sections) if data_sections else "No additional data provided."
    
    def _extract_incident_id(self, input_data: Any) -> Optional[str]:
        """Extract incident ID from input data"""
        if isinstance(input_data, Incident):
            return input_data.id
        elif isinstance(input_data, dict):
            return input_data.get("id")
        return None
    
    def _parse_analysis_result(self, response: str) -> Dict[str, Any]:
        """Parse and validate the analysis response"""
        try:
            # Clean response
            response = response.strip()
            if response.startswith("```json"):
                response = response[7:]
            if response.endswith("```"):
                response = response[:-3]
            
            result = json.loads(response.strip())
            
            # Validate structure
            expected_sections = [
                "root_cause_analysis", "impact_assessment", "remediation_plan",
                "prevention_measures", "escalation_recommendation"
            ]
            
            for section in expected_sections:
                if section not in result:
                    result[section] = {"status": "analysis_incomplete"}
            
            # Ensure confidence score exists
            if "confidence_score" not in result:
                result["confidence_score"] = 0.5
            
            return result
            
        except (json.JSONDecodeError, ValueError) as e:
            self.logger.warning("Failed to parse analysis result", error=str(e), response=response)
            return {
                "parse_error": str(e),
                "raw_response": response,
                "confidence_score": 0.0,
                "root_cause_analysis": {"status": "parse_failed"},
                "impact_assessment": {"status": "parse_failed"},
                "remediation_plan": {"status": "parse_failed"},
                "prevention_measures": {"status": "parse_failed"},
                "escalation_recommendation": {"status": "parse_failed"}
            }


# Convenience functions
async def analyze_incident(incident: Incident, config, additional_context: Optional[Dict] = None) -> Dict[str, Any]:
    """Convenience function to analyze an incident"""
    agent = IncidentAnalysisAgent(config)
    return await agent.process(incident, additional_context)