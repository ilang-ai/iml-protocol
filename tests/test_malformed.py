"""Malformed corpus: every case raises exactly the expected error code, with an offset.
A decompile case names the header version its input carries and the reader that reads
it: `version` 0.4 and 0.3 are both read by the default reader (one reader, two accepted
headers), 0.2 by the 0.2 reader (version="0.2"). A compile case is I-Lang input, the
same on every surface."""

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from iml import DEFAULT_VERSION, VERSIONS, IMLError, decompile, parse_L2  # noqa: E402

CASES = ROOT / "corpus" / "malformed" / "cases.json"
GOLDEN = ROOT / "corpus" / "golden"
GOLDEN_03 = ROOT / "corpus" / "golden-0.3"
GOLDEN_04 = ROOT / "corpus" / "golden-0.4"
CASE_VERSIONS = ("0.4", "0.3", "0.2")
READER = {"0.4": DEFAULT_VERSION, "0.3": DEFAULT_VERSION, "0.2": "0.2"}
H04 = "#iml/0.4/88d05d0839c1 "


def reader_for(case):
    return READER[case["version"]]


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
                self.assertIn(c["version"], CASE_VERSIONS)
                self.assertIn(reader_for(c), VERSIONS)
            self.assertRegex(c["expect"], r"^E(200|300|302|303|304|502)$")
            key = (c["direction"], c.get("version"), c["input"])
            self.assertNotIn(key, seen)
            seen.add(key)
        directions = {c["direction"] for c in self.cases}
        self.assertEqual(directions, {"compile", "decompile"})
        versions = {c["version"] for c in self.cases if c["direction"] == "decompile"}
        self.assertEqual(versions, set(CASE_VERSIONS))
        codes = {c["expect"] for c in self.cases}
        self.assertEqual(codes, {"E200", "E300", "E302", "E303", "E304", "E502"})
        codes_03 = {c["expect"] for c in self.cases if c.get("version") == "0.3"}
        self.assertEqual(codes_03, {"E200", "E300", "E302", "E303", "E304", "E502"})
        codes_04 = {c["expect"] for c in self.cases if c.get("version") == "0.4"}
        self.assertEqual(codes_04, {"E300", "E304", "E502"})

    def test_each_case_reports_its_code(self):
        for c in self.cases:
            with self.subTest(direction=c["direction"], version=c.get("version"), input=c["input"], label=c.get("label")):
                if c["direction"] == "compile":
                    fn = parse_L2
                else:
                    fn = lambda text, v=reader_for(c): decompile(text, version=v)  # noqa: E731
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
        second header, `$` at value start, trailing space, the 0.2 marks in a 0.3 message.
        The 0.3 inputs are read by the default (0.4) reader and keep their codes."""
        d03 = [c for c in self.cases if c.get("version") == "0.3"]
        d02 = [c for c in self.cases if c.get("version") == "0.2"]
        self.assertGreaterEqual(len(d03), 40)
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

    def test_0_4_cases_cover_the_design_list(self):
        """design-0.4 section 8: the IML side of the verb reference, a 0.2 header on the
        0.4 reader, and on the I-Lang side the unknown, lower-case and OUT references, a
        reference on another verb, the empty reference, and two chains on one line."""
        d04 = {c["input"]: c["expect"] for c in self.cases if c.get("version") == "0.4"}
        self.assertGreaterEqual(len(d04), 14)
        for tail, code in (("BT:", "E300"), ("BT:R", "E300"), ("BT:rd", "E300"), ("BT:XX", "E304"), ("RD:FM", "E300"),
                           ("BT:RD@SR", "E300"), ("BT:$", "E300"), ("BT: RD", "E300"), ("BT:@SR", "E300"), ("$:RD", "E300")):
            self.assertEqual(d04.get(H04 + tail), code, tail)
        self.assertEqual(d04.get("#iml/0.2/88d05d0839c1 RD"), "E502")
        self.assertTrue(any("\n" in inp and code == "E300" for inp, code in d04.items()))
        compile_cases = {c["input"]: c["expect"] for c in self.cases if c["direction"] == "compile"}
        for src, code in (("[BATC:REED]", "E304"), ("[BATC:read]", "E304"), ("[Π:Ω]", "E502"), ("[BATC:OUT]", "E502"),
                          ("[LOOP:READ]", "E300"), ("[BATC:]", "E300"), ("[READ] [FMT]", "E502"),
                          ("[READ:@SRC]=>[Ω] [FMT]=>[Ω]", "E502"), ("=>[READ]", "E300"),
                          ("[READ] =>[FMT]", "E300"), ("[READ]=> [FMT]", "E300")):
            self.assertEqual(compile_cases.get(src), code, src)
        # the batch shorthand is valid in 0.4: no malformed case rejects it
        for src in ("[Π:READ]", "[BATC:READ]"):
            self.assertNotIn(src, compile_cases)

    def test_disjoint_from_golden(self):
        golden_inputs = set()
        for d in (GOLDEN, GOLDEN_03, GOLDEN_04):
            for p in d.iterdir():
                text = p.read_text(encoding="utf-8").rstrip("\n")
                golden_inputs.add(text)
                golden_inputs.update(line for line in text.split("\n") if line)
        for c in self.cases:
            self.assertNotIn(c["input"], golden_inputs)


if __name__ == "__main__":
    unittest.main()
