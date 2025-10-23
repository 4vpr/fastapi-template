from fastapi import APIRouter, HTTPException, Depends
from tortoise.exceptions import DoesNotExist

from src.model.schema.token import (
    TokenRefreshRequest,
    TokenRefreshResponse,
    TokenResponse,
)
from src.model.schema.user import UserCreate, UserLogin, UserResponse
from src.model.user import User
from src.tools.jwt import issue_tokens_for_user, refresh_access_token, get_user_from_token

router = APIRouter(
    prefix="/user",
    tags=["user"],
    responses={404: {"description": "Not found"}},
)


@router.post("/login", response_model=TokenResponse)
async def login(user_login: UserLogin):
    try:
        user = await User.get(login_id=user_login.login_id)
    except DoesNotExist:
        raise HTTPException(status_code=400, detail="Invalid login ID or password")

    if not user.verify_password(user_login.password):
        raise HTTPException(status_code=400, detail="Invalid login ID or password")

    tokens = issue_tokens_for_user(user)
    return TokenResponse(**tokens)

@router.post("/refresh", response_model=TokenRefreshResponse)
async def refresh_tokens(request: TokenRefreshRequest):
    try:
        access_token = await refresh_access_token(request.refresh_token)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc))

    return TokenRefreshResponse(access_token=access_token)

@router.post("/me", response_model=UserResponse)
async def get_current_user(user: User = Depends(get_user_from_token)):
    return UserResponse(
        id=user.id,
        username=user.username,
        number_of_posts=user.number_of_posts,
    )

@router.post("/", response_model=UserResponse)
async def create_user(user_create: UserCreate):
    if await User.filter(login_id=user_create.login_id).exists():
        raise HTTPException(status_code=400, detail="Login ID already registered")

    user = User(username=user_create.username, login_id=user_create.login_id)
    user.set_password(user_create.password)
    await user.save()
    return UserResponse(
        id=user.id,
        username=user.username,
        number_of_posts=user.number_of_posts,
    )
