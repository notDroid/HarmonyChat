"""
Render Jinja2 config templates for a target environment.
"""

import json
import sys
from omegaconf import OmegaConf
import argparse
from pathlib import Path
from jinja2 import Environment, FileSystemLoader

def render(config_files: list[str], templates_dir: str, output_dir: str) -> None:
    loaded_configs = []
    for config_file in config_files:
        with open(config_file) as f:
            loaded_configs.append(OmegaConf.load(f))
    
    conf = OmegaConf.merge(*loaded_configs)
    variables = OmegaConf.to_container(conf, resolve=True)

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
    parser.add_argument("config_files", nargs="+", help="Paths to the config YAML files")
    parser.add_argument("templates_dir", help="Path to the templates directory")
    parser.add_argument("output_dir", help="Path to the output directory")
    args = parser.parse_args()

    print(f"Rendering templates from {args.templates_dir} to {args.output_dir} using variables from {', '.join(args.config_files)}...\n")

    render(config_files=args.config_files, templates_dir=args.templates_dir, output_dir=args.output_dir)