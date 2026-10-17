FROM 192.168.96.116:5000/base/python:3.11-slim

# Создаём рабочую директорию
WORKDIR /app

# Копируем зависимости
COPY requirements.txt .

# Устанавливаем зависимости
##если надо качать
#RUN pip install --upgrade pip \
#    && pip install --no-cache-dir -r requirements.txt
## если использовать из кеша
RUN pip install --upgrade pip \
    && pip install -r requirements.txt



# Копируем весь код
COPY . /app

# Экспонируем порт FastAPI
EXPOSE 8000

# Команда запуска
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

