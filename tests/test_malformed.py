"""Malformed corpus: every case raises exactly the expected error code, with an offset.
A decompile case names the surface it is read on (`version` 0.3 or 0.2); a compile case
is I-Lang input, the same on both surfaces."""

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from iml import VERSIONS, IMLError, decompile, parse_L2  # noqa: E402

CASES = ROOT / "corpus" / "malformed" / "cases.json"
GOLDEN = ROOT / "corpus" / "golden"
GOLDEN_03 = ROOT / "corpus" / "golden-0.3"


class TestMalformed(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases = json.loads(CASES.read_text(encoding="utf-8"))

    def test_corpus_shape(self):
        self.assertGreaterEqual(len(self.cases), 40)
        seen = set()
        for c in self.cases:
            self.assertIn(c["direction"], ("compile", "decompile"))
            if c["direction"] == "compile":
                self.assertEqual(set(c) - {"label"}, {"input", "direction", "expect"})
            else:
                self.assertEqual(set(c) - {"label"}, {"input", "direction", "expect", "version"})
                self.assertIn(c["version"], VERSIONS)
            self.assertRegex(c["expect"], r"^E(200|300|302|303|304|502)$")
            key = (c["direction"], c.get("version"), c["input"])
            self.assertNotIn(key, seen)
            seen.add(key)
        directions = {c["direction"] for c in self.cases}
        self.assertEqual(directions, {"compile", "decompile"})
        versions = {c["version"] for c in self.cases if c["direction"] == "decompile"}
        self.assertEqual(versions, set(VERSIONS))
        codes = {c["expect"] for c in self.cases}
        self.assertEqual(codes, {"E200", "E300", "E302", "E303", "E304", "E502"})
        codes_03 = {c["expect"] for c in self.cases if c.get("version") == "0.3"}
        self.assertEqual(codes_03, {"E200", "E300", "E302", "E303", "E304", "E502"})

    def test_each_case_reports_its_code(self):
        for c in self.cases:
            with self.subTest(direction=c["direction"], version=c.get("version"), input=c["input"], label=c.get("label")):
                if c["direction"] == "compile":
                    fn = parse_L2
                else:
                    fn = lambda text, v=c["version"]: decompile(text, version=v)  # noqa: E731
                with self.assertRaises(IMLError) as cm:
                    fn(c["input"])
                err = cm.exception
                self.assertEqual(err.code, c["expect"], str(err))
                self.assertIsInstance(err.offset, int)
                self.assertGreaterEqual(err.offset, 0)
                self.assertLessEqual(err.offset, len(c["input"]))
                self.assertIn(c["expect"], str(err))

    def test_0_3_cases_cover_the_design_list(self):
        """SPEC-IML-0.3.md section 6: version mismatch both ways, blank line in a document,
        second header, `$` at value start, trailing space, the 0.2 marks in a 0.3 message."""
        d03 = [c for c in self.cases if c.get("version") == "0.3"]
        d02 = [c for c in self.cases if c.get("version") == "0.2"]
        self.assertTrue(any(c["input"].startswith("#iml/0.2/") and c["expect"] == "E502" for c in d03))
        self.assertTrue(any(c["input"].startswith("#iml/0.3/") and c["expect"] == "E502" for c in d02))
        self.assertTrue(any("\n\n" in c["input"] and c["expect"] == "E300" for c in d03))
        self.assertTrue(any(c["input"].count("#iml/") == 2 and c["expect"] == "E502" for c in d03))
        self.assertTrue(any("=$" in c["input"] and c["expect"] == "E303" for c in d03))
        self.assertTrue(any(c["input"].endswith(" ") and c["expect"] == "E300" for c in d03))
        self.assertTrue(any(" \n" in c["input"] and c["expect"] == "E300" for c in d03))
        for mark in ("Φ", "Ω", "→"):
            self.assertTrue(any(mark in c["input"] and c["expect"] == "E300" for c in d03), mark)
        self.assertTrue(any("\n" in c["input"] and c["input"].count("#iml/") == 1 and c["expect"] == "E300"
                            and "\n\n" not in c["input"] for c in d03))

    def test_disjoint_from_golden(self):
        golden_inputs = {p.read_text(encoding="utf-8").rstrip("\n") for d in (GOLDEN, GOLDEN_03) for p in d.iterdir()}
        for c in self.cases:
            self.assertNotIn(c["input"], golden_inputs)


if __name__ == "__main__":
    unittest.main()
