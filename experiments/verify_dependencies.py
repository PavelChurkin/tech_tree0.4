#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script to verify dependencies in techno2.json
"""

import json

# Load the JSON file
with open('techno2.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

technologies = data['технологии']
tech_names = {tech['название'] for tech in technologies}

print(f"Total technologies: {len(technologies)}")
print(f"Unique names: {len(tech_names)}")

# Check for duplicates
name_counts = {}
for tech in technologies:
    name = tech['название']
    name_counts[name] = name_counts.get(name, 0) + 1

duplicates = {name: count for name, count in name_counts.items() if count > 1}
if duplicates:
    print(f"\nDUPLICATES FOUND: {duplicates}")
else:
    print("\nNo duplicates found ✓")

# Check for missing dependencies
missing_deps = []
for tech in technologies:
    name = tech['название']
    условия = tech.get('условия', [])

    # Handle both simple list and list of alternatives
    if isinstance(условия, list):
        for условие in условия:
            if isinstance(условие, list):
                # Alternative path
                for dep in условие:
                    if dep not in tech_names:
                        missing_deps.append((name, dep))
            elif isinstance(условие, str):
                if условие not in tech_names:
                    missing_deps.append((name, условие))

if missing_deps:
    print(f"\nMISSING DEPENDENCIES: {len(missing_deps)}")
    for tech, dep in missing_deps[:10]:  # Show first 10
        print(f"  {tech} requires missing: {dep}")
    if len(missing_deps) > 10:
        print(f"  ... and {len(missing_deps) - 10} more")
else:
    print("\nNo missing dependencies ✓")

# Check for technologies without descriptions
no_desc = [tech['название'] for tech in technologies if not tech.get('описание') or tech['описание'] in ['', 'Пусто']]
if no_desc:
    print(f"\nTECHNOLOGIES WITHOUT DESCRIPTION: {len(no_desc)}")
    for name in no_desc[:10]:
        print(f"  - {name}")
else:
    print("\nAll technologies have descriptions ✓")

# Check for circular dependencies (simple check - direct circles only)
print("\nChecking for direct circular dependencies...")
circular = []
for tech in technologies:
    name = tech['название']
    условия = tech.get('условия', [])

    if isinstance(условия, list):
        for условие in условия:
            if isinstance(условие, str) and условие in tech_names:
                # Check if the dependency also depends on this tech
                dep_tech = next((t for t in technologies if t['название'] == условие), None)
                if dep_tech:
                    dep_условия = dep_tech.get('условия', [])
                    if isinstance(dep_условия, list):
                        for dep_условие in dep_условия:
                            if isinstance(dep_условие, str) and dep_условие == name:
                                circular.append((name, условие))

if circular:
    print(f"CIRCULAR DEPENDENCIES FOUND: {len(circular)}")
    for a, b in circular:
        print(f"  {a} ↔ {b}")
else:
    print("No direct circular dependencies found ✓")

print("\nVerification complete!")
