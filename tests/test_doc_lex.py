"""iml/doc_lex.py restates the validator's line-level rules; each pattern and helper must
be the validator's own (design-0.5 section 1: parse_doc segments and classifies as the
validator does). The codec package imports nothing from canon/, so the equality is checked
here, against the pinned file."""

import ast
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

from iml import default_registry, doc_lex  # noqa: E402
from validator_oracle import VALIDATOR, namespace  # noqa: E402

PATTERNS = ("RE_DOC_MARKER", "RE_DECL_HEAD", "RE_BAD_DECL_HEAD", "RE_TEMPORAL_PREFIX", "RE_TEMPORAL_BIND",
            "RE_TEMPORAL_NOTE", "RE_TAG_LINE", "RE_TAG_TEXT", "RE_KEY", "RE_ENTITY_TOKEN", "RE_BRACKET_GROUPS")
SAMPLES = ['[READ:@SRC|path="a,b"]', '[TAG] text', '[TAG:x][B:y]', '[LIST:known_repos]', '[READ]=>[FMT]',
           '[NOTE:"x]y"]', 'T:x', 'A:y⇒z', 'KEY:value', 'T[1]=2001', 'T[2] note', '[sic] prose', '[not a tag',
           '[Σ]', '[φ:@LOG|whr=lvl:fatal]', 'https://example.com', '=>[Ω]', 'plain prose', '[W:"a\\"b"]',
           '[GEN:@IMG|txt="[draft]"]=>[Ω]', '[A-B:c]', '[a:b]', '']


class TestDocLex(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ns = namespace()
        cls.src = VALIDATOR.read_text(encoding="utf-8")
        reg = default_registry()
        cls.verbs = frozenset(reg.verbs) | frozenset(reg.aliases)

    def test_patterns_are_the_validators(self):
        for name in PATTERNS:
            with self.subTest(name=name):
                mine, theirs = getattr(doc_lex, name), self.ns[name]
                self.assertEqual((mine.pattern, mine.flags), (theirs.pattern, theirs.flags))
        self.assertEqual(doc_lex.STRUCTURAL_CHARS, self.ns["Linter"].STRUCTURAL_CHARS)
        self.assertEqual(self.verbs, frozenset(self.ns["VERBS"]) | frozenset(self.ns["ALIASES"]))

    def test_inline_patterns_stand_in_the_validator(self):
        """The three patterns the validator writes inline, as raw strings in its source."""
        literals = {node.value for node in ast.walk(ast.parse(self.src))
                    if isinstance(node, ast.Constant) and isinstance(node.value, str)}
        for name in ("RE_DELIMITER", "RE_DOUBLE_INLINE", "RE_DOUBLE_SPAN"):
            self.assertIn(getattr(doc_lex, name).pattern, literals, name)

    def test_helpers_answer_as_the_validators(self):
        linter = self.ns["Linter"]("<x>", "")
        for s in SAMPLES:
            with self.subTest(s=s):
                self.assertEqual(doc_lex.mask_quoted(s), self.ns["mask_quoted"](s))
                self.assertEqual(doc_lex.head_of(s), linter.head_of(s))
                self.assertEqual(doc_lex.is_body_form(s, self.verbs), linter.is_body_form(s))
                ms = self.ns["mask_quoted"](s)          # the preamble test written inline in lint_region
                self.assertEqual(doc_lex.is_tag_line(s), bool(self.ns["RE_TAG_LINE"].match(ms)) and "]=>" not in ms)
        for rest in ("{a}", "{a{b}c}", "{a}}", "{", "{a}{b}", "}"):
            self.assertEqual(doc_lex.find_close(rest), linter.find_close(rest), rest)

    def test_messages_are_the_validators(self):
        """Every wording taken from the validator stands in its source (format placeholders
        as the validator writes them)."""
        for name in dir(doc_lex):
            if name.startswith("MSG_") and name not in IML_ONLY:
                msg = getattr(doc_lex, name)
                fragment = max(msg.replace("%d", "%s").split("%s"), key=len)
                with self.subTest(name=name):
                    self.assertGreaterEqual(len(fragment), 12)
                    self.assertIn(fragment, self.src)
        self.assertIn(doc_lex.fullwidth_message("{a｜b}")[:20], self.src)
        self.assertIsNone(doc_lex.fullwidth_message("{a：b:c}"))      # the pipe segment has an ASCII colon


IML_ONLY = {"MSG_UNTERMINATED", "MSG_CONTINUATION_SEPARATED", "MSG_OPAQUE_OPEN", "MSG_OPAQUE_TRAILING",
            "MSG_SET_HEADER", "MSG_TRAILING_DECL", "MSG_TRAILING_CONTINUATION", "MSG_NESTED_TWO_SEGMENTS",
            "MSG_NESTED_FORM", "MSG_NESTED_B8", "MSG_CONTROL", "MSG_BOM", "MSG_FULLWIDTH_TRAILING",
            "MSG_PREAMBLE_CHAIN"}


if __name__ == "__main__":
    unittest.main()
