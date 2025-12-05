#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для тестирования Flask приложения и API endpoints
"""

import sys
import os
import time
import requests
import json

# Добавляем родительскую директорию в путь для импорта
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_app():
    """Тестирование Flask приложения"""

    print("=" * 60)
    print("Тестирование Flask приложения и API")
    print("=" * 60)

    base_url = "http://127.0.0.1:5000"

    # Проверяем, что сервер запущен
    print("\n1. Проверка доступности сервера...")
    try:
        response = requests.get(base_url, timeout=2)
        if response.status_code == 200:
            print(f"   ✓ Сервер доступен: {base_url}")
        else:
            print(f"   ✗ Сервер вернул код: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("   ✗ Сервер недоступен! Запустите сервер командой: python app.py")
        print("   Примечание: Этот тест требует запущенного Flask сервера")
        return False
    except Exception as e:
        print(f"   ✗ Ошибка подключения: {e}")
        return False

    # 2. Тестирование API /api/technologies
    print("\n2. Тестирование GET /api/technologies...")
    try:
        response = requests.get(f"{base_url}/api/technologies")
        if response.status_code == 200:
            data = response.json()
            tech_count = len(data.get('технологии', []))
            print(f"   ✓ API работает, найдено технологий: {tech_count}")
        else:
            print(f"   ✗ Ошибка API: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ✗ Ошибка: {e}")
        return False

    # 3. Тестирование API сохранения прогресса
    print("\n3. Тестирование POST /api/progress/save...")
    test_progress = {
        "Огонь": True,
        "Колесо": True,
        "Письменность": False
    }

    try:
        response = requests.post(
            f"{base_url}/api/progress/save",
            json={"progress": test_progress},
            headers={"Content-Type": "application/json"}
        )
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print(f"   ✓ Прогресс сохранен: {data.get('message')}")
            else:
                print(f"   ✗ Ошибка: {data.get('message')}")
                return False
        else:
            print(f"   ✗ Ошибка API: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ✗ Ошибка: {e}")
        return False

    # 4. Тестирование API загрузки прогресса
    print("\n4. Тестирование GET /api/progress/load...")
    try:
        response = requests.get(f"{base_url}/api/progress/load")
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                loaded_progress = data.get('progress', {})
                print(f"   ✓ Прогресс загружен: {len(loaded_progress)} технологий")
                print(f"   Загружено: {list(loaded_progress.keys())}")

                # Проверяем, что загруженный прогресс соответствует сохраненному
                expected = {k: v for k, v in test_progress.items() if v}
                if loaded_progress == expected:
                    print("   ✓ Загруженные данные соответствуют сохраненным")
                else:
                    print("   ⚠ Загруженные данные не совпадают полностью")
                    print(f"   Ожидалось: {expected}")
                    print(f"   Получено: {loaded_progress}")
            else:
                print(f"   ✗ Ошибка: {data.get('message')}")
                return False
        else:
            print(f"   ✗ Ошибка API: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ✗ Ошибка: {e}")
        return False

    # 5. Тестирование API древа технологий
    print("\n5. Тестирование GET /api/tree/<tech_name>...")
    try:
        # Пробуем получить дерево для первой технологии
        response = requests.get(f"{base_url}/api/technologies")
        data = response.json()
        if data.get('технологии') and len(data['технологии']) > 0:
            test_tech = data['технологии'][0]['название']
            print(f"   Тестируем дерево для: {test_tech}")

            response = requests.get(f"{base_url}/api/tree/{test_tech}")
            if response.status_code == 200:
                tree_data = response.json()
                print(f"   ✓ Получено дерево технологий")
                print(f"   Центр: {tree_data.get('center')}")
                print(f"   Узлов: {len(tree_data.get('nodes', []))}")
                print(f"   Связей: {len(tree_data.get('edges', []))}")
            else:
                print(f"   ✗ Ошибка API: {response.status_code}")
                return False
        else:
            print("   ⚠ Нет технологий для тестирования")
    except Exception as e:
        print(f"   ✗ Ошибка: {e}")
        return False

    print("\n" + "=" * 60)
    print("✓ Все API тесты пройдены успешно!")
    print("=" * 60)
    return True

if __name__ == '__main__':
    try:
        success = test_app()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ Ошибка при выполнении тестов: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
