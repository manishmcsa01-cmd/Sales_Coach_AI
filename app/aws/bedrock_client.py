import json
import logging
import boto3
from typing import Dict, Any, Generator
from botocore.config import Config
from botocore.exceptions import ClientError
from app.config import get_settings
from app.aws.llm_guardrails import (
    guardrails,
    LLMGuardrailError,
    LLMBudgetExceededError,
    LLMRateLimitExceededError,
    LLMDailyLimitExceededError,
    LLMCircuitBreakerActiveError,
)
from app.aws.cloudwatch_client import cloudwatch_client

settings = get_settings()
logger = logging.getLogger(__name__)


class BedrockClient:
    """Bedrock runtime client protected with FinOps cost caps ($100/mo), rate limits, and fallback guardrails."""

    FALLBACK_MODELS = [
        "anthropic.claude-3-5-sonnet-20240620-v1:0",
        "apac.anthropic.claude-3-5-sonnet-20240620-v1:0",
        "anthropic.claude-3-sonnet-20240229-v1:0",
        "apac.anthropic.claude-3-sonnet-20240229-v1:0",
        "apac.anthropic.claude-3-haiku-20240307-v1:0",
        "amazon.nova-lite-v1:0",
        "amazon.nova-micro-v1:0",
        "amazon.nova-pro-v1:0",
        "apac.amazon.nova-lite-v1:0",
        "apac.amazon.nova-micro-v1:0",
        "apac.amazon.nova-pro-v1:0",
    ]

    def __init__(self):
        self._client = None
        self._guardrail_client = None

    def _get_boto_config(self) -> Config:
        """Enforce standard retries (max 2 attempts) to prevent costly infinite retry storms."""
        return Config(
            retries={
                'max_attempts': 2,
                'mode': 'standard'
            },
            connect_timeout=5,
            read_timeout=30
        )

    @property
    def client(self):
        if self._client is None:
            kwargs = {
                "region_name": settings.aws_region or "ap-southeast-1",
                "config": self._get_boto_config()
            }
            if getattr(settings, "aws_access_key_id", None) and getattr(settings, "aws_secret_access_key", None):
                kwargs["aws_access_key_id"] = settings.aws_access_key_id
                kwargs["aws_secret_access_key"] = settings.aws_secret_access_key
            self._client = boto3.client('bedrock-runtime', **kwargs)
        return self._client

    @property
    def guardrail_client(self):
        if self._guardrail_client is None:
            kwargs = {
                "region_name": settings.aws_region or "ap-southeast-1",
                "config": self._get_boto_config()
            }
            if getattr(settings, "aws_access_key_id", None) and getattr(settings, "aws_secret_access_key", None):
                kwargs["aws_access_key_id"] = settings.aws_access_key_id
                kwargs["aws_secret_access_key"] = settings.aws_secret_access_key
            self._guardrail_client = boto3.client('bedrock-runtime', **kwargs)
        return self._guardrail_client

    def invoke_model(self, model_id: str, system_prompt: str, user_message: str, max_tokens: int = 1024) -> str:
        """Invoke Bedrock LLM with FinOps cost guardrails, input truncation, token ceiling, and caching."""
        
        # 1. Input Guardrail: Truncate input to avoid runaway prompt cost
        user_message = guardrails.truncate_input(user_message or "")
        system_prompt = guardrails.truncate_input(system_prompt or "") if system_prompt else ""
        
        # 2. Output Guardrail: Clamp output max tokens to ceiling
        max_tokens = guardrails.clamp_max_tokens(max_tokens)

        # 3. Cache / Deduplication Guardrail: Check if identical query has already been generated
        cache_key = guardrails.compute_cache_key(model_id, system_prompt, user_message)
        cached_res = guardrails.get_cached_response(cache_key)
        if cached_res:
            logger.info(f"Guardrail: Cache hit for hash {cache_key[:8]}... (Zero AWS cost incurred)")
            return cached_res

        # 4. FinOps Guardrail: Acquire rate limit and verify $100 monthly budget
        # Will raise LLMBudgetExceededError, LLMRateLimitExceededError, or LLMCircuitBreakerActiveError
        guardrails.check_and_acquire()

        models_to_try = [model_id]
        for fb in self.FALLBACK_MODELS:
            if fb not in models_to_try:
                models_to_try.append(fb)

        attempted_errors = []
        for candidate_model in models_to_try:
            # 1. Bedrock Converse API
            try:
                converse_response = self.client.converse(
                    modelId=candidate_model,
                    messages=[
                        {
                            "role": "user",
                            "content": [{"text": user_message}]
                        }
                    ],
                    system=[{"text": system_prompt}] if system_prompt else [],
                    inferenceConfig={
                        "maxTokens": max_tokens,
                        "temperature": 0.3,
                        "topP": 0.9
                    }
                )
                output_msg = converse_response.get("output", {}).get("message", {})
                content_blocks = output_msg.get("content", [])
                text_pieces = [c.get("text", "") for c in content_blocks if "text" in c]
                result_text = "".join(text_pieces).strip()
                
                if result_text:
                    # Extract usage tokens for cost tracking
                    usage = converse_response.get("usage", {})
                    input_tokens = usage.get("inputTokens", max(len(user_message) // 4, 1))
                    output_tokens = usage.get("outputTokens", max(len(result_text) // 4, 1))

                    # Track cost and store cache
                    call_cost = guardrails.record_usage(input_tokens, output_tokens)
                    guardrails.set_cached_response(cache_key, result_text)
                    self._emit_metrics(input_tokens, output_tokens, call_cost)

                    logger.info(f"Bedrock Converse API succeeded with model: {candidate_model}")
                    return result_text

            except ClientError as ce:
                err_code = ce.response.get("Error", {}).get("Code", "")
                attempted_errors.append(f"{candidate_model} (Converse ClientError): {err_code}")
                # Circuit breaker trip on upstream rate limiting or quota exhaustion
                if err_code in ["ThrottlingException", "ServiceQuotaExceededException", "ModelNotReadyException", "TooManyRequestsException"]:
                    guardrails.trip_circuit_breaker(f"{err_code} from Bedrock on {candidate_model}")
                    raise LLMCircuitBreakerActiveError(f"Bedrock throttled request ({err_code}). Tripped circuit breaker.") from ce
            except Exception as conv_err:
                attempted_errors.append(f"{candidate_model} (Converse): {conv_err}")
                logger.debug(f"Converse API call for {candidate_model} failed ({conv_err}), attempting invoke_model...")

            # 2. Fallback to InvokeModel with Anthropic Messages API
            try:
                payload = {
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": max_tokens,
                    "system": system_prompt,
                    "messages": [{"role": "user", "content": user_message}]
                }
                body_bytes = json.dumps(payload).encode('utf-8')
                response = self.client.invoke_model(
                    modelId=candidate_model,
                    body=body_bytes,
                    contentType="application/json",
                    accept="application/json"
                )
                response_body = json.loads(response['body'].read().decode('utf-8'))
                text = response_body.get('content', [{}])[0].get('text', '')
                
                if text:
                    # Approximate token usage
                    input_tokens = max(len(user_message) // 4, 1)
                    output_tokens = max(len(text) // 4, 1)
                    call_cost = guardrails.record_usage(input_tokens, output_tokens)
                    guardrails.set_cached_response(cache_key, text)
                    self._emit_metrics(input_tokens, output_tokens, call_cost)

                    logger.info(f"Bedrock invoke_model succeeded with model: {candidate_model}")
                    return text

            except ClientError as ce:
                err_code = ce.response.get("Error", {}).get("Code", "")
                attempted_errors.append(f"{candidate_model} (InvokeModel ClientError): {err_code}")
                if err_code in ["ThrottlingException", "ServiceQuotaExceededException", "ModelNotReadyException"]:
                    guardrails.trip_circuit_breaker(f"{err_code} on {candidate_model}")
                    raise LLMCircuitBreakerActiveError(f"Bedrock throttled request ({err_code}). Tripped circuit breaker.") from ce
            except Exception as e:
                attempted_errors.append(f"{candidate_model} (InvokeModel): {e}")
                logger.warning(f"Bedrock model {candidate_model} failed: {e}. Trying next candidate...")

        summary_msg = " | ".join(attempted_errors[:3])
        raise RuntimeError(f"All Bedrock candidates failed: {summary_msg}")

    def _emit_metrics(self, input_tokens: int, output_tokens: int, cost_usd: float) -> None:
        """Emit CloudWatch metrics for FinOps observability."""
        try:
            cloudwatch_client.put_metric("SalesCoachAI/Bedrock", "LLMInvocations", 1.0, "Count")
            cloudwatch_client.put_metric("SalesCoachAI/Bedrock", "InputTokens", float(input_tokens), "Count")
            cloudwatch_client.put_metric("SalesCoachAI/Bedrock", "OutputTokens", float(output_tokens), "Count")
            cloudwatch_client.put_metric("SalesCoachAI/Bedrock", "EstimatedCostUSD", cost_usd, "None")
        except Exception as e:
            logger.debug(f"Failed to publish CloudWatch metric: {e}")

    def invoke_model_stream(self, model_id: str, system_prompt: str, user_message: str, max_tokens: int = 1024) -> Generator[str, None, None]:
        guardrails.check_and_acquire()
        max_tokens = guardrails.clamp_max_tokens(max_tokens)
        user_message = guardrails.truncate_input(user_message)
        
        payload = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_tokens,
            "system": system_prompt,
            "messages": [{"role": "user", "content": user_message}]
        }
        response = self.client.invoke_model_with_response_stream(
            modelId=model_id,
            body=json.dumps(payload)
        )
        for event in response.get('body'):
            chunk = event.get('chunk')
            if chunk:
                chunk_obj = json.loads(chunk.get('bytes').decode('utf-8'))
                if chunk_obj['type'] == 'content_block_delta':
                    yield chunk_obj['delta'].get('text', '')

    def apply_guardrail(self, guardrail_id: str, text: str, source: str = 'OUTPUT') -> Dict[str, Any]:
        response = self.guardrail_client.apply_guardrail(
            guardrailIdentifier=guardrail_id,
            guardrailVersion=settings.bedrock_guardrail_version or 'DRAFT',
            source=source,
            content=[{'text': {'text': text}}]
        )
        return {
            "action": response.get("action", "NONE"),
            "filtered_text": response.get("outputs", [{}])[0].get("text", text)
        }


bedrock_client = BedrockClient()
