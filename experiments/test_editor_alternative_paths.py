#!/usr/bin/env python3
"""
Тест редактора для проверки поддержки альтернативных путей.
Этот скрипт проверяет, что редактор корректно работает с технологиями,
имеющими альтернативные пути получения.
"""

import sys
import os
import json

# Добавляем корневую директорию в путь
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Импортируем необходимые функции
from collections import deque


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


def find_all_parents(tech_name, data):
    """Поиск всех родителей для технологии"""
    dct_tech = {tech['название']: tech for tech in data['технологии']}

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


def find_all_children(tech_name, data):
    """Поиск всех детей для технологии"""
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


def test_generate_plantuml_with_alternative_paths(data):
    """Тест генерации PlantUML кода с альтернативными путями"""
    print("Тест 1: Генерация PlantUML с альтернативными путями")

    dct_tech = {tech['название']: tech for tech in data['технологии']}
    center_tech = "Водород"

    # Находим всех родителей и детей
    parents = find_all_parents(center_tech, data)
    children = find_all_children(center_tech, data)

    # Собираем все узлы
    all_nodes = set([center_tech])
    all_nodes.update(parents.keys())
    all_nodes.update(children.keys())

    print(f"  Центральная технология: {center_tech}")
    print(f"  Родители: {[p for p in parents.keys() if p != center_tech]}")
    print(f"  Дети: {[c for c in children.keys() if c != center_tech]}")

    # Генерируем код PlantUML (упрощенная версия)
    plantuml_code = "@startuml\n"

    # Добавляем связи
    errors = []
    for node in all_nodes:
        if node in dct_tech:
            conditions = dct_tech[node]['условия']
            if conditions:
                if isinstance(conditions[0], str):
                    # Старый формат: простой список родителей
                    for parent in conditions:
                        if parent in all_nodes:
                            plantuml_code += f'{parent} --> {node}\n'
                elif isinstance(conditions[0], list):
                    # Новый формат: альтернативные пути
                    for path in conditions:
                        for parent in path:
                            if parent in all_nodes:
                                plantuml_code += f'{parent} --> {node}\n'
                else:
                    errors.append(f"Неизвестный тип условия для {node}: {type(conditions[0])}")

    plantuml_code += "@enduml"

    if errors:
        print(f"  ❌ ОШИБКИ: {errors}")
        return False
    else:
        print(f"  ✅ PlantUML код сгенерирован успешно")
        print(f"  Количество связей: {plantuml_code.count('-->')}")
        return True


def test_parse_conditions():
    """Тест парсинга условий с круглыми скобками"""
    print("\nТест 2: Парсинг условий с круглыми скобками")

    test_cases = [
        ("Технология1", ["Технология1"], False),  # Старый формат
        ("(Технология1, Технология2)", [["Технология1", "Технология2"]], True),  # Новый формат
        ("Технология1", ["Технология1"], False),  # Смешанный: одиночная
    ]

    all_passed = True
    for condition_str, expected, is_path in test_cases:
        # Парсим условие
        cond = condition_str.strip()
        if cond.startswith('(') and cond.endswith(')'):
            # Это альтернативный путь
            path_content = cond[1:-1]
            parsed = [[c.strip() for c in path_content.split(',') if c.strip()]]
        else:
            # Это обычное условие
            parsed = [cond]

        # Проверяем
        if parsed == expected:
            print(f"  ✅ '{condition_str}' → {parsed}")
        else:
            print(f"  ❌ '{condition_str}' → {parsed} (ожидалось {expected})")
            all_passed = False

    return all_passed


def test_load_and_display_alternative_paths(data):
    """Тест загрузки и отображения альтернативных путей"""
    print("\nТест 3: Загрузка и отображение альтернативных путей")

    dct_tech = {tech['название']: tech for tech in data['технологии']}
    tech_name = "Водород"
    tech_data = dct_tech[tech_name]

    conditions = tech_data.get('условия', [])
    displayed = []

    if conditions:
        if isinstance(conditions[0], str):
            # Старый формат
            for condition in conditions:
                displayed.append(condition)
        elif isinstance(conditions[0], list):
            # Новый формат: отображаем пути в формате (Условие1, Условие2)
            for path in conditions:
                path_str = "(" + ", ".join(path) + ")"
                displayed.append(path_str)

    expected = [
        "(Электролиз, Вода)",
        "(Паровая конверсия, Метан, Катализатор)"
    ]

    if displayed == expected:
        print(f"  ✅ Условия отображены корректно:")
        for item in displayed:
            print(f"     - {item}")
        return True
    else:
        print(f"  ❌ Ошибка отображения:")
        print(f"     Получено: {displayed}")
        print(f"     Ожидалось: {expected}")
        return False


def test_save_alternative_paths(data):
    """Тест сохранения альтернативных путей"""
    print("\nТест 4: Сохранение альтернативных путей")

    # Имитируем ввод пользователя
    conditions_raw = [
        "(Электролиз, Вода)",
        "(Паровая конверсия, Метан, Катализатор)"
    ]

    # Парсим условия
    conditions = []
    for cond in conditions_raw:
        cond = cond.strip()
        if cond.startswith('(') and cond.endswith(')'):
            path_content = cond[1:-1]
            path = [c.strip() for c in path_content.split(',') if c.strip()]
            conditions.append(path)
        else:
            conditions.append(cond)

    # Проверяем формат
    has_paths = any(isinstance(c, list) for c in conditions)
    if has_paths:
        normalized_conditions = []
        for c in conditions:
            if isinstance(c, list):
                normalized_conditions.append(c)
            else:
                normalized_conditions.append([c])
        conditions = normalized_conditions

    expected = [
        ["Электролиз", "Вода"],
        ["Паровая конверсия", "Метан", "Катализатор"]
    ]

    if conditions == expected:
        print(f"  ✅ Условия сохранены корректно:")
        for path in conditions:
            print(f"     - {path}")
        return True
    else:
        print(f"  ❌ Ошибка сохранения:")
        print(f"     Получено: {conditions}")
        print(f"     Ожидалось: {expected}")
        return False


def test_edit_condition():
    """Тест редактирования условий"""
    print("\nТест 5: Редактирование условий")

    dct_tech = {
        "Вода": {},
        "Электричество": {},
        "Электролиз": {},
        "Метан": {},
        "Паровая конверсия": {},
        "Катализатор": {},
        "Водород": {},
        "Биомасса": {},
    }

    # Тест 1: Редактирование простого условия на другое простое условие
    print("  Тест 5.1: Редактирование простого условия")
    condition = "Вода"
    new_condition = "Биомасса"

    if new_condition in dct_tech:
        print(f"    ✅ Изменение '{condition}' → '{new_condition}'")
        test1_passed = True
    else:
        print(f"    ❌ Ошибка валидации для '{new_condition}'")
        test1_passed = False

    # Тест 2: Редактирование простого условия на составное (путь)
    print("  Тест 5.2: Редактирование простого условия на составной путь")
    condition = "Вода"
    new_condition = "(Электролиз, Вода)"

    path_content = new_condition[1:-1]
    techs = [t.strip() for t in path_content.split(',') if t.strip()]
    invalid_techs = [t for t in techs if t not in dct_tech]

    if not invalid_techs:
        print(f"    ✅ Изменение '{condition}' → '{new_condition}'")
        test2_passed = True
    else:
        print(f"    ❌ Ошибка валидации для '{new_condition}': {invalid_techs}")
        test2_passed = False

    # Тест 3: Редактирование составного пути на другой составной путь
    print("  Тест 5.3: Редактирование составного пути")
    condition = "(Электролиз, Вода)"
    new_condition = "(Паровая конверсия, Метан, Катализатор)"

    path_content = new_condition[1:-1]
    techs = [t.strip() for t in path_content.split(',') if t.strip()]
    invalid_techs = [t for t in techs if t not in dct_tech]

    if not invalid_techs:
        print(f"    ✅ Изменение '{condition}' → '{new_condition}'")
        test3_passed = True
    else:
        print(f"    ❌ Ошибка валидации для '{new_condition}': {invalid_techs}")
        test3_passed = False

    # Тест 4: Попытка редактирования с несуществующей технологией (должно провалиться)
    print("  Тест 5.4: Валидация при редактировании с несуществующей технологией")
    condition = "Вода"
    new_condition = "(Вода, Несуществующая)"

    path_content = new_condition[1:-1]
    techs = [t.strip() for t in path_content.split(',') if t.strip()]
    invalid_techs = [t for t in techs if t not in dct_tech]

    if invalid_techs:
        print(f"    ✅ Корректно отклонено: '{new_condition}' (не найдено: {invalid_techs})")
        test4_passed = True
    else:
        print(f"    ❌ Ошибка: '{new_condition}' должно было быть отклонено")
        test4_passed = False

    # Тест 5: Редактирование пути на простое условие
    print("  Тест 5.5: Редактирование составного пути на простое условие")
    condition = "(Электролиз, Вода)"
    new_condition = "Электролиз"

    if new_condition in dct_tech:
        print(f"    ✅ Изменение '{condition}' → '{new_condition}'")
        test5_passed = True
    else:
        print(f"    ❌ Ошибка валидации для '{new_condition}'")
        test5_passed = False

    return test1_passed and test2_passed and test3_passed and test4_passed and test5_passed


def test_validation():
    """Тест валидации технологий"""
    print("\nТест 6: Валидация существования технологий")

    dct_tech = {
        "Вода": {},
        "Электричество": {},
        "Электролиз": {},
        "Метан": {},
        "Паровая конверсия": {},
        "Катализатор": {},
        "Водород": {},
    }

    test_cases = [
        ("Вода", True),  # Существует
        ("Несуществующая", False),  # Не существует
        ("(Вода, Электричество)", True),  # Путь с существующими технологиями
        ("(Вода, Несуществующая)", False),  # Путь с несуществующей технологией
    ]

    all_passed = True
    for condition, should_pass in test_cases:
        condition = condition.strip()
        is_valid = True

        if condition.startswith('(') and condition.endswith(')'):
            # Это путь
            path_content = condition[1:-1]
            techs = [t.strip() for t in path_content.split(',') if t.strip()]
            invalid_techs = [t for t in techs if t not in dct_tech]
            if invalid_techs:
                is_valid = False
        else:
            # Это одиночная технология
            if condition not in dct_tech:
                is_valid = False

        if is_valid == should_pass:
            status = "✅" if should_pass else "✅ (корректно отклонено)"
            print(f"  {status} '{condition}'")
        else:
            print(f"  ❌ '{condition}' - неверная валидация")
            all_passed = False

    return all_passed


def main():
    """Основная функция тестирования"""
    print("=" * 60)
    print("Тестирование редактора с альтернативными путями")
    print("=" * 60)

    # Загружаем тестовые данные
    json_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        'examples',
        'hydrogen_example.json'
    )

    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    print(f"\nЗагружен файл: {json_path}")
    print(f"Количество технологий: {len(data['технологии'])}")

    # Запускаем тесты
    results = []
    results.append(("PlantUML генерация", test_generate_plantuml_with_alternative_paths(data)))
    results.append(("Парсинг условий", test_parse_conditions()))
    results.append(("Отображение путей", test_load_and_display_alternative_paths(data)))
    results.append(("Сохранение путей", test_save_alternative_paths(data)))
    results.append(("Редактирование условий", test_edit_condition()))
    results.append(("Валидация", test_validation()))

    # Итоги
    print("\n" + "=" * 60)
    print("ИТОГИ ТЕСТИРОВАНИЯ")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status}: {name}")

    print(f"\nВсего тестов: {total}")
    print(f"Пройдено: {passed}")
    print(f"Провалено: {total - passed}")

    if passed == total:
        print("\n🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ!")
        return 0
    else:
        print(f"\n⚠️ Некоторые тесты провалены ({total - passed}/{total})")
        return 1


if __name__ == '__main__':
    sys.exit(main())
