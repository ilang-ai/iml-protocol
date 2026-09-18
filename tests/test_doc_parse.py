"""parse_doc and print_doc (design-0.5 sections 1, 3, 5 and 8): shapes, bodies, top-level
lines, layout that is not carried, the canonical print, and errors in the validator's
wording where it has one."""

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

from iml import Chain, Decl, IMLError, Text, parse_doc, parse_L2, print_doc  # noqa: E402
from validator_oracle import lint  # noqa: E402

M = "::ILANG::v5.0\n"


def one(src):
    items = parse_doc(M + src)
    assert items[0] == Text("::ILANG::v5.0")
    return items[1:]


class TestShapes(unittest.TestCase):
    def test_inline_and_header_body(self):
        self.assertEqual(one("::FACT{key:a|value:b}"), [Decl("FACT", head="key:a|value:b")])
        d, = one("::GENE{g|conf:c}\n  T:x\n  A:y⇒z\n  ::PRIOR{p:q}\n    reason:r")
        self.assertEqual(d.body, (Text("T:x"), Text("A:y⇒z"), Decl("PRIOR", head="p:q", body=[Text("reason:r")])))
        flush, = one("::CLAUSE{C|conf:c}\nT:a\nA:b⇒c\n[NOTE] tag text")
        indented, = one("::CLAUSE{C|conf:c}\n    T:a\n  A:b⇒c\n\t[NOTE] tag text")
        self.assertEqual(flush, indented)                              # flush-left or indented: layout
        trailing, = one("::MODE{M1|name:X}     T:same_line")
        self.assertEqual(trailing, Decl("MODE", head="M1|name:X", body=[Text("T:same_line")]))
        self.assertEqual(one("::MODE{M1|name:X}\n  T:same_line"), [trailing])

    def test_trailing_chain_and_body_chain_with_continuations(self):
        d, = one("::ACTIVATE{a} [READ:@SRC]=>[Ω]")
        self.assertEqual(d.body, (parse_L2("[READ:@SRC]=>[Ω]"),))
        d, = one("::ACTIVATE{a}\n  [READ:@SPEC|src=...]\n    =>[PARS|typ=v5.0]\n  =>[Ω]\n  ON:x")
        self.assertEqual(d.body, (parse_L2("[READ:@SPEC|src=...]=>[PARS|typ=v5.0]=>[Ω]"), Text("ON:x")))

    def test_spans(self):
        self.assertEqual(one("::PRIORITY{\n  a > b\n\n  c\n}"), [Decl("PRIORITY", shape="set", lines=["a > b", "c"])])
        self.assertEqual(one("::GENE_MUTABLE{s|\n  T:a|\n  Θ:b}"),
                         [Decl("GENE_MUTABLE", shape="wrapped", head="s|", lines=["T:a|", "Θ:b"])])
        self.assertEqual(one("::GENE_MUTABLE{s|\n  T:a|\n}"),
                         [Decl("GENE_MUTABLE", shape="wrapped", head="s|", lines=["T:a|", ""])])
        self.assertEqual(one("::MODULE::CORE{\n  [WHAT] x\n}"),
                         [Decl("MODULE", sub="CORE", shape="set", lines=["[WHAT] x"])])

    def test_double_brace(self):
        self.assertEqual(one("::SAY{@A→@B}{hi {there}}"), [Decl("SAY", addr="@A→@B", head="hi {there}")])
        self.assertEqual(one("::DISCOVER{@S}{\n  x\n}"), [Decl("DISCOVER", addr="@S", shape="set", lines=["x"])])
        self.assertEqual(one("::THINK{@S}{a\n  b}"), [Decl("THINK", addr="@S", shape="wrapped", head="a", lines=["b"])])
        self.assertEqual(one("::SILENCE{}"), [Decl("SILENCE")])

    def test_opaque(self):
        items = one("::UNTRUSTED{id:u|delimiter:EOF}\n<<<EOF\n  ::GENE{x}  \n\nEOF\n::END_UNTRUSTED{id:u}")
        self.assertEqual(items[0], Decl("UNTRUSTED", shape="opaque", head="id:u|delimiter:EOF",
                                        lines=["<<<EOF", "  ::GENE{x}  ", ""]))
        self.assertEqual(items[1], Decl("END_UNTRUSTED", head="id:u"))
        self.assertEqual(one("::UNTRUSTED{id:u}\n  src:x"), [Decl("UNTRUSTED", head="id:u", body=[Text("src:x")])])

    def test_prefix_sub_and_layout_whitespace(self):
        a = one("T[0]  ::EVENT {1998|x}\n      ::FACT{k:v}")
        b = one("T[0]\t::EVENT{1998|x}\n  ::FACT{k:v}")
        self.assertEqual(a, b)
        self.assertEqual(a, [Decl("EVENT", prefix="0", head="1998|x", body=[Decl("FACT", head="k:v")])])


class TestLines(unittest.TestCase):
    def test_top_level_texts(self):
        src = ("::ILANG::v5.0::SPEC\n[TYPE:x]\n[LIST:known_repos]\nColophon line one\n::FACT{a:b}\n\nT[1]=2001\n"
               "T[2] a note\nPARALLEL{a, b}  both\n→ annotation\n<<<EOF_note\nT[3] ::LATENCY{2}\n::CONFIDENCE{0.9}\n"
               "[READ:@SRC]=>[Ω]\n---\n::ILANG::v5.0::END\n")
        items = parse_doc(src)
        kinds = [type(x).__name__ for x in items]
        self.assertEqual(kinds, ["Text", "Text", "Text", "Text", "Decl", "Text", "Text", "Text", "Text", "Text",
                                 "Text", "Text", "Chain", "Text"])
        self.assertEqual(items[2], Text("[LIST:known_repos]"))          # a preamble tag, even with a verb name
        self.assertEqual(items[11], Text("::CONFIDENCE{0.9}"))
        self.assertEqual(lint(src)[1], [])
        # the same tag after the preamble is an operation line (and the validator reads it so)
        self.assertEqual(one("::FACT{a:b}\n[LIST:@X]"), [Decl("FACT", head="a:b"), parse_L2("[LIST:@X]")])

    def test_body_line_kinds(self):
        d, = one("::LESSON{id:l}\n  T:a\n  KEY:v|k:w\n  V:[a=1]\n  [NOTE] t\n  [NOTE:v]\n  prose line\n"
                 "  [sic] bracket prose\n  T[1]=x\n  T[2] note\n  → note\n  ::LATENCY{0}\n  [DPLO:@WORKER]=>[Ω]")
        self.assertEqual([type(b).__name__ for b in d.body], ["Text"] * 11 + ["Chain"])
        # TAG is a canon verb (SPEC.md 3.7): `[TAG] t` is an operation line, and not a chain IML carries
        with self.assertRaises(IMLError) as cm:
            one("::LESSON{id:l}\n  [TAG] t")
        self.assertEqual(cm.exception.code, "E300")

    def test_control_characters_and_line_ends(self):
        self.assertEqual(parse_doc(M + "::GENE{g}\r\n\t T:a \t\r\n"), parse_doc(M + "::GENE{g}\n  T:a\n"))
        self.assertEqual(parse_doc(M + "::FACT{a:b}\r"), parse_doc(M + "::FACT{a:b}"))     # one CR ends a line, as in 0.4
        for src, code in ((M + "::GENE{g}\n  T:a\tb\n", "E300"), (M + "::FACT{a\tb}\n", "E300"),
                          (M + "::FACT{a:b}\x0b\n", "E300"), (M + "::FACT{a:b}\r::FACT{c:d}", "E300"),
                          (M + "::FACT{a:b}\x85\n", "E300"), ("\ufeff" + M, "E502")):
            with self.assertRaises(IMLError) as cm:
                parse_doc(src)
            self.assertEqual(cm.exception.code, code, repr(src))
            self.assertIsInstance(cm.exception.offset, int)

    def test_empty_and_blank_documents(self):
        self.assertEqual(parse_doc(""), [])
        self.assertEqual(parse_doc("\n \n---\n"), [])


class TestPrint(unittest.TestCase):
    def test_canonical_forms(self):
        src = (M + "T[0]   ::EVENT{1998|x}     T:y\n::GENE{g}\nT:a\n::PRIORITY{\n    a > b\n}\n"
               "::GENE_MUTABLE{s|\n T:a|\n}\n::SAY{@A}{hi}\n  ::LATENCY{0}\n"
               "::UNTRUSTED{id:u|delimiter:E}\n  kept\nE\n::LESSON{l}\n  ::PRIOR{p}\n      T:q\n  [READ:@SRC]\n   =>[Ω]")
        expected = ("::ILANG::v5.0\nT[0] ::EVENT{1998|x}\n  T:y\n::GENE{g}\n  T:a\n::PRIORITY{\n  a > b\n}\n"
                    "::GENE_MUTABLE{s|\n  T:a|\n}\n::SAY{@A}{hi}\n  ::LATENCY{0}\n"
                    "::UNTRUSTED{id:u|delimiter:E}\n  kept\nE\n::LESSON{l}\n  ::PRIOR{p}\n    T:q\n  [READ:@SRC]=>[Ω]")
        self.assertEqual(print_doc(parse_doc(src)), expected)
        self.assertEqual(print_doc(parse_doc(expected)), expected)

    def test_blank_line_before_a_body_form_after_an_empty_body(self):
        """The one blank line of the print: without it the tag line (or the bind) would bind as
        the flush-left body of the declaration above it on reading."""
        for line in ("[NOTE:x]", "T[4]=2020"):
            items = one("::FACT{a:b}\n\n" + line)
            self.assertEqual(items, [Decl("FACT", head="a:b"), Text(line)])
            printed = print_doc([Text("::ILANG::v5.0")] + items)
            self.assertEqual(printed, M + "::FACT{a:b}\n\n" + line)
            self.assertEqual(parse_doc(printed)[1:], items)
            joined = one("::FACT{a:b}\n" + line)                          # without the blank line: its body
            self.assertEqual(joined, [Decl("FACT", head="a:b", body=[Text(line)])])
        # no blank line where the next line cannot bind
        self.assertEqual(print_doc(one("::FACT{a:b}\n\nT[1] note")), "::FACT{a:b}\nT[1] note")

    def test_idempotent_on_the_validator_selftest_document(self):
        from validator_oracle import namespace
        good = namespace()["GOOD_DOC"].replace("sbj=a fox", 'sbj="a fox"')   # a space in a bare value is E300 in IML
        items = parse_doc(good)
        printed = print_doc(items)
        self.assertEqual(parse_doc(printed), items)
        self.assertEqual(print_doc(parse_doc(printed)), printed)
        self.assertEqual(lint(printed + "\n")[1], [])
        with self.assertRaises(IMLError) as cm:
            parse_doc(namespace()["GOOD_DOC"])
        self.assertEqual(cm.exception.code, "E300")                 # the 0.4 chain rule stays: no space in a bare value


class TestWording(unittest.TestCase):
    def test_messages_follow_the_validator(self):
        """For every malformed document the validator rejects, IML's message is one of the
        validator's messages for it, or the codec's own chain message (codes of the chain layer)."""
        cases = json.loads((ROOT / "corpus" / "malformed" / "cases.json").read_text(encoding="utf-8"))
        same = 0
        for c in cases:
            if c["direction"] != "compile-document" or c["label"].startswith("stricter:") or not c["input"].startswith("::"):
                continue
            with self.assertRaises(IMLError) as cm:
                parse_doc(c["input"])
            messages = [f[3] for f in lint(c["input"])[1]]
            if cm.exception.message in messages:
                same += 1
            else:
                self.assertIn(cm.exception.code, ("E302", "E304"), (c["label"], cm.exception.message, messages))
        self.assertGreaterEqual(same, 20)


if __name__ == "__main__":
    unittest.main()
