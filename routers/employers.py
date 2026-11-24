"""Учебная доработка модуля сотрудников для практических работ ЗПП."""
from typing import Literal
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy import func, or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from database import get_db
from auth import require_admin
from models import Employer
from employers_schemas import EmployerCreate, EmployerUpdate, EmployerStatus, EmployerResponse

router=APIRouter(prefix='/employers',tags=['Сотрудники / Менеджеры'],dependencies=[Depends(require_admin)])

def find_employer(db, employer_id):
    item=db.get(Employer,employer_id)
    if item is None:
        raise HTTPException(404,'Сотрудник не найден')
    return item

def save(db,item):
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409,'Логин сотрудника уже существует')
    db.refresh(item)
    return item

@router.get('/',response_model=list[EmployerResponse])
def get_all_employers(query: str=Query('',max_length=150),
    role: Literal['MANAGER','ADMIN'] | None=None,
    is_active: Literal['ACTIVE','BLOCKED'] | None=None,
    sort_by: Literal['id','username','full_name']='id',
    order: Literal['asc','desc']='asc', db: Session=Depends(get_db)):
    items=db.query(Employer).all()
    needle=query.strip().casefold()
    items=[item for item in items if (not needle or needle in item.full_name.casefold() or needle in item.username.casefold())
           and (role is None or item.role==role) and (is_active is None or item.is_active==is_active)]
    def key(item):
        value=getattr(item,sort_by)
        return (value.casefold() if isinstance(value,str) else value,item.id)
    return sorted(items,key=key,reverse=order=='desc')

@router.get('/search',response_model=list[EmployerResponse])
def search_employers(query: str=Query(...,min_length=1,max_length=150),db: Session=Depends(get_db)):
    if not query.strip():
        raise HTTPException(422,'Укажите строку поиска')
    return get_all_employers(query=query,role=None,is_active=None,sort_by='id',order='asc',db=db)

@router.get('/{employer_id}',response_model=EmployerResponse)
def get_employer_by_id(employer_id: int, db: Session=Depends(get_db)):
    return find_employer(db,employer_id)

@router.post('/',response_model=EmployerResponse,status_code=201)
def create_employer(item: EmployerCreate,db: Session=Depends(get_db)):
    existing=db.query(Employer).filter(func.lower(Employer.username)==item.username.lower()).first()
    if existing:
        raise HTTPException(409,'Логин сотрудника уже существует')
    employee=Employer(**item.model_dump(),is_active='ACTIVE')
    db.add(employee)
    return save(db,employee)

@router.put('/{employer_id}',response_model=EmployerResponse)
def update_employer(employer_id: int, changes: EmployerUpdate, db: Session=Depends(get_db)):
    item=find_employer(db,employer_id)
    for key,value in changes.model_dump(exclude_unset=True).items():
        setattr(item,key,value)
    return save(db,item)

@router.patch('/{employer_id}/status',response_model=EmployerResponse)
def set_employer_status(employer_id: int,changes: EmployerStatus,db: Session=Depends(get_db)):
    item=find_employer(db,employer_id)
    item.is_active=changes.is_active
    return save(db,item)

@router.delete('/{employer_id}',status_code=204)
def delete_employer(employer_id: int,db: Session=Depends(get_db)):
    item=find_employer(db,employer_id)
    if item.is_active!='BLOCKED':
        raise HTTPException(409,'Перед удалением заблокируйте карточку сотрудника')
    db.delete(item)
    db.commit()
    return Response(status_code=204)
