"""Создание первого администратора для новой установки."""
import secrets
from sqlalchemy import text
from database import SessionLocal
from auth import User, passwords
import models

def create_initial_admin():
    """Вернуть новые реквизиты один раз, сохранив существующих пользователей."""
    with SessionLocal() as db:
        # SQLite-проекты могут стартовать одновременно из нескольких процессов.
        if db.get_bind().dialect.name == "sqlite":
            db.execute(text("BEGIN IMMEDIATE"))
        if db.query(User).filter_by(role="ADMIN").first():
            return None
        username = "club_admin"
        if db.query(User).filter_by(username=username).first():
            username += "_" + secrets.token_hex(4)
        password = secrets.token_urlsafe(18)
        client = models.Client(
            full_name="Администратор клуба",
            phone="admin-" + secrets.token_hex(16),
        )
        db.add(client)
        db.flush()
        db.add(User(
            username=username,
            password_hash=passwords.hash(password),
            role="ADMIN",
            client_id=client.id,
        ))
        db.commit()
        return username, password
