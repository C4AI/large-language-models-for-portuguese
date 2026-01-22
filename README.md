# LLMs for Portuguese

This repository contains a list of large language models tailored for the Portuguese language.

Criteria:
- Multilingual models are only included if they have been fine-tuned for Portuguese;
- Only models that can answer queries or questions are considered (not models that only complete sentences);
- Models with less than 1 billion parameters are not listed.

Models are grouped into "families", usually when they share a name and have been developed by the same team.

# Adding models

To add models to our list, create directories under *data/models/* containing `metadata.toml` files
following this template:

<details>
<summary>Template</summary>

```toml
name = "Your Model Name"
url = "https://example.com/your-model"
release_date = "2025-12-31"
license = "The Model's License 123"
language_varieties = [ "pt-PT", "pt-BR" ]
size = "1.8B"
base_model = "Name of the Base Model"
model_id = "my_model_1.8b"

[[training_data]]
name = "Dataset 1"
url = ""

[[training_data]]
name = "Dataset 2"
url = "https://example.com/dataset2"

[[origin]]
name = "Person or Institution 1"
url = "https://example.com/institution1"

[[origin]]
name = "Person or Institution 2"
url = ""

[weight_availability]
available_now = false

[public_api_availability]
available_now = true
url = "https://example.com/your-model-api"

[online_chat_availability]
available_now = false
planned = true

[knowledge_cutoff]
date = "2024-12"
type = "possibly_later"
```

</details>

# Fields:

Note that most fields are required, and a blank string should be used when the information is not available.

For models that are grouped into families,
the `name` field is mandatory in all levels,
and all the other fields must be defined
only once per model and cannot be overridden
(i.e. if a family already defines `size`,
its subdirectories must not redefine `size`).

1. `name`: The model name (required).
2. `url`: The address of a webpage that is relevant to the model
          (such as a page about the model on the website of the company or institution that developed it,
          or a published paper, or a Hugging Face link if nothing else is available).
          If there are no relevant URLs, leave the field blank.
3. `release_date`: When the model was released.
      Accepted formats: `YYYY-MM-DD` ("2025-12-31"), `YYYY-MM` ("2025-12"), `YYYY` ("2025"),
      `future` (for unreleased models), or a blank string (when the information was not found).
4. `license`: The model license. If it is a proprietary model, write the string `proprietary`.
      If the license is unknown, leave the field blank.
5. `language_varieties`: The list of language varieties the model was trained to handle.
      If unknown, write an empty list `[ ]`. Currently, the possible values are `pt-BR` (Brazilian Portuguese),
      `pt-PT` (European Portuguese) and `gl-ES` (Galician).
6. `size`: The number of parameters in the model.
   It must be a number followed by `B` (billions) or `T` (trillions), e.g. "2.5B", or a blank string if not found.
7. `base_model`: Name of the base model, in case it is the result of a fine-tuning process.
   If this information is not available, leave it blank.
8. `model_id`: ID of the model, as used by model repositories and API servers.
9. `training_data`: 
    List of datasets used to train/fine-tune the model. 
    Write one `[[training_data]]` block for each dataset, with its `name=` (required) and `url=` (required even if blank).
    If the training data is not known, remove the `[[training_data]]` blocks and write the line `training_data = [ ]`.
10. `origin`: 
    List of people or institutions responsible for developing the model.
    Write one `[[origin]]` block for each item, with its `name=` (required) and `url=` (required even if blank).
    If the origin is not known, remove the `[[origin]]` blocks and write the line `origin = [ ]`.
11. `weight_availability`: Public availability of the model's weights. If the subfield `available_now`
      is `false`, then no `url` should be given, and the optional subfield `planned = true` can be added
      in case the weights are expected to be released in the future. If the subfield `available_now`
      is `true`, then the `url` is mandatory and should point where the weights can be found.
12. `public_api_availability`: Availability of an API where the model can be accessed programmatically.
      If the subfield `available_now`
      is `false`, then no `url` should be given, and the optional subfield `planned = true` can be added
      in case an API is expected to be released in the future. If the subfield `available_now`
      is `true`, then the `url` is mandatory and should point to where the API can be accessed.
13. `online_chat_availability`: Availability of an online chat where the model can be accessed by users.
      If the subfield `available_now`
      is `false`, then no `url` should be given, and the optional subfield `planned = true` can be added
      in case an online chat is expected to be released in the future. If the subfield `available_now`
      is `true`, then the `url` is mandatory and should point to where the chat can be accessed.
14. `knowledge_cutoff`: The limit date of the model's knowledge. The subfield `date` accepts the
      following formats: `YYYY-MM-DD` ("2025-12-31"), `YYYY-MM` ("2025-12"), `YYYY` ("2025"),
      or a blank string (when the information was not found). The subfield `type` must be one of
      `exact`, `possibly_earlier` and `possibly_later`, or blank if the date is also blank.

# Running the script:

Install `uv`, then run `uv sync` to install the dependencies.

To check the integrity of the data and generate an HTML page, run:

```shell
uv run python main.py data/ html/
```

If there are errors, the script will print them and halt.
Otherwise, HTML files will be generated in the *html/* directory,
one per language.
