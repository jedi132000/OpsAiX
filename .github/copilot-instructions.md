# AI Agent Instructions for OpsAiX

## Project Overview
OpsAiX is an AI-powered incident response and remediation platform that combines agentic GenAI workflows with enterprise integrations. The platform uses LangChain, LangGraph, RAG, and MCP (Model Context Protocol) for intelligent operations management.

## Core Architecture Principles

### Agentic Workflow Design
- Build modular agents using **LangChain/LangGraph** for specialized tasks:
  - Telemetry analysis agents
  - Incident detection and classification agents  
  - ChatOps communication agents
  - ITSM workflow agents
  - Dashboard and alerting agents
- Each agent should be independently testable and deployable
- Use LangGraph for complex multi-step workflows with decision points

### Data Integration Patterns
- Implement **data adapters** for ingesting from:
  - ELK Stack (Elasticsearch, Logstash, Kibana)
  - Datadog metrics and logs
  - Prometheus/Grafana monitoring
  - Custom log sources via standardized interfaces
- Design adapters as pluggable modules in `src/adapters/`
- Use consistent data models for cross-platform correlation

### RAG Knowledge Base Implementation
- Store runbooks, compliance docs, and troubleshooting guides in vector DB
- Implement context-aware retrieval for incident-specific knowledge
- Design for real-time knowledge updates and version control
- Focus on actionable, procedural knowledge over generic documentation

## Integration Requirements

### ITSM Systems
- **Jira Integration**: Automated ticket creation, status sync, field mapping
- **ServiceNow Integration**: Incident lifecycle management, change requests
- Implement standardized ITSM interfaces in `src/integrations/itsm/`
- Handle authentication, rate limiting, and error recovery

### ChatOps Implementation  
- **Slack/Teams Bots**: Real-time incident notifications and response commands
- Design conversational interfaces for incident triage and escalation
- Implement bot permissions and security controls
- Store bot configurations in `config/chatops/`

### Security & Compliance
- Implement **RBAC** (Role-Based Access Control) throughout the platform
- Support OAuth/SAML/LDAP authentication methods
- Enable comprehensive audit logging for compliance requirements
- Design for GDPR and enterprise security standards

## Development Workflow

### Configuration Management
- Use `config.yaml` as the primary configuration file
- Environment-specific overrides in `config/environments/`
- Sensitive credentials via environment variables only
- Validate configuration on startup with clear error messages

### Container & Deployment
- Docker Compose for local development (`docker-compose.yml`)
- Separate services for different components (UI, API, agents, databases)
- Health checks and graceful shutdown handling
- Production-ready Kubernetes manifests in `k8s/`

### UI Framework
- Use **Gradio or Streamlit** for rapid dashboard development
- Focus on real-time updates for incident status and metrics
- Implement responsive design for mobile incident response
- Default UI accessible at `http://localhost:8080`

## Code Organization Patterns

```
src/
├── agents/           # LangChain/LangGraph agent implementations
├── adapters/         # Data source integrations  
├── integrations/     # ITSM, ChatOps, and third-party APIs
├── rag/             # Knowledge base and retrieval logic
├── ui/              # Dashboard and interface components
├── models/          # Data models and schemas
└── utils/           # Shared utilities and helpers
```

## Key Implementation Notes

- **Multi-cloud Ready**: Design for deployment across cloud, hybrid, and bare-metal
- **Plugin Architecture**: Make all integrations extensible and configurable
- **Real-time Processing**: Use event-driven patterns for incident detection and response
- **Observability**: Instrument all components with metrics, logs, and traces
- **Fail-safe Design**: Graceful degradation when external services are unavailable

## Testing Strategy
- Unit tests for individual agents and adapters
- Integration tests for ITSM and ChatOps workflows  
- End-to-end tests for complete incident response scenarios
- Load testing for high-volume telemetry ingestion

When implementing features, prioritize modularity, observability, and enterprise-grade reliability. The platform should handle mission-critical incidents with confidence and transparency.