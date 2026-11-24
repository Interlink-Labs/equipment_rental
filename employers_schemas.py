"""Контракты модуля сотрудников без изменения схем других пар."""
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

class EmployerCreate(BaseModel):
    model_config = ConfigDict(extra='forbid')
    username: str = Field(min_length=3, max_length=64)
    full_name: str = Field(min_length=1, max_length=150)
    role: Literal['MANAGER','ADMIN'] = 'MANAGER'

    @field_validator('username','full_name', mode='before')
    @classmethod
    def trim_text(cls, value):
        return value.strip() if isinstance(value,str) else value

class EmployerUpdate(BaseModel):
    model_config = ConfigDict(extra='forbid')
    full_name: str | None = Field(default=None,min_length=1,max_length=150)
    role: Literal['MANAGER','ADMIN'] | None = None

    @field_validator('full_name',mode='before')
    @classmethod
    def trim_text(cls,value):
        return value.strip() if isinstance(value,str) else value

    @model_validator(mode='after')
    def require_change(self):
        if not self.model_fields_set or any(getattr(self,key) is None for key in self.model_fields_set):
            raise ValueError('Укажите непустые изменяемые поля')
        return self

class EmployerStatus(BaseModel):
    model_config = ConfigDict(extra='forbid')
    is_active: Literal['ACTIVE','BLOCKED']

class EmployerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    username: str
    full_name: str
    role: str
    is_active: str
