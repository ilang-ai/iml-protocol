"""Load the IML registries and verify their digests (SPEC-IML-0.5.md section 1, SPEC-IML-0.6.md section 1).

Three files, all derived from the I-Lang canon by tools/derive_registry.py:

  registry/iml-registry-0.6.json   the default: the chain tables (verbs, aliases, keys,
                                   entities, value codes) plus the declarations table (50
                                   names with two-character codes, ::EXCLUDE registered by
                                   the canon's 5.0.11 amendment) and the tolerated
                                   annotations; its digest is new in 0.6
  registry/iml-registry-0.5.json   the declaration registry of 0.5 (49 names), kept byte
                                   for byte: the one a 0.5 header names
  registry/iml-registry-0.2.json   the chain registry of 0.2, 0.3 and 0.4, kept byte for
                                   byte (digest 88d05d0839c1...)

Loading a file recomputes the digest (sha256 of the JSON without the `digest` member, keys
sorted, separators `,` and `:`, ensure_ascii False) and refuses a file whose digest does
not match. Loading the 0.5 registry also loads the 0.2 registry and checks that the chain
tables and the canon pin of the two are equal, so that a 0.4 or 0.3 text, which carries
the 0.2 digest in its header, is read with exactly the tables it was written with.

Every header carries the first 12 hex characters of a digest: `#iml/0.5/` the 0.5
registry's, `#iml/0.4/`, `#iml/0.3/` and `#iml/0.2/` the 0.2 registry's (the chain digest).
The version in a header is the surface version; HEADER_VERSION below is the one compile
writes.
"""

import hashlib
import json
import re
from pathlib import Path

REGISTRY_DIR = Path(__file__).resolve().parents[1] / "registry"
DEFAULT_PATH = REGISTRY_DIR / "iml-registry-0.6.json"   # the declaration registry of 0.6 (50 declarations, canon 5.0.11)
DOC_PATH_05 = REGISTRY_DIR / "iml-registry-0.5.json"    # the declaration registry of 0.5, kept byte for byte: a 0.5 header names it
CHAIN_PATH = REGISTRY_DIR / "iml-registry-0.2.json"     # the chain registry of 0.2, 0.3 and 0.4
HEADER_PREFIX = "#iml/"
HEADER_VERSION = "0.6"   # the surface written by compile; 0.5, 0.4 and 0.3 are read by the same reader, 0.2 is read only (codec.SURFACES)
DOCUMENT_LAYER_VERSIONS = ("0.6", "0.5")   # header versions whose digest is a declaration registry's (the declaration layer)
CHAIN_TABLES = ("canon", "verbs", "aliases", "keys", "entities", "value_codes")
CHAIN_CONTENT = ("verbs", "aliases", "keys", "entities", "value_codes")   # the tables every registry shares; the canon pin may move


class RegistryError(Exception):
    pass


def compute_digest(obj):
    body = {k: v for k, v in obj.items() if k != "digest"}
    data = json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


class Registry:
    """Bidirectional tables: verbs <-> roots, aliases -> verbs, keys <-> codes,
    entities <-> marks, and the (empty in 0.2) value code tables per key."""

    def __init__(self, obj, path=None):
        self.path = path
        self.raw = obj
        self.version = obj["iml_version"]
        self.digest = obj["digest"]
        self.commit = obj["canon"]["commit"]
        self.canon_files = dict(obj["canon"]["files"])
        self.verbs = [v["name"] for v in obj["verbs"]]
        self.verb_root = {v["name"]: v["root"] for v in obj["verbs"] if v["root"]}
        self.root_verb = {v["root"]: v["name"] for v in obj["verbs"] if v["root"]}
        self.aliases = dict(obj["aliases"])
        self.keys = [k["name"] for k in obj["keys"]]
        self.key_code = {k["name"]: k["code"] for k in obj["keys"]}
        self.code_key = {k["code"]: k["name"] for k in obj["keys"]}
        self.key_tier = {k["name"]: k["tier"] for k in obj["keys"]}
        self.entities = [e["name"] for e in obj["entities"]]
        self.entity_mark = {e["name"]: e["mark"] for e in obj["entities"]}
        self.mark_entity = {e["mark"]: e["name"] for e in obj["entities"]}
        self.entity_tier = {e["name"]: e["tier"] for e in obj["entities"]}
        self.value_codes = {k: dict(v) for k, v in obj["value_codes"].items()}
        # 0.5: the declarations table (empty for the 0.2 registry) and the tolerated annotations
        decls = obj.get("declarations", [])
        self.declarations = [d["name"] for d in decls]
        self.decl_code = {d["name"]: d["code"] for d in decls}
        self.code_decl = {d["code"]: d["name"] for d in decls}
        self.decl_class = {d["name"]: d["class"] for d in decls}
        self.double = frozenset(d["name"] for d in decls if d["double"])
        self.prose = frozenset(d["name"] for d in decls if d["prose"])
        self.tolerated = tuple(obj.get("tolerated_annotations", ()))
        # the digest that 0.2, 0.3 and 0.4 headers carry: this file's own for the 0.2
        # registry, the 0.2 registry's for the 0.5 one (set by load_registry)
        self.chain_digest = self.digest
        # 0.6: the earlier declaration registry a header may still name (0.5), loaded by load_registry
        self.prev = None
        self.doc_digests = {self.version: self.digest} if self.declarations else {}

    @property
    def has_declarations(self):
        return bool(self.declarations)

    def digest_for(self, version):
        """The digest a header of the given version carries: a declaration registry's own for 0.6 and 0.5 (the
        declaration layer; the 0.5 digest comes from the frozen 0.5 file), the chain digest for 0.4, 0.3 and 0.2."""
        if version in DOCUMENT_LAYER_VERSIONS:
            if not self.has_declarations:
                raise RegistryError("registry %s carries no declarations table: no %s header" % (self.version, version))
            d = self.doc_digests.get(version)
            if d is None:
                raise RegistryError("registry %s carries no %s declarations table: no %s header" % (self.version, version, version))
            return d
        return self.chain_digest

    def for_version(self, version):
        """The registry whose tables a header of the given version was written with: this one for its own version
        and for the chain versions, the frozen earlier declaration registry (prev) for an earlier declaration-layer
        header."""
        if version == self.version or version not in DOCUMENT_LAYER_VERSIONS:
            return self
        if self.prev is not None and self.prev.version == version:
            return self.prev
        raise RegistryError("registry %s holds no tables for a %s header" % (self.version, version))

    def header_for(self, version):
        """`#iml/<version>/<12 hex>`: the header of the given surface version over the
        digest that version carries (digest_for)."""
        return HEADER_PREFIX + version + "/" + self.digest_for(version)[:12]

    @property
    def header(self):
        """The header compile writes with this registry: its own version for a declaration registry (0.6, or 0.5 when
        the frozen 0.5 registry is passed explicitly), HEADER_VERSION otherwise."""
        return self.header_for(self.version if self.version in DOCUMENT_LAYER_VERSIONS else HEADER_VERSION)

    def is_verb(self, name):
        return name in self.verbs

    def resolve_verb(self, spelling):
        """Canon verb name for a verb or alias spelling, or None."""
        name = self.aliases.get(spelling, spelling)
        return name if name in self.verbs else None


def validate_structure(obj):
    for member in ("iml_version", "canon", "verbs", "aliases", "keys", "entities", "value_codes", "digest"):
        if member not in obj:
            raise RegistryError("registry lacks member %r" % member)
    roots = [v["root"] for v in obj["verbs"] if v["root"]]
    codes = [k["code"] for k in obj["keys"]]
    marks = [e["mark"] for e in obj["entities"]]
    for what, seq in (("roots", roots), ("key codes", codes), ("marks", marks)):
        if len(seq) != len(set(seq)):
            raise RegistryError("registry %s are not unique" % what)
    for v in obj["verbs"]:
        if v["name"] == "OUT" and v["root"] is not None:
            raise RegistryError("OUT must carry no root")
    if set(obj["value_codes"]) != {k["name"] for k in obj["keys"]}:
        raise RegistryError("value_codes must carry one table per key")
    if obj["iml_version"] != "0.2":
        for member in ("declarations", "tolerated_annotations"):
            if member not in obj:
                raise RegistryError("registry %s lacks member %r" % (obj["iml_version"], member))
        names = [d["name"] for d in obj["declarations"]]
        dcodes = [d["code"] for d in obj["declarations"]]
        for what, seq in (("declaration names", names), ("declaration codes", dcodes)):
            if len(seq) != len(set(seq)):
                raise RegistryError("registry %s are not unique" % what)
        for d in obj["declarations"]:
            if not re.fullmatch(r"[A-Z0-9]{2}", d["code"]) or not re.fullmatch(r"[A-Z][A-Z0-9_]*", d["name"]):
                raise RegistryError("declaration %r has a malformed name or code" % (d,))
        if set(obj["tolerated_annotations"]) & set(names):
            raise RegistryError("a tolerated annotation is a registered declaration")


def load_registry(path=None, chain_path=None, prev_path=None):
    """Load a registry file (default: the 0.6 registry) and verify its digest. A registry
    with a declarations table is paired with the chain registry (default: the 0.2 file):
    its digest is verified too, its chain tables (verbs, aliases, keys, entities, value
    codes) must equal this file's, and its digest becomes chain_digest, the one 0.4, 0.3
    and 0.2 headers carry. The 0.6 registry is also paired with the frozen 0.5 registry
    (default: the 0.5 file), whose digest a 0.5 header carries and whose tables read a 0.5
    document; its chain tables must equal too. The canon pin may differ between the files:
    0.6 derives from the canon at 5.0.11, the earlier files from the canon at 127ba56."""
    reg = _load_one(Path(path) if path else DEFAULT_PATH)
    if reg.version != "0.2":
        chain = _load_one(Path(chain_path) if chain_path else CHAIN_PATH)
        if chain.version != "0.2":
            raise RegistryError("chain registry %s is not a 0.2 registry" % chain.path)
        for member in CHAIN_CONTENT:
            if chain.raw[member] != reg.raw[member]:
                raise RegistryError("registry %s and chain registry %s differ in %r" % (reg.path, chain.path, member))
        reg.chain_digest = chain.digest
        if reg.version == "0.6":
            prev = _load_one(Path(prev_path) if prev_path else DOC_PATH_05)
            if prev.version != "0.5":
                raise RegistryError("registry %s is not a 0.5 registry" % prev.path)
            for member in CHAIN_CONTENT:
                if chain.raw[member] != prev.raw[member]:
                    raise RegistryError("registry %s and chain registry %s differ in %r" % (prev.path, chain.path, member))
            prev.chain_digest = chain.digest
            reg.prev = prev
            reg.doc_digests[prev.version] = prev.digest
    return reg


def _load_one(path):
    try:
        obj = json.loads(path.read_text(encoding="utf-8"))
    except OSError as e:
        raise RegistryError("cannot read registry %s: %s" % (path, e))
    except ValueError as e:
        raise RegistryError("registry %s is not valid JSON: %s" % (path, e))
    validate_structure(obj)
    digest = compute_digest(obj)
    if digest != obj["digest"]:
        raise RegistryError("registry digest mismatch: file says %s, content is %s" % (obj["digest"], digest))
    return Registry(obj, path)


_default = None


def default_registry():
    global _default
    if _default is None:
        _default = load_registry()
    return _default
