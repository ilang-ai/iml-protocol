"""Round-trip laws (design 0.2 section 6) on the golden corpus and on 10,000 generated
chains, plus the independent legality oracle: the vendored canon validator run on the
printed I-Lang of a 500-chain sample (raw mode, first line `::ILANG::v4.0`).

Laws checked for every chain x (AST a = parse_L2(x), message m = compile(a)):
  L1   decompile(m) == a                             (AST fidelity)
  L2a  print_L2(parse_L2(print_L2(a))) == print_L2(a) (canonical print is idempotent)
  L2b  compile(decompile(m)) == m                    (codec-produced messages are fixed points)
  L2c  print_L2(decompile(m)) == print_L2(a)         (canonical text survives the loop)
The generator is not the oracle: it only has to stay inside the 0.2 subset and inside
what the canon validator accepts (media profile keys only on @IMG, @VID, @AUD).
"""

import json
import random
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from iml import compile, decompile, default_registry, parse_L2, print_L2  # noqa: E402
from iml.l2 import ilang_bareable  # noqa: E402

SEED = 20260918
COUNT = 10000
SAMPLE = 500
VALIDATOR = ROOT / "canon" / "ilang_grammar_validator.py"
GOLDEN = ROOT / "corpus" / "golden"
MEDIA = {"IMG", "VID", "AUD"}
BARE_ALPHABET = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._/-:*^#~{}@Φ→Ω"
FREE_ALPHABET = "abcdefghijklmnopqrstuvwxyz 0123456789,|][=>\"\\\n:@~Φ→Ωé中文"
NUMBERS = ["007", "0", "1", "1.0", "-3", "42", "3.14", "1e5", "0.50", "1.00", "2048x1365", "16:9"]
CUSTOM = ["MYDATA", "HOUSE_LOOK", "X", "A1", "REPORT_2026", "T_", "ZINE_LOOK", "OUT", "READ"]


class Generator:
    def __init__(self, seed):
        self.rng = random.Random(seed)
        self.reg = default_registry()
        self.non_out = [v for v in self.reg.verbs if v != "OUT"]
        self.alias_of = {v: a for a, v in self.reg.aliases.items()}
        self.core = [k for k in self.reg.keys if self.reg.key_tier[k] == "core"]
        self.media = [k for k in self.reg.keys if self.reg.key_tier[k] == "media"]

    def custom_name(self):
        rng = self.rng
        if rng.random() < 0.5:
            return rng.choice(CUSTOM)
        return rng.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ") + "".join(
            rng.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_") for _ in range(rng.randint(0, 8)))

    def entity(self):
        if self.rng.random() < 0.75:
            return "@" + self.rng.choice(self.reg.entities)
        return "@" + self.custom_name()

    def value(self):
        rng = self.rng
        r = rng.random()
        if r < 0.12:
            return self.entity()
        if r < 0.30:
            content = rng.choice(NUMBERS)
        elif r < 0.38:
            content = rng.choice(["true", "false"])
        elif r < 0.75:
            content = "".join(rng.choice(BARE_ALPHABET) for _ in range(rng.randint(1, 12)))
        else:
            content = "".join(rng.choice(FREE_ALPHABET) for _ in range(rng.randint(0, 20)))
        if ilang_bareable(content) and rng.random() < 0.8:
            return content
        return '"' + content.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n") + '"'

    def chain(self):
        rng = self.rng
        n = rng.randint(1, 8)
        ops = []
        for k in range(n):
            last = k == n - 1
            if last and rng.random() < 0.6:
                verb, target = "OUT", None
            else:
                verb = rng.choice(self.non_out)
                r = rng.random()
                target = None if r < 0.45 else (self.entity() if r < 0.85 else "@" + self.custom_name())
            pool = list(self.core)
            if target is not None and target[1:] in MEDIA:
                pool += self.media
            m = rng.choice([0, 0, 1, 1, 2, 3, 4])
            keys = rng.sample(pool, m)
            if verb == "OUT":
                spelling = rng.choice(["Ω", "Ω", "OUT"])
            elif verb in self.alias_of and rng.random() < 0.3:
                spelling = self.alias_of[verb]
            else:
                spelling = verb
            s = spelling
            if target is not None:
                s += ":" + target
            if keys:
                s += "|" + ",".join(key + "=" + self.value() for key in keys)
            ops.append("[" + s + "]")
        return "=>".join(ops)


def laws(x):
    a = parse_L2(x)
    m = compile(a)
    back = decompile(m)
    canon = print_L2(a)
    return {
        "L1": back == a,
        "L2a": print_L2(parse_L2(canon)) == canon,
        "L2b": compile(back) == m,
        "L2c": print_L2(back) == canon,
    }, canon


def run_validator(lines):
    """Lint the printed chains with the vendored canon validator (raw mode). Returns the
    parsed JSON report of the one file."""
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "sample.md"
        path.write_bytes(("::ILANG::v4.0\n" + "\n".join(lines) + "\n").encode("utf-8"))
        r = subprocess.run([sys.executable, str(VALIDATOR), "--lint", str(path), "--json"],
                           capture_output=True, text=True, encoding="utf-8")
    if r.returncode not in (0, 1):
        raise AssertionError("validator failed to run: %s" % r.stderr)
    report = json.loads(r.stdout)
    return report["files"][0]


class TestRoundTripGolden(unittest.TestCase):
    def test_laws_on_golden(self):
        pairs = sorted(GOLDEN.glob("*.ilang"))
        self.assertGreaterEqual(len(pairs), 60)
        for p in pairs:
            x = p.read_text(encoding="utf-8").rstrip("\n")
            with self.subTest(file=p.name):
                result, _ = laws(x)
                self.assertTrue(all(result.values()), result)

    def test_golden_prints_pass_canon_validator(self):
        lines = [print_L2(parse_L2(p.read_text(encoding="utf-8").rstrip("\n")))
                 for p in sorted(GOLDEN.glob("*.ilang"))]
        rep = run_validator(lines)
        errors = [f for f in rep["findings"] if f["level"] == "ERROR"]
        self.assertEqual(rep["mode"], "raw")
        self.assertEqual(errors, [])
        print("\nvalidator on golden: %d chains, %d error(s), %d warning(s)"
              % (len(lines), rep["errors"], rep["warnings"]))


class TestRoundTripRandom(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        gen = Generator(SEED)
        cls.chains = [gen.chain() for _ in range(COUNT)]

    def test_generator_is_deterministic(self):
        again = Generator(SEED)
        self.assertEqual([again.chain() for _ in range(50)], self.chains[:50])

    def test_laws_on_10000_chains(self):
        passed = 0
        failures = []
        canon = []
        for i, x in enumerate(self.chains):
            result, c = laws(x)
            canon.append(c)
            if all(result.values()):
                passed += 1
            elif len(failures) < 5:
                failures.append((i, x, result))
        print("\nrandom chains: %d/%d pass L1, L2a, L2b, L2c (seed %d, python %s)"
              % (passed, COUNT, SEED, sys.version.split()[0]))
        self.assertEqual(passed, COUNT, failures)
        lengths = {len(parse_L2(x).ops) for x in self.chains[:2000]}
        self.assertEqual(lengths, set(range(1, 9)))
        type(self).canon = canon

    def test_500_sample_passes_canon_validator(self):
        canon = getattr(type(self), "canon", None)
        if canon is None:
            canon = [laws(x)[1] for x in self.chains]
        sample = canon[::COUNT // SAMPLE][:SAMPLE]
        self.assertEqual(len(sample), SAMPLE)
        rep = run_validator(sample)
        errors = [f for f in rep["findings"] if f["level"] == "ERROR"]
        print("\nvalidator on %d-sample: %d error(s), %d warning(s), mode=%s"
              % (len(sample), rep["errors"], rep["warnings"], rep["mode"]))
        self.assertEqual(rep["mode"], "raw")
        self.assertEqual(errors, [], errors[:5])


if __name__ == "__main__":
    unittest.main()
