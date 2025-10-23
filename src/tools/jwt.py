from __future__ import annotations

from datetime import datetime, timedelta, timezone
import jwt
from jwt import ExpiredSignatureError, InvalidTokenError
from tortoise.exceptions import DoesNotExist

from config import jwt_access_min, jwt_algorithm, jwt_refresh_day, jwt_secret_key
from src.model.user import User

_ACCESS = "access"
_REFRESH = "refresh"


def _generate_token(user_id: int, token_type: str, expires_delta: timedelta) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "type": token_type,
        "iat": int(now.timestamp()),
        "exp": int((now + expires_delta).timestamp()),
    }
    token = jwt.encode(payload, jwt_secret_key, algorithm=jwt_algorithm)
    return token if isinstance(token, str) else token.decode()


def issue_tokens_for_user(user: User) -> dict[str, str]:
    return {
        "access_token": _generate_token(user.id, _ACCESS, timedelta(minutes=jwt_access_min)),
        "refresh_token": _generate_token(user.id, _REFRESH, timedelta(days=jwt_refresh_day)),
    }


def decode_token(token: str, expected_type: str | None = None) -> dict:
    try:
        payload = jwt.decode(token, jwt_secret_key, algorithms=[jwt_algorithm])
    except ExpiredSignatureError as exc:
        raise ValueError("Token has expired") from exc
    except InvalidTokenError as exc:
        raise ValueError("Token is invalid") from exc

    token_type = payload.get("type")
    if expected_type is not None and token_type != expected_type:
        raise ValueError(f"Token must be of type '{expected_type}'")

    return payload


async def get_user_from_token(token: str, expected_type: str | None = None) -> User:
    payload = decode_token(token, expected_type)
    user_id = payload.get("sub")
    if user_id is None:
        raise ValueError("Token payload missing subject")

    try:
        return await User.get(id=user_id)
    except DoesNotExist as exc:
        raise ValueError("User not found for token") from exc


async def refresh_access_token(refresh_token: str) -> str:
    payload = decode_token(refresh_token, _REFRESH)
    user_id = payload.get("sub")
    if user_id is None:
        raise ValueError("Token payload missing subject")

    # ensure the user still exists
    try:
        await User.get(id=user_id)
    except DoesNotExist as exc:
        raise ValueError("User not found for token") from exc

    return _generate_token(user_id, _ACCESS, timedelta(minutes=jwt_access_min))
