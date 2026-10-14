"""
routers/employers.py — Эндпоинты для работы с сотрудниками и менеджерами.
Зона ответственности: Ветка feature/employers.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from database import get_db
import models
import schemas

router = APIRouter(prefix="/employers", tags=["Сотрудники / Менеджеры"])


@router.get("/", response_model=List[schemas.EmployerResponse])
def get_all_employers(db: Session = Depends(get_db)):
    """Получить список всех сотрудников/менеджеров."""
    return db.query(models.Employer).all()


@router.get("/{employer_id}", response_model=schemas.EmployerResponse)
def get_employer_by_id(employer_id: int, db: Session = Depends(get_db)):
    """Получить данные сотрудника по ID."""
    employer = db.query(models.Employer).filter(models.Employer.id == employer_id).first()
    if not employer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Сотрудник не найден"
        )
    return employer


@router.post("/", response_model=schemas.EmployerResponse, status_code=status.HTTP_201_CREATED)
def create_employer(item: schemas.EmployerCreate, db: Session = Depends(get_db)):
    """
    Добавить нового сотрудника (менеджера).
    Проверяет уникальность логина (username).
    """
    existing = db.query(models.Employer).filter(models.Employer.username == item.username).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Сотрудник с логином '{item.username}' уже существует!"
        )

    new_emp = models.Employer(
        username=item.username,
        full_name=item.full_name,
        role=item.role or "MANAGER",
        is_active="ACTIVE"
    )
    db.add(new_emp)
    db.commit()
    db.refresh(new_emp)
    return new_emp
