import json
import boto3
from typing import Dict, Any, Generator
from app.config import get_settings

settings = get_settings()

class BedrockClient:
    def __init__(self):
        self.client = boto3.client('bedrock-runtime', region_name=settings.aws_region)
        self.guardrail_client = boto3.client('bedrock-runtime', region_name=settings.aws_region)

    def invoke_model(self, model_id: str, system_prompt: str, user_message: str, max_tokens: int = 2048) -> str:
        payload = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_tokens,
            "system": system_prompt,
            "messages": [{"role": "user", "content": user_message}]
        }
        response = self.client.invoke_model(
            modelId=model_id,
            body=json.dumps(payload),
            contentType="application/json",
            accept="application/json"
        )
        response_body = json.loads(response['body'].read().decode('utf-8'))
        return response_body.get('content', [{}])[0].get('text', '')

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
