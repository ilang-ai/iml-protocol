"""Registry derivation: idempotent, digest-verified, counts and shapes as the design says."""

import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from iml import __version__  # noqa: E402
from iml.registry import DEFAULT_PATH, HEADER_VERSION, RegistryError, compute_digest, load_registry  # noqa: E402

EXPECTED_ALIASES = {
    "Σ": "MERGE", "Δ": "DIFF", "φ": "FILT", "∇": "SORT", "λ": "MAP", "∂": "SPLIT", "μ": "STAT",
    "ψ": "SENT", "ξ": "HASH", "ζ": "CMPR", "θ": "XLAT", "Ω": "OUT", "Π": "BATC",
}
CANON_COMMIT = "127ba56f4eb1f35c2951d4aec4b7bd22831119ff"


def load_derive_module():
    spec = importlib.util.spec_from_file_location("derive_registry", ROOT / "tools" / "derive_registry.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class TestDerivation(unittest.TestCase):
    def test_derivation_is_idempotent_and_matches_file(self):
        d = load_derive_module()
        first = d.serialize(d.derive())
        second = d.serialize(d.derive())
        self.assertEqual(first, second)
        self.assertEqual(first, DEFAULT_PATH.read_bytes())

    def test_check_mode_exits_zero(self):
        r = subprocess.run([sys.executable, str(ROOT / "tools" / "derive_registry.py"), "--check"],
                           cwd=str(ROOT), capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_registry_file_is_lf_utf8_without_bom(self):
        data = DEFAULT_PATH.read_bytes()
        self.assertFalse(data.startswith(b"\xef\xbb\xbf"))
        self.assertEqual(data.count(b"\r"), 0)
        self.assertTrue(data.endswith(b"\n"))


class TestRegistryContent(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.obj = json.loads(DEFAULT_PATH.read_text(encoding="utf-8"))
        cls.reg = load_registry()

    def test_digest(self):
        self.assertEqual(len(self.obj["digest"]), 64)
        self.assertEqual(compute_digest(self.obj), self.obj["digest"])
        self.assertEqual(self.obj["digest"][:12], "88d05d0839c1")
        # the registry is the 0.2 one, unchanged in 0.3 and 0.4: its own version stays 0.2;
        # the header carries the surface version, 0.4 for what compile writes
        self.assertEqual(self.reg.version, "0.2")
        self.assertEqual(self.obj["iml_version"], "0.2")
        self.assertEqual(HEADER_VERSION, "0.4")
        self.assertEqual(HEADER_VERSION, __version__.rsplit(".", 1)[0])
        self.assertEqual(self.reg.header, "#iml/0.4/" + self.obj["digest"][:12])
        self.assertEqual(self.reg.header_for("0.4"), self.reg.header)
        self.assertEqual(self.reg.header_for("0.3"), "#iml/0.3/" + self.obj["digest"][:12])
        self.assertEqual(self.reg.header_for("0.2"), "#iml/0.2/" + self.obj["digest"][:12])

    def test_canon_pin(self):
        self.assertEqual(self.obj["canon"]["commit"], CANON_COMMIT)
        files = self.obj["canon"]["files"]
        self.assertEqual(set(files), {"SPEC.md", "SPEC-v4.1-MEDIA-PROFILE.md",
                                      "archive/SPEC-v5.0-PATCH-2.md", "ilang_grammar_validator.py"})
        for name, sha in files.items():
            self.assertEqual(hashlib.sha256((ROOT / "canon" / name).read_bytes()).hexdigest(), sha, name)
        pin = (ROOT / "canon" / "PIN").read_text(encoding="utf-8")
        self.assertIn("commit " + CANON_COMMIT, pin)
        for name, sha in files.items():
            self.assertIn(sha + "  " + name, pin)

    def test_counts(self):
        reg = self.reg
        self.assertEqual(len(reg.verbs), 88)
        self.assertEqual(len(reg.verb_root), 87)
        self.assertEqual(len(reg.aliases), 13)
        self.assertEqual(len(reg.keys), 49)
        self.assertEqual(sum(1 for k in reg.keys if reg.key_tier[k] == "core"), 29)
        self.assertEqual(sum(1 for k in reg.keys if reg.key_tier[k] == "media"), 20)
        self.assertEqual(len(reg.entities), 25)
        tiers = [reg.entity_tier[e] for e in reg.entities]
        self.assertEqual([tiers.count(t) for t in (1, 2, 3, 4)], [8, 6, 8, 3])

    def test_shapes_and_uniqueness(self):
        reg = self.reg
        roots = list(reg.verb_root.values())
        self.assertEqual(len(roots), len(set(roots)))
        for r in roots:
            self.assertRegex(r, r"^[A-Z0-9]{2}$")
        self.assertNotIn("OT", roots)
        self.assertNotIn("OUT", reg.verb_root)
        codes = list(reg.key_code.values())
        self.assertEqual(len(codes), len(set(codes)))
        for c in codes:
            self.assertRegex(c, r"^[a-z]{2}$")
        marks = list(reg.entity_mark.values())
        self.assertEqual(len(marks), len(set(marks)))
        for m in marks:
            self.assertRegex(m, r"^[A-Z0-9]{2}$")
        for e in reg.entities:
            self.assertRegex(e, r"^[A-Z][A-Z0-9_]*$")

    def test_aliases(self):
        self.assertEqual(self.reg.aliases, EXPECTED_ALIASES)
        for alias, verb in self.reg.aliases.items():
            self.assertEqual(self.reg.resolve_verb(alias), verb)

    def test_canon_order(self):
        reg = self.reg
        self.assertEqual(reg.verbs[:12], "READ WRIT GET DEL LIST COPY MOVE STRM CACH SYNC SEND RUN".split())
        self.assertEqual(reg.verbs[-1], "BATC")
        self.assertEqual(reg.keys[:4], ["src", "dst", "path", "fmt"])
        self.assertEqual(reg.keys[29], "sbj")
        self.assertEqual(reg.entities[:8], "SRC DST PREV LOCAL SCREEN LOG NULL STDIN".split())
        self.assertEqual(reg.entities[8:14], "GH R2 COS DRIVE WORKER CF".split())
        self.assertEqual(reg.entities[14:22], "SYSTEM RUNTIME GRADER USER SELF AGENT TASK TOOL".split())
        self.assertEqual(reg.entities[22:], "IMG VID AUD".split())

    def test_first_come_first_served_examples(self):
        reg = self.reg
        self.assertEqual(reg.verb_root["READ"], "RD")
        self.assertEqual(reg.verb_root["FILT"], "FL")   # FILT precedes FLAT in the canon table
        self.assertEqual(reg.verb_root["FLAT"], "FT")
        self.assertEqual(reg.key_code["lng"], "ln")     # lng precedes len
        self.assertEqual(reg.key_code["len"], "le")
        self.assertEqual(reg.key_code["to"], "to")
        self.assertEqual(reg.entity_mark["R2"], "R2")

    def test_value_code_tables_are_empty(self):
        self.assertEqual(set(self.reg.value_codes), set(self.reg.keys))
        for table in self.reg.value_codes.values():
            self.assertEqual(table, {})

    def test_tampered_registry_is_refused(self):
        obj = json.loads(DEFAULT_PATH.read_text(encoding="utf-8"))
        obj["verbs"][0]["root"] = "QQ"
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "bad.json"
            p.write_text(json.dumps(obj, sort_keys=True, ensure_ascii=False), encoding="utf-8")
            with self.assertRaises(RegistryError):
                load_registry(p)


if __name__ == "__main__":
    unittest.main()
