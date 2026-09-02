import boto3
import base64
from app.config import get_settings

settings = get_settings()

class KMSClient:
    def __init__(self):
        self.client = boto3.client('kms', region_name=settings.aws_region)
        self.key_id = settings.kms_key_id

    def encrypt(self, plaintext: str) -> str:
        response = self.client.encrypt(
            KeyId=self.key_id,
            Plaintext=plaintext.encode('utf-8')
        )
        return base64.b64encode(response['CiphertextBlob']).decode('utf-8')

    def decrypt(self, ciphertext: str) -> str:
        blob = base64.b64decode(ciphertext.encode('utf-8'))
        response = self.client.decrypt(CiphertextBlob=blob)
        return response['Plaintext'].decode('utf-8')

kms_client = KMSClient()
