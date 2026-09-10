"""Application Configuration Module.

Provides centralized typed settings using Pydantic Settings, loading from .env
for AWS deployment.
"""

from functools import lru_cache
from typing import Literal
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration settings with environment variable bindings."""

    # Application Environment
    app_env: Literal["staging", "production"] = Field(
        default="production",
        description="Deployment environment (staging, production)",
    )
    secret_key: str = Field(
        ...,
        description="Secret key used for JWT tokens and cryptographic operations",
    )

    # Database & Cache
    database_url: str = Field(
        ...,
        description="PostgreSQL database connection URL with asyncpg driver",
    )
    redis_url: str = Field(
        ...,
        description="Redis connection URL for caching, session storage, and rate limiting",
    )

    # AWS General Configuration
    aws_region: str = Field(
        ...,
        description="AWS region",
    )
    aws_access_key_id: str = Field(
        default="",
        description="AWS Access Key ID (uses ECS task role when empty)",
    )
    aws_secret_access_key: str = Field(
        default="",
        description="AWS Secret Access Key (uses ECS task role when empty)",
    )

    # Amazon Bedrock (GenAI & Guardrails)
    bedrock_model_id: str = Field(
        default="amazon.nova-lite-v1:0",
        description="Amazon Bedrock Foundation Model ID / Inference Profile",
    )
    bedrock_guardrail_id: str = Field(
        ...,
        description="Amazon Bedrock Guardrail ID",
    )
    bedrock_guardrail_version: str = Field(
        default="DRAFT",
        description="Amazon Bedrock Guardrail Version",
    )

    # FinOps & LLM Cost Guardrails ($100/mo cap)
    llm_monthly_budget_usd: float = Field(
        default=100.0,
        description="Hard monthly budget cap in USD for Bedrock LLM consumption",
    )
    llm_daily_request_limit: int = Field(
        default=2000,
        description="Maximum allowed LLM requests per day across all users",
    )
    llm_rate_limit_per_minute: int = Field(
        default=60,
        description="Maximum allowed LLM requests per minute (burst protection)",
    )
    llm_max_input_chars: int = Field(
        default=8000,
        description="Maximum prompt character length allowed per request (~2,000 tokens)",
    )
    llm_max_output_tokens: int = Field(
        default=1024,
        description="Maximum response tokens allowed per request",
    )
    llm_cost_per_1k_input_tokens: float = Field(
        default=0.0003,
        description="Estimated cost per 1k input tokens in USD (e.g. Nova Lite / Haiku)",
    )
    llm_cost_per_1k_output_tokens: float = Field(
        default=0.00125,
        description="Estimated cost per 1k output tokens in USD",
    )
    llm_circuit_breaker_cooldown_seconds: int = Field(
        default=60,
        description="Seconds to pause LLM invocations after a 429 / QuotaExceeded error",
    )

    # Storage & Persistence
    s3_bucket_name: str = Field(
        ...,
        description="S3 bucket name",
    )
    dynamodb_table_prefix: str = Field(
        ...,
        description="Prefix for DynamoDB tables",
    )

    # Identity & Access Management
    cognito_user_pool_id: str = Field(
        ...,
        description="Amazon Cognito User Pool ID",
    )
    cognito_client_id: str = Field(
        ...,
        description="Amazon Cognito App Client ID",
    )

    # Machine Learning Inference
    sagemaker_endpoint_name: str = Field(
        default="",
        description="Amazon SageMaker endpoint name (optional)",
    )

    # Messaging & Search
    sns_alert_topic_arn: str = Field(
        ...,
        description="Amazon SNS topic ARN",
    )
    opensearch_endpoint: str = Field(
        default="",
        description="Amazon OpenSearch endpoint (optional)",
    )

    # Security & Encryption
    kms_key_id: str = Field(
        ...,
        description="AWS KMS Key ARN/Alias",
    )
    
    # Observability
    cloudwatch_log_group: str = Field(
        default="salescoach-ai",
        description="CloudWatch Log Group Name",
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def is_production(self) -> bool:
        """Check if application is running in production environment."""
        return self.app_env == "production"

    @property
    def is_staging(self) -> bool:
        """Check if application is running in staging environment."""
        return self.app_env == "staging"

    @property
    def cognito_app_client_id(self) -> str:
        """Alias for cognito_client_id."""
        return self.cognito_client_id


@lru_cache()
def get_settings() -> Settings:
    """Return cached application settings singleton instance."""
    return Settings()
