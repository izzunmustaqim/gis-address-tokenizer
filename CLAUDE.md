# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

A university assignment (AM GIS Application): a console program written in **Python** that parses and tokenizes free-form address strings into structured address components. No source code exists yet — the repo currently holds only the requirements.

- `spec.md` — the project specification: component rules, output format, proposed OOP architecture, robustness requirements, testing plan. Primary source of truth.
- `design.md` — module layout, class interfaces, parsing algorithm, error-handling strategy. Follow this unless there is a good reason not to (update it if the implementation diverges).
- `tasks.md` — phased checklist of implementation work. Check off boxes as tasks complete.
- `address_tokenizer_specification.md` — original assignment requirements (component rules, input/output examples). Cross-check against `spec.md` when they differ.
- `Assignment Address Tokenizer_AM GIS Application.pdf` — original assignment brief. Prefer the markdown spec for day-to-day work; note the PDF may contain details not yet transcribed into the markdown.

## Requirements Overview

- Order-agnostic input; every component (apt, section, postcode, city, state, street) is optional — do not assume a fixed field order or completeness.
- Parsing rules are defined per component in the spec (e.g. `No <digits>` for apt, fixed city/state lookup lists, postcode range `01000`–`98859`, street prefixes `Jalan `/`Jln `/`Lorong `/`Persiaran`). `{Section}` is the catch-all for unmatched text.
- Comma-free input handling earns bonus marks.
- Evaluation emphasizes OOP design, SOLID principles, graceful handling of malformed input and runtime errors, and output accuracy (JSON keyed by component, omitting absent fields).

## Commands

Tooling: `pytest` for tests (installed). Linting (`ruff`) not yet configured — prefer zero-config choices when adding it.

- Run the app: `python main.py`
- Run all tests: `python -m pytest`
- Single test: `python -m pytest tests/test_tokenizer.py::test_name`
