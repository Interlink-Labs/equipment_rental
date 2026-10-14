"""
main.py — Главная точка входа в приложение Equipment Rental.
Запускает веб-сервер, подключает базу данных и объединяет все маршруты (роутеры).
"""
import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from database import engine, Base
from routers import equipment, clients, rentals, employers

# Автоматически создаем таблицы в файле базы данных SQLite при старте приложения, если их еще нет
Base.metadata.create_all(bind=engine)

# Инициализируем приложение FastAPI
app = FastAPI(
    title="Equipment Rental API 🛠️",
    description="Учебная система учета аренды оборудования и инструментов",
    version="1.0.0"
)

# Подключаем роутеры по направлениям
app.include_router(equipment.router)
app.include_router(clients.router)
app.include_router(rentals.router)
app.include_router(employers.router)

# Подключаем папку со статическими файлами (стили CSS и скрипты JS)
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")


# Главная страница сайта
@app.get("/", tags=["Главная"])
def read_root():
    """
    Отдает HTML-страницу index.html для браузера.
    Если файла нет — отдает приветственное сообщение со ссылкой на Swagger.
    """
    template_path = os.path.join(os.path.dirname(__file__), "templates", "index.html")
    if os.path.exists(template_path):
        return FileResponse(template_path)
    return {
        "message": "Сервер Equipment Rental работает!",
        "docs": "Откройте http://127.0.0.1:8000/docs для интерактивного тестирования API"
    }
