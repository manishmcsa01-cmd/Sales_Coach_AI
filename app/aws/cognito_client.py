import boto3
import json
import urllib.request
from typing import Dict, Any
from jose import jwk, jwt
from jose.utils import base64url_decode
from app.config import get_settings

settings = get_settings()

class CognitoClient:
    def __init__(self):
        self.client = boto3.client('cognito-idp', region_name=settings.aws_region)
        self.user_pool_id = settings.cognito_user_pool_id
        self.client_id = settings.cognito_client_id
        self.region = settings.aws_region
        self.jwks_url = f"https://cognito-idp.{self.region}.amazonaws.com/{self.user_pool_id}/.well-known/jwks.json"
        self._jwks = None

    def _get_jwks(self):
        if not self._jwks:
            with urllib.request.urlopen(self.jwks_url) as response:
                self._jwks = json.loads(response.read().decode('utf-8'))
        return self._jwks

    def verify_token(self, token: str) -> Dict[str, Any]:
        headers = jwt.get_unverified_headers(token)
        kid = headers.get('kid')
        jwks = self._get_jwks()
        
        key_index = -1
        for i in range(len(jwks['keys'])):
            if kid == jwks['keys'][i]['kid']:
                key_index = i
                break
        if key_index == -1:
            raise ValueError("Public key not found in jwks.json")
            
        public_key = jwk.construct(jwks['keys'][key_index])
        message, encoded_signature = str(token).rsplit('.', 1)
        decoded_signature = base64url_decode(encoded_signature.encode('utf-8'))
        
        if not public_key.verify(message.encode('utf-8'), decoded_signature):
            raise ValueError("Signature verification failed")
            
        claims = jwt.get_unverified_claims(token)
        return claims

    def get_user(self, access_token: str) -> Dict[str, Any]:
        response = self.client.get_user(AccessToken=access_token)
        return response

    def authenticate_user(self, username: str, password: str) -> Dict[str, Any]:
        response = self.client.admin_initiate_auth(
            UserPoolId=self.user_pool_id,
            ClientId=self.client_id,
            AuthFlow='ADMIN_NO_SRP_AUTH',
            AuthParameters={
                'USERNAME': username,
                'PASSWORD': password
            }
        )
        return response.get('AuthenticationResult', {})

cognito_client = CognitoClient()
