# Address Tokenizer — Task Breakdown

Ordered, checkable tasks derived from `spec.md` and `design.md`.
Update the boxes as work completes.

Legend: `[ ]` not started · `[~]` in progress · `[x]` done

---

## Phase 0 — Version Control

- [x] `git init` with Python `.gitignore` (`__pycache__/`, `.venv/`,
      `.pytest_cache/`, `.ruff_cache/`, etc.).
- [x] Initial commit: specs and docs as the design baseline.
- [ ] Commit policy: one commit per completed phase below, only when
      `python -m pytest` passes on a working increment.

## Phase 1 — Skeleton

- [x] Create package layout: `address_tokenizer/` with `__init__.py`, empty
      `model.py`, `rules.py`, `tokenizer.py`, `app.py`; `tests/` package.
- [x] Add `main.py` entry point stub.
- [x] Verify test runner works: `python -m pytest` collects 0 tests cleanly.

## Phase 2 — Domain Model

- [x] Implement `Address` frozen dataclass with six optional `str | None` fields.
- [x] Implement `Address.with_field(name, value)` via `dataclasses.replace`,
      raising `KeyError`/`ValueError` for unknown field names.
- [x] Implement `to_dict()` — canonical key order, `None`s omitted.
- [x] Implement `to_json()` using the `json` module.
- [x] Unit tests: empty address -> `{}`; partial address omits absent keys;
      postcode keeps leading zeros (`"01000"`).

## Phase 3 — Rules

- [x] Define `ComponentRule` ABC (`name`, `matches`, `apply`).
- [x] Add `CITIES` / `STATES` frozenset constants (full lists from spec §3.1–3.2).
- [x] `AptRule` — `No \d+` fullmatch; rejects `No`, `No ABC`, `no 11` (case).
- [x] `StreetRule` — prefixes `Jalan `, `Jln `, `Lorong `, `Persiaran`;
      rejects `Jalan` with no trailing space/content.
- [x] `PostcodeRule` — 5 digits AND inclusive `01000`–`98859`;
      rejects `00999`, `98860`, `2108`, `210800`, non-numeric.
- [x] `CityRule` / `StateRule` — exact set membership;
      rejects unknown names and partial matches (`Kuala` alone).
- [x] `SectionRule` — always matches.
- [x] Table-driven unit tests per rule: accepts, rejects, boundary values.

## Phase 4 — Tokenizer Core (comma path)

- [ ] `AddressTokenizer.__init__` with injectable rule list; default order
      `apt, street, postcode, city, state, section`.
- [ ] `_split` comma path: split, strip, drop empty tokens.
- [ ] `_consume`: first matching rule wins; return updated `Address`.
- [ ] `tokenize(raw)`: normalize input (strip, collapse whitespace, drop
      trailing punctuation).
- [ ] Integration tests:
  - [ ] Spec example 1 (full address) matches expected JSON exactly.
  - [ ] Spec example 2 (incomplete address) matches expected JSON exactly.
  - [ ] Order permutation: state/city first, apt last.
  - [ ] Single-component inputs (one field each).
  - [ ] Empty / whitespace input -> `{}` without raising.

## Phase 5 — Comma-Free Parsing (bonus)

- [ ] Detect absence of commas and switch to the regex-scan strategy.
- [ ] Build `TOKEN_RE` with named groups: apt, street, postcode, city, state.
      City/state alternations sorted longest-first.
- [ ] Extract residue spans between matches as section tokens; discard
      whitespace/punctuation-only spans.
- [ ] Ensure embedded pairs parse: `21080 Kuala Terengganu` -> postcode + city.
- [ ] Tests: comma-free versions of both spec examples; mixed comma/no-comma
      input; trailing-period input.

## Phase 6 — Console App

- [ ] `ConsoleApp.run()` loop: prompt, read line, tokenize, print JSON,
      repeat.
- [ ] Exit paths: `exit`/`quit` command, EOF (Ctrl-D / pipe end), Ctrl-C.
- [ ] Per-iteration `except Exception` — print message, continue loop;
      no bare `except:`.
- [ ] Injected `input_fn` / `output_fn` for testability; return exit codes
      (0 normal, 130 on interrupt).
- [ ] App tests: scripted input sequence, assert JSON output lines parse;
      a raising line does not terminate the loop.

## Phase 7 — Polish & Verification

- [ ] Full test suite green: `python -m pytest`.
- [ ] Lint clean: `ruff check .` (add config if needed).
- [ ] Manual smoke test: `python main.py` with all spec examples plus
      comma-free and garbage inputs.
- [ ] Confirm SOLID review pass: one reason to change per class, no concrete
      rule imports in `tokenizer.py` construction path, no dead code.
- [ ] Ensure `spec.md`, `design.md`, and code agree (update docs if the
      implementation diverged).
