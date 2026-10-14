"""
services.py — Бизнес-логика и расчетные формулы.
Здесь хранятся функции, которые выполняют математические расчеты и сложные проверки,
чтобы не раздувать код в роутерах.
"""
from datetime import date
from sqlalchemy.orm import Session
import models


def calculate_rental_price(daily_rate: float, start_date: date, end_date: date) -> float:
    """
    Рассчитывает общую стоимость аренды:
    Формула: (Количество дней) * (Тариф за сутки).
    Если оборудование берут и возвращают в один и тот же день — считается как 1 день.
    """
    days = (end_date - start_date).days
    if days <= 0:
        days = 1  # Минимальный срок аренды — 1 сутки
    return round(daily_rate * days, 2)


def is_equipment_available_for_dates(
    db: Session,
    equipment_id: int,
    start_date: date,
    end_date: date
) -> bool:
    """
    Проверяет, свободен ли инструмент на указанные даты.
    Инструмент занят, если существует активная аренда, даты которой пересекаются с нашими.

    Условие пересечения двух интервалов [A_start, A_end] и [B_start, B_end]:
    A_start <= B_end AND A_end >= B_start
    """
    overlapping_rental = db.query(models.Rental).filter(
        models.Rental.equipment_id == equipment_id,
        models.Rental.status == "ACTIVE",
        models.Rental.start_date <= end_date,
        models.Rental.end_date >= start_date
    ).first()

    # Если пересечений не найдено, инструмент свободен (True)
    return overlapping_rental is None
