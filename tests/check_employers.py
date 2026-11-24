"""Проверки выполняются только во временной базе данных."""
import os,sys,tempfile,json
from pathlib import Path
base=Path(__file__).resolve().parent
project=base/'project' if (base/'project').exists() else base.parent
sys.path.insert(0,str(project))
os.environ['JWT_SECRET']='only-for-local-automated-tests-2026'
from fastapi.testclient import TestClient
logs=[]
def check(label,response,status):
    assert response.status_code==status,(label,response.status_code,response.text)
    logs.append(f'PASS | {label} | HTTP {status}')
    return response
with tempfile.TemporaryDirectory() as temp:
    old=os.getcwd();os.chdir(temp)
    from main import app
    from database import SessionLocal,engine
    from auth import User,create_token
    import models
    with SessionLocal() as db:
        client=models.Client(full_name='Тестовый администратор',phone='+7-900-000-00-01')
        db.add(client);db.flush()
        admin=User(username='testadmin',password_hash='unused',role='ADMIN',client_id=client.id)
        db.add(admin);db.commit();db.refresh(admin)
        admin_header={'Authorization':'Bearer '+create_token(admin)}
        client2=models.Client(full_name='Тестовый пользователь',phone='+7-900-000-00-02')
        db.add(client2);db.flush()
        user=User(username='testuser',password_hash='unused',role='USER',client_id=client2.id)
        db.add(user);db.commit();db.refresh(user)
        user_header={'Authorization':'Bearer '+create_token(user)}
    try:
        with TestClient(app) as c:
            check('без токена',c.get('/employers/'),401)
            check('роль USER',c.get('/employers/',headers=user_header),403)
            check('поддельный токен',c.get('/employers/',headers={'Authorization':'Bearer fake'}),401)
            def req(method,url,**kwargs):return getattr(c,method)(url,headers=admin_header,**kwargs)
            a=check('создание сотрудника',req('post','/employers/',json={'username':'manager1','full_name':'  Анна Иванова  '}),201).json()
            assert a['full_name']=='Анна Иванова' and a['is_active']=='ACTIVE'
            b=check('создание администратора карточки',req('post','/employers/',json={'username':'manager2','full_name':'Борис Петров','role':'ADMIN'}),201).json()
            eid=a['id']
            check('повтор логина',req('post','/employers/',json={'username':'manager1','full_name':'Другой'}),409)
            check('пустое ФИО',req('post','/employers/',json={'username':'manager3','full_name':'   '}),422)
            check('недопустимая роль',req('post','/employers/',json={'username':'manager3','full_name':'Тест','role':'ROOT'}),422)
            check('короткий логин',req('post','/employers/',json={'username':'ab','full_name':'Тест'}),422)
            result=check('поиск без учёта регистра',req('get','/employers/?query=ИВАНОВА'),200).json();assert [x['id'] for x in result]==[eid]
            assert len(check('отдельный поиск',req('get','/employers/search?query=manager'),200).json())==2
            check('пустой поиск',req('get','/employers/search?query=%20'),422)
            asc=check('сортировка ASC',req('get','/employers/?sort_by=full_name&order=asc'),200).json()
            desc=check('сортировка DESC',req('get','/employers/?sort_by=full_name&order=desc'),200).json()
            assert [x['id'] for x in asc]==list(reversed([x['id'] for x in desc]))
            assert len(check('фильтр роли',req('get','/employers/?role=ADMIN'),200).json())==1
            check('ошибочное направление',req('get','/employers/?order=bad'),422)
            check('изменение ФИО',req('put',f'/employers/{eid}',json={'full_name':'Анна Соколова'}),200)
            check('пустое изменение',req('put',f'/employers/{eid}',json={}),422)
            check('null вместо ФИО',req('put',f'/employers/{eid}',json={'full_name':None}),422)
            check('удаление активной карточки',req('delete',f'/employers/{eid}'),409)
            check('блокировка карточки',req('patch',f'/employers/{eid}/status',json={'is_active':'BLOCKED'}),200)
            assert len(check('фильтр статуса',req('get','/employers/?is_active=BLOCKED'),200).json())==1
            check('неверный статус',req('patch',f'/employers/{eid}/status',json={'is_active':'DELETED'}),422)
            check('чтение карточки',req('get',f'/employers/{eid}'),200)
            check('удаление блокированной карточки',req('delete',f'/employers/{eid}'),204)
            check('карточка после удаления',req('get',f'/employers/{eid}'),404)
            for method,tail,body in [('post','/',{'username':'newman','full_name':'Новый'}),('put',f'/{b["id"]}',{'role':'MANAGER'}),('patch',f'/{b["id"]}/status',{'is_active':'BLOCKED'}),('delete',f'/{b["id"]}',None)]:
                kwargs={'headers':user_header}
                if body is not None:kwargs['json']=body
                check('запрет USER '+method.upper(),getattr(c,method)('/employers'+tail,**kwargs),403)
            schema=c.get('/openapi.json').json()
            Path(__file__).with_name('openapi.json').write_text(json.dumps(schema,ensure_ascii=False,indent=2),encoding='utf-8')
    finally:
        engine.dispose();os.chdir(old)
logs.append(f'ИТОГО: {len(logs)} проверок успешно. Рабочая БД не изменялась.')
Path(__file__).with_name('test_results.txt').write_text('\n'.join(logs),encoding='utf-8')
print('\n'.join(logs))
