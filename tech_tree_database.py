"""
Класс-обертка для работы с базой данных технологического древа
"""

import sqlite3
from typing import List, Dict, Optional, Tuple
from datetime import datetime


class TechTreeDatabase:
    """Класс для работы с базой данных технологического древа"""

    def __init__(self, db_path: str = 'tech_tree.db'):
        """
        Инициализация подключения к базе данных

        Args:
            db_path: Путь к файлу базы данных SQLite
        """
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
            self.conn = None

    def __enter__(self):
        """Поддержка context manager"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Закрытие при выходе из context manager"""
        self.close()

    def get_all_technologies(self) -> List[Dict]:
        """
        Получить все технологии с их зависимостями

        Returns:
            Список словарей с данными технологий в формате JSON
        """
        cursor = self.conn.cursor()

        # Получаем все технологии
        cursor.execute("SELECT id, name, description FROM technologies ORDER BY name")
        raw_technologies = cursor.fetchall()

        technologies = []
        for row in raw_technologies:
            tech = {
                'название': row['name'],
                'описание': row['description']
            }

            # Получаем зависимости
            cursor.execute("""
                SELECT t.name
                FROM technology_dependencies td
                JOIN technologies t ON td.depends_on_id = t.id
                WHERE td.technology_id = ?
                ORDER BY t.name
            """, (row['id'],))

            tech['условия'] = [dep_row['name'] for dep_row in cursor.fetchall()]
            technologies.append(tech)

        return technologies

    def get_technology_by_name(self, name: str) -> Optional[Dict]:
        """
        Получить технологию по названию

        Args:
            name: Название технологии

        Returns:
            Словарь с данными технологии в формате JSON или None
        """
        cursor = self.conn.cursor()

        cursor.execute("""
            SELECT id, name, description
            FROM technologies
            WHERE name = ?
        """, (name,))

        row = cursor.fetchone()
        if not row:
            return None

        tech = {
            'название': row['name'],
            'описание': row['description']
        }

        # Получаем зависимости
        cursor.execute("""
            SELECT t.name
            FROM technology_dependencies td
            JOIN technologies t ON td.depends_on_id = t.id
            WHERE td.technology_id = ?
            ORDER BY t.name
        """, (row['id'],))

        tech['условия'] = [dep_row['name'] for dep_row in cursor.fetchall()]

        return tech

    def get_all_parents(self, tech_name: str) -> Dict[str, int]:
        """
        Получить всех предков технологии с уровнями (рекурсивный поиск)

        Args:
            tech_name: Название технологии

        Returns:
            Словарь {название_технологии: уровень_вложенности}
        """
        cursor = self.conn.cursor()

        cursor.execute("""
            WITH RECURSIVE ancestors AS (
                -- Базовый случай: прямые родители
                SELECT
                    t_dep.id,
                    t_dep.name,
                    1 as level
                FROM technology_dependencies td
                JOIN technologies t_dep ON td.depends_on_id = t_dep.id
                WHERE td.technology_id = (SELECT id FROM technologies WHERE name = ?)

                UNION ALL

                -- Рекурсивный случай: родители родителей
                SELECT
                    t_dep.id,
                    t_dep.name,
                    a.level + 1
                FROM ancestors a
                JOIN technology_dependencies td ON a.id = td.technology_id
                JOIN technologies t_dep ON td.depends_on_id = t_dep.id
                WHERE a.level < 100  -- Защита от бесконечной рекурсии
            )
            SELECT DISTINCT name, MIN(level) as level
            FROM ancestors
            GROUP BY name
            ORDER BY level
        """, (tech_name,))

        result = {tech_name: 0}  # Добавляем саму технологию с уровнем 0
        result.update({row['name']: row['level'] for row in cursor.fetchall()})

        return result

    def get_all_children(self, tech_name: str) -> Dict[str, int]:
        """
        Получить всех потомков технологии с уровнями (рекурсивный поиск)

        Args:
            tech_name: Название технологии

        Returns:
            Словарь {название_технологии: уровень_вложенности}
        """
        cursor = self.conn.cursor()

        cursor.execute("""
            WITH RECURSIVE descendants AS (
                -- Базовый случай: прямые потомки
                SELECT
                    t.id,
                    t.name,
                    1 as level
                FROM technology_dependencies td
                JOIN technologies t ON td.technology_id = t.id
                WHERE td.depends_on_id = (SELECT id FROM technologies WHERE name = ?)

                UNION ALL

                -- Рекурсивный случай: потомки потомков
                SELECT
                    t.id,
                    t.name,
                    d.level + 1
                FROM descendants d
                JOIN technology_dependencies td ON d.id = td.depends_on_id
                JOIN technologies t ON td.technology_id = t.id
                WHERE d.level < 100  -- Защита от бесконечной рекурсии
            )
            SELECT DISTINCT name, MIN(level) as level
            FROM descendants
            GROUP BY name
            ORDER BY level
        """, (tech_name,))

        result = {tech_name: 0}  # Добавляем саму технологию с уровнем 0
        result.update({row['name']: row['level'] for row in cursor.fetchall()})

        return result

    def is_technology_available(self, tech_name: str, user_id: str = 'default') -> bool:
        """
        Проверить доступность технологии для разблокировки

        Args:
            tech_name: Название технологии
            user_id: ID пользователя

        Returns:
            True если технология доступна для разблокировки
        """
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
        """
        Разблокировать технологию

        Args:
            tech_name: Название технологии
            user_id: ID пользователя

        Returns:
            True если разблокировка прошла успешно
        """
        try:
            cursor = self.conn.cursor()

            cursor.execute("""
                UPDATE user_progress
                SET is_unlocked = 1
                WHERE user_id = ?
                AND technology_id = (SELECT id FROM technologies WHERE name = ?)
            """, (user_id, tech_name))

            self.conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            self.conn.rollback()
            print(f"Ошибка разблокировки: {e}")
            return False

    def lock_technology(self, tech_name: str, user_id: str = 'default') -> bool:
        """
        Заблокировать технологию

        Args:
            tech_name: Название технологии
            user_id: ID пользователя

        Returns:
            True если блокировка прошла успешно
        """
        try:
            cursor = self.conn.cursor()

            cursor.execute("""
                UPDATE user_progress
                SET is_unlocked = 0, unlocked_at = NULL
                WHERE user_id = ?
                AND technology_id = (SELECT id FROM technologies WHERE name = ?)
            """, (user_id, tech_name))

            self.conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            self.conn.rollback()
            print(f"Ошибка блокировки: {e}")
            return False

    def toggle_technology(self, tech_name: str, user_id: str = 'default') -> bool:
        """
        Переключить состояние технологии

        Args:
            tech_name: Название технологии
            user_id: ID пользователя

        Returns:
            True если переключение прошло успешно
        """
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
                SET is_unlocked = ?
                WHERE user_id = ?
                AND technology_id = (SELECT id FROM technologies WHERE name = ?)
            """, (new_state, user_id, tech_name))

            self.conn.commit()
            return True
        except Exception as e:
            self.conn.rollback()
            print(f"Ошибка переключения: {e}")
            return False

    def get_user_progress(self, user_id: str = 'default') -> Dict:
        """
        Получить прогресс пользователя

        Args:
            user_id: ID пользователя

        Returns:
            Словарь со статистикой прогресса
        """
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
        """
        Получить флаги разблокировки всех технологий (для совместимости со старым кодом)

        Args:
            user_id: ID пользователя

        Returns:
            Словарь {название_технологии: разблокирована}
        """
        cursor = self.conn.cursor()

        cursor.execute("""
            SELECT t.name, up.is_unlocked
            FROM technologies t
            JOIN user_progress up ON t.id = up.technology_id
            WHERE up.user_id = ?
        """, (user_id,))

        return {row['name']: bool(row['is_unlocked']) for row in cursor.fetchall()}

    def save_progress(self, tech_flags: Dict[str, bool], user_id: str = 'default') -> bool:
        """
        Сохранить прогресс (для совместимости со старым кодом)

        Args:
            tech_flags: Словарь {название_технологии: разблокирована}
            user_id: ID пользователя

        Returns:
            True если сохранение прошло успешно
        """
        try:
            cursor = self.conn.cursor()

            for tech_name, is_unlocked in tech_flags.items():
                cursor.execute("""
                    UPDATE user_progress
                    SET is_unlocked = ?
                    WHERE user_id = ?
                    AND technology_id = (SELECT id FROM technologies WHERE name = ?)
                """, (is_unlocked, user_id, tech_name))

            self.conn.commit()
            return True
        except Exception as e:
            self.conn.rollback()
            print(f"Ошибка сохранения прогресса: {e}")
            return False

    def get_available_technologies(self, user_id: str = 'default') -> List[Dict]:
        """
        Получить список доступных для разблокировки технологий

        Args:
            user_id: ID пользователя

        Returns:
            Список словарей с информацией о доступных технологиях
        """
        cursor = self.conn.cursor()

        cursor.execute("""
            SELECT
                t.id,
                t.name,
                t.description,
                COUNT(td.depends_on_id) as required_count
            FROM technologies t
            LEFT JOIN technology_dependencies td ON t.id = td.technology_id
            LEFT JOIN user_progress up_self ON t.id = up_self.technology_id AND up_self.user_id = ?
            WHERE up_self.is_unlocked = 0  -- Технология еще не разблокирована
            AND NOT EXISTS (
                -- Все зависимости должны быть разблокированы
                SELECT 1
                FROM technology_dependencies td2
                LEFT JOIN user_progress up_dep ON td2.depends_on_id = up_dep.technology_id AND up_dep.user_id = ?
                WHERE td2.technology_id = t.id
                AND (up_dep.is_unlocked IS NULL OR up_dep.is_unlocked = 0)
            )
            GROUP BY t.id, t.name, t.description
            ORDER BY required_count, t.name
        """, (user_id, user_id))

        return [dict(row) for row in cursor.fetchall()]

    def get_statistics(self, user_id: str = 'default') -> Dict:
        """
        Получить общую статистику по базе данных

        Args:
            user_id: ID пользователя (для статистики прогресса)

        Returns:
            Словарь со статистикой
        """
        cursor = self.conn.cursor()

        stats = {}

        # Общее количество технологий
        cursor.execute("SELECT COUNT(*) FROM technologies")
        stats['total_technologies'] = cursor.fetchone()[0]

        # Общее количество зависимостей
        cursor.execute("SELECT COUNT(*) FROM technology_dependencies")
        stats['total_dependencies'] = cursor.fetchone()[0]

        # Количество корневых технологий (без зависимостей)
        cursor.execute("""
            SELECT COUNT(*)
            FROM technologies t
            LEFT JOIN technology_dependencies td ON t.id = td.technology_id
            WHERE td.id IS NULL
        """)
        stats['root_technologies'] = cursor.fetchone()[0]

        # Количество разблокированных технологий
        cursor.execute("""
            SELECT COUNT(*)
            FROM user_progress
            WHERE user_id = ? AND is_unlocked = 1
        """, (user_id,))
        stats['unlocked_technologies'] = cursor.fetchone()[0]

        # Средний процент выполнения зависимостей
        cursor.execute("""
            SELECT AVG(dep_count) as avg_deps
            FROM (
                SELECT COUNT(td.depends_on_id) as dep_count
                FROM technologies t
                LEFT JOIN technology_dependencies td ON t.id = td.technology_id
                GROUP BY t.id
            )
        """)
        row = cursor.fetchone()
        stats['avg_dependencies'] = float(row['avg_deps']) if row['avg_deps'] else 0.0

        # Технология с наибольшим количеством зависимостей
        cursor.execute("""
            SELECT t.name, COUNT(td.depends_on_id) as dep_count
            FROM technologies t
            LEFT JOIN technology_dependencies td ON t.id = td.technology_id
            GROUP BY t.id, t.name
            ORDER BY dep_count DESC
            LIMIT 1
        """)
        row = cursor.fetchone()
        if row:
            stats['most_complex_tech'] = {'name': row['name'], 'dependencies': row['dep_count']}

        # Технология с наибольшим количеством потомков
        cursor.execute("""
            SELECT t.name, COUNT(td.technology_id) as child_count
            FROM technologies t
            LEFT JOIN technology_dependencies td ON t.id = td.depends_on_id
            GROUP BY t.id, t.name
            ORDER BY child_count DESC
            LIMIT 1
        """)
        row = cursor.fetchone()
        if row:
            stats['most_influential_tech'] = {'name': row['name'], 'children': row['child_count']}

        return stats


# Пример использования
if __name__ == "__main__":
    # Используем context manager для автоматического закрытия соединения
    with TechTreeDatabase('tech_tree.db') as db:
        # Получить все технологии
        techs = db.get_all_technologies()
        print(f"Всего технологий: {len(techs)}")

        # Получить технологию
        fire = db.get_technology_by_name('Огонь')
        if fire:
            print(f"\nОгонь: {fire['описание']}")
            print(f"Зависимости: {fire['условия']}")

        # Получить предков
        parents = db.get_all_parents('Компьютеры')
        print(f"\nПредки Компьютеров ({len(parents)} шт.):")
        for name, level in sorted(parents.items(), key=lambda x: x[1]):
            print(f"  Уровень {level}: {name}")

        # Проверить доступность
        available = db.is_technology_available('Колесо')
        print(f"\nКолесо доступно: {available}")

        # Разблокировать технологию
        db.unlock_technology('Огонь')
        print("\nОгонь разблокирован")

        # Получить прогресс
        progress = db.get_user_progress()
        print(f"\nПрогресс: {progress['unlocked']}/{progress['total']} ({progress['percentage']}%)")

        # Получить доступные технологии (возвращает словари с английскими ключами)
        available_techs = db.get_available_technologies()
        print(f"\nДоступно для разблокировки: {len(available_techs)} технологий")
        for tech in available_techs[:5]:
            print(f"  - {tech['name']}")

        # Статистика
        stats = db.get_statistics()
        print(f"\nОбщая статистика:")
        print(f"  Всего технологий: {stats['total_technologies']}")
        print(f"  Всего зависимостей: {stats['total_dependencies']}")
        print(f"  Корневых технологий: {stats['root_technologies']}")
        print(f"  Разблокировано: {stats['unlocked_technologies']}")
        print(f"  Среднее число зависимостей: {stats['avg_dependencies']:.2f}")
        if 'most_complex_tech' in stats:
            print(f"  Самая сложная: {stats['most_complex_tech']['name']} ({stats['most_complex_tech']['dependencies']} зависимостей)")
        if 'most_influential_tech' in stats:
            print(f"  Самая влиятельная: {stats['most_influential_tech']['name']} ({stats['most_influential_tech']['children']} потомков)")
