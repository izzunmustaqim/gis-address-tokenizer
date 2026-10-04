"""ConsoleApp — I/O boundary for the interactive loop.

See design.md 2.5: reads input, invokes the tokenizer, prints JSON,
converts failures into user-facing messages (no stack traces for ordinary
input problems). Knows nothing about rules. Injected input_fn/output_fn
keep the loop testable without real stdin.
"""

from __future__ import annotations

from collections.abc import Callable

from .tokenizer import AddressTokenizer

_PROMPT = "address> "
_EXIT_COMMANDS = frozenset({"exit", "quit"})
_FAREWELL = "Goodbye."
_INTERRUPT_MESSAGE = "\nInterrupted — goodbye."
_NO_COMPONENTS = "(no components found)"


class ConsoleApp:
    """Interactive loop: prompt -> read line -> tokenize -> print JSON."""

    def __init__(
        self,
        tokenizer: AddressTokenizer,
        input_fn: Callable[[str], str] = input,
        output_fn: Callable[[str], None] = print,
    ) -> None:
        self._tokenizer = tokenizer
        self._input = input_fn
        self._output = output_fn

    def run(self) -> int:
        """Run until exit command, EOF, or interrupt.

        Returns 0 on normal exit, 130 on Ctrl-C (spec 7 / design 2.5).
        One bad line never kills the loop: unexpected exceptions are
        caught per-iteration and reported without a stack trace.
        """
        while True:
            try:
                line = self._input(_PROMPT)
            except EOFError:
                # Ctrl-D / pipe end: newline then exit cleanly
                self._output("")
                self._output(_FAREWELL)
                return 0
            except KeyboardInterrupt:
                # Ctrl-C at the prompt
                self._output(_INTERRUPT_MESSAGE)
                return 130

            if line.strip().lower() in _EXIT_COMMANDS:
                self._output(_FAREWELL)
                return 0

            try:
                address = self._tokenizer.tokenize(line)
            except Exception as exc:  # noqa: BLE001 — boundary catch, per design
                self._output(f"Error: could not parse input ({type(exc).__name__}: {exc})")
                continue

            # Empty input is normal, not an error: note it, keep prompting.
            self._output(address.to_json() if address.to_dict() else _NO_COMPONENTS)
