"""
models.py — Таблицы базы данных (модели SQLAlchemy).
Каждый класс описывает одну таблицу в файле базы данных.
"""
from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey
from sqlalchemy.orm import relationship
from database import Base


class Equipment(Base):
    """
    Таблица оборудования (инструментов).
    Зона ответственности: Пара 1.
    """
    __tablename__ = "equipment"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)                        # Название (напр., 'Перфоратор Bosch 2-26')
    inventory_number = Column(String, unique=True, index=True)   # Инвентарный номер (уникальный код)
    daily_rate = Column(Float, nullable=False)                   # Стоимость за одни сутки аренды (в рублях)
    status = Column(String, default="AVAILABLE")                 # Статусы: 'AVAILABLE', 'RENTED', 'REPAIR'

    # Связь с арендами: один инструмент может иметь много записей об аренде
    rentals = relationship("Rental", back_populates="equipment")


class Client(Base):
    """
    Таблица клиентов.
    Зона ответственности: Пара 2.
    """
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, nullable=False)                   # ФИО клиента
    phone = Column(String, unique=True, index=True)              # Номер телефона (уникальный)

    # Связь с арендами: один клиент может оформлять много аренд
    rentals = relationship("Rental", back_populates="client")


class Rental(Base):
    """
    Таблица договоров аренды (факты выдачи оборудования клиенту).
    Зона ответственности: Пара 3.
    """
    __tablename__ = "rentals"

    id = Column(Integer, primary_key=True, index=True)
    equipment_id = Column(Integer, ForeignKey("equipment.id"), nullable=False)  # Ссылка на инструмент
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)        # Ссылка на клиента

    start_date = Column(Date, nullable=False)                    # Дата начала аренды
    end_date = Column(Date, nullable=False)                      # Дата окончания аренды
    total_cost = Column(Float, default=0.0)                      # Итоговая сумма заказа (руб.)
    status = Column(String, default="ACTIVE")                    # Статусы: 'ACTIVE' (на руках), 'RETURNED' (сдан)

    # Двусторонние связи для удобного обращения: rental.client и rental.equipment
    equipment = relationship("Equipment", back_populates="rentals")
    client = relationship("Client", back_populates="rentals")
