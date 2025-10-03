"""
Slack Integration for OpsAiX ChatOps
"""
from typing import Optional, Dict, Any
import structlog
from slack_sdk.web.async_client import AsyncWebClient
from slack_sdk.errors import SlackApiError

from src.models.incident import Incident
from src.utils.config import OpsAiXConfig

logger = structlog.get_logger()


class SlackIntegration:
    """Integration with Slack for ChatOps functionality"""
    
    def __init__(self, config: OpsAiXConfig):
        self.config = config
        self.logger = structlog.get_logger().bind(integration="slack")
        self._client = None
        
        # Default channels for different severity levels
        self.severity_channels = {
            "critical": "#critical-incidents",
            "high": "#high-priority-incidents", 
            "medium": "#incidents",
            "low": "#incidents"
        }
    
    @property
    def client(self) -> Optional[AsyncWebClient]:
        """Get Slack client, creating it if needed"""
        if not self.config.chatops.slack.enabled:
            return None
            
        if self._client is None:
            token = self.config.chatops.slack.bot_token
            if token:
                self._client = AsyncWebClient(token=token)
                self.logger.info("Slack client initialized")
            else:
                self.logger.warning("Slack bot token not configured")
        
        return self._client
    
    async def send_incident_notification(self, incident: Incident, channel: Optional[str] = None) -> Optional[str]:
        """
        Send incident notification to Slack
        
        Args:
            incident: The incident to notify about
            channel: Specific channel to send to (optional)
            
        Returns:
            Slack thread timestamp if successful, None otherwise
        """
        if not self.client:
            self.logger.warning("Slack client not available")
            return None
        
        try:
            # Determine channel
            target_channel = channel or self.severity_channels.get(incident.severity.value, "#incidents")
            
            # Create message blocks
            blocks = self._create_incident_message_blocks(incident)
            
            # Send message
            response = await self.client.chat_postMessage(
                channel=target_channel,
                blocks=blocks,
                text=f"🚨 New Incident: {incident.title}"  # Fallback text
            )
            
            if response["ok"]:
                thread_ts = response["ts"]
                self.logger.info("Incident notification sent to Slack",
                               incident_id=incident.id,
                               channel=target_channel,
                               thread_ts=thread_ts)
                return thread_ts
            else:
                self.logger.error("Failed to send Slack notification", 
                                response=response)
                return None
                
        except SlackApiError as e:
            self.logger.error("Slack API error", 
                            incident_id=incident.id,
                            error=str(e))
            return None
    
    async def update_incident_thread(self, incident: Incident, thread_ts: str, update_message: str) -> bool:
        """
        Post an update to an incident thread
        
        Args:
            incident: The incident being updated
            thread_ts: Slack thread timestamp
            update_message: Update message to post
            
        Returns:
            True if successful, False otherwise
        """
        if not self.client:
            return False
        
        try:
            # Determine channel
            channel = self.severity_channels.get(incident.severity.value, "#incidents")
            
            response = await self.client.chat_postMessage(
                channel=channel,
                thread_ts=thread_ts,
                text=f"📝 *Update:* {update_message}\n\n*Status:* {incident.status.value.title()}"
            )
            
            if response["ok"]:
                self.logger.info("Incident thread updated",
                               incident_id=incident.id,
                               thread_ts=thread_ts)
                return True
            return False
            
        except SlackApiError as e:
            self.logger.error("Failed to update Slack thread",
                            incident_id=incident.id,
                            error=str(e))
            return False
    
    async def send_incident_resolution(self, incident: Incident, thread_ts: str) -> bool:
        """
        Send incident resolution notification
        
        Args:
            incident: The resolved incident
            thread_ts: Slack thread timestamp
            
        Returns:
            True if successful, False otherwise
        """
        if not self.client:
            return False
        
        try:
            # Determine channel
            channel = self.severity_channels.get(incident.severity.value, "#incidents")
            
            # Create resolution message
            resolution_text = f"""✅ *Incident Resolved*

*Incident ID:* {incident.id}
*Title:* {incident.title}
*Resolution Time:* {incident.resolved_at}
*Status:* {incident.status.value.title()}
"""
            
            if incident.resolution_summary:
                resolution_text += f"\n*Resolution Summary:* {incident.resolution_summary}"
            
            response = await self.client.chat_postMessage(
                channel=channel,
                thread_ts=thread_ts,
                text=resolution_text
            )
            
            # Also react to original message
            await self.client.reactions_add(
                channel=channel,
                timestamp=thread_ts,
                name="white_check_mark"
            )
            
            return response["ok"]
            
        except SlackApiError as e:
            self.logger.error("Failed to send resolution notification",
                            incident_id=incident.id,
                            error=str(e))
            return False
    
    async def send_custom_message(self, channel: str, message: str, thread_ts: Optional[str] = None) -> bool:
        """
        Send a custom message to Slack
        
        Args:
            channel: Channel to send to
            message: Message content
            thread_ts: Optional thread timestamp for reply
            
        Returns:
            True if successful, False otherwise
        """
        if not self.client:
            return False
        
        try:
            kwargs = {
                "channel": channel,
                "text": message
            }
            
            if thread_ts:
                kwargs["thread_ts"] = thread_ts
            
            response = await self.client.chat_postMessage(**kwargs)
            return response["ok"]
            
        except SlackApiError as e:
            self.logger.error("Failed to send custom Slack message",
                            channel=channel,
                            error=str(e))
            return False
    
    def _create_incident_message_blocks(self, incident: Incident) -> list:
        """Create Slack message blocks for incident notification"""
        
        # Severity emoji mapping
        severity_emojis = {
            "critical": "🔴",
            "high": "🟡", 
            "medium": "🟠",
            "low": "🔵"
        }
        
        emoji = severity_emojis.get(incident.severity.value, "⚪")
        
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"{emoji} New Incident Detected"
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*ID:*\n{incident.id}"
                    },
                    {
                        "type": "mrkdwn", 
                        "text": f"*Severity:*\n{incident.severity.value.title()}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Status:*\n{incident.status.value.title()}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Created:*\n{incident.created_at.strftime('%Y-%m-%d %H:%M UTC')}"
                    }
                ]
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Title:* {incident.title}\n\n*Description:* {incident.description}"
                }
            }
        ]
        
        # Add affected service if available
        if incident.affected_service:
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Affected Service:* {incident.affected_service}"
                }
            })
        
        # Add components if available
        if incident.affected_components:
            components_text = ", ".join(incident.affected_components)
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Affected Components:* {components_text}"
                }
            })
        
        # Add recommended actions if available
        if incident.metadata.get("recommended_actions"):
            actions = incident.metadata["recommended_actions"]
            actions_text = "\n• ".join(actions)
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Recommended Actions:*\n• {actions_text}"
                }
            })
        
        # Add JIRA link if available
        if incident.jira_ticket_id:
            jira_url = f"{self.config.itsm.jira.url}/browse/{incident.jira_ticket_id}"
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*JIRA Ticket:* <{jira_url}|{incident.jira_ticket_id}>"
                }
            })
        
        return blocks
    
    async def test_connection(self) -> bool:
        """Test Slack connection"""
        if not self.client:
            return False
        
        try:
            response = await self.client.auth_test()
            if response["ok"]:
                self.logger.info("Slack connection test successful", 
                               user=response.get("user"),
                               team=response.get("team"))
                return True
            return False
            
        except SlackApiError as e:
            self.logger.error("Slack connection test failed", error=str(e))
            return False