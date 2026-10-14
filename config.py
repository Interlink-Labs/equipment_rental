# Настройки (DB URL, секреты)
import os

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./equipment_rental.db",
)