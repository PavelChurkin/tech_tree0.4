# Руководство по миграции на SQLite

Это краткое руководство поможет вам быстро начать работу с SQLite базой данных для технологического древа.

## Быстрый старт

### 1. Миграция данных из JSON в SQLite

```bash
python migrate_to_sqlite.py import techno2.json tech_tree.db
```

Эта команда создаст базу данных `tech_tree.db` и импортирует все данные из `techno2.json`.

### 2. Использование базы данных в коде

```python
from tech_tree_database import TechTreeDatabase

# Создаем подключение
with TechTreeDatabase('tech_tree.db') as db:
    # Получить все технологии
    all_techs = db.get_all_technologies()

    # Получить конкретную технологию
    fire = db.get_technology_by_name('Огонь')

    # Найти всех предков
    parents = db.get_all_parents('Компьютеры')

    # Найти всех потомков
    children = db.get_all_children('Огонь')

    # Проверить доступность
    available = db.is_technology_available('Колесо')

    # Разблокировать технологию
    db.unlock_technology('Огонь')

    # Получить прогресс
    progress = db.get_user_progress()
    print(f"Прогресс: {progress['unlocked']}/{progress['total']} ({progress['percentage']}%)")
```

### 3. Экспорт обратно в JSON (если нужно)

```bash
python migrate_to_sqlite.py export tech_tree.db output.json
```

## Интеграция с tech_tree.py

Минимальные изменения для интеграции:

```python
# В начале файла
from tech_tree_database import TechTreeDatabase

# Вместо загрузки JSON:
db = TechTreeDatabase('tech_tree.db')
data = {'технологии': db.get_all_technologies()}
dct_tech = {tech['название']: tech for tech in data['технологии']}

# Загрузка прогресса
tech_flags = db.get_technology_flags()

# Замените функции:
def find_all_parents(tech_name):
    return db.get_all_parents(tech_name)

def find_all_children(tech_name):
    return db.get_all_children(tech_name)

def is_tech_available(tech_name):
    return db.is_technology_available(tech_name)

# При переключении технологии (клик правой кнопкой):
def on_right_click(event):
    # ... код определения узла ...
    db.toggle_technology(node)
    # ... остальной код ...
```

## Основные команды

### Миграция
```bash
# Импорт из JSON
python migrate_to_sqlite.py import <json_file> <db_file>

# Экспорт в JSON
python migrate_to_sqlite.py export <db_file> <json_file>

# Примеры
python migrate_to_sqlite.py import techno2.json tech_tree.db
python migrate_to_sqlite.py export tech_tree.db backup.json
```

### Работа с базой данных
```python
# Создание подключения
db = TechTreeDatabase('tech_tree.db')

# Основные операции
techs = db.get_all_technologies()
tech = db.get_technology_by_name('Огонь')
parents = db.get_all_parents('Колесо')
children = db.get_all_children('Огонь')

# Работа с прогрессом
available = db.is_technology_available('Колесо')
db.unlock_technology('Огонь')
db.lock_technology('Огонь')
db.toggle_technology('Огонь')

# Статистика
progress = db.get_user_progress()
available_techs = db.get_available_technologies()
stats = db.get_statistics()

# Не забудьте закрыть соединение
db.close()

# Или используйте context manager (рекомендуется)
with TechTreeDatabase('tech_tree.db') as db:
    # ... ваш код ...
    pass  # Соединение автоматически закроется
```

## Преимущества SQLite по сравнению с JSON

1. **Производительность**
   - Быстрый рекурсивный поиск предков/потомков
   - Эффективные индексы для поиска
   - Оптимизированные запросы

2. **Функциональность**
   - Поддержка множественных пользователей
   - История разблокировки технологий
   - Сложные запросы (доступные технологии, статистика)
   - Транзакции для целостности данных

3. **Масштабируемость**
   - Легко добавлять новые поля
   - Можно добавить категории, сложность, иконки
   - Поддержка миграций схемы

4. **Надежность**
   - Foreign key constraints предотвращают некорректные данные
   - Триггеры автоматически обновляют связанные данные
   - Встроенная валидация

## Примеры SQL запросов

### Получить доступные технологии
```sql
SELECT t.name
FROM technologies t
LEFT JOIN user_progress up ON t.id = up.technology_id
WHERE up.is_unlocked = 0
AND NOT EXISTS (
    SELECT 1 FROM technology_dependencies td
    LEFT JOIN user_progress up2 ON td.depends_on_id = up2.technology_id
    WHERE td.technology_id = t.id
    AND (up2.is_unlocked IS NULL OR up2.is_unlocked = 0)
);
```

### Топ технологий по количеству зависимостей
```sql
SELECT t.name, COUNT(td.depends_on_id) as deps
FROM technologies t
LEFT JOIN technology_dependencies td ON t.id = td.technology_id
GROUP BY t.id, t.name
ORDER BY deps DESC
LIMIT 10;
```

### Прогресс по категориям (если используется вариант 2)
```sql
SELECT c.name,
       COUNT(*) as total,
       SUM(CASE WHEN up.is_unlocked = 1 THEN 1 ELSE 0 END) as unlocked
FROM categories c
JOIN technologies t ON c.id = t.category_id
JOIN user_progress up ON t.id = up.technology_id
GROUP BY c.id, c.name;
```

## Дополнительные ресурсы

- [DATABASE_ARCHITECTURE.md](./DATABASE_ARCHITECTURE.md) - Полная документация по архитектуре
- [migrate_to_sqlite.py](./migrate_to_sqlite.py) - Исходный код скрипта миграции
- [tech_tree_database.py](./tech_tree_database.py) - Исходный код класса для работы с БД

## Устранение неполадок

### База данных заблокирована
```python
# Убедитесь, что закрываете соединения
db.close()

# Или используйте context manager
with TechTreeDatabase('tech_tree.db') as db:
    # работа с БД
    pass
```

### Данные не синхронизируются
```python
# Убедитесь, что вызываете commit после изменений
# (класс TechTreeDatabase делает это автоматически)
```

### Дубликаты технологий
```bash
# Скрипт миграции автоматически обрабатывает дубликаты
# Будет использована первая встреченная технология
```

## Вопросы и поддержка

Если у вас возникли вопросы или проблемы:
1. Проверьте [DATABASE_ARCHITECTURE.md](./DATABASE_ARCHITECTURE.md) для детальной информации
2. Посмотрите примеры в коде `tech_tree_database.py`
3. Создайте issue в репозитории

---

Удачи в работе с базой данных! 🚀
