# Используем официальный образ Python
FROM python:3.9-slim

# Устанавливаем зависимости системы, необходимые для работы с PostgreSQL и другими библиотеками
RUN apt-get update && apt-get install -y \
    libpq-dev \
    && pip install --upgrade pip wheel

# Копируем requirements.txt и устанавливаем Python зависимости
COPY requirements.txt /app/requirements.txt
RUN pip install -r /app/requirements.txt

# Копируем весь проект в контейнер
COPY . /app

# Устанавливаем рабочую директорию
WORKDIR /app

# Устанавливаем команду по умолчанию, которая будет выполняться при запуске контейнера
CMD ["python", "app.py"]
