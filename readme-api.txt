Что умеет бекенд на данном этапе

Структура проекта готова

app/main.py – точка входа FastAPI.

app/api/router.py – собирает эндпоинты.

app/models/ – модели SQLAlchemy (User, Item).

app/db/base.py – общий Base для моделей.

app/core/config.py – настройки через Pydantic 2 (DATABASE_URL и другие переменные).

.env – хранит переменные окружения (URL базы, секреты, и т.д.).

Alembic готов к созданию и управлению миграциями.

База данных подключена

FastAPI через SQLAlchemy подключается к PostgreSQL.

Миграции Alembic готовы, чтобы создавать таблицы (User, Item) в базе.

API готов к расширению

Есть базовый роутер router.py, health.py для проверки работоспособности.

Подключена структура для JWT (core/security.py) и будущего auth.

Запуск и горячая перезагрузка

uvicorn main:app --reload – сервер стартует, отслеживает изменения в коде и автоматически перезагружается.




миграция из app
python -m alembic revision --autogenerate -m "init"
python -m alembic revision --autogenerate -m "описание правок"
python -m alembic upgrade head


запуск fastapi
uvicorn main:app --reload

Проверка доступности сервера

В браузере или через curl:

curl http://127.0.0.1:8000/health


Проверка JWT (если хочешь прямо сейчас)

Можно вызвать функции в core/security.py для генерации токена и проверки:

from core.security import create_access_token, verify_password, hash_password

hashed = hash_password("mypassword")
assert verify_password("mypassword", hashed)
token = create_access_token({"sub": "user1"})
print(token)

Если ошибок нет → auth-механика готова, даже если эндпоинтов логина пока нет.

Продолжаем писать API, добавлять auth, CRUD для пользователей и предметов, подключать фронтенд.

план следующего шага: auth + CRUD + JWT + миграции, чтобы бекенд был полностью рабочий

Мы сделаем полноценный CRUD для Item.

То есть API сможет:

Метод	Endpoint	Что делает
POST	/items	создать item
GET	/items	получить список
GET	/items/{id}	получить один item
PUT	/items/{id}	изменить item
DELETE	/items/{id}	удалить item

http://127.0.0.1:8000/docs


создал юзера {
  "email": "test@test.com",
  "password": "123456"
}


Response body

{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhbGljZSIsImV4cCI6MTc3MzQxMjE2OH0.KwfIAImCQukfL19mSF3lYnJqmps_s-KQ9VmwTbMpbOY",
  "token_type": "bearer"
}
