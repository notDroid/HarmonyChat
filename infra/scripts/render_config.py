"""
Render Jinja2 config templates for a target environment.
"""

import json
import sys
import yaml
import argparse
from pathlib import Path
from jinja2 import Environment, FileSystemLoader

def render(config_file: str, templates_dir: str, output_dir: str) -> None:
    with open(config_file) as f:
        variables = yaml.safe_load(f)

    output_root = Path(output_dir)
    templates_dir = Path(templates_dir)
    templates = sorted(templates_dir.rglob("*.j2"))

    if not templates:
        print(f"No templates found in {templates_dir}")
        sys.exit(1)

    jinja_env = Environment(loader=FileSystemLoader(str(templates_dir)))
    jinja_env.filters["tojson"] = json.dumps

    for tmpl_path in templates:
        rel = tmpl_path.relative_to(templates_dir)
        out_rel = Path(str(rel).removesuffix(".j2"))
        out_file = output_root / out_rel
        out_file.parent.mkdir(parents=True, exist_ok=True)

        rendered = jinja_env.get_template(str(rel)).render(**variables)
        out_file.write_text(rendered)
        print(f"  ✓ {out_file}")

    print(f"\nRendered {len(templates)} file(s) → {output_root}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Render Jinja2 config templates")
    parser.add_argument("config_file", help="Path to the config YAML file")
    parser.add_argument("templates_dir", help="Path to the templates directory")
    parser.add_argument("output_dir", help="Path to the output directory")
    args = parser.parse_args()

    print(f"Rendering templates from {args.templates_dir} to {args.output_dir} using variables from {args.config_file}...\n")

    render(config_file=args.config_file, templates_dir=args.templates_dir, output_dir=args.output_dir)