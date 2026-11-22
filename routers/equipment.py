"""
routers/equipment.py — Эндпоинты для работы с оборудованием (инструментами).
Зона ответственности: Пара 1 (ветка feature/equipment).
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from math import isfinite
from typing import List, Optional, Literal
from sqlalchemy import text
from fastapi import Query

from database import get_db
from auth import require_admin
import models
import schemas

router = APIRouter(prefix="/equipment", tags=["Оборудование"])


@router.get("/", response_model=List[schemas.EquipmentResponse])
def get_all_equipment(
    status_filter: Optional[str] = None,
    query: str = Query("", max_length=150),
    sort: Literal["id", "name", "price_asc", "price_desc"] = "id",
    db: Session = Depends(get_db),
):
    """Публичный каталог: поиск, статус и порядок цен."""
    items = db.query(models.Equipment).all()
    if status_filter:
        status_filter = status_filter.upper()
        if status_filter not in {"AVAILABLE", "RENTED", "REPAIR"}:
            raise HTTPException(422, "Неизвестный статус оборудования")
        items = [item for item in items if item.status == status_filter]
    search = query.strip().casefold()
    if search:
        items = [item for item in items if search in item.name.casefold()
                 or search in (item.inventory_number or "").casefold()]
    if sort == "name":
        return sorted(items, key=lambda item: (item.name.casefold(), item.id))
    if sort == "price_asc":
        return sorted(items, key=lambda item: (item.daily_rate, item.id))
    if sort == "price_desc":
        return sorted(items, key=lambda item: (-item.daily_rate, item.id))
    return sorted(items, key=lambda item: item.id)


def lock_equipment(db: Session):
    """Использовать ту же блокировку SQLite, что и при выдаче аренды."""
    if db.get_bind().dialect.name == "sqlite":
        db.execute(text("BEGIN IMMEDIATE"))

@router.get("/{equipment_id}", response_model=schemas.EquipmentResponse)
def get_equipment_by_id(equipment_id: int, db: Session = Depends(get_db)):
    """Получить один инструмент по его ID."""
    tool = db.query(models.Equipment).filter(models.Equipment.id == equipment_id).first()
    if not tool:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Инструмент с ID {equipment_id} не найден"
        )
    return tool


@router.post("/", response_model=schemas.EquipmentResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_admin)])
def create_equipment(item: schemas.EquipmentCreateValidated, db: Session = Depends(get_db)):
    """
    Добавить новый инструмент в базу.
    Проверяет, чтобы инвентарный номер был уникальным.
    """
    # 1. Проверяем, нет ли уже инструмента с таким инвентарным номером
    lock_equipment(db)
    existing_item = db.query(models.Equipment).filter(
        models.Equipment.inventory_number == item.inventory_number
    ).first()
    if existing_item:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Инструмент с инвентарным номером '{item.inventory_number}' уже существует!"
        )

    # 2. Создаем объект модели и сохраняем его в базу
    new_tool = models.Equipment(
        name=item.name,
        inventory_number=item.inventory_number,
        daily_rate=item.daily_rate,
        status="AVAILABLE"
    )
    db.add(new_tool)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Инвентарный номер уже используется")
    db.refresh(new_tool) # Считываем созданную запись (вместе со сгенерированным id)
    return new_tool


@router.put("/{equipment_id}", response_model=schemas.EquipmentResponse, dependencies=[Depends(require_admin)])
def update_equipment(
    equipment_id: int, update_data: schemas.EquipmentUpdate, db: Session = Depends(get_db)
):
    """Изменить название, тариф или статус инструмента."""
    lock_equipment(db)
    tool = get_equipment_by_id(equipment_id, db)
    changes = update_data.model_dump(exclude_none=True)
    if "name" in changes:
        changes["name"] = changes["name"].strip()
        if not changes["name"]:
            raise HTTPException(422, "Укажите название инструмента")
    if "daily_rate" in changes:
        rate = changes["daily_rate"]
        if not isfinite(rate) or rate <= 0:
            raise HTTPException(422, "Тариф должен быть положительным числом")
    if "status" in changes:
        changes["status"] = changes["status"].upper()
        if changes["status"] not in {"AVAILABLE", "REPAIR"}:
            raise HTTPException(422, "Допустимые статусы: AVAILABLE и REPAIR")
        active_rental = db.query(models.Rental).filter_by(equipment_id=equipment_id, status="ACTIVE").first()
        if tool.status == "RENTED" or active_rental:
            raise HTTPException(409, "Сначала оформите возврат инструмента")

    for field, value in changes.items():
        setattr(tool, field, value)
    db.commit()
    db.refresh(tool)
    return tool


@router.delete("/{equipment_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_admin)])
def delete_equipment(equipment_id: int, db: Session = Depends(get_db)):
    """Удалить инструмент, если с ним не связаны записи об аренде."""
    lock_equipment(db)
    tool = get_equipment_by_id(equipment_id, db)
    if tool.status == "RENTED" or tool.rentals:
        raise HTTPException(409, "У инструмента есть записи об аренде")
    db.delete(tool)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(409, "У инструмента есть связанные записи") from exc
