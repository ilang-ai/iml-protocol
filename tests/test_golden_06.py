"""corpus/golden-0.6/: I-Lang documents with their IML 0.6 documents. 0.6 adds one registered declaration, ::EXCLUDE
(the canon's 5.0.11 amendment), and a new registry file; this corpus holds the documents that use it. The 0.5 corpus
stays as the record of 0.5 and is read with the frozen 0.5 registry (tests/test_golden_05.py)."""

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

from iml import Decl, IMLError, compile_doc, decompile, decompile_doc, default_registry, parse_doc, print_doc  # noqa: E402
from validator_oracle import lint  # noqa: E402

GOLDEN_06 = ROOT / "corpus" / "golden-0.6"


def read_lf(path):
    data = path.read_bytes()
    if data.startswith(b"\xef\xbb\xbf") or b"\r" in data or not data.endswith(b"\n"):
        raise AssertionError("%s must be UTF-8 without BOM, LF only, ending in LF" % path)
    return data.decode("utf-8")


class TestGolden06(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reg = default_registry()
        cls.docs = [(p.stem, read_lf(p), read_lf(p.with_suffix(".iml"))) for p in sorted(GOLDEN_06.glob("*.ilang"))]
        cls.asts = {stem: parse_doc(src) for stem, src, _ in cls.docs}

    def test_pairing_and_hygiene(self):
        stems = {p.stem for p in GOLDEN_06.glob("*.ilang")}
        self.assertGreaterEqual(len(stems), 1)
        self.assertEqual({p.name for p in GOLDEN_06.iterdir()}, {s + e for s in stems for e in (".ilang", ".iml")})
        for stem, src, iml in self.docs:
            self.assertTrue(src.startswith("::ILANG::"), stem)
            self.assertTrue(iml.startswith(self.reg.header + "\n"), stem)
            self.assertTrue(iml.startswith("#iml/0.6/"), stem)

    def test_compile_matches_the_record_and_the_laws_hold(self):
        for stem, src, iml in self.docs:
            with self.subTest(stem=stem):
                items = self.asts[stem]
                m = iml[:-1]
                printed = print_doc(items)
                self.assertEqual(compile_doc(items), m)
                self.assertEqual(decompile_doc(m), items)                     # L1
                self.assertEqual(decompile(m), items)
                self.assertEqual(print_doc(parse_doc(printed)), printed)       # L2
                self.assertEqual(compile_doc(decompile_doc(m)), m)             # L2
                raw, errors = lint(src)
                self.assertTrue(raw)
                self.assertEqual(errors, [], stem)

    def test_exclude_is_coded_and_refused_by_the_0_5_registry(self):
        for stem, src, iml in self.docs:
            items = self.asts[stem]
            excl = [d for d in items if isinstance(d, Decl) and d.name == "EXCLUDE"]
            self.assertTrue(excl, stem)
            self.assertIn(':EX"', iml)
            self.assertEqual(self.reg.decl_code["EXCLUDE"], "EX")
            prev = self.reg.for_version("0.5")
            self.assertNotIn("EXCLUDE", prev.declarations)
            with self.assertRaises(IMLError) as cm:
                compile_doc(items, registry=prev)
            self.assertEqual(cm.exception.code, "E300")
            # the same text under a 0.5 header is read with the 0.5 tables, which have no EX
            with self.assertRaises(IMLError):
                decompile(prev.header + iml[len(self.reg.header):-1])


if __name__ == "__main__":
    unittest.main()
