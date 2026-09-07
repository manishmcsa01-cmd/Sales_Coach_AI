from fastapi import APIRouter, Depends, HTTPException
from app.schemas.auth import LoginRequest, LoginResponse, UserClaims
from app.api.dependencies import get_db, get_current_user
from app.aws.cognito_client import cognito_client
from app.config import get_settings

router = APIRouter()

@router.post("/login", response_model=LoginResponse)
def login(request: LoginRequest, db = Depends(get_db)):
    settings = get_settings()
    try:
        response = cognito_client.client.admin_initiate_auth(
            UserPoolId=settings.cognito_user_pool_id,
            ClientId=settings.cognito_app_client_id,
            AuthFlow='ADMIN_NO_SRP_AUTH',
            AuthParameters={
                'USERNAME': request.email,
                'PASSWORD': request.password
            }
        )
        
        auth_result = response.get('AuthenticationResult')
        if not auth_result:
            raise HTTPException(status_code=401, detail="Authentication failed")
            
        access_token = auth_result.get('AccessToken')
        id_token = auth_result.get('IdToken')
        
        return LoginResponse(
            access_token=id_token,
            role="unknown",
            user_name=request.email.split('@')[0]
        )
    except cognito_client.client.exceptions.NotAuthorizedException:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/logout")
def logout(user: UserClaims = Depends(get_current_user)):
    settings = get_settings()
    try:
        cognito_client.client.admin_user_global_sign_out(
            UserPoolId=settings.cognito_user_pool_id,
            Username=user.user_id
        )
        return {"message": "Logged out"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/me", response_model=UserClaims)
def me(user: UserClaims = Depends(get_current_user)):
    return user
