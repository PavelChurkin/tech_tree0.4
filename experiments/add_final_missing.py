#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Add final missing technologies
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

def main():
    print("Loading techno2.json...")
    data = load_json('techno2.json')
    technologies = data['технологии']

    added_count = 0

    print("\nAdding final missing technologies...")

    # Infrastructure and basic tech
    if add_technology(technologies, "Электросеть",
                     "Система линий и подстанций для распределения электроэнергии от электростанций к потребителям.",
                     ["Генератор электричества", "Провод", "Трансформатор"]):
        added_count += 1

    if add_technology(technologies, "Реактор",
                     "Устройство для осуществления управляемой цепной ядерной реакции деления.",
                     ["Физика", "Уран", "Графит"]):
        added_count += 1

    # Tools and fasteners
    if add_technology(technologies, "Ножницы",
                     "Режущий инструмент из двух лезвий, соединённых осью для резки ткани, бумаги и других материалов.",
                     ["Кузнечное дело", "Винты"]):
        added_count += 1

    if add_technology(technologies, "Топор",
                     "Рубящий инструмент с лезвием, закреплённым на рукояти, используемый для рубки дерева.",
                     ["Кузнечное дело"]):
        added_count += 1

    # Chemicals
    if add_technology(technologies, "Спирт",
                     "Этиловый спирт (этанол), бесцветная жидкость, используемая в медицине как антисептик и в химии.",
                     ["Дистилляция", "Виноделие"]):
        added_count += 1

    if add_technology(technologies, "Соль",
                     "Хлорид натрия, важнейшая пищевая добавка и химическое сырьё, добываемая из соляных месторождений.",
                     []):
        added_count += 1

    if add_technology(technologies, "Уран",
                     "Радиоактивный металл, используемый как топливо в ядерных реакторах.",
                     ["Металлургия промышленная", "Химия"]):
        added_count += 1

    # Biology/Medicine
    if add_technology(technologies, "Микробиология",
                     "Наука о микроорганизмах, их строении, жизнедеятельности и роли в природе и жизни человека.",
                     ["Медицина", "Микроскоп"]):
        added_count += 1

    # Production processes
    if add_technology(technologies, "Ёмкость",
                     "Сосуд для хранения или обработки жидкостей и сыпучих материалов.",
                     [["Керамика"], ["Металлообработка"]]):
        added_count += 1

    if add_technology(technologies, "Осциллограф",
                     "Прибор для наблюдения и измерения электрических сигналов во времени на экране.",
                     ["Электронно-лучевая трубка", "Электроника"]):
        added_count += 1

    if add_technology(technologies, "Антенна",
                     "Устройство для излучения и приёма радиоволн в радиосвязи и радиовещании.",
                     ["Провод", "Радиопередатчик"]):
        added_count += 1

    if add_technology(technologies, "Провод",
                     "Металлический проводник для передачи электрического тока, обычно покрытый изоляцией.",
                     ["Медь", "Волочение"]):
        added_count += 1

    if add_technology(technologies, "Верёвка",
                     "Изделие из скрученных или сплетённых волокон для связывания, подъёма грузов и других целей.",
                     [["Текстильная промышленность"], ["Земледелие"]]):
        added_count += 1

    if add_technology(technologies, "Серная кислота",
                     "Сильная двухосновная кислота (H2SO4), важнейший продукт химической промышленности.",
                     ["Производство кислот", "Сера"]):
        added_count += 1

    if add_technology(technologies, "Сера",
                     "Неметалл жёлтого цвета, используемый в химической промышленности для производства кислот и вулканизации.",
                     ["Горное дело"]):
        added_count += 1

    if add_technology(technologies, "Горное дело",
                     "Отрасль по добыче полезных ископаемых из недр земли через шахты и карьеры.",
                     ["Обработка камня", "Кузнечное дело"]):
        added_count += 1

    if add_technology(technologies, "Волочение",
                     "Процесс протягивания металла через отверстие для получения проволоки или прутков.",
                     ["Металлообработка", "Фильера"]):
        added_count += 1

    if add_technology(technologies, "Фильера",
                     "Инструмент с калиброванным отверстием для волочения проволоки и изготовления нитей.",
                     ["Металлообработка", "Сверло"]):
        added_count += 1

    if add_technology(technologies, "Графит",
                     "Форма углерода с слоистой структурой, используемая в карандашах, смазках и как замедлитель в реакторах.",
                     ["Горное дело"]):
        added_count += 1

    if add_technology(technologies, "Медь",
                     "Красновато-золотистый металл с высокой электро- и теплопроводностью.",
                     ["Металлургия примитивная"]):
        added_count += 1

    if add_technology(technologies, "Электронно-лучевая трубка",
                     "Вакуумный прибор для преобразования электрических сигналов в видимое изображение на люминесцентном экране.",
                     ["Электроника", "Стекло", "Вакуумный насос"]):
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
