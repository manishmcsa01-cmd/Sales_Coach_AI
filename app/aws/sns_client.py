import boto3
from app.config import get_settings

settings = get_settings()

class SNSClient:
    def __init__(self):
        self.client = boto3.client('sns', region_name=settings.aws_region)

    def publish(self, topic_arn: str, subject: str, message: str):
        self.client.publish(
            TopicArn=topic_arn,
            Subject=subject,
            Message=message
        )

sns_client = SNSClient()
