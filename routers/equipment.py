"""
routers/equipment.py — Эндпоинты для работы с оборудованием (инструментами).
Зона ответственности: Пара 1 (ветка feature/equipment).
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from database import get_db
import models
import schemas

router = APIRouter(prefix="/equipment", tags=["Оборудование"])


@router.get("/", response_model=List[schemas.EquipmentResponse])
def get_all_equipment(
    status_filter: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Получить список всех инструментов.
    Если передан параметр status_filter (напр., ?status_filter=AVAILABLE), возвращаются только подходящие.
    """
    query = db.query(models.Equipment)
    if status_filter:
        query = query.filter(models.Equipment.status == status_filter.upper())
    return query.all()


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


@router.post("/", response_model=schemas.EquipmentResponse, status_code=status.HTTP_201_CREATED)
def create_equipment(item: schemas.EquipmentCreate, db: Session = Depends(get_db)):
    """
    Добавить новый инструмент в базу.
    Проверяет, чтобы инвентарный номер был уникальным.
    """
    # 1. Проверяем, нет ли уже инструмента с таким инвентарным номером
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
    db.commit()          # Записываем изменения в SQLite
    db.refresh(new_tool) # Считываем созданную запись (вместе со сгенерированным id)
    return new_tool


# =======================================================================
# ЗАДАЧИ ДЛЯ ПАРЫ 1 (Раскомментируйте и допишите логику):
# =======================================================================

# @router.put("/{equipment_id}", response_model=schemas.EquipmentResponse)
# def update_equipment(equipment_id: int, update_data: schemas.EquipmentUpdate, db: Session = Depends(get_db)):
#     """TODO: Пара 1 — Редактирование инструмента (название, тариф или статус)."""
#     pass

# @router.delete("/{equipment_id}", status_code=status.HTTP_204_NO_CONTENT)
# def delete_equipment(equipment_id: int, db: Session = Depends(get_db)):
#     """TODO: Пара 1 — Удаление инструмента из базы данных."""
#     pass
