#!/usr/bin/env python3
import argparse
import dataclasses
import re
from pathlib import Path


ASSIGN_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)=(.*)$")
FUNC_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)\(\)\s*\{")
YAML_ITEM_RE = re.compile(r"^\s*-\s+name:\s*['\"]?([^'\"\s#]+)")
YAML_SECTION_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_-]*):\s*$")


@dataclasses.dataclass
class JinxRecipe:
    kind: str
    name: str
    path: Path
    fields: dict[str, str]
    functions: list[str]
    old_patch_dir: Path | None
    new_patch_dir: Path | None


def shell_unquote(value: str) -> str:
    value = value.strip()
    if "#" in value:
        quote = None
        out = []
        for ch in value:
            if ch in ("'", '"'):
                quote = None if quote == ch else ch if quote is None else quote
            if ch == "#" and quote is None:
                break
            out.append(ch)
        value = "".join(out).strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
        value = value[1:-1]
    return value


def parse_jinx_recipe(path: Path, kind: str, root: Path) -> JinxRecipe:
    fields = {}
    functions = []
    for line in path.read_text(errors="replace").splitlines():
        match = ASSIGN_RE.match(line.strip())
        if match:
            fields[match.group(1)] = shell_unquote(match.group(2))
            continue
        match = FUNC_RE.match(line.strip())
        if match:
            functions.append(match.group(1))

    name = fields.get("name", path.name)
    old_patch_dir = root / "uts" / "patches" / name
    new_patch_dir = root / "patches" / name
    return JinxRecipe(
        kind=kind,
        name=name,
        path=path,
        fields=fields,
        functions=functions,
        old_patch_dir=old_patch_dir if old_patch_dir.is_dir() else None,
        new_patch_dir=new_patch_dir if new_patch_dir.is_dir() else None,
    )


def parse_bootstrap_names(root: Path) -> dict[str, set[str]]:
    names = {"sources": set(), "tools": set(), "packages": set()}
    for path in sorted((root / "bootstrap.d").glob("*.y4.yml")):
        section = None
        for line in path.read_text(errors="replace").splitlines():
            section_match = YAML_SECTION_RE.match(line)
            if section_match:
                candidate = section_match.group(1)
                section = candidate if candidate in names else None
                continue
            item_match = YAML_ITEM_RE.match(line)
            if section and item_match:
                names[section].add(item_match.group(1))
    return names


def collect_recipes(root: Path) -> list[JinxRecipe]:
    recipe_dirs = [
        ("source", root / "uts" / "source-recipes"),
        ("package", root / "uts" / "recipes"),
        ("host-tool", root / "uts" / "host-recipes"),
    ]
    recipes = []
    for kind, directory in recipe_dirs:
        if not directory.is_dir():
            continue
        for path in sorted(p for p in directory.iterdir() if p.is_file()):
            recipes.append(parse_jinx_recipe(path, kind, root))
    return recipes


def field(recipe: JinxRecipe, name: str) -> str:
    value = recipe.fields.get(name)
    return value if value else "-"


def patch_status(recipe: JinxRecipe) -> str:
    if recipe.new_patch_dir and recipe.old_patch_dir:
        return "old+new"
    if recipe.new_patch_dir:
        return "new"
    if recipe.old_patch_dir:
        return "old"
    return "-"


def migration_status(recipe: JinxRecipe, bootstrap_names: dict[str, set[str]]) -> str:
    if recipe.kind == "source":
        return "present" if recipe.name in bootstrap_names["sources"] else "missing"
    if recipe.kind == "host-tool":
        host_name = f"host-{recipe.name}"
        if host_name in bootstrap_names["tools"] or recipe.name in bootstrap_names["tools"]:
            return "present"
        return "missing"
    if recipe.name in bootstrap_names["packages"]:
        return "present"
    return "missing"


def render_report(root: Path, recipes: list[JinxRecipe], bootstrap_names: dict[str, set[str]]) -> str:
    lines = [
        "# Jinx to xbstrap migration audit",
        "",
        "Generated from the old Jinx tree under `uts/` and the current xbstrap recipes under `bootstrap.d/`.",
        "",
        "Patch status means:",
        "",
        "- `old`: a patch directory exists only under `uts/patches/<name>`.",
        "- `new`: a patch directory exists only under `patches/<name>`.",
        "- `old+new`: both trees have a patch directory; compare before dropping either side.",
        "",
    ]

    by_kind = {}
    for recipe in recipes:
        by_kind.setdefault(recipe.kind, []).append(recipe)

    for kind in ("source", "host-tool", "package"):
        group = by_kind.get(kind, [])
        present = sum(1 for r in group if migration_status(r, bootstrap_names) == "present")
        lines.append(f"## {kind.title()} recipes")
        lines.append("")
        lines.append(f"{present}/{len(group)} already have a matching xbstrap entry.")
        lines.append("")
        lines.append("| Done | Name | Status | Version | Revision | Patches | Dependencies | Custom steps | Old recipe |")
        lines.append("| --- | --- | --- | --- | --- | --- | --- | --- | --- |")
        for recipe in group:
            status = migration_status(recipe, bootstrap_names)
            done = "x" if status == "present" and patch_status(recipe) in ("-", "new") else " "
            deps = " ".join(
                value
                for value in (
                    recipe.fields.get("hostdeps"),
                    recipe.fields.get("hostrundeps"),
                    recipe.fields.get("deps"),
                    recipe.fields.get("rundeps"),
                    recipe.fields.get("imagedeps"),
                )
                if value
            )
            custom = ", ".join(recipe.functions) if recipe.functions else "-"
            old_path = recipe.path.relative_to(root)
            lines.append(
                f"| [{done}] | `{recipe.name}` | {status} | {field(recipe, 'version')} | "
                f"{field(recipe, 'revision')} | {patch_status(recipe)} | {deps or '-'} | "
                f"{custom} | `{old_path}` |"
            )
        lines.append("")

    old_patch_names = {p.name for p in (root / "uts" / "patches").iterdir() if p.is_dir()} if (root / "uts" / "patches").is_dir() else set()
    new_patch_names = {p.name for p in (root / "patches").iterdir() if p.is_dir()} if (root / "patches").is_dir() else set()
    stale_old = sorted(old_patch_names - new_patch_names)
    overlapping = sorted(old_patch_names & new_patch_names)

    lines.extend(
        [
            "## Patch directories",
            "",
            f"- Old-only patch directories: {len(stale_old)}",
            f"- Present in both trees: {len(overlapping)}",
            "",
        ]
    )
    if stale_old:
        lines.append("Old-only patches to review:")
        lines.append("")
        for name in stale_old:
            lines.append(f"- [ ] `{name}`")
        lines.append("")
    if overlapping:
        lines.append("Patch directories that exist in both places and should be diffed:")
        lines.append("")
        for name in overlapping:
            lines.append(f"- [ ] `{name}`")
        lines.append("")

    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit migration progress from old Jinx recipes to xbstrap.")
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="bootstrap repository root")
    parser.add_argument("--output", type=Path, help="write the Markdown report to this path")
    args = parser.parse_args()

    root = args.root.resolve()
    recipes = collect_recipes(root)
    bootstrap_names = parse_bootstrap_names(root)
    report = render_report(root, recipes, bootstrap_names)

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(report + "\n")
    else:
        print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
