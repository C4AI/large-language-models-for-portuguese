#!/usr/bin/env python3
import argparse

from pathlib import Path
import re
from lxml import html

import toml


def extract_links(cell):
    items = []
    for a in cell.xpath(".//a"):
        name = (a.text or "").strip()
        url = a.get("href")
        if name or url:
            items.append({"name": name, "url": url})
    return items


def parse_html(input_path):
    tree = html.parse(input_path)
    rows = tree.xpath("//table[contains(@class,'waffle')]/tbody/tr")
    header = [th.text_content().strip() for th in rows[0].xpath(".//td")]
    data_rows = rows[1:]

    mapping = {
        "Nome": "name",
        "Data de lançamento": "release_date",
        "Licença": "license",
        "Variante do português": "language_varieties",
        "Tamanho": "size",
        "Modelo base": "base_model",
        "Pesos disponíveis": "weight_availability",
        "Variações": "model_id",
        "Dados usados no treinamento": "training_data",
        "Data de corte dos dados": "knowledge_cutoff",
        "API": "public_api_availability",
        "Chat online": "online_chat_availability",
        "Responsáveis": "origin",
    }

    idx_map = {mapping[h]: i for i, h in enumerate(header) if h in mapping}
    return data_rows, idx_map


def parse_special_field(field, cell):
    text_content = cell.text_content().strip()
    if field == "language_varieties":
        varieties = text_content.split(" e ")
        if varieties == ["(?)"] or varieties == [""]:
            return None
        return [
            {"Portugal": "pt-PT", "Brasil": "pt-BR", "Galiza": "gl-ES"}[v]
            for v in varieties
        ]
    if field == "license" and text_content.lower() == "proprietária":
        return "proprietary"
    if field == "knowledge_cutoff":
        if text_content == "(?)":
            return None
        if text_content.startswith("≥"):
            return {"date": text_content.lstrip("≥ ").strip(), "type": "possibly_later"}
        elif text_content.startswith("≤"):
            return {
                "date": text_content.lstrip("≤ ").strip(),
                "type": "possibly_earlier",
            }
        else:
            return {"date": text_content, "type": "strict"}

    if field in ["training_data", "origin"]:
        return extract_links(cell)
    if field == "release_date" and text_content == "(futuro)":
        return "future"
    if field in [
        "weight_availability",
        "public_api_availability",
        "online_chat_availability",
    ]:
        a = cell.xpath(".//a")
        url = a[0].get("href") if a else None
        text = (a[0].text or "").strip().lower() if a else text_content.lower()
        return {
            "available_now": "sim" in text or "paga" in text,
            "planned": ("futuro" in text or "talvez" in text) or None,
            "url": url,
        }
    if text_content in ["(?)", "(confidencial)", "-"]:
        return ""
    return text_content


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("output_dir", type=Path)
    args = parser.parse_args()

    rows, idx_map = parse_html(args.input)

    for row in rows:
        cells = row.xpath(".//td")
        if not cells:
            continue
        name_cell = cells[idx_map["name"]]
        name_text = name_cell.text_content().strip()
        if not name_text or name_text == "(?)":
            continue

        base_dir = args.output_dir / name_text
        base_dir.mkdir(parents=True, exist_ok=True)

        data = {}
        for field, i in idx_map.items():
            cell = cells[i]
            value = parse_special_field(field, cell)
            if field == "name":
                name_with_link = extract_links(cell)
                if name_with_link:
                    data["url"] = name_with_link[0]["url"]

            if field == "model_id":
                if "," in value:
                    models = [m.strip() for m in value.split(",")]
                    for m in models:
                        subdir = base_dir / m
                        subdir.mkdir(parents=True, exist_ok=True)
                        toml.dump({"model_id": m}, open(subdir / "metadata.toml", "w"))
                    continue
            data[field] = value

        text = toml.dumps(data)
        text = text.replace("\n[[", "\n\n[[").replace("\n\n\n", "\n\n")
        text = re.sub(r",\](\n|$)", r" ]\1", text)
        (base_dir / "metadata.toml").write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main()
