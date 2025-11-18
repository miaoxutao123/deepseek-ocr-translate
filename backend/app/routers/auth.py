from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
import logging

from ..config import settings
from ..database import get_db
from ..models import User
from ..schemas import TokenData, UserCreate, UserLogin, Token, UserResponse, APIConfig, APIConfigResponse
from ..utils import verify_password, get_password_hash, EncryptionManager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["authentication"])
security = HTTPBearer(auto_error=False)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    """Authenticate user with username and password"""
    user = db.query(User).filter(User.username == username).first()
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    token_query: Optional[str] = Query(None, alias="token"),
    db: Session = Depends(get_db)
) -> User:
    """Get current authenticated user from JWT token (header or query parameter)"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # Try to get token from header first, then from query parameter
    token = None
    if credentials:
        token = credentials.credentials
    elif token_query:
        token = token_query

    if not token:
        logger.error("No token provided in header or query parameter")
        raise credentials_exception

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            logger.error(f"Token payload missing 'sub' field: {payload}")
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError as e:
        logger.error(f"JWT decode error: {str(e)}")
        raise credentials_exception

    user = db.query(User).filter(User.username == token_data.username).first()
    if user is None:
        logger.error(f"User not found: {token_data.username}")
        raise credentials_exception

    if not user.is_active:
        logger.error(f"User inactive: {token_data.username}")
        raise HTTPException(status_code=400, detail="Inactive user")

    return user


@router.post("/register", response_model=UserResponse)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """Register a new user"""
    # Check if user exists
    existing_user = db.query(User).filter(User.username == user_data.username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already registered")

    # Create new user
    hashed_password = get_password_hash(user_data.password)
    new_user = User(
        username=user_data.username,
        hashed_password=hashed_password
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user


@router.post("/login", response_model=Token)
def login(user_data: UserLogin, db: Session = Depends(get_db)):
    """Login and get access token"""
    user = authenticate_user(db, user_data.username, user_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    return current_user


@router.post("/api-config", response_model=APIConfigResponse)
async def save_api_config(
    config: APIConfig,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Save user's API configuration (keys will be encrypted)"""
    # Encrypt API keys
    if config.ocr_api_key:
        current_user.ocr_api_key = EncryptionManager.encrypt_api_key(
            config.ocr_api_key, current_user.id, settings.SECRET_KEY
        )
    if config.translate_api_key:
        current_user.translate_api_key = EncryptionManager.encrypt_api_key(
            config.translate_api_key, current_user.id, settings.SECRET_KEY
        )
    if config.embedding_api_key:
        current_user.embedding_api_key = EncryptionManager.encrypt_api_key(
            config.embedding_api_key, current_user.id, settings.SECRET_KEY
        )

    # Save other configurations
    current_user.ocr_api_base = config.ocr_api_base
    current_user.ocr_model = config.ocr_model
    current_user.translate_api_base = config.translate_api_base
    current_user.translate_model = config.translate_model
    current_user.embedding_api_base = config.embedding_api_base

    db.commit()

    return APIConfigResponse(
        ocr_api_base=current_user.ocr_api_base,
        ocr_model=current_user.ocr_model,
        ocr_api_key_set=bool(current_user.ocr_api_key),
        translate_api_base=current_user.translate_api_base,
        translate_model=current_user.translate_model,
        translate_api_key_set=bool(current_user.translate_api_key),
        embedding_api_base=current_user.embedding_api_base,
        embedding_api_key_set=bool(current_user.embedding_api_key),
    )


@router.get("/api-config", response_model=APIConfigResponse)
async def get_api_config(
    current_user: User = Depends(get_current_user)
):
    """Get user's API configuration (keys will be masked)"""
    return APIConfigResponse(
        ocr_api_base=current_user.ocr_api_base,
        ocr_model=current_user.ocr_model,
        ocr_api_key_set=bool(current_user.ocr_api_key),
        translate_api_base=current_user.translate_api_base,
        translate_model=current_user.translate_model,
        translate_api_key_set=bool(current_user.translate_api_key),
        embedding_api_base=current_user.embedding_api_base,
        embedding_api_key_set=bool(current_user.embedding_api_key),
    )
