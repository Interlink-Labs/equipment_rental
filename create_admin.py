"""Назначить администратора существующему аккаунту на сервере."""
import argparse
from database import SessionLocal
from auth import User
import models

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("username")
    args = parser.parse_args()
    with SessionLocal() as db:
        user = db.query(User).filter_by(username=args.username).first()
        if user is None:
            parser.error("Сначала зарегистрируйте аккаунт")
        user.role = "ADMIN"
        db.commit()
        print("Администратор назначен")
