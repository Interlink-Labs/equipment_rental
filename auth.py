"""Общая авторизация для модулей проекта."""
import os
import secrets
from pathlib import Path
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pwdlib import PasswordHash
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import Session
from database import Base, get_db

class User(Base):
    __tablename__ = "auth_users"
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, nullable=False, default="USER")
    client_id = Column(Integer, ForeignKey("clients.id"), unique=True, nullable=False)

passwords = PasswordHash.recommended()
dummy_hash = passwords.hash(secrets.token_urlsafe(24))
bearer = HTTPBearer(auto_error=False)

def secret_key():
    configured = os.environ.get("JWT_SECRET")
    if configured:
        return configured
    path = Path(".jwt-secret")
    try:
        with path.open("x", encoding="utf-8") as stream:
            stream.write(secrets.token_urlsafe(48))
    except FileExistsError:
        pass
    return path.read_text(encoding="utf-8").strip()

def create_token(user):
    now = datetime.now(timezone.utc)
    return jwt.encode(
        {"sub": str(user.id), "iat": now, "exp": now + timedelta(minutes=30)},
        secret_key(), algorithm="HS256",
    )

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer),
    db: Session = Depends(get_db),
):
    error = HTTPException(401, "Войдите в аккаунт", headers={"WWW-Authenticate": "Bearer"})
    if credentials is None:
        raise error
    try:
        payload = jwt.decode(credentials.credentials, secret_key(), algorithms=["HS256"],
                             options={"require": ["exp", "sub", "iat"]})
        user_id = int(payload["sub"])
    except (jwt.InvalidTokenError, ValueError, TypeError):
        raise error
    user = db.get(User, user_id)
    if user is None:
        raise error
    return user

def require_admin(user: User = Depends(get_current_user)):
    if user.role != "ADMIN":
        raise HTTPException(403, "Требуются права администратора")
    return user
