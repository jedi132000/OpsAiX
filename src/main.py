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
        gradio_app = gr.mount_gradio_app(app, gradio_app, path="/dashboard")
        
        # Start the server
        uvicorn.run(
            gradio_app,
            host=config.app.host,
            port=config.app.port,
            log_level="info"
        )
        
    except Exception as e:
        logger.error("Failed to start OpsAiX", error=str(e))
        raise

if __name__ == "__main__":
    main()