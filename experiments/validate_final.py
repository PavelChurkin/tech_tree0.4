#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Comprehensive validation script for techno2.json
"""

import json
import sys
from collections import defaultdict

def load_json(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        return json.load(f)

def validate():
    print("Loading techno2.json...")
    data = load_json('techno2.json')
    technologies = data['технологии']

    print(f"\n{'='*80}")
    print(f"VALIDATION REPORT")
    print(f"{'='*80}\n")

    print(f"Total technologies: {len(technologies)}")

    # Create a set of all technology names
    tech_names = {tech['название'] for tech in technologies}
    print(f"Unique technology names: {len(tech_names)}")

    # Check for duplicates
    name_counts = defaultdict(int)
    for tech in technologies:
        name_counts[tech['название']] += 1

    duplicates = {name: count for name, count in name_counts.items() if count > 1}
    if duplicates:
        print(f"\n❌ DUPLICATES FOUND: {len(duplicates)}")
        for name, count in duplicates.items():
            print(f"  - {name}: {count} times")
    else:
        print("✓ No duplicates found")

    # Check for technologies without descriptions
    no_desc = []
    empty_desc = []
    for tech in technologies:
        if 'описание' not in tech:
            no_desc.append(tech['название'])
        elif not tech['описание'] or tech['описание'].strip() == '' or tech['описание'].lower() == 'пусто':
            empty_desc.append(tech['название'])

    if no_desc or empty_desc:
        print(f"\n❌ MISSING DESCRIPTIONS: {len(no_desc) + len(empty_desc)}")
        if no_desc:
            print(f"  Missing 'описание' field: {len(no_desc)}")
            for name in no_desc[:5]:
                print(f"    - {name}")
        if empty_desc:
            print(f"  Empty descriptions: {len(empty_desc)}")
            for name in empty_desc[:5]:
                print(f"    - {name}")
    else:
        print("✓ All technologies have descriptions")

    # Check for missing dependencies
    missing_deps = []
    for tech in technologies:
        if 'условия' not in tech:
            continue

        conditions = tech['условия']
        if isinstance(conditions, list):
            for item in conditions:
                if isinstance(item, list):
                    # OR condition
                    for dep in item:
                        if dep not in tech_names:
                            missing_deps.append((tech['название'], dep))
                elif isinstance(item, str):
                    if item not in tech_names:
                        missing_deps.append((tech['название'], item))

    if missing_deps:
        print(f"\n❌ MISSING DEPENDENCIES: {len(missing_deps)}")
        for tech_name, dep_name in missing_deps[:10]:
            print(f"  - {tech_name} depends on non-existent '{dep_name}'")
        if len(missing_deps) > 10:
            print(f"  ... and {len(missing_deps) - 10} more")
    else:
        print("✓ All dependencies exist")

    # Check for direct cycles (A depends on B, B depends on A)
    def get_direct_deps(tech):
        deps = set()
        if 'условия' not in tech:
            return deps
        conditions = tech['условия']
        if isinstance(conditions, list):
            for item in conditions:
                if isinstance(item, list):
                    deps.update(item)
                elif isinstance(item, str):
                    deps.add(item)
        return deps

    tech_dict = {tech['название']: tech for tech in technologies}
    direct_cycles = []

    for tech in technologies:
        tech_name = tech['название']
        direct_deps = get_direct_deps(tech)
        for dep_name in direct_deps:
            if dep_name in tech_dict:
                dep_deps = get_direct_deps(tech_dict[dep_name])
                if tech_name in dep_deps:
                    cycle = (min(tech_name, dep_name), max(tech_name, dep_name))
                    if cycle not in direct_cycles:
                        direct_cycles.append(cycle)

    if direct_cycles:
        print(f"\n❌ DIRECT CYCLES: {len(direct_cycles)}")
        for tech1, tech2 in direct_cycles:
            print(f"  - {tech1} ↔ {tech2}")
    else:
        print("✓ No direct cycles found")

    # Statistics
    print(f"\n{'='*80}")
    print(f"STATISTICS")
    print(f"{'='*80}\n")

    # Count technologies by dependency count
    dep_counts = defaultdict(int)
    for tech in technologies:
        if 'условия' not in tech or not tech['условия']:
            dep_counts[0] += 1
        else:
            deps = get_direct_deps(tech)
            dep_counts[len(deps)] += 1

    print("Technologies by dependency count:")
    for count in sorted(dep_counts.keys()):
        print(f"  {count} dependencies: {dep_counts[count]} technologies")

    # Find technologies with no dependencies (base technologies)
    base_techs = [tech['название'] for tech in technologies
                  if 'условия' not in tech or not tech['условия']]
    print(f"\nBase technologies (no dependencies): {len(base_techs)}")
    for name in sorted(base_techs)[:10]:
        print(f"  - {name}")
    if len(base_techs) > 10:
        print(f"  ... and {len(base_techs) - 10} more")

    # Find technologies with most dependencies
    max_deps = []
    for tech in technologies:
        deps = get_direct_deps(tech)
        if deps:
            max_deps.append((tech['название'], len(deps)))

    max_deps.sort(key=lambda x: x[1], reverse=True)
    print(f"\nTechnologies with most dependencies:")
    for name, count in max_deps[:5]:
        print(f"  - {name}: {count} dependencies")

    # Final verdict
    print(f"\n{'='*80}")
    if not duplicates and not no_desc and not empty_desc and not missing_deps and not direct_cycles:
        print("✅ ALL VALIDATION CHECKS PASSED!")
        print(f"{'='*80}\n")
        return 0
    else:
        print("⚠️  VALIDATION COMPLETED WITH WARNINGS")
        print(f"{'='*80}\n")
        return 1

if __name__ == "__main__":
    sys.exit(validate())
