"""Console loop behavior — scripted stdin, captured stdout (tasks Phase 6)."""

import json

import pytest

from address_tokenizer import AddressTokenizer
from address_tokenizer.app import ConsoleApp


def run_script(script: list[str], *, interrupt_at: int | None = None,
               eof_after: bool = True) -> tuple[list[str], int]:
    """Drive ConsoleApp with a scripted input sequence.

    Raises KeyboardInterrupt when the script is exhausted if
    interrupt_at is set to the step where the prompt should be hit.
    """
    calls = {"n": 0}
    outputs: list[str] = []

    def input_fn(prompt: str) -> str:
        i = calls["n"]
        calls["n"] += 1
        if interrupt_at is not None and i >= interrupt_at:
            raise KeyboardInterrupt
        if i >= len(script):
            if eof_after:
                raise EOFError
            return ""
        return script[i]

    app = ConsoleApp(AddressTokenizer(), input_fn=input_fn, output_fn=outputs.append)
    return outputs, app.run()


class TestLoopOutput:
    def test_spec_examples_print_valid_json(self) -> None:
        outputs, code = run_script(
            [
                "No 11, Chendering, 21080 Kuala Terengganu, Terengganu.",
                "No 11, Kuala Terengganu, Chendering",
                "exit",
            ]
        )
        assert code == 0
        json_lines = [ln for ln in outputs if ln.startswith("{")]
        assert len(json_lines) == 2
        first = json.loads(json_lines[0])
        assert first == {
            "apt": "No 11",
            "section": "Chendering",
            "postcode": "21080",
            "city": "Kuala Terengganu",
            "state": "Terengganu",
        }
        assert json.loads(json_lines[1])["city"] == "Kuala Terengganu"

    def test_empty_input_gets_note_not_crash(self) -> None:
        outputs, code = run_script(["", "   ", "exit"])
        assert code == 0
        assert "(no components found)" in outputs

    def test_loop_continues_after_garbage(self) -> None:
        # garbage parses to empty (section) rather than raising, but a
        # genuinely raising line must not kill the loop either
        outputs, code = run_script(["!!!!", "Kajang", "exit"])
        assert code == 0
        assert any("Kajang" in ln for ln in outputs)


class TestExitPaths:
    @pytest.mark.parametrize("cmd", ["exit", "quit", "EXIT", " Quit "])
    def test_exit_commands(self, cmd: str) -> None:
        outputs, code = run_script([cmd])
        assert code == 0
        assert "Goodbye." in outputs

    def test_eof_exits_zero(self) -> None:
        outputs, code = run_script(["Kajang"])  # eof after script exhausted
        assert code == 0
        assert "Goodbye." in outputs

    def test_ctrl_c_returns_130(self) -> None:
        outputs, code = run_script([], interrupt_at=0)
        assert code == 130
        assert any("Interrupted" in ln for ln in outputs)


class TestErrorContainment:
    def test_raising_line_does_not_kill_loop(self, monkeypatch: pytest.MonkeyPatch) -> None:
        outputs: list[str] = []
        script = ["boom", "Kajang", "exit"]
        state = {"n": 0}

        def input_fn(prompt: str) -> str:
            i = state["n"]
            state["n"] += 1
            return script[i] if i < len(script) else (_ for _ in ()).throw(EOFError())

        app = ConsoleApp(AddressTokenizer(), input_fn=input_fn, output_fn=outputs.append)

        def exploding_tokenize(raw: str):
            if raw == "boom":
                raise RuntimeError("simulated failure")
            return AddressTokenizer().tokenize(raw)

        monkeypatch.setattr(app._tokenizer, "tokenize", exploding_tokenize)
        code = app.run()
        assert code == 0
        assert any("Error:" in ln for ln in outputs)
        # loop continued: the good line after the failure still parsed
        assert any("Kajang" in ln for ln in outputs)
