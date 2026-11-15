<div align="center">

# Equipment Rental

**Аренда оборудования для разработки**

Каталог ноутбуков, рабочих станций и плат для программирования и тестирования.

![Python](https://img.shields.io/badge/Python-29352F?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-38594A?style=for-the-badge&logo=fastapi&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-394852?style=for-the-badge&logo=sqlite&logoColor=white)
![JavaScript](https://img.shields.io/badge/JavaScript-5E5034?style=for-the-badge&logo=javascript&logoColor=white)

[Быстрый запуск](#быстрый-запуск) · [Структура проекта](#структура-проекта) · [Правила работы](./CONTRIBUTING.md) · [Доска команды](https://github.com/orgs/Interlink-Labs/projects/6)

</div>

---

## Возможности

| Раздел | Что в нём |
| --- | --- |
| **Оборудование** | Каталог с дневными тарифами и инвентарными номерами |
| **Клиенты** | Карточки клиентов с контактными данными |
| **Аренды** | Оформление аренды и брони, расчёт стоимости по датам |
| **Сотрудники** | Учёт сотрудников и их ролей |

В браузере доступен каталог оборудования. Маршруты всех разделов собраны в Swagger.

## Быстрый запуск

Откройте терминал в папке проекта и создайте виртуальное окружение.

```bash
python -m venv venv
```

Активируйте его командой для своей системы.

| Терминал | Команда |
| --- | --- |
| Windows PowerShell | `venv\Scripts\Activate.ps1` |
| Windows CMD | `venv\Scripts\activate.bat` |
| macOS / Linux | `source venv/bin/activate` |

Установите зависимости и запустите сервер.

```bash
python -m pip install -r requirements.txt
python main.py
```

[Открыть каталог](http://127.0.0.1:8000/) · [Открыть Swagger](http://127.0.0.1:8000/docs)

## Структура проекта

| Файлы | Назначение |
| --- | --- |
| [`main.py`](./main.py) | Запуск FastAPI и подключение маршрутов |
| [`database.py`](./database.py), [`models.py`](./models.py) | Подключение SQLite и модели таблиц |
| [`schemas.py`](./schemas.py) | Проверка входных данных и схемы ответов |
| [`services.py`](./services.py) | Расчёт стоимости и проверка дат |
| [`routers/`](./routers/) | Маршруты API по разделам |
| [`templates/`](./templates/), [`static/`](./static/) | Разметка, стили и JavaScript |

![Equipment Rental — аренда IT-оборудования](./assets/equipment-rental-banner.png)

---

<div align="center">
  <sub>Учебный проект команды Interlink Labs · 2026</sub>
</div>
