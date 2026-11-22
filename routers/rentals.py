"""
routers/rentals.py — Эндпоинты для оформления, возврата и просмотра аренд.
Зона ответственности: Пара 3 (ветка feature/rentals).
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Literal, Optional
from datetime import date
from sqlalchemy import text

from database import get_db
import models
import schemas
import services

router = APIRouter(prefix="/rentals", tags=["Аренды"])



def lock_rental_write(db: Session):
    """Сериализовать проверки и запись аренды в SQLite."""
    if db.get_bind().dialect.name == "sqlite":
        db.execute(text("BEGIN IMMEDIATE"))

@router.get("/", response_model=List[schemas.RentalResponse])
def get_all_rentals(
    status_filter: Optional[Literal["ACTIVE", "RESERVED", "RETURNED"]] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    db: Session = Depends(get_db),
):
    """Получить список всех аренд."""
    if date_from and date_to and date_from > date_to:
        raise HTTPException(422, "Начало периода не может быть позже окончания")
    query = db.query(models.Rental)
    if status_filter:
        query = query.filter(models.Rental.status == status_filter)
    if date_from:
        query = query.filter(models.Rental.end_date >= date_from)
    if date_to:
        query = query.filter(models.Rental.start_date <= date_to)
    return query.order_by(models.Rental.id.desc()).all()


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
    lock_rental_write(db)
    # 1. Проверяем инструмент
    tool = db.query(models.Equipment).filter(models.Equipment.id == rental_data.equipment_id).first()
    if not tool:
        raise HTTPException(status_code=404, detail="Инструмент не найден")

    if tool.status == "REPAIR":
        raise HTTPException(409, "Оборудование находится в ремонте")

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

    if tool.status == "RENTED":
        raise HTTPException(409, "Оборудование ещё не возвращено")

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
    lock_rental_write(db)
    # 1. Проверяем инструмент
    tool = db.query(models.Equipment).filter(models.Equipment.id == booking_data.equipment_id).first()
    if not tool:
        raise HTTPException(status_code=404, detail="Инструмент не найден")

    if tool.status == "REPAIR":
        raise HTTPException(409, "Оборудование находится в ремонте")

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

@router.post("/{rental_id}/return", response_model=schemas.RentalResponse)
def return_equipment(rental_id: int, db: Session = Depends(get_db)):
    """Закрыть активную аренду и обновить статус оборудования."""
    lock_rental_write(db)
    updated = db.query(models.Rental).filter_by(id=rental_id, status="ACTIVE").update(
        {"status": "RETURNED"}
    )
    rental = db.get(models.Rental, rental_id)
    if rental is None:
        raise HTTPException(404, "Аренда не найдена")
    if not updated and rental.status != "RETURNED":
        raise HTTPException(409, "Вернуть можно только оборудование из активной аренды")

    if updated:
        other_active = db.query(models.Rental).filter_by(
            equipment_id=rental.equipment_id, status="ACTIVE"
        ).first()
        if other_active is None and rental.equipment.status == "RENTED":
            rental.equipment.status = "AVAILABLE"
        db.commit()
        db.refresh(rental)
    return rental


@router.post("/{rental_id}/issue", response_model=schemas.RentalResponse)
def issue_booking(rental_id: int, db: Session = Depends(get_db)):
    """Выдать оборудование по существующей брони."""
    lock_rental_write(db)
    rental = db.get(models.Rental, rental_id)
    if rental is None:
        raise HTTPException(404, "Аренда не найдена")
    if rental.status == "ACTIVE":
        return rental
    if rental.status != "RESERVED":
        raise HTTPException(409, "Выдать можно только забронированное оборудование")
    if not rental.start_date <= date.today() <= rental.end_date:
        raise HTTPException(409, "Выдача возможна только в период брони")
    if rental.equipment.status != "AVAILABLE":
        raise HTTPException(409, "Оборудование недоступно для выдачи")
    if db.query(models.Rental).filter(
        models.Rental.equipment_id == rental.equipment_id,
        models.Rental.id != rental.id,
        models.Rental.status == "ACTIVE",
    ).first():
        raise HTTPException(409, "Оборудование ещё не возвращено")
    rental.status = "ACTIVE"
    rental.equipment.status = "RENTED"
    db.commit()
    db.refresh(rental)
    return rental