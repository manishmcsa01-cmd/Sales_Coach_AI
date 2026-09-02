import boto3
import time
from typing import Dict, List, Any
from app.config import get_settings

settings = get_settings()

class CloudWatchClient:
    def __init__(self):
        self.client = boto3.client('cloudwatch', region_name=settings.aws_region)
        self.logs_client = boto3.client('logs', region_name=settings.aws_region)
        self._sequence_tokens = {}

    def put_metric(self, namespace: str, metric_name: str, value: float, unit: str = 'None', dimensions: List[Dict[str, str]] = None):
        dims = dimensions or []
        self.client.put_metric_data(
            Namespace=namespace,
            MetricData=[
                {
                    'MetricName': metric_name,
                    'Dimensions': dims,
                    'Value': value,
                    'Unit': unit
                }
            ]
        )

    def put_log_event(self, log_group: str, log_stream: str, message: str):
        timestamp = int(round(time.time() * 1000))
        log_event = {
            'timestamp': timestamp,
            'message': message
        }
        
        kwargs = {
            'logGroupName': log_group,
            'logStreamName': log_stream,
            'logEvents': [log_event]
        }
        
        token_key = f"{log_group}:{log_stream}"
        if token_key in self._sequence_tokens:
            kwargs['sequenceToken'] = self._sequence_tokens[token_key]
            
        try:
            response = self.logs_client.put_log_events(**kwargs)
            self._sequence_tokens[token_key] = response['nextSequenceToken']
        except self.logs_client.exceptions.InvalidSequenceTokenException as e:
            kwargs['sequenceToken'] = e.response['expectedSequenceToken']
            response = self.logs_client.put_log_events(**kwargs)
            self._sequence_tokens[token_key] = response['nextSequenceToken']
        except self.logs_client.exceptions.DataAlreadyAcceptedException as e:
            self._sequence_tokens[token_key] = e.response['expectedSequenceToken']

cloudwatch_client = CloudWatchClient()
