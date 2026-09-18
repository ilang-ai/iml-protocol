"""The 0.5 registry (design-0.5 section 2): the declarations table derived from the canon
text, cross-checked against the validator's sets, counts, flags, the 49 codes as derived
(stable), and the pairing with the 0.2 chain registry, which stays byte for byte."""

import hashlib
import json
import re
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

from iml.registry import CHAIN_PATH, DEFAULT_PATH, RegistryError, load_registry  # noqa: E402
from test_registry import load_derive_module  # noqa: E402
from validator_oracle import namespace  # noqa: E402

# the codes as derived at the pin (tools/derive_registry.py --tables); a change is a new registry
CODES = ("STATE=ST TRUST=TR ALIVE=AL MEMORY=MM GENE=GN GENE_MUTABLE=GM RULE=RL ACTIVATE=AC FACT=FC LESSON=LS "
         "PROGRESS=PR PRIORITY=PT DECAY=DC IMMUNE=IM UNTRUSTED=UN BUDGET=BD STATUS=SS OBJECTIVE=OB RUBRIC=RB "
         "EVIDENCE=EV PRIOR=PI FALLBACK=FL JUDGE=JD BOUNDARY=BN DIM=DM MODE=MD FUNC=FN SCHEMA=SC CASE=CS CLAUSE=CL "
         "MODULE=ML LIST=LT GRAMMAR=GR BODY=BY REGISTRY=RG END_UNTRUSTED=EN SAY=SY THINK=TH ACT=AT DECIDE=DD "
         "DISCOVER=DS CREATE=CR EVENT=ET SILENCE=SL META=MT IRONY=IR FORESHADOW=FR CALLBACK=CB EMOTION_FIELD=EM")
DIGEST_05 = "7e29fae7f5eab384fd1588c23ac9860dbb387e5d66bd1be71343d0bc728d61ba"
DIGEST_02 = "88d05d0839c1a2002abdb6f6be3c9846c2990496ce655b738d874217cc78c03f"
FILE_SHA_02 = "bf20e03caac60d663b17bca436cd9d80c350bce57bce9bb9e5cf33c4a5081b34"
CLASS_SETS = {"v3": "REGISTRY_V3", "v4": "REGISTRY_V4", "v5": "REGISTRY_V5", "amended": "REGISTRY_AMEND",
              "meta": "META_DECLS", "terminator": "TERMINATORS", "narrative": "DECL_NARRATIVE"}


class TestRegistry05(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.obj = json.loads(DEFAULT_PATH.read_text(encoding="utf-8"))
        cls.reg = load_registry()
        cls.ns = namespace()

    def test_files_and_digests(self):
        self.assertEqual(DEFAULT_PATH.name, "iml-registry-0.5.json")
        self.assertEqual(CHAIN_PATH.name, "iml-registry-0.2.json")
        self.assertEqual(self.reg.digest, DIGEST_05)
        self.assertEqual(self.reg.chain_digest, DIGEST_02)
        # the 0.2 file is the one of 0.2 to 0.4.1, byte for byte (sha256 of the file at v0.4.1, 7a65bb1)
        self.assertEqual(hashlib.sha256(CHAIN_PATH.read_bytes()).hexdigest(), FILE_SHA_02)
        self.assertEqual(self.reg.header, "#iml/0.5/" + DIGEST_05[:12])
        chain = json.loads(CHAIN_PATH.read_text(encoding="utf-8"))
        for member in ("canon", "verbs", "aliases", "keys", "entities", "value_codes"):
            self.assertEqual(self.obj[member], chain[member], member)
        self.assertEqual(set(self.obj) - set(chain), {"declarations", "tolerated_annotations"})

    def test_order_counts_and_classes(self):
        classes = [d["class"] for d in self.obj["declarations"]]
        runs = []
        for c in classes:
            if not runs or runs[-1][0] != c:
                runs.append([c, 0])
            runs[-1][1] += 1
        self.assertEqual([tuple(r) for r in runs], [("v3", 14), ("v4", 8), ("v5", 9), ("amended", 1), ("meta", 3),
                                                    ("terminator", 1), ("narrative", 13)])
        self.assertEqual(len(self.reg.declarations), 49)
        self.assertEqual(sorted(self.reg.double), sorted("SAY THINK ACT DECIDE DISCOVER CREATE".split()))
        self.assertEqual(sorted(self.reg.prose), sorted("LESSON MODULE LIST RULE OBJECTIVE".split()))
        self.assertEqual(self.reg.tolerated, ("LATENCY", "CONFIDENCE"))
        for d in self.obj["declarations"]:
            self.assertEqual(set(d), {"name", "code", "class", "double", "prose"})

    def test_cross_check_with_the_validator(self):
        for cls, const in CLASS_SETS.items():
            names = {d["name"] for d in self.obj["declarations"] if d["class"] == cls}
            self.assertEqual(names, set(self.ns[const]), cls)
        self.assertEqual(set(self.reg.double), set(self.ns["NARR_DOUBLE"]))
        self.assertEqual(set(self.reg.prose), set(self.ns["PROSE_BODY"]))
        self.assertEqual(set(self.reg.tolerated), set(self.ns["TOLERATED_ANNOT"]))

    def test_codes_as_derived(self):
        self.assertEqual(" ".join("%s=%s" % (d["name"], d["code"]) for d in self.obj["declarations"]), CODES)
        codes = [d["code"] for d in self.obj["declarations"]]
        self.assertEqual(len(set(codes)), 49)
        for c in codes:
            self.assertRegex(c, r"^[A-Z0-9]{2}$")
        # a namespace of its own: the same two characters may be a verb root (ST is STRM there)
        self.assertEqual(self.reg.verb_root["STRM"], "ST")
        self.assertEqual(self.reg.decl_code["STATE"], "ST")
        self.assertEqual(self.reg.code_decl["PI"], "PRIOR")      # PR is taken by PROGRESS, first come

    def test_derivation_parses_the_canon_text(self):
        d = load_derive_module()
        classes, double, prose, tolerated = d.parse_declarations(d.canon_text("archive/SPEC-v5.0-PATCH-2.md"),
                                                                 d.canon_text("SPEC.md"))
        self.assertEqual([c for c, _ in classes], ["v3", "v4", "v5", "amended", "meta", "terminator", "narrative"])
        self.assertEqual(double, "SAY THINK ACT DECIDE DISCOVER CREATE".split())
        self.assertEqual(prose, "LESSON MODULE LIST RULE OBJECTIVE".split())
        self.assertEqual(tolerated, ["LATENCY", "CONFIDENCE"])
        # a list that wraps onto a second line is read whole (PATCH-2 1.5, v3.0 layer)
        lists = d.decl_lists(["**x (3)**", "`::A` `::B`", "`::C`", "", "`::D`"])
        self.assertEqual(lists, [("x (3)", ["A", "B", "C"]), ("x (3)", ["D"])])

    def test_derivation_refuses_a_changed_count(self):
        d = load_derive_module()
        patch2 = d.canon_text("archive/SPEC-v5.0-PATCH-2.md").replace("`::PRIOR` `::FALLBACK`", "`::PRIOR`")
        with self.assertRaises(d.DeriveError):
            d.parse_declarations(patch2, d.canon_text("SPEC.md"))

    def test_tampered_or_mismatched_registry_is_refused(self):
        obj = json.loads(DEFAULT_PATH.read_text(encoding="utf-8"))
        obj["declarations"][0]["code"] = "QQ"
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "bad.json"
            p.write_text(json.dumps(obj, sort_keys=True, ensure_ascii=False), encoding="utf-8")
            with self.assertRaises(RegistryError):
                load_registry(p)
            # a 0.5 registry whose chain tables differ from the chain registry's is refused
            d = load_derive_module()
            reg02, reg05 = d.derive_both()
            reg05 = dict(reg05)
            reg05["keys"] = reg05["keys"][:-1]
            reg05["value_codes"] = {k["name"]: {} for k in reg05["keys"]}
            reg05["digest"] = d.digest_of(reg05)
            p.write_bytes(d.serialize(reg05))
            with self.assertRaises(RegistryError) as cm:
                load_registry(p)
            self.assertIn("differ", str(cm.exception))

    def test_the_0_2_registry_alone_has_no_0_5_header(self):
        chain = load_registry(CHAIN_PATH)
        self.assertFalse(chain.has_declarations)
        self.assertEqual(chain.header_for("0.4"), "#iml/0.4/" + DIGEST_02[:12])
        with self.assertRaises(RegistryError):
            chain.header_for("0.5")
        self.assertTrue(re.fullmatch(r"#iml/0\.5/[0-9a-f]{12}", self.reg.header))


if __name__ == "__main__":
    unittest.main()
