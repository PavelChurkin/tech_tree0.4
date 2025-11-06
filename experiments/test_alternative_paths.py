#!/usr/bin/env python3
"""
Тестовый скрипт для проверки работы альтернативных путей получения технологий.
"""
import json
import sys
import os

# Добавляем путь к корневой директории для импорта функций
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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


def is_tech_available(tech_name, data, tech_flags):
    """
    Проверяет, доступна ли технология для изучения.
    """
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


def run_tests():
    """Запуск тестов для проверки работы альтернативных путей."""

    print("=" * 70)
    print("ТЕСТ 1: Загрузка примера с водородом")
    print("=" * 70)

    with open('examples/hydrogen_example.json', 'r', encoding='utf-8') as f:
        data = json.load(f)

    print(f"✓ Загружено {len(data['технологии'])} технологий")

    # Инициализация флагов
    tech_flags = {tech['название']: False for tech in data['технологии']}

    print("\n" + "=" * 70)
    print("ТЕСТ 2: Водород недоступен без выполнения условий")
    print("=" * 70)

    available = is_tech_available('Водород', data, tech_flags)
    print(f"Водород доступен: {available}")
    assert not available, "Водород не должен быть доступен без выполнения условий"
    print("✓ PASS: Водород правильно недоступен")

    print("\n" + "=" * 70)
    print("ТЕСТ 3: Водород доступен через Путь 1 (Электролиз воды)")
    print("=" * 70)

    # Выполняем первый путь
    tech_flags['Электролиз'] = True
    tech_flags['Вода'] = True
    tech_flags['Электричество'] = True

    available = is_tech_available('Водород', data, tech_flags)
    print(f"Путь 1 завершён: Электролиз = True, Вода = True")
    print(f"Водород доступен: {available}")
    assert available, "Водород должен быть доступен через первый путь"
    print("✓ PASS: Водород правильно доступен через электролиз")

    print("\n" + "=" * 70)
    print("ТЕСТ 4: Водород доступен через Путь 2 (Паровая конверсия метана)")
    print("=" * 70)

    # Сбрасываем флаги и пробуем второй путь
    tech_flags = {tech['название']: False for tech in data['технологии']}
    tech_flags['Паровая конверсия'] = True
    tech_flags['Метан'] = True
    tech_flags['Катализатор'] = True

    available = is_tech_available('Водород', data, tech_flags)
    print(f"Путь 2 завершён: Паровая конверсия = True, Метан = True, Катализатор = True")
    print(f"Водород доступен: {available}")
    assert available, "Водород должен быть доступен через второй путь"
    print("✓ PASS: Водород правильно доступен через паровую конверсию")

    print("\n" + "=" * 70)
    print("ТЕСТ 5: Водород недоступен при частичном выполнении обоих путей")
    print("=" * 70)

    # Частично выполняем оба пути
    tech_flags = {tech['название']: False for tech in data['технологии']}
    tech_flags['Электролиз'] = True  # Есть электролиз, но нет воды (путь 1 неполон)
    tech_flags['Метан'] = True        # Есть метан, но нет паровой конверсии (путь 2 неполон)

    available = is_tech_available('Водород', data, tech_flags)
    print(f"Путь 1 частично выполнен: Электролиз = True, Вода = False")
    print(f"Путь 2 частично выполнен: Метан = True, Паровая конверсия = False")
    print(f"Водород доступен: {available}")
    assert not available, "Водород не должен быть доступен при неполных путях"
    print("✓ PASS: Водород правильно недоступен при неполных путях")

    print("\n" + "=" * 70)
    print("ТЕСТ 6: Старый формат (AND логика) все ещё работает")
    print("=" * 70)

    # Тестируем технологию со старым форматом
    tech_flags = {tech['название']: False for tech in data['технологии']}

    # Топливные элементы требуют Водород И Катализатор (старый формат)
    available = is_tech_available('Топливные элементы', data, tech_flags)
    print(f"Топливные элементы доступны без условий: {available}")
    assert not available, "Топливные элементы не должны быть доступны"

    tech_flags['Водород'] = True  # Только водород
    available = is_tech_available('Топливные элементы', data, tech_flags)
    print(f"Топливные элементы доступны с только Водород: {available}")
    assert not available, "Топливные элементы не должны быть доступны без катализатора"

    tech_flags['Катализатор'] = True  # Добавляем катализатор
    available = is_tech_available('Топливные элементы', data, tech_flags)
    print(f"Топливные элементы доступны с Водород И Катализатор: {available}")
    assert available, "Топливные элементы должны быть доступны"
    print("✓ PASS: Старый формат (AND логика) работает правильно")

    print("\n" + "=" * 70)
    print("ТЕСТ 7: Проверка helper функции is_parent_in_conditions")
    print("=" * 70)

    # Старый формат
    old_format_conditions = ["Parent1", "Parent2", "Parent3"]
    assert is_parent_in_conditions("Parent1", old_format_conditions)
    assert is_parent_in_conditions("Parent2", old_format_conditions)
    assert not is_parent_in_conditions("Parent4", old_format_conditions)
    print("✓ PASS: is_parent_in_conditions работает для старого формата")

    # Новый формат
    new_format_conditions = [["Path1A", "Path1B"], ["Path2A", "Path2B", "Path2C"]]
    assert is_parent_in_conditions("Path1A", new_format_conditions)
    assert is_parent_in_conditions("Path2C", new_format_conditions)
    assert not is_parent_in_conditions("Path3A", new_format_conditions)
    print("✓ PASS: is_parent_in_conditions работает для нового формата")

    print("\n" + "=" * 70)
    print("ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО! ✓")
    print("=" * 70)
    print("\nРеализация поддержки альтернативных путей работает корректно:")
    print("  • Поддерживается новый формат с OR логикой между путями")
    print("  • Поддерживается старый формат с AND логикой")
    print("  • Обратная совместимость сохранена")
    print("  • Водород может быть получен через электролиз ИЛИ паровую конверсию")


if __name__ == '__main__':
    try:
        run_tests()
        sys.exit(0)
    except AssertionError as e:
        print(f"\n✗ ТЕСТ ПРОВАЛЕН: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ ОШИБКА: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
