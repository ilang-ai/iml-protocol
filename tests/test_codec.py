"""Golden corpus on both surfaces, both directions, the document form, plus coverage of
the dimensions the design lists. corpus/golden/*.iml is the 0.2 record (read with
version="0.2"); corpus/golden-0.3/*.iml is what compile writes."""

import re
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from iml import (Chain, IMLError, Op, Value, compile, compile_document, decompile, default_registry,  # noqa: E402
                 is_document, parse_L2, print_L2)

GOLDEN = ROOT / "corpus" / "golden"          # .ilang sources shared by both surfaces; .iml is the 0.2 record
GOLDEN_03 = ROOT / "corpus" / "golden-0.3"   # .iml expected on the 0.3 surface
WORKED_EXAMPLE = "[READ:@GH|path=readme.md]=>[XLAT|lng=zh]=>[FMT|fmt=md]=>[Ω]"
WORKED_03 = "RD@GHpt=readme.md XLln=zh FMfm=md $"
WORKED_02 = "RDΦGHpt=readme.md→XLln=zh→FMfm=md→Ω"
RE_HEAD = re.compile(r"\[([^\[\]:|]+)")
# Chains whose value spelling differs between the surfaces (quoting is spelling, L3):
# 057 `@not_an_entity` is bare in 0.2 and quoted in 0.3; 068 `Φ` and 069 `→arrow` are
# quoted in 0.2 and bare in 0.3; 070 `Ω` is bare content on both and must not be mapped.
SPELLING_DIFFERS = {"057", "068", "069", "070"}


def read_one_line(path):
    text = path.read_text(encoding="utf-8")
    if not text.endswith("\n") or text.count("\n") != 1:
        raise AssertionError("%s must hold exactly one line ending in LF" % path)
    return text[:-1]


def golden():
    quads = []
    for p in sorted(GOLDEN.glob("*.ilang")):
        quads.append((p.stem, read_one_line(p), read_one_line(p.with_suffix(".iml")),
                      read_one_line(GOLDEN_03 / (p.stem + ".iml"))))
    return quads


def body(message):
    return message.split(" ", 1)[1]


class TestGolden(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reg = default_registry()
        cls.h03 = cls.reg.header
        cls.h02 = cls.reg.header_for("0.2")
        cls.quads = golden()
        cls.asts = {stem: parse_L2(src) for stem, src, _, _ in cls.quads}

    def test_corpus_size_and_pairing(self):
        self.assertGreaterEqual(len(self.quads), 60)
        ilang = {p.stem for p in GOLDEN.glob("*.ilang")}
        iml02 = {p.stem for p in GOLDEN.glob("*.iml")}
        iml03 = {p.stem for p in GOLDEN_03.glob("*.iml")}
        self.assertEqual(ilang, iml02)
        self.assertEqual(ilang, iml03)
        self.assertEqual({p.suffix for p in GOLDEN_03.iterdir()}, {".iml"})
        for stem in ilang:
            self.assertRegex(stem, r"^\d{3}$")

    def test_files_are_lf_utf8(self):
        for d in (GOLDEN, GOLDEN_03):
            for p in d.iterdir():
                data = p.read_bytes()
                self.assertFalse(data.startswith(b"\xef\xbb\xbf"), p)
                self.assertEqual(data.count(b"\r"), 0, p)
                data.decode("utf-8")

    def test_compile_matches_expected(self):
        for stem, src, expected02, expected03 in self.quads:
            with self.subTest(stem=stem):
                self.assertEqual(compile(self.asts[stem]), expected03)
                self.assertEqual(compile(self.asts[stem], version="0.3"), expected03)
                self.assertEqual(compile(self.asts[stem], version="0.2"), expected02)

    def test_decompile_matches_ast(self):
        for stem, src, expected02, expected03 in self.quads:
            with self.subTest(stem=stem):
                self.assertEqual(decompile(expected03), self.asts[stem])
                self.assertEqual(decompile(expected03, version="0.3"), self.asts[stem])
                self.assertEqual(decompile(expected02, version="0.2"), self.asts[stem])

    def test_0_3_golden_is_the_0_2_golden_under_the_surface_map(self):
        """Independent cross-check of the two records: outside values, 0.3 is 0.2 with
        Φ->@, Ω->$, →->space. The four chains whose value spelling differs are checked
        by their explicit forms."""
        for stem, src, expected02, expected03 in self.quads:
            with self.subTest(stem=stem):
                if stem in SPELLING_DIFFERS:
                    continue
                mapped = body(expected02).replace("Φ", "@").replace("Ω", "$").replace("→", " ")
                self.assertEqual(mapped, body(expected03))
        by_stem = {stem: (e02, e03) for stem, _, e02, e03 in self.quads}
        self.assertIn("pt=@not_an_entity", by_stem["057"][0])
        self.assertIn('pt="@not_an_entity"', by_stem["057"][1])
        self.assertIn('sb="Φ"', by_stem["068"][0])
        self.assertIn("sb=Φ", by_stem["068"][1])
        self.assertIn('pt="→arrow"', by_stem["069"][0])
        self.assertIn("pt=→arrow", by_stem["069"][1])
        self.assertIn("fm=Ω", by_stem["070"][0])
        self.assertIn("fm=Ω", by_stem["070"][1])

    def test_0_3_surface_is_ascii_outside_values(self):
        """A chain whose values are ASCII has an all-ASCII 0.3 message; the 0.2 message of
        the same chain is not ASCII (Φ, Ω or → appear in every chain)."""
        checked = 0
        for stem, src, expected02, expected03 in self.quads:
            texts = [v.text for op in self.asts[stem].ops for _, v in op.mods]
            if all(t.isascii() for t in texts):
                self.assertTrue(expected03.isascii(), stem)
                self.assertFalse(expected02.isascii(), stem)
                checked += 1
        self.assertGreaterEqual(checked, 60)

    def test_headers(self):
        for stem, src, expected02, expected03 in self.quads:
            self.assertTrue(expected03.startswith(self.h03 + " "), stem)
            self.assertTrue(expected02.startswith(self.h02 + " "), stem)
            self.assertEqual(expected03.count("\n"), 0)
            self.assertFalse(expected03.endswith(" "), stem)
        self.assertEqual(self.h03, "#iml/0.3/88d05d0839c1")
        self.assertEqual(self.h02, "#iml/0.2/88d05d0839c1")

    def test_worked_example(self):
        ast = parse_L2(WORKED_EXAMPLE)
        message = compile(ast)
        self.assertEqual(message, self.h03 + " " + WORKED_03)
        self.assertEqual(print_L2(decompile(message)), WORKED_EXAMPLE)
        message02 = compile(ast, version="0.2")
        self.assertEqual(message02, self.h02 + " " + WORKED_02)
        self.assertEqual(print_L2(decompile(message02, version="0.2")), WORKED_EXAMPLE)

    def test_document_form(self):
        order = [stem for stem, _, _, _ in self.quads]
        chains = [self.asts[stem] for stem in order]
        document = compile_document(chains)
        expected = self.h03 + "\n" + "\n".join(body(e03) for _, _, _, e03 in self.quads)
        self.assertEqual(document, expected)
        self.assertTrue(is_document(document))
        self.assertFalse(is_document(compile(chains[0])))
        self.assertEqual(decompile(document), chains)
        self.assertEqual(decompile(document + "\n"), chains)
        self.assertEqual(decompile(document.replace("\n", "\r\n")), chains)
        self.assertEqual(decompile(document.replace("\n", "\r\n") + "\r\n"), chains)
        self.assertEqual([print_L2(c) for c in decompile(document)], [print_L2(c) for c in chains])
        self.assertEqual(compile_document(decompile(document)), document)
        one = compile_document(chains[:1])
        self.assertEqual(one, self.h03 + "\n" + body(self.quads[0][3]))
        self.assertEqual(decompile(one), chains[:1])
        with self.assertRaises(IMLError) as cm:
            compile_document([])
        self.assertEqual(cm.exception.code, "E300")
        with self.assertRaises(IMLError) as cm:
            compile_document([chains[0], Chain([Op("REED")])])
        self.assertEqual(cm.exception.code, "E304")
        self.assertIn("chain 1", cm.exception.message)
        with self.assertRaises(IMLError) as cm:
            decompile(document, version="0.2")
        self.assertEqual(cm.exception.code, "E502")

    # --------------------------------------------------------------- coverage
    def test_every_verb_and_alias(self):
        verbs = {op.verb for ast in self.asts.values() for op in ast.ops}
        self.assertEqual(verbs, set(self.reg.verbs))
        spellings = {m for _, src, _, _ in self.quads for m in RE_HEAD.findall(src)}
        self.assertTrue(set(self.reg.aliases) <= spellings, set(self.reg.aliases) - spellings)
        self.assertIn("OUT", spellings)

    def test_every_key(self):
        keys = {k for ast in self.asts.values() for op in ast.ops for k, _ in op.mods}
        self.assertEqual(keys, set(self.reg.keys))

    def test_every_registered_entity_and_custom(self):
        names = set()
        for ast in self.asts.values():
            for op in ast.ops:
                if op.target:
                    names.add(op.target)
                for _, v in op.mods:
                    if v.kind == "entity":
                        names.add(v.text)
        self.assertTrue(set(self.reg.entities) <= names, set(self.reg.entities) - names)
        custom = names - set(self.reg.entities)
        self.assertTrue(custom, "no custom entity in the golden corpus")
        for c in custom:
            self.assertRegex(c, r"^[A-Z][A-Z0-9_]*$")

    def test_values(self):
        raw = "\n".join(src for _, src, _, _ in self.quads)
        self.assertIn('\\"', raw)
        self.assertIn("\\\\", raw)
        self.assertIn("\\n", raw)
        texts = [v.text for ast in self.asts.values() for op in ast.ops for _, v in op.mods if v.kind != "entity"]
        self.assertIn("007", texts)
        self.assertIn("1.0", texts)
        self.assertIn("true", texts)
        self.assertIn("false", texts)
        self.assertIn("", texts)
        entity_values = [v for ast in self.asts.values() for op in ast.ops for _, v in op.mods if v.kind == "entity"]
        self.assertTrue(entity_values)
        self.assertIn(Value("entity", "PREV"), entity_values)
        # the lexeme 007 survives both directions on both surfaces
        for stem, src, expected02, expected03 in self.quads:
            if "path=007" in src:
                self.assertIn("pt=007", expected03)
                self.assertIn("pt=007", expected02)
                self.assertIn("path=007", print_L2(decompile(expected03)))
                self.assertIn("path=007", print_L2(decompile(expected02, version="0.2")))

    def test_omega_forms_and_chain_lengths(self):
        with_mods = without = 0
        lengths = set()
        for ast in self.asts.values():
            lengths.add(len(ast.ops))
            last = ast.ops[-1]
            if last.verb == "OUT":
                if last.mods:
                    with_mods += 1
                else:
                    without += 1
        self.assertTrue(with_mods and without)
        self.assertTrue(any(ast.ops[-1].verb != "OUT" for ast in self.asts.values()))
        self.assertTrue(set(range(1, 9)) <= lengths, lengths)


class TestAst(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.h03 = default_registry().header
        cls.h02 = default_registry().header_for("0.2")

    def test_value_equality_is_kind_normalised(self):
        self.assertEqual(Value("bare", "x"), Value("quoted", "x"))
        self.assertEqual(hash(Value("bare", "x")), hash(Value("quoted", "x")))
        self.assertNotEqual(Value("bare", "PREV"), Value("entity", "PREV"))
        self.assertNotEqual(Value("bare", "x"), Value("bare", "y"))
        with self.assertRaises(ValueError):
            Value("number", "1")

    def test_quoting_is_spelling(self):
        a = parse_L2('[FMT|fmt=json]')
        b = parse_L2('[FMT|fmt="json"]')
        self.assertEqual(a, b)
        self.assertEqual(compile(a), compile(b))
        self.assertEqual(print_L2(b), "[FMT|fmt=json]")
        self.assertEqual(parse_L2("[Σ]"), parse_L2("[MERGE]"))
        self.assertEqual(parse_L2("[OUT]"), parse_L2("[Ω]"))
        self.assertEqual(print_L2(parse_L2("[OUT]")), "[Ω]")

    def test_equals_and_greater_than_are_bare_content(self):
        x = "[FILT:@SRC|whr=score>80,mch=a=1]=>[Ω]"
        a = parse_L2(x)
        self.assertEqual([v for _, v in a.ops[0].mods], [Value("bare", "score>80"), Value("bare", "a=1")])
        self.assertEqual(print_L2(a), x)
        m = compile(a)
        self.assertEqual(body(m), "FL@SRwh=score>80,mc=a=1 $")
        self.assertEqual(decompile(m), a)
        self.assertEqual(print_L2(decompile(m)), x)
        self.assertEqual(print_L2(parse_L2('[FILT|whr="a=>b"]')), "[FILT|whr=a=>b]")

    def test_print_quotes_the_reserved_characters_only(self):
        x = '[READ|path="a[b",fmt="x|y",lng="c,d",sty="e]f",ton="g\\"h",len="i\\\\j",lim="k l",typ=""]'
        self.assertEqual(print_L2(parse_L2(x)), x)
        for bad, code in (("[READ|path=a[b]", "E303"), ('[READ|path=a"b]', "E303"), ("[READ|path=a\\b]", "E303"),
                          ("[READ|path=a b]", "E300"), ("[READ|path=a|b]", "E300")):
            with self.assertRaises(IMLError) as cm:
                parse_L2(bad)
            self.assertEqual(cm.exception.code, code, bad)

    def test_dollar_at_and_the_0_2_marks_in_values(self):
        """0.3: a value may not start with `$` (E303 when read; quoted when written) or
        `@` (an entity reference); inside a value `$`, `@`, `Φ`, `Ω` and `→` are content.
        0.2: `→` is reserved anywhere and a value may not start with `Φ`."""
        x = '[FMT|fmt=$x,len=a$b,sty="@x",ton=a@b,typ=a→b,src=Φ,dst=Ω,col="a b"]'
        a = parse_L2(x)
        m = compile(a)
        self.assertEqual(body(m), 'FMfm="$x",le=a$b,st="@x",tn=a@b,ty=a→b,sr=Φ,ds=Ω,cl="a b"')
        self.assertEqual(decompile(m), a)
        self.assertEqual(print_L2(decompile(m)), x)
        m02 = compile(a, version="0.2")
        self.assertEqual(body(m02), 'FMfm=$x,le=a$b,st=@x,tn=a@b,ty="a→b",sr="Φ",ds=Ω,cl="a b"')
        self.assertEqual(decompile(m02, version="0.2"), a)
        with self.assertRaises(IMLError) as cm:
            decompile(self.h03 + " FMfm=$x")
        self.assertEqual(cm.exception.code, "E303")
        self.assertEqual(decompile(self.h03 + " FMfm=a$b").ops[0].mods[0][1], Value("bare", "a$b"))
        self.assertEqual(decompile(self.h02 + " FMfm=$x", version="0.2").ops[0].mods[0][1], Value("bare", "$x"))
        for text, code in ((self.h03 + " RDΦGH", "E300"), (self.h03 + " Ω", "E300"), (self.h03 + " RD→XL", "E300"),
                           (self.h03 + " RD@GH→$", "E300"), (self.h02 + " RD@GH", "E300"), (self.h02 + " RD $", "E300")):
            with self.assertRaises(IMLError) as cm:
                decompile(text, version="0.3" if text.startswith("#iml/0.3/") else "0.2")
            self.assertEqual(cm.exception.code, code, text)

    def test_space_is_the_separator_and_quotes_protect_it(self):
        a = parse_L2('[READ:@SRC|path="a b",whr="x, y"]=>[FMT|fmt="c d"]=>[Ω|fmt=json]')
        m = compile(a)
        self.assertEqual(body(m), 'RD@SRpt="a b",wh="x, y" FMfm="c d" $fm=json')
        self.assertEqual(decompile(m), a)
        self.assertEqual(len(decompile(m).ops), 3)
        d = compile_document([a, a])
        self.assertEqual(decompile(d), [a, a])
        for text in (self.h03 + " RD ", self.h03 + " RD  FM", self.h03 + " RD\tFM", self.h03 + " RDpt=a b",
                     self.h03 + " RDpt=a, FM", self.h03 + " RD pt=a", self.h03 + "\nRD \nFM"):
            with self.assertRaises(IMLError) as cm:
                decompile(text)
            self.assertEqual(cm.exception.code, "E300", text)

    def test_raw_control_characters_inside_quotes(self):
        for ch in ("\x00", "\t", "\n", "\x1f", "\x7f", " ", " "):
            with self.assertRaises(IMLError) as cm:
                parse_L2('[READ|path="a%sb"]' % ch)
            self.assertEqual(cm.exception.code, "E300", repr(ch))
            with self.assertRaises(IMLError) as cm:
                decompile(self.h03 + ' RDpt="a%sb"' % ch)
            self.assertEqual(cm.exception.code, "E300", repr(ch))
            with self.assertRaises(IMLError) as cm:
                decompile(self.h02 + ' RDpt="a%sb"' % ch, version="0.2")
            self.assertEqual(cm.exception.code, "E300", repr(ch))
        a = parse_L2('[READ|path="a\\nb"]')
        self.assertEqual(a.ops[0].mods[0][1].text, "a\nb")
        self.assertEqual(print_L2(a), '[READ|path="a\\nb"]')
        self.assertEqual(body(compile(a)), 'RDpt="a\\nb"')

    def test_header_shape_before_version_and_digest(self):
        h = self.h03
        for text, code in (("RD", "E502"), ("RD@GH", "E502"), ("#iml/3/88d05d0839c1 RD", "E300"),
                           ("#iml/0.2/88D05D0839C1 RD", "E300"), ("#iml/0.2/88d05d0839c1 RD", "E502"),
                           ("#iml/0.2/88d05d0839c1\nRD", "E502"), ("#iml/0.3/000000000000 RD", "E502"),
                           ("#iml/0.3/000000000000\nRD", "E502"), (h + "RD", "E300"), (h + "  RD", "E300"),
                           (h, "E300"), (h + "\n", "E300"), (h + "\r\n", "E300"), (h + " ", "E300")):
            with self.assertRaises(IMLError) as cm:
                decompile(text)
            self.assertEqual(cm.exception.code, code, text)
        h = self.h02
        for text, code in (("RD", "E502"), ("#iml/2/88d05d0839c1 RD", "E300"), ("#iml/0.1/88D05D0839C1 RD", "E300"),
                           ("#iml/0.1/88d05d0839c1 RD", "E502"), ("#iml/0.3/88d05d0839c1 RD", "E502"),
                           ("#iml/0.2/000000000000 RD", "E502"), (h + "RD", "E300"), (h + "  RD", "E300"),
                           (h, "E300"), (h + "\nRD", "E300")):
            with self.assertRaises(IMLError) as cm:
                decompile(text, version="0.2")
            self.assertEqual(cm.exception.code, code, text)

    def test_the_0_2_surface_is_read_only(self):
        a = parse_L2(WORKED_EXAMPLE)
        m03, m02 = compile(a), compile(a, version="0.2")
        with self.assertRaises(IMLError) as cm:
            decompile(m02)
        self.assertEqual(cm.exception.code, "E502")
        self.assertIn("--version 0.2", cm.exception.message)
        with self.assertRaises(IMLError) as cm:
            decompile(m03, version="0.2")
        self.assertEqual(cm.exception.code, "E502")
        self.assertEqual(decompile(m02, version="0.2"), decompile(m03))
        with self.assertRaises(ValueError):
            compile(a, version="0.4")
        with self.assertRaises(ValueError):
            decompile(m03, version="0.1")

    def test_entity_reference_is_distinct_from_string(self):
        ent = parse_L2("[READ|src=@PREV]")
        s = parse_L2('[READ|src="@PREV"]')
        self.assertNotEqual(ent, s)
        self.assertEqual(body(compile(ent)), "RDsr=@PR")
        self.assertEqual(body(compile(s)), 'RDsr="@PREV"')
        self.assertEqual(body(compile(ent, version="0.2")), "RDsr=ΦPR")
        self.assertEqual(body(compile(s, version="0.2")), "RDsr=@PREV")
        self.assertEqual(print_L2(s), '[READ|src="@PREV"]')
        self.assertEqual(decompile(compile(s)), s)
        self.assertNotEqual(decompile(compile(s)), ent)
        custom = parse_L2("[READ|src=@MYDATA]")
        self.assertEqual(body(compile(custom)), "RDsr=@{MYDATA}")
        self.assertEqual(body(compile(custom, version="0.2")), "RDsr=Φ{MYDATA}")

    def test_compile_validates_hand_built_ast(self):
        with self.assertRaises(IMLError) as cm:
            compile(Chain([Op("REED")]))
        self.assertEqual(cm.exception.code, "E304")
        self.assertEqual(cm.exception.op_index, 0)
        with self.assertRaises(IMLError) as cm:
            compile(Chain([Op("READ", None, [("nope", Value("bare", "x"))])]))
        self.assertEqual(cm.exception.code, "E302")
        with self.assertRaises(IMLError) as cm:
            compile(Chain([Op("READ", "bad")]))
        self.assertEqual(cm.exception.code, "E200")
        with self.assertRaises(IMLError) as cm:
            compile(Chain([Op("OUT"), Op("READ")]))
        self.assertEqual(cm.exception.code, "E502")
        self.assertEqual(cm.exception.op_index, 0)
        with self.assertRaises(IMLError) as cm:
            compile(Chain([Op("READ", None, [("fmt", Value("code", "js"))])]))
        self.assertEqual(cm.exception.code, "E303")
        with self.assertRaises(IMLError) as cm:
            compile(Chain([]))
        self.assertEqual(cm.exception.code, "E300")

    def test_errors_carry_offsets(self):
        with self.assertRaises(IMLError) as cm:
            parse_L2("[READ|pth=x]")
        self.assertEqual((cm.exception.code, cm.exception.offset, cm.exception.op_index), ("E302", 6, 0))
        with self.assertRaises(IMLError) as cm:
            decompile(self.h03 + " RD ZZ")
        self.assertEqual((cm.exception.code, cm.exception.op_index), ("E304", 1))
        self.assertEqual(cm.exception.offset, len(self.h03) + 4)
        with self.assertRaises(IMLError) as cm:
            decompile(self.h02 + " RD→ZZ", version="0.2")
        self.assertEqual((cm.exception.code, cm.exception.op_index), ("E304", 1))
        self.assertEqual(cm.exception.offset, len(self.h02) + 4)
        # in a document the offset is into the whole text and the op index restarts per line
        with self.assertRaises(IMLError) as cm:
            decompile(self.h03 + "\nRD\nFM ZZ")
        self.assertEqual((cm.exception.code, cm.exception.op_index), ("E304", 1))
        self.assertEqual(cm.exception.offset, len(self.h03) + 1 + 3 + 3)
        with self.assertRaises(IMLError) as cm:
            decompile(self.h03 + "\nRD\n\nFM")
        self.assertEqual((cm.exception.code, cm.exception.offset), ("E300", len(self.h03) + 4))
        with self.assertRaises(IMLError) as cm:
            decompile(self.h03 + "\nRD\n" + self.h03)
        self.assertEqual((cm.exception.code, cm.exception.offset), ("E502", len(self.h03) + 4))


class TestCli(unittest.TestCase):
    def run_cli(self, *args, stdin=None):
        # bytes in and out: the text layer would translate newlines (on Windows the CRLF
        # case below would arrive as CR CR LF); stdout and stderr are decoded here
        r = subprocess.run([sys.executable, "-m", "iml", *args], cwd=str(ROOT),
                           input=None if stdin is None else stdin.encode("utf-8"), capture_output=True)
        r.stdout = r.stdout.decode("utf-8").replace("\r\n", "\n")
        r.stderr = r.stderr.decode("utf-8").replace("\r\n", "\n")
        return r

    def test_compile_and_decompile_golden_file(self):
        stem, src, expected02, expected03 = golden()[0]
        r = self.run_cli("compile", str(GOLDEN / (stem + ".ilang")))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout.strip(), expected03)
        r = self.run_cli("decompile", str(GOLDEN_03 / (stem + ".iml")))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout.strip(), print_L2(parse_L2(src)))
        r = self.run_cli("decompile", "--version", "0.2", str(GOLDEN / (stem + ".iml")))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout.strip(), print_L2(parse_L2(src)))
        r = self.run_cli("decompile", str(GOLDEN / (stem + ".iml")))
        self.assertEqual(r.returncode, 1)
        self.assertIn("E502", r.stderr)
        self.assertIn("--version 0.2", r.stderr)

    def test_stdin_and_errors(self):
        r = self.run_cli("compile", stdin=WORKED_EXAMPLE + "\n")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue(r.stdout.startswith("#iml/0.3/"))
        r = self.run_cli("compile", stdin="[REED]\n")
        self.assertEqual(r.returncode, 1)
        self.assertIn("E304", r.stderr)
        r = self.run_cli("decompile", stdin="no header\n")
        self.assertEqual(r.returncode, 1)
        self.assertIn("E502", r.stderr)
        r = self.run_cli("decompile", "--version", "0.4", stdin="")
        self.assertEqual(r.returncode, 2)
        r = self.run_cli("compile", "--version", "0.2", stdin="")
        self.assertEqual(r.returncode, 2)
        r = self.run_cli("decompile", "--document", stdin="")
        self.assertEqual(r.returncode, 2)

    def test_document_on_the_command_line(self):
        quads = golden()[:3]
        ilang = "".join(src + "\n" for _, src, _, _ in quads)
        r = self.run_cli("compile", "--document", stdin=ilang)
        self.assertEqual(r.returncode, 0, r.stderr)
        lines = r.stdout.splitlines()
        self.assertEqual(lines[0], default_registry().header)
        self.assertEqual(lines[1:], [body(e03) for _, _, _, e03 in quads])
        r = self.run_cli("decompile", stdin=r.stdout)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout.splitlines(), [print_L2(parse_L2(src)) for _, src, _, _ in quads])
        # a stream of messages, blank lines skipped, is still read one message per line
        r = self.run_cli("decompile", stdin="\n".join(e03 for _, _, _, e03 in quads) + "\n\n")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(len(r.stdout.splitlines()), 3)
        # inside a document a blank line is an error, reported with its line number
        broken = "\n".join(lines[:2] + [""] + lines[2:]) + "\n"
        r = self.run_cli("decompile", stdin=broken)
        self.assertEqual(r.returncode, 1)
        self.assertIn("<stdin>:3: E300", r.stderr)
        r = self.run_cli("decompile", stdin="\r\n".join(lines) + "\r\n")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(len(r.stdout.splitlines()), 3)

    def test_roundtrip_and_check_registry(self):
        stem, _, _, _ = golden()[0]
        r = self.run_cli("roundtrip", str(GOLDEN / (stem + ".ilang")))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("OK", r.stdout)
        self.assertIn("document OK", r.stdout)
        self.assertIn("#iml/0.3/", r.stdout)
        r = self.run_cli("check-registry")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("verbs 88", r.stdout)
        self.assertIn(default_registry().digest, r.stdout)
        self.assertIn("header #iml/0.3/88d05d0839c1", r.stdout)
        self.assertIn("header #iml/0.2/88d05d0839c1 (read only)", r.stdout)


if __name__ == "__main__":
    unittest.main()
