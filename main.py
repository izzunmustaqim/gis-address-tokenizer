"""Entry point: wire up and run the console app."""

from address_tokenizer import AddressTokenizer
from address_tokenizer.app import ConsoleApp

if __name__ == "__main__":
    raise SystemExit(ConsoleApp(AddressTokenizer()).run())
