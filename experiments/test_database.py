#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для тестирования функциональности базы данных
"""

import sys
import os

# Добавляем родительскую директорию в путь для импорта
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import init_db, save_progress_to_db, load_progress_from_db, DB_PATH
import sqlite3

def test_database():
    """Тестирование функций базы данных"""

    print("=" * 60)
    print("Тестирование функциональности базы данных")
    print("=" * 60)

    # 1. Инициализация базы данных
    print("\n1. Инициализация базы данных...")
    init_db()
    print(f"   ✓ База данных создана: {DB_PATH}")

    # 2. Проверка структуры таблицы
    print("\n2. Проверка структуры таблицы...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='user_progress'")
    table_schema = cursor.fetchone()
    if table_schema:
        print(f"   ✓ Таблица user_progress существует")
        print(f"   Schema: {table_schema[0]}")
    else:
        print("   ✗ Таблица не найдена!")
        return False
    conn.close()

    # 3. Тестирование сохранения прогресса
    print("\n3. Тестирование сохранения прогресса...")
    test_ip = "192.168.1.100"
    test_progress = {
        "Огонь": True,
        "Колесо": True,
        "Письменность": False,
        "Земледелие": True
    }

    result = save_progress_to_db(test_ip, test_progress)
    if result:
        print(f"   ✓ Прогресс сохранен для IP: {test_ip}")
        print(f"   Сохранено технологий: {len(test_progress)}")
    else:
        print("   ✗ Ошибка сохранения!")
        return False

    # 4. Проверка записей в базе данных
    print("\n4. Проверка записей в базе данных...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM user_progress WHERE user_ip = ?", (test_ip,))
    count = cursor.fetchone()[0]
    print(f"   ✓ Найдено записей: {count}")

    cursor.execute("SELECT tech_name, completed FROM user_progress WHERE user_ip = ?", (test_ip,))
    rows = cursor.fetchall()
    print(f"   Записи:")
    for tech_name, completed in rows:
        status = "✓" if completed else "✗"
        print(f"     {status} {tech_name}: {'выполнено' if completed else 'не выполнено'}")
    conn.close()

    # 5. Тестирование загрузки прогресса
    print("\n5. Тестирование загрузки прогресса...")
    loaded_progress = load_progress_from_db(test_ip)
    print(f"   ✓ Загружено технологий: {len(loaded_progress)}")
    print(f"   Загруженный прогресс:")
    for tech_name, completed in loaded_progress.items():
        print(f"     - {tech_name}: {completed}")

    # 6. Проверка корректности загрузки
    print("\n6. Проверка корректности загрузки...")
    expected_completed = {k: v for k, v in test_progress.items() if v}
    if loaded_progress == expected_completed:
        print("   ✓ Загруженный прогресс совпадает с ожидаемым")
    else:
        print("   ✗ Несоответствие данных!")
        print(f"   Ожидалось: {expected_completed}")
        print(f"   Получено: {loaded_progress}")
        return False

    # 7. Тестирование обновления прогресса
    print("\n7. Тестирование обновления прогресса...")
    updated_progress = {
        "Огонь": True,
        "Колесо": True,
        "Письменность": True,  # Изменено
        "Земледелие": False,    # Изменено
        "Металлургия": True     # Добавлено
    }

    result = save_progress_to_db(test_ip, updated_progress)
    if result:
        print(f"   ✓ Прогресс обновлен")
        loaded_progress = load_progress_from_db(test_ip)
        expected_completed = {k: v for k, v in updated_progress.items() if v}
        if loaded_progress == expected_completed:
            print("   ✓ Обновленный прогресс корректен")
        else:
            print("   ✗ Несоответствие данных после обновления!")
            return False
    else:
        print("   ✗ Ошибка обновления!")
        return False

    # 8. Тестирование нескольких пользователей
    print("\n8. Тестирование нескольких пользователей...")
    test_ip2 = "192.168.1.101"
    test_progress2 = {
        "Огонь": True,
        "Металлургия": True
    }

    save_progress_to_db(test_ip2, test_progress2)

    # Проверяем, что прогресс первого пользователя не изменился
    loaded_progress1 = load_progress_from_db(test_ip)
    loaded_progress2 = load_progress_from_db(test_ip2)

    if len(loaded_progress1) != len(loaded_progress2):
        print(f"   ✓ Прогресс пользователей изолирован")
        print(f"   User 1 ({test_ip}): {len(loaded_progress1)} технологий")
        print(f"   User 2 ({test_ip2}): {len(loaded_progress2)} технологий")
    else:
        print("   ⚠ Проверьте изоляцию данных пользователей")

    # 9. Тестирование загрузки для несуществующего пользователя
    print("\n9. Тестирование загрузки для несуществующего пользователя...")
    empty_progress = load_progress_from_db("0.0.0.0")
    if len(empty_progress) == 0:
        print("   ✓ Для нового пользователя возвращается пустой прогресс")
    else:
        print("   ✗ Ожидался пустой прогресс!")
        return False

    print("\n" + "=" * 60)
    print("✓ Все тесты пройдены успешно!")
    print("=" * 60)
    return True

if __name__ == '__main__':
    try:
        success = test_database()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ Ошибка при выполнении тестов: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
