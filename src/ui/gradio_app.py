"""
Gradio-based dashboard for OpsAiX
"""
import asyncio
import json
import gradio as gr
import structlog
from datetime import datetime
from typing import Dict, Any, Optional

from src.utils.config import load_config
from src.agents.incident_detection_agent import IncidentDetectionAgent
from src.agents.incident_analysis_agent import IncidentAnalysisAgent
from src.integrations.itsm.jira_integration import JiraIntegration
from src.integrations.chatops.slack_integration import SlackIntegration

logger = structlog.get_logger()

# Global config instance
config = load_config()


def create_gradio_app() -> gr.Blocks:
    """Create the main Gradio dashboard application"""
    
    with gr.Blocks(title="OpsAiX Dashboard", theme=gr.themes.Soft()) as app:
        
        # Header
        gr.Markdown("""
        # 🚨 OpsAiX - AI-Powered Incident Response Platform 
        
        **Real-time incident detection, analysis, and automated remediation**
        """)
        
        # Status overview
        with gr.Row():
            with gr.Column():
                gr.Markdown("### 📊 System Status")
                system_status = gr.HTML(value=get_system_status_html())
                
            with gr.Column():
                gr.Markdown("### 🔔 Recent Alerts")
                recent_alerts = gr.HTML(value=get_recent_alerts_html())
        
        # Main tabs
        with gr.Tabs():
            
            # Incident Detection Tab
            with gr.Tab("🔍 Incident Detection"):
                with gr.Row():
                    with gr.Column():
                        gr.Markdown("### Analyze Logs/Metrics")
                        log_input = gr.Textbox(
                            label="Log Data or Metric Query",
                            placeholder="Paste logs or enter metric query...",
                            lines=5
                        )
                        analyze_btn = gr.Button("🔍 Analyze for Incidents", variant="primary")
                        
                    with gr.Column():
                        gr.Markdown("### Analysis Results")
                        analysis_output = gr.HTML(label="Incident Analysis")
                
                analyze_btn.click(
                    fn=analyze_incident,
                    inputs=[log_input],
                    outputs=[analysis_output]
                )
            
            # ChatOps Tab
            with gr.Tab("💬 ChatOps"):
                with gr.Row():
                    with gr.Column():
                        gr.Markdown("### Incident Communication")
                        incident_id = gr.Textbox(label="Incident ID", placeholder="INC-2024-001")
                        message_input = gr.Textbox(
                            label="Message", 
                            placeholder="Update team about incident status...",
                            lines=3
                        )
                        channel_select = gr.Dropdown(
                            choices=["#incidents", "#ops-team", "#critical-alerts"],
                            label="Channel",
                            value="#incidents"
                        )
                        send_btn = gr.Button("📤 Send to Slack/Teams", variant="primary")
                        
                    with gr.Column():
                        gr.Markdown("### Communication History")
                        comm_history = gr.HTML(label="Recent Messages")
                
                send_btn.click(
                    fn=send_chatops_message,
                    inputs=[incident_id, message_input, channel_select],
                    outputs=[comm_history]
                )
            
            # Knowledge Base Tab
            with gr.Tab("📚 Knowledge Base"):
                with gr.Row():
                    with gr.Column():
                        gr.Markdown("### Query Knowledge Base")
                        kb_query = gr.Textbox(
                            label="Search Query",
                            placeholder="How to resolve database connection timeout...",
                            lines=2
                        )
                        search_btn = gr.Button("🔍 Search Runbooks", variant="primary")
                        
                    with gr.Column():
                        gr.Markdown("### Search Results")
                        kb_results = gr.HTML(label="Knowledge Base Results")
                
                search_btn.click(
                    fn=search_knowledge_base,
                    inputs=[kb_query],
                    outputs=[kb_results]
                )
            
            # Configuration Tab
            with gr.Tab("⚙️ Configuration"):
                gr.Markdown("### System Configuration")
                
                with gr.Row():
                    with gr.Column():
                        gr.Markdown("#### Data Sources")
                        elk_status = gr.HTML(value="<span style='color: orange;'>⚠️ ELK Stack: Not Configured</span>")
                        datadog_status = gr.HTML(value="<span style='color: orange;'>⚠️ Datadog: Not Configured</span>")
                        
                    with gr.Column():
                        gr.Markdown("#### Integrations")
                        jira_status = gr.HTML(value="<span style='color: orange;'>⚠️ Jira: Not Configured</span>")
                        slack_status = gr.HTML(value="<span style='color: orange;'>⚠️ Slack: Not Configured</span>")
        
        # Auto-refresh components
        refresh_btn = gr.Button("🔄 Refresh Dashboard", variant="secondary")
        refresh_btn.click(
            fn=refresh_dashboard,
            outputs=[system_status, recent_alerts]
        )
    
    return app


def get_system_status_html() -> str:
    """Get current system status as HTML"""
    return f"""
    <div style="padding: 10px; border-radius: 5px; background-color: #f0f8ff;">
        <p><strong>Status:</strong> <span style="color: green;">🟢 Operational</span></p>
        <p><strong>Uptime:</strong> Starting up...</p>
        <p><strong>Active Incidents:</strong> 0</p>
        <p><strong>Last Update:</strong> {datetime.now().strftime('%H:%M:%S')}</p>
    </div>
    """


def get_recent_alerts_html() -> str:
    """Get recent alerts as HTML"""
    return """
    <div style="padding: 10px; border-radius: 5px; background-color: #fff8f0;">
        <p><em>No recent alerts</em></p>
        <p style="font-size: 12px; color: #666;">
            Alerts will appear here when incidents are detected
        </p>
    </div>
    """


def analyze_incident(log_data: str) -> str:
    """Analyze log data for potential incidents using AI agents"""
    if not log_data.strip():
        return "<p><em>Please provide log data or metric query to analyze</em></p>"
    
    try:
        # Run incident detection asynchronously
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Create detection agent and analyze
        detection_agent = IncidentDetectionAgent(config)
        result = loop.run_until_complete(detection_agent.process(log_data))
        
        loop.close()
        
        # Format results
        detection = result.get("detection_result", {})
        incident_data = result.get("incident")
        
        if detection.get("incident_detected", False):
            # Incident detected
            confidence = detection.get("confidence_score", 0.0)
            severity = detection.get("severity", "unknown")
            
            # Format description with better line breaks and readability
            description = detection.get('description', 'No description available')
            # Clean up the description and add proper formatting
            description = description.strip()
            
            # Break long sentences into readable chunks
            if len(description) > 150:
                # Split by sentences and add line breaks
                sentences = description.split('. ')
                formatted_sentences = []
                for sentence in sentences:
                    sentence = sentence.strip()
                    if sentence and not sentence.endswith('.'):
                        sentence += '.'
                    formatted_sentences.append(sentence)
                
                # Group sentences into paragraphs (every 2-3 sentences)
                paragraphs = []
                current_paragraph = []
                for i, sentence in enumerate(formatted_sentences):
                    current_paragraph.append(sentence)
                    # Create paragraph break every 2 sentences or if sentence is very long
                    if (i + 1) % 2 == 0 or len(sentence) > 120:
                        paragraphs.append(' '.join(current_paragraph))
                        current_paragraph = []
                
                # Add remaining sentences
                if current_paragraph:
                    paragraphs.append(' '.join(current_paragraph))
                
                description = '<br><br>'.join(paragraphs)
            
            # Ensure proper spacing around key terms
            description = description.replace('Redis', '<strong>Redis</strong>')
            description = description.replace('database', '<strong>database</strong>')
            description = description.replace('API', '<strong>API</strong>')
            description = description.replace('memory', '<strong>memory</strong>')
            
            # Format recommended actions with better readability
            actions = detection.get('recommended_actions', ['No actions suggested'])
            actions_html = ""
            for i, action in enumerate(actions, 1):
                # Clean and format action text
                clean_action = action.strip()
                # Break long actions into multiple lines if needed
                if len(clean_action) > 80:
                    words = clean_action.split(' ')
                    lines = []
                    current_line = []
                    current_length = 0
                    
                    for word in words:
                        if current_length + len(word) + 1 > 80 and current_line:
                            lines.append(' '.join(current_line))
                            current_line = [word]
                            current_length = len(word)
                        else:
                            current_line.append(word)
                            current_length += len(word) + 1
                    
                    if current_line:
                        lines.append(' '.join(current_line))
                    
                    formatted_action = '<br>'.join(lines)
                else:
                    formatted_action = clean_action
                
                actions_html += f"""
                <div style='margin: 12px 0; padding: 16px; background: #ffffff; border: 1px solid #e0e0e0; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);'>
                    <div style='display: flex; align-items: flex-start; gap: 12px;'>
                        <div style='background: #2196f3; color: white; width: 28px; height: 28px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 14px; flex-shrink: 0;'>{i}</div>
                        <div style='flex: 1;'>
                            <p style='margin: 0; font-size: 15px; line-height: 1.6; color: #333; word-wrap: break-word;'>{formatted_action}</p>
                        </div>
                    </div>
                </div>
                """
            
            # Format affected components
            components = detection.get('affected_components', [])
            components_html = ""
            if components:
                components_html = f"""
                <p><strong>Affected Components:</strong></p>
                <div style="margin: 10px 0;">
                    {"".join([f"<span style='display: inline-block; margin: 4px; padding: 4px 8px; background: #e3f2fd; border-radius: 12px; font-size: 12px;'>{comp}</span>" for comp in components])}
                </div>
                """
            
            # Try to create JIRA ticket if incident was created
            jira_status = ""
            if incident_data and config.itsm.jira.enabled:
                try:
                    jira_integration = JiraIntegration(config)
                    jira_status = "<p style='color: #2e7d32;'><strong>✅ JIRA Integration:</strong> Ready (ticket creation would happen in full workflow)</p>"
                except Exception:
                    jira_status = "<p style='color: #f57c00;'><strong>⚠️ JIRA Integration:</strong> Not configured</p>"
            
            return f"""
            <div style="padding: 20px; border-radius: 8px; background: linear-gradient(135deg, #fff8dc 0%, #ffeaa7 100%); border-left: 6px solid #ff8c00; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                <h3 style="color: #d32f2f; margin-top: 0;">🚨 Critical Incident Detected!</h3>
                
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin: 15px 0;">
                    <div><strong>Severity:</strong> <span style="color: #d32f2f; font-size: 16px; font-weight: bold;">{severity.upper()}</span></div>
                    <div><strong>Confidence:</strong> <span style="color: #2e7d32; font-size: 16px; font-weight: bold;">{confidence:.1%}</span></div>
                </div>
                
                <div style="margin: 15px 0; padding: 12px; background: white; border-radius: 6px;">
                    <p style="margin: 0;"><strong style="color: #1976d2;">Title:</strong></p>
                    <p style="font-size: 16px; margin: 5px 0 0 0; color: #333;">{detection.get('title', 'Untitled Incident')}</p>
                </div>
                
                <div style="margin: 15px 0; padding: 12px; background: white; border-radius: 6px;">
                    <p style="margin: 0;"><strong style="color: #1976d2;">Description:</strong></p>
                    <p style="font-size: 14px; line-height: 1.6; margin: 8px 0 0 0; color: #444;">{description}</p>
                </div>
                
                {components_html}
                
                <div style="margin: 20px 0;">
                    <div style="margin: 0 0 16px 0; padding: 12px; background: #e3f2fd; border-radius: 8px; border-left: 4px solid #2196f3;">
                        <h4 style="margin: 0; color: #1565c0; font-size: 18px;">🎯 Recommended Actions</h4>
                        <p style="margin: 4px 0 0 0; font-size: 14px; color: #666;">Follow these steps to resolve the incident:</p>
                    </div>
                    {actions_html}
                </div>
                
                {jira_status}
                
                <div style="margin-top: 15px; padding-top: 10px; border-top: 1px solid #ddd; font-size: 12px; color: #666;">
                    <strong>Analysis completed at:</strong> {datetime.now().strftime('%H:%M:%S')} | <strong>Agent:</strong> IncidentDetectionAgent
                </div>
            </div>
            """
        else:
            # No incident detected
            return f"""
            <div style="padding: 20px; border-radius: 8px; background: linear-gradient(135deg, #f8fff8 0%, #c8e6c9 100%); border-left: 6px solid #4caf50; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                <h3 style="color: #2e7d32; margin-top: 0;">📋 Analysis Complete</h3>
                
                <div style="display: flex; align-items: center; margin: 15px 0; padding: 12px; background: white; border-radius: 6px;">
                    <div style="font-size: 24px; margin-right: 12px;">✅</div>
                    <div>
                        <p style="margin: 0; font-size: 16px; font-weight: bold; color: #2e7d32;">No Critical Incidents Detected</p>
                        <p style="margin: 5px 0 0 0; font-size: 14px; color: #666;">Your systems appear to be operating normally</p>
                    </div>
                </div>
                
                <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 15px; margin: 15px 0;">
                    <div style="text-align: center; padding: 10px; background: white; border-radius: 6px;">
                        <div style="font-size: 18px; font-weight: bold; color: #2e7d32;">{detection.get('confidence_score', 0.0):.1%}</div>
                        <div style="font-size: 12px; color: #666;">Confidence</div>
                    </div>
                    <div style="text-align: center; padding: 10px; background: white; border-radius: 6px;">
                        <div style="font-size: 18px; font-weight: bold; color: #1976d2;">{len(log_data):,}</div>
                        <div style="font-size: 12px; color: #666;">Characters Analyzed</div>
                    </div>
                    <div style="text-align: center; padding: 10px; background: white; border-radius: 6px;">
                        <div style="font-size: 18px; font-weight: bold; color: #f57c00;">{datetime.now().strftime('%H:%M:%S')}</div>
                        <div style="font-size: 12px; color: #666;">Analysis Time</div>
                    </div>
                </div>
                
                <div style="margin-top: 15px; padding: 12px; background: rgba(255,255,255,0.7); border-radius: 6px;">
                    <p style="margin: 0; font-size: 14px; color: #555;">
                        <strong>💡 Tip:</strong> The AI analyzed your logs and found no patterns indicating critical incidents. 
                        Continue monitoring for proactive issue detection.
                    </p>
                </div>
            </div>
            """
    
    except Exception as e:
        logger.error("Incident analysis failed", error=str(e))
        return f"""
        <div style="padding: 20px; border-radius: 8px; background: linear-gradient(135deg, #ffe6e6 0%, #ffcdd2 100%); border-left: 6px solid #f44336; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
            <h3 style="color: #c62828; margin-top: 0;">❌ Analysis Error</h3>
            
            <div style="margin: 15px 0; padding: 12px; background: white; border-radius: 6px;">
                <p style="margin: 0 0 8px 0;"><strong style="color: #c62828;">Error Details:</strong></p>
                <p style="font-family: 'Courier New', monospace; font-size: 13px; background: #f5f5f5; padding: 8px; border-radius: 4px; margin: 0; word-wrap: break-word;">{str(e)}</p>
            </div>
            
            <div style="margin: 15px 0; padding: 12px; background: rgba(255,255,255,0.7); border-radius: 6px;">
                <p style="margin: 0; font-size: 14px; color: #555;">
                    <strong>💡 Troubleshooting:</strong><br>
                    • Check your OpenAI API key configuration<br>
                    • Verify network connectivity<br>
                    • Try with smaller log samples<br>
                    • Check the console logs for more details
                </p>
            </div>
            
            <div style="margin-top: 15px; padding-top: 10px; border-top: 1px solid #ddd; font-size: 12px; color: #666;">
                <strong>Error occurred at:</strong> {datetime.now().strftime('%H:%M:%S')}
            </div>
        </div>
        """


def send_chatops_message(incident_id: str, message: str, channel: str) -> str:
    """Send message to ChatOps channel"""
    if not incident_id or not message:
        return "<p><em>Please provide incident ID and message</em></p>"
    
    try:
        # Test Slack integration
        slack_status = "❌ Not configured"
        if config.chatops.slack.enabled and config.chatops.slack.bot_token:
            slack_integration = SlackIntegration(config)
            slack_status = "✅ Ready"
        
        logger.info("ChatOps message prepared", incident_id=incident_id, channel=channel)
        
        return f"""
        <div style="padding: 20px; border-radius: 8px; background: linear-gradient(135deg, #f0f8ff 0%, #e3f2fd 100%); border-left: 6px solid #2196f3; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
            <h3 style="color: #1565c0; margin-top: 0;">📤 ChatOps Message Ready</h3>
            
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin: 15px 0;">
                <div style="padding: 12px; background: white; border-radius: 6px;">
                    <p style="margin: 0 0 4px 0; font-size: 12px; color: #666; text-transform: uppercase;">Incident ID</p>
                    <p style="margin: 0; font-size: 16px; font-weight: bold; color: #1565c0;">{incident_id}</p>
                </div>
                <div style="padding: 12px; background: white; border-radius: 6px;">
                    <p style="margin: 0 0 4px 0; font-size: 12px; color: #666; text-transform: uppercase;">Channel</p>
                    <p style="margin: 0; font-size: 16px; font-weight: bold; color: #1565c0;">{channel}</p>
                </div>
            </div>
            
            <div style="margin: 15px 0; padding: 12px; background: white; border-radius: 6px;">
                <p style="margin: 0 0 8px 0; font-size: 12px; color: #666; text-transform: uppercase;">Message Content</p>
                <div style="background: #f8f9fa; padding: 12px; border-radius: 4px; border-left: 4px solid #2196f3;">
                    <p style="margin: 0; font-size: 14px; line-height: 1.5; color: #333;">"{message}"</p>
                </div>
            </div>
            
            <div style="margin: 15px 0; padding: 12px; background: white; border-radius: 6px;">
                <p style="margin: 0 0 8px 0; font-size: 12px; color: #666; text-transform: uppercase;">Integration Status</p>
                <p style="margin: 0; font-size: 14px;">{slack_status}</p>
            </div>
            
            <div style="margin: 15px 0; padding: 12px; background: rgba(33, 150, 243, 0.1); border-radius: 6px;">
                <p style="margin: 0; font-size: 14px; color: #1565c0;">
                    <strong>📋 Production Behavior:</strong><br>
                    • Message will be sent to the configured Slack channel<br>
                    • Incident thread will be created or updated<br>
                    • Team members will receive real-time notifications<br>
                    • Message history will be tracked for audit purposes
                </p>
            </div>
            
            <div style="margin-top: 15px; padding-top: 10px; border-top: 1px solid #ddd; font-size: 12px; color: #666;">
                <strong>Message prepared at:</strong> {datetime.now().strftime('%H:%M:%S')}
            </div>
        </div>
        """
    
    except Exception as e:
        logger.error("ChatOps message failed", error=str(e))
        return f"""
        <div style="padding: 10px; border-radius: 5px; background-color: #ffe6e6;">
            <h4>❌ ChatOps Error</h4>
            <p><strong>Error:</strong> {str(e)}</p>
        </div>
        """


def search_knowledge_base(query: str) -> str:
    """Search the knowledge base for relevant information"""
    if not query.strip():
        return "<p><em>Please enter a search query</em></p>"
    
    logger.info("Searching knowledge base", query=query)
    
    return f"""
    <div style="padding: 10px; border-radius: 5px; background-color: #fff8f0;">
        <h4>📚 Knowledge Base Results</h4>
        <p><strong>Query:</strong> "{query}"</p>
        <p><strong>Results:</strong> RAG-powered search will be implemented here</p>
        <p><strong>Search time:</strong> {datetime.now().strftime('%H:%M:%S')}</p>
        <div style="margin-top: 10px; padding: 10px; background-color: #f5f5f5; border-radius: 3px;">
            <p><strong>Sample Runbook:</strong> Database Connection Troubleshooting</p>
            <ol>
                <li>Check database server status</li>
                <li>Verify connection credentials</li>
                <li>Test network connectivity</li>
                <li>Review recent configuration changes</li>
            </ol>
        </div>
    </div>
    """


def refresh_dashboard():
    """Refresh dashboard components"""
    return get_system_status_html(), get_recent_alerts_html()


if __name__ == "__main__":
    # For testing the Gradio app independently
    app = create_gradio_app()
    app.launch(server_name="0.0.0.0", server_port=7860)