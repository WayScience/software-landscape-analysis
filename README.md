# Landscape Analysis

A "landscape analysis" is an informational survey of existing software and other tooling that solve similar problems or use similar technologies.
This repository performs landscape analyses for specific projects.

## Installation

Please use Python [`poetry`](https://python-poetry.org/) to run and install related content.

```bash
# after installing poetry, create the environment
poetry install
```

## Development

### Jupyter Lab

Please follow installation steps above and then use a relevant Jupyter environment to open and explore the notebooks under the `notebooks` directory.

```bash
# after creating poetry environment, run jupyter
poetry run jupyter lab
```

### Poe the Poet

We use [Poe the Poet](https://poethepoet.natn.io/index.html) to define and run tasks defined within `pyproject.toml` under the section `[tool.poe.tasks*]`.
This allows for the definition and use of a task workflow when implementing multiple procedures in sequence.

For example, use the following to run the `cytomining_ecosystem` task:

```bash
# run cytomining_ecosystem using poethepoet
poetry run poe cytomining_ecosystem
```
