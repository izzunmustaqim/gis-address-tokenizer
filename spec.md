# Address Tokenizer — Project Specification

## 1. Overview

A **Python console program** that parses a free-form address string into its distinct
address components and prints them as structured JSON. Built as an AM GIS Application
assignment, evaluated on architecture (OOP, SOLID), parsing accuracy, and robustness
against malformed input.

## 2. Technology

- **Language:** Python (3.10+)
- **Runtime:** standard library only — no third-party dependencies required
  (`json`, `re`, `dataclasses`, `abc` cover everything needed)
- **Entry point:** interactive console loop (read a line, print JSON) with a clean
  exit path (`Ctrl+C` / `exit` / EOF)

## 3. Address Components

| # | Component  | Key        | Rule / Matching Criteria |
|:-:|:-----------|:-----------|:-------------------------|
| 1 | Apt Number | `apt`      | Starts with `"No "` followed by a series of digits. |
| 2 | City       | `city`     | Exact match against the fixed city list (§3.1). |
| 3 | State      | `state`    | Exact match against the fixed state list (§3.2). |
| 4 | Postcode   | `postcode` | Numeric, inclusive range `01000`–`98859` (5 digits). |
| 5 | Street     | `street`   | Begins with `"Jalan "`, `"Jln "`, `"Lorong "`, or `"Persiaran"`. |
| 6 | Section    | `section`  | Catch-all: any text block not claimed by another rule. |

### 3.1 City list (exact match)

Kuala Terengganu, Kuala Lumpur, Kajang, Bangi, Damansara, Petaling Jaya, Puchong,
Subang Jaya, Cyberjaya, Putrajaya, Mantin, Kuching, Seremban

### 3.2 State list (exact match)

Selangor, Terengganu, Pahang, Kelantan, Melaka, Pulau Pinang, Kedah, Johor, Perlis,
Sabah, Sarawak

## 4. Input Constraints

- **Order-agnostic** — components may appear in any order.
- **All components optional** — an address may contain as few as one component;
  never assume a fixed field order or full completeness.
- **Comma-free input** must parse correctly (bonus marks). Delimiters are a hint,
  not a requirement: fall back to rule-based matching when commas are absent.
- Trailing punctuation (e.g. the final `.` in `...Terengganu.`) must not corrupt
  matching.

## 5. Output Format

- JSON object keyed by component name, **omitting absent components entirely**
  (no `null`s, no empty strings).
- Values are strings; the postcode is output as a string preserving leading zeros
  (e.g. `"01000"`).
- Output key set: `apt`, `section`, `postcode`, `city`, `state`, `street` (whichever
  matched).

### Example 1 — full address

Input:
```text
No 11, Chendering, 21080 Kuala Terengganu, Terengganu.
```
Output:
```json
{
  "apt": "No 11",
  "section": "Chendering",
  "postcode": "21080",
  "city": "Kuala Terengganu",
  "state": "Terengganu"
}
```

### Example 2 — incomplete address

Input:
```text
No 11, Kuala Terengganu, Chendering
```
Output:
```json
{
  "apt": "No 11",
  "section": "Chendering",
  "city": "Kuala Terengganu"
}
```

## 6. Architecture (OOP / SOLID)

The evaluation explicitly scores design, so structure the code around these seams:

- **`Address`** — immutable value object (dataclass) holding the six optional
  components; responsible for serializing itself to the JSON dict.
- **`ComponentRule`** (abstract) — single-responsibility interface:
  `matches(token) -> bool` and `apply(token, address)`. One concrete rule per
  component (AptRule, CityRule, StateRule, PostcodeRule, StreetRule),
  each knowing only its own matching logic. Open for extension (new components)
  without modifying existing rules (OCP).
- **`SectionRule`** — catch-all, applied only after every specific rule has
  declined a token.
- **`AddressTokenizer`** — orchestrator: takes raw input, splits it into candidate
  tokens, dispatches each token through an ordered list of rules, returns an
  `Address`. Depends on the `ComponentRule` abstraction, not concrete rules (DIP);
  the rule list is injected so rules can be reordered or extended.
- **`ConsoleApp` / `main.py`** — I/O boundary: reads input, invokes the tokenizer,
  prints JSON, and converts failures into user-facing messages (no stack traces
  for ordinary input problems).

Suggested parsing flow:

1. Normalize input (strip, collapse whitespace).
2. Split on commas when present; when absent, use rule-based tokenization
   (scan for patterns such as `No \d+`, 5-digit postcodes, city/state dictionary
   matching, street prefixes) so comma-free input still works.
3. For each token, try specific rules in priority order:
   `apt` → `street` → `postcode` → `city` → `state` → `section`.
4. Unclaimed text becomes `section` (last write wins, or append if the design
   prefers — document the choice).

## 7. Robustness Requirements

- Empty input, whitespace-only input, and input containing no recognizable
  components must not raise — return whatever matched (possibly an empty
  `Address`) or a clear message.
- Guard out-of-range postcodes (`00000`, `99999`) and near-misses
  (`No ABC`, `Jalan` without trailing space) — they must not be accepted as their
  respective components.
- The console loop must survive malformed lines and continue prompting;
  unexpected exceptions are caught at the boundary and reported gracefully.
- Avoid bare `except:`; catch specific exceptions.

## 8. Testing

Use `pytest` (or stdlib `unittest`) with cases covering:

- Both examples above (§5).
- Comma-free variants of both examples (bonus behavior).
- Each component in isolation and in unusual positions (state first, city last).
- Rejections: out-of-range postcode, malformed apt, unknown city/state names.
- Empty and garbage input.

Run: `python -m pytest` — single test:
`python -m pytest tests/test_tokenizer.py::test_name`
