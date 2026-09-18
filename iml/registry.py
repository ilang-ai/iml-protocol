"""Load registry/iml-registry-0.2.json and verify its digest (SPEC-IML-0.3.md section 1).

The registry is derived from the I-Lang canon by tools/derive_registry.py. Loading it
recomputes the digest (sha256 of the JSON without the `digest` member, keys sorted,
separators `,` and `:`, ensure_ascii False) and refuses a file whose digest does not
match. Every header carries the first 12 hex characters of that digest.

The registry is the one derived for 0.2 and is unchanged in 0.3: its `iml_version`
member (0.2) names the vocabulary, and the digest 88d05d0839c1... stays. The version in
a header is the surface version, HEADER_VERSION below, which the codec owns.
"""

import hashlib
import json
from pathlib import Path

DEFAULT_PATH = Path(__file__).resolve().parents[1] / "registry" / "iml-registry-0.2.json"
HEADER_PREFIX = "#iml/"
HEADER_VERSION = "0.3"   # the surface written by compile; 0.2 is read only (codec.SURFACES)


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

    def header_for(self, version):
        """`#iml/<version>/<12 hex>`: the header of the given surface version over this
        registry's digest."""
        return HEADER_PREFIX + version + "/" + self.digest[:12]

    @property
    def header(self):
        """The header compile writes: the current surface version (HEADER_VERSION)."""
        return self.header_for(HEADER_VERSION)

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


def load_registry(path=None):
    path = Path(path) if path else DEFAULT_PATH
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
