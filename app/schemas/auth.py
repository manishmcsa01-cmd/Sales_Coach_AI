from pydantic import BaseModel
from typing import Optional

class LoginRequest(BaseModel):
    email: str
    password: str

class LoginResponse(BaseModel):
    access_token: str
    role: str
    user_name: str

class UserClaims(BaseModel):
    user_id: str
    dsp_id: Optional[str] = None
    role: str
    area_id: Optional[str] = None
    manager_id: Optional[str] = None
