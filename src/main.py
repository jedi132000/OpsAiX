"""
Main application entry point for OpsAiX
"""
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import gradio as gr
import structlog

from src.utils.config import load_config
from src.ui.gradio_app import create_gradio_app

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

def create_app() -> FastAPI:
    """Create and configure the FastAPI application"""
    
    config = load_config()
    
    app = FastAPI(
        title="OpsAiX API",
        description="AI-Powered Incident Response Platform",
        version="0.1.0",
        debug=config.app.debug
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    @app.get("/health")
    async def health_check():
        """Health check endpoint"""
        return {"status": "healthy", "service": "opsaix"}
    
    @app.get("/")
    async def root():
        """Root endpoint"""
        return {"message": "Welcome to OpsAiX - AI-Powered Incident Response Platform"}
    
    @app.post("/api/analyze-logs")
    async def analyze_logs(request: dict):
        """API endpoint to analyze logs for incidents"""
        try:
            from src.agents.incident_detection_agent import IncidentDetectionAgent
            
            logs = request.get("logs", "")
            if not logs:
                return {"error": "No logs provided"}
            
            detection_agent = IncidentDetectionAgent(config)
            result = await detection_agent.process(logs)
            
            return {
                "success": True,
                "result": result
            }
            
        except Exception as e:
            logger.error("API log analysis failed", error=str(e))
            return {"success": False, "error": str(e)}
    
    @app.get("/api/integrations/status")
    async def integrations_status():
        """Check status of integrations"""
        try:
            from src.integrations.itsm.jira_integration import JiraIntegration
            from src.integrations.chatops.slack_integration import SlackIntegration
            
            status = {
                "jira": {
                    "enabled": config.itsm.jira.enabled,
                    "configured": bool(config.itsm.jira.url and config.itsm.jira.username),
                },
                "slack": {
                    "enabled": config.chatops.slack.enabled,
                    "configured": bool(config.chatops.slack.bot_token),
                }
            }
            
            # Test connections if configured
            if status["jira"]["configured"]:
                jira_integration = JiraIntegration(config)
                status["jira"]["connection_test"] = await jira_integration.test_connection()
            
            if status["slack"]["configured"]:
                slack_integration = SlackIntegration(config)
                status["slack"]["connection_test"] = await slack_integration.test_connection()
            
            return status
            
        except Exception as e:
            logger.error("Integration status check failed", error=str(e))
            return {"error": str(e)}
    
    return app

def main():
    """Main application entry point"""
    try:
        config = load_config()
        logger.info("Starting OpsAiX", version="0.1.0")
        
        # Create FastAPI app
        app = create_app()
        
        # Mount Gradio app
        gradio_app = create_gradio_app()
        app = gr.mount_gradio_app(app, gradio_app, path="/")
        
        # Start the server
        uvicorn.run(
            app,
            host=config.app.host,
            port=config.app.port,
            log_level="info"
        )
        
    except Exception as e:
        logger.error("Failed to start OpsAiX", error=str(e))
        raise

if __name__ == "__main__":
    main()