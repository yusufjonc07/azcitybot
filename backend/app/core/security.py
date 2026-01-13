import hashlib
import hmac
import time
from datetime import datetime, timedelta, timezone
from typing import Any
from urllib.parse import parse_qs

import jwt
from passlib.context import CryptContext

from app.core.config import settings


ALGORITHM = "HS256"
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(subject: str | Any, expires_delta: timedelta) -> str:
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_telegram_auth(data: dict) -> bool:
    """
    Verify the Telegram login widget authentication data.
    https://core.telegram.org/widgets/login#checking-authorization
    """
    check_hash = data.pop("hash", None)
    if not check_hash:
        return False
    
    # Check auth_date is not too old (within 24 hours)
    auth_date = data.get("auth_date")
    if auth_date:
        if time.time() - int(auth_date) > 86400:  # 24 hours
            return False
    
    # Create the data-check-string
    data_check_arr = sorted([f"{k}={v}" for k, v in data.items() if v is not None])
    data_check_string = "\n".join(data_check_arr)
    
    # Create secret key from bot token
    secret_key = hashlib.sha256(settings.TELEGRAM_BOT_TOKEN.encode()).digest()
    
    # Calculate HMAC-SHA256
    calculated_hash = hmac.new(
        secret_key, 
        data_check_string.encode(), 
        hashlib.sha256
    ).hexdigest()
    
    # Compare hashes
    return hmac.compare_digest(calculated_hash, check_hash)


def verify_webapp_init_data(init_data: str) -> dict | None:
    """
    Verify Telegram Mini App (WebApp) init data.
    https://core.telegram.org/bots/webapps#validating-data-received-via-the-mini-app
    
    Returns parsed user data if valid, None if invalid.
    """
    # Parse the init_data query string
    parsed = parse_qs(init_data)
    
    # Extract hash
    if "hash" not in parsed:
        return None
    check_hash = parsed["hash"][0]
    
    # Check auth_date is not too old (within 24 hours)
    if "auth_date" in parsed:
        auth_date = int(parsed["auth_date"][0])
        if time.time() - auth_date > 86400:  # 24 hours
            return None
    
    # Build data-check-string (exclude hash, sort alphabetically)
    data_check_arr = []
    for key in sorted(parsed.keys()):
        if key != "hash":
            data_check_arr.append(f"{key}={parsed[key][0]}")
    data_check_string = "\n".join(data_check_arr)
    
    # Create secret key: HMAC_SHA256(bot_token, "WebAppData")
    secret_key = hmac.new(
        b"WebAppData",
        settings.TELEGRAM_BOT_TOKEN.encode(),
        hashlib.sha256
    ).digest()
    
    # Calculate HMAC-SHA256 of data-check-string
    calculated_hash = hmac.new(
        secret_key,
        data_check_string.encode(),
        hashlib.sha256
    ).hexdigest()
    
    # Verify hash
    if not hmac.compare_digest(calculated_hash, check_hash):
        return None
    
    # Parse and return user data
    import json
    if "user" in parsed:
        try:
            return json.loads(parsed["user"][0])
        except json.JSONDecodeError:
            return None
    
    return None
