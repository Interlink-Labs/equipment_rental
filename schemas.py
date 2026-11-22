"""
schemas.py — Pydantic-схемы для валидации (проверки) данных.
Схемы определяют:
1. Какие поля обязательны при отправке запроса (Create).
2. В каком виде возвращается ответ клиенту (Response).
"""
from pydantic import BaseModel, ConfigDict
from datetime import date
from typing import Optional


# ==========================================
# 1. Схемы для Оборудования (Пара 1)
# ==========================================
class EquipmentBase(BaseModel):
    name: str
    inventory_number: str
    daily_rate: float


class EquipmentCreate(EquipmentBase):
    """Схема для создания нового оборудования (POST)."""
    pass


class EquipmentUpdate(BaseModel):
    """Схема для редактирования оборудования (PUT/PATCH). Все поля опциональны."""
    name: Optional[str] = None
    daily_rate: Optional[float] = None
    status: Optional[str] = None


class EquipmentResponse(EquipmentBase):
    """Схема ответа сервера с добавлением id и статуса."""
    id: int
    status: str

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# 2. Схемы для Клиентов (Пара 2)
# ==========================================
class ClientBase(BaseModel):
    full_name: str
    phone: str


class ClientCreate(ClientBase):
    """Схема для создания клиента (POST)."""
    pass


class ClientResponse(ClientBase):
    """Схема ответа сервера при выдаче данных клиента."""
    id: int

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# 3. Схемы для Сотрудников / Менеджеров (Employers)
# ==========================================
class EmployerBase(BaseModel):
    username: str
    full_name: str
    role: Optional[str] = "MANAGER"


class EmployerCreate(EmployerBase):
    """Схема создания сотрудника."""
    pass


class EmployerResponse(EmployerBase):
    """Схема ответа с данными сотрудника."""
    id: int
    is_active: str

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# 4. Схемы для Аренды (Пара 3)
# ==========================================
class RentalCreate(BaseModel):
    """Схема создания аренды: клиент указывает какой инструмент берет, свой ID и даты."""
    equipment_id: int
    client_id: int
    start_date: date
    end_date: date


class RentalResponse(RentalCreate):
    """Схема ответа сервера по договору аренды."""
    id: int
    total_cost: float
    status: str

    model_config = ConfigDict(from_attributes=True)


# Аренды: клиент обычного пользователя определяется из JWT.
class RentalBooking(RentalCreate):
    client_id: Optional[int] = None


# Пара клиентов — проверка новых данных, существующие записи читаются без изменений.
import re
from pydantic import Field, field_validator

def normalize_client_phone(value: str) -> str:
    digits = re.sub(r"[\s()+-]", "", value)
    if not re.fullmatch(r"[78]\d{10}", digits):
        raise ValueError("Введите российский телефон в формате +7-XXX-XXX-XX-XX")
    return f"+7-{digits[1:4]}-{digits[4:7]}-{digits[7:9]}-{digits[9:11]}"

class ClientUpdate(BaseModel):
    full_name: Optional[str] = Field(default=None, min_length=1, max_length=150)
    phone: Optional[str] = None

    @field_validator("full_name")
    @classmethod
    def validate_name(cls, value):
        if value is None or not value.strip():
            raise ValueError("Укажите ФИО")
        return value.strip()

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value):
        if value is None:
            raise ValueError("Укажите телефон")
        return normalize_client_phone(value)

class ClientCreateValidated(ClientUpdate):
    full_name: str
    phone: str
