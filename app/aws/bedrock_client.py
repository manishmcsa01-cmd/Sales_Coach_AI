import json
import boto3
from typing import Dict, Any, Generator
from app.config import get_settings

settings = get_settings()

import logging

logger = logging.getLogger(__name__)

class BedrockClient:
    # Supported Claude models in order of priority (including Sonnet 3.5 v1, v2, and cross-region APAC)
    FALLBACK_MODELS = [
        "anthropic.claude-3-5-sonnet-20240620-v1:0",
        "anthropic.claude-3-5-sonnet-20241022-v2:0",
        "apac.anthropic.claude-3-5-sonnet-20240620-v1:0",
        "apac.anthropic.claude-3-5-sonnet-20241022-v2:0",
        "anthropic.claude-3-sonnet-20240229-v1:0",
        "anthropic.claude-3-haiku-20240307-v1:0",
    ]

    def __init__(self):
        self._client = None
        self._guardrail_client = None

    @property
    def client(self):
        if self._client is None:
            kwargs = {"region_name": settings.aws_region or "ap-southeast-1"}
            if getattr(settings, "aws_access_key_id", None) and getattr(settings, "aws_secret_access_key", None):
                kwargs["aws_access_key_id"] = settings.aws_access_key_id
                kwargs["aws_secret_access_key"] = settings.aws_secret_access_key
            self._client = boto3.client('bedrock-runtime', **kwargs)
        return self._client

    @property
    def guardrail_client(self):
        if self._guardrail_client is None:
            kwargs = {"region_name": settings.aws_region or "ap-southeast-1"}
            if getattr(settings, "aws_access_key_id", None) and getattr(settings, "aws_secret_access_key", None):
                kwargs["aws_access_key_id"] = settings.aws_access_key_id
                kwargs["aws_secret_access_key"] = settings.aws_secret_access_key
            self._guardrail_client = boto3.client('bedrock-runtime', **kwargs)
        return self._guardrail_client

    def invoke_model(self, model_id: str, system_prompt: str, user_message: str, max_tokens: int = 2048) -> str:
        # Try requested model first, then fallback models
        models_to_try = [model_id]
        for fb in self.FALLBACK_MODELS:
            if fb not in models_to_try:
                models_to_try.append(fb)

        last_err = None
        for candidate_model in models_to_try:
            # 1. Try modern Bedrock Converse API first (AWS recommended standard for Claude models)
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
                    logger.info(f"Bedrock Converse API succeeded with model: {candidate_model}")
                    return result_text
            except Exception as conv_err:
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
                    logger.info(f"Bedrock invoke_model succeeded with model: {candidate_model}")
                    return text
            except Exception as e:
                last_err = e
                logger.warning(f"Bedrock model {candidate_model} failed: {e}. Trying next candidate...")

        raise last_err or RuntimeError("All Bedrock model candidates failed")

    def invoke_model_stream(self, model_id: str, system_prompt: str, user_message: str, max_tokens: int = 2048) -> Generator[str, None, None]:
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
            guardrailVersion='DRAFT',
            source=source,
            content=[{'text': {'text': text}}]
        )
        return {
            "action": response.get("action", "NONE"),
            "filtered_text": response.get("outputs", [{}])[0].get("text", text)
        }

bedrock_client = BedrockClient()
