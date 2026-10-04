"""AddressTokenizer orchestrator — splitting and rule dispatch.

See design.md §2.3–2.4: injectable rule list (default priority order),
comma-path split, and the regex-scan fallback for comma-free input.
Depends on the ComponentRule abstraction, not concrete rules.
"""
