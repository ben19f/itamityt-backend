настроил одну миграцию для прот и дев базах
добавил регистрацию с подтверждением через почту
для удаления опечатки в имени ветки


# ITAMITYT Backend

Backend сервиса [itamityt.ru](https://itamityt.ru), построенный на FastAPI.

Backend отвечает за:

* регистрацию и авторизацию пользователей;
* управление профилем;
* аватары пользователей;
* фотографии профиля;
* управление ссылками профиля;
* публичные профили;
* работу с PostgreSQL;
* хранение изображений в S3;
* API для frontend;
* миграции базы данных через Alembic.

---

## Стек

* Python 3.11+
* FastAPI
* Uvicorn
* SQLAlchemy 2
* PostgreSQL
* asyncpg
* Alembic
* Pydantic Settings
* JWT
* bcrypt
* boto3
* S3-compatible storage

Для production backend запускается в Kubernetes.

---

# Структура проекта

Основные директории:

```text
itamityt-backend/
├── api/
│   ├── router.py
│   ├── health.py
│   ├── public.py
│   └── users.py
│
├── core/
│   ├── config.py
│   └── security.py
│
├── db/
│   ├── base.py
│   ├── deps.py
│   └── session.py
│
├── models/
│   ├── user.py
│   └── item.py
│
├── schemas/
│   └── ...
│
├── services/
│   └── storage.py
│
├── alembic/
│   ├── versions/
│   └── ...
│
├── main.py
├── requirements.txt
├── Dockerfile
└── README.md
```

---

# Переменные окружения

Backend использует переменные окружения.

Основные параметры:

```text
DATABASE_URL
SECRET_KEY
ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES

S3_ENDPOINT
S3_PUBLIC_URL
S3_ACCESS_KEY
S3_SECRET_KEY
S3_BUCKET
S3_REGION
S3_PREFIX
```

Пример локального `.backendenv`:

```env
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/itamityt

SECRET_KEY=change-me
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

S3_ENDPOINT=https://s3.example.com
S3_PUBLIC_URL=https://s3.example.com/bucket
S3_ACCESS_KEY=your-access-key
S3_SECRET_KEY=your-secret-key
S3_BUCKET=your-bucket
S3_REGION=us-east-1
S3_PREFIX=dev
```

> Файл с реальными credentials не должен попадать в Git.

---

# S3

Для хранения пользовательских изображений используется S3-compatible storage.

Backend работает с S3 через `boto3`.

Схема:

```text
Browser
   │
   │ upload
   ▼
FastAPI
   │
   │ boto3
   ▼
S3
   │
   │ public URL
   ▼
Browser
```

Frontend **не получает S3 credentials**.

Backend загружает изображения в S3 и сохраняет публичный URL в PostgreSQL.

---

## Структура файлов в S3

Используется разделение окружений:

```text
dev/
└── users/
    ├── avatars/
    │   └── <user_id>/
    └── photos/
        └── <user_id>/

prod/
└── users/
    ├── avatars/
    │   └── <user_id>/
    └── photos/
        └── <user_id>/
```

Переменная:

```env
S3_PREFIX=dev
```

для тестового окружения и:

```env
S3_PREFIX=prod
```

для production.

Таким образом один Docker image можно использовать в разных окружениях.

---

# Установка локально

Создание виртуального окружения:

```bash
python3 -m venv .venv
```

Активация:

```bash
source .venv/bin/activate
```

Установка зависимостей:

```bash
pip install -r requirements.txt
```

Если зависимости устанавливаются впервые, убедитесь, что присутствует:

```text
boto3
python-multipart
```

`python-multipart` необходим FastAPI для загрузки файлов через `UploadFile`.

---

# Запуск локально

Для локального запуска необходимо задать переменные окружения.

Если используется `.backendenv`, можно запускать backend через Docker Compose.

Пример:

```yaml
services:
  itamityt_web:
    build: .
    env_file:
      - ../.backendenv
    ports:
      - "8100:8000"
```

После запуска API будет доступен по адресу:

```text
http://localhost:8100
```

Swagger:

```text
http://localhost:8100/docs
```

ReDoc:

```text
http://localhost:8100/redoc
```

---

# Запуск без Docker

При наличии PostgreSQL:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Swagger:

```text
http://localhost:8000/docs
```

---

# Database migrations

Для работы с миграциями используется Alembic.

Создание миграции:

```bash
alembic revision --autogenerate -m "description"
```

Применение миграций:

```bash
alembic upgrade head
```

Просмотр текущей версии:

```bash
alembic current
```

Просмотр истории:

```bash
alembic history
```

Откат последней миграции:

```bash
alembic downgrade -1
```

---

# Docker

Сборка:

```bash
docker build -t itamityt-backend .
```

Локальный запуск:

```bash
docker run --env-file ../.backendenv -p 8100:8000 itamityt-backend
```

Для Kubernetes Docker image публикуется во внутренний registry:

```text
192.168.96.116:5000/itamityt/backend
```

Например:

```bash
docker build \
  -t 192.168.96.116:5000/itamityt/backend:latest \
  .

docker push \
  192.168.96.116:5000/itamityt/backend:latest
```

---

# Kubernetes

Backend разворачивается через Helm.

Основные Kubernetes-ресурсы:

```text
Deployment
Service
Secret
ConfigMap
```

Backend получает конфигурацию через:

```yaml
envFrom:
  - secretRef:
      name: projectsecrets
  - configMapRef:
      name: projectconfigs
```

---

## Secret

Секреты backend хранятся в Kubernetes Secret.

Пример:

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: projectsecrets
  namespace: testspaceita
type: Opaque
stringData:
  DATABASE_URL: "..."
  SECRET_KEY: "..."

  S3_ENDPOINT: "https://s3.example.com"
  S3_PUBLIC_URL: "https://s3.example.com/bucket"
  S3_BUCKET: "..."
  S3_REGION: "us-east-1"

  S3_ACCESS_KEY: "..."
  S3_SECRET_KEY: "..."

  S3_PREFIX: "dev"
```

Применение:

```bash
kubectl apply -f projectsecrets.yaml
```

> После изменения Secret необходимо пересоздать Pod или выполнить rollout restart Deployment, если значения используются как environment variables.

Например:

```bash
kubectl -n testspaceita rollout restart deployment backend
```

Проверка:

```bash
kubectl -n testspaceita rollout status deployment backend
```

---

# Проверка Kubernetes

Список Pod:

```bash
kubectl -n testspaceita get pods
```

Логи:

```bash
kubectl -n testspaceita logs deployment/backend
```

Описание Deployment:

```bash
kubectl -n testspaceita describe deployment backend
```

Проверка Secret:

```bash
kubectl -n testspaceita get secret projectsecrets
```

Не выводите значения Secret в терминал без необходимости.

---

# Profile API

## Текущий пользователь

```http
GET /users/me
```

Требует JWT:

```http
Authorization: Bearer <token>
```

---

## Изменение профиля

```http
PATCH /users/me
```

Пример:

```json
{
  "display_name": "Музей костей",
  "profile_description": "Просветительская выставка анатомических скелетов",
  "profile_extra_info": "Сочи"
}
```

---

# Avatar API

## Загрузка аватара

```http
POST /users/me/avatar
```

Формат:

```text
multipart/form-data
```

Поле:

```text
file
```

Разрешены:

```text
JPEG
PNG
WEBP
```

Максимальный размер:

```text
5 MB
```

---

## Удаление аватара

```http
DELETE /users/me/avatar
```

---

# Photos API

Пользователь может загрузить до 5 фотографий.

Максимальный размер одной фотографии:

```text
10 MB
```

---

## Получение фотографий пользователя

```http
GET /users/me/photos
```

Ответ:

```json
[
  {
    "id": 1,
    "image_url": "https://s3.example.com/...",
    "position": 0
  }
]
```

---

## Загрузка фотографии

```http
POST /users/me/photos
```

Формат:

```text
multipart/form-data
```

Поле:

```text
file
```

---

## Удаление фотографии

```http
DELETE /users/me/photos/{photo_id}
```

---

# Public Profile API

Публичный профиль:

```http
GET /public/profile/{username}
```

Авторизация не требуется.

Пример:

```text
GET /public/profile/muzej_kostej
```

Ответ содержит:

```json
{
  "username": "muzej_kostej",
  "display_name": "Выставка \"Музей костей\"",
  "avatar_url": null,
  "photos": [],
  "items": [],
  "profile_description": "...",
  "profile_extra_info": "...",
  "blocks": [
    "gallery",
    "description",
    "links",
    "extra"
  ]
}
```

---

# Links / Items API

Пользователь может создавать ссылки своего профиля.

Получение ссылок:

```http
GET /items/
```

Создание:

```http
POST /items/
```

Пример:

```json
{
  "name": "VK",
  "description": "Группа ВКонтакте"
}
```

Удаление:

```http
DELETE /items/{item_id}
```

---

# Авторизация

Для защищённых endpoints используется JWT.

После авторизации frontend сохраняет токен и передаёт его в HTTP header:

```http
Authorization: Bearer <JWT>
```

Основные endpoints авторизации:

```text
POST /users/register
POST /auth/login
```

Точный список доступных routes можно посмотреть в Swagger:

```text
/docs
```

---

# Health check

Для проверки доступности backend используется health endpoint:

```http
GET /health
```

Пример:

```bash
curl http://localhost:8000/health
```

---

# Конфигурация окружений

Один Docker image используется для разных окружений.

Различия между окружениями задаются конфигурацией Kubernetes.

Например:

### Test

```env
S3_PREFIX=dev
```

### Production

```env
S3_PREFIX=prod
```

Это позволяет использовать один и тот же image:

```text
itamityt/backend:<tag>
```

при разных настройках окружения.

---

# Безопасность

Не хранить в Git:

* `DATABASE_URL` с паролем;
* `SECRET_KEY`;
* `S3_ACCESS_KEY`;
* `S3_SECRET_KEY`;
* JWT credentials;
* другие production secrets.

Для Kubernetes использовать:

```text
Secret
```

Для обычной конфигурации:

```text
ConfigMap
```

S3 credentials не должны попадать во frontend JavaScript.

---

# Разработка

Рекомендуемый цикл разработки:

```text
Изменение кода
      ↓
Локальный запуск
      ↓
Проверка /docs
      ↓
Проверка миграций
      ↓
Docker build
      ↓
Push в registry
      ↓
Helm deploy
      ↓
Проверка Pod
      ↓
Проверка API
```

---

# Проверка после деплоя

После обновления backend:

```bash
kubectl -n testspaceita get pods
```

Проверить rollout:

```bash
kubectl -n testspaceita rollout status deployment backend
```

Проверить логи:

```bash
kubectl -n testspaceita logs deployment/backend
```

Проверить API:

```bash
curl https://api.itamityt.ru/health
```

Swagger:

```text
https://api.itamityt.ru/docs
```

---

# Важные особенности

## S3

Изображения не проходят через frontend напрямую к S3.

```text
Frontend
   ↓
FastAPI
   ↓
S3
```

После загрузки backend возвращает публичный URL изображения.

```text
https://s3.../bucket/dev/users/...
```

Frontend использует этот URL непосредственно для отображения изображения.

---

## Пользовательские фотографии

Фотографии хранятся отдельно от аватара:

```text
users/avatars/<user_id>/
users/photos/<user_id>/
```

При удалении записи фотографии backend также пытается удалить объект из S3.

---

## Public profile

Публичный профиль не требует авторизации.

URL:

```text
/uun/{username}
```

Frontend получает данные через:

```text
GET /public/profile/{username}
```

Изображения загружаются браузером непосредственно из S3.

---

# Troubleshooting

## Backend не запускается с ошибкой `s3_endpoint Field required`

Проверить наличие S3-переменных:

```bash
kubectl -n testspaceita get secret projectsecrets
```

Убедиться, что Secret был применён:

```bash
kubectl apply -f projectsecrets.yaml
```

После изменения Secret:

```bash
kubectl -n testspaceita rollout restart deployment backend
```

---

## Проверка ключей Secret

Не выводя значения:

```bash
kubectl -n testspaceita get secret projectsecrets \
  -o jsonpath='{.data}'
```

При необходимости можно проверить наличие конкретного ключа:

```bash
kubectl -n testspaceita get secret projectsecrets \
  -o jsonpath='{.data.S3_ENDPOINT}'
echo
```

---

## Backend запускается, но изображения не загружаются

Проверить:

1. `S3_ENDPOINT`;
2. `S3_PUBLIC_URL`;
3. `S3_BUCKET`;
4. `S3_ACCESS_KEY`;
5. `S3_SECRET_KEY`;
6. `S3_REGION`;
7. публичный доступ к bucket;
8. права access key;
9. `S3_PREFIX`.

Проверить API через Swagger:

```text
/docs
```

---

# License

Проект находится в разработке.

Copyright © ITAMITYT
