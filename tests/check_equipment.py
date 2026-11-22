"""Проверка оборудования на временной базе без изменения рабочих данных."""
import os, tempfile
from datetime import date
from concurrent.futures import ThreadPoolExecutor
from fastapi.testclient import TestClient

original = os.getcwd()
with tempfile.TemporaryDirectory() as folder:
    os.chdir(folder)
    from main import app
    from database import engine, SessionLocal
    from auth import User
    try:
        with TestClient(app) as c:
            def account(name):
                data = dict(username=name,password="safe-password",full_name=name,phone="+7-900-000-"+("00-01" if name=="admin" else "00-02"))
                user=c.post("/auth/registration",json=data).json()
                token=c.post("/auth/login",json={"username":name,"password":data["password"]}).json()["access_token"]
                return user,{"Authorization":"Bearer "+token}
            admin,ah=account("admin")
            user,uh=account("viewer")
            with SessionLocal() as db:
                db.get(User,admin["id"]).role="ADMIN"
                db.commit()
            assert c.get("/equipment/").status_code==200
            data={"name":"  Монитор 144 Гц ","inventory_number":" INV-01 ","daily_rate":500}
            assert c.post("/equipment/",json=data).status_code==401
            assert c.post("/equipment/",headers=uh,json=data).status_code==403
            pc=c.post("/equipment/",headers=ah,json=data)
            assert pc.status_code==201,pc.text
            pc=pc.json();eid=pc["id"]
            assert pc["name"]=="Монитор 144 Гц" and pc["inventory_number"]=="INV-01"
            assert c.post("/equipment/",headers=ah,json=data).status_code in (400,409)
            for field,value in (("name"," "),("inventory_number"," "),("daily_rate",0),("daily_rate",-5)):
                invalid={**data,field:value}
                assert c.post("/equipment/",headers=ah,json=invalid).status_code==422
            second=c.post("/equipment/",headers=ah,json=dict(name="Клавиатура",inventory_number="INV-02",daily_rate=100)).json()
            assert len(c.get("/equipment/?query=МОНИТОР").json())==1
            assert len(c.get("/equipment/?query=inv-01").json())==1
            assert c.get("/equipment/?sort=price_asc").json()[0]["id"]==second["id"]
            assert c.get("/equipment/?sort=price_desc").json()[0]["id"]==eid
            assert c.get("/equipment/?sort=unknown").status_code==422
            assert c.get("/equipment/?status_filter=broken").status_code==422
            for method in ("put","delete"):
                kwargs={"json":{"name":"Hacked"}} if method=="put" else {}
                assert getattr(c,method)(f"/equipment/{eid}",headers=uh,**kwargs).status_code==403
            assert c.put(f"/equipment/{eid}",headers=ah,json={"name":"Экран","daily_rate":600,"status":"REPAIR"}).status_code==200
            assert c.get("/equipment/?status_filter=repair").json()[0]["id"]==eid
            assert c.put(f"/equipment/{eid}",headers=ah,json={"status":"AVAILABLE"}).status_code==200
            rental=c.post("/rentals/",headers=ah,json=dict(client_id=user["client_id"],equipment_id=eid,start_date=str(date.today()),end_date=str(date.today())))
            assert rental.status_code==201,rental.text
            assert c.put(f"/equipment/{eid}",headers=ah,json={"status":"REPAIR"}).status_code==409
            assert c.delete(f"/equipment/{eid}",headers=ah).status_code==409
            c.post(f"/rentals/{rental.json()['id']}/return",headers=ah)
            assert c.delete(f"/equipment/{eid}",headers=ah).status_code==409
            assert c.delete(f"/equipment/{second['id']}",headers=ah).status_code==204
            assert c.get(f"/equipment/{second['id']}").status_code==404
            def race(_):
                return c.post("/equipment/",headers=ah,json=dict(name="Race",inventory_number="RACE",daily_rate=100)).status_code
            with ThreadPoolExecutor(2) as pool:
                assert sorted(pool.map(race,range(2)))==[201,400]
            assert "equipment-sort" in c.get("/").text
    finally:
        engine.dispose()
        os.chdir(original)
print("PASS: equipment CRUD, prices, search, filters, JWT, duplicates and rental history")
