"""
database.py — Настройка подключения к базе данных SQLite с помощью SQLAlchemy.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Адрес базы данных: локальный файл renttool.db в корне проекта
SQLALCHEMY_DATABASE_URL = "sqlite:///./renttool.db"

# Движок базы данных
# check_same_thread=False обязателен для работы SQLite в многопоточном режиме FastAPI
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}
)

# Фабрика сессий. Сессия — это сеанс связи с базой данных (открыли -> сделали запрос -> закрыли)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Базовый класс для всех моделей таблиц
Base = declarative_base()


def get_db():
    """
    Генератор зависимости (Dependency) для FastAPI.
    Выдает сессию базы данных на время выполнения HTTP-запроса и гарантированно закрывает ее после.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
