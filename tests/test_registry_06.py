"""The 0.6 registry (SPEC-IML-0.6.md section 1): the declarations table derived from the current canon (ilang-spec
5.0.11, where the section 1.5 amendment registered ::EXCLUDE), 50 names, the 49 codes of 0.5 unchanged and EXCLUDE=EX,
the frozen 0.5 and 0.2 files paired with it, and a reader that takes a 0.5 header with the 0.5 tables."""

import hashlib
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

from iml import compile_doc, decompile_doc, parse_doc  # noqa: E402
from iml.registry import CHAIN_PATH, DEFAULT_PATH, DOC_PATH_05, HEADER_VERSION, RegistryError, load_registry  # noqa: E402
from test_registry import load_derive_module  # noqa: E402
from test_registry_05 import CODES as CODES_05, DIGEST_02, DIGEST_05  # noqa: E402
from validator_oracle import namespace  # noqa: E402

DIGEST_06 = "ba5fde00dd6998a6a212311798e6ae30800e330b72c2cbef1b02a97947c9bacb"
CANON_COMMIT_06 = "d1d436733373c6342a74d4865348761320138613"
FILE_SHA_05 = "698b8834f589f9487f53c9547d9c07975fb31451766b4a56e380c5231546fe75"
CODES_06 = CODES_05.replace("LIST=LT GRAMMAR=GR", "LIST=LT EXCLUDE=EX GRAMMAR=GR")
GOLDEN_05 = ROOT / "corpus" / "golden-0.5"


class TestRegistry06(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.obj = json.loads(DEFAULT_PATH.read_text(encoding="utf-8"))
        cls.reg = load_registry()
        cls.ns = namespace()

    def test_files_and_digests(self):
        self.assertEqual(DEFAULT_PATH.name, "iml-registry-0.6.json")
        self.assertEqual(self.reg.version, "0.6")
        self.assertEqual(self.reg.digest, DIGEST_06)
        self.assertEqual(self.reg.chain_digest, DIGEST_02)
        self.assertEqual(self.reg.prev.version, "0.5")
        self.assertEqual(self.reg.prev.digest, DIGEST_05)
        self.assertEqual(hashlib.sha256(DOC_PATH_05.read_bytes()).hexdigest(), FILE_SHA_05)   # the 0.5 file is frozen
        self.assertEqual(HEADER_VERSION, "0.6")
        self.assertEqual(self.reg.header, "#iml/0.6/" + DIGEST_06[:12])
        self.assertEqual(self.reg.header_for("0.5"), "#iml/0.5/" + DIGEST_05[:12])
        self.assertEqual(self.reg.prev.header, "#iml/0.5/" + DIGEST_05[:12])
        for v in ("0.4", "0.3", "0.2"):
            self.assertEqual(self.reg.header_for(v), "#iml/%s/" % v + DIGEST_02[:12])
        self.assertEqual(self.obj["canon"]["commit"], CANON_COMMIT_06)
        self.assertIn("SPEC-v5.0.md", self.obj["canon"]["files"])
        chain = json.loads(CHAIN_PATH.read_text(encoding="utf-8"))
        for member in ("verbs", "aliases", "keys", "entities", "value_codes"):
            self.assertEqual(self.obj[member], chain[member], member)

    def test_table(self):
        decls = self.obj["declarations"]
        self.assertEqual(len(decls), 50)
        runs = []
        for d in decls:
            if not runs or runs[-1][0] != d["class"]:
                runs.append([d["class"], 0])
            runs[-1][1] += 1
        self.assertEqual([tuple(r) for r in runs], [("v3", 14), ("v4", 8), ("v5", 9), ("amended", 2), ("meta", 3),
                                                    ("terminator", 1), ("narrative", 13)])
        self.assertEqual(" ".join("%s=%s" % (d["name"], d["code"]) for d in decls), CODES_06)
        self.assertEqual(self.reg.decl_code["EXCLUDE"], "EX")
        self.assertEqual(self.reg.decl_class["EXCLUDE"], "amended")
        self.assertFalse("EXCLUDE" in self.reg.double or "EXCLUDE" in self.reg.prose)
        self.assertNotIn("EXCLUDE", self.reg.prev.declarations)
        for name, code in self.reg.prev.decl_code.items():
            self.assertEqual(self.reg.decl_code[name], code, name)          # the 49 codes of 0.5 are unchanged

    def test_cross_check_with_the_validator(self):
        for cls, const in (("v3", "REGISTRY_V3"), ("v4", "REGISTRY_V4"), ("v5", "REGISTRY_V5"), ("amended", "REGISTRY_AMEND"),
                           ("meta", "META_DECLS"), ("terminator", "TERMINATORS"), ("narrative", "DECL_NARRATIVE")):
            names = {d["name"] for d in self.obj["declarations"] if d["class"] == cls}
            self.assertEqual(names, set(self.ns[const]), cls)
        self.assertEqual(set(self.ns["REGISTRY_AMEND"]), {"LIST", "EXCLUDE"})
        self.assertEqual(len(self.ns["DECL_STRUCTURAL"]), 33)

    def test_derivation(self):
        d = load_derive_module()
        classes, double, prose, tolerated = d.parse_declarations(d.canon_text("SPEC-v5.0.md"), d.canon_text("SPEC.md"))
        self.assertEqual([(c, len(ns)) for c, ns in classes], d.DECL_CLASSES_06)
        self.assertEqual(dict(classes)["amended"], ["LIST", "EXCLUDE"])
        frozen02, reg06 = d.derive_both()
        self.assertEqual(d.serialize(frozen02), CHAIN_PATH.read_bytes())
        self.assertEqual(d.serialize(reg06), DEFAULT_PATH.read_bytes())
        d.check_frozen()
        # the archived PATCH-2 still yields the 0.5 table, which the frozen 0.5 file records
        classes05, _, _, _ = d.parse_declarations(d.canon_text("archive/SPEC-v5.0-PATCH-2.md"), d.canon_text("SPEC.md"))
        self.assertEqual([(c, len(ns)) for c, ns in classes05], d.DECL_CLASSES)

    def test_for_version_reads_a_0_5_document_with_the_0_5_tables(self):
        self.assertIs(self.reg.for_version("0.6"), self.reg)
        self.assertIs(self.reg.for_version("0.5"), self.reg.prev)
        self.assertIs(self.reg.for_version("0.4"), self.reg)
        with self.assertRaises(RegistryError):
            self.reg.prev.for_version("0.6")
        with self.assertRaises(RegistryError):
            self.reg.prev.header_for("0.6")
        src = (GOLDEN_05 / "001.ilang").read_text(encoding="utf-8")
        iml05 = (GOLDEN_05 / "001.iml").read_text(encoding="utf-8")[:-1]
        items = parse_doc(src)
        self.assertEqual(decompile_doc(iml05), items)                                  # read with the 0.5 tables
        self.assertEqual(compile_doc(items, registry=self.reg.prev), iml05)             # written as 0.5 on request
        iml06 = compile_doc(items)
        self.assertTrue(iml06.startswith(self.reg.header + "\n"))
        self.assertEqual(iml06[len(self.reg.header):], iml05[len(self.reg.prev.header):])   # same codes, new header


if __name__ == "__main__":
    unittest.main()
