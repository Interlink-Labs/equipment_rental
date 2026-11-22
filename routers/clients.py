"""Клиенты — модуль пары Риты и Влады."""
from typing import List, Literal
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from database import get_db
from auth import User, require_admin
import models
import schemas

router = APIRouter(prefix="/clients", tags=["Клиенты"], dependencies=[Depends(require_admin)])

def get_client(client_id: int, db: Session):
    client = db.get(models.Client, client_id)
    if client is None:
        raise HTTPException(404, "Клиент не найден")
    return client

def lock_clients(db: Session):
    if db.get_bind().dialect.name == "sqlite":
        db.execute(text("BEGIN IMMEDIATE"))

def ensure_unique_phone(db: Session, phone: str, client_id=None):
    # Сравниваем и номера старых записей, сохранённые без разделителей.
    for other in db.query(models.Client).filter(models.Client.id != client_id).all():
        try:
            normalized = schemas.normalize_client_phone(other.phone or "")
        except ValueError:
            normalized = other.phone
        if normalized == phone:
            raise HTTPException(409, "Клиент с таким телефоном уже существует")

def save_client(db: Session, client):
    try:
        db.commit()
        db.refresh(client)
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Телефон уже используется или запись связана с другими данными")
    return client

@router.get("/", response_model=List[schemas.ClientResponse])
def list_clients(query: str = Query("", max_length=150),
                 sort: Literal["id", "name"] = "id", db: Session = Depends(get_db)):
    items = db.query(models.Client).all()
    search = query.strip().casefold()
    if search:
        digits = "".join(char for char in search if char.isdigit())
        items = [item for item in items if search in item.full_name.casefold()
                 or search in (item.phone or "").casefold()
                 or (digits and all(char.isdigit() or char in " +()-" for char in search)
                     and digits in "".join(char for char in (item.phone or "") if char.isdigit()))]
    return sorted(items, key=lambda item: (item.full_name.casefold(), item.id) if sort == "name" else item.id)

@router.get("/search", response_model=List[schemas.ClientResponse])
def search_clients(query: str = Query("", max_length=150), db: Session = Depends(get_db)):
    return list_clients(query=query, db=db)

@router.get("/{client_id}", response_model=schemas.ClientResponse)
def read_client(client_id: int, db: Session = Depends(get_db)):
    return get_client(client_id, db)

@router.post("/", response_model=schemas.ClientResponse, status_code=201)
def create_client(data: schemas.ClientCreateValidated, db: Session = Depends(get_db)):
    lock_clients(db)
    ensure_unique_phone(db, data.phone)
    client = models.Client(**data.model_dump())
    db.add(client)
    return save_client(db, client)

@router.put("/{client_id}", response_model=schemas.ClientResponse)
def update_client(client_id: int, data: schemas.ClientUpdate, db: Session = Depends(get_db)):
    lock_clients(db)
    client = get_client(client_id, db)
    changes = data.model_dump(exclude_unset=True)
    if "phone" in changes:
        ensure_unique_phone(db, changes["phone"], client_id)
    for field, value in changes.items():
        setattr(client, field, value)
    return save_client(db, client)

@router.delete("/{client_id}", status_code=204)
def delete_client(client_id: int, db: Session = Depends(get_db)):
    lock_clients(db)
    client = get_client(client_id, db)
    if client.rentals:
        raise HTTPException(409, "У клиента есть история аренды. Удаление невозможно")
    if db.query(User).filter_by(client_id=client_id).first():
        raise HTTPException(409, "Клиент связан с аккаунтом. Удаление невозможно")
    db.delete(client)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Клиент связан с другими данными")
    return Response(status_code=204)
