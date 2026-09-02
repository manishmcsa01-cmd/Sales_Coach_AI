import boto3
import json
from typing import Dict, Any
from app.config import get_settings

settings = get_settings()

class SecretsClient:
    def __init__(self):
        self.client = boto3.client('secretsmanager', region_name=settings.aws_region)

    def get_secret(self, secret_name: str) -> Dict[str, Any]:
        response = self.client.get_secret_value(SecretId=secret_name)
        if 'SecretString' in response:
            return json.loads(response['SecretString'])
        return {}

secrets_client = SecretsClient()
