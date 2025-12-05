#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Веб-приложение для технологического древа
Конвертация главного окна tech_tree.py в веб-версию для удобного использования на смартфонах
"""

from flask import Flask, render_template, jsonify, request, send_from_directory
import json
import os
import sqlite3
from collections import deque
from datetime import datetime

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False

# Путь к текущей директории
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Путь к базе данных
DB_PATH = os.path.join(BASE_DIR, 'progress.db')

# Инициализация базы данных
def init_db():
    """Инициализация базы данных SQLite для хранения прогресса"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Создаем таблицу для хранения прогресса пользователей
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_ip TEXT NOT NULL,
            tech_name TEXT NOT NULL,
            completed INTEGER NOT NULL DEFAULT 0,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_ip, tech_name)
        )
    ''')

    # Создаем индекс для быстрого поиска по IP
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_user_ip
        ON user_progress(user_ip)
    ''')

    conn.commit()
    conn.close()

# Функция для получения IP адреса клиента
def get_client_ip():
    """Получить IP адрес клиента с учетом прокси"""
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0].strip()
    elif request.headers.get('X-Real-IP'):
        return request.headers.get('X-Real-IP')
    else:
        return request.remote_addr

# Функция для сохранения прогресса в базу данных
def save_progress_to_db(user_ip, progress_data):
    """
    Сохранить прогресс пользователя в базу данных
    progress_data: dict {tech_name: bool}
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # Удаляем старый прогресс пользователя
        cursor.execute('DELETE FROM user_progress WHERE user_ip = ?', (user_ip,))

        # Вставляем новый прогресс
        for tech_name, completed in progress_data.items():
            cursor.execute('''
                INSERT INTO user_progress (user_ip, tech_name, completed, updated_at)
                VALUES (?, ?, ?, ?)
            ''', (user_ip, tech_name, 1 if completed else 0, datetime.now()))

        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        print(f"Error saving progress: {e}")
        return False
    finally:
        conn.close()

# Функция для загрузки прогресса из базы данных
def load_progress_from_db(user_ip):
    """
    Загрузить прогресс пользователя из базы данных
    Возвращает: dict {tech_name: bool}
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        cursor.execute('''
            SELECT tech_name, completed
            FROM user_progress
            WHERE user_ip = ? AND completed = 1
        ''', (user_ip,))

        rows = cursor.fetchall()
        progress = {tech_name: bool(completed) for tech_name, completed in rows}
        return progress
    except Exception as e:
        print(f"Error loading progress: {e}")
        return {}
    finally:
        conn.close()

# Загрузка данных из JSON файла
def load_tech_data():
    json_path = os.path.join(BASE_DIR, 'techno2.json')
    try:
        with open(json_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
        return data
    except FileNotFoundError:
        return {"технологии": []}

data = load_tech_data()

# Вспомогательная функция для проверки наличия родителя в условиях
def is_parent_in_conditions(parent_name, conditions):
    """
    Проверяет, является ли parent_name одним из условий технологии.
    Поддерживает оба формата: старый (список строк) и новый (список путей).
    """
    if not conditions:
        return False

    if isinstance(conditions[0], str):
        # Старый формат: простой список
        return parent_name in conditions
    elif isinstance(conditions[0], list):
        # Новый формат: альтернативные пути
        for path in conditions:
            if parent_name in path:
                return True
        return False
    return False

# Функция для поиска всех родителей
def find_all_parents(tech_name):
    parents = {}
    queue = deque([(tech_name, 0)])
    while queue:
        current_tech, level = queue.popleft()
        if current_tech in parents:
            continue
        parents[current_tech] = level
        for tech in data['технологии']:
            if tech['название'] == current_tech:
                conditions = tech['условия']
                # Обработка обоих форматов условий
                if conditions:
                    if isinstance(conditions[0], str):
                        # Старый формат: простой список родителей
                        for parent in conditions:
                            queue.append((parent, level + 1))
                    elif isinstance(conditions[0], list):
                        # Новый формат: альтернативные пути
                        for path in conditions:
                            for parent in path:
                                queue.append((parent, level + 1))
                break
    return parents

# Функция для поиска всех детей
def find_all_children(tech_name):
    children = {}
    queue = deque([(tech_name, 0)])
    while queue:
        current_tech, level = queue.popleft()
        if current_tech in children:
            continue
        children[current_tech] = level
        for tech in data['технологии']:
            # Проверяем, является ли current_tech родителем для tech
            if is_parent_in_conditions(current_tech, tech['условия']):
                queue.append((tech['название'], level + 1))
    return children

# Функция для проверки доступности технологии
def is_tech_available(tech_name, tech_flags):
    for tech in data['технологии']:
        if tech['название'] == tech_name:
            conditions = tech['условия']

            # Если нет условий, технология доступна
            if not conditions:
                return True

            # Проверка типа первого элемента для определения формата
            if isinstance(conditions[0], str):
                # Старый формат: все условия должны быть выполнены (AND логика)
                for parent in conditions:
                    if not tech_flags.get(parent, False):
                        return False
                return True
            elif isinstance(conditions[0], list):
                # Новый формат: хотя бы один путь должен быть полностью выполнен (OR логика между путями)
                for path in conditions:
                    path_completed = True
                    for parent in path:
                        if not tech_flags.get(parent, False):
                            path_completed = False
                            break
                    if path_completed:
                        return True
                return False
    return True

@app.route('/')
def index():
    """Главная страница приложения"""
    return render_template('index.html')

@app.route('/api/technologies')
def get_technologies():
    """Получить список всех технологий"""
    return jsonify(data)

@app.route('/api/technology/<tech_name>')
def get_technology(tech_name):
    """Получить информацию о конкретной технологии"""
    for tech in data['технологии']:
        if tech['название'] == tech_name:
            return jsonify(tech)
    return jsonify({'error': 'Technology not found'}), 404

@app.route('/api/tree/<tech_name>')
def get_tech_tree(tech_name):
    """Получить древо технологии (родители и дети)"""
    parents = find_all_parents(tech_name)
    children = find_all_children(tech_name)

    # Собираем узлы и связи для визуализации
    nodes = set([tech_name])
    nodes.update(parents.keys())
    nodes.update(children.keys())

    edges = []
    for node in nodes:
        for tech in data['технологии']:
            if tech['название'] == node:
                conditions = tech['условия']
                if conditions:
                    if isinstance(conditions[0], str):
                        for parent in conditions:
                            if parent in nodes:
                                edges.append({'from': parent, 'to': node})
                    elif isinstance(conditions[0], list):
                        for path in conditions:
                            for parent in path:
                                if parent in nodes:
                                    edges.append({'from': parent, 'to': node})
                break

    return jsonify({
        'center': tech_name,
        'nodes': list(nodes),
        'edges': edges,
        'parents': parents,
        'children': children
    })

@app.route('/api/check_availability', methods=['POST'])
def check_availability():
    """Проверить доступность технологий на основе прогресса"""
    tech_flags = request.json.get('progress', {})
    result = {}

    for tech in data['технологии']:
        tech_name = tech['название']
        if tech_flags.get(tech_name, False):
            result[tech_name] = 'completed'
        elif is_tech_available(tech_name, tech_flags):
            result[tech_name] = 'available'
        else:
            result[tech_name] = 'unavailable'

    return jsonify(result)

@app.route('/api/tech_help/<tech_name>')
def check_tech_help(tech_name):
    """Проверить наличие mhtml файла для технологии и вернуть информацию о нём"""
    web_dir = os.path.join(BASE_DIR, 'web')

    # Проверяем существование директории web
    if not os.path.exists(web_dir):
        return jsonify({'exists': False})

    # Ищем mhtml файл с названием технологии
    mhtml_file = os.path.join(web_dir, f'{tech_name}.mhtml')

    if os.path.exists(mhtml_file):
        return jsonify({'exists': True, 'filename': f'{tech_name}.mhtml'})

    return jsonify({'exists': False})

@app.route('/web/<filename>')
def serve_web_file(filename):
    """Отдать mhtml файл из папки web"""
    web_dir = os.path.join(BASE_DIR, 'web')
    # Устанавливаем правильный MIME тип и Content-Disposition для открытия в браузере
    response = send_from_directory(web_dir, filename)
    response.headers['Content-Type'] = 'multipart/related'
    response.headers['Content-Disposition'] = 'inline'
    return response

@app.route('/api/progress/save', methods=['POST'])
def save_progress():
    """Сохранить прогресс пользователя в базу данных"""
    try:
        user_ip = get_client_ip()
        progress_data = request.json.get('progress', {})

        if save_progress_to_db(user_ip, progress_data):
            return jsonify({'success': True, 'message': 'Прогресс успешно сохранен'})
        else:
            return jsonify({'success': False, 'message': 'Ошибка сохранения прогресса'}), 500
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/progress/load', methods=['GET'])
def load_progress():
    """Загрузить прогресс пользователя из базы данных"""
    try:
        user_ip = get_client_ip()
        progress_data = load_progress_from_db(user_ip)
        return jsonify({'success': True, 'progress': progress_data})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

if __name__ == '__main__':
    # Инициализация базы данных
    init_db()

    # Запуск сервера
    # Для разработки используем debug=True
    # Для продакшена используйте gunicorn или uwsgi
    app.run(host='0.0.0.0', port=5000, debug=True)
