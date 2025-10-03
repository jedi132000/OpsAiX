#!/usr/bin/env python3
"""
Test script for OpsAiX agents and integrations
"""
import asyncio
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.utils.config import load_config
from src.agents.incident_detection_agent import IncidentDetectionAgent
from src.agents.incident_analysis_agent import IncidentAnalysisAgent
from src.models.incident import Incident, IncidentSeverity, IncidentStatus
from src.models.log_entry import LogEntry, LogLevel
from datetime import datetime
import json


async def test_incident_detection():
    """Test incident detection agent"""
    print("🔍 Testing Incident Detection Agent...")
    
    config = load_config()
    agent = IncidentDetectionAgent(config)
    
    # Test with sample error logs
    test_logs = """
    2024-10-02 14:30:15 [ERROR] Database connection failed: Connection timeout after 30 seconds
    2024-10-02 14:30:16 [ERROR] Unable to connect to redis://localhost:6379 - connection refused
    2024-10-02 14:30:17 [WARN] High memory usage detected: 95% of available memory in use
    2024-10-02 14:30:18 [ERROR] API endpoint /users returned 500 Internal Server Error
    2024-10-02 14:30:19 [ERROR] Transaction rollback executed due to database constraint violation
    """
    
    try:
        result = await agent.process(test_logs, {"service": "web-api", "environment": "production"})
        
        print("✅ Detection completed!")
        print(f"📊 Results: {json.dumps(result, indent=2, default=str)}")
        
        return result.get("incident")
        
    except Exception as e:
        print(f"❌ Detection failed: {e}")
        return None


async def test_incident_analysis():
    """Test incident analysis agent"""
    print("\n🔬 Testing Incident Analysis Agent...")
    
    config = load_config()
    agent = IncidentAnalysisAgent(config)
    
    # Create a test incident
    test_incident = Incident(
        id="INC-20241002-001",
        title="Database Connection Failures",
        description="Multiple database connection timeouts detected in production environment",
        severity=IncidentSeverity.HIGH,
        status=IncidentStatus.INVESTIGATING,
        affected_service="web-api",
        affected_components=["database", "redis", "api-gateway"],
        tags=["database", "timeout", "production"]
    )
    
    # Additional context
    context = {
        "logs": [
            "Connection timeout to primary database",
            "Redis connection refused",
            "High memory usage detected"
        ],
        "metrics": {
            "database_connections": 0,
            "redis_connections": 0,
            "memory_usage": 95
        },
        "service_health": {
            "database": "down",
            "redis": "down",
            "web-api": "degraded"
        }
    }
    
    try:
        result = await agent.process(test_incident, context)
        
        print("✅ Analysis completed!")
        print(f"📊 Results: {json.dumps(result, indent=2, default=str)}")
        
        return result
        
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        return None


async def test_integrations():
    """Test JIRA and Slack integrations"""
    print("\n🔗 Testing Integrations...")
    
    config = load_config()
    
    # Test JIRA
    try:
        from src.integrations.itsm.jira_integration import JiraIntegration
        jira = JiraIntegration(config)
        
        if config.itsm.jira.enabled:
            jira_test = await jira.test_connection()
            print(f"📋 JIRA Integration: {'✅ Connected' if jira_test else '❌ Failed'}")
        else:
            print("📋 JIRA Integration: ⚠️ Not enabled")
    except Exception as e:
        print(f"📋 JIRA Integration: ❌ Error - {e}")
    
    # Test Slack
    try:
        from src.integrations.chatops.slack_integration import SlackIntegration
        slack = SlackIntegration(config)
        
        if config.chatops.slack.enabled:
            slack_test = await slack.test_connection()
            print(f"💬 Slack Integration: {'✅ Connected' if slack_test else '❌ Failed'}")
        else:
            print("💬 Slack Integration: ⚠️ Not enabled")
    except Exception as e:
        print(f"💬 Slack Integration: ❌ Error - {e}")


async def main():
    """Run all tests"""
    print("🚨 OpsAiX Component Tests 🚀\n")
    
    # Test incident detection
    incident = await test_incident_detection()
    
    # Test incident analysis
    await test_incident_analysis()
    
    # Test integrations
    await test_integrations()
    
    print("\n✨ All tests completed!")
    
    if incident:
        print(f"\n🎯 Sample incident created: {incident}")


if __name__ == "__main__":
    # Set up environment
    os.environ.setdefault('PYTHONPATH', os.path.dirname(os.path.dirname(__file__)))
    
    # Run tests
    asyncio.run(main())