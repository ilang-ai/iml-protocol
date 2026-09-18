"""Malformed corpus: every case raises exactly the expected error code, with an offset."""

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from iml import IMLError, decompile, parse_L2  # noqa: E402

CASES = ROOT / "corpus" / "malformed" / "cases.json"
GOLDEN = ROOT / "corpus" / "golden"


class TestMalformed(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases = json.loads(CASES.read_text(encoding="utf-8"))

    def test_corpus_shape(self):
        self.assertGreaterEqual(len(self.cases), 40)
        seen = set()
        for c in self.cases:
            self.assertEqual(set(c) - {"label"}, {"input", "direction", "expect"})
            self.assertIn(c["direction"], ("compile", "decompile"))
            self.assertRegex(c["expect"], r"^E(200|300|302|303|304|502)$")
            self.assertNotIn((c["direction"], c["input"]), seen)
            seen.add((c["direction"], c["input"]))
        directions = {c["direction"] for c in self.cases}
        self.assertEqual(directions, {"compile", "decompile"})
        codes = {c["expect"] for c in self.cases}
        self.assertEqual(codes, {"E200", "E300", "E302", "E303", "E304", "E502"})

    def test_each_case_reports_its_code(self):
        for c in self.cases:
            with self.subTest(direction=c["direction"], input=c["input"], label=c.get("label")):
                fn = parse_L2 if c["direction"] == "compile" else decompile
                with self.assertRaises(IMLError) as cm:
                    fn(c["input"])
                err = cm.exception
                self.assertEqual(err.code, c["expect"], str(err))
                self.assertIsInstance(err.offset, int)
                self.assertGreaterEqual(err.offset, 0)
                self.assertLessEqual(err.offset, len(c["input"]))
                self.assertIn(c["expect"], str(err))

    def test_disjoint_from_golden(self):
        golden_inputs = {p.read_text(encoding="utf-8").rstrip("\n") for p in GOLDEN.iterdir()}
        for c in self.cases:
            self.assertNotIn(c["input"], golden_inputs)


if __name__ == "__main__":
    unittest.main()
