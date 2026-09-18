"""corpus/golden-0.5/: I-Lang documents NNN.ilang with their IML 0.5 documents NNN.iml
(design-0.5 section 10): hygiene and pairing, the compile output as recorded, the laws L1
and L2, coverage (every declaration name, every shape, the body forms), the canon text
kept verbatim where the corpus quotes it, and the pinned validator on every source and
every canonical print (raw mode, 0 errors)."""

import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

from iml import Chain, Decl, Text, compile_doc, decompile, decompile_doc, default_registry, parse_doc, print_doc  # noqa: E402
from validator_oracle import lint  # noqa: E402

GOLDEN_05 = ROOT / "corpus" / "golden-0.5"


def read_lf(path):
    data = path.read_bytes()
    if data.startswith(b"\xef\xbb\xbf") or b"\r" in data or not data.endswith(b"\n"):
        raise AssertionError("%s must be UTF-8 without BOM, LF only, ending in LF" % path)
    return data.decode("utf-8")


def walk(items):
    for it in items:
        yield it
        if isinstance(it, Decl):
            yield from walk(it.body)


def blocks(text, start, end):
    a = text.index(start)
    return re.findall(r"```\n(.*?)```", text[a:text.index(end, a + len(start))], re.S)


class TestGolden05(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reg = default_registry()
        cls.docs = []
        for p in sorted(GOLDEN_05.glob("*.ilang")):
            cls.docs.append((p.stem, read_lf(p), read_lf(p.with_suffix(".iml"))))
        cls.asts = {stem: parse_doc(src) for stem, src, _ in cls.docs}

    def test_pairing_and_hygiene(self):
        stems = {p.stem for p in GOLDEN_05.glob("*.ilang")}
        self.assertGreaterEqual(len(stems), 16)
        self.assertEqual({p.name for p in GOLDEN_05.iterdir()}, {s + e for s in stems for e in (".ilang", ".iml")})
        self.assertEqual(stems, {"%03d" % k for k in range(1, len(stems) + 1)})
        for stem, src, iml in self.docs:
            self.assertTrue(src.startswith("::ILANG::"), stem)
            self.assertTrue(iml.startswith(self.reg.header + "\n"), stem)

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
                self.assertEqual(parse_doc(printed), items)
                self.assertEqual(compile_doc(decompile_doc(m)), m)             # L2

    def test_coverage(self):
        every = [x for items in self.asts.values() for x in walk(items)]
        decls = [x for x in every if isinstance(x, Decl)]
        self.assertEqual({d.name for d in decls}, set(self.reg.declarations))
        self.assertEqual({d.shape for d in decls}, {"brace", "set", "wrapped", "opaque"})
        self.assertTrue(any(d.addr is not None and d.shape == s for d in decls for s in ("set", "wrapped")))
        self.assertTrue(any(d.prefix is not None for d in decls) and any(d.sub is not None for d in decls))
        nested = [b for d in decls for b in d.body if isinstance(b, Decl)]
        self.assertTrue(any(n.body for n in nested) and any(n.name in self.reg.double for n in nested))
        self.assertTrue(any(isinstance(b, Chain) for d in decls for b in d.body))
        texts = [x.text for x in every if isinstance(x, Text)]
        for pattern in (r"^T:", r"^A:", r"^[A-Za-z_]+:\[", r"^[A-Za-z_]+:.*\|", r"^\[[A-Z]+\] ", r"^\[[A-Z]+:",
                        r"^T\[[^\]]+\]=", r"^T\[[^\]]+\]\s", r"^PARALLEL\{", r"^→", r"^<<<", r"^::LATENCY",
                        r"^::CONFIDENCE", r"^::ILANG::"):
            self.assertTrue(any(re.search(pattern, t) for t in texts), pattern)
        sources = "\n".join(src for _, src, _ in self.docs)
        self.assertIn("\n  =>[", sources)                                     # continuation lines in a body
        self.assertIn("\n    =>[", sources)

    def test_canon_text_verbatim(self):
        patch2 = (ROOT / "canon" / "archive" / "SPEC-v5.0-PATCH-2.md").read_text(encoding="utf-8")
        spec = (ROOT / "canon" / "SPEC.md").read_text(encoding="utf-8")
        src = {stem: s for stem, s, _ in self.docs}
        self.assertEqual(src["001"], "::ILANG::v5.0\n" + blocks(patch2, "## Appendix A", "Shapes exercised:")[0])
        for stem, (a, b) in (("002", ("### 10.2 ", "### 10.3 ")), ("003", ("### 10.3 ", "### 10.4 ")),
                             ("004", ("### 10.4 ", "### 10.5 ")), ("005", ("### 10.5 ", "### 10.6 ")),
                             ("006", ("### 10.6 ", "### 10.7 ")), ("007", ("### 10.7 ", "## 11. "))):
            self.assertEqual(src[stem], "::ILANG::v5.0\n" + "\n".join(blocks(spec, a, b)), stem)
        for stem, start in (("013", "::GRAMMAR{shape:inline"), ("014", "::BODY{B1|name:trait}"),
                            ("015", "::REGISTRY{custom")):
            body = src[stem].split("\n", 1)[1]
            for block in body.split("\n\n"):
                if block.strip():
                    self.assertIn(block.strip("\n"), patch2, stem)

    def test_canon_validator_on_sources_and_prints(self):
        lines = 0
        for stem, src, _ in self.docs:
            with self.subTest(stem=stem):
                raw, errors = lint(src)
                self.assertTrue(raw)
                self.assertEqual(errors, [])
                raw, errors = lint(print_doc(self.asts[stem]) + "\n")
                self.assertTrue(raw)
                self.assertEqual(errors, [])
            lines += src.count("\n")
        print("\nvalidator on golden-0.5: %d documents (%d source lines), sources and canonical prints, 0 errors"
              % (len(self.docs), lines))


if __name__ == "__main__":
    unittest.main()
