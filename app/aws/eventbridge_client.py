import boto3
import json
from typing import Dict, Any
from app.config import get_settings

settings = get_settings()

class EventBridgeClient:
    def __init__(self):
        self.client = boto3.client('events', region_name=settings.aws_region)

    def put_event(self, source: str, detail_type: str, detail: Dict[str, Any]):
        self.client.put_events(
            Entries=[
                {
                    'Source': source,
                    'DetailType': detail_type,
                    'Detail': json.dumps(detail)
                }
            ]
        )

eventbridge_client = EventBridgeClient()
