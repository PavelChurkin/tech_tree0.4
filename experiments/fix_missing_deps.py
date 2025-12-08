#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fix missing dependencies by adding missing technologies or updating references
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
    return False

def update_dependency_in_tech(tech, old_name, new_name):
    """Update a specific dependency in a technology."""
    if 'условия' not in tech:
        return False

    updated = False
    conditions = tech['условия']

    if isinstance(conditions, list):
        for i, item in enumerate(conditions):
            if isinstance(item, list):
                # OR condition
                for j, dep in enumerate(item):
                    if dep == old_name:
                        conditions[i][j] = new_name
                        updated = True
            elif isinstance(item, str):
                if item == old_name:
                    conditions[i] = new_name
                    updated = True

    return updated

def main():
    print("Loading techno2.json...")
    data = load_json('techno2.json')
    technologies = data['технологии']

    added_count = 0
    updated_count = 0

    print("\n" + "="*80)
    print("Adding missing base technologies")
    print("="*80)

    # Add missing base technologies
    if add_technology(technologies, "Стекло",
                     "Прозрачный твёрдый материал, получаемый при охлаждении расплава кремнезёма с добавками.",
                     ["Стеклодувное дело"]):
        added_count += 1

    if add_technology(technologies, "Металлообработка",
                     "Комплекс технологий обработки металлов: ковка, литьё, резание, сварка для создания изделий.",
                     ["Кузнечное дело", "Токарный станок1"]):
        added_count += 1

    if add_technology(technologies, "Вентилятор",
                     "Устройство для перемещения воздуха с помощью вращающихся лопастей.",
                     ["Электродвигатель", "Лопасти"]):
        added_count += 1

    if add_technology(technologies, "Генератор электричества",
                     "Устройство для преобразования механической энергии в электрическую с помощью электромагнитной индукции.",
                     ["Электромагнетизм", "Магнит природный", "Провод"]):
        added_count += 1

    # Add missing technologies that should have been there
    if add_technology(technologies, "Камень",
                     "Твёрдая горная порода, базовый строительный и инструментальный материал.",
                     []):
        added_count += 1

    if add_technology(technologies, "Обработка дерева",
                     "Технология обработки древесины: рубка, тёска, распиловка для изготовления изделий.",
                     ["Топор"]):
        added_count += 1

    print("\n" + "="*80)
    print("Fixing dependency references")
    print("="*80)

    # Fix references to non-existent technologies
    dependency_fixes = {
        'Печь': 'Кирпичная печь',
        'Ядерная физика': 'Физика',
    }

    for old_name, new_name in dependency_fixes.items():
        print(f"\nReplacing '{old_name}' → '{new_name}'")
        for tech in technologies:
            if update_dependency_in_tech(tech, old_name, new_name):
                print(f"  ✓ Updated: {tech['название']}")
                updated_count += 1

    # Special fixes for specific technologies
    print("\n" + "="*80)
    print("Special fixes")
    print("="*80)

    # Fix "Строительство" to depend on existing technology
    for tech in technologies:
        if tech['название'] == 'Строительство':
            tech['условия'] = [["Камень"], ["Обработка дерева"]]
            print("✓ Fixed: Строительство dependencies")
            updated_count += 1
            break

    # Update "Листовой металл" dependencies
    for tech in technologies:
        if tech['название'] == 'Листовой металл':
            # Check if Прокатный стан exists
            if tech_exists(technologies, 'Прокатный стан'):
                tech['условия'] = ['Прокатный стан', 'Металлургия промышленная']
            else:
                tech['условия'] = ['Вальцы', 'Металлургия промышленная']
            print("✓ Fixed: Листовой металл dependencies")
            updated_count += 1
            break

    print(f"\n{'='*80}")
    print(f"SUMMARY")
    print(f"{'='*80}")
    print(f"Technologies added: {added_count}")
    print(f"Dependencies updated: {updated_count}")
    print(f"Total technologies: {len(technologies)}")

    # Save the updated data
    print("\nSaving techno2.json...")
    save_json('techno2.json', data)
    print("✓ Saved successfully!")

    return 0

if __name__ == "__main__":
    sys.exit(main())
