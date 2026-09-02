from fastapi import Depends, HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
import urllib.request
import json
from app.config import get_settings
from app.schemas.auth import UserClaims
from app.db.session import get_db as _get_db, AsyncSessionLocal

security = HTTPBearer(auto_error=False)

async def get_db():
    """Async database session dependency."""
    async with AsyncSessionLocal() as session:
        yield session

def get_cognito_jwks():
    settings = get_settings()
    url = f"https://cognito-idp.{settings.aws_region}.amazonaws.com/{settings.cognito_user_pool_id}/.well-known/jwks.json"
    with urllib.request.urlopen(url) as response:
        return json.loads(response.read().decode("utf-8"))

def get_current_user(credentials: HTTPAuthorizationCredentials = Security(security)) -> UserClaims:
    """Extract and validate user from JWT token using AWS Cognito JWKS."""
    if credentials is None:
        raise HTTPException(status_code=401, detail="Not authenticated")

    token = credentials.credentials
    settings = get_settings()
    
    try:
        # Get unverified header to find the kid
        unverified_header = jwt.get_unverified_header(token)
        jwks = get_cognito_jwks()
        
        rsa_key = {}
        for key in jwks["keys"]:
            if key["kid"] == unverified_header["kid"]:
                rsa_key = {
                    "kty": key["kty"],
                    "kid": key["kid"],
                    "use": key["use"],
                    "n": key["n"],
                    "e": key["e"]
                }
                break
                
        if not rsa_key:
            raise HTTPException(status_code=401, detail="Invalid token kid")
            
        payload = jwt.decode(
            token,
            rsa_key,
            algorithms=["RS256"],
            audience=settings.cognito_app_client_id,
            issuer=f"https://cognito-idp.{settings.aws_region}.amazonaws.com/{settings.cognito_user_pool_id}"
        )
        
        # Extract user claims
        user_id = payload.get("sub")
        role = payload.get("custom:role") or (payload.get("cognito:groups", [None])[0])
        dsp_id = payload.get("custom:dsp_id")
        area_id = payload.get("custom:area_id")
        manager_id = payload.get("custom:manager_id")
        
        return UserClaims(
            user_id=user_id,
            role=role,
            dsp_id=dsp_id,
            area_id=area_id,
            manager_id=manager_id
        )
    except JWTError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=401, detail="Authentication failed")
