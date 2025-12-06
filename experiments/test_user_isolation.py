#!/usr/bin/env python3
"""
Тест изоляции пользователей - проверяем, что прогресс разных пользователей не смешивается
"""
import os
import sys
import sqlite3

# Добавляем путь к корневой директории
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import save_progress_to_db, load_progress_from_db, DB_PATH

def test_user_isolation():
    """Тест изоляции данных разных пользователей"""
    print("=== Тест изоляции пользователей ===\n")

    # Удаляем тестовую БД если существует
    test_db = 'test_user_isolation.db'
    if os.path.exists(test_db):
        os.remove(test_db)

    # Временно меняем путь к БД
    import app
    original_db_path = app.DB_PATH
    app.DB_PATH = test_db

    try:
        # Данные пользователя 1
        user1_ip = "192.168.1.100"
        user1_progress = {
            "Письменность": True,
            "Земледелие": True,
            "Колесо": True
        }

        # Данные пользователя 2
        user2_ip = "192.168.1.200"
        user2_progress = {
            "Математика": True,
            "Астрономия": True,
            "Философия": True
        }

        # Данные пользователя 3
        user3_ip = "10.0.0.50"
        user3_progress = {
            "Металлургия": True,
            "Кузнечное дело": True
        }

        print("1. Сохраняем прогресс пользователя 1")
        result = save_progress_to_db(user1_ip, user1_progress)
        print(f"   Результат: {result}")
        assert result, "Ошибка сохранения прогресса пользователя 1"

        print("\n2. Сохраняем прогресс пользователя 2")
        result = save_progress_to_db(user2_ip, user2_progress)
        print(f"   Результат: {result}")
        assert result, "Ошибка сохранения прогресса пользователя 2"

        print("\n3. Сохраняем прогресс пользователя 3")
        result = save_progress_to_db(user3_ip, user3_progress)
        print(f"   Результат: {result}")
        assert result, "Ошибка сохранения прогресса пользователя 3"

        # Проверяем загрузку
        print("\n4. Загружаем прогресс пользователя 1")
        loaded1 = load_progress_from_db(user1_ip)
        print(f"   Загружено: {loaded1}")
        assert loaded1 == user1_progress, f"Прогресс пользователя 1 не совпадает! Ожидалось {user1_progress}, получено {loaded1}"

        print("\n5. Загружаем прогресс пользователя 2")
        loaded2 = load_progress_from_db(user2_ip)
        print(f"   Загружено: {loaded2}")
        assert loaded2 == user2_progress, f"Прогресс пользователя 2 не совпадает! Ожидалось {user2_progress}, получено {loaded2}"

        print("\n6. Загружаем прогресс пользователя 3")
        loaded3 = load_progress_from_db(user3_ip)
        print(f"   Загружено: {loaded3}")
        assert loaded3 == user3_progress, f"Прогресс пользователя 3 не совпадает! Ожидалось {user3_progress}, получено {loaded3}"

        # Проверяем что в БД действительно разные записи
        print("\n7. Проверяем записи в БД")
        conn = sqlite3.connect(test_db)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(DISTINCT user_ip) FROM user_progress")
        unique_users = cursor.fetchone()[0]
        print(f"   Уникальных пользователей в БД: {unique_users}")
        assert unique_users == 3, f"Ожидалось 3 уникальных пользователя, получено {unique_users}"

        cursor.execute("SELECT user_ip, COUNT(*) FROM user_progress GROUP BY user_ip")
        for row in cursor.fetchall():
            print(f"   IP {row[0]}: {row[1]} технологий")

        conn.close()

        # Обновляем прогресс пользователя 1 и проверяем что другие не изменились
        print("\n8. Обновляем прогресс пользователя 1")
        user1_updated = {
            "Письменность": True,
            "Земледелие": True,
            "Колесо": True,
            "Бронза": True,
            "Железо": True
        }
        result = save_progress_to_db(user1_ip, user1_updated)
        print(f"   Результат: {result}")

        print("\n9. Проверяем что прогресс пользователя 2 не изменился")
        loaded2_check = load_progress_from_db(user2_ip)
        print(f"   Загружено: {loaded2_check}")
        assert loaded2_check == user2_progress, f"Прогресс пользователя 2 был изменен! Ожидалось {user2_progress}, получено {loaded2_check}"

        print("\n10. Проверяем что прогресс пользователя 3 не изменился")
        loaded3_check = load_progress_from_db(user3_ip)
        print(f"   Загружено: {loaded3_check}")
        assert loaded3_check == user3_progress, f"Прогресс пользователя 3 был изменен! Ожидалось {user3_progress}, получено {loaded3_check}"

        print("\n✅ Все тесты пройдены успешно!")
        print("\nИзоляция пользователей работает корректно:")
        print("- Каждый пользователь имеет свой изолированный прогресс")
        print("- Изменение прогресса одного пользователя не влияет на других")
        print("- Данные корректно сохраняются и загружаются по IP адресу")

        return True

    finally:
        # Восстанавливаем оригинальный путь к БД
        app.DB_PATH = original_db_path

        # Удаляем тестовую БД
        if os.path.exists(test_db):
            os.remove(test_db)

if __name__ == '__main__':
    try:
        test_user_isolation()
    except AssertionError as e:
        print(f"\n❌ Тест провален: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Ошибка при выполнении теста: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
