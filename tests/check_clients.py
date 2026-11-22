"""Регрессионная проверка модуля клиентов во временной базе."""
import os, tempfile
from datetime import date
from concurrent.futures import ThreadPoolExecutor
from fastapi.testclient import TestClient

original = os.getcwd()
with tempfile.TemporaryDirectory() as folder:
    os.chdir(folder)
    from main import app
    from database import SessionLocal, engine
    from auth import User
    import models
    try:
        with TestClient(app) as c:
            data = dict(username="testadmin", password="safe-password", full_name="Admin", phone="+7-900-000-00-00")
            account = c.post("/auth/registration", json=data).json()
            token = c.post("/auth/login", json={"username":data["username"], "password":data["password"]}).json()["access_token"]
            headers = {"Authorization":"Bearer "+token}
            assert c.get("/clients/", headers=headers).status_code == 403
            assert c.get("/clients/").status_code == 401
            with SessionLocal() as db:
                db.get(User,account["id"]).role="ADMIN"
                db.add(models.Client(full_name="Старая запись",phone="89991234567"))
                db.commit()
            assert c.post("/clients/",headers=headers,json={"full_name":"Duplicate","phone":"+7-999-123-45-67"}).status_code == 409
            created=c.post("/clients/",headers=headers,json={"full_name":"  Анна Иванова  ","phone":"8 (901) 111-22-33"})
            assert created.status_code==201,created.text
            client=created.json()
            assert client["full_name"]=="Анна Иванова" and client["phone"]=="+7-901-111-22-33"
            cid=client["id"]
            assert len(c.get("/clients/search?query=иванова",headers=headers).json())==1
            assert len(c.get("/clients/?query=9011112233&sort=name",headers=headers).json())==1
            assert c.put(f"/clients/{cid}",headers=headers,json={"full_name":"Анна Петрова"}).json()["full_name"]=="Анна Петрова"
            assert c.put(f"/clients/{cid}",headers=headers,json={"phone":None}).status_code==422
            assert c.put(f"/clients/{cid}",headers=headers,json={"full_name":" "}).status_code==422
            assert c.post("/clients/",headers=headers,json={"full_name":"Bad","phone":"123"}).status_code==422
            assert c.delete(f"/clients/{account['client_id']}",headers=headers).status_code==409
            pc=c.post("/equipment/",headers=headers,json={"name":"PC","inventory_number":"TEST","daily_rate":500}).json()
            rental=c.post("/rentals/",headers=headers,json=dict(client_id=cid,equipment_id=pc["id"],start_date=str(date.today()),end_date=str(date.today())))
            assert rental.status_code==201,rental.text
            assert c.delete(f"/clients/{cid}",headers=headers).status_code==409
            def duplicate(_):
                return c.post("/clients/",headers=headers,json={"full_name":"Race","phone":"+7-902-000-00-01"}).status_code
            with ThreadPoolExecutor(2) as pool:
                assert sorted(pool.map(duplicate,range(2)))==[201,409]
            spare=c.post("/clients/",headers=headers,json={"full_name":"Удалить","phone":"+7-903-000-00-01"}).json()
            assert c.delete(f"/clients/{spare['id']}",headers=headers).status_code==204
            assert c.get(f"/clients/{spare['id']}",headers=headers).status_code==404
            assert c.delete("/clients/99999",headers=headers).status_code==404
            assert c.get("/static/client-actions.js").status_code==200
    finally:
        engine.dispose()
        os.chdir(original)
print("PASS: client CRUD, search, phones, permissions, references and concurrent duplicates")
