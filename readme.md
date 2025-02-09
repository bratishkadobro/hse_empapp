# HSE EMP APP
Веб сервис для контроля посещаемости сотрудниками ФКН ВШЭ своего рабочего места

# Поднимаем базу данных
В корне лежит скрипт для создания базы (flask empapp.sql), включая все необходимые таблицы. Для администрирования базы рекомендую pgAdmin4. 

# Разворачиваем проект (dev)
1. Склонировать репозиторий через git clone
2. Создать виртуальное окружение и установить зависимости
```shell
python -m venv env && env\Scripts\activate && python -m pip install --upgrade pip wheel && pip install -r requirements.txt
```
3. В корне проекта необходимо создать файл с конфигом config.py
```python
# Secret Key для хранения сессий. Просто сгенерируйте что-то сложное. 
SECRET_KEY = '1RiClG8ia4I5TX3PJJTI0RvhgfjJVJOi4LLelBuA8Mk4ZJ5J8Y4NVLIawNV5syJ0'

# Данные для подключения к базе данных PostgreSQL
DB_HOST = 'postgres_emp_app'
DB_PORT = 5432
DB_NAME = 'postgres_empapp_db'
DB_USER = 'postgres_empapp'
DB_PWD = 'YJ1iKdaNDQMfuj7keOce3AKxTvzGo50r' 

ABOUT_FILE = 'static/about.md' # файл в котором описана информация для помощи
```

4. python app.py

# Разворачиваем проект (prod)
1. Склонировать репозиторий через git clone
2. В корне проекта необходимо создать файл с конфигом config.py (см. выше)
3. Установить docker и docker-compose
4. Поднять проект с помощью docker-compose
```shell
docker-compose up -d --build
```
5. Проверить статус можно так:
```
docker ps -a
docker-compose logs -f *container_name*
```
Также туда зашит скрипт для поднятия postgresql