from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from database import get_db
from auth import User, passwords, dummy_hash, create_token, get_current_user
import models

router = APIRouter(prefix="/auth", tags=["Авторизация"])

class Registration(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    username: str = Field(min_length=3, max_length=64)
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=1, max_length=150)
    phone: str = Field(min_length=5, max_length=30)

class Login(BaseModel):
    username: str
    password: str = Field(max_length=128)

class Account(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    username: str
    role: str
    client_id: int

@router.post("/registration", response_model=Account, status_code=201)
def register(data: Registration, db: Session = Depends(get_db)):
    client = models.Client(full_name=data.full_name, phone=data.phone)
    user = User(username=data.username, password_hash=passwords.hash(data.password), role="USER")
    try:
        db.add(client)
        db.flush()
        user.client_id = client.id
        db.add(user)
        db.commit()
        db.refresh(user)
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Логин или телефон уже используется")
    return user

@router.post("/login")
def login(data: Login, db: Session = Depends(get_db)):
    user = db.query(User).filter_by(username=data.username).first()
    valid = passwords.verify(data.password, user.password_hash if user else dummy_hash)
    if user is None or not valid:
        raise HTTPException(401, "Неверный логин или пароль", headers={"WWW-Authenticate": "Bearer"})
    return {"access_token": create_token(user), "token_type": "bearer", "expires_in": 1800}

@router.get("/me", response_model=Account)
def me(user: User = Depends(get_current_user)):
    return user
