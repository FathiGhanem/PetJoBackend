from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from db.session import get_db
from schemas.auth import Token, LoginRequest, RefreshTokenRequest, ResetPasswordRequest, ChangePasswordRequest
from schemas.user import UserCreate, User as UserSchema
from schemas.common import ApiResponse
from dependencies import get_user_service, get_current_user_id
from services.user_service import UserService
from core.security import create_access_token, create_refresh_token, decode_token
from core.token_blacklist import blacklist_refresh_token, blacklist_token, is_token_blacklisted
from core.rate_limit import limiter, RATE_LIMITS
from core.config import settings
from exceptions import (
    InvalidCredentialsException,
    EmailAlreadyExistsException,
    InactiveAccountException,
    AuthenticationException
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post(
    "/register",
    response_model=ApiResponse[UserSchema],
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="Create a new user account with email and password"
)
@limiter.limit(RATE_LIMITS["auth"])
async def register(
    request: Request,
    user_in: UserCreate,
    user_service: UserService = Depends(get_user_service)
):
    """Register a new user."""
    logger.info(f"Registering new user: {user_in.email}")
    
    try:
        user = await user_service.create_user(
            email=user_in.email,
            password=user_in.password,
            full_name=user_in.full_name
        )
        
        logger.info(f"User registered successfully: {user.id}")
        return ApiResponse(
            success=True,
            data=user,
            message="User registered successfully"
        )
    
    except EmailAlreadyExistsException:
        logger.warning(f"Registration failed: Email already exists")
        raise


@router.post(
    "/login",
    response_model=ApiResponse[Token],
    summary="Login",
    description="Authenticate and get access/refresh tokens"
)
@limiter.limit(RATE_LIMITS["auth"])
async def login(
    request: Request,
    login_data: LoginRequest,
    user_service: UserService = Depends(get_user_service)
):
    """Login and get access token."""
    logger.info(f"Login attempt for: {login_data.email}")
    
    user = await user_service.authenticate(
        email=login_data.email,
        password=login_data.password
    )
    
    if not user:
        logger.warning(f"Failed login attempt for: {login_data.email}")
        raise InvalidCredentialsException()
    
    if not user.is_active:
        logger.warning(f"Inactive account login attempt: {login_data.email}")
        raise InactiveAccountException()
    
    # Create tokens
    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})
    
    logger.info(f"User logged in successfully: {user.id}")
    
    return ApiResponse(
        success=True,
        data={
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        },
        message="Login successful"
    )


@router.post(
    "/refresh",
    response_model=ApiResponse[Token],
    summary="Refresh token",
    description="Get new access token using refresh token"
)
@limiter.limit(RATE_LIMITS["auth"])
async def refresh_token(request: Request, refresh_data: RefreshTokenRequest):
    """Refresh access token using refresh token."""
    logger.info("Token refresh attempt")
    
    try:
        # Check if refresh token is blacklisted
        if await is_token_blacklisted(refresh_data.refresh_token):
            logger.warning("Attempt to use blacklisted refresh token")
            raise AuthenticationException("Token has been revoked")
        
        payload = decode_token(refresh_data.refresh_token)
        
        if payload.get("type") != "refresh":
            logger.warning("Invalid token type for refresh")
            raise AuthenticationException("Invalid token type")
        
        user_id = payload.get("sub")
        if not user_id:
            logger.warning("Invalid token payload")
            raise AuthenticationException("Invalid token")
        
        # Blacklist the old refresh token (single-use refresh tokens)
        await blacklist_refresh_token(user_id, refresh_data.refresh_token)
        
        # Create new tokens
        access_token = create_access_token(data={"sub": user_id})
        new_refresh_token = create_refresh_token(data={"sub": user_id})
        
        logger.info(f"Token refreshed successfully for user: {user_id}")
        
        return ApiResponse(
            success=True,
            data={
                "access_token": access_token,
                "refresh_token": new_refresh_token,
                "token_type": "bearer"
            },
            message="Token refreshed successfully"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh error: {str(e)}")
        raise AuthenticationException("Could not validate refresh token")


@router.post(
    "/logout",
    response_model=ApiResponse[dict],
    summary="Logout",
    description="Logout and invalidate refresh token"
)
@limiter.limit(RATE_LIMITS["auth"])
async def logout(
    request: Request,
    refresh_data: RefreshTokenRequest,
    user_id: str = Depends(get_current_user_id)
):
    """Logout and blacklist refresh token."""
    logger.info(f"Logout attempt for user: {user_id}")
    
    try:
        # Blacklist the refresh token
        await blacklist_refresh_token(user_id, refresh_data.refresh_token)
        
        logger.info(f"User logged out successfully: {user_id}")
        
        return ApiResponse(
            success=True,
            data={"message": "Logged out successfully"},
            message="Logged out successfully"
        )
    
    except Exception as e:
        logger.error(f"Logout error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not logout"
        )


@router.post(
    "/reset-password",
    response_model=ApiResponse[dict],
    summary="Reset password",
    description="Request a password reset (sends reset instructions)"
)
@limiter.limit(RATE_LIMITS["auth"])
async def reset_password(
    request: Request,
    reset_data: ResetPasswordRequest,
    user_service: UserService = Depends(get_user_service)
):
    """Request a password reset by email.
    
    Always returns success to prevent email enumeration.
    """
    logger.info(f"Password reset requested for: {reset_data.email}")
    
    # Always return success even if email doesn't exist (prevent enumeration)
    # TODO: Implement actual email sending logic
    
    return ApiResponse(
        success=True,
        data={"message": "If an account with this email exists, password reset instructions have been sent"},
        message="Password reset instructions sent"
    )


@router.post(
    "/change-password",
    response_model=ApiResponse[dict],
    summary="Change password",
    description="Change the current user's password (requires authentication)"
)
@limiter.limit(RATE_LIMITS["auth"])
async def change_password(
    request: Request,
    password_data: ChangePasswordRequest,
    user_id: str = Depends(get_current_user_id),
    user_service: UserService = Depends(get_user_service)
):
    """Change the authenticated user's password."""
    logger.info(f"Password change attempt for user: {user_id}")
    
    from uuid import UUID
    success = await user_service.change_password(
        user_id=UUID(user_id),
        old_password=password_data.current_password,
        new_password=password_data.new_password
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid current password"
        )
    
    logger.info(f"Password changed successfully for user: {user_id}")
    
    return ApiResponse(
        success=True,
        data={"message": "Password changed successfully"},
        message="Password changed successfully"
    )
