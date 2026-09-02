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
        ...,
        description="AWS Access Key ID",
    )
    aws_secret_access_key: str = Field(
        ...,
        description="AWS Secret Access Key",
    )

    # Amazon Bedrock (GenAI & Guardrails)
    bedrock_model_id: str = Field(
        ...,
        description="Amazon Bedrock Foundation Model ID",
    )
    bedrock_guardrail_id: str = Field(
        ...,
        description="Amazon Bedrock Guardrail ID",
    )
    bedrock_guardrail_version: str = Field(
        default="DRAFT",
        description="Amazon Bedrock Guardrail Version",
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
        ...,
        description="Amazon SageMaker endpoint name",
    )

    # Messaging & Search
    sns_alert_topic_arn: str = Field(
        ...,
        description="Amazon SNS topic ARN",
    )
    opensearch_endpoint: str = Field(
        ...,
        description="Amazon OpenSearch endpoint",
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


@lru_cache()
def get_settings() -> Settings:
    """Return cached application settings singleton instance."""
    return Settings()
