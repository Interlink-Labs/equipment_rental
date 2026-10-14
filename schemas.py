from pydantic import BaseModel, ConfigDict, EmailStr


class ClientCreate(BaseModel):
    username: str
    firstName: str
    lastName: str
    email: EmailStr
    password: str
    phone: str


class ClientUpdate(BaseModel):
    username: str
    firstName: str
    lastName: str
    email: EmailStr
    password: str
    phone: str


class ClientRead(BaseModel):
    id: int
    username: str
    firstName: str
    lastName: str
    email: EmailStr
    phone: str

    model_config = ConfigDict(from_attributes)
