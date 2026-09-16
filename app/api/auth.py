"""POST /auth/login."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.adapters.db import get_db
from app.api.errors import unauthorized
from app.services.login import authenticate
from app.settings import Settings, get_settings

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginBody(BaseModel):
    username: str = Field(min_length=1)
    password: str = Field(min_length=1)


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int


@router.post("/login", response_model=LoginResponse)
def login(
    body: LoginBody,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> LoginResponse:
    result = authenticate(db, body.username, body.password, settings)
    if result is None:
        unauthorized()
    token, user_id = result
    return LoginResponse(access_token=token, user_id=user_id)
