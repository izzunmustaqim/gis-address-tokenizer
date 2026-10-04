# Address Tokenizer — Design Document

Implementation-level design derived from `spec.md`. Class responsibilities, module
layout, interfaces, and key algorithms.

---

## 1. Module Layout

```
gis/
├── main.py                  # Entry point: wires up and runs the console app
├── address_tokenizer/
│   ├── __init__.py          # Public exports: Address, AddressTokenizer
│   ├── model.py             # Address value object
│   ├── rules.py             # ComponentRule ABC + concrete rules + SectionRule
│   ├── tokenizer.py         # AddressTokenizer orchestrator
│   └── app.py               # ConsoleApp — I/O boundary
└── tests/
    ├── test_rules.py        # Unit tests per rule
    ├── test_tokenizer.py    # Integration tests: string in, Address out
    └── test_app.py          # Console loop behavior (stdin/stdout)
```

Dependency direction (no cycles):

```
main.py -> app.py -> tokenizer.py -> rules.py -> model.py
                      tokenizer.py -> model.py
```

`model.py` imports nothing from the package. Rules depend only on `model`.
The tokenizer depends on the `ComponentRule` abstraction; concrete rules are
injected, never hard-coded at the call site.

---

## 2. Class Design

### 2.1 `Address` (model.py)

Immutable value object — frozen dataclass. All six components optional.

```python
@dataclass(frozen=True)
class Address:
    apt: str | None = None
    section: str | None = None
    postcode: str | None = None
    city: str | None = None
    state: str | None = None
    street: str | None = None

    def with_field(self, name: str, value: str) -> "Address":
        """Return a new Address with `name` set (via dataclasses.replace)."""
        ...

    def to_dict(self) -> dict[str, str]:
        """Ordered dict of only the non-None components."""
        ...

    def to_json(self, *, indent: int | None = 2) -> str:
        ...
```

Design notes:
- Frozen + `with_field` keeps the object immutable while rules "fill it in" by
  returning updated copies — safe to share, no hidden mutation.
- `to_dict` emits keys in canonical order (`apt`, `section`, `postcode`,
  `city`, `state`, `street`) and drops `None`s, satisfying the output contract.
- Postcode is stored as a string so leading zeros survive.

### 2.2 `ComponentRule` ABC (rules.py)

Single interface every rule implements.

```python
class ComponentRule(ABC):
    name: ClassVar[str]                    # output key, e.g. "city"

    @abstractmethod
    def matches(self, token: str) -> bool:
        """True if this token belongs to this component. Must not raise."""

    @abstractmethod
    def apply(self, address: Address, token: str) -> Address:
        """Return address with this component set from token."""
```

`matches` is a pure predicate; `apply` is only called after `matches` returns
true (tokenizer contract). This lets the tokenizer probe rules without
committing to a mutation.

#### Concrete rules

| Class | `name` | `matches` logic |
|:------|:-------|:----------------|
| `AptRule` | `apt` | `re.fullmatch(r"No \d+", token)` after strip |
| `StreetRule` | `street` | token starts with `Jalan `, `Jln `, `Lorong `, `Persiaran` |
| `PostcodeRule` | `postcode` | `re.fullmatch(r"\d{5}", token)` and `01000 <= int(token) <= 98859` |
| `CityRule` | `city` | token in `CITIES` frozenset |
| `StateRule` | `state` | token in `STATES` frozenset |
| `SectionRule` | `section` | always `True` — catch-all, consulted last |

Lookup data lives as module constants:

```python
CITIES = frozenset({"Kuala Terengganu", "Kuala Lumpur", "Kajang", ...})
STATES = frozenset({"Selangor", "Terengganu", "Pahang", ...})
```

Correctness notes:
- `PostcodeRule` rejects `00000` and `98860`+ via the explicit range check;
  `AptRule` rejects `No ABC` via the regex. Both are total — no input raises.
- Rules are mutually exclusive on well-formed tokens, but the tokenizer still
  probes in priority order rather than relying on that.
- `SectionRule` never fails; it exists so "everything else" is handled
  uniformly instead of as a special case.

### 2.3 `AddressTokenizer` (tokenizer.py)

Orchestrator. Owns the ordered rule list; does splitting and dispatch.

```python
class AddressTokenizer:
    def __init__(self, rules: Sequence[ComponentRule] | None = None) -> None:
        # Default: specific rules in priority order, SectionRule appended last.
        self._rules = list(rules) if rules is not None else default_rules()

    def tokenize(self, raw: str) -> Address:
        address = Address()
        for token in self._split(raw):
            address = self._consume(address, token)
        return address

    def _split(self, raw: str) -> list[str]:
        """Comma split when commas present; regex scan fallback otherwise."""
        ...

    def _consume(self, address: Address, token: str) -> Address:
        for rule in self._rules:
            if rule.matches(token):
                return rule.apply(address, token)
        return address  # defensive: SectionRule should always match
```

Default priority order:

```python
def default_rules() -> list[ComponentRule]:
    return [AptRule(), StreetRule(), PostcodeRule(),
            CityRule(), StateRule(), SectionRule()]
```

Priority is explicit and injectable (DIP), so future rules that could overlap
can be ordered deliberately rather than by accident.

### 2.4 Splitting algorithm (`_split`) — the bonus-mark path

Two strategies behind one method:

1. **Comma path** — `raw.split(",")`, strip each part, drop empty parts.
2. **Comma-free path** — single regex scan with named groups, used only when
   the input contains no comma:

```python
TOKEN_RE = re.compile(
    r"""
      (?P<apt>No\ \d+)                                # No 11
    | (?P<street>(?:Jalan|Jln|Lorong)\ .*|Persiaran\S*)
    | (?P<postcode>\b\d{5}\b)                         # 21080
    | (?P<city>...)                                   # alternation of CITIES, longest-first
    | (?P<state>...)                                  # alternation of STATES
    """,
    re.VERBOSE,
)
```

Non-matched spans between matches become section tokens (whitespace collapsed;
pure punctuation/whitespace spans discarded). City/state alternations are sorted
longest-first so `Kuala Terengganu` wins over any shorter prefix match.

Key case: `21080 Kuala Terengganu` with no commas — the scan yields separate
matches `21080` and `Kuala Terengganu`, and the space between them is residue,
not section text. Trailing `.` is stripped during normalization so
`Terengganu.` still matches `Terengganu`.

### 2.5 `ConsoleApp` (app.py)

I/O boundary. Knows about the tokenizer, printing, and error reporting —
knows nothing about rules.

```python
class ConsoleApp:
    def __init__(self, tokenizer: AddressTokenizer,
                 input_fn=input, output_fn=print) -> None: ...

    def run(self) -> int:
        # Loop: prompt -> read line -> tokenize -> print JSON.
        # Handles exit commands, EOFError, KeyboardInterrupt, and catches
        # Exception per-iteration so one bad line never kills the loop.
        ...
```

Injected `input_fn`/`output_fn` make the loop testable without real stdin.
`run()` returns a process exit code (0 normal, 130 on Ctrl-C).

### 2.6 `main.py`

```python
from address_tokenizer import Address, AddressTokenizer
from address_tokenizer.app import ConsoleApp

if __name__ == "__main__":
    raise SystemExit(ConsoleApp(AddressTokenizer()).run())
```

---

## 3. Error Handling Strategy

| Situation | Behavior |
|:----------|:---------|
| Empty / whitespace-only input | Tokenizer returns empty `Address`; app prints `{}` (or a "no components found" note — pick one and keep it consistent). |
| Unrecognizable tokens | Captured by `SectionRule`, else ignored. |
| Out-of-range postcode, `No ABC` | `matches` returns False -> falls through per the scan path. |
| Unexpected exception in one iteration | Caught in `ConsoleApp.run`, message printed, loop continues. |
| Ctrl-C / EOF | Caught, clean farewell, exit code 130 / 0. |

Rules never raise: every `matches` is regex / frozenset / range based.
Exceptions are contained at the app boundary, not swallowed mid-stack.
No bare `except:` anywhere.

---

## 4. Extension Points

- **New component** (e.g. country): add one rule class + register it in
  `default_rules()`; add a field to `Address`. No existing rule changes (OCP).
- **Different priority**: inject a custom rule list into `AddressTokenizer`.
- **Alternative output** (CSV, XML): add a serializer next to `to_json`;
  tokenizer and rules untouched.

---

## 5. Testing Design

- **Rule unit tests** — table-driven: per rule, a list of
  `(token, expected_bool)` pairs covering accepts, rejects, and boundaries
  (`01000`/`98859` in range; `00999`/`98860` out; `Jalan` without trailing space).
- **Tokenizer integration tests** — both spec examples verbatim, comma-free
  variants, order permutations, single-component inputs, garbage input.
- **App tests** — scripted input via injected `input_fn`, captured `output_fn`
  output, assert valid JSON and that the loop survives a raising line.
