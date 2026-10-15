from fastapi import Depends, FastAPI, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from database import Base, SessionLocal, engine
from models import Client
from schemas import ClientCreate, ClientResponse, ClientUpdate

Base.metadata.create_all(bind=engine)

app = FastAPI(title="API управления клиентами")
API_PREFIX = "/api/v1"


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_client_or_404(client_id: int, db: Session) -> Client:
    client = db.query(Client).filter(Client.id == client_id).first()
    if client is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Клиент не найден",
        )
    return client


@app.get("/")
def home():
    return {"message": "API работает", "clients": f"{API_PREFIX}/clients"}


@app.post(
    f"{API_PREFIX}/clients",
    response_model=ClientResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_client(data: ClientCreate, db: Session = Depends(get_db)):
    if db.query(Client).filter(Client.phone == data.phone).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Клиент с таким телефоном уже существует",
        )

    if data.email and db.query(Client).filter(Client.email == data.email).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Клиент с таким email уже существует",
        )

    client = Client(**data.model_dump())
    db.add(client)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Клиент с таким телефоном или email уже существует",
        )

    db.refresh(client)
    return client


@app.get(f"{API_PREFIX}/clients", response_model=list[ClientResponse])
def get_clients(db: Session = Depends(get_db)):
    return db.query(Client).order_by(Client.id).all()


@app.get(
    f"{API_PREFIX}/clients/{{client_id}}",
    response_model=ClientResponse,
)
def get_client(client_id: int, db: Session = Depends(get_db)):
    return get_client_or_404(client_id, db)


@app.put(
    f"{API_PREFIX}/clients/{{client_id}}",
    response_model=ClientResponse,
)
def update_client(
    client_id: int,
    data: ClientUpdate,
    db: Session = Depends(get_db),
):
    client = get_client_or_404(client_id, db)
    changes = data.model_dump(exclude_unset=True)

    if "phone" in changes and changes["phone"] is not None:
        duplicate = (
            db.query(Client)
            .filter(Client.phone == changes["phone"], Client.id != client_id)
            .first()
        )
        if duplicate:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Клиент с таким телефоном уже существует",
            )

    if "email" in changes and changes["email"] is not None:
        duplicate = (
            db.query(Client)
            .filter(Client.email == changes["email"], Client.id != client_id)
            .first()
        )
        if duplicate:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Клиент с таким email уже существует",
            )

    for field, value in changes.items():
        setattr(client, field, value)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Клиент с таким телефоном или email уже существует",
        )

    db.refresh(client)
    return client


@app.delete(f"{API_PREFIX}/clients/{{client_id}}")
def delete_client(client_id: int, db: Session = Depends(get_db)):
    client = get_client_or_404(client_id, db)

    db.delete(client)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Невозможно удалить клиента: с ним связаны другие записи",
        )

    return {"message": "Клиент удалён"}