"""Unit tests for FinOps and operational LLM guardrails."""

import os
import sys
import time
import types
import unittest
from unittest.mock import MagicMock

# 1. Setup mock AWS environment variables for local testing
os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/test")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("AWS_REGION", "ap-southeast-1")
os.environ.setdefault("BEDROCK_GUARDRAIL_ID", "test-guardrail-id")
os.environ.setdefault("S3_BUCKET_NAME", "test-bucket")
os.environ.setdefault("DYNAMODB_TABLE_PREFIX", "test-table")
os.environ.setdefault("COGNITO_USER_POOL_ID", "test-pool")
os.environ.setdefault("COGNITO_CLIENT_ID", "test-client")
os.environ.setdefault("SNS_ALERT_TOPIC_ARN", "arn:aws:sns:test")
os.environ.setdefault("KMS_KEY_ID", "alias/test")

# 2. Mock external AWS SDKs for offline local execution
boto3_mock = types.ModuleType("boto3")
boto3_mock.__path__ = []
boto3_mock.client = MagicMock()
boto3_mock.resource = MagicMock()

dynamodb_mock = types.ModuleType("boto3.dynamodb")
dynamodb_mock.__path__ = []
conditions_mock = types.ModuleType("boto3.dynamodb.conditions")
conditions_mock.Key = MagicMock()

botocore_mock = types.ModuleType("botocore")
botocore_mock.__path__ = []
config_mock = types.ModuleType("botocore.config")
config_mock.Config = MagicMock()
exceptions_mock = types.ModuleType("botocore.exceptions")
exceptions_mock.ClientError = type("ClientError", (Exception,), {})

xray_mock = types.ModuleType("aws_xray_sdk")
xray_mock.__path__ = []
xray_core = types.ModuleType("aws_xray_sdk.core")
xray_core.xray_recorder = MagicMock()
xray_core.patch_all = MagicMock()

redis_mock = types.ModuleType("redis")
redis_mock.__path__ = []
redis_asyncio = types.ModuleType("redis.asyncio")

jose_mock = types.ModuleType("jose")
jose_mock.__path__ = []
jose_mock.jwt = MagicMock()
jose_mock.jwk = MagicMock()
jose_utils = types.ModuleType("jose.utils")
jose_utils.base64url_decode = MagicMock()

sys.modules.update({
    "boto3": boto3_mock,
    "boto3.dynamodb": dynamodb_mock,
    "boto3.dynamodb.conditions": conditions_mock,
    "botocore": botocore_mock,
    "botocore.config": config_mock,
    "botocore.exceptions": exceptions_mock,
    "aws_xray_sdk": xray_mock,
    "aws_xray_sdk.core": xray_core,
    "redis": redis_mock,
    "redis.asyncio": redis_asyncio,
    "jose": jose_mock,
    "jose.utils": jose_utils,
})

from app.aws.llm_guardrails import (
    FinOpsGuardrailManager,
    LLMBudgetExceededError,
    LLMRateLimitExceededError,
    LLMDailyLimitExceededError,
    LLMCircuitBreakerActiveError,
)
from app.config import get_settings


class TestLLMGuardrails(unittest.TestCase):

    def setUp(self):
        self.mgr = FinOpsGuardrailManager()
        self.mgr._init_state()
        self.settings = get_settings()

    def test_input_truncation(self):
        """Test that inputs exceeding max_input_chars are truncated safely."""
        long_input = "A" * (self.settings.llm_max_input_chars + 500)
        truncated = self.mgr.truncate_input(long_input)
        self.assertTrue(truncated.startswith("A" * self.settings.llm_max_input_chars))
        self.assertIn("[Context truncated by Guardrail]", truncated)

    def test_output_token_clamping(self):
        """Test that requested max_tokens does not exceed max_output_tokens ceiling."""
        clamped = self.mgr.clamp_max_tokens(4096)
        self.assertEqual(clamped, self.settings.llm_max_output_tokens)
        
        small_clamped = self.mgr.clamp_max_tokens(256)
        self.assertEqual(small_clamped, 256)

    def test_cache_deduplication(self):
        """Test that identical prompt hashes return cached response."""
        key = self.mgr.compute_cache_key("model-1", "sys", "hello")
        self.assertIsNone(self.mgr.get_cached_response(key))
        
        self.mgr.set_cached_response(key, "cached answer", ttl=60)
        self.assertEqual(self.mgr.get_cached_response(key), "cached answer")

    def test_monthly_budget_cap_enforcement(self):
        """Test that reaching the $100 budget blocks further LLM calls."""
        # Simulate having reached the monthly budget
        self.mgr.monthly_estimated_cost_usd = self.settings.llm_monthly_budget_usd + 0.01
        
        with self.assertRaises(LLMBudgetExceededError):
            self.mgr.check_and_acquire()

    def test_daily_request_limit_enforcement(self):
        """Test that reaching daily request limit blocks further LLM calls."""
        self.mgr.daily_requests = self.settings.llm_daily_request_limit
        
        with self.assertRaises(LLMDailyLimitExceededError):
            self.mgr.check_and_acquire()

    def test_rate_limiting_per_minute(self):
        """Test that exceeding per-minute rate limits raises LLMRateLimitExceededError."""
        now = time.time()
        # Fill the sliding window to the limit
        self.mgr._request_timestamps = [now] * self.settings.llm_rate_limit_per_minute
        
        with self.assertRaises(LLMRateLimitExceededError):
            self.mgr.check_and_acquire()

    def test_circuit_breaker(self):
        """Test that tripping the circuit breaker pauses subsequent calls."""
        self.mgr.trip_circuit_breaker("Simulated ThrottlingException")
        
        with self.assertRaises(LLMCircuitBreakerActiveError):
            self.mgr.check_and_acquire()

    def test_usage_recording(self):
        """Test accurate accumulation of tokens and estimated cost."""
        initial_cost = self.mgr.monthly_estimated_cost_usd
        call_cost = self.mgr.record_usage(input_tokens=1000, output_tokens=1000)
        
        expected_cost = (1000 / 1000.0 * self.settings.llm_cost_per_1k_input_tokens) + \
                        (1000 / 1000.0 * self.settings.llm_cost_per_1k_output_tokens)
        self.assertAlmostEqual(call_cost, expected_cost, places=5)
        self.assertAlmostEqual(self.mgr.monthly_estimated_cost_usd, initial_cost + expected_cost, places=5)
        self.assertEqual(self.mgr.monthly_input_tokens, 1000)
        self.assertEqual(self.mgr.monthly_output_tokens, 1000)

    def test_status_reporting(self):
        """Test get_status payload structure for admin dashboard."""
        status = self.mgr.get_status()
        self.assertIn("monthly_budget_usd", status)
        self.assertIn("monthly_spent_usd", status)
        self.assertIn("circuit_breaker_active", status)
        self.assertEqual(status["monthly_budget_usd"], 100.0)


if __name__ == "__main__":
    unittest.main()
