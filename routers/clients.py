"""
routers/clients.py — Эндпоинты для работы с клиентами.
Зона ответственности: Пара 2 (ветка feature/clients).
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from database import get_db
import models
import schemas

router = APIRouter(prefix="/clients", tags=["Клиенты"])


# =======================================================================
# ЗАДАНИЕ ДЛЯ ПАРЫ 2:
# Посмотрите, как сделан файл routers/equipment.py, и сделайте аналогично:
# =======================================================================

@router.get("/", response_model=List[schemas.ClientResponse])
def get_all_clients(db: Session = Depends(get_db)):
    """
    TODO: Пара 2 — Получить список всех клиентов.
    Подсказка: db.query(models.Client).all()
    """
    clients = db.query(models.Client).all()
    return clients


@router.post("/", response_model=schemas.ClientResponse, status_code=status.HTTP_201_CREATED)
def create_client(client_data: schemas.ClientCreate, db: Session = Depends(get_db)):
    """
    TODO: Пара 2 — Добавить нового клиента.
    Не забудьте проверить, что клиент с таким номером телефона еще не зарегистрирован!
    """
    # 1. Проверяем телефон на дубликаты
    existing = db.query(models.Client).filter(models.Client.phone == client_data.phone).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Клиент с таким номером телефона уже существует!"
        )

    # 2. Создаем и сохраняем
    new_client = models.Client(
        full_name=client_data.full_name,
        phone=client_data.phone
    )
    db.add(new_client)
    db.commit()
    db.refresh(new_client)
    return new_client


# @router.get("/search", response_model=List[schemas.ClientResponse])
# def search_clients(query: str, db: Session = Depends(get_db)):
#     """TODO: Пара 2 — Поиск клиента по ФИО или номеру телефона."""
#     pass
