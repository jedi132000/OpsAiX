"""
Gradio-based dashboard for OpsAiX
"""
import gradio as gr
import structlog
from datetime import datetime

logger = structlog.get_logger()


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
    """Analyze log data for potential incidents"""
    if not log_data.strip():
        return "<p><em>Please provide log data or metric query to analyze</em></p>"
    
    # Placeholder analysis - would integrate with LangChain agents
    logger.info("Analyzing incident data", data_length=len(log_data))
    
    return f"""
    <div style="padding: 10px; border-radius: 5px; background-color: #f8fff8;">
        <h4>📋 Analysis Results</h4>
        <p><strong>Status:</strong> <span style="color: green;">✅ No critical incidents detected</span></p>
        <p><strong>Data processed:</strong> {len(log_data)} characters</p>
        <p><strong>Analysis time:</strong> {datetime.now().strftime('%H:%M:%S')}</p>
        <p><em>Advanced AI analysis with LangChain agents will be implemented here</em></p>
    </div>
    """


def send_chatops_message(incident_id: str, message: str, channel: str) -> str:
    """Send message to ChatOps channel"""
    if not incident_id or not message:
        return "<p><em>Please provide incident ID and message</em></p>"
    
    logger.info("Sending ChatOps message", incident_id=incident_id, channel=channel)
    
    return f"""
    <div style="padding: 10px; border-radius: 5px; background-color: #f0f8ff;">
        <h4>📤 Message Sent</h4>
        <p><strong>Incident:</strong> {incident_id}</p>
        <p><strong>Channel:</strong> {channel}</p>
        <p><strong>Time:</strong> {datetime.now().strftime('%H:%M:%S')}</p>
        <p><strong>Message:</strong> "{message}"</p>
        <p><em>ChatOps integration will be implemented here</em></p>
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