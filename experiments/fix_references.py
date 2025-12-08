#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fix references to renamed technologies
"""

import json
import sys

def load_json(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json(filename, data):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def update_dependency(dep, replacements):
    """Update a single dependency string."""
    for old, new in replacements.items():
        if dep == old:
            return new
    return dep

def update_conditions(conditions, replacements):
    """Update conditions list recursively."""
    if isinstance(conditions, list):
        result = []
        for item in conditions:
            if isinstance(item, list):
                # OR condition - update each element
                result.append([update_dependency(dep, replacements) for dep in item])
            elif isinstance(item, str):
                result.append(update_dependency(item, replacements))
            else:
                result.append(item)
        return result
    elif isinstance(conditions, str):
        return update_dependency(conditions, replacements)
    return conditions

def main():
    print("Loading techno2.json...")
    data = load_json('techno2.json')
    technologies = data['технологии']

    # Define replacements
    replacements = {
        'Магнит': 'Магнит природный',
        'Клей': 'Клей природный'  # Most uses are for natural glue, we'll handle synthetic separately
    }

    # Special cases that should use synthetic glue
    synthetic_glue_techs = {
        'Композитные материалы',
        'Углеродное волокно',
        'Пластиковые трубы',
        'Клей синтетический'  # self-reference
    }

    print("\nUpdating dependencies...")
    updated_count = 0

    for tech in technologies:
        if 'условия' not in tech:
            continue

        tech_name = tech['название']
        conditions = tech['условия']

        # Special handling for technologies that should use synthetic glue
        if tech_name in synthetic_glue_techs:
            # For these, Клей → Клей синтетический
            special_replacements = replacements.copy()
            special_replacements['Клей'] = 'Клей синтетический'
            new_conditions = update_conditions(conditions, special_replacements)
        else:
            new_conditions = update_conditions(conditions, replacements)

        if new_conditions != conditions:
            tech['условия'] = new_conditions
            updated_count += 1
            print(f"✓ Updated: {tech_name}")

    print(f"\nTotal dependencies updated: {updated_count}")

    # Save the updated data
    print("\nSaving techno2.json...")
    save_json('techno2.json', data)
    print("✓ Saved successfully!")

    return 0

if __name__ == "__main__":
    sys.exit(main())
