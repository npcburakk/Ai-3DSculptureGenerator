"""
User Service — kayıt, giriş, profil işlemleri
"""

import uuid
from datetime import datetime

from fastapi import HTTPException, status

from app.auth.auth_handler import hash_password, verify_password, create_access_token
from app.database.base import SessionLocal
from app.database.db_models import UserDB
from app.schemas.user_schema import UserRegisterRequest, UserLoginRequest, UserResponse, TokenResponse


class UserService:

    def register(self, payload: UserRegisterRequest) -> UserResponse:
        with SessionLocal() as db:
            # Kullanıcı adı kontrolü
            if db.query(UserDB).filter(UserDB.username == payload.username).first():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Bu kullanıcı adı zaten kullanılıyor",
                )
            # Email kontrolü
            if db.query(UserDB).filter(UserDB.email == payload.email).first():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Bu email zaten kullanılıyor",
                )

            user = UserDB(
                id=str(uuid.uuid4()),
                username=payload.username,
                email=payload.email,
                hashed_password=hash_password(payload.password),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            db.add(user)
            db.commit()
            db.refresh(user)

            return UserResponse(
                id=user.id,
                username=user.username,
                email=user.email,
                is_active=user.is_active,
                created_at=user.created_at,
            )

    def login(self, payload: UserLoginRequest) -> TokenResponse:
        with SessionLocal() as db:
            user = db.query(UserDB).filter(UserDB.username == payload.username).first()

            if not user or not verify_password(payload.password, user.hashed_password):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Kullanıcı adı veya şifre hatalı",
                )

            if not user.is_active:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Hesabınız devre dışı",
                )

            token = create_access_token({"sub": user.id, "username": user.username})

            return TokenResponse(
                access_token=token,
                token_type="bearer",
                user=UserResponse(
                    id=user.id,
                    username=user.username,
                    email=user.email,
                    is_active=user.is_active,
                    created_at=user.created_at,
                ),
            )

    def get_profile(self, user: UserDB) -> UserResponse:
        return UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            is_active=user.is_active,
            created_at=user.created_at,
        )
