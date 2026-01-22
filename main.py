#!/usr/bin/env python3

import argparse
import shutil
import tomllib
from pathlib import Path
from typing import Annotated, Any, Literal

from jinja2 import Environment, FileSystemLoader, select_autoescape
from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

LANGUAGES = ("pt", "en")


FlexibleDate = Annotated[
    str, StringConstraints(pattern=r"^(\d{4}(-\d{2}(-\d{2})?)?)?|(future)$")
]
NonEmptyStr = Annotated[str, StringConstraints(min_length=1)]
ModelSize = Annotated[str, StringConstraints(pattern=r"^(\d+(\.\d+)?[MBT])?$")]


class Availability(BaseModel):
    available_now: bool
    url: str | None = Field(default=None)
    planned: bool | None = Field(default=None)

    @model_validator(mode="after")
    def validate_planned(self):
        if self.available_now and self.planned is not None:
            msg = "When 'available_now' is true, 'planned' should not be set"
            raise ValueError(msg)
        return self

    @model_validator(mode="after")
    def validate_url(self):
        if self.available_now and not self.url:
            msg = "When 'available_now' is true, 'url' must be set"
            raise ValueError(msg)
        return self

    model_config = ConfigDict(extra="forbid")


class CutOffDate(BaseModel):
    date: FlexibleDate
    type: Literal["strict", "possibly_earlier", "possibly_later", ""]

    @model_validator(mode="after")
    def validate_combination(self):
        if self.date == "future":
            msg = "Cutoff date does not accept future date"
            raise ValueError(msg)
        if self.date and not self.type:
            msg = "When 'date' is empty, 'type' must be empty too"
            raise ValueError(msg)
        if not self.date and self.type:
            msg = "When 'date' is non-empty, 'type' must be non-empty too"
            raise ValueError(msg)
        return self

    model_config = ConfigDict(extra="forbid")


class NameAndUrl(BaseModel):
    name: NonEmptyStr
    url: str

    model_config = ConfigDict(extra="forbid")


class LanguageModel(BaseModel):
    name: NonEmptyStr
    url: str
    language_varieties: list[Literal["pt-BR", "pt-PT", "gl-ES"]]
    release_date: FlexibleDate
    license: str
    size: ModelSize
    model_id: str
    base_model: str
    origin: list[NameAndUrl]
    training_data: list[NameAndUrl]
    knowledge_cutoff: CutOffDate
    weight_availability: Availability
    public_api_availability: Availability
    online_chat_availability: Availability

    model_config = ConfigDict(extra="forbid")


def parse_metadata_tree(directory: Path):
    result = {}
    metadata_file = directory / "metadata.toml"
    if metadata_file.is_file():
        with metadata_file.open("rb") as fd:
            result.update(tomllib.load(fd))
    children = []
    for subdir in sorted(directory.iterdir(), key=lambda f: f.name.lower()):
        if subdir.is_dir():
            if (child := parse_metadata_tree(subdir)) is not None:
                children.append(child)
    if children:
        result["children"] = children
    return result or None


def check_metadata_tree(
    tree: dict[str, Any], parent_data: dict[str, Any] | None = None
):
    if parent_data is None:
        parent_data = {}
    children = tree.get("children", [])
    if not children:
        data = parent_data | {k: v for k, v in tree.items() if k != "children"}
        print(f"\n\nVALIDATING '{data['name']}':")
        if "name" not in tree:
            msg = "Missing name"
            raise ValueError(msg)
        tree["full_model"] = LanguageModel.model_validate(data)
        print("OK.")
    else:
        for child in children:
            p_data = parent_data | {k: v for k, v in child.items() if k != "children"}
            duplicate_keys = (set(parent_data) & set(child)) - {"name"}
            if duplicate_keys:
                msg = f"\n\nDUPLICATE KEYS in '{tree.get('name')}' and its parents: {duplicate_keys}."
                raise ValueError(msg)
            check_metadata_tree(child, p_data)


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

    with (template_dir / f"i18n-{lang}.toml").open("rb") as fd:
        i18n = tomllib.load(fd)

    title = (template_dir / f"01-title-{lang}.txt").read_text()

    root_template = env.get_template("00-root.html.jinja2")
    intro_template = env.get_template(f"02-intro-{lang}.html.jinja2")
    models_template = env.get_template("03-models.html.jinja2")
    model_template = env.get_template("04-model.html.jinja2")
    outro_template = env.get_template("05-outro.html.jinja2")

    intro_html = intro_template.render()
    rendered_models = [
        model_template.render(model=model, i18n=i18n) for model in models
    ]
    models_html = models_template.render(model_htmls=rendered_models, i18n=i18n)
    outro_html = outro_template.render(contributors=contributors, i18n=i18n)

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

    tree = parse_metadata_tree(args.data_dir / "models")
    check_metadata_tree(tree)
    all_models = tree["children"]
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
