"""
JIRA Integration for OpsAiX
"""
from typing import Optional, Dict, Any, List
import structlog
from jira import JIRA
from jira.exceptions import JIRAError

from src.models.incident import Incident, IncidentSeverity, IncidentStatus
from src.utils.config import OpsAiXConfig

logger = structlog.get_logger()


class JiraIntegration:
    """Integration with JIRA for incident management"""
    
    def __init__(self, config: OpsAiXConfig):
        self.config = config
        self.logger = structlog.get_logger().bind(integration="jira")
        self._client = None
        
        # Severity to priority mapping
        self.severity_priority_map = {
            IncidentSeverity.CRITICAL: "Highest",
            IncidentSeverity.HIGH: "High", 
            IncidentSeverity.MEDIUM: "Medium",
            IncidentSeverity.LOW: "Low"
        }
        
        # Status mapping
        self.status_map = {
            IncidentStatus.NEW: "To Do",
            IncidentStatus.IN_PROGRESS: "In Progress",
            IncidentStatus.INVESTIGATING: "In Progress", 
            IncidentStatus.RESOLVED: "Done",
            IncidentStatus.CLOSED: "Done"
        }
    
    @property
    def client(self) -> Optional[JIRA]:
        """Get JIRA client, creating it if needed"""
        if not self.config.itsm.jira.enabled:
            return None
            
        if self._client is None:
            try:
                self._client = JIRA(
                    server=self.config.itsm.jira.url,
                    basic_auth=(
                        self.config.itsm.jira.username,
                        self.config.itsm.jira.token
                    )
                )
                self.logger.info("JIRA client initialized", server=self.config.itsm.jira.url)
            except JIRAError as e:
                self.logger.error("Failed to initialize JIRA client", error=str(e))
                return None
        
        return self._client
    
    async def create_ticket_from_incident(self, incident: Incident) -> Optional[str]:
        """
        Create a JIRA ticket from an incident
        
        Args:
            incident: The incident to create a ticket for
            
        Returns:
            JIRA ticket key if successful, None otherwise
        """
        if not self.client:
            self.logger.warning("JIRA client not available")
            return None
        
        try:
            # Prepare issue data
            issue_dict = {
                'project': {'key': self.config.itsm.jira.project_key},
                'summary': incident.title,
                'description': self._format_incident_description(incident),
                'issuetype': {'name': 'Bug'},  # Default to Bug, can be configured
                'priority': {'name': self.severity_priority_map.get(incident.severity, "Medium")}
            }
            
            # Add labels if tags exist
            if incident.tags:
                issue_dict['labels'] = [tag.replace(' ', '_') for tag in incident.tags]
            
            # Create the issue
            new_issue = self.client.create_issue(fields=issue_dict)
            
            self.logger.info("JIRA ticket created", 
                           incident_id=incident.id, 
                           jira_key=new_issue.key)
            
            return new_issue.key
            
        except JIRAError as e:
            self.logger.error("Failed to create JIRA ticket", 
                            incident_id=incident.id, 
                            error=str(e))
            return None
    
    async def update_ticket_status(self, ticket_key: str, incident_status: IncidentStatus) -> bool:
        """
        Update JIRA ticket status based on incident status
        
        Args:
            ticket_key: JIRA ticket key
            incident_status: New incident status
            
        Returns:
            True if successful, False otherwise
        """
        if not self.client:
            return False
        
        try:
            issue = self.client.issue(ticket_key)
            
            # Get available transitions
            transitions = self.client.transitions(issue)
            target_status = self.status_map.get(incident_status)
            
            # Find matching transition
            transition_id = None
            for transition in transitions:
                if transition['to']['name'] == target_status:
                    transition_id = transition['id']
                    break
            
            if transition_id:
                self.client.transition_issue(issue, transition_id)
                self.logger.info("JIRA ticket status updated", 
                               ticket_key=ticket_key, 
                               new_status=target_status)
                return True
            else:
                self.logger.warning("No valid transition found", 
                                  ticket_key=ticket_key, 
                                  target_status=target_status)
                return False
                
        except JIRAError as e:
            self.logger.error("Failed to update JIRA ticket status", 
                            ticket_key=ticket_key, 
                            error=str(e))
            return False
    
    async def add_comment_to_ticket(self, ticket_key: str, comment: str) -> bool:
        """
        Add a comment to a JIRA ticket
        
        Args:
            ticket_key: JIRA ticket key
            comment: Comment text
            
        Returns:
            True if successful, False otherwise
        """
        if not self.client:
            return False
        
        try:
            self.client.add_comment(ticket_key, comment)
            self.logger.info("Comment added to JIRA ticket", ticket_key=ticket_key)
            return True
            
        except JIRAError as e:
            self.logger.error("Failed to add comment to JIRA ticket", 
                            ticket_key=ticket_key, 
                            error=str(e))
            return False
    
    async def get_ticket_info(self, ticket_key: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a JIRA ticket
        
        Args:
            ticket_key: JIRA ticket key
            
        Returns:
            Ticket information dict or None if failed
        """
        if not self.client:
            return None
        
        try:
            issue = self.client.issue(ticket_key)
            
            return {
                'key': issue.key,
                'summary': issue.fields.summary,
                'description': issue.fields.description,
                'status': issue.fields.status.name,
                'priority': issue.fields.priority.name if issue.fields.priority else None,
                'assignee': issue.fields.assignee.displayName if issue.fields.assignee else None,
                'created': str(issue.fields.created),
                'updated': str(issue.fields.updated),
                'labels': issue.fields.labels
            }
            
        except JIRAError as e:
            self.logger.error("Failed to get JIRA ticket info", 
                            ticket_key=ticket_key, 
                            error=str(e))
            return None
    
    async def sync_incident_with_jira(self, incident: Incident) -> bool:
        """
        Sync incident with JIRA (create or update)
        
        Args:
            incident: Incident to sync
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # If incident doesn't have JIRA ticket, create one
            if not incident.jira_ticket_id:
                ticket_key = await self.create_ticket_from_incident(incident)
                if ticket_key:
                    incident.set_jira_ticket(ticket_key)
                    return True
                return False
            
            # Update existing ticket status
            return await self.update_ticket_status(incident.jira_ticket_id, incident.status)
            
        except Exception as e:
            self.logger.error("Failed to sync incident with JIRA", 
                            incident_id=incident.id, 
                            error=str(e))
            return False
    
    def _format_incident_description(self, incident: Incident) -> str:
        """Format incident data for JIRA description"""
        
        description_parts = [
            f"*Incident ID:* {incident.id}",
            f"*Severity:* {incident.severity.value.title()}",
            f"*Created:* {incident.created_at}",
            "",
            "*Description:*",
            incident.description,
        ]
        
        if incident.affected_service:
            description_parts.extend([
                "",
                f"*Affected Service:* {incident.affected_service}"
            ])
        
        if incident.affected_components:
            description_parts.extend([
                "",
                "*Affected Components:*",
                "* " + "\n* ".join(incident.affected_components)
            ])
        
        if incident.metadata.get("recommended_actions"):
            description_parts.extend([
                "",
                "*Recommended Actions:*",
                "* " + "\n* ".join(incident.metadata["recommended_actions"])
            ])
        
        description_parts.extend([
            "",
            "---",
            f"_This ticket was created automatically by OpsAiX_"
        ])
        
        return "\n".join(description_parts)
    
    async def test_connection(self) -> bool:
        """Test JIRA connection"""
        try:
            if not self.client:
                return False
            
            # Try to get current user info
            user = self.client.current_user()
            self.logger.info("JIRA connection test successful", user=user)
            return True
            
        except Exception as e:
            self.logger.error("JIRA connection test failed", error=str(e))
            return False