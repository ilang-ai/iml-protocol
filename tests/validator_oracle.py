"""The pinned canon validator as a legality oracle for the document tests (SPEC-IML-0.5.md
section 6). It is loaded the way tools/derive_registry.py loads it: the file
canon/ilang_grammar_validator.py is executed as a module under another name, so its
command line does not run. Only the tests import it; the codec package imports nothing
from canon/.

lint(text) runs one Linter over text and returns (raw_mode, [ERROR findings]); a text that
begins with a `::ILANG::` marker is linted in raw mode, the reading IML follows."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "canon" / "ilang_grammar_validator.py"

_ns = None


def namespace():
    global _ns
    if _ns is None:
        ns = {"__name__": "iml_canon_validator", "__file__": str(VALIDATOR)}
        try:
            exec(compile(VALIDATOR.read_text(encoding="utf-8"), str(VALIDATOR), "exec"), ns)
        except SystemExit:
            pass
        _ns = ns
    return _ns


def lint(text):
    """(raw_mode, errors) for text; errors are the validator's (level, line, code, message)
    findings of level ERROR."""
    linter = namespace()["Linter"]("<doc>", text)
    findings = linter.run()
    return linter.raw_mode, [f for f in findings if f[0] == "ERROR"]
