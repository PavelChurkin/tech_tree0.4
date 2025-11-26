"""
Скрипт миграции данных из JSON в SQLite базу данных
"""

import json
import sqlite3
import sys
from pathlib import Path
from datetime import datetime


def create_tables(cursor):
    """Создание всех таблиц базы данных"""

    print("Создание таблиц...")

    # Таблица технологий
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS technologies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            description TEXT,
            category_id INTEGER,
            difficulty INTEGER DEFAULT 1 CHECK(difficulty BETWEEN 1 AND 5),
            icon TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("CREATE INDEX IF NOT EXISTS idx_tech_name ON technologies(name)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_tech_category ON technologies(category_id)")

    # Таблица зависимостей
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS technology_dependencies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            technology_id INTEGER NOT NULL,
            depends_on_id INTEGER NOT NULL,
            dependency_type TEXT DEFAULT 'required' CHECK(dependency_type IN ('required', 'optional')),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (technology_id) REFERENCES technologies(id) ON DELETE CASCADE,
            FOREIGN KEY (depends_on_id) REFERENCES technologies(id) ON DELETE CASCADE,
            UNIQUE(technology_id, depends_on_id)
        )
    """)

    cursor.execute("CREATE INDEX IF NOT EXISTS idx_tech_deps_tech ON technology_dependencies(technology_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_tech_deps_parent ON technology_dependencies(depends_on_id)")

    # Таблица прогресса пользователя
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL DEFAULT 'default',
            technology_id INTEGER NOT NULL,
            is_unlocked BOOLEAN DEFAULT 0,
            unlocked_at TIMESTAMP,
            notes TEXT,
            FOREIGN KEY (technology_id) REFERENCES technologies(id) ON DELETE CASCADE,
            UNIQUE(user_id, technology_id)
        )
    """)

    cursor.execute("CREATE INDEX IF NOT EXISTS idx_progress_user ON user_progress(user_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_progress_tech ON user_progress(technology_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_progress_unlocked ON user_progress(is_unlocked)")

    # Триггер для обновления updated_at
    cursor.execute("""
        CREATE TRIGGER IF NOT EXISTS update_tech_timestamp
        AFTER UPDATE ON technologies
        BEGIN
            UPDATE technologies SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
        END
    """)

    # Триггер для автоматического обновления unlocked_at
    cursor.execute("""
        CREATE TRIGGER IF NOT EXISTS update_unlock_timestamp
        AFTER UPDATE OF is_unlocked ON user_progress
        WHEN NEW.is_unlocked = 1 AND OLD.is_unlocked = 0
        BEGIN
            UPDATE user_progress SET unlocked_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
        END
    """)

    print("✓ Таблицы созданы успешно")


def migrate_json_to_sqlite(json_file_path, db_path):
    """Миграция данных из JSON в SQLite базу"""

    print(f"\nНачало миграции:")
    print(f"  JSON файл: {json_file_path}")
    print(f"  База данных: {db_path}")
    print()

    # Проверяем существование JSON файла
    if not Path(json_file_path).exists():
        print(f"ОШИБКА: JSON файл '{json_file_path}' не найден!")
        return False

    # Загружаем JSON
    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print(f"✓ JSON файл загружен ({len(data.get('технологии', []))} технологий)")
    except Exception as e:
        print(f"ОШИБКА при загрузке JSON: {e}")
        return False

    # Подключаемся к БД
    try:
        conn = sqlite3.connect(db_path)
        conn.execute("PRAGMA foreign_keys = ON")
        cursor = conn.cursor()
        print(f"✓ Подключение к базе данных установлено")
    except Exception as e:
        print(f"ОШИБКА при подключении к БД: {e}")
        return False

    try:
        # Создаем таблицы
        create_tables(cursor)

        # Словарь для маппинга названий на ID
        tech_name_to_id = {}

        # Шаг 1: Импортируем все технологии
        print("\nИмпорт технологий...")
        skipped_duplicates = []

        for i, tech in enumerate(data['технологии'], 1):
            try:
                cursor.execute("""
                    INSERT INTO technologies (name, description)
                    VALUES (?, ?)
                """, (tech['название'], tech['описание']))

                tech_id = cursor.lastrowid
                tech_name_to_id[tech['название']] = tech_id

                if i % 50 == 0:
                    print(f"  Импортировано {i} технологий...")

            except sqlite3.IntegrityError as e:
                # Обрабатываем дубликаты - используем существующую запись
                if 'UNIQUE constraint failed' in str(e):
                    skipped_duplicates.append(tech['название'])
                    cursor.execute("SELECT id FROM technologies WHERE name = ?", (tech['название'],))
                    tech_id = cursor.fetchone()[0]
                    tech_name_to_id[tech['название']] = tech_id
                else:
                    raise

        print(f"✓ Импортировано {len(tech_name_to_id)} технологий")

        if skipped_duplicates:
            print(f"⚠ Пропущено дубликатов: {len(skipped_duplicates)}")
            for dup in skipped_duplicates:
                print(f"  - {dup}")

        # Шаг 2: Импортируем зависимости
        print("\nИмпорт зависимостей...")
        dep_count = 0
        warnings = []

        for tech in data['технологии']:
            tech_id = tech_name_to_id[tech['название']]

            for dependency_name in tech['условия']:
                if dependency_name in tech_name_to_id:
                    depends_on_id = tech_name_to_id[dependency_name]

                    try:
                        cursor.execute("""
                            INSERT INTO technology_dependencies (technology_id, depends_on_id)
                            VALUES (?, ?)
                        """, (tech_id, depends_on_id))
                        dep_count += 1
                    except sqlite3.IntegrityError:
                        warnings.append(f"Дублирующаяся зависимость: {tech['название']} -> {dependency_name}")
                else:
                    warnings.append(f"Зависимость '{dependency_name}' не найдена для '{tech['название']}'")

        print(f"✓ Импортировано {dep_count} зависимостей")

        if warnings:
            print(f"\n⚠ Предупреждения ({len(warnings)}):")
            for warning in warnings[:10]:  # Показываем первые 10
                print(f"  - {warning}")
            if len(warnings) > 10:
                print(f"  ... и еще {len(warnings) - 10} предупреждений")

        # Шаг 3: Создаем начальный прогресс для пользователя по умолчанию
        print("\nСоздание прогресса пользователя...")
        for tech_id in tech_name_to_id.values():
            cursor.execute("""
                INSERT INTO user_progress (user_id, technology_id, is_unlocked)
                VALUES ('default', ?, 0)
            """, (tech_id,))

        print(f"✓ Прогресс инициализирован для {len(tech_name_to_id)} технологий")

        # Коммитим транзакцию
        conn.commit()
        print("\n✓ Миграция завершена успешно!")

        # Вывод статистики
        print("\nСтатистика базы данных:")

        cursor.execute("SELECT COUNT(*) FROM technologies")
        tech_count = cursor.fetchone()[0]
        print(f"  Технологий: {tech_count}")

        cursor.execute("SELECT COUNT(*) FROM technology_dependencies")
        dep_count = cursor.fetchone()[0]
        print(f"  Зависимостей: {dep_count}")

        cursor.execute("SELECT COUNT(*) FROM user_progress")
        progress_count = cursor.fetchone()[0]
        print(f"  Записей прогресса: {progress_count}")

        # Топ-5 технологий с наибольшим количеством зависимостей
        print("\nТоп-5 технологий с наибольшим количеством зависимостей:")
        cursor.execute("""
            SELECT t.name, COUNT(td.depends_on_id) as dep_count
            FROM technologies t
            LEFT JOIN technology_dependencies td ON t.id = td.technology_id
            GROUP BY t.id, t.name
            ORDER BY dep_count DESC
            LIMIT 5
        """)

        for row in cursor.fetchall():
            print(f"  - {row[0]}: {row[1]} зависимостей")

        # Технологии без зависимостей (корневые)
        cursor.execute("""
            SELECT COUNT(*)
            FROM technologies t
            LEFT JOIN technology_dependencies td ON t.id = td.technology_id
            WHERE td.id IS NULL
        """)
        root_count = cursor.fetchone()[0]
        print(f"\nКорневых технологий (без зависимостей): {root_count}")

        conn.close()
        return True

    except Exception as e:
        print(f"\n❌ ОШИБКА при миграции: {e}")
        conn.rollback()
        conn.close()
        return False


def export_sqlite_to_json(db_path, json_file_path):
    """Экспорт данных из SQLite обратно в JSON формат"""

    print(f"\nЭкспорт из SQLite в JSON:")
    print(f"  База данных: {db_path}")
    print(f"  JSON файл: {json_file_path}")
    print()

    # Проверяем существование БД
    if not Path(db_path).exists():
        print(f"ОШИБКА: База данных '{db_path}' не найдена!")
        return False

    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        print("✓ Подключение к базе данных установлено")

        # Получаем все технологии
        cursor.execute("""
            SELECT id, name, description
            FROM technologies
            ORDER BY name
        """)

        technologies = []
        tech_id_to_data = {}

        for row in cursor.fetchall():
            tech_data = {
                "название": row['name'],
                "описание": row['description'] or "",
                "условия": []
            }
            technologies.append(tech_data)
            tech_id_to_data[row['id']] = tech_data

        print(f"✓ Загружено {len(technologies)} технологий")

        # Получаем все зависимости
        cursor.execute("""
            SELECT td.technology_id, t_dep.name
            FROM technology_dependencies td
            JOIN technologies t_dep ON td.depends_on_id = t_dep.id
            ORDER BY td.technology_id
        """)

        dep_count = 0
        for row in cursor.fetchall():
            if row['technology_id'] in tech_id_to_data:
                tech_id_to_data[row['technology_id']]["условия"].append(row['name'])
                dep_count += 1

        print(f"✓ Загружено {dep_count} зависимостей")

        # Формируем результат
        result = {
            "технологии": technologies
        }

        # Сохраняем в JSON
        with open(json_file_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        conn.close()

        print(f"✓ Экспорт завершен успешно!")
        print(f"  Экспортировано {len(technologies)} технологий в {json_file_path}")

        return True

    except Exception as e:
        print(f"\n❌ ОШИБКА при экспорте: {e}")
        return False


def main():
    """Главная функция"""

    print("=" * 60)
    print("  Миграция данных технологического древа")
    print("=" * 60)

    if len(sys.argv) < 2:
        print("\nИспользование:")
        print("  python migrate_to_sqlite.py import [json_file] [db_file]")
        print("  python migrate_to_sqlite.py export [db_file] [json_file]")
        print("\nПримеры:")
        print("  python migrate_to_sqlite.py import techno2.json tech_tree.db")
        print("  python migrate_to_sqlite.py export tech_tree.db techno_export.json")
        return

    command = sys.argv[1].lower()

    if command == 'import':
        json_file = sys.argv[2] if len(sys.argv) > 2 else 'techno2.json'
        db_file = sys.argv[3] if len(sys.argv) > 3 else 'tech_tree.db'

        success = migrate_json_to_sqlite(json_file, db_file)

        if success:
            print("\n" + "=" * 60)
            print("  Миграция завершена успешно!")
            print("=" * 60)
        else:
            print("\n" + "=" * 60)
            print("  Миграция завершилась с ошибками")
            print("=" * 60)
            sys.exit(1)

    elif command == 'export':
        db_file = sys.argv[2] if len(sys.argv) > 2 else 'tech_tree.db'
        json_file = sys.argv[3] if len(sys.argv) > 3 else 'techno_export.json'

        success = export_sqlite_to_json(db_file, json_file)

        if success:
            print("\n" + "=" * 60)
            print("  Экспорт завершен успешно!")
            print("=" * 60)
        else:
            print("\n" + "=" * 60)
            print("  Экспорт завершился с ошибками")
            print("=" * 60)
            sys.exit(1)

    else:
        print(f"\nНеизвестная команда: {command}")
        print("Используйте 'import' или 'export'")
        sys.exit(1)


if __name__ == "__main__":
    main()
