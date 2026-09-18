"""The document laws on generated documents (design-0.5 section 6): 2,000 raw I-Lang
documents from tests/doc_generator.py (seed 20260918), each checked under

  L1  decompile_doc(compile_doc(parse_doc(x))) == parse_doc(x)
  L2  print_doc(parse_doc(print_doc(d))) == print_doc(d), and
      compile_doc(decompile_doc(m)) == m for the document m the codec produced

and the pinned validator as the oracle on every source and every canonical print (raw
mode, 0 errors). Then 1,000 mutated documents: whatever the codec accepts, the validator
accepts too, and the laws hold on it."""

import random
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

from doc_generator import DocGenerator  # noqa: E402
from iml import (Chain, Decl, IMLError, Text, compile_doc, decompile_doc, default_registry,  # noqa: E402
                 parse_doc, print_doc)
from validator_oracle import lint  # noqa: E402

SEED = 20260918
COUNT = 2000
MUTATIONS = 1000
PIECES = ["{", "}", "[", "]", "::", "=>", "|", ":", " ", "\t", "T[1]", "@x", "\n", "\n  ", "\n\n", "=", '"',
          "::GENE", "::SAY", "}{", "→", "---", "::ILANG::v5.0", "[NOTE]", "[READ]"]


def laws(items):
    m = compile_doc(items)
    back = decompile_doc(m)
    printed = print_doc(items)
    return (back == items and compile_doc(back) == m and parse_doc(printed) == items
            and print_doc(parse_doc(printed)) == printed), printed


def outside_media_gating(errors):
    """The validator's errors less the one documented difference of chains (design-0.5
    section 6; SPEC-IML-0.4.md section 0.2): E302 for a media profile key on a non-media
    target, which the codec does not judge."""
    return [f for f in errors if not (f[2] == "E302" and "media profile key used on a non-media target" in f[3])]


def walk(items):
    for it in items:
        yield it
        if isinstance(it, Decl):
            yield from walk(it.body)


class TestDocRandom(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        gen = DocGenerator(SEED)
        cls.sources = [gen.document() for _ in range(COUNT)]
        cls.asts = [parse_doc(s) for s in cls.sources]

    def test_generator_is_deterministic(self):
        again = DocGenerator(SEED)
        self.assertEqual([again.document() for _ in range(20)], self.sources[:20])

    def test_laws_and_oracle_on_2000_documents(self):
        passed = lines = items = 0
        for k, (src, ast) in enumerate(zip(self.sources, self.asts)):
            ok, printed = laws(ast)
            raw_src, err_src = lint(src)
            raw_print, err_print = lint(printed + "\n")
            self.assertTrue(raw_src and raw_print, k)
            self.assertEqual(err_src, [], (k, src))
            self.assertEqual(err_print, [], (k, printed))
            self.assertTrue(ok, (k, src))
            passed += 1
            lines += src.count("\n")
            items += len(ast)
        print("\nrandom documents: %d/%d pass L1 and L2; validator on sources and prints: 0 errors"
              " (%d source lines, %d items, seed %d, python %s)" % (passed, COUNT, lines, items, SEED, sys.version.split()[0]))
        self.assertEqual(passed, COUNT)

    def test_generator_coverage(self):
        reg = default_registry()
        every = [x for ast in self.asts for x in walk(ast)]
        decls = [x for x in every if isinstance(x, Decl)]
        self.assertEqual({d.name for d in decls}, set(reg.declarations))
        self.assertEqual({d.shape for d in decls}, {"brace", "set", "wrapped", "opaque"})
        for shape in ("brace", "set", "wrapped"):
            self.assertTrue(any(d.addr is not None and d.shape == shape for d in decls), shape)
        self.assertTrue(any(d.prefix is not None for d in decls))
        nested = [b for d in decls for b in d.body if isinstance(b, Decl)]
        self.assertTrue(any(n.body for n in nested) and any(n.sub for n in nested) and any(n.addr is not None for n in nested))
        self.assertTrue(any(isinstance(b, Chain) for d in decls for b in d.body))
        self.assertTrue(any(isinstance(x, Chain) for ast in self.asts for x in ast))
        self.assertTrue(any(d.shape == "opaque" and "" in d.lines for d in decls))
        texts = [x.text for x in every if isinstance(x, Text)]
        for start in ("T:", "A:", "M:", "V:", "[NOTE", "T[", "PARALLEL{", "→", "<<<", "::LATENCY", "::CONFIDENCE",
                      "::ILANG::", "[sic]"):
            self.assertTrue(any(t.startswith(start) for t in texts), start)
        joined = "\n".join(self.sources)
        for layout in ("\n\t", "\n  =>", "\n    =>", "\n---\n", "} T:", "}\tT", "T[3]\t::", " \n"):
            self.assertIn(layout, joined, repr(layout))
        separated = sum(1 for ast in self.asts if "\n\n" in print_doc(ast))
        self.assertGreater(separated, 0)                                     # the print's one blank line
        print("\ndocument generator: %d declarations (%d nested), %d texts, %d prints with the separating blank line"
              % (len(decls), len(nested), len(texts), separated))

    def test_mutated_documents(self):
        """The second half of the oracle: a mutated document the codec accepts is one the
        validator accepts, and the laws hold on it."""
        rng = random.Random(SEED + 2)
        accepted = refused = 0
        for k in range(MUTATIONS):
            s = self.sources[k]
            for _ in range(rng.randint(1, 3)):
                at = rng.randrange(len(s) + 1)
                if rng.random() < 0.5:
                    s = s[:at] + rng.choice(PIECES) + s[at:]
                else:
                    s = s[:at] + s[at + rng.randint(1, 4):]
            if not s.startswith("::ILANG::"):
                s = "::ILANG::v5.0\n" + s
            try:
                ast = parse_doc(s)
            except IMLError:
                refused += 1
                continue
            accepted += 1
            self.assertEqual(outside_media_gating(lint(s)[1]), [], s)
            ok, printed = laws(ast)
            self.assertTrue(ok, s)
            self.assertEqual(outside_media_gating(lint(printed + "\n")[1]), [], s)
        print("\nmutated documents: %d accepted (validator 0 errors on each, laws hold), %d refused" % (accepted, refused))
        self.assertGreater(accepted, 0)
        self.assertGreater(refused, 0)


if __name__ == "__main__":
    unittest.main()
