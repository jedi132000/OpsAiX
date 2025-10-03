"""
Base agent class for OpsAiX LangChain agents
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, List
import structlog
from langchain.schema import BaseMessage
from langchain_openai import ChatOpenAI
from langchain.schema.runnable import RunnableConfig

from src.utils.config import OpsAiXConfig

logger = structlog.get_logger()


class BaseAgent(ABC):
    """Base class for all OpsAiX agents"""
    
    def __init__(self, config: OpsAiXConfig, name: str):
        self.config = config
        self.name = name
        self.logger = structlog.get_logger().bind(agent=name)
        
        # Initialize LLM
        import os
        
        llm_kwargs = {
            "model": config.langchain.model_name,
            "temperature": config.langchain.temperature,
            "max_tokens": config.langchain.max_tokens,
        }
        
        # Get API key from config or environment
        api_key = config.langchain.openai_api_key or os.getenv("OPENAI_API_KEY")
        if api_key:
            llm_kwargs["api_key"] = api_key
            
        self.llm = ChatOpenAI(**llm_kwargs)
    
    @abstractmethod
    async def process(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Main processing method for the agent
        
        Args:
            input_data: The input data to process
            context: Optional context information
            
        Returns:
            Processing result as dictionary
        """
        pass
    
    def get_system_prompt(self) -> str:
        """Get the system prompt for this agent"""
        return f"""You are {self.name}, an AI agent specialized in incident response and operations management.

You are part of OpsAiX, an enterprise-grade incident response platform. Your role is to:
1. Analyze operational data (logs, metrics, alerts)
2. Detect and classify incidents
3. Provide actionable recommendations
4. Communicate findings clearly and concisely

Always be precise, factual, and focus on actionable insights."""
    
    async def _invoke_llm(self, messages: List[BaseMessage], **kwargs) -> str:
        """Helper method to invoke the LLM with error handling"""
        try:
            response = await self.llm.ainvoke(messages, **kwargs)
            return response.content
        except Exception as e:
            self.logger.error("LLM invocation failed", error=str(e))
            raise
    
    def _create_context_summary(self, context: Optional[Dict[str, Any]]) -> str:
        """Create a summary of context for the agent"""
        if not context:
            return "No additional context provided."
        
        summary_parts = []
        for key, value in context.items():
            if isinstance(value, (str, int, float, bool)):
                summary_parts.append(f"- {key}: {value}")
            elif isinstance(value, (list, dict)):
                summary_parts.append(f"- {key}: {type(value).__name__} with {len(value)} items")
            else:
                summary_parts.append(f"- {key}: {type(value).__name__}")
        
        return "Context:\n" + "\n".join(summary_parts)
    
    def log_processing_start(self, input_data: Any):
        """Log the start of processing"""
        self.logger.info("Starting agent processing", 
                        input_type=type(input_data).__name__)
    
    def log_processing_complete(self, result: Dict[str, Any]):
        """Log the completion of processing"""
        self.logger.info("Agent processing complete", 
                        result_keys=list(result.keys()))