import psycopg2
from werkzeug.security import generate_password_hash
from config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PWD

# Функция для подключения к базе данных
def get_db_connection():
    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PWD
    )
    return conn

# Функция для получения ID департамента владельца
def get_user_department_id(user_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT department_owner_id FROM users WHERE id = %s", (user_id,))
    department_id = cur.fetchone()
    cur.close()
    conn.close()
    return department_id[0] if department_id else None

def get_user_realname(user_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT realname FROM users WHERE id = %s", (user_id,))
    department_id = cur.fetchone()
    cur.close()
    conn.close()
    return department_id[0] if department_id else None

# Функция для получения пользователя по имени
def get_user_by_username(username):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
    user = cursor.fetchone()  # Получаем одного пользователя
    cursor.close()
    conn.close()
    
    # Если пользователь найден, возвращаем его как словарь
    if user:
        return {'id': user[0], 'username': user[1], 'password': user[2], 'active': user[3], 'department_owner_id': user[4], 'realname': user[5], 'email': user[6], 'force_pwd': user[7], 'is_admin': user[8]}  # Возвращаем данные в виде словаря
    return None

# Получение всех подразделений
def get_all_departments():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, department_name FROM departments")
    departments = cur.fetchall()
    cur.close()
    conn.close()
    return departments

def get_all_users():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users")
    users = cur.fetchall()
    cur.close()
    conn.close()
    return [{'id': user[0], 'username': user[1], 'password': user[2], 'active': user[3], 'department_owner_id': user[4], 'realname': user[5], 'email': user[6], 'force_pwd': user[7], 'is_admin': user[8]} for user in users]

# Сохранение данных о человеке в базу данных
def save_person_to_db(full_name, department_id, reason, date, added_by):
    conn = get_db_connection()
    cur = conn.cursor()
    query = """
        INSERT INTO persons (full_name, department_id, reason, date, added_by)
        VALUES (%s, %s, %s, %s, %s)
    """
    values = (full_name, department_id, reason, date, added_by)
    cur.execute(query, values)
    conn.commit()
    cur.close()
    conn.close()

# Получение списка записей о людях
def get_persons_by_department(department_id=None):
    conn = get_db_connection()
    cur = conn.cursor()

    if department_id == 999:
        # Если department_id == 999, показываем всех сотрудников по всем департаментам
        query = """
            SELECT p.id, p.date, p.full_name, d.department_name, p.reason, p.added_by
            FROM persons p
            JOIN departments d ON p.department_id = d.id
            ORDER BY p.date DESC;
        """
        cur.execute(query)
    else:
        # Фильтрация по конкретному департаменту
        query = """
            SELECT p.id, p.date, p.full_name, d.department_name, p.reason, p.added_by
            FROM persons p
            JOIN departments d ON p.department_id = d.id
            WHERE p.department_id = %s
            ORDER BY p.date DESC;
        """
        cur.execute(query, [department_id])

    persons = cur.fetchall()
    cur.close()
    conn.close()
    return persons


def delete_person(person_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM persons WHERE id = %s", (person_id,))
    conn.commit()
    cur.close()
    conn.close()

# Функция для получения пользователя по ID
def get_user_by_id(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
    user = cursor.fetchone()  # Получаем одного пользователя
    cursor.close()
    conn.close()
    
    # Если пользователь найден, возвращаем его как словарь
    if user:
        return {'id': user[0], 'username': user[1], 'password': user[2], 'active': user[3], 'department_owner_id': user[4], 'realname': user[5], 'email': user[6], 'force_pwd': user[7], 'is_admin': user[8]}  # Возвращаем данные в виде словаря
    return None

def update_user_password(user_id, new_pwd):
    conn = get_db_connection()
    cursor = conn.cursor()
    new_pwd = generate_password_hash(new_pwd)
    cursor.execute("UPDATE users SET password = %s, force_pwd=False WHERE id = %s", (new_pwd, user_id,))
    conn.commit()
    cursor.close()
    conn.close()

def create_user(username, pwd, active, department_owner, realname, email, force_pwd, is_admin):
    conn = get_db_connection()
    cursor = conn.cursor()
    pwd = generate_password_hash(pwd)
    cursor.execute(
        "INSERT INTO users (username, password, active, department_owner_id, realname, email, force_pwd, is_admin) \
            VALUES \
                (%s, %s, %s, %s, %s, %s, %s, %s)", (username, pwd, active, department_owner, realname, email, force_pwd, is_admin, ))
    conn.commit()
    cursor.close()
    conn.close()

def update_user(user_id, username, pwd, active, department_owner, realname, email, force_pwd, is_admin):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Если пароль был указан, то хешируем его
    if pwd:
        hashed_pwd = generate_password_hash(pwd)
        cursor.execute(
            "UPDATE users SET username = %s, password = %s, active = %s, department_owner_id = %s, realname = %s, \
             email = %s, force_pwd = %s, is_admin = %s WHERE id = %s", 
            (username, hashed_pwd, active, department_owner, realname, email, force_pwd, is_admin, user_id)
        )
    else:
        # Если пароль не был изменён, обновляем все поля, кроме пароля
        cursor.execute(
            "UPDATE users SET username = %s, active = %s, department_owner_id = %s, realname = %s, \
             email = %s, force_pwd = %s, is_admin = %s WHERE id = %s", 
            (username, active, department_owner, realname, email, force_pwd, is_admin, user_id)
        )

    conn.commit()
    cursor.close()
    conn.close()

def delete_user(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
    conn.commit()
    cursor.close()
    conn.close()


def get_all_departments_with_users():
    conn = get_db_connection()
    cur = conn.cursor()
    query = """
        SELECT d.id, d.department_name, 
               COALESCE(ARRAY_AGG(u.username), ARRAY[]::text[]) AS users
        FROM departments d
        LEFT JOIN users u ON d.id = u.department_owner_id
        GROUP BY d.id, d.department_name
        ORDER BY d.id
    """
    cur.execute(query)
    departments = cur.fetchall()
    cur.close()
    conn.close()
    # Возвращаем список департаментов с пользователями
    return [{'id': row[0], 'name': row[1], 'users': row[2]} for row in departments]


def delete_department(department_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM departments WHERE id = %s", (department_id,))
    conn.commit()
    cur.close()
    conn.close()

def get_department_by_id(department_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM departments WHERE id = %s", (department_id,))
    department = cur.fetchone()
    cur.close()
    conn.close()
    if department:
        return {'id': department[0], 'name': department[1]}  # Пример структуры возвращаемого значения
    return None

def update_department_name(department_id, department_name):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE departments SET department_name = %s WHERE id = %s", 
        (department_name, department_id)
    )
    conn.commit()
    cursor.close()
    conn.close()

def get_department_by_name(name):
    """Проверка, существует ли департамент с таким названием."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM departments WHERE department_name = %s', (name,))
    department = cursor.fetchone()
    conn.close()
    return department

def create_department(name):
    """Создание нового департамента в базе данных."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO departments (department_name) VALUES (%s)', (name,))
    conn.commit()
    conn.close()
