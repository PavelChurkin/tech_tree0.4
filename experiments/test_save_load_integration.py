#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Интеграционный тест для проверки сохранения и загрузки прогресса через API
"""

import sys
import os
import time
import requests
import json
from multiprocessing import Process

# Добавляем родительскую директорию в путь для импорта
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def run_server():
    """Запустить Flask сервер в отдельном процессе"""
    from app import app, init_db
    init_db()
    app.run(host='127.0.0.1', port=5000, debug=False, use_reloader=False)

def test_api_integration():
    """Интеграционный тест API"""

    print("=" * 60)
    print("Интеграционный тест сохранения и загрузки прогресса")
    print("=" * 60)

    base_url = "http://127.0.0.1:5000"

    # Ждем пока сервер запустится
    print("\n1. Ожидание запуска сервера...")
    max_attempts = 10
    for i in range(max_attempts):
        try:
            response = requests.get(base_url, timeout=2)
            if response.status_code == 200:
                print(f"   ✓ Сервер доступен")
                break
        except requests.exceptions.ConnectionError:
            if i < max_attempts - 1:
                print(f"   Попытка {i+1}/{max_attempts}...")
                time.sleep(1)
            else:
                print("   ✗ Не удалось подключиться к серверу")
                return False

    # Проверяем статус БД
    print("\n2. Проверка статуса базы данных...")
    try:
        response = requests.get(f"{base_url}/api/debug/db_status")
        if response.status_code == 200:
            status = response.json()
            print(f"   ✓ БД доступна")
            print(f"   Путь к БД: {status['db_path']}")
            print(f"   БД существует: {status['db_exists']}")
            print(f"   Размер БД: {status['db_size']} байт")
            print(f"   БД доступна для записи: {status['db_writable']}")
            if status['db_exists']:
                print(f"   Таблица существует: {status.get('table_exists', 'N/A')}")
                print(f"   Всего записей: {status.get('total_records', 'N/A')}")
        else:
            print(f"   ⚠ Статус код: {response.status_code}")
    except Exception as e:
        print(f"   ✗ Ошибка: {e}")

    # Тест сохранения прогресса
    print("\n3. Тестирование сохранения прогресса...")
    test_progress = {
        "Огонь": True,
        "Колесо": True,
        "Письменность": False,
        "Земледелие": True,
        "Металлургия": True
    }

    try:
        response = requests.post(
            f"{base_url}/api/progress/save",
            json={"progress": test_progress},
            headers={"Content-Type": "application/json"}
        )

        print(f"   Статус код: {response.status_code}")
        data = response.json()
        print(f"   Ответ: {json.dumps(data, ensure_ascii=False, indent=2)}")

        if response.status_code == 200 and data.get('success'):
            print(f"   ✓ Прогресс сохранен: {data.get('message')}")
            print(f"   Сохранено технологий: {data.get('saved_count')}")
        else:
            print(f"   ✗ Ошибка сохранения: {data.get('message')}")
            return False
    except Exception as e:
        print(f"   ✗ Ошибка: {e}")
        return False

    # Проверяем статус БД после сохранения
    print("\n4. Проверка БД после сохранения...")
    try:
        response = requests.get(f"{base_url}/api/debug/db_status")
        if response.status_code == 200:
            status = response.json()
            print(f"   Всего записей в БД: {status.get('total_records', 'N/A')}")
            print(f"   Записей текущего пользователя: {status.get('current_user_records', 'N/A')}")
            print(f"   IP текущего пользователя: {status.get('current_user_ip', 'N/A')}")
    except Exception as e:
        print(f"   ✗ Ошибка: {e}")

    # Тест загрузки прогресса
    print("\n5. Тестирование загрузки прогресса...")
    try:
        response = requests.get(f"{base_url}/api/progress/load")

        print(f"   Статус код: {response.status_code}")
        data = response.json()
        print(f"   Ответ: {json.dumps(data, ensure_ascii=False, indent=2)}")

        if response.status_code == 200 and data.get('success'):
            loaded_progress = data.get('progress', {})
            print(f"   ✓ Прогресс загружен")
            print(f"   Загружено технологий: {data.get('loaded_count')}")
            print(f"   Технологии: {list(loaded_progress.keys())}")

            # Проверяем корректность данных
            expected_completed = {k: v for k, v in test_progress.items() if v}
            if loaded_progress == expected_completed:
                print("   ✓ Загруженные данные соответствуют сохраненным")
            else:
                print("   ✗ Несоответствие данных!")
                print(f"   Ожидалось: {expected_completed}")
                print(f"   Получено: {loaded_progress}")
                return False
        else:
            print(f"   ✗ Ошибка загрузки: {data.get('message')}")
            return False
    except Exception as e:
        print(f"   ✗ Ошибка: {e}")
        return False

    # Тест обновления прогресса
    print("\n6. Тестирование обновления прогресса...")
    updated_progress = {
        "Огонь": True,
        "Колесо": False,  # Изменено
        "Письменность": True,  # Изменено
        "Бронза": True  # Добавлено
    }

    try:
        response = requests.post(
            f"{base_url}/api/progress/save",
            json={"progress": updated_progress},
            headers={"Content-Type": "application/json"}
        )

        if response.status_code == 200 and response.json().get('success'):
            print(f"   ✓ Прогресс обновлен")

            # Проверяем, что изменения применились
            response = requests.get(f"{base_url}/api/progress/load")
            loaded_progress = response.json().get('progress', {})
            expected_completed = {k: v for k, v in updated_progress.items() if v}

            if loaded_progress == expected_completed:
                print("   ✓ Обновленные данные корректны")
            else:
                print("   ✗ Несоответствие данных после обновления!")
                return False
        else:
            print(f"   ✗ Ошибка обновления")
            return False
    except Exception as e:
        print(f"   ✗ Ошибка: {e}")
        return False

    print("\n" + "=" * 60)
    print("✓ Все интеграционные тесты пройдены успешно!")
    print("=" * 60)
    return True

if __name__ == '__main__':
    # Запускаем сервер в отдельном процессе
    server_process = Process(target=run_server)
    server_process.start()

    try:
        # Даем серверу время на запуск
        time.sleep(2)

        # Запускаем тесты
        success = test_api_integration()

        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\nТестирование прервано")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Ошибка при выполнении тестов: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        # Останавливаем сервер
        server_process.terminate()
        server_process.join()
