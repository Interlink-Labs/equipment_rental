"""Проверка авторизации и полного цикла аренды на временной БД."""
import os
import tempfile
from datetime import date, datetime, timedelta, timezone
from concurrent.futures import ThreadPoolExecutor
import jwt
from fastapi.testclient import TestClient

original = os.getcwd()
with tempfile.TemporaryDirectory() as directory:
    os.chdir(directory)
    from main import app
    from database import engine, SessionLocal
    from auth import User, secret_key
    try:
        with TestClient(app) as c:
            def register(name):
                data = {"username": name, "password": "strong-pass-123", "full_name": name, "phone": "12345-" + name}
                response = c.post("/auth/registration", json=data)
                assert response.status_code == 201, response.text
                login = c.post("/auth/login", json={"username": name, "password": data["password"]})
                assert login.status_code == 200, login.text
                return response.json(), {"Authorization": "Bearer " + login.json()["access_token"]}

            admin, ah = register("admin")
            alice, uh = register("alice")
            bob, bh = register("bobby")
            with SessionLocal() as db:
                user = db.get(User, admin["id"])
                assert user.password_hash != "strong-pass-123"
                user.role = "ADMIN"
                db.commit()
            assert c.post("/auth/registration", json={"username": "elevate", "password": "strong-pass", "full_name": "X", "phone": "123456", "role": "ADMIN"}).status_code == 422
            assert c.post("/auth/login", json={"username": "alice", "password": "wrong"}).status_code == 401
            assert c.get("/rentals/").status_code == 401
            assert c.get("/clients/", headers=uh).status_code == 403
            assert c.get("/employers/", headers=uh).status_code == 403
            expired = jwt.encode({"sub": str(alice["id"]), "iat": datetime.now(timezone.utc)-timedelta(hours=2), "exp": datetime.now(timezone.utc)-timedelta(hours=1)}, secret_key(), algorithm="HS256")
            assert c.get("/rentals/", headers={"Authorization": "Bearer " + expired}).status_code == 401
            assert c.get("/rentals/", headers={"Authorization": "Bearer altered"}).status_code == 401
            pc = c.post("/equipment/", headers=ah, json={"name": "PC", "inventory_number": "test", "daily_rate": 500})
            assert pc.status_code == 201, pc.text
            eid = pc.json()["id"]
            assert c.put(f"/equipment/{eid}", headers=uh, json={"daily_rate": 1}).status_code == 403
            data = dict(client_id=bob["client_id"], equipment_id=eid, start_date=str(date.today()), end_date=str(date.today()))
            # Simultaneous bookings for the same dates cannot both succeed.
            def book(_):
                return c.post("/rentals/book", json=data, headers=uh)
            with ThreadPoolExecutor(2) as pool:
                results = list(pool.map(book, range(2)))
            assert sorted(r.status_code for r in results) == [201, 400], [r.text for r in results]
            booking = next(r.json() for r in results if r.status_code == 201)
            assert booking["client_id"] == alice["client_id"]
            rid = booking["id"]
            assert len(c.get("/rentals/", headers=uh).json()) == 1
            assert c.get("/rentals/", headers=bh).json() == []
            assert c.get(f"/rentals/{rid}", headers=bh).status_code == 404
            assert c.get(f"/rentals/{rid}", headers=uh).status_code == 200
            assert c.get(f"/rentals/{rid}", headers=ah).status_code == 200
            for action in ("issue", "return"):
                assert c.post(f"/rentals/{rid}/{action}", headers=uh).status_code == 403
            assert c.post("/rentals/", json=data, headers=uh).status_code == 403
            assert c.post(f"/rentals/{rid}/issue", headers=ah).status_code == 200
            assert c.post(f"/rentals/{rid}/issue", headers=ah).status_code == 200
            assert c.get(f"/equipment/{eid}").json()["status"] == "RENTED"
            assert c.post(f"/rentals/{rid}/return", headers=ah).status_code == 200
            assert c.post(f"/rentals/{rid}/return", headers=ah).status_code == 200
            assert c.get(f"/equipment/{eid}").json()["status"] == "AVAILABLE"
            assert len(c.get("/rentals/?status_filter=RETURNED", headers=uh).json()) == 1
            assert c.get("/rentals/?status_filter=ACTIVE", headers=uh).json() == []
            assert c.get("/rentals/?date_from=2030-12-01&date_to=2030-01-01", headers=uh).status_code == 422
            assert c.post(f"/rentals/{rid}/issue", headers=ah).status_code == 409
            assert c.post("/rentals/999/issue", headers=ah).status_code == 404
            assert c.get("/static/auth-session.js").status_code == 200
    finally:
        engine.dispose()
        os.chdir(original)
print("PASS: JWT, ownership, roles, concurrent booking, filters, issue and return")
