#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fix final issues: missing dependencies and cycles
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

def find_tech(technologies, name):
    for tech in technologies:
        if tech['название'] == name:
            return tech
    return None

def main():
    print("Loading techno2.json...")
    data = load_json('techno2.json')
    technologies = data['технологии']

    added_count = 0
    fixed_count = 0

    print("\n" + "="*80)
    print("Adding missing technologies")
    print("="*80)

    if add_technology(technologies, "Ракета",
                     "Летательный аппарат с реактивным двигателем для полёта в атмосфере и космосе.",
                     ["Реактивный двигатель", "Металлообработка", "Топливный бак"]):
        added_count += 1

    if add_technology(technologies, "Гироскоп",
                     "Устройство с быстро вращающимся ротором для определения ориентации в пространстве.",
                     ["Металлообработка", "Подшипник"]):
        added_count += 1

    if add_technology(technologies, "Пайка",
                     "Процесс соединения металлических деталей расплавленным припоем при температуре ниже их плавления.",
                     ["Паяльник", "Олово"]):
        added_count += 1

    if add_technology(technologies, "Паяльник",
                     "Инструмент для нагрева припоя при пайке металлических изделий.",
                     ["Кузнечное дело", "Медь"]):
        added_count += 1

    if add_technology(technologies, "Литьё",
                     "Процесс получения изделий путём заливки расплавленного металла в литейную форму.",
                     ["Металлургия примитивная", "Форма для литья"]):
        added_count += 1

    if add_technology(technologies, "Форма для литья",
                     "Ёмкость с полостью определённой формы для заливки расплавленного материала.",
                     ["Керамика", "Обработка дерева"]):
        added_count += 1

    if add_technology(technologies, "Вальцы",
                     "Машина с вращающимися валками для прокатки металла в листы и полосы.",
                     ["Металлообработка", "Паровой двигатель", "Вал"]):
        added_count += 1

    if add_technology(technologies, "Реактивный двигатель",
                     "Двигатель, создающий тягу за счёт выброса реактивной струи газов при сгорании топлива.",
                     ["Турбина", "Топливный бак", "Камера сгорания"]):
        added_count += 1

    if add_technology(technologies, "Топливный бак",
                     "Ёмкость для хранения топлива в транспортных средствах и двигателях.",
                     ["Листовой металл", "Сварка"]):
        added_count += 1

    if add_technology(technologies, "Камера сгорания",
                     "Полость в двигателе, где происходит сжигание топлива для получения энергии.",
                     ["Металлообработка", "Литьё"]):
        added_count += 1

    print("\n" + "="*80)
    print("Fixing circular dependency: Антенна ↔ Радиопередатчик")
    print("="*80)

    # Fix: Антенна should not depend on Радиопередатчик
    antenna = find_tech(technologies, "Антенна")
    if antenna:
        # Remove Радиопередатчик from dependencies
        new_conditions = []
        for dep in antenna['условия']:
            if isinstance(dep, list):
                new_dep = [d for d in dep if d != 'Радиопередатчик']
                if new_dep:
                    new_conditions.append(new_dep if len(new_dep) > 1 else new_dep[0])
            elif dep != 'Радиопередатчик':
                new_conditions.append(dep)

        antenna['условия'] = new_conditions if new_conditions else ["Провод"]
        print(f"✓ Fixed: Антенна dependencies: {antenna['условия']}")
        fixed_count += 1

    print(f"\n{'='*80}")
    print(f"SUMMARY")
    print(f"{'='*80}")
    print(f"Technologies added: {added_count}")
    print(f"Circular dependencies fixed: {fixed_count}")
    print(f"Total technologies: {len(technologies)}")

    # Save the updated data
    print("\nSaving techno2.json...")
    save_json('techno2.json', data)
    print("✓ Saved successfully!")

    return 0

if __name__ == "__main__":
    sys.exit(main())
