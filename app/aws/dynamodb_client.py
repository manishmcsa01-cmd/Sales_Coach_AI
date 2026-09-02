import boto3
from typing import Dict, Any, List
from boto3.dynamodb.conditions import Key
from app.config import get_settings

settings = get_settings()

class DynamoDBClient:
    def __init__(self):
        self.resource = boto3.resource('dynamodb', region_name=settings.aws_region)

    def put_item(self, table: str, item: Dict[str, Any]):
        self.resource.Table(table).put_item(Item=item)

    def get_item(self, table: str, key: Dict[str, Any]) -> Dict[str, Any]:
        response = self.resource.Table(table).get_item(Key=key)
        return response.get('Item', {})

    def query(self, table: str, key_condition: Dict[str, Any]) -> List[Dict[str, Any]]:
        if not key_condition:
            return []
        
        condition_expression = None
        for k, v in key_condition.items():
            if condition_expression is None:
                condition_expression = Key(k).eq(v)
            else:
                condition_expression = condition_expression & Key(k).eq(v)
                
        response = self.resource.Table(table).query(
            KeyConditionExpression=condition_expression
        )
        return response.get('Items', [])

    def delete_item(self, table: str, key: Dict[str, Any]):
        self.resource.Table(table).delete_item(Key=key)

dynamodb_client = DynamoDBClient()
