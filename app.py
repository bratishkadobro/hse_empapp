import os
import markdown
from flask import Flask, render_template, request, redirect, url_for, session
from flask_session import Session
from db import db
from collections import defaultdict
from config import ABOUT_FILE
from werkzeug.security import check_password_hash
from datetime import datetime, date


app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Используйте реальный секретный ключ
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)


# Проверка авторизации
def is_authenticated():
    return 'user_id' in session


# Проверка, нужно ли сменить пароль
def is_force_pwd():
    return session.get('force_pwd', False)


def is_admin():
    user_id = session.get('user_id')
    user = db.get_user_by_id(user_id)
    return user['is_admin']


# Очистка сессии
def clear_session():
    session.pop('user_id', None)
    session.pop('force_pwd', None)


@app.route('/')
def index():
    if not is_authenticated():
        return redirect(url_for('login'))
    if is_force_pwd():
        return redirect(url_for('force_change_pwd'))
    return render_template('index.html')


@app.route('/form', methods=['GET', 'POST'])
def form():
    if not is_authenticated() or is_force_pwd():
        return redirect(url_for('login'))

    user_id = session['user_id']
    department_owner_id = db.get_user_department_id(user_id)
    added_by = db.get_user_realname(user_id)

    departments = db.get_all_departments()
    departments = [d for d in departments if d[0] == department_owner_id]

    if request.method == 'POST':
        # Получаем данные из формы
        last_name = request.form.get('last-name')
        first_name = request.form.get('first-name')
        department = request.form.get('department')
        absence_reason = request.form.get('absence-reason')
        absence_dates = request.form.get('absence-dates')  # Множественные даты

        # Преобразуем даты в список
        absence_dates_list = absence_dates.split(' ')

        for absence_date in absence_dates_list:
            db.save_person_to_db(f"{last_name} {first_name}", department, absence_reason, absence_date, added_by)
            return redirect(url_for('table'))

    return render_template('form.html', departments=departments)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username, password = request.form.get('username'), request.form.get('password')
        if not username or not password:
            return "Пожалуйста, заполните все поля", 400

        user = db.get_user_by_username(username)
        if not user or not bool(user['active']):
            return "Действие Вашей учетной записи приостановлено", 401

        if check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['force_pwd'] = user['force_pwd']
            session['is_admin'] = user['is_admin']

            if is_force_pwd():
                return redirect(url_for('force_change_pwd'))
            return redirect(url_for('index'))

        return "Неверное имя пользователя или пароль", 401

    return render_template('login.html')


@app.route('/table', methods=['GET', 'POST'])
def table():
    if not is_authenticated() or is_force_pwd():
        return redirect(url_for('login'))


    user_id = session.get('user_id')
    department_id = db.get_user_department_id(user_id)
    is_admin = db.get_user_by_id(user_id)['is_admin']

    department_name, persons = '', []
    if is_admin:
        # Если пользователь админ, то видит все департаменты
        persons = db.get_persons_by_department(department_id=999)
        department_name = "Все отделы"
        accessible_departments = db.get_all_departments()  # Все департамент
    else:
        # Если у пользователя есть доступ только к одному департаменту
        persons = db.get_persons_by_department(department_id)
        department_name = next((d[1] for d in db.get_all_departments() if d[0] == department_id), None)
        accessible_departments = [d for d in db.get_all_departments() if d[0] == department_id]

    # Фильтрация данных по полям формы
    filters = {key: request.args.get(key, '') for key in ('employee', 'department', 'start_date', 'end_date')}
    filtered_persons = filter_persons(persons, filters)

    # Проверяем, есть ли отфильтрованные данные
    no_data = len(filtered_persons) == 0

    return render_template('table.html', 
                           grouped_data=group_by_date(filtered_persons),
                           department_name=department_name, 
                           filtered_count=len(filtered_persons),
                           departments=accessible_departments,  # Передаем только доступные департаменты
                           no_data=no_data,  # передаем переменную no_data
                           **filters)


def filter_persons(persons, filters):
    start_date = datetime.strptime(filters['start_date'], '%Y-%m-%d').date() if filters['start_date'] else None
    end_date = datetime.strptime(filters['end_date'], '%Y-%m-%d').date() if filters['end_date'] else None

    return [
        person for person in persons
        if all([ 
            (not filters['employee'] or filters['employee'].lower() in person[2].lower()),
            (not filters['department'] or filters['department'].lower() in person[3].lower()),
            (not start_date or person[1] >= start_date),
            (not end_date or person[1] <= end_date)
        ])
    ]


def group_by_date(filtered_persons):
    grouped_data = defaultdict(list)
    for person in filtered_persons:
        person_date = person[1] if isinstance(person[1], date) else datetime.strptime(person[1], '%Y-%m-%d').date()
        grouped_data[person_date].append(person)
    return grouped_data


@app.route('/delete_person/<int:person_id>', methods=['POST'])
def delete_person(person_id):
    if not is_authenticated() or is_force_pwd():
        return redirect(url_for('login'))

    db.delete_person(person_id)
    return redirect(url_for('table'))


@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if not is_authenticated() or is_force_pwd():
        return redirect(url_for('login'))

    user = db.get_user_by_id(session['user_id'])
    department_name = db.get_all_departments()
    department_name = 'Доступны все подразделения' if user['department_owner_id'] == 999 else \
        next(d[1] for d in department_name if d[0] == user['department_owner_id'])
    
    role = 'Администратор' if user['is_admin'] else 'Пользователь'

    if request.method == 'POST':
        pwd = request.form.get('new-password')
        db.update_user_password(user['id'], pwd)
        clear_session()
        return render_template('success_change_pwd.html')

    return render_template('profile.html', user=user['username'], department_name=department_name,
                           realname=user['realname'], email=user['email'], role=role)


@app.route('/force_change_pwd', methods=['GET', 'POST'])
def force_change_pwd():
    if not is_authenticated():
        return redirect(url_for('login'))

    user = db.get_user_by_id(session['user_id'])

    if request.method == 'POST':
        pwd = request.form.get('new-password')
        db.update_user_password(user['id'], pwd)
        session['force_pwd'] = False  # Сбрасываем флаг
        clear_session()
        return render_template('success_change_pwd.html')

    return render_template('force_change_pwd.html', user=user['username'])


@app.route('/about')
def about():
    if not is_authenticated() or is_force_pwd():
        return redirect(url_for('login'))

    if os.path.exists(ABOUT_FILE):
        with open(ABOUT_FILE, 'r', encoding='utf-8') as file:
            html_content = markdown.markdown(file.read())
    else:
        html_content = "<p>Информация не найдена.</p>"

    return render_template('about.html', content=html_content)


@app.route('/admin')
def admin():
    if not is_authenticated() or is_force_pwd():
        return redirect(url_for('login'))

    if not is_admin():  # Проверка, является ли пользователь администратором
        return "Доступ запрещен", 403

    return render_template('admin/admin.html')


@app.route('/admin/users')
def users():
    if not is_authenticated() or is_force_pwd():
        return redirect(url_for('login'))

    if not is_admin():  
        return "Доступ запрещен", 400
    
    users = db.get_all_users()  # Получаем всех пользователей
    departments = db.get_all_departments()  # Получаем список всех департаментов

    users_with_departments = []
    for user in users:
        department_name = next((d[1] for d in departments if d[0] == user['department_owner_id']), 'Неизвестен')
        users_with_departments.append({
            'id': user['id'],
            'username': user['username'],
            'realname': user['realname'],
            'email': user['email'],
            'role': 'Администратор' if user['is_admin'] else 'Пользователь',
            'status': 'Активен' if user['active'] else 'Заблокирован',
            'force_pwd': 'Да' if user['force_pwd'] else 'Нет',
            'department': f"{department_name} (ID: {int(user['department_owner_id'])})"
        })
    
    return render_template('admin/admin_users.html', users=users_with_departments)  # Выводим пользователей и департамент


@app.route('/admin/users/create', methods=['GET', 'POST'])
def create_user():
    if not is_authenticated() or is_force_pwd():
        return redirect(url_for('login'))
    
    if not is_admin():
        return "Доступ запрещен", 400

    # Если форма отправлена методом POST
    if request.method == 'POST':
        print('post')
        # Получаем данные из формы
        login = request.form['login']
        full_name = request.form['fullName']
        email = request.form['email']
        department_id = request.form['department']
        password = request.form['password']
        force_change_password = 'forceChangePassword' in request.form
        is_admin_user = 'isAdmin' in request.form
        is_blocked = 'isBlocked' in request.form

        if db.get_user_by_username(login):
            return "Пользователь с таким логином уже существует в базе!"

        result = f'''
            <b>Пользователь успешно создан!</b><br><br>
            Логин: {login}<br>
            ФИО: {full_name}<br>
            Электронная почта: {email}<br>
            Подразделение ID: {department_id}<br>
            Пароль: {password}<br>
            Принудительная смена пароля: {force_change_password}<br>
            Является администратором: {is_admin_user}<br>
            Заблокирован: {is_blocked}<br><br><br><br>'''

        result += '<a href="/admin">Вернуться в админ-панель</a>'

        db.create_user(username=login, pwd=password, active=not is_blocked, 
                       department_owner=department_id, realname=full_name, 
                       email=email, force_pwd=force_change_password,
                       is_admin=is_admin_user)

        return result

    # Получаем список всех департаментов
    departments = db.get_all_departments()

    return render_template('admin/admin_create_user.html', departments=departments)


@app.route('/admin/users/update/<int:user_id>', methods=['GET', 'POST'])
def update_user(user_id):
    if not is_authenticated() or is_force_pwd():
        return redirect(url_for('login'))
    
    if not is_admin():
        return "Доступ запрещен", 400
    
    user = db.get_user_by_id(user_id)
    if not user:
        return "Пользователь не существует", 400
    
    # Если форма отправлена методом POST
    if request.method == 'POST':
        # Получаем данные из формы
        login = request.form['login']
        full_name = request.form['fullName']
        email = request.form['email']
        department_id = request.form['department']
        password = request.form['password']
        force_change_password = 'forceChangePassword' in request.form
        is_admin_user = 'isAdmin' in request.form
        is_blocked = 'isBlocked' in request.form

        # Выводим полученные данные в консоль (или используйте их для обновления в базе данных)
        print(f'Обновленные данные пользователя {user_id}:')
        print(f'Логин: {login}')
        print(f'ФИО: {full_name}')
        print(f'Электронная почта: {email}')
        print(f'Подразделение ID: {department_id}')
        print(f'Пароль: {password}')
        print(f'Принудительная смена пароля: {force_change_password}')
        print(f'Является администратором: {is_admin_user}')
        print(f'Заблокирован: {is_blocked}')

        db.update_user(user_id, username=login, pwd=password, active=not is_blocked, 
                        department_owner=department_id, realname=full_name, 
                        email=email, force_pwd=force_change_password,
                        is_admin=is_admin_user)
        
        return f'Пользователь {login} успешно обновлен!'

    # Получаем список всех департаментов
    departments = db.get_all_departments()
    
    # Назначаем данные текущего пользователя на форму
    department_name = next((d[1] for d in departments if d[0] == user['department_owner_id']), 'Неизвестен')
    
    user_data = {
        'id': user_id,
        'username': user['username'],
        'realname': user['realname'],
        'email': user['email'],
        'department_name': department_name,
        'department_id': user['department_owner_id'],
        'is_admin': user['is_admin'],
        'active': user['active'],
        'force_pwd': user['force_pwd']
    }

    return render_template('admin/admin_update_user.html', user_data=user_data, departments=departments)

    
@app.route('/admin/users/delete/<int:user_id>', methods=['GET', 'POST'])
def delete_user(user_id):
    if not is_authenticated() or is_force_pwd():
        return redirect(url_for('login'))
    
    if not is_admin():
        return "Доступ запрещен", 400

    user = db.get_user_by_id(user_id)
    if not user:
        return "Пользователь не найден", 404
    
    if request.method == 'POST':
        db.delete_user(user_id)
        return redirect(url_for('users'))

    return render_template('admin/admin_confirm_delete_user.html', user=user)
    

@app.route('/admin/departments')
def admin_departments():
    if not is_authenticated() or is_force_pwd():
        return redirect(url_for('login'))

    if not is_admin():
        return "Доступ запрещен", 400

    departments = db.get_all_departments_with_users()  # Получаем департаменты с пользователями

    return render_template('admin/admin_departments.html', departments=departments)

@app.route('/admin/departments/delete/<int:department_id>', methods=['GET', 'POST'])
def confirm_delete_department(department_id):
    if not is_authenticated() or is_force_pwd():
        return redirect(url_for('login'))
    
    if not is_admin():
        return "Доступ запрещен", 400
    
    department = db.get_department_by_id(department_id)
    
    if not department:
        return redirect(url_for('admin_departments'))  # Убедитесь, что здесь используется правильный эндпоинт

    if request.method == 'POST':
        # Если POST запрос, подтверждаем удаление
        db.delete_department(department_id)
        return redirect(url_for('admin_departments'))  # Убедитесь, что здесь используется правильный эндпоинт

    return render_template('admin/admin_confirm_department_delete.html', department=department)


@app.route('/admin/departments/update/<int:department_id>', methods=['GET', 'POST'])
def update_department(department_id):
    if not is_authenticated() or is_force_pwd():
        return redirect(url_for('login'))
    
    if not is_admin():
        return "Доступ запрещен", 400
    
    department = db.get_department_by_id(department_id)
    if not department:
        return "Департамент не существует", 400
    
    # Если форма отправлена методом POST
    if request.method == 'POST':
        # Получаем новое название департамента
        department_name = request.form['department_name']
        

        if db.get_department_by_name(department_name):
            return "Департамент с таким названием уже существует в базе!"

        # Обновляем название департамента в базе данных
        db.update_department_name(department_id, department_name)
        
        return f'Департамент с ID {department_id} успешно обновлен на "{department_name}"!'

    return render_template('admin/admin_update_department.html', department=department)

@app.route('/admin/departments/create', methods=['GET', 'POST'])
def create_department():
    # Проверка на авторизацию и права доступа
    if not is_authenticated() or is_force_pwd():
        return redirect(url_for('login'))

    if not is_admin():
        return "Доступ запрещен", 400

    # Если форма отправлена методом POST
    if request.method == 'POST':
        # Получаем данные из формы
        department_name = request.form['departmentName']

        # Проверка, что департамент с таким именем не существует
        if db.get_department_by_name(department_name):
            return "Департамент с таким названием уже существует в базе!"

        # Создаем департамент в базе данных
        db.create_department(name=department_name)

        result = f'''
            <b>Департамент успешно создан!</b><br><br>
            Название департамента: {department_name}<br><br><br><br>
        '''

        result += '<a href="/admin">Вернуться в админ-панель</a>'

        return result

    # Если метод GET, то отображаем форму
    return render_template('admin/admin_create_department.html')


@app.route('/logout')
def logout():
    clear_session()
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=80)
