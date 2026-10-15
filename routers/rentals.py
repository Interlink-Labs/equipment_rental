"""
routers/rentals.py — Эндпоинты для оформления, возврата и просмотра аренд.
Зона ответственности: Пара 3 (ветка feature/rentals).
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import date

from database import get_db
import models
import schemas
import services

router = APIRouter(prefix="/rentals", tags=["Аренды"])


@router.get("/", response_model=List[schemas.RentalResponse])
def get_all_rentals(db: Session = Depends(get_db)):
    """Получить список всех аренд."""
    return db.query(models.Rental).all()


@router.post("/", response_model=schemas.RentalResponse, status_code=status.HTTP_201_CREATED)
def create_rental(rental_data: schemas.RentalCreate, db: Session = Depends(get_db)):
    """
    Оформить аренду инструмента.
    Логика:
    1. Проверить существование клиента и инструмента.
    2. Проверить даты (дата начала <= дата окончания).
    3. Проверить, свободен ли инструмент (функция из services.py).
    4. Рассчитать стоимость аренды (функция из services.py).
    5. Создать запись аренды и обновить статус инструмента на 'RENTED'.
    """
    # 1. Проверяем инструмент
    tool = db.query(models.Equipment).filter(models.Equipment.id == rental_data.equipment_id).first()
    if not tool:
        raise HTTPException(status_code=404, detail="Инструмент не найден")

    # 2. Проверяем клиента
    client = db.query(models.Client).filter(models.Client.id == rental_data.client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Клиент не найден")

    # 3. Проверка дат
    if rental_data.start_date > rental_data.end_date:
        raise HTTPException(status_code=400, detail="Дата начала не может быть позже даты окончания!")

    # 4. Проверяем доступность через services.py
    if not services.is_equipment_available_for_dates(db, tool.id, rental_data.start_date, rental_data.end_date):
        raise HTTPException(status_code=400, detail="Инструмент уже занят на эти даты!")

    # 5. Расчет стоимости
    price = services.calculate_rental_price(tool.daily_rate, rental_data.start_date, rental_data.end_date)

    # 6. Создаем запись аренды
    new_rental = models.Rental(
        equipment_id=rental_data.equipment_id,
        client_id=rental_data.client_id,
        start_date=rental_data.start_date,
        end_date=rental_data.end_date,
        total_cost=price,
        status="ACTIVE"
    )
    tool.status = "RENTED"  # Меняем статус инструмента на 'В аренде'

    db.add(new_rental)
    db.commit()
    db.refresh(new_rental)
    return new_rental


# =======================================================================
# СОЗДАНИЕ БРОНИ
# =======================================================================

@router.post("/book", response_model=schemas.RentalResponse, status_code=status.HTTP_201_CREATED)
def create_booking(booking_data: schemas.RentalCreate, db: Session = Depends(get_db)):
    """
    Оформить бронь инструмента на будущие даты.
    Отличие от аренды: инструмент не выдаётся сразу, статус инструмента
    не меняется на 'RENTED', а сама бронь получает статус 'RESERVED'.

    Логика:
    1. Проверить существование клиента и инструмента.
    2. Проверить корректность дат (start_date <= end_date).
    3. Проверить, что дата начала — в будущем (иначе это уже аренда).
    4. Проверить доступность инструмента на выбранные даты.
    5. Рассчитать стоимость.
    6. Создать запись брони со статусом 'RESERVED'.
    """
    # 1. Проверяем инструмент
    tool = db.query(models.Equipment).filter(models.Equipment.id == booking_data.equipment_id).first()
    if not tool:
        raise HTTPException(status_code=404, detail="Инструмент не найден")

    # 2. Проверяем клиента
    client = db.query(models.Client).filter(models.Client.id == booking_data.client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Клиент не найден")

    # 3. Проверка корректности дат
    if booking_data.start_date > booking_data.end_date:
        raise HTTPException(status_code=400, detail="Дата начала не может быть позже даты окончания!")

    # 4. Бронь имеет смысл только на будущие даты
    if booking_data.start_date < date.today():
        raise HTTPException(
            status_code=400,
            detail="Дата начала брони не может быть в прошлом. Для текущей аренды используйте POST /rentals/"
        )

    # 5. Проверяем доступность инструмента на выбранные даты
    if not services.is_equipment_available_for_dates(
        db, tool.id, booking_data.start_date, booking_data.end_date
    ):
        raise HTTPException(status_code=400, detail="Инструмент уже занят или забронирован на эти даты!")

    # 6. Расчет стоимости
    price = services.calculate_rental_price(
        tool.daily_rate, booking_data.start_date, booking_data.end_date
    )

    # 7. Создаём бронь (статус инструмента НЕ меняем — он остаётся доступным
    #    для других броней на непересекающиеся даты)
    new_booking = models.Rental(
        equipment_id=booking_data.equipment_id,
        client_id=booking_data.client_id,
        start_date=booking_data.start_date,
        end_date=booking_data.end_date,
        total_cost=price,
        status="RESERVED"
    )

    db.add(new_booking)
    db.commit()
    db.refresh(new_booking)
    return new_booking


# =======================================================================
# ЗАДАЧИ ДЛЯ ПАРЫ 3 (Допишите ручки):
# =======================================================================

# @router.post("/{rental_id}/return", response_model=schemas.RentalResponse)
# def return_equipment(rental_id: int, db: Session = Depends(get_db)):
#     """
#     TODO: Пара 3 — Возврат оборудования.
#     1. Найти аренду по rental_id.
#     2. Перевести статус аренды в 'RETURNED'.
#     3. Найти связанный инструмент и вернуть ему статус 'AVAILABLE'.
#     """
#     pass