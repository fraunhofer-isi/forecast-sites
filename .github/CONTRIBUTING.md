<!-- SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München -->
<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->

# Contributing to FORECAST-Sites

Thank you for your interest in contributing. Bug reports, questions, documentation improvements and code contributions
are welcome. By participating you agree to follow the [Code of Conduct](CODE_OF_CONDUCT.md).

## Reporting issues

Please open an issue on [GitHub](https://github.com/fraunhofer-isi/forecast-sites/issues). For bugs, include

- what you did (the relevant part of `src/simulation_options.toml` and the input data you changed),
- what you expected and what happened instead,
- the Python version and the operating system.

Security problems should not be reported publicly, see [SECURITY.md](SECURITY.md).

## Development setup

```bash
git clone https://github.com/fraunhofer-isi/forecast-sites.git
cd forecast-sites
pip install .[dev]
```

Run all commands from the project root, because the paths in `src/simulation_options.toml` are relative to it.

## Making changes

1. Fork the repository and create a branch: `git checkout -b my-feature`.
2. Make your changes. Add or adapt unit tests in `test/` (the structure mirrors `src/`). The project requires a test
   coverage of 100 %.
3. Run the quality checks:

   ```bash
   ruff format src test check
   ruff check src test check
   pytest --cov
   python check/check_naming_conventions.py
   ```

4. Commit, push the branch and open a pull request. Describe what changed and why.

## Conventions

- The code style is defined by [Ruff](https://docs.astral.sh/ruff/) in `pyproject.toml` (single quotes, line length 130).
- File and folder names are snake_case.
- Every file needs a license header according to the [REUSE](https://reuse.software/) specification (see existing
  files). The project is licensed under the AGPL-3.0-or-later, your contribution will be licensed accordingly.
- Changes of the model behavior should be documented in the [Architecture section](../README.md#architecture) of the README.
- Agent-facing conventions are documented in `AGENTS.md`.
- Do not commit generated files such as `results/` or `resources/input/input.sqlite`.

## Input data

The model input is the set of CSV files in `resources/input/por`. After changing them, validate the data:

```bash
python check/check_csv_integrity.py resources/input/por
```

See the [README](../README.md#configuration) for a description of the files.
