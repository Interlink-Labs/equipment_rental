
# Точка входа: создаём приложение, подключаем роутеры
from fastapi import FastAPI

app = FastAPI(title="Мой проект")

@app.get("/")
async def home():
    return {"message": "API работает"}

@app.get("/items/{item_id}")
async def get_item(item_id: int):
    return {"item_id": item_id}