from pydantic import BaseModel, ConfigDict, EmailStr


class ClientCreate(BaseModel):
    name: str
    phone: str
    email: EmailStr | None = None


class ClientUpdate(BaseModel):
    name: str | None = None
    phone: str | None = None
    email: EmailStr | None = None


class ClientResponse(BaseModel):
    id: int
    name: str
    phone: str
    email: str | None

    model_config = ConfigDict(from_attributes=True)