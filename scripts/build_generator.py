#!/usr/bin/env python3
"""
build_generator.py — Generates PoE2 Build Planner (.json) files.

Creates JSON files compatible with GGG's official Build Planner:
https://www.pathofexile.com/developer/docs/game#build-planner

NOTE: GGG's website Build Planner requires .json extension, not .build
(see https://www.pathofexile.com/forum/view-thread/3972505)

The .build file format is JSON with a single root Build object containing
passives, skills, items, ascendancy, name, and description fields.
"""

import json
import argparse
from pathlib import Path
from datetime import datetime

PROJECT_DIR = Path(__file__).resolve().parent.parent
BUILD_DIR = PROJECT_DIR / "builds"
BUILD_DIR.mkdir(exist_ok=True)


def create_build(name, description, ascendancy, passives, skills, items, include_examples=False):
    """Create a .json build file structure per GGG's schema.

    Args:
        name: Build name
        description: Build description (supports markup)
        ascendancy: Ascendancy class ID (e.g., "Mercenary2", "Huntress1")
        passives: List of passive node IDs or dicts with id/level_interval
        skills: List of skill gem IDs or dicts with id/support_skills
        items: List of BuildItem dicts with inventory_id, slot_x, slot_y
        include_examples: Add example markup/text

    Returns:
        dict matching GGG Build object schema
    """
    build = {
        "name": name,
        "description": description,
        "ascendancy": ascendancy,
        "passives": passives,
        "skills": skills,
        "items": items,
    }
    return build


def save_build(build, filename):
    """Save build dict as a .json file (GGG Build Planner format)."""
    filepath = BUILD_DIR / f"{filename}.json"
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(build, f, indent=2, ensure_ascii=False)
    return filepath


def generate_template(class_name, ascendancy_num=1):
    """Generate a starter template .json build file for a given class + ascendancy.

    Uses the actual GGG data from the skill tree JSON to populate valid node IDs.
    Class starting positions are found via the 'root' node's connections.
    """
    # Load skill tree to get valid node IDs for the class
    tree_path = PROJECT_DIR / "data" / "skill_tree_poe2_v4.5_us.json"
    if tree_path.exists():
        tree_data = json.loads(tree_path.read_text(encoding="utf-8"))
        classes_data = tree_data.get("classes", [])
    else:
        classes_data = []

    # Class name to starting node name mapping (PoE2 uses same class names as PoE1)
    class_name_map = {
        "Marauder": "MARAUDER",
        "Witch": "WITCH",
        "Ranger": "RANGER",
        "Duelist": "DUELIST",
        "Shadow": "SIX",
        "Templar": "TEMPLAR",
        "Scion": "SCION",
    }

    ascendancy_id = f"{class_name}{ascendancy_num}"

    # Get sample passive nodes from the class's starting area
    passives = []
    if tree_data:
        # Find class starting node via root connections
        nodes = tree_data.get("nodes", {})
        root_node = nodes.get("root", {})
        class_start_nodes = {}
        for nid in root_node.get("out", []):
            n = nodes.get(nid, {})
            if isinstance(n, dict):
                class_start_nodes[n.get("name", "")] = nid

        # Get the class starting node
        start_name = class_name_map.get(class_name, class_name.upper())
        start_node_id = class_start_nodes.get(start_name)

        if start_node_id:
            start_node = nodes.get(start_node_id, {})
            group_id = start_node.get("group", 0)
            group = tree_data.get("groups", {}).get(str(group_id), {})
            start_x = group.get("x", 0)
            start_y = group.get("y", 0)
            # GGG tree coordinates are in large units (~22k range), use larger radius
            nearby_nodes = _find_nearby_nodes(tree_data, start_x, start_y, 3000)
            # Filter out ascendancy nodes
            nodes_data = tree_data.get("nodes", {})
            passives = [n for n in nearby_nodes if not nodes_data.get(n, {}).get("isAscendancy", False)][:30]

    build = {
        "name": f"{class_name} Starter Template",
        "description": f"A starter {class_name} build template. Replace with your own name/description.",
        "ascendancy": ascendancy_id,
        "passives": passives,
        "skills": [],
        "items": [],
    }
    return build


def _find_nearby_nodes(tree_data, center_x, center_y, max_dist=200):
    """Find passive skill nodes near given coordinates in the skill tree.
    
    Uses group coordinates (not node coordinates, which are often None)
    to determine proximity.
    """
    groups = tree_data.get("groups", {})
    nearby = []
    for gid_str, group in groups.items():
        if not isinstance(group, dict):
            continue
        gx = group.get("x", None)
        gy = group.get("y", None)
        if gx is None or gy is None:
            continue
        dx = gx - center_x
        dy = gy - center_y
        dist = (dx ** 2 + dy ** 2) ** 0.5
        if dist <= max_dist:
            for node_id in group.get("nodes", []):
                nearby.append(node_id)
    # Deduplicate while preserving order
    seen = set()
    result = []
    for n in nearby:
        if n not in seen:
            seen.add(n)
            result.append(n)
    return result


def list_available_classes():
    """List all available classes from the downloaded skill tree data."""
    tree_path = BUILD_DIR.parent / "data" / "skill_tree_poe2_v4.5_us.json"
    if not tree_path.exists():
        return []
    tree_data = json.loads(tree_path.read_text(encoding="utf-8"))
    classes_data = tree_data.get("classes", [])
    if isinstance(classes_data, list):
        return [c.get("name", "") for c in classes_data if isinstance(c, dict) and "name" in c]
    elif isinstance(classes_data, dict):
        return list(classes_data.keys())
    return []


def main():
    parser = argparse.ArgumentParser(description="Generate PoE2 .build files")
    parser.add_argument("--name", "-n", required=False, help="Build name")
    parser.add_argument("--description", "-d", help="Build description (supports markup)")
    parser.add_argument("--class", "-c", required=False, dest="class_name", help="Class name (e.g., Mercenary, Huntress, Witch)")
    parser.add_argument("--ascendancy", "-a", type=int, default=1, help="Ascendancy number (1-3)")
    parser.add_argument(
        "--template", action="store_true",
        help="Generate a starter template with nearby passive nodes"
    )
    parser.add_argument(
        "--passives", "-p", nargs="+",
        help="List of passive node IDs (or 'nearby:N' for N nearby default nodes)"
    )
    parser.add_argument(
        "--skills", "-s", nargs="+",
        help="List of skill gem IDs"
    )
    parser.add_argument(
        "--output", "-o",
        help="Output filename (without .json extension)"
    )
    parser.add_argument(
        "--list-classes", action="store_true",
        help="List all available classes from skill tree data"
    )

    args = parser.parse_args()

    if args.list_classes:
        classes = list_available_classes()
        print("Available classes:")
        for c in classes:
            print(f"  - {c}")
        return

    if not args.name or not args.class_name:
        parser.error("--name and --class are required unless --list-classes is used")

    # Parse passives
    passives = []
    if args.passives:
        for p in args.passives:
            if p.startswith("nearby:"):
                n = int(p.split(":")[1])
                template = generate_template(args.class_name, args.ascendancy)
                passives = template["passives"][:n]
                break
            else:
                passives.append(p)

    if not passives and args.template:
        passives = generate_template(args.class_name, args.ascendancy)["passives"]

    # Parse skills
    skills = []
    if args.skills:
        for s in args.skills:
            if ":" in s:
                gem_id, supports = s.split(":", 1)
                skills.append({
                    "id": gem_id,
                    "support_skills": supports.split(",")
                })
            else:
                skills.append(s)

    description = args.description or f"Generated build: {args.name}"
    build = create_build(
        name=args.name,
        description=description,
        ascendancy=f"{args.class_name}{args.ascendancy}",
        passives=passives,
        skills=skills,
        items=[],
    )

    filename = args.output or args.name.lower().replace(" ", "_")
    filepath = save_build(build, filename)
    print(f"✅ Build saved to: {filepath}")
    print(f"   Passives: {len(passives)}")
    print(f"   Skills: {len(skills)}")
    print(f"   Ascendancy: {build['ascendancy']}")


if __name__ == "__main__":
    main()
