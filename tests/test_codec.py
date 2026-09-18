"""Golden corpus, both directions, plus coverage of the dimensions the design lists."""

import re
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from iml import Chain, IMLError, Op, Value, compile, decompile, default_registry, parse_L2, print_L2  # noqa: E402

GOLDEN = ROOT / "corpus" / "golden"
WORKED_EXAMPLE = "[READ:@GH|path=readme.md]=>[XLAT|lng=zh]=>[FMT|fmt=md]=>[Ω]"
RE_HEAD = re.compile(r"\[([^\[\]:|]+)")


def read_one_line(path):
    text = path.read_text(encoding="utf-8")
    if not text.endswith("\n") or text.count("\n") != 1:
        raise AssertionError("%s must hold exactly one line ending in LF" % path)
    return text[:-1]


def golden():
    pairs = []
    for p in sorted(GOLDEN.glob("*.ilang")):
        q = p.with_suffix(".iml")
        pairs.append((p.stem, read_one_line(p), read_one_line(q)))
    return pairs


class TestGolden(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reg = default_registry()
        cls.pairs = golden()
        cls.asts = {stem: parse_L2(src) for stem, src, _ in cls.pairs}

    def test_corpus_size_and_pairing(self):
        self.assertGreaterEqual(len(self.pairs), 60)
        ilang = {p.stem for p in GOLDEN.glob("*.ilang")}
        iml = {p.stem for p in GOLDEN.glob("*.iml")}
        self.assertEqual(ilang, iml)
        for stem in ilang:
            self.assertRegex(stem, r"^\d{3}$")

    def test_files_are_lf_utf8(self):
        for p in GOLDEN.iterdir():
            data = p.read_bytes()
            self.assertFalse(data.startswith(b"\xef\xbb\xbf"), p)
            self.assertEqual(data.count(b"\r"), 0, p)
            data.decode("utf-8")

    def test_compile_matches_expected(self):
        for stem, src, expected in self.pairs:
            with self.subTest(stem=stem):
                self.assertEqual(compile(self.asts[stem]), expected)

    def test_decompile_matches_ast(self):
        for stem, src, expected in self.pairs:
            with self.subTest(stem=stem):
                self.assertEqual(decompile(expected), self.asts[stem])

    def test_canonical_print_is_stable(self):
        for stem, src, expected in self.pairs:
            with self.subTest(stem=stem):
                canon = print_L2(self.asts[stem])
                self.assertEqual(print_L2(decompile(expected)), canon)
                self.assertEqual(print_L2(parse_L2(canon)), canon)
                self.assertNotIn(" ", canon.replace('"', "").split("|")[0])

    def test_headers(self):
        for stem, src, expected in self.pairs:
            self.assertTrue(expected.startswith(self.reg.header + " "), stem)
            self.assertEqual(expected.count("\n"), 0)

    def test_worked_example(self):
        ast = parse_L2(WORKED_EXAMPLE)
        message = compile(ast)
        self.assertTrue(message.startswith("#iml/0.2/"))
        self.assertEqual(print_L2(decompile(message)), WORKED_EXAMPLE)
        self.assertEqual(message.split(" ", 1)[1], "RDΦGHpt=readme.md→XLln=zh→FMfm=md→Ω")

    # --------------------------------------------------------------- coverage
    def test_every_verb_and_alias(self):
        verbs = {op.verb for ast in self.asts.values() for op in ast.ops}
        self.assertEqual(verbs, set(self.reg.verbs))
        spellings = {m for _, src, _ in self.pairs for m in RE_HEAD.findall(src)}
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
        raw = "\n".join(src for _, src, _ in self.pairs)
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
        # the lexeme 007 survives both directions
        for stem, src, expected in self.pairs:
            if "path=007" in src:
                self.assertIn("pt=007", expected)
                self.assertIn("path=007", print_L2(decompile(expected)))

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

    def test_entity_reference_is_distinct_from_string(self):
        ent = parse_L2("[READ|src=@PREV]")
        s = parse_L2('[READ|src="@PREV"]')
        self.assertNotEqual(ent, s)
        self.assertEqual(compile(ent).split(" ", 1)[1], "RDsr=ΦPR")
        self.assertEqual(compile(s).split(" ", 1)[1], "RDsr=@PREV")
        self.assertEqual(print_L2(s), '[READ|src="@PREV"]')
        custom = parse_L2("[READ|src=@MYDATA]")
        self.assertEqual(compile(custom).split(" ", 1)[1], "RDsr=Φ{MYDATA}")

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
            decompile(default_registry().header + " RD→ZZ")
        self.assertEqual((cm.exception.code, cm.exception.op_index), ("E304", 1))
        self.assertEqual(cm.exception.offset, len(default_registry().header) + 4)


class TestCli(unittest.TestCase):
    def run_cli(self, *args, stdin=None):
        return subprocess.run([sys.executable, "-m", "iml", *args], cwd=str(ROOT), input=stdin,
                              capture_output=True, text=True, encoding="utf-8")

    def test_compile_and_decompile_golden_file(self):
        stem, src, expected = golden()[0]
        r = self.run_cli("compile", str(GOLDEN / (stem + ".ilang")))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout.strip(), expected)
        r = self.run_cli("decompile", str(GOLDEN / (stem + ".iml")))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout.strip(), print_L2(parse_L2(src)))

    def test_stdin_and_errors(self):
        r = self.run_cli("compile", stdin=WORKED_EXAMPLE + "\n")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue(r.stdout.startswith("#iml/0.2/"))
        r = self.run_cli("compile", stdin="[REED]\n")
        self.assertEqual(r.returncode, 1)
        self.assertIn("E304", r.stderr)
        r = self.run_cli("decompile", stdin="no header\n")
        self.assertEqual(r.returncode, 1)
        self.assertIn("E502", r.stderr)

    def test_roundtrip_and_check_registry(self):
        stem, _, _ = golden()[0]
        r = self.run_cli("roundtrip", str(GOLDEN / (stem + ".ilang")))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("OK", r.stdout)
        r = self.run_cli("check-registry")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("verbs 88", r.stdout)
        self.assertIn(default_registry().digest, r.stdout)


if __name__ == "__main__":
    unittest.main()
