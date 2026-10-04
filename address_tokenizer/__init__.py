"""Address Tokenizer — parses free-form address strings into components.

Public exports (populated as implementation lands, see design.md §2):
    Address — immutable value object
    AddressTokenizer — orchestrator
"""

from .model import Address

# from .tokenizer import AddressTokenizer

__all__ = ["Address"]
