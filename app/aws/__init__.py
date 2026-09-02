from .bedrock_client import bedrock_client, BedrockClient
from .s3_client import s3_client, S3Client
from .dynamodb_client import dynamodb_client, DynamoDBClient
from .cognito_client import cognito_client, CognitoClient
from .cloudwatch_client import cloudwatch_client, CloudWatchClient
from .secrets_client import secrets_client, SecretsClient
from .sns_client import sns_client, SNSClient
from .eventbridge_client import eventbridge_client, EventBridgeClient
from .sagemaker_client import sagemaker_client, SageMakerClient
from .kms_client import kms_client, KMSClient
from .xray_helpers import init_xray, trace, XRayMiddleware

__all__ = [
    'bedrock_client', 'BedrockClient',
    's3_client', 'S3Client',
    'dynamodb_client', 'DynamoDBClient',
    'cognito_client', 'CognitoClient',
    'cloudwatch_client', 'CloudWatchClient',
    'secrets_client', 'SecretsClient',
    'sns_client', 'SNSClient',
    'eventbridge_client', 'EventBridgeClient',
    'sagemaker_client', 'SageMakerClient',
    'kms_client', 'KMSClient',
    'init_xray', 'trace', 'XRayMiddleware'
]
