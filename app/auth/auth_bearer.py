"""
Auth Bearer — FastAPI JWT dependency
"""

from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.auth.auth_handler import decode_token
from app.database.db_models import UserDB
from app.database.base import SessionLocal

security = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Optional[UserDB]:
    """
    Token varsa kullanıcıyı döner, yoksa None döner.
    Opsiyonel auth — zorunlu değil.
    """
    if not credentials:
        return None

    payload = decode_token(credentials.credentials)
    if not payload:
        return None

    user_id = payload.get("sub")
    if not user_id:
        return None

    with SessionLocal() as db:
        user = db.query(UserDB).filter(UserDB.id == user_id).first()
        return user


def require_current_user(
    user: Optional[UserDB] = Depends(get_current_user),
) -> UserDB:
    """
    Token zorunlu — yoksa 401 döner.
    """
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Giriş yapmanız gerekiyor",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user
