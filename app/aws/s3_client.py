import boto3
from app.config import get_settings

settings = get_settings()

class S3Client:
    def __init__(self):
        self.client = boto3.client('s3', region_name=settings.aws_region)

    def upload_file(self, bucket: str, key: str, data: bytes):
        self.client.put_object(Bucket=bucket, Key=key, Body=data)

    def download_file(self, bucket: str, key: str) -> bytes:
        response = self.client.get_object(Bucket=bucket, Key=key)
        return response['Body'].read()

    def list_objects(self, bucket: str, prefix: str = '') -> list:
        response = self.client.list_objects_v2(Bucket=bucket, Prefix=prefix)
        return [obj['Key'] for obj in response.get('Contents', [])]

s3_client = S3Client()
