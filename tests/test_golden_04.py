"""corpus/golden-0.4/: the 0.4 pairs (NNN.ilang, a source that may span several lines,
and NNN.iml, the one-line 0.4 message) and the document pair doc-01; hygiene, the four
laws, coverage of the design list (design-0.4 section 8), the command line, and the
canon validator as the legality oracle on the canonical prints and on the sources as
written (continuation lines included)."""

import re
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

from iml import compile, compile_document, decompile, default_registry, is_document, parse_L2, print_L2  # noqa: E402
from iml.__main__ import join_chain_lines  # noqa: E402
from test_roundtrip import run_validator  # noqa: E402

GOLDEN_04 = ROOT / "corpus" / "golden-0.4"
WORKFLOW_10_7 = (
    "[CREA:@LOCAL|path=auth/login.go]\n  =>[TEST]\n  =>[REVW]\n  =>[Ω]",
    "[CREA:@LOCAL|path=auth/register.go]\n  =>[TEST]\n  =>[REVW]\n  =>[Ω]",
    "[DPLO:@WORKER]\n  =>[CHEK|whr=status:200]\n  =>[Ω]",
    "[PLAN:@SRC|len=5-15]=>[Ω]",
)
DESIGN_LIST = ("[Π:READ]", "[BATC:READ]", "[BATC:READ|src=@LOCAL,mch=*.md]", "[Π:Σ]", "[BATC:READ|op=FMT]",
               "[BATC|op=READ]", "[BATC:@SRC|op=SCAN]", "[LOOP|whr=until:done]", "[WAIT|whr=status:ready]",
               "[CHEK|whr=status:200]", "[LOOP:@LIST|op=READ]", "[BATC:READ|whr=lvl:fatal]", 'path="a b"',
               'path="say \\"hi\\""', 'exc="a\\\\b"', 'sty="line\\nbreak"', "\n  =>[Π:READ]\n")


def read_lf(path):
    data = path.read_bytes()
    if data.startswith(b"\xef\xbb\xbf") or b"\r" in data or not data.endswith(b"\n"):
        raise AssertionError("%s must be UTF-8 without BOM, LF only, ending in LF" % path)
    return data.decode("utf-8")


def run_cli(*args, stdin=None):
    r = subprocess.run([sys.executable, "-m", "iml", *args], cwd=str(ROOT),
                       input=None if stdin is None else stdin.encode("utf-8"), capture_output=True)
    r.stdout = r.stdout.decode("utf-8").replace("\r\n", "\n")
    r.stderr = r.stderr.decode("utf-8").replace("\r\n", "\n")
    return r


class TestGolden04(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reg = default_registry()
        cls.h = cls.reg.header
        cls.items = []   # (stem, source text, message text), both with their final LF
        for p in sorted(GOLDEN_04.glob("[0-9][0-9][0-9].ilang")):
            cls.items.append((p.stem, read_lf(p), read_lf(p.with_suffix(".iml"))))
        cls.asts = {}
        for stem, src, iml in cls.items:
            (no, text), = join_chain_lines(src)
            assert no == 1, stem
            cls.asts[stem] = parse_L2(text)

    def test_pairing_and_hygiene(self):
        names = {p.name for p in GOLDEN_04.iterdir()}
        stems = {p.stem for p in GOLDEN_04.glob("[0-9][0-9][0-9].ilang")}
        self.assertGreaterEqual(len(stems), 24)
        self.assertEqual(names, {s + ".ilang" for s in stems} | {s + ".iml" for s in stems} | {"doc-01.ilang", "doc-01.iml"})
        self.assertEqual(stems, {"%03d" % k for k in range(1, len(stems) + 1)})
        for stem, src, iml in self.items:
            self.assertEqual(iml.count("\n"), 1, stem)          # the message is one line
            self.assertTrue(iml.startswith(self.h + " "), stem)
            self.assertFalse(iml.endswith(" \n"), stem)
        for p in GOLDEN_04.iterdir():
            read_lf(p)

    def test_compile_decompile_and_the_four_laws(self):
        for stem, src, iml in self.items:
            with self.subTest(stem=stem):
                a = self.asts[stem]
                m = iml[:-1]
                canon = print_L2(a)
                self.assertEqual(compile(a), m)
                self.assertEqual(decompile(m), a)                          # L1
                self.assertEqual(print_L2(parse_L2(canon)), canon)         # L2a
                self.assertEqual(compile(decompile(m)), m)                 # L2b
                self.assertEqual(print_L2(decompile(m)), canon)            # L2c
                self.assertNotIn("\n", canon)
                # the same text under a 0.3 header reads the same (the header names the writer)
                self.assertEqual(decompile("#iml/0.3/" + m[len("#iml/0.4/"):]), a)

    def test_multi_line_sources(self):
        multi = [(stem, src) for stem, src, _ in self.items if "\n" in src.rstrip("\n")]
        self.assertGreaterEqual(len(multi), 5)
        for stem, src in multi:
            lines = src.rstrip("\n").split("\n")
            self.assertTrue(lines[0].startswith("["), stem)
            for line in lines[1:]:
                self.assertTrue(line.startswith("  =>["), (stem, line))    # two-space indent, SPEC.md section 10 layout
            one_line = "".join(line.strip() for line in lines)
            self.assertEqual(parse_L2(one_line), self.asts[stem])
            self.assertEqual(compile(parse_L2(one_line)), compile(self.asts[stem]))
            self.assertEqual(print_L2(self.asts[stem]), print_L2(parse_L2(one_line)))
        sources = {src.rstrip("\n") for _, src, _ in self.items}
        for chain in WORKFLOW_10_7:
            self.assertIn(chain, sources)

    def test_coverage_of_the_design_list(self):
        raw = "\n".join(src for _, src, _ in self.items)
        for needle in DESIGN_LIST:
            self.assertIn(needle, raw, needle)
        asts = list(self.asts.values())
        refs = [op.verbref for a in asts for op in a.ops if op.verbref is not None]
        self.assertGreaterEqual(len(refs), 24)
        for verb in ("READ", "MERGE", "BATC", "LOOP", "WAIT", "NOOP", "FMT", "CNT", "XLAT", "PARS", "VALD"):
            self.assertIn(verb, refs, verb)
        # every alias but Ω and Π is used as a reference spelling and collapses to its verb;
        # Π is used as the verb spelling of BATC
        spellings = set(re.findall(r"\[(?:Π|BATC):([^\]|@]+)", raw))
        for alias, verb in self.reg.aliases.items():
            if verb in ("OUT", "BATC"):
                continue
            self.assertIn(alias, spellings, alias)
            self.assertIn(verb, refs, verb)
        self.assertIn("[Π:", raw)
        self.assertIn("[BATC:BATC]", raw)
        # custom entities, entity references, quoted values and `:` values next to a verb reference
        customs = {op.target for a in asts for op in a.ops if op.target and op.target not in self.reg.entities}
        self.assertTrue({"LIST", "REPORT_2026", "SPEC"} <= customs, customs)
        self.assertTrue(any(v.kind == "entity" and v.text == "MYDATA" for a in asts for op in a.ops for _, v in op.mods))
        self.assertTrue(any(v.kind == "entity" and v.text == "PREV" for a in asts for op in a.ops for _, v in op.mods))
        self.assertTrue(any(op.verbref and any(v.kind == "quoted" for _, v in op.mods) for a in asts for op in a.ops))
        self.assertTrue(any(op.verbref and any(":" in v.text for _, v in op.mods) for a in asts for op in a.ops))
        self.assertTrue(any(op.verbref and op.mods and op.mods[0][0] == "op" for a in asts for op in a.ops))
        self.assertTrue(any(op.verb == "BATC" and op.target == "SRC" for a in asts for op in a.ops))
        self.assertTrue(any(op.verb == "BATC" and op.verbref is None and op.target is None for a in asts for op in a.ops))
        lengths = {len(a.ops) for a in asts}
        self.assertIn(1, lengths)
        self.assertIn(8, lengths)
        self.assertTrue(any(a.ops[-1].verb != "OUT" for a in asts))
        self.assertTrue(any(a.ops[-1].verb == "OUT" and a.ops[-1].mods for a in asts))
        self.assertTrue(any(a.ops[0].verbref is not None for a in asts))       # a reference as the first op
        self.assertTrue(any(a.ops[-1].verbref is not None for a in asts))      # and as the last op

    def test_document_pair(self):
        src = read_lf(GOLDEN_04 / "doc-01.ilang")
        iml = read_lf(GOLDEN_04 / "doc-01.iml")
        chains = join_chain_lines(src)
        self.assertEqual([no for no, _ in chains], [1, 3, 7, 12, 16])
        asts = [parse_L2(t) for _, t in chains]
        self.assertEqual(len(asts), 5)
        self.assertIn("\n\n", src)
        self.assertIn("\n  =>[", src)
        self.assertEqual(compile_document(asts) + "\n", iml)
        self.assertEqual(decompile(iml), asts)
        self.assertEqual(decompile(iml[:-1]), asts)
        self.assertTrue(is_document(iml))
        self.assertEqual(iml.split("\n")[0], self.h)
        self.assertEqual(iml.count("\n"), 6)
        self.assertEqual(compile_document(decompile(iml)), iml[:-1])
        self.assertTrue(any(op.verbref for a in asts for op in a.ops))
        # the same five chains, each on one line, compile to the same document
        one_line = "\n".join(print_L2(a) for a in asts) + "\n"
        self.assertEqual(compile_document([parse_L2(t) for _, t in join_chain_lines(one_line)]) + "\n", iml)

    def test_cli(self):
        stem, src, iml = self.items[15]
        self.assertEqual(stem, "016")
        self.assertIn("\n  =>", src)
        r = run_cli("compile", str(GOLDEN_04 / (stem + ".ilang")))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout, iml)
        r = run_cli("decompile", str(GOLDEN_04 / (stem + ".iml")))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout, print_L2(self.asts[stem]) + "\n")
        r = run_cli("compile", "--document", str(GOLDEN_04 / "doc-01.ilang"))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout, read_lf(GOLDEN_04 / "doc-01.iml"))
        r = run_cli("decompile", str(GOLDEN_04 / "doc-01.iml"))
        self.assertEqual(r.returncode, 0, r.stderr)
        expected = [print_L2(parse_L2(t)) for _, t in join_chain_lines(read_lf(GOLDEN_04 / "doc-01.ilang"))]
        self.assertEqual(r.stdout.splitlines(), expected)
        r = run_cli("roundtrip", str(GOLDEN_04 / "doc-01.ilang"))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("document OK (5 chains under one header, 6 lines)", r.stdout)
        self.assertIn("5 chain(s), 0 failure(s)", r.stdout)

    def test_canon_validator_accepts_prints_and_sources(self):
        prints = [print_L2(a) for a in self.asts.values()]
        rep = run_validator(prints)
        errors = [f for f in rep["findings"] if f["level"] == "ERROR"]
        self.assertEqual(rep["mode"], "raw")
        self.assertEqual(errors, [], errors[:5])
        # the sources as written (continuation lines: the validator's B8 rule), doc-01 included
        lines = []
        for _, src, _ in self.items:
            lines.extend(src.rstrip("\n").split("\n"))
        lines.extend(read_lf(GOLDEN_04 / "doc-01.ilang").rstrip("\n").split("\n"))
        rep_src = run_validator(lines)
        errors = [f for f in rep_src["findings"] if f["level"] == "ERROR"]
        self.assertEqual(rep_src["mode"], "raw")
        self.assertEqual(errors, [], errors[:5])
        print("\nvalidator on golden-0.4: %d prints (%d error(s), %d warning(s)); %d source lines (%d error(s), %d warning(s))"
              % (len(prints), rep["errors"], rep["warnings"], len(lines), rep_src["errors"], rep_src["warnings"]))


if __name__ == "__main__":
    unittest.main()
