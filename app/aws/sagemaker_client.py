import boto3
import json
from typing import Dict, Any
from app.config import get_settings

settings = get_settings()

class SageMakerClient:
    def __init__(self):
        self.client = boto3.client('sagemaker-runtime', region_name=settings.aws_region)

    def invoke_endpoint(self, endpoint_name: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        response = self.client.invoke_endpoint(
            EndpointName=endpoint_name,
            ContentType='application/json',
            Body=json.dumps(payload)
        )
        return json.loads(response['Body'].read().decode('utf-8'))

sagemaker_client = SageMakerClient()
