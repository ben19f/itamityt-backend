#FROM python:3.12
#
#WORKDIR /app
#
#COPY requirements.txt .
#RUN pip install -r requirements.txt
#
#COPY app ./app
#
#CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
# Берём официальный Python
FROM python:3.11-slim

# Создаём рабочую директорию
WORKDIR /app

# Копируем зависимости
COPY app/requirements.txt .

# Устанавливаем зависимости
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Копируем весь код
COPY app/. /app

# Экспонируем порт FastAPI
EXPOSE 8100

# Команда запуска
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8100"]

