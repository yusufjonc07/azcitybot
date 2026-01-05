from datetime import timedelta
from typing import Any

from fastapi import APIRouter, HTTPException

from app import crud
from app.api.deps import CurrentUser, SessionDep
from app.core import security
from app.core.config import settings
from app.models import Message, TelegramLoginData, TelegramWebAppData, Token, UserPublic

router = APIRouter(tags=["login"])


@router.post("/login/telegram")
def login_with_telegram(session: SessionDep, data: TelegramLoginData) -> Token:
    """
    Telegram Login Widget authentication.
    Verifies the Telegram data and returns an access token.
    """
    # Prepare data dict for verification
    auth_data = {
        "id": data.id,
        "first_name": data.first_name,
        "auth_date": data.auth_date,
        "hash": data.hash,
    }
    if data.last_name:
        auth_data["last_name"] = data.last_name
    if data.username:
        auth_data["username"] = data.username
    if data.photo_url:
        auth_data["photo_url"] = data.photo_url
    
    # Verify Telegram authentication
    if not security.verify_telegram_auth(auth_data):
        raise HTTPException(status_code=400, detail="Invalid Telegram authentication")
    
    # Build full name
    full_name = data.first_name
    if data.last_name:
        full_name = f"{data.first_name} {data.last_name}"
    
    # Get or create user
    user = crud.get_or_create_user_from_telegram(
        session=session,
        telegram_id=data.id,
        username=data.username,
        full_name=full_name,
        photo_url=data.photo_url,
    )
    
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    
    # Create access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return Token(
        access_token=security.create_access_token(
            user.id, expires_delta=access_token_expires
        )
    )


@router.post("/login/webapp")
def login_with_webapp(session: SessionDep, data: TelegramWebAppData) -> Token:
    """
    Telegram Mini App (WebApp) authentication.
    Verifies the initData and returns an access token.
    """
    # Verify and parse the init data
    user_data = security.verify_webapp_init_data(data.init_data)
    if not user_data:
        raise HTTPException(status_code=400, detail="Invalid WebApp init data")
    
    telegram_id = user_data.get("id")
    if not telegram_id:
        raise HTTPException(status_code=400, detail="User ID not found in init data")
    
    # Build full name
    first_name = user_data.get("first_name", "")
    last_name = user_data.get("last_name", "")
    full_name = f"{first_name} {last_name}".strip() or first_name
    
    # Get or create user
    user = crud.get_or_create_user_from_telegram(
        session=session,
        telegram_id=telegram_id,
        username=user_data.get("username"),
        full_name=full_name,
        photo_url=user_data.get("photo_url"),
    )
    
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    
    # Create access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return Token(
        access_token=security.create_access_token(
            user.id, expires_delta=access_token_expires
        )
    )


@router.post("/login/test-token", response_model=UserPublic)
def test_token(current_user: CurrentUser) -> Any:
    """
    Test access token
    """
    return current_user


@router.get("/login/telegram-config")
def get_telegram_config() -> dict:
    """
    Get Telegram bot configuration for the login widget.
    """
    return {
        "bot_username": settings.TELEGRAM_BOT_USERNAME,
    }
