from datetime import datetime, timedelta, timezone

import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

import config
from db.connection import get_session_dependency
from db.models import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")
oauth2_scheme_optional = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def create_access_token(user_id: int) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=config.settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return jwt.encode(
        {"sub": str(user_id), "exp": expire},
        config.settings.JWT_SECRET_KEY,
        algorithm=config.settings.JWT_ALGORITHM,
    )


def _decode_token(token: str, session: Session) -> User:
    error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token,
            config.settings.JWT_SECRET_KEY,
            algorithms=[config.settings.JWT_ALGORITHM],
        )
        user_id: str | None = payload.get("sub")
        if user_id is None:
            raise error
    except JWTError:
        raise error
    user = session.query(User).filter_by(id=int(user_id)).first()
    if user is None:
        raise error
    return user


def get_current_user(
        token: str = Depends(oauth2_scheme),
        session: Session = Depends(get_session_dependency),
) -> User:
    return _decode_token(token, session)


def get_current_user_optional(
        token: str | None = Depends(oauth2_scheme_optional),
        session: Session = Depends(get_session_dependency),
) -> User | None:
    if not token:
        return None
    try:
        return _decode_token(token, session)
    except HTTPException:
        return None
