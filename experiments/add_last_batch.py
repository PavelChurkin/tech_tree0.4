#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Add the last batch of missing technologies
"""

import json
import sys

def load_json(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json(filename, data):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def tech_exists(technologies, name):
    return any(tech['название'] == name for tech in technologies)

def add_technology(technologies, название, описание, условия):
    if not tech_exists(technologies, название):
        technologies.append({
            "название": название,
            "описание": описание,
            "условия": условия
        })
        print(f"✓ Added: {название}")
        return True
    else:
        print(f"  Exists: {название}")
        return False

def main():
    print("Loading techno2.json...")
    data = load_json('techno2.json')
    technologies = data['технологии']

    added_count = 0

    print("\nAdding last batch of missing technologies...")

    # Add fasteners (already exist in the tree as "Винты", "Болты", "Гайки")
    # But let's check if they use correct names
    if add_technology(technologies, "Винты",
                     "Крепёжные изделия с внешней резьбой для соединения деталей путём ввинчивания.",
                     ["Металлообработка", "Резьба"]):
        added_count += 1

    if add_technology(technologies, "Болты",
                     "Крепёжные изделия с резьбой и головкой, используемые вместе с гайками для разъёмных соединений.",
                     ["Металлообработка", "Резьба"]):
        added_count += 1

    if add_technology(technologies, "Гайки",
                     "Крепёжные изделия с внутренней резьбой для навинчивания на болты и винты.",
                     ["Металлообработка", "Резьба"]):
        added_count += 1

    if add_technology(technologies, "Резьба",
                     "Спиральный выступ на поверхности цилиндра или конуса для получения разъёмного соединения.",
                     ["Металлообработка", "Резец"]):
        added_count += 1

    # Add chemistry/catalysis
    if add_technology(technologies, "Катализ",
                     "Ускорение химических реакций с помощью катализаторов, которые не расходуются в процессе.",
                     ["Химия"]):
        added_count += 1

    # Add electricity
    if add_technology(technologies, "Электричество",
                     "Форма энергии, связанная с движением электрических зарядов в проводниках и полупроводниках.",
                     ["Генератор электричества"]):
        added_count += 1

    # Add radio technologies
    if add_technology(technologies, "Радиопередатчик",
                     "Устройство для генерации и излучения радиоволн для передачи информации.",
                     ["Электроника", "Антенна", "Электромагнетизм"]):
        added_count += 1

    if add_technology(technologies, "Радиоприёмник",
                     "Устройство для приёма радиоволн и преобразования их в звук или другую информацию.",
                     ["Электроника", "Антенна", "Динамик"]):
        added_count += 1

    # Add materials
    if add_technology(technologies, "Стекловолокно",
                     "Тонкие нити из стекла, используемые для армирования композитных материалов и теплоизоляции.",
                     ["Стекло", "Печь электрическая"]):
        added_count += 1

    if add_technology(technologies, "Нанотехнологии",
                     "Технологии манипуляции материей на атомном и молекулярном уровне (1-100 нанометров).",
                     ["Микроскоп", "Физика", "Химия", "Электроника"]):
        added_count += 1

    # Add speaker if missing
    if add_technology(technologies, "Динамик",
                     "Устройство для преобразования электрических сигналов в звуковые колебания.",
                     ["Электромагнетизм", "Магнит природный", "Провод"]):
        added_count += 1

    print(f"\nTotal technologies added: {added_count}")
    print(f"Total technologies: {len(technologies)}")

    # Save the updated data
    print("\nSaving techno2.json...")
    save_json('techno2.json', data)
    print("✓ Saved successfully!")

    return 0

if __name__ == "__main__":
    sys.exit(main())
