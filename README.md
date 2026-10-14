# 🛠️ Equipment Rental — Система учета аренды оборудования

Простой и понятный учебный проект для команды из 8 разработчиков.
Проект на GitHub Projects: [Interlink-Labs / equipment_rental](https://github.com/orgs/Interlink-Labs/projects/6)

- **Backend:** Python + FastAPI
- **База данных:** SQLite (хранится в одном локальном файле `equipment_rental.db`)
- **ORM:** SQLAlchemy 2.0
- **Frontend:** Чистый HTML5 + CSS3 + Vanilla JavaScript
- **API Документация:** Swagger UI (доступна из коробки!)

---

## 🚀 Пошаговая инструкция по запуску на компьютере

### Шаг 1. Откройте терминал в папке проекта
Если вы в VS Code: нажмите в верхнем меню `Терминал -> Новый терминал` (`Ctrl + ~`).

### Шаг 2. Создайте виртуальное окружение Python (1 раз)
```bash
python -m venv venv
```

### Шаг 3. Активируйте виртуальное окружение
- **Windows (PowerShell):**
  ```powershell
  venv\Scripts\Activate.ps1
  ```
  *(Если ругается на политики выполнения: запустите `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` и повторите).*
- **Windows (CMD):**
  ```cmd
  venv\Scripts\activate.bat
  ```
- **macOS / Linux:**
  ```bash
  source venv/bin/activate
  ```
*(Слева в строке терминала появится зеленая надпись `(venv)` — значит, окружение активно).*

### Шаг 4. Установите библиотеки
```bash
pip install -r requirements.txt
```

### Шаг 5. Запустите сервер
```bash
uvicorn main:app --reload
```

---

## 🌐 Где посмотреть результат?

После запуска перейдите по ссылкам в браузере:
1. **Веб-интерфейс приложения:** [http://127.0.0.1:8000](http://127.0.0.1:8000)
2. **Интерактивная панель Swagger (API Docs):** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
   *(Здесь можно нажимать кнопки `Try it out` и тестировать любые эндпоинты без написания фронтенда!)*

---

## 📁 Структура папок

```text
equipment_rental/
├── main.py              # Запуск FastAPI приложения и объединение маршрутов
├── database.py          # Подключение к файлу SQLite
├── models.py            # Модели таблиц базы данных (Equipment, Client, Rental)
├── schemas.py           # Pydantic схемы валидации
├── services.py          # Бизнес-логика (расчет цен, проверка дат)
├── routers/             # Роутеры по парам
│   ├── equipment.py     # Зона ответственности Пары 1
│   ├── clients.py       # Зона ответственности Пары 2
│   ├── rentals.py       # Зона ответственности Пары 3
│   └── employers.py     # Модуль сотрудников и менеджеров (feature/employers)
├── templates/
│   └── index.html       # HTML интерфейс
├── static/
│   ├── style.css        # Стили
│   └── app.js           # Логика фронтенда (Пара 4)
├── requirements.txt     # Зависимости
├── CONTRIBUTING.md      # Правила работы с Git для пар
└── README.md            # Данная инструкция
```
