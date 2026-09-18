"""0.4, flow within the canon (SPEC-IML-0.4.md sections 2 to 7): the verb reference
target of BATC, the multi-line chain join on the compile side (a continuation line is
joined only after a closed operation; a line of whitespace only is a blank line), header
acceptance (0.4 written; 0.3 read by the same reader; 0.2 only with version="0.2";
version="0.3" names no surface), what the command line does with its input bytes (one
leading byte order mark dropped, input that is not UTF-8 reported as E300), and the two
assertions over the 72 chains of corpus/golden/: their 0.4 message is the 0.3 record
under the 0.4 header, and the 0.3 record decompiles under the default reader to the same
canonical text as its source.

0.5 changed on purpose, and these tests follow: compile writes the 0.5 header (#iml/0.5/
and the 0.5 registry digest); the default reader is 0.5 and reads a 0.4 and a 0.3 header
without a flag, so version="0.4" names no surface; `roundtrip` reads its file as a whole
I-Lang document (iml.doc_parse), so an operation line broken inside a quoted value is
reported there with the validator's wording for a bracket line."""

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

from iml import (DEFAULT_VERSION, VERSIONS, Chain, IMLError, Op, Value, compile, compile_document,  # noqa: E402
                 decompile, default_registry, parse_L2, print_L2)
from iml.__main__ import UNTERMINATED, join_chain_lines, non_empty_lines, parse_chain  # noqa: E402
from iml.codec import SURFACES, surface  # noqa: E402
from iml.l2 import ends_with_closed_operation  # noqa: E402
from test_roundtrip import PREAMBLE_LINES, run_validator  # noqa: E402

GOLDEN = ROOT / "corpus" / "golden"
GOLDEN_03 = ROOT / "corpus" / "golden-0.3"
WORKED = "[READ:@GH|path=readme.md]=>[XLAT|lng=zh]=>[FMT|fmt=md]=>[Ω]"
NOT_AN_ENTITY = "is not an @ENTITY (v3.0 \u00a72.2; BATC/Π excepted)"
ORPHAN = "orphan `=>` continuation: no preceding operation line"
SECOND_CHAIN = "a second operation chain on the line: IML carries one chain per line"
BOM = b"\xef\xbb\xbf"
# the four examples of design-0.4 section 3 (the roots are the registry's, see test_registry)
DESIGN_EXAMPLES = [
    ("[LIST:@LOCAL|mch=*.md]=>[Π:READ]=>[Σ]=>[Ω]", "LS@LCmc=*.md BT:RD MR $",
     "[LIST:@LOCAL|mch=*.md]=>[BATC:READ]=>[MERGE]=>[Ω]"),
    ("[BATC:READ|src=@LOCAL]=>[Ω]", "BT:RDsr=@LC $", "[BATC:READ|src=@LOCAL]=>[Ω]"),
    ("[BATC|op=READ]=>[Ω]", "BTop=READ $", "[BATC|op=READ]=>[Ω]"),
    ("[BATC:@SRC|op=SCAN]=>[Ω]", "BT@SRop=SCAN $", "[BATC:@SRC|op=SCAN]=>[Ω]"),
]


def body(message):
    return message.split(" ", 1)[1]


def run_cli(*args, stdin=None):
    """stdin is text (sent as UTF-8) or the bytes to send as they are."""
    if isinstance(stdin, str):
        stdin = stdin.encode("utf-8")
    r = subprocess.run([sys.executable, "-m", "iml", *args], cwd=str(ROOT), input=stdin, capture_output=True)
    r.stdout = r.stdout.decode("utf-8").replace("\r\n", "\n")
    r.stderr = r.stderr.decode("utf-8").replace("\r\n", "\n")
    return r


class TestVerbRef(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reg = default_registry()
        cls.h = cls.reg.header

    def test_design_examples(self):
        for src, iml, canon in DESIGN_EXAMPLES:
            with self.subTest(src=src):
                a = parse_L2(src)
                m = compile(a)
                self.assertEqual(m, self.h + " " + iml)
                self.assertEqual(decompile(m), a)
                self.assertEqual(print_L2(a), canon)
                self.assertEqual(print_L2(decompile(m)), canon)
                self.assertEqual(compile(decompile(m)), m)
                self.assertEqual(print_L2(parse_L2(canon)), canon)

    def test_alias_collapses_and_the_ast_holds_the_canon_name(self):
        ref = Op("BATC", None, (), "MERGE")
        for src in ("[BATC:MERGE]", "[Π:MERGE]", "[BATC:Σ]", "[Π:Σ]"):
            with self.subTest(src=src):
                a = parse_L2(src)
                self.assertEqual(a, Chain([ref]))
                self.assertEqual(a.ops[0].verbref, "MERGE")
                self.assertIsNone(a.ops[0].target)
                self.assertEqual(print_L2(a), "[BATC:MERGE]")
                self.assertEqual(body(compile(a)), "BT:MR")
        self.assertEqual(parse_L2("[Π:Π]"), Chain([Op("BATC", verbref="BATC")]))
        self.assertEqual(body(compile(parse_L2("[BATC:BATC]"))), "BT:BT")
        # every alias except Ω works as a reference and collapses to its verb
        for alias, verb in self.reg.aliases.items():
            if verb == "OUT":
                continue
            a = parse_L2("[Π:%s]" % alias)
            self.assertEqual(a.ops[0].verbref, verb, alias)
            self.assertEqual(body(compile(a)), "BT:" + self.reg.verb_root[verb])
            self.assertEqual(print_L2(a), "[BATC:%s]" % verb)
        # every verb with a root can be referenced; the IML root is the verb's own root
        for verb, root in self.reg.verb_root.items():
            a = parse_L2("[BATC:%s]" % verb)
            self.assertEqual(body(compile(a)), "BT:" + root)
            self.assertEqual(decompile(self.h + " BT:" + root), a)

    def test_three_spellings_three_asts(self):
        ref = parse_L2("[BATC:READ]")
        mod = parse_L2("[BATC|op=READ]")
        ent = parse_L2("[BATC:@SRC]")
        self.assertNotEqual(ref, mod)
        self.assertNotEqual(ref, ent)
        self.assertNotEqual(mod, ent)
        self.assertEqual(ref.ops[0], Op("BATC", verbref="READ"))
        self.assertEqual(mod.ops[0], Op("BATC", None, [("op", Value("bare", "READ"))]))
        self.assertEqual(ent.ops[0], Op("BATC", "SRC"))
        for a, iml in ((ref, "BT:RD"), (mod, "BTop=READ"), (ent, "BT@SR")):
            m = compile(a)
            self.assertEqual(body(m), iml)
            self.assertEqual(decompile(m), a)
            self.assertEqual(print_L2(decompile(m)), print_L2(a))
        # the conflict form is accepted as written on both sides: the codec judges no conflict
        both = parse_L2("[BATC:READ|op=FMT]")
        self.assertEqual(both.ops[0], Op("BATC", None, [("op", Value("bare", "FMT"))], "READ"))
        self.assertEqual(body(compile(both)), "BT:RDop=FMT")
        self.assertEqual(decompile(compile(both)), both)
        self.assertEqual(print_L2(both), "[BATC:READ|op=FMT]")

    def test_op_equality_hash_repr_and_exclusion(self):
        a = Op("BATC", verbref="READ")
        b = Op("BATC", None, (), "READ")
        c = Op("BATC")
        d = Op("BATC", "SRC")
        self.assertEqual(a, b)
        self.assertEqual(hash(a), hash(b))
        self.assertNotEqual(a, c)
        self.assertNotEqual(a, d)
        self.assertNotEqual(hash(a), hash(c))
        self.assertIn("verbref='READ'", repr(a))
        self.assertNotIn("verbref", repr(c))
        self.assertEqual(eval(repr(a)), a)
        self.assertEqual(eval(repr(c)), c)
        with self.assertRaises(ValueError):
            Op("BATC", "SRC", (), "READ")
        self.assertEqual(len({a, b, c, d}), 3)

    def test_colon_inside_a_value_stays_content(self):
        a = parse_L2("[φ:@LOG|whr=lvl:fatal]=>[Π:CNT]=>[BATC:READ|whr=lvl:fatal,path=a:b]=>[Ω]")
        self.assertEqual(a.ops[0].mods[0][1], Value("bare", "lvl:fatal"))
        self.assertEqual(a.ops[2].verbref, "READ")
        m = compile(a)
        self.assertEqual(body(m), "FL@LGwh=lvl:fatal BT:CT BT:RDwh=lvl:fatal,pt=a:b $")
        self.assertEqual(decompile(m), a)
        self.assertEqual(print_L2(decompile(m)),
                         "[FILT:@LOG|whr=lvl:fatal]=>[BATC:CNT]=>[BATC:READ|whr=lvl:fatal,path=a:b]=>[Ω]")

    def test_continuations_after_a_verb_reference(self):
        h = self.h
        self.assertEqual(decompile(h + " BT:RD"), Chain([Op("BATC", verbref="READ")]))
        self.assertEqual(decompile(h + " BT:RDsr=@LC"),
                         Chain([Op("BATC", None, [("src", Value("entity", "LOCAL"))], "READ")]))
        self.assertEqual(decompile(h + " BT:RD MR"), Chain([Op("BATC", verbref="READ"), Op("MERGE")]))
        self.assertEqual(decompile(h + "\nBT:RD\nBT:MR $"),
                         [Chain([Op("BATC", verbref="READ")]), Chain([Op("BATC", verbref="MERGE"), Op("OUT")])])

    def test_ilang_errors(self):
        for src, code, text in (("[BATC:REED]", "E304", "BATC verb reference `REED` is not a registered verb or alias"),
                                ("[BATC:read]", "E304", "BATC verb reference `read` is not a registered verb or alias"),
                                ("[Π:Ω]", "E502", "OUT cannot be batched: not representable in IML"),
                                ("[BATC:OUT]", "E502", "OUT cannot be batched"),
                                ("[LOOP:READ]", "E300", "operation target `READ` " + NOT_AN_ENTITY),
                                ("[READ:x]", "E300", "operation target `x` " + NOT_AN_ENTITY),
                                ("[BATC:]", "E300", "empty target after `:`"),
                                ("[BATC: READ]", "E300", "whitespace is not allowed outside a quoted value"),
                                ("[BATC:READ ]", "E300", "whitespace is not allowed outside a quoted value"),
                                ("[BATC:READ|]", "E300", "modifier lacks `=`"),
                                ("[BATC:READ]=>", "E300", "missing operation after `=>`"),
                                ("[READ]=>=>[FMT]", "E300", "expected `[` to open an operation"),
                                ("[BATC:READ:X]", "E304", "`READ:X`"),
                                ("[Φ:@GH]", "E304", "unknown verb"),          # the validator: E305, unknown alias
                                ("[BATC:@SRC:READ]", "E200", "'@SRC:READ'"),
                                ("[READ:@SRC]=>[Ω] [FMT]=>[Ω]", "E502", SECOND_CHAIN),
                                ("[READ] [FMT]", "E502", SECOND_CHAIN),
                                ("[READ]  \t[FMT]", "E502", SECOND_CHAIN),
                                ("[READ] =>[FMT]", "E300", "whitespace is not allowed"),
                                ("[READ]=> [FMT]", "E300", "whitespace is not allowed"),
                                ("[READ|path=a] b", "E300", "whitespace is not allowed"),
                                ("=>[READ]", "E300", ORPHAN),
                                ("=>", "E300", ORPHAN)):
            with self.subTest(src=src):
                with self.assertRaises(IMLError) as cm:
                    parse_L2(src)
                self.assertEqual(cm.exception.code, code)
                self.assertIn(text, cm.exception.message)
                self.assertIsInstance(cm.exception.offset, int)
        with self.assertRaises(IMLError) as cm:
            parse_L2("[LOOP:READ]")
        self.assertEqual((cm.exception.offset, cm.exception.op_index), (6, 0))
        with self.assertRaises(IMLError) as cm:
            parse_L2("[READ:@SRC]=>[Ω] [FMT]=>[Ω]")
        self.assertEqual(cm.exception.offset, 16)
        # a quoted value keeps its `]`, space and `[`: no second chain there
        self.assertEqual(parse_L2('[READ|path="] ["]').ops[0].mods[0][1], Value("quoted", "] ["))

    def test_messages_follow_the_validator_where_it_has_a_wording(self):
        """SPEC-IML-0.4.md section 7: the two messages the codec takes from the validator
        are the validator's, backticks included; the validator's E305 (unknown alias) is
        E304 in the codec."""
        lines = ["[LOOP:READ]=>[Ω]", "[LIST:@LOCAL]=>[BATC:REED]=>[Ω]", "[Φ:@GH]=>[Ω]"]
        rep = run_validator(lines)
        found = {f["line"] - PREAMBLE_LINES: (f["code"], f["message"]) for f in rep["findings"] if f["level"] == "ERROR"}
        self.assertEqual(sorted(found), [1, 2, 3])
        for no, code in ((1, "E300"), (2, "E304")):
            with self.assertRaises(IMLError) as cm:
                parse_L2(lines[no - 1])
            self.assertEqual((cm.exception.code, cm.exception.message), found[no], lines[no - 1])
            self.assertEqual(cm.exception.code, code)
            self.assertIn("`", cm.exception.message)
            self.assertNotIn("'", cm.exception.message)
        self.assertEqual(found[3][0], "E305")
        with self.assertRaises(IMLError) as cm:
            parse_L2(lines[2])
        self.assertEqual(cm.exception.code, "E304")

    def test_iml_errors(self):
        h = self.h
        n = len(h) + 1
        for tail, code, offset, text in (("BT:", "E300", n + 3, "`BT:` must be followed by a verb root [A-Z0-9]{2}"),
                                         ("BT:R", "E300", n + 3, "seen 'R'"),
                                         ("BT:rd", "E300", n + 3, "seen 'rd'"),
                                         ("BT: RD", "E300", n + 3, "seen ' R'"),
                                         ("BT:$", "E300", n + 3, "seen '$'"),
                                         ("BT:@SR", "E300", n + 3, "seen '@S'"),
                                         ("BT:XX", "E304", n + 3, "BATC verb reference root 'XX' is not in the registry"),
                                         ("RD:FM", "E300", n + 2, "`:` after a root other than BT (RD)"),
                                         ("BT:RD@SR", "E300", n + 5, "a target after a verb reference"),
                                         ("BT:RD:MR", "E300", n + 5, "stray character ':'"),
                                         ("$:RD", "E300", n + 1, "`$` (OUT) takes no verb reference"),
                                         ("RD BT:RD@SR", "E300", n + 8, "a target after a verb reference")):
            with self.subTest(tail=tail):
                with self.assertRaises(IMLError) as cm:
                    decompile(h + " " + tail)
                self.assertEqual(cm.exception.code, code)
                self.assertEqual(cm.exception.offset, offset)
                self.assertIn(text, cm.exception.message)
        with self.assertRaises(IMLError) as cm:
            decompile(h + " RD BT:RD@SR")
        self.assertEqual(cm.exception.op_index, 1)
        with self.assertRaises(IMLError) as cm:
            decompile(h + "\nRD\nBT:XX")
        self.assertEqual((cm.exception.code, cm.exception.offset), ("E304", len(h) + 1 + 3 + 3))

    def test_hand_built_ast_is_validated_on_compile(self):
        for op, code, text in ((Op("LOOP", verbref="READ"), "E300", "only BATC references a verb"),
                               (Op("BATC", verbref="OUT"), "E502", "OUT cannot be batched"),
                               (Op("BATC", verbref="REED"), "E304", "not a registered verb"),
                               (Op("BATC", verbref="Σ"), "E304", "not a registered verb"),
                               (Op("OUT", verbref="READ"), "E502", "OUT with a verb reference")):
            with self.subTest(op=repr(op)):
                with self.assertRaises(IMLError) as cm:
                    compile(Chain([op]))
                self.assertEqual(cm.exception.code, code)
                self.assertIn(text, cm.exception.message)
                self.assertEqual(cm.exception.op_index, 0)
        with self.assertRaises(IMLError) as cm:
            compile_document([Chain([Op("READ")]), Chain([Op("LOOP", verbref="READ")])])
        self.assertEqual(cm.exception.code, "E300")
        self.assertIn("chain 1", cm.exception.message)

    def test_no_0_2_spelling(self):
        a = parse_L2("[Π:READ]=>[Ω]")
        with self.assertRaises(IMLError) as cm:
            compile(a, version="0.2")
        self.assertEqual(cm.exception.code, "E502")
        self.assertIn("0.2 surface", cm.exception.message)
        with self.assertRaises(IMLError) as cm:
            decompile(self.reg.header_for("0.2") + " BT:RD", version="0.2")
        self.assertEqual(cm.exception.code, "E300")
        self.assertIn("stray character ':'", cm.exception.message)
        self.assertFalse(SURFACES["0.2"].verbref)
        self.assertTrue(SURFACES["0.5"].verbref)


class TestJoinChainLines(unittest.TestCase):
    ONE = "[CREA:@LOCAL|path=auth/login.go]=>[TEST]=>[REVW]=>[Ω]"
    MULTI = "[CREA:@LOCAL|path=auth/login.go]\n  =>[TEST]\n  =>[REVW]\n  =>[Ω]\n"

    def test_join(self):
        self.assertEqual(join_chain_lines(self.MULTI), [(1, self.ONE)])
        self.assertEqual(join_chain_lines(self.MULTI.replace("\n", "\r\n")), [(1, self.ONE)])
        self.assertEqual(join_chain_lines(self.MULTI.replace("  =>", "\t=>")), [(1, self.ONE)])
        self.assertEqual(join_chain_lines(self.MULTI.replace("  =>", "=>")), [(1, self.ONE)])
        self.assertEqual(join_chain_lines(self.MULTI.replace("  =>", "    =>")), [(1, self.ONE)])
        self.assertEqual(join_chain_lines(self.ONE), [(1, self.ONE)])
        self.assertEqual(join_chain_lines(""), [])
        self.assertEqual(join_chain_lines("\n\n"), [])
        # one-line chains are one entry each, exactly as non_empty_lines reads them
        two = "[READ]\n[FMT]\n"
        self.assertEqual(join_chain_lines(two), non_empty_lines(two))

    def test_same_ast_message_and_print_as_one_line(self):
        (no, text), = join_chain_lines(self.MULTI)
        self.assertEqual(no, 1)
        a = parse_L2(text)
        self.assertEqual(a, parse_L2(self.ONE))
        self.assertEqual(compile(a), compile(parse_L2(self.ONE)))
        self.assertEqual(print_L2(a), self.ONE)
        self.assertEqual(print_L2(decompile(compile(a))), self.ONE)

    def test_blank_line_ends_the_chain_and_numbers_are_first_lines(self):
        data = "[READ]\n  =>[FMT]\n\n[LIST]\n\n\n[Ω]\n  =>[X]\n"
        self.assertEqual(join_chain_lines(data), [(1, "[READ]=>[FMT]"), (4, "[LIST]"), (7, "[Ω]=>[X]")])
        with self.assertRaises(IMLError) as cm:
            parse_L2(join_chain_lines(data)[2][1])
        self.assertEqual(cm.exception.code, "E502")     # OUT not last, judged on the joined text

    def test_orphan_continuation(self):
        for data, entries in (("=>[READ]\n", [(1, "=>[READ]")]),
                              ("  =>[READ]\n", [(1, "=>[READ]")]),
                              ("[READ]\n\n  =>[FMT]\n", [(1, "[READ]"), (3, "=>[FMT]")]),
                              ("\n\n=>[FMT]\n[READ]\n", [(3, "=>[FMT]"), (4, "[READ]")]),
                              ("=>[A]\n=>[B]\n", [(1, "=>[A]"), (2, "=>[B]")])):   # an orphan opens no chain
            with self.subTest(data=data):
                self.assertEqual(join_chain_lines(data), entries)
        with self.assertRaises(IMLError) as cm:
            parse_L2("=>[READ]")
        self.assertEqual((cm.exception.code, cm.exception.offset), ("E300", 0))
        self.assertEqual(cm.exception.message, ORPHAN)

    def test_continuation_is_joined_only_after_a_closed_operation(self):
        """0.4.1: the two inputs of the review of 0.4.0 compiled to `RDwh=abc=>def` and
        `RDwh=abc=>x`, chains that no single line spells and that the validator rejects."""
        for data, offset in (('[READ|whr="abc\n  =>def"]\n', 14),          # the line break inside a quoted value
                             ("[READ|whr=abc\n  =>x]\n", 13),              # inside a bare value
                             ('[READ|whr="a]\n  =>b"]\n', 13),             # `]` before the break, but inside quotes
                             ('[READ|whr="a\\"]\n  =>b"]\n', 15),          # an escaped quote does not close the value
                             ("[READ]=>\n  =>[FMT]\n", 8),                 # a line ending in the pipe operator
                             ("[READ]#c\n  =>[FMT]\n", 8),                 # text after the operation
                             ("[READ]  \n  =>[FMT]\n", 8),                 # trailing whitespace above the break
                             ("[READ\n=>[FMT]\n  =>[LIST]\n", 5)):         # further lines go with the refused chain
            with self.subTest(data=data):
                (no, err), = join_chain_lines(data)
                self.assertEqual(no, 1)
                self.assertIsInstance(err, IMLError)
                self.assertEqual((err.code, err.message, err.offset), ("E300", UNTERMINATED, offset))
                with self.assertRaises(IMLError) as cm:
                    parse_chain(err)
                self.assertIs(cm.exception, err)
        self.assertIn("continuation after an unterminated operation line", UNTERMINATED)
        # a closed operation above the break joins as before, a `]` or a quote inside its quoted value included
        for data, joined in (('[READ|path="a]"]\n  =>[FMT]\n', '[READ|path="a]"]=>[FMT]'),
                             ('[READ|path="a\\"]"]\n  =>[FMT]\n', '[READ|path="a\\"]"]=>[FMT]'),
                             ('[READ|path="a=\\"b"]\n  =>[FMT]\n', '[READ|path="a=\\"b"]=>[FMT]'),
                             ('[READ|path="x\\\\"]\n  =>[FMT]\n', '[READ|path="x\\\\"]=>[FMT]')):
            with self.subTest(data=data):
                self.assertEqual(join_chain_lines(data), [(1, joined)])
                self.assertEqual(parse_chain(joined), parse_L2(joined))
                self.assertEqual(len(parse_L2(joined).ops), 2)
        for text, closed in (("[READ]", True), ("[READ]=>[FMT|fmt=md]", True), ('[READ|path="]"]', True), ("", False),
                             ("[READ", False), ("[READ]=>", False), ('[READ|path="]', False), ('[READ|path="a\\"]', False),
                             ("[READ] ", False), ("=>[READ]", True)):
            self.assertEqual(ends_with_closed_operation(text), closed, text)
        # the chains before and after a refused chain are read as usual
        data = "[LIST]\n[READ|whr=abc\n  =>x]\n  =>[FMT]\n\n[FMT]\n  =>[Ω]\n"
        entries = join_chain_lines(data)
        self.assertEqual([no for no, _ in entries], [1, 2, 6])
        self.assertEqual((entries[0][1], entries[2][1]), ("[LIST]", "[FMT]=>[Ω]"))
        self.assertIsInstance(entries[1][1], IMLError)

    def test_continuation_spellings_the_validator_accepts(self):
        """SPEC-IML-0.4.md section 0.3: a space after the `=>` of a continuation line, and a
        `=>` line under a line that ends in `=>`, pass the validator with 0 errors; both
        are E300 here, reported at the chain's first line."""
        spaced = "[READ:@SRC]\n  => [Ω]\n"
        doubled = "[READ:@SRC]=>\n  =>[Ω]\n"
        for data in (spaced, doubled):
            rep = run_validator(data.rstrip("\n").split("\n"))
            self.assertEqual([f for f in rep["findings"] if f["level"] == "ERROR"], [], data)
        (no, text), = join_chain_lines(spaced)
        self.assertEqual(text, "[READ:@SRC]=> [Ω]")
        with self.assertRaises(IMLError) as cm:
            parse_chain(text)
        self.assertEqual((cm.exception.code, cm.exception.offset), ("E300", 13))
        (no, err), = join_chain_lines(doubled)
        self.assertEqual((no, err.code, err.message, err.offset), (1, "E300", UNTERMINATED, 13))

    def test_whitespace_only_line_is_a_blank_line(self):
        """As the validator reads it: the line ends the current chain, opens none, and is
        skipped; a `=>` line after it is an orphan."""
        for blank in ("   ", "\t", " \t ", "  \r", "\u3000", "\xa0 "):
            with self.subTest(blank=blank):
                data = "[READ]\n" + blank + "\n  =>[FMT]\n"
                self.assertEqual(join_chain_lines(data), [(1, "[READ]"), (3, "=>[FMT]")])
                data = "[READ]\n  =>[FMT]\n" + blank + "\n[LIST]\n" + blank + "\n"
                self.assertEqual(join_chain_lines(data), [(1, "[READ]=>[FMT]"), (4, "[LIST]")])
        self.assertEqual(join_chain_lines("  \n\t\n"), [])
        rep = run_validator(["[READ:@SRC]", "   ", "  =>[Ω]"])
        errors = [(f["line"] - PREAMBLE_LINES, f["code"], f["message"]) for f in rep["findings"] if f["level"] == "ERROR"]
        self.assertEqual(errors, [(3, "E300", ORPHAN)])
        r = run_cli("compile", stdin="[READ]\n   \n[FMT]\n \t \n  =>[LIST]\n")
        self.assertEqual(r.returncode, 1)
        self.assertEqual(r.stdout.splitlines(), [default_registry().header + " RD", default_registry().header + " FM"])
        self.assertIn("<stdin>:5: E300", r.stderr)
        self.assertIn(ORPHAN, r.stderr)

    def test_offsets_count_in_the_joined_text(self):
        data = "[READ:@SRC]\n  =>[FMT|pth=x]\n  =>[Ω]\n"
        (no, text), = join_chain_lines(data)
        self.assertEqual(text, "[READ:@SRC]=>[FMT|pth=x]=>[Ω]")
        with self.assertRaises(IMLError) as cm:
            parse_L2(text)
        self.assertEqual((cm.exception.code, cm.exception.offset, cm.exception.op_index), ("E302", 18, 1))
        # trailing whitespace on a continuation line is an error at its joined offset
        data = "[READ:@SRC]\n  =>[Ω]  \n"
        (no, text), = join_chain_lines(data)
        self.assertEqual(text, "[READ:@SRC]=>[Ω]  ")
        with self.assertRaises(IMLError) as cm:
            parse_L2(text)
        self.assertEqual((cm.exception.code, cm.exception.offset), ("E300", len(text) - 1))

    def test_cli_compile_document_and_roundtrip(self):
        expected = compile(parse_L2(self.ONE))
        r = run_cli("compile", stdin=self.MULTI)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout, expected + "\n")
        r = run_cli("compile", stdin=self.MULTI.replace("\n", "\r\n"))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout, expected + "\n")
        doc_src = self.MULTI + "\n[PLAN:@SRC|len=5-15]=>[Ω]\n\n[DPLO:@WORKER]\n  =>[CHEK|whr=status:200]\n  =>[Ω]\n"
        asts = [parse_L2(t) for _, t in join_chain_lines(doc_src)]
        self.assertEqual(len(asts), 3)
        r = run_cli("compile", "--document", stdin=doc_src)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout, compile_document(asts) + "\n")
        r = run_cli("decompile", stdin=r.stdout)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout.splitlines(), [print_L2(a) for a in asts])
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "multi.ilang"
            p.write_bytes(doc_src.encode("utf-8"))
            r = run_cli("roundtrip", str(p))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn(":1 OK", r.stdout)
        self.assertIn(":6 OK", r.stdout)
        self.assertIn(":8 OK", r.stdout)
        self.assertIn("document OK (3 chains under one header, 4 lines)", r.stdout)
        self.assertIn("3 chain(s), 0 failure(s)", r.stdout)

    def test_cli_errors_name_the_first_line_of_the_chain(self):
        r = run_cli("compile", stdin="[READ:@SRC]\n  =>[FMT|pth=x]\n")
        self.assertEqual(r.returncode, 1)
        self.assertIn("<stdin>:1: E302", r.stderr)
        self.assertIn("offset 18", r.stderr)
        r = run_cli("compile", stdin="[READ]\n\n  =>[FMT]\n")
        self.assertEqual(r.returncode, 1)
        self.assertIn("<stdin>:3: E300", r.stderr)
        self.assertIn(ORPHAN, r.stderr)
        r = run_cli("compile", "--document", stdin="  =>[FMT]\n")
        self.assertEqual(r.returncode, 1)
        self.assertIn("<stdin>:1: E300", r.stderr)
        r = run_cli("compile", stdin="[READ]=>[Ω] [FMT]=>[Ω]\n")
        self.assertEqual(r.returncode, 1)
        self.assertIn("<stdin>:1: E502", r.stderr)
        self.assertIn(SECOND_CHAIN, r.stderr)
        # a continuation under an unterminated operation line: the chain's first line, the
        # chains before it already printed, nothing compiled from the broken one
        for stdin in ('[LIST]\n[READ|whr="abc\n  =>def"]\n', "[LIST]\n[READ|whr=abc\n  =>x]\n"):
            r = run_cli("compile", stdin=stdin)
            self.assertEqual(r.returncode, 1)
            self.assertEqual(r.stdout, default_registry().header + " LS\n")
            self.assertIn("<stdin>:2: E300 Syntax Error: " + UNTERMINATED, r.stderr)
            self.assertNotIn("=>def", r.stdout + r.stderr)
            r = run_cli("compile", "--document", stdin=stdin)
            self.assertEqual((r.returncode, r.stdout), (1, ""))
            self.assertIn("<stdin>:2: E300", r.stderr)
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "broken.ilang"
            p.write_bytes(b'[READ|whr="abc\n  =>def"]\n')
            r = run_cli("roundtrip", str(p))
        self.assertEqual(r.returncode, 1)
        self.assertIn(":1: E300", r.stderr)
        # 0.5: roundtrip reads the file as a document; the validator does not read `[READ|whr="abc`
        # as an operation line (no closed bracket group), so the wording is the validator's own
        self.assertIn("bracket line is neither tag nor operation", r.stderr)

    def test_decompile_direction_does_not_join(self):
        h = default_registry().header
        for text in (h + "\nRD\n=>FM", h + "\nRD\n  =>FM", h + " RD\n=>FM"):
            with self.assertRaises(IMLError) as cm:
                decompile(text)
            self.assertEqual(cm.exception.code, "E300", text)
        r = run_cli("decompile", stdin=h + " RD\n  =>FM\n")
        self.assertEqual(r.returncode, 1)
        self.assertIn("<stdin>:2: E", r.stderr)


class TestCommandLineInput(unittest.TestCase):
    """0.4.1: what read_text does with the bytes it is given. The library functions take
    text and stay strict."""

    @classmethod
    def setUpClass(cls):
        cls.h = default_registry().header
        cls.message = compile(parse_L2(WORKED))

    def test_one_leading_bom_is_dropped(self):
        src = (WORKED + "\n").encode("utf-8")
        multi = "[DPLO:@WORKER]\n  =>[CHEK|whr=status:200]\n  =>[Ω]\n".encode("utf-8")
        document = (self.h + "\nRD\nBT:RD $\n").encode("utf-8")
        with tempfile.TemporaryDirectory() as tmp:
            files = {}
            for name, data in (("bom.ilang", BOM + src), ("bom-multi.ilang", BOM + multi),
                               ("bom.iml", BOM + (self.message + "\n").encode("utf-8")), ("bom-doc.iml", BOM + document),
                               ("bom-crlf.ilang", BOM + src.replace(b"\n", b"\r\n")), ("two-boms.ilang", BOM + BOM + src)):
                files[name] = Path(tmp) / name
                files[name].write_bytes(data)
                self.assertTrue(files[name].read_bytes().startswith(b"\xef\xbb\xbf"))
            for name in ("bom.ilang", "bom-crlf.ilang"):
                r = run_cli("compile", str(files[name]))
                self.assertEqual((r.returncode, r.stdout, r.stderr), (0, self.message + "\n", ""), name)
            r = run_cli("compile", "--document", str(files["bom.ilang"]))
            self.assertEqual((r.returncode, r.stdout), (0, compile_document([parse_L2(WORKED)]) + "\n"), r.stderr)
            r = run_cli("compile", str(files["bom-multi.ilang"]))
            self.assertEqual((r.returncode, r.stdout), (0, self.h + " DP@WR CKwh=status:200 $\n"), r.stderr)
            r = run_cli("roundtrip", str(files["bom.ilang"]))
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn("1 chain(s), 0 failure(s)", r.stdout)
            r = run_cli("decompile", str(files["bom.iml"]))
            self.assertEqual((r.returncode, r.stdout), (0, WORKED + "\n"), r.stderr)
            r = run_cli("decompile", str(files["bom-doc.iml"]))
            self.assertEqual((r.returncode, r.stdout.splitlines()), (0, ["[READ]", "[BATC:READ]=>[Ω]"]), r.stderr)
            # one mark is dropped, not two: the second reaches the parser and is refused
            r = run_cli("compile", str(files["two-boms.ilang"]))
            self.assertEqual(r.returncode, 1)
            self.assertIn(":1: E502", r.stderr)
        # the same on standard input
        r = run_cli("compile", stdin=BOM + src)
        self.assertEqual((r.returncode, r.stdout), (0, self.message + "\n"), r.stderr)
        r = run_cli("decompile", stdin=BOM + document)
        self.assertEqual((r.returncode, r.stdout.splitlines()), (0, ["[READ]", "[BATC:READ]=>[Ω]"]), r.stderr)
        r = run_cli("decompile", "--version", "0.2", stdin=BOM + (compile(parse_L2(WORKED), version="0.2") + "\n").encode("utf-8"))
        self.assertEqual((r.returncode, r.stdout), (0, WORKED + "\n"), r.stderr)

    def test_the_library_stays_strict_about_a_bom(self):
        for fn, text in ((parse_L2, "\ufeff" + WORKED), (decompile, "\ufeff" + self.message),
                         (decompile, "\ufeff" + self.h + "\nRD")):
            with self.assertRaises(IMLError) as cm:
                fn(text)
            self.assertEqual((cm.exception.code, cm.exception.offset), ("E502", 0), text)
        with self.assertRaises(IMLError) as cm:
            decompile("\ufeff" + compile(parse_L2(WORKED), version="0.2"), version="0.2")
        self.assertEqual(cm.exception.code, "E502")
        # inside a value the character is content, as any other
        a = parse_L2('[READ|path="a\ufeffb"]')
        self.assertEqual(decompile(compile(a)), a)

    def test_input_that_is_not_utf8_is_e300_without_a_traceback(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "latin1.ilang"
            p.write_bytes(b"[READ|path=caf\xe9]\n")
            for args in (("compile",), ("compile", "--document"), ("decompile",), ("decompile", "--version", "0.2"), ("roundtrip",)):
                r = run_cli(*args, str(p))
                self.assertEqual(r.returncode, 1, args)
                self.assertEqual(r.stdout, "")
                self.assertEqual(r.stderr, "%s:1: E300 Syntax Error: input is not valid UTF-8 (byte offset 14)\n" % p)
                self.assertNotIn("Traceback", r.stderr)
            # the offset counts the bytes of the input as read, a dropped byte order mark included
            p.write_bytes(BOM + b"[READ]\n[FMT|path=\xe9]\n")
            r = run_cli("compile", str(p))
            self.assertEqual((r.returncode, r.stdout), (1, ""))
            self.assertEqual(r.stderr, "%s:1: E300 Syntax Error: input is not valid UTF-8 (byte offset 20)\n" % p)
        r = run_cli("compile", stdin=b"[READ]\n[FMT|path=\xe9]\n")
        self.assertEqual((r.returncode, r.stdout), (1, ""))          # nothing is compiled from input that cannot be read
        self.assertEqual(r.stderr, "<stdin>:1: E300 Syntax Error: input is not valid UTF-8 (byte offset 17)\n")
        r = run_cli("decompile", stdin=self.message.encode("utf-8") + b" \xff\n")
        self.assertEqual(r.returncode, 1)
        self.assertIn("<stdin>:1: E300 Syntax Error: input is not valid UTF-8 (byte offset %d)" % (len(self.message.encode("utf-8")) + 1),
                      r.stderr)
        self.assertNotIn("Traceback", r.stderr)


class TestHeaderAcceptance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reg = default_registry()
        cls.hw = cls.reg.header                   # the header compile writes (0.5)
        cls.h04, cls.h03, cls.h02 = cls.reg.header_for("0.4"), cls.reg.header_for("0.3"), cls.reg.header_for("0.2")

    def test_versions(self):
        self.assertEqual(DEFAULT_VERSION, "0.5")
        self.assertEqual(VERSIONS, ("0.5", "0.2"))
        self.assertEqual(surface("0.5").reads, {"0.5", "0.4", "0.3"})
        self.assertEqual(surface("0.2").reads, {"0.2"})
        self.assertEqual(self.hw, "#iml/0.5/7e29fae7f5ea")
        self.assertEqual(self.h04, "#iml/0.4/88d05d0839c1")
        for v in ("0.3", "0.4"):
            with self.assertRaises(ValueError) as cm:
                surface(v)
            self.assertIn("default reader", str(cm.exception))

    def test_0_3_header_read_without_a_flag(self):
        a = parse_L2(WORKED)
        mw = compile(a)
        m03 = self.h03 + " " + body(mw)
        m04 = self.h04 + " " + body(mw)
        for m in (m03, m04):
            self.assertEqual(decompile(m), a)
            self.assertEqual(decompile(m + "\n"), a)
            self.assertEqual(decompile(m, version="0.5"), a)
            self.assertEqual(print_L2(decompile(m)), print_L2(a))
            self.assertEqual(compile(decompile(m)), mw)        # recompiles under the 0.5 header
        dw = compile_document([a, a])
        for h in (self.h03, self.h04):
            d = h + dw[len(self.hw):]
            self.assertEqual(decompile(d), [a, a])
            self.assertEqual(decompile(d.replace("\n", "\r\n") + "\r\n"), [a, a])
            # the document law is promised for codec-produced (0.5) documents; a decompiled
            # 0.3 or 0.4 document recompiles with the 0.5 header
            self.assertEqual(compile_document(decompile(d)), dw)
            self.assertNotEqual(compile_document(decompile(d)), d)
        # the reader does not tell the headers apart: the header names what the writer wrote
        self.assertEqual(decompile(self.h03 + " BT:RD"), decompile(self.h04 + " BT:RD"))
        self.assertEqual(decompile(self.hw + " BT:RD"), decompile(self.h04 + " BT:RD"))

    def test_0_2_needs_the_flag_and_0_3_is_not_a_flag(self):
        a = parse_L2(WORKED)
        m02 = compile(a, version="0.2")
        with self.assertRaises(IMLError) as cm:
            decompile(m02)
        self.assertEqual(cm.exception.code, "E502")
        self.assertIn("--version 0.2", cm.exception.message)
        self.assertEqual(decompile(m02, version="0.2"), a)
        for text in (self.h04 + " RD", self.h03 + " RD"):
            with self.assertRaises(IMLError) as cm:
                decompile(text, version="0.2")
            self.assertEqual(cm.exception.code, "E502")
            self.assertIn("default reader", cm.exception.message)
        with self.assertRaises(ValueError):
            decompile(self.h03 + " RD", version="0.3")
        with self.assertRaises(ValueError):
            compile(a, version="0.3")
        r = run_cli("decompile", "--version", "0.3", stdin=self.h03 + " RD\n")
        self.assertEqual(r.returncode, 2)
        self.assertIn("default reader", r.stderr)
        self.assertIn("0.3", r.stderr)
        r = run_cli("decompile", stdin=self.h03 + " RD\n" + self.h04 + " FM\n")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout.splitlines(), ["[READ]", "[FMT]"])
        r = run_cli("decompile", stdin=self.h03 + "\nRD\nFM\n")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout.splitlines(), ["[READ]", "[FMT]"])
        r = run_cli("decompile", stdin=self.h02 + " RD\n")
        self.assertEqual(r.returncode, 1)
        self.assertIn("E502", r.stderr)
        r = run_cli("compile", stdin="[READ]\n")
        self.assertEqual(r.stdout, self.hw + " RD\n")
        r = run_cli("check-registry")
        self.assertIn("header #iml/0.5/7e29fae7f5ea\n", r.stdout)
        self.assertIn("header #iml/0.4/88d05d0839c1 (read by the default reader, chains only)\n", r.stdout)
        self.assertIn("header #iml/0.3/88d05d0839c1 (read by the default reader, chains only)\n", r.stdout)
        self.assertIn("header #iml/0.2/88d05d0839c1 (read only, --version 0.2)\n", r.stdout)


class TestGolden72(unittest.TestCase):
    """The 72 chains of corpus/golden/ under 0.5: their message is the 0.3 record under the
    0.5 header (design-0.4 section 8, the header updated in 0.5)."""

    @classmethod
    def setUpClass(cls):
        cls.pairs = []
        for p in sorted(GOLDEN.glob("*.ilang")):
            src = p.read_text(encoding="utf-8").rstrip("\n")
            record03 = (GOLDEN_03 / (p.stem + ".iml")).read_text(encoding="utf-8").rstrip("\n")
            cls.pairs.append((p.stem, src, record03))
        cls.hw = default_registry().header

    def test_size(self):
        self.assertEqual(len(self.pairs), 72)

    def test_0_5_message_is_the_0_3_record_under_the_0_5_header(self):
        for stem, src, record03 in self.pairs:
            with self.subTest(stem=stem):
                self.assertTrue(record03.startswith("#iml/0.3/88d05d0839c1 "))
                self.assertEqual(compile(parse_L2(src)), "#iml/0.5/7e29fae7f5ea " + body(record03))
                self.assertEqual(decompile("#iml/0.4/88d05d0839c1 " + body(record03)), parse_L2(src))
        asts = [parse_L2(src) for _, src, _ in self.pairs]
        self.assertEqual(compile_document(asts), self.hw + "\n" + "\n".join(body(r) for _, _, r in self.pairs))

    def test_0_3_record_decompiles_under_the_default_reader_to_the_same_canonical_text(self):
        for stem, src, record03 in self.pairs:
            with self.subTest(stem=stem):
                a = parse_L2(src)
                self.assertEqual(decompile(record03), a)
                self.assertEqual(print_L2(decompile(record03)), print_L2(a))
        document03 = "#iml/0.3/88d05d0839c1\n" + "\n".join(body(r) for _, _, r in self.pairs)
        self.assertEqual([print_L2(c) for c in decompile(document03)],
                         [print_L2(parse_L2(src)) for _, src, _ in self.pairs])
        # no 0.3 record carries a verb reference: 0.4 adds it, 0.3 had none
        self.assertFalse(any(op.verbref is not None for _, _, r in self.pairs for op in decompile(r).ops))


if __name__ == "__main__":
    unittest.main()
