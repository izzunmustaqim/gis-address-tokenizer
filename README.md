# GIS Address Tokenizer

A Python console program that parses free-form Malaysian address strings into
structured components and prints them as JSON. Built for the AM GIS Application
assignment; evaluated on OOP/SOLID design, parsing accuracy, and robustness.

```text
> No 11, Chendering, 21080 Kuala Terengganu, Terengganu.
{
  "apt": "No 11",
  "section": "Chendering",
  "postcode": "21080",
  "city": "Kuala Terengganu",
  "state": "Terengganu"
}
```

## Features

- **Order-agnostic** — components can appear in any order.
- **All components optional** — parses partial addresses like `No 11, Kuala Terengganu, Chendering`.
- **Comma-free input** — falls back to pattern scanning when no commas are present (bonus behavior).
- **Graceful** — malformed or empty input never crashes the loop; unexpected errors are reported and the session continues.

## Requirements

- Python 3.10+
- No third-party runtime dependencies (standard library only)

## Usage

```bash
python main.py
```

Type an address and press Enter; the program prints a JSON object containing
only the components it matched. Type `exit` or `quit` (or press `Ctrl+C` /
`Ctrl+D`) to leave.

### Recognized components

| Component  | Key        | Matches                                             |
|:-----------|:-----------|:----------------------------------------------------|
| Apt number | `apt`      | `No ` followed by digits (e.g. `No 11`)             |
| Street     | `street`   | Starts with `Jalan `, `Jln `, `Lorong `, `Persiaran` |
| Postcode   | `postcode` | 5 digits in range `01000`–`98859`                   |
| City       | `city`     | Exact match against the fixed city list             |
| State      | `state`    | Exact match against the fixed state list            |
| Section    | `section`  | Catch-all for remaining text (e.g. a township)      |

Absent components are omitted from the output entirely — no nulls, no empty
strings. Postcodes are output as strings, preserving leading zeros.

## Development

```bash
# Run the full test suite
python -m pytest

# Run a single test
python -m pytest tests/test_tokenizer.py::test_name

# Lint
ruff check .
```

## Project Structure

```
main.py                      Entry point
address_tokenizer/
├── model.py                 Address value object (frozen dataclass)
├── rules.py                 ComponentRule ABC + one rule per component
├── tokenizer.py             Orchestrator: splits input, applies rules
└── app.py                   ConsoleApp — I/O boundary, error containment
tests/                       Rule, tokenizer, and console tests
```

Design and requirements live in [`spec.md`](spec.md) and
[`design.md`](design.md); the implementation checklist is
[`tasks.md`](tasks.md).

## License

Course assignment — for academic use.
