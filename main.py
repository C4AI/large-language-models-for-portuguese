#!/usr/bin/env python3

import argparse
from pathlib import Path
import shutil
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape

import tomllib

LANGUAGES = ("pt",)


def parse_metadata_tree(directory: Path):
    result = {}
    metadata_file = directory / "metadata.toml"
    if metadata_file.is_file():
        with metadata_file.open("rb") as fd:
            result.update(tomllib.load(fd))
    children = []
    for subdir in directory.iterdir():
        if subdir.is_dir():
            if (child := parse_metadata_tree(subdir)) is not None:
                children.append(child)
    if children:
        result["children"] = children
    return result or None


def generate_html(
    models: list[dict[str, Any]],
    contributors: list[dict[str, Any]],
    output_directory: Path,
    lang: str,
):
    output_directory.mkdir(exist_ok=True, parents=True)

    repo_root = Path(__file__).parent
    template_dir = repo_root / "templates"
    env = Environment(
        loader=FileSystemLoader(template_dir), autoescape=select_autoescape()
    )

    title = (template_dir / f"01-title-{lang}.txt").read_text()

    root_template = env.get_template("00-root.html.jinja2")
    intro_template = env.get_template(f"02-intro-{lang}.html.jinja2")
    models_template = env.get_template(f"03-models-{lang}.html.jinja2")
    model_template = env.get_template(f"04-model-{lang}.html.jinja2")
    outro_template = env.get_template(f"05-outro-{lang}.html.jinja2")

    intro_html = intro_template.render()
    rendered_models = [model_template.render(model=model) for model in models]
    models_html = models_template.render(model_htmls=rendered_models)
    outro_html = outro_template.render(contributors=contributors)

    html = root_template.render(
        lang=lang,
        title=title,
        intro_html=intro_html,
        models_html=models_html,
        outro_html=outro_html,
    )
    (output_directory / "index.html").write_text(html)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "data_dir",
        type=Path,
        help="Path to the input data directory.",
    )
    parser.add_argument(
        "out_dir",
        type=Path,
        help="Path to the output directory.",
    )

    args = parser.parse_args()

    all_models = parse_metadata_tree(args.data_dir / "models")["children"]
    all_models.sort(key=lambda m: m["name"])
    with (args.data_dir / "contributors.toml").open("rb") as fd:
        contributors = tomllib.load(fd)["contributors"]
    css_files = [*(Path(__file__).parent / "styles").glob("*.css")]
    for lang in LANGUAGES:
        out_dir = args.out_dir / lang
        generate_html(all_models, contributors, out_dir, lang)
        for css_file in css_files:
            shutil.copy(css_file, out_dir)


if __name__ == "__main__":
    main()
