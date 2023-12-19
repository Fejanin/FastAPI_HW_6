from pydantic import BaseModel
from pydantic import Field
from hashlib import sha256
from sqlalchemy import create_engine, Integer, Column, String, Float, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from databases import Database
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
import pandas as pd
from fastapi.templating import Jinja2Templates


DATABASE_URL = 'sqlite:///my_db.db'
engine = create_engine(DATABASE_URL, connect_args={'check_same_thread': False})
database = Database(DATABASE_URL)
Base = declarative_base()
templates =Jinja2Templates(directory='templates')


class User(BaseModel):
    id: int = Field(default=None, alias='user_id')
    username: str = Field(min_length=3, max_length=30)
    sur_name: str = Field(min_length=3, max_length=30)
    email: str = Field(min_length=10, max_length=100)
    password: str = Field(min_length=12, max_length=100)


class DbUser(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String(30))
    sur_name = Column(String(30))
    email = Column(String(100))
    password = Column(String(100))


class Goods(BaseModel):
    id: int = Field(default=None, alias='good_id')
    name: str = Field(min_length=3, max_length=30)
    description: str = Field(min_length=0, max_length=500)
    prise: float = Field(title="Price", gt=0, le=100000)


class DbGoods(Base):
    __tablename__ = 'goods'
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(30))
    description = Column(String(500))
    prise = Column(Float)


class Orders(BaseModel):
    id: int = Field(default=None, alias='order_id')
    user_id: int = Field()
    good_id: int = Field()
    date: str = Field(String(20))
    status: bool = Field(default=False)


class DbOrders(Base):
    __tablename__ = 'orders'
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    good_id = Column(Integer, ForeignKey('goods.id'))
    date = Column(String(20))
    status = Column(Boolean)


Base.metadata.create_all(bind=engine)

app = FastAPI()


@app.on_event('startup')
async def startup():
    await database.connect()


@app.on_event('shutdown')
async def shutdown():
    await database.disconnect()


@app.post('/users/', response_model=User)
async def create_user(user: User):
    user.password = sha256(user.password.encode(encoding='utf-8')).hexdigest()
    data = vars(user) # vars возвращает словарь с атрибутами
    del data['id']
    query = DbUser.__table__.insert().values(data)
    user.id = await database.execute(query)
    print(user)
    return user


@app.post('/goods/', response_model=Goods)
async def create_good(good: Goods):
    data = vars(good) # vars возвращает словарь с атрибутами
    del data['id']
    query = DbGoods.__table__.insert().values(data)
    good.id = await database.execute(query)
    return good


@app.post('/orders/', response_model=Orders)
async def create_good(good: Orders):
    data = vars(good) # vars возвращает словарь с атрибутами
    del data['id']
    query = DbOrders.__table__.insert().values(data)
    good.id = await database.execute(query)
    return good


@app.get('/users/', response_class=HTMLResponse)
async def get_users(request: Request):
    query = DbUser.__table__.select()
    users = await database.fetch_all(query)
    table = pd.DataFrame([user for user in users]).to_html()
    print(DbUser.__tablename__.upper())
    return templates.TemplateResponse('index.html', {
        'request': request,
        'table': table,
        'page_name': DbUser.__tablename__.upper()
    })


@app.get('/goods/', response_class=HTMLResponse)
async def get_goods(request: Request):
    query = DbGoods.__table__.select()
    goods = await database.fetch_all(query)
    table = pd.DataFrame([good for good in goods]).to_html()
    return templates.TemplateResponse('index.html', {
        'request': request,
        'table': table,
        'page_name': DbGoods.__tablename__.upper()
    })


@app.get('/orders/', response_class=HTMLResponse)
async def get_orders(request: Request):
    query = DbOrders.__table__.select()
    orders = await database.fetch_all(query)
    table = pd.DataFrame([order for order in orders]).to_html()
    return templates.TemplateResponse('index.html', {
        'request': request,
        'table': table,
        'page_name': DbOrders.__tablename__.upper()
    })


@app.get('/users/{user_id}', response_model=User)
async def get_user(user_id: int):
    query = DbUser.__table__.select().where(DbUser.id == user_id)
    user = await database.fetch_one(query)
    return User(**user)


@app.get('/goods/{good_id}', response_model=Goods)
async def get_good(good_id: int):
    query = DbGoods.__table__.select().where(DbGoods.id == good_id)
    good = await database.fetch_one(query)
    return Goods(**good)


@app.get('/orders/{order_id}', response_model=Orders)
async def get_order(order_id: int):
    query = DbOrders.__table__.select().where(DbOrders.id == order_id)
    order = await database.fetch_one(query)
    return Orders(**order)


@app.put('/users/{user_id}', response_model=User)
async def up_user(user_id: int, user: User):
    user.password = sha256(user.password.encode(encoding='utf-8')).hexdigest()
    data = vars(user)  # vars возвращает словарь с атрибутами
    del data['id']
    query = DbUser.__table__.update().where(DbUser.id == user_id).values(data)
    user.id = await database.execute(query)
    return user


@app.put('/goods/{good_id}', response_model=Goods)
async def up_good(good_id: int, good: Goods):
    data = vars(good)  # vars возвращает словарь с атрибутами
    del data['id']
    query = DbGoods.__table__.update().where(DbGoods.id == good_id).values(data)
    good.id = await database.execute(query)
    return good


@app.put('/orders/{order_id}', response_model=Orders)
async def up_order(order_id: int, order: Orders):
    data = vars(order)  # vars возвращает словарь с атрибутами
    del data['id']
    query = DbOrders.__table__.update().where(DbOrders.id == order_id).values(data)
    order.id = await database.execute(query)
    return order


@app.delete('/users/{user_id}')
async def del_user(user_id: int):
    query = DbUser.__table__.delete().where(DbUser.id == user_id)
    await database.execute(query)
    return {'message': 'User was deleted.'}


@app.delete('/goods/{good_id}')
async def del_good(good_id: int):
    query = DbGoods.__table__.delete().where(DbGoods.id == good_id)
    await database.execute(query)
    return {'message': 'Good was deleted.'}


@app.delete('/orders/{order_id}')
async def del_order(order_id: int):
    query = DbOrders.__table__.delete().where(DbOrders.id == order_id)
    await database.execute(query)
    return {'message': 'Order was deleted.'}
