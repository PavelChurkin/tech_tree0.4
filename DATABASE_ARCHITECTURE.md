# Архитектура базы данных SQLite для древа технологий

## Содержание
1. [Введение](#введение)
2. [Варианты архитектуры](#варианты-архитектуры)
3. [Рекомендуемый вариант](#рекомендуемый-вариант)
4. [Миграция данных](#миграция-данных)
5. [Примеры запросов](#примеры-запросов)
6. [Интеграция с существующим кодом](#интеграция-с-существующим-кодом)

---

## Введение

Этот документ предлагает несколько вариантов архитектуры базы данных SQLite для замены JSON-хранилища технологического древа.

### Текущая структура JSON:
```json
{
  "технологии": [
    {
      "название": "Огонь",
      "описание": "Навык добывания и использования огня...",
      "условия": []
    },
    {
      "название": "Колесо",
      "описание": "Изобретение колеса...",
      "условия": ["Резец"]
    }
  ]
}
```

### Требования к базе данных:
- Хранение технологий с названиями и описаниями
- Поддержка иерархических связей (условия/зависимости)
- Быстрый поиск родителей и потомков
- Поддержка прогресса пользователя
- Возможность расширения (метаданные, версионность)

---

## Варианты архитектуры

### Вариант 1: Простая нормализованная схема

#### Описание
Базовая нормализованная схема с отдельной таблицей для связей между технологиями.

#### Схема

```
┌─────────────────────────────┐
│     technologies            │
├─────────────────────────────┤
│ id (INTEGER PRIMARY KEY)    │
│ name (TEXT UNIQUE NOT NULL) │
│ description (TEXT)          │
│ created_at (TIMESTAMP)      │
│ updated_at (TIMESTAMP)      │
└─────────────────────────────┘
           │
           │ 1:N
           ▼
┌─────────────────────────────┐
│  technology_dependencies    │
├─────────────────────────────┤
│ id (INTEGER PRIMARY KEY)    │
│ technology_id (INTEGER)     │ ───┐
│ depends_on_id (INTEGER)     │ ───┼─> FK к technologies.id
│ created_at (TIMESTAMP)      │    │
└─────────────────────────────┘    │
           ▲                        │
           └────────────────────────┘
```

#### SQL DDL

```sql
-- Создание таблицы технологий
CREATE TABLE technologies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Индекс для быстрого поиска по имени
CREATE INDEX idx_tech_name ON technologies(name);

-- Создание таблицы зависимостей
CREATE TABLE technology_dependencies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    technology_id INTEGER NOT NULL,
    depends_on_id INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (technology_id) REFERENCES technologies(id) ON DELETE CASCADE,
    FOREIGN KEY (depends_on_id) REFERENCES technologies(id) ON DELETE CASCADE,
    UNIQUE(technology_id, depends_on_id)
);

-- Индексы для быстрого поиска зависимостей
CREATE INDEX idx_tech_deps_tech ON technology_dependencies(technology_id);
CREATE INDEX idx_tech_deps_parent ON technology_dependencies(depends_on_id);

-- Триггер для обновления updated_at
CREATE TRIGGER update_tech_timestamp
AFTER UPDATE ON technologies
BEGIN
    UPDATE technologies SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;
```

#### Преимущества
- Простая и понятная структура
- Легко добавлять новые технологии
- Нет дублирования данных
- Легко удалять и изменять зависимости

#### Недостатки
- Требует JOIN для получения списка условий
- Медленнее для глубоких рекурсивных запросов
- Не хранит метаданные о связях

---

### Вариант 2: Расширенная схема с метаданными

#### Описание
Расширенная версия первого варианта с дополнительными таблицами для метаданных, категорий и прогресса.

#### Схема

```
┌─────────────────────────────┐
│       categories            │
├─────────────────────────────┤
│ id (INTEGER PRIMARY KEY)    │
│ name (TEXT UNIQUE)          │
│ description (TEXT)          │
│ color (TEXT)                │
└─────────────────────────────┘
           │
           │ 1:N
           ▼
┌─────────────────────────────┐
│     technologies            │
├─────────────────────────────┤
│ id (INTEGER PRIMARY KEY)    │
│ name (TEXT UNIQUE NOT NULL) │
│ description (TEXT)          │
│ category_id (INTEGER)       │ ───> FK к categories.id
│ difficulty (INTEGER)        │
│ icon (TEXT)                 │
│ created_at (TIMESTAMP)      │
│ updated_at (TIMESTAMP)      │
└─────────────────────────────┘
           │
           │ 1:N                    1:N
           ▼                         │
┌─────────────────────────────┐     │
│  technology_dependencies    │     │
├─────────────────────────────┤     │
│ id (INTEGER PRIMARY KEY)    │     │
│ technology_id (INTEGER)     │     │
│ depends_on_id (INTEGER)     │     │
│ dependency_type (TEXT)      │     │
│ created_at (TIMESTAMP)      │     │
└─────────────────────────────┘     │
                                     │
                                     ▼
                        ┌─────────────────────────────┐
                        │    user_progress            │
                        ├─────────────────────────────┤
                        │ id (INTEGER PRIMARY KEY)    │
                        │ user_id (TEXT)              │
                        │ technology_id (INTEGER)     │ ───> FK
                        │ is_unlocked (BOOLEAN)       │
                        │ unlocked_at (TIMESTAMP)     │
                        │ notes (TEXT)                │
                        └─────────────────────────────┘
```

#### SQL DDL

```sql
-- Таблица категорий технологий
CREATE TABLE categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    description TEXT,
    color TEXT DEFAULT '#808080'
);

-- Основная таблица технологий
CREATE TABLE technologies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    description TEXT,
    category_id INTEGER,
    difficulty INTEGER DEFAULT 1 CHECK(difficulty BETWEEN 1 AND 5),
    icon TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE SET NULL
);

-- Индексы
CREATE INDEX idx_tech_name ON technologies(name);
CREATE INDEX idx_tech_category ON technologies(category_id);
CREATE INDEX idx_tech_difficulty ON technologies(difficulty);

-- Таблица зависимостей с типами
CREATE TABLE technology_dependencies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    technology_id INTEGER NOT NULL,
    depends_on_id INTEGER NOT NULL,
    dependency_type TEXT DEFAULT 'required' CHECK(dependency_type IN ('required', 'optional')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (technology_id) REFERENCES technologies(id) ON DELETE CASCADE,
    FOREIGN KEY (depends_on_id) REFERENCES technologies(id) ON DELETE CASCADE,
    UNIQUE(technology_id, depends_on_id)
);

CREATE INDEX idx_tech_deps_tech ON technology_dependencies(technology_id);
CREATE INDEX idx_tech_deps_parent ON technology_dependencies(depends_on_id);

-- Таблица прогресса пользователя
CREATE TABLE user_progress (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL DEFAULT 'default',
    technology_id INTEGER NOT NULL,
    is_unlocked BOOLEAN DEFAULT 0,
    unlocked_at TIMESTAMP,
    notes TEXT,
    FOREIGN KEY (technology_id) REFERENCES technologies(id) ON DELETE CASCADE,
    UNIQUE(user_id, technology_id)
);

CREATE INDEX idx_progress_user ON user_progress(user_id);
CREATE INDEX idx_progress_tech ON user_progress(technology_id);
CREATE INDEX idx_progress_unlocked ON user_progress(is_unlocked);

-- Триггеры
CREATE TRIGGER update_tech_timestamp
AFTER UPDATE ON technologies
BEGIN
    UPDATE technologies SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER update_unlock_timestamp
AFTER UPDATE OF is_unlocked ON user_progress
WHEN NEW.is_unlocked = 1 AND OLD.is_unlocked = 0
BEGIN
    UPDATE user_progress SET unlocked_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;
```

#### Преимущества
- Полная поддержка всех функций приложения
- Разделение прогресса по пользователям
- Категоризация технологий
- Гибкость для будущих расширений
- Метаданные о связях (типы зависимостей)

#### Недостатки
- Более сложная структура
- Требует больше таблиц и JOIN-ов
- Избыточна для простых случаев

---

### Вариант 3: Closure Table (таблица замыкания)

#### Описание
Специализированная структура для эффективной работы с иерархиями и быстрого поиска всех предков/потомков.

#### Схема

```
┌─────────────────────────────┐
│     technologies            │
├─────────────────────────────┤
│ id (INTEGER PRIMARY KEY)    │
│ name (TEXT UNIQUE NOT NULL) │
│ description (TEXT)          │
└─────────────────────────────┘
           │
           │ 1:N (для обоих FK)
           ▼
┌─────────────────────────────┐
│  technology_closure         │
├─────────────────────────────┤
│ ancestor_id (INTEGER)       │ ───┐
│ descendant_id (INTEGER)     │ ───┼─> FK к technologies.id
│ depth (INTEGER)             │    │
│ PRIMARY KEY (ancestor, desc)│    │
└─────────────────────────────┘    │
           ▲                        │
           └────────────────────────┘
```

#### SQL DDL

```sql
-- Таблица технологий
CREATE TABLE technologies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_tech_name ON technologies(name);

-- Closure table для хранения всех путей в графе
CREATE TABLE technology_closure (
    ancestor_id INTEGER NOT NULL,
    descendant_id INTEGER NOT NULL,
    depth INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (ancestor_id, descendant_id),
    FOREIGN KEY (ancestor_id) REFERENCES technologies(id) ON DELETE CASCADE,
    FOREIGN KEY (descendant_id) REFERENCES technologies(id) ON DELETE CASCADE
);

-- Индексы для быстрого поиска
CREATE INDEX idx_closure_ancestor ON technology_closure(ancestor_id);
CREATE INDEX idx_closure_descendant ON technology_closure(descendant_id);
CREATE INDEX idx_closure_depth ON technology_closure(depth);

-- Таблица прямых зависимостей (для редактирования)
CREATE TABLE technology_dependencies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    technology_id INTEGER NOT NULL,
    depends_on_id INTEGER NOT NULL,
    FOREIGN KEY (technology_id) REFERENCES technologies(id) ON DELETE CASCADE,
    FOREIGN KEY (depends_on_id) REFERENCES technologies(id) ON DELETE CASCADE,
    UNIQUE(technology_id, depends_on_id)
);

-- Триггер для обновления closure table при добавлении связи
CREATE TRIGGER add_dependency_closure
AFTER INSERT ON technology_dependencies
BEGIN
    -- Добавляем прямую связь
    INSERT OR IGNORE INTO technology_closure (ancestor_id, descendant_id, depth)
    VALUES (NEW.depends_on_id, NEW.technology_id, 1);

    -- Добавляем транзитивные связи (все предки зависимости -> технология)
    INSERT OR IGNORE INTO technology_closure (ancestor_id, descendant_id, depth)
    SELECT tc.ancestor_id, NEW.technology_id, tc.depth + 1
    FROM technology_closure tc
    WHERE tc.descendant_id = NEW.depends_on_id;

    -- Добавляем транзитивные связи (зависимость -> все потомки технологии)
    INSERT OR IGNORE INTO technology_closure (ancestor_id, descendant_id, depth)
    SELECT NEW.depends_on_id, tc.descendant_id, tc.depth + 1
    FROM technology_closure tc
    WHERE tc.ancestor_id = NEW.technology_id;

    -- Добавляем полные транзитивные пути
    INSERT OR IGNORE INTO technology_closure (ancestor_id, descendant_id, depth)
    SELECT tc1.ancestor_id, tc2.descendant_id, tc1.depth + tc2.depth + 1
    FROM technology_closure tc1, technology_closure tc2
    WHERE tc1.descendant_id = NEW.depends_on_id
    AND tc2.ancestor_id = NEW.technology_id;
END;

-- Триггер для удаления из closure table
CREATE TRIGGER remove_dependency_closure
BEFORE DELETE ON technology_dependencies
BEGIN
    DELETE FROM technology_closure
    WHERE (ancestor_id, descendant_id) IN (
        SELECT tc1.ancestor_id, tc2.descendant_id
        FROM technology_closure tc1
        JOIN technology_closure tc2
        WHERE tc1.descendant_id = OLD.depends_on_id
        AND tc2.ancestor_id = OLD.technology_id
        AND NOT EXISTS (
            SELECT 1 FROM technology_dependencies td
            JOIN technology_closure tc3 ON tc3.descendant_id = td.depends_on_id
            JOIN technology_closure tc4 ON tc4.ancestor_id = td.technology_id
            WHERE tc3.ancestor_id = tc1.ancestor_id
            AND tc4.descendant_id = tc2.descendant_id
            AND td.id != OLD.id
        )
    );
END;
```

#### Преимущества
- Очень быстрый поиск всех предков/потомков (один SELECT без рекурсии)
- Оптимально для глубоких иерархий
- Легко найти все пути между узлами
- Быстрое определение доступности технологии

#### Недостатки
- Более сложная схема
- Триггеры усложняют обслуживание
- Занимает больше места (хранятся все пути)
- Сложнее для понимания новым разработчикам

---

### Вариант 4: Гибридная схема с JSON

#### Описание
Компромиссный вариант, использующий SQLite с некоторыми полями в JSON формате для гибкости.

#### SQL DDL

```sql
-- Основная таблица с JSON полями
CREATE TABLE technologies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    description TEXT,
    -- Хранение зависимостей как JSON массив
    dependencies_json TEXT DEFAULT '[]',
    -- Дополнительные метаданные
    metadata_json TEXT DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_tech_name ON technologies(name);

-- Виртуальная таблица для полнотекстового поиска
CREATE VIRTUAL TABLE technologies_fts USING fts5(
    name,
    description,
    content=technologies,
    content_rowid=id
);

-- Триггеры для синхронизации FTS
CREATE TRIGGER tech_fts_insert AFTER INSERT ON technologies
BEGIN
    INSERT INTO technologies_fts(rowid, name, description)
    VALUES (NEW.id, NEW.name, NEW.description);
END;

CREATE TRIGGER tech_fts_update AFTER UPDATE ON technologies
BEGIN
    UPDATE technologies_fts
    SET name = NEW.name, description = NEW.description
    WHERE rowid = NEW.id;
END;

CREATE TRIGGER tech_fts_delete AFTER DELETE ON technologies
BEGIN
    DELETE FROM technologies_fts WHERE rowid = OLD.id;
END;

-- Материализованное представление для часто используемых запросов
CREATE TABLE tech_stats (
    technology_id INTEGER PRIMARY KEY,
    direct_parents_count INTEGER DEFAULT 0,
    direct_children_count INTEGER DEFAULT 0,
    total_depth INTEGER DEFAULT 0,
    FOREIGN KEY (technology_id) REFERENCES technologies(id) ON DELETE CASCADE
);

-- Таблица прогресса
CREATE TABLE user_progress (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL DEFAULT 'default',
    technology_id INTEGER NOT NULL,
    is_unlocked BOOLEAN DEFAULT 0,
    unlocked_at TIMESTAMP,
    FOREIGN KEY (technology_id) REFERENCES technologies(id) ON DELETE CASCADE,
    UNIQUE(user_id, technology_id)
);

CREATE INDEX idx_progress_user ON user_progress(user_id);
```

#### Преимущества
- Простота миграции с JSON
- Гибкость для нестандартных полей
- Полнотекстовый поиск (FTS5)
- Меньше JOIN-ов

#### Недостатки
- Сложнее запросы для работы с зависимостями
- JSON поля не индексируются эффективно
- Смешивание парадигм (реляционная + документная)

---

## Рекомендуемый вариант

### Вариант 2 (Расширенная схема с метаданными) + элементы из Варианта 3

Рекомендую использовать **Вариант 2** как основу с добавлением некоторых оптимизаций из **Варианта 3** для критичных запросов.

#### Обоснование:

1. **Полнота функциональности**: Покрывает все текущие требования + расширения
2. **Баланс сложности/производительности**: Не слишком сложен, но эффективен
3. **Масштабируемость**: Легко добавлять новые фичи
4. **Поддержка пользователей**: Разделение прогресса
5. **Производительность**: Для графа из ~250 технологий достаточно быстр

#### Оптимизация для поиска предков/потомков:

Для ускорения рекурсивных запросов используем **Recursive CTE** (поддерживается в SQLite 3.8.3+):

```sql
-- Создаем материализованное представление для кеширования результатов
CREATE TABLE technology_tree_cache (
    technology_id INTEGER NOT NULL,
    ancestor_id INTEGER,
    depth INTEGER NOT NULL,
    PRIMARY KEY (technology_id, ancestor_id),
    FOREIGN KEY (technology_id) REFERENCES technologies(id) ON DELETE CASCADE,
    FOREIGN KEY (ancestor_id) REFERENCES technologies(id) ON DELETE CASCADE
);

CREATE INDEX idx_tree_cache_tech ON technology_tree_cache(technology_id);
CREATE INDEX idx_tree_cache_ancestor ON technology_tree_cache(ancestor_id);
```

---

## Миграция данных

### Скрипт миграции с JSON на SQLite

```python
import json
import sqlite3
from datetime import datetime

def migrate_json_to_sqlite(json_file_path, db_path):
    """Миграция данных из JSON в SQLite базу"""

    # Загружаем JSON
    with open(json_file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Подключаемся к БД
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Создаем таблицы (используем схему из Варианта 2)
    create_tables(cursor)

    # Словарь для маппинга названий на ID
    tech_name_to_id = {}

    # Шаг 1: Импортируем все технологии
    print("Импорт технологий...")
    for tech in data['технологии']:
        cursor.execute("""
            INSERT INTO technologies (name, description)
            VALUES (?, ?)
        """, (tech['название'], tech['описание']))

        tech_id = cursor.lastrowid
        tech_name_to_id[tech['название']] = tech_id

    print(f"Импортировано {len(tech_name_to_id)} технологий")

    # Шаг 2: Импортируем зависимости
    print("Импорт зависимостей...")
    dep_count = 0
    for tech in data['технологии']:
        tech_id = tech_name_to_id[tech['название']]

        for dependency_name in tech['условия']:
            if dependency_name in tech_name_to_id:
                depends_on_id = tech_name_to_id[dependency_name]

                cursor.execute("""
                    INSERT INTO technology_dependencies (technology_id, depends_on_id)
                    VALUES (?, ?)
                """, (tech_id, depends_on_id))

                dep_count += 1
            else:
                print(f"ВНИМАНИЕ: Зависимость '{dependency_name}' не найдена для '{tech['название']}'")

    print(f"Импортировано {dep_count} зависимостей")

    # Шаг 3: Создаем начальный прогресс для пользователя по умолчанию
    print("Создание прогресса...")
    for tech_id in tech_name_to_id.values():
        cursor.execute("""
            INSERT INTO user_progress (user_id, technology_id, is_unlocked)
            VALUES ('default', ?, 0)
        """, (tech_id,))

    conn.commit()
    print("Миграция завершена успешно!")

    # Вывод статистики
    cursor.execute("SELECT COUNT(*) FROM technologies")
    tech_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM technology_dependencies")
    dep_count = cursor.fetchone()[0]

    print(f"\nСтатистика базы данных:")
    print(f"- Технологий: {tech_count}")
    print(f"- Зависимостей: {dep_count}")

    conn.close()

def create_tables(cursor):
    """Создание всех таблиц"""

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

    # Таблица зависимостей
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS technology_dependencies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            technology_id INTEGER NOT NULL,
            depends_on_id INTEGER NOT NULL,
            dependency_type TEXT DEFAULT 'required',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (technology_id) REFERENCES technologies(id) ON DELETE CASCADE,
            FOREIGN KEY (depends_on_id) REFERENCES technologies(id) ON DELETE CASCADE,
            UNIQUE(technology_id, depends_on_id)
        )
    """)

    cursor.execute("CREATE INDEX IF NOT EXISTS idx_tech_deps_tech ON technology_dependencies(technology_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_tech_deps_parent ON technology_dependencies(depends_on_id)")

    # Таблица прогресса
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

# Использование
if __name__ == "__main__":
    migrate_json_to_sqlite('techno2.json', 'tech_tree.db')
```

### Обратная миграция (SQLite -> JSON)

```python
def export_sqlite_to_json(db_path, json_file_path):
    """Экспорт данных из SQLite обратно в JSON формат"""

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Получаем все технологии
    cursor.execute("""
        SELECT id, name, description
        FROM technologies
        ORDER BY name
    """)

    technologies = []
    tech_id_to_data = {}

    for tech_id, name, description in cursor.fetchall():
        tech_data = {
            "название": name,
            "описание": description or "",
            "условия": []
        }
        technologies.append(tech_data)
        tech_id_to_data[tech_id] = tech_data

    # Получаем все зависимости
    cursor.execute("""
        SELECT td.technology_id, t_dep.name
        FROM technology_dependencies td
        JOIN technologies t_dep ON td.depends_on_id = t_dep.id
        ORDER BY td.technology_id
    """)

    for tech_id, dependency_name in cursor.fetchall():
        if tech_id in tech_id_to_data:
            tech_id_to_data[tech_id]["условия"].append(dependency_name)

    # Формируем результат
    result = {
        "технологии": technologies
    }

    # Сохраняем в JSON
    with open(json_file_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    conn.close()
    print(f"Экспортировано {len(technologies)} технологий в {json_file_path}")
```

---

## Примеры запросов

### 1. Получить все технологии с их зависимостями

```sql
SELECT
    t.id,
    t.name,
    t.description,
    GROUP_CONCAT(t_dep.name, ', ') as dependencies
FROM technologies t
LEFT JOIN technology_dependencies td ON t.id = td.technology_id
LEFT JOIN technologies t_dep ON td.depends_on_id = t_dep.id
GROUP BY t.id, t.name, t.description
ORDER BY t.name;
```

### 2. Найти все прямые зависимости (родители) для технологии

```sql
SELECT t_dep.name as parent_name
FROM technology_dependencies td
JOIN technologies t_dep ON td.depends_on_id = t_dep.id
WHERE td.technology_id = (
    SELECT id FROM technologies WHERE name = 'Колесо'
);
```

### 3. Найти все технологии, которые зависят от данной (дети)

```sql
SELECT t.name as child_name
FROM technology_dependencies td
JOIN technologies t ON td.technology_id = t.id
WHERE td.depends_on_id = (
    SELECT id FROM technologies WHERE name = 'Огонь'
);
```

### 4. Найти все предки технологии (рекурсивный запрос)

```sql
WITH RECURSIVE ancestors AS (
    -- Базовый случай: прямые родители
    SELECT
        t_dep.id,
        t_dep.name,
        1 as level
    FROM technology_dependencies td
    JOIN technologies t_dep ON td.depends_on_id = t_dep.id
    WHERE td.technology_id = (SELECT id FROM technologies WHERE name = 'Компьютеры')

    UNION ALL

    -- Рекурсивный случай: родители родителей
    SELECT
        t_dep.id,
        t_dep.name,
        a.level + 1
    FROM ancestors a
    JOIN technology_dependencies td ON a.id = td.technology_id
    JOIN technologies t_dep ON td.depends_on_id = t_dep.id
)
SELECT DISTINCT name, level
FROM ancestors
ORDER BY level, name;
```

### 5. Найти все потомки технологии (рекурсивный запрос)

```sql
WITH RECURSIVE descendants AS (
    -- Базовый случай: прямые потомки
    SELECT
        t.id,
        t.name,
        1 as level
    FROM technology_dependencies td
    JOIN technologies t ON td.technology_id = t.id
    WHERE td.depends_on_id = (SELECT id FROM technologies WHERE name = 'Огонь')

    UNION ALL

    -- Рекурсивный случай: потомки потомков
    SELECT
        t.id,
        t.name,
        d.level + 1
    FROM descendants d
    JOIN technology_dependencies td ON d.id = td.depends_on_id
    JOIN technologies t ON td.technology_id = t.id
)
SELECT DISTINCT name, level
FROM descendants
ORDER BY level, name;
```

### 6. Проверить доступность технологии для разблокировки

```sql
SELECT
    t.name,
    CASE
        WHEN COUNT(td.depends_on_id) = 0 THEN 'Доступна сразу'
        WHEN COUNT(td.depends_on_id) = SUM(CASE WHEN up.is_unlocked = 1 THEN 1 ELSE 0 END)
        THEN 'Доступна для разблокировки'
        ELSE 'Недоступна'
    END as availability_status,
    COUNT(td.depends_on_id) as total_dependencies,
    SUM(CASE WHEN up.is_unlocked = 1 THEN 1 ELSE 0 END) as unlocked_dependencies
FROM technologies t
LEFT JOIN technology_dependencies td ON t.id = td.technology_id
LEFT JOIN user_progress up ON td.depends_on_id = up.technology_id AND up.user_id = 'default'
WHERE t.name = 'Колесо'
GROUP BY t.id, t.name;
```

### 7. Получить список доступных для разблокировки технологий

```sql
SELECT
    t.id,
    t.name,
    t.description,
    COUNT(td.depends_on_id) as required_count
FROM technologies t
LEFT JOIN technology_dependencies td ON t.id = td.technology_id
LEFT JOIN user_progress up_self ON t.id = up_self.technology_id AND up_self.user_id = 'default'
WHERE up_self.is_unlocked = 0  -- Технология еще не разблокирована
AND NOT EXISTS (
    -- Все зависимости должны быть разблокированы
    SELECT 1
    FROM technology_dependencies td2
    LEFT JOIN user_progress up_dep ON td2.depends_on_id = up_dep.technology_id AND up_dep.user_id = 'default'
    WHERE td2.technology_id = t.id
    AND (up_dep.is_unlocked IS NULL OR up_dep.is_unlocked = 0)
)
GROUP BY t.id, t.name, t.description
ORDER BY required_count, t.name;
```

### 8. Разблокировать технологию

```sql
UPDATE user_progress
SET is_unlocked = 1,
    unlocked_at = CURRENT_TIMESTAMP
WHERE user_id = 'default'
AND technology_id = (SELECT id FROM technologies WHERE name = 'Огонь');
```

### 9. Получить статистику прогресса пользователя

```sql
SELECT
    COUNT(*) as total_technologies,
    SUM(CASE WHEN is_unlocked = 1 THEN 1 ELSE 0 END) as unlocked_count,
    ROUND(100.0 * SUM(CASE WHEN is_unlocked = 1 THEN 1 ELSE 0 END) / COUNT(*), 2) as completion_percentage
FROM user_progress
WHERE user_id = 'default';
```

### 10. Полнотекстовый поиск технологий

```sql
-- Для использования с FTS5 (вариант 4)
SELECT
    t.name,
    t.description,
    snippet(technologies_fts, 1, '<b>', '</b>', '...', 32) as snippet
FROM technologies_fts
JOIN technologies t ON technologies_fts.rowid = t.id
WHERE technologies_fts MATCH 'огонь OR металл*'
ORDER BY rank;
```

---

## Интеграция с существующим кодом

### Класс-обертка для работы с базой данных

```python
import sqlite3
from typing import List, Dict, Optional, Tuple
from datetime import datetime

class TechTreeDatabase:
    """Класс для работы с базой данных технологического древа"""

    def __init__(self, db_path: str = 'tech_tree.db'):
        self.db_path = db_path
        self.conn = None
        self._connect()

    def _connect(self):
        """Подключение к базе данных"""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row  # Доступ к колонкам по имени
        # Включаем поддержку foreign keys
        self.conn.execute("PRAGMA foreign_keys = ON")

    def close(self):
        """Закрытие соединения"""
        if self.conn:
            self.conn.close()

    def get_all_technologies(self) -> List[Dict]:
        """Получить все технологии с их зависимостями"""
        cursor = self.conn.cursor()

        # Получаем все технологии
        cursor.execute("SELECT id, name, description FROM technologies ORDER BY name")
        technologies = [dict(row) for row in cursor.fetchall()]

        # Для каждой технологии получаем зависимости
        for tech in technologies:
            cursor.execute("""
                SELECT t.name
                FROM technology_dependencies td
                JOIN technologies t ON td.depends_on_id = t.id
                WHERE td.technology_id = ?
            """, (tech['id'],))

            tech['условия'] = [row['name'] for row in cursor.fetchall()]

        return technologies

    def get_technology_by_name(self, name: str) -> Optional[Dict]:
        """Получить технологию по названию"""
        cursor = self.conn.cursor()

        cursor.execute("""
            SELECT id, name, description
            FROM technologies
            WHERE name = ?
        """, (name,))

        row = cursor.fetchone()
        if not row:
            return None

        tech = dict(row)

        # Получаем зависимости
        cursor.execute("""
            SELECT t.name
            FROM technology_dependencies td
            JOIN technologies t ON td.depends_on_id = t.id
            WHERE td.technology_id = ?
        """, (tech['id'],))

        tech['условия'] = [row['name'] for row in cursor.fetchall()]

        return tech

    def get_all_parents(self, tech_name: str) -> Dict[str, int]:
        """Получить всех предков технологии с уровнями"""
        cursor = self.conn.cursor()

        cursor.execute("""
            WITH RECURSIVE ancestors AS (
                SELECT
                    t_dep.id,
                    t_dep.name,
                    1 as level
                FROM technology_dependencies td
                JOIN technologies t_dep ON td.depends_on_id = t_dep.id
                WHERE td.technology_id = (SELECT id FROM technologies WHERE name = ?)

                UNION ALL

                SELECT
                    t_dep.id,
                    t_dep.name,
                    a.level + 1
                FROM ancestors a
                JOIN technology_dependencies td ON a.id = td.technology_id
                JOIN technologies t_dep ON td.depends_on_id = t_dep.id
            )
            SELECT DISTINCT name, level FROM ancestors
        """, (tech_name,))

        return {row['name']: row['level'] for row in cursor.fetchall()}

    def get_all_children(self, tech_name: str) -> Dict[str, int]:
        """Получить всех потомков технологии с уровнями"""
        cursor = self.conn.cursor()

        cursor.execute("""
            WITH RECURSIVE descendants AS (
                SELECT
                    t.id,
                    t.name,
                    1 as level
                FROM technology_dependencies td
                JOIN technologies t ON td.technology_id = t.id
                WHERE td.depends_on_id = (SELECT id FROM technologies WHERE name = ?)

                UNION ALL

                SELECT
                    t.id,
                    t.name,
                    d.level + 1
                FROM descendants d
                JOIN technology_dependencies td ON d.id = td.depends_on_id
                JOIN technologies t ON td.technology_id = t.id
            )
            SELECT DISTINCT name, level FROM descendants
        """, (tech_name,))

        return {row['name']: row['level'] for row in cursor.fetchall()}

    def is_technology_available(self, tech_name: str, user_id: str = 'default') -> bool:
        """Проверить доступность технологии для разблокировки"""
        cursor = self.conn.cursor()

        cursor.execute("""
            SELECT
                CASE
                    WHEN COUNT(td.depends_on_id) = 0 THEN 1
                    WHEN COUNT(td.depends_on_id) = SUM(CASE WHEN up.is_unlocked = 1 THEN 1 ELSE 0 END)
                    THEN 1
                    ELSE 0
                END as is_available
            FROM technologies t
            LEFT JOIN technology_dependencies td ON t.id = td.technology_id
            LEFT JOIN user_progress up ON td.depends_on_id = up.technology_id AND up.user_id = ?
            WHERE t.name = ?
            GROUP BY t.id
        """, (user_id, tech_name))

        row = cursor.fetchone()
        return bool(row['is_available']) if row else False

    def unlock_technology(self, tech_name: str, user_id: str = 'default') -> bool:
        """Разблокировать технологию"""
        try:
            cursor = self.conn.cursor()

            cursor.execute("""
                UPDATE user_progress
                SET is_unlocked = 1, unlocked_at = CURRENT_TIMESTAMP
                WHERE user_id = ?
                AND technology_id = (SELECT id FROM technologies WHERE name = ?)
            """, (user_id, tech_name))

            self.conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            self.conn.rollback()
            print(f"Ошибка разблокировки: {e}")
            return False

    def toggle_technology(self, tech_name: str, user_id: str = 'default') -> bool:
        """Переключить состояние технологии"""
        try:
            cursor = self.conn.cursor()

            # Получаем текущее состояние
            cursor.execute("""
                SELECT is_unlocked
                FROM user_progress
                WHERE user_id = ?
                AND technology_id = (SELECT id FROM technologies WHERE name = ?)
            """, (user_id, tech_name))

            row = cursor.fetchone()
            if not row:
                return False

            new_state = not row['is_unlocked']

            # Обновляем состояние
            cursor.execute("""
                UPDATE user_progress
                SET is_unlocked = ?,
                    unlocked_at = CASE WHEN ? = 1 THEN CURRENT_TIMESTAMP ELSE NULL END
                WHERE user_id = ?
                AND technology_id = (SELECT id FROM technologies WHERE name = ?)
            """, (new_state, new_state, user_id, tech_name))

            self.conn.commit()
            return True
        except Exception as e:
            self.conn.rollback()
            print(f"Ошибка переключения: {e}")
            return False

    def get_user_progress(self, user_id: str = 'default') -> Dict:
        """Получить прогресс пользователя"""
        cursor = self.conn.cursor()

        cursor.execute("""
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN is_unlocked = 1 THEN 1 ELSE 0 END) as unlocked,
                ROUND(100.0 * SUM(CASE WHEN is_unlocked = 1 THEN 1 ELSE 0 END) / COUNT(*), 2) as percentage
            FROM user_progress
            WHERE user_id = ?
        """, (user_id,))

        row = cursor.fetchone()
        return dict(row) if row else {'total': 0, 'unlocked': 0, 'percentage': 0.0}

    def get_technology_flags(self, user_id: str = 'default') -> Dict[str, bool]:
        """Получить флаги разблокировки всех технологий (для совместимости со старым кодом)"""
        cursor = self.conn.cursor()

        cursor.execute("""
            SELECT t.name, up.is_unlocked
            FROM technologies t
            JOIN user_progress up ON t.id = up.technology_id
            WHERE up.user_id = ?
        """, (user_id,))

        return {row['name']: bool(row['is_unlocked']) for row in cursor.fetchall()}

    def save_progress(self, tech_flags: Dict[str, bool], user_id: str = 'default'):
        """Сохранить прогресс (для совместимости со старым кодом)"""
        try:
            cursor = self.conn.cursor()

            for tech_name, is_unlocked in tech_flags.items():
                cursor.execute("""
                    UPDATE user_progress
                    SET is_unlocked = ?,
                        unlocked_at = CASE WHEN ? = 1 THEN CURRENT_TIMESTAMP ELSE NULL END
                    WHERE user_id = ?
                    AND technology_id = (SELECT id FROM technologies WHERE name = ?)
                """, (is_unlocked, is_unlocked, user_id, tech_name))

            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            print(f"Ошибка сохранения прогресса: {e}")

# Пример использования
if __name__ == "__main__":
    db = TechTreeDatabase('tech_tree.db')

    # Получить все технологии
    techs = db.get_all_technologies()
    print(f"Всего технологий: {len(techs)}")

    # Получить технологию
    fire = db.get_technology_by_name('Огонь')
    print(f"Огонь: {fire}")

    # Получить предков
    parents = db.get_all_parents('Компьютеры')
    print(f"Предки Компьютеров: {parents}")

    # Проверить доступность
    available = db.is_technology_available('Колесо')
    print(f"Колесо доступно: {available}")

    # Разблокировать технологию
    db.unlock_technology('Огонь')

    # Получить прогресс
    progress = db.get_user_progress()
    print(f"Прогресс: {progress}")

    db.close()
```

### Минимальные изменения в tech_tree.py

```python
# В начале файла вместо загрузки JSON:
from tech_tree_database import TechTreeDatabase

# Создаем подключение к БД
db = TechTreeDatabase('tech_tree.db')

# Загрузка данных
data = {'технологии': db.get_all_technologies()}
dct_tech = {tech['название']: tech for tech in data['технологии']}

# Загрузка прогресса пользователя
tech_flags = db.get_technology_flags()

# При сохранении прогресса:
def save_progress():
    db.save_progress(tech_flags)
    messagebox.showinfo("Успех", "Прогресс сохранен!")

# При загрузке прогресса:
def load_progress():
    global tech_flags
    tech_flags = db.get_technology_flags()
    update_visualization(selected_tech.get())
    update_listbox_colors()

# Функция find_all_parents использует БД:
def find_all_parents(tech_name):
    return db.get_all_parents(tech_name)

# Функция find_all_children использует БД:
def find_all_children(tech_name):
    return db.get_all_children(tech_name)

# Функция is_tech_available использует БД:
def is_tech_available(tech_name):
    return db.is_technology_available(tech_name)
```

---

## Заключение

Предложены 4 варианта архитектуры базы данных SQLite:

1. **Простая нормализованная** - для небольших проектов
2. **Расширенная с метаданными** - рекомендуемый вариант (оптимальный баланс)
3. **Closure Table** - для максимальной производительности на больших графах
4. **Гибридная с JSON** - компромиссный вариант для легкой миграции

Рекомендуется использовать **Вариант 2** как оптимальное решение, которое:
- Покрывает все текущие требования
- Легко расширяется
- Обеспечивает хорошую производительность
- Поддерживает множественных пользователей
- Имеет понятную структуру

Предоставлены скрипты миграции и класс-обертка для легкой интеграции с существующим кодом.
