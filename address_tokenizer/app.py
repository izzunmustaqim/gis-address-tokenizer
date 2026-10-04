"""ConsoleApp — I/O boundary for the interactive loop.

See design.md §2.5: reads input, invokes the tokenizer, prints JSON,
converts failures into user-facing messages. Injected input_fn/output_fn
keep it testable; run() returns an exit code.
"""
