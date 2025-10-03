"""
Configuration management for OpsAiX
"""
from typing import List
import yaml
from pathlib import Path
from pydantic import BaseModel
from pydantic_settings import BaseSettings


class AppConfig(BaseModel):
    name: str = "OpsAiX"
    version: str = "0.1.0"
    debug: bool = True
    host: str = "0.0.0.0"
    port: int = 8080


class LangChainConfig(BaseModel):
    model_provider: str = "openai"
    model_name: str = "gpt-4"
    temperature: float = 0.1
    max_tokens: int = 2048


class VectorDbConfig(BaseModel):
    provider: str = "chroma"
    collection_name: str = "opsaix_knowledge"
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    persist_directory: str = "./chroma_db"


class DataSourceConfig(BaseModel):
    enabled: bool = False


class ElasticsearchConfig(DataSourceConfig):
    hosts: List[str] = []
    username: str = ""
    password: str = ""


class DatadogConfig(DataSourceConfig):
    api_key: str = ""
    app_key: str = ""
    site: str = "datadoghq.com"


class PrometheusConfig(DataSourceConfig):
    url: str = ""
    username: str = ""
    password: str = ""


class DataSourcesConfig(BaseModel):
    elasticsearch: ElasticsearchConfig = ElasticsearchConfig()
    datadog: DatadogConfig = DatadogConfig()
    prometheus: PrometheusConfig = PrometheusConfig()


class JiraConfig(DataSourceConfig):
    url: str = ""
    username: str = ""
    token: str = ""
    project_key: str = ""


class ServiceNowConfig(DataSourceConfig):
    instance_url: str = ""
    username: str = ""
    password: str = ""
    table: str = "incident"


class ITSMConfig(BaseModel):
    jira: JiraConfig = JiraConfig()
    servicenow: ServiceNowConfig = ServiceNowConfig()


class SlackConfig(DataSourceConfig):
    bot_token: str = ""
    app_token: str = ""
    signing_secret: str = ""


class TeamsConfig(DataSourceConfig):
    bot_id: str = ""
    bot_password: str = ""


class ChatOpsConfig(BaseModel):
    slack: SlackConfig = SlackConfig()
    teams: TeamsConfig = TeamsConfig()


class SecurityConfig(BaseModel):
    secret_key: str = "change-me-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30


class AuthConfig(BaseModel):
    provider: str = "local"
    require_auth: bool = False


class LoggingConfig(BaseModel):
    level: str = "INFO"
    format: str = "json"
    file: str = "logs/opsaix.log"


class OpsAiXConfig(BaseSettings):
    app: AppConfig = AppConfig()
    langchain: LangChainConfig = LangChainConfig()
    vector_db: VectorDbConfig = VectorDbConfig()
    data_sources: DataSourcesConfig = DataSourcesConfig()
    itsm: ITSMConfig = ITSMConfig()
    chatops: ChatOpsConfig = ChatOpsConfig()
    security: SecurityConfig = SecurityConfig()
    auth: AuthConfig = AuthConfig()
    logging: LoggingConfig = LoggingConfig()

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"  # Allow extra fields from environment


def load_config(config_path: str = "config.yaml") -> OpsAiXConfig:
    """Load configuration from YAML file and environment variables"""
    
    config_file = Path(config_path)
    config_data = {}
    
    if config_file.exists():
        with open(config_file, 'r', encoding='utf-8') as f:
            config_data = yaml.safe_load(f) or {}
    
    # Create config object which will also load from environment variables
    return OpsAiXConfig(**config_data)