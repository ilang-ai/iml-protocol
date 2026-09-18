#!/usr/bin/env python3
"""Derive the IML 0.2 registry from the vendored I-Lang canon.

Sources (canon/, pinned by canon/PIN):
  SPEC.md                        verbs (section 3 tables, in order), aliases (3.10),
                                 core modifier keys (section 4), entity tiers 1 and 2
                                 (5.1, 5.2)
  archive/SPEC-v5.0-PATCH-2.md   entity tier 3 (section 2.1, the eight role entities;
                                 SPEC.md 5.3 only refers to this table)
  SPEC-v4.1-MEDIA-PROFILE.md     media profile keys (4.4.2), entity tier 4 (5.4)
  ilang_grammar_validator.py     cross-check only: its VERBS, ALIASES, MODIFIERS,
                                 MEDIA_PROFILE and TIER1..TIER4 must equal the parsed sets

Order of items is the order of first appearance in the canon tables. Codes are assigned
first come, first served (design 0.2 section 1). IML registers nothing of its own.

Usage:
  python tools/derive_registry.py            derive and write registry/iml-registry-0.2.json
  python tools/derive_registry.py --check    derive again and compare with the file (CI)
  python tools/derive_registry.py --tables   print name=code tables to stdout
"""

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CANON = ROOT / "canon"
PIN = CANON / "PIN"
REGISTRY_PATH = ROOT / "registry" / "iml-registry-0.2.json"

IML_VERSION = "0.2"
CANON_FILES = [
    "SPEC.md",
    "SPEC-v4.1-MEDIA-PROFILE.md",
    "archive/SPEC-v5.0-PATCH-2.md",
    "ilang_grammar_validator.py",
]
ALPHANUM = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
VOWELS = set("AEIOU")
RE_VERB = re.compile(r"^[A-Z]{2,5}$")
RE_KEY = re.compile(r"^[a-z]+$")
RE_ENTITY = re.compile(r"^@[A-Z][A-Z0-9_]*$")
RE_COUNT = re.compile(r"\((\d+)\)\s*$")


class DeriveError(Exception):
    pass


def fail(msg):
    raise DeriveError(msg)


# ----------------------------------------------------------------- canon files
def read_pin():
    upstream = commit = None
    shas = {}
    for line in PIN.read_text(encoding="utf-8").splitlines():
        if line.startswith("upstream "):
            upstream = line[len("upstream "):].strip()
        elif line.startswith("commit "):
            commit = line[len("commit "):].strip()
        elif line.strip():
            sha, _, name = line.partition("  ")
            shas[name.strip()] = sha.strip()
    if not upstream or not re.fullmatch(r"[0-9a-f]{40}", commit or ""):
        fail("canon/PIN lacks an upstream or a 40-hex commit line")
    return upstream, commit, shas


def verify_canon():
    """Return {name: sha256} of the vendored files after checking them against PIN."""
    _, commit, pinned = read_pin()
    if set(pinned) != set(CANON_FILES):
        fail("canon/PIN lists %s, expected %s" % (sorted(pinned), sorted(CANON_FILES)))
    shas = {}
    for name in CANON_FILES:
        data = (CANON / name).read_bytes()
        sha = hashlib.sha256(data).hexdigest()
        if sha != pinned[name]:
            fail("canon/%s does not match canon/PIN (%s != %s)" % (name, sha, pinned[name]))
        shas[name] = sha
    return commit, shas


def canon_text(name):
    return (CANON / name).read_text(encoding="utf-8")


# ---------------------------------------------------------------- table parsing
def section(text, start, ends):
    """Lines after the first line starting with `start`, up to the first following line
    starting with any of `ends` (or the end of the text when `ends` is empty)."""
    lines = text.splitlines()
    out, inside = [], False
    for line in lines:
        if not inside:
            if line.startswith(start):
                inside = True
                out.append(line)
            continue
        if any(line.startswith(e) for e in ends):
            break
        out.append(line)
    if not inside:
        fail("section %r not found" % start)
    return out


def table_rows(lines):
    """Cells of every Markdown table row, header and separator rows excluded."""
    for line in lines:
        s = line.strip()
        if not s.startswith("|"):
            continue
        cells = [c.strip() for c in s.strip("|").split("|")]
        if all(re.fullmatch(r":?-+:?", c) for c in cells if c) and any(cells):
            continue
        yield cells


def header_count(lines):
    m = RE_COUNT.search(lines[0])
    return int(m.group(1)) if m else None


def parse_spec(spec):
    verbs, column_aliases = [], {}
    for n in range(1, 10):
        sec = section(spec, "### 3.%d " % n, ["### 3.%d" % (n + 1)])
        found = []
        for cells in table_rows(sec):
            if len(cells) < 2 or cells[0] == "Verb" or not RE_VERB.match(cells[0]):
                continue
            found.append(cells[0])
            if cells[1]:
                if cells[1] in column_aliases:
                    fail("alias %s listed twice in the verb tables" % cells[1])
                column_aliases[cells[1]] = cells[0]
        want = header_count(sec)
        if want is not None and want != len(found):
            fail("section 3.%d announces %d verbs, table has %d" % (n, want, len(found)))
        verbs.extend(found)
    quick = {}
    for cells in table_rows(section(spec, "### 3.10", ["---", "## 4."])):
        for a, v in ((0, 1), (2, 3)):
            if len(cells) > v and cells[a] and cells[v] and cells[a] != "Alias":
                if cells[a] in quick:
                    fail("alias %s listed twice in 3.10" % cells[a])
                quick[cells[a]] = cells[v]
    if quick != column_aliases:
        fail("3.10 alias table %s differs from the Alias column %s" % (quick, column_aliases))
    core = []
    for cells in table_rows(section(spec, "## 4. Modifiers", ["### 4.1"])):
        if cells and cells[0] != "Mod" and RE_KEY.match(cells[0]):
            core.append(cells[0])
    tier1 = [c[0] for c in table_rows(section(spec, "### 5.1", ["### 5.2"])) if RE_ENTITY.match(c[0])]
    tier2 = [c[0] for c in table_rows(section(spec, "### 5.2", ["### 5.3"])) if RE_ENTITY.match(c[0])]
    return verbs, quick, core, tier1, tier2


def parse_patch2(patch2):
    def tier(start, ends):
        out = []
        for cells in table_rows(section(patch2, start, ends)):
            name = cells[0].strip("`")
            if RE_ENTITY.match(name):
                out.append(name)
        return out
    t1 = tier("**Tier 1", ["**Tier 2"])
    t2 = tier("**Tier 2", ["**Tier 3"])
    t3 = tier("**Tier 3", ["::CLAUSE{ENTITY-COUNT"])
    return t1, t2, t3


def parse_media(v41):
    keys = []
    for cells in table_rows(section(v41, "### 4.4.2", ["### 4.4.3"])):
        if cells and cells[0] != "Key" and RE_KEY.match(cells[0]):
            keys.append(cells[0])
    ents = [c[0] for c in table_rows(section(v41, "## 5.4", [])) if RE_ENTITY.match(c[0])]
    return keys, ents


def load_validator_constants():
    """Execute the vendored validator as a module and return its namespace. Its
    `__main__` guard is not taken (the namespace is named otherwise); a SystemExit
    raised anyway is swallowed so the constants stay readable."""
    path = CANON / "ilang_grammar_validator.py"
    ns = {"__name__": "iml_canon_validator", "__file__": str(path)}
    try:
        exec(compile(path.read_text(encoding="utf-8"), str(path), "exec"), ns)
    except SystemExit:
        pass
    return ns


def unique(seq, what):
    seen = set()
    for x in seq:
        if x in seen:
            fail("%s: %s appears twice in the canon tables" % (what, x))
        seen.add(x)


def crosscheck(name, parsed, validator_set):
    if set(parsed) != set(validator_set):
        fail("%s: canon tables %s differ from validator %s"
             % (name, sorted(set(parsed) - set(validator_set)), sorted(set(validator_set) - set(parsed))))


# -------------------------------------------------------------- code assignment
def letters(name):
    return "".join(ch for ch in name.upper() if ch in ALPHANUM)


def is_consonant(ch):
    return ch not in VOWELS


def candidates(name):
    s = letters(name)
    if not s:
        fail("name %r has no letters or digits" % name)
    first, rest = s[0], s[1:]
    for ch in rest:
        if is_consonant(ch):
            yield first + ch
    for ch in rest:
        if not is_consonant(ch):
            yield first + ch
    for ch in ALPHANUM[:26]:
        yield first + ch
    for a in ALPHANUM[:26]:
        for b in ALPHANUM[:26]:
            yield a + b


def assign(names, used):
    codes = {}
    for name in names:
        for cand in candidates(name):
            if cand not in used:
                used.add(cand)
                codes[name] = cand
                break
        else:
            fail("no free code for %s" % name)
    return codes


# --------------------------------------------------------------------- registry
def digest_of(obj):
    body = {k: v for k, v in obj.items() if k != "digest"}
    data = json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def derive():
    commit, shas = verify_canon()
    verbs, aliases, core, tier1, tier2 = parse_spec(canon_text("SPEC.md"))
    p1, p2, tier3 = parse_patch2(canon_text("archive/SPEC-v5.0-PATCH-2.md"))
    media_keys, tier4 = parse_media(canon_text("SPEC-v4.1-MEDIA-PROFILE.md"))

    unique(verbs, "verbs")
    unique(core + media_keys, "keys")
    unique(tier1 + tier2 + tier3 + tier4, "entities")
    if p1 != tier1 or p2 != tier2:
        fail("PATCH-2 tier 1/2 tables differ from SPEC.md 5.1/5.2")
    counts = (len(verbs), len(aliases), len(core), len(media_keys), len(tier1), len(tier2), len(tier3), len(tier4))
    if counts != (88, 13, 29, 20, 8, 6, 8, 3):
        fail("counts %s, expected (88, 13, 29, 20, 8, 6, 8, 3)" % (counts,))
    for a, v in aliases.items():
        if v not in verbs:
            fail("alias %s points at unknown verb %s" % (a, v))

    ns = load_validator_constants()
    crosscheck("verbs", verbs, ns["VERBS"])
    crosscheck("aliases", aliases.keys(), ns["ALIASES"])
    crosscheck("core modifiers", core, ns["MODIFIERS"])
    crosscheck("media profile", media_keys, ns["MEDIA_PROFILE"])
    crosscheck("tier 1", tier1, ns["TIER1"])
    crosscheck("tier 2", tier2, ns["TIER2"])
    crosscheck("tier 3", tier3, ns["TIER3"])
    crosscheck("tier 4", tier4, ns["TIER4"])

    roots = assign([v for v in verbs if v != "OUT"], set())
    key_codes = {k: c.lower() for k, c in assign(core + media_keys, set()).items()}
    ent_names = [e[1:] for e in tier1 + tier2 + tier3 + tier4]
    marks = assign(ent_names, set())
    tiers = {}
    for t, ents in enumerate((tier1, tier2, tier3, tier4), start=1):
        for e in ents:
            tiers[e[1:]] = t

    reg = {
        "iml_version": IML_VERSION,
        "canon": {"commit": commit, "files": shas},
        "verbs": [{"name": v, "root": roots.get(v)} for v in verbs],
        "aliases": aliases,
        "keys": [{"name": k, "code": key_codes[k], "tier": "core" if k in core else "media"}
                 for k in core + media_keys],
        "entities": [{"name": e, "mark": marks[e], "tier": tiers[e]} for e in ent_names],
        "value_codes": {k: {} for k in core + media_keys},
    }
    reg["digest"] = digest_of(reg)
    return reg


def serialize(reg):
    return (json.dumps(reg, sort_keys=True, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def print_tables(reg):
    print("ROOTS %d" % sum(1 for v in reg["verbs"] if v["root"]))
    print(" ".join("%s=%s" % (v["name"], v["root"] or "-") for v in reg["verbs"]))
    print("KEYS %d" % len(reg["keys"]))
    print(" ".join("%s=%s" % (k["name"], k["code"]) for k in reg["keys"]))
    print("MARKS %d" % len(reg["entities"]))
    print(" ".join("%s=%s" % (e["name"], e["mark"]) for e in reg["entities"]))
    print("DIGEST " + reg["digest"])


def main(argv=None):
    p = argparse.ArgumentParser(description="derive the IML 0.2 registry from canon/")
    p.add_argument("--check", action="store_true", help="re-derive and compare with the registry file")
    p.add_argument("--tables", action="store_true", help="print name=code tables")
    a = p.parse_args(argv)
    try:
        reg = derive()
    except DeriveError as e:
        print("derive_registry: ABORT: %s" % e, file=sys.stderr)
        return 1
    data = serialize(reg)
    if a.tables:
        print_tables(reg)
        return 0
    if a.check:
        if not REGISTRY_PATH.exists():
            print("derive_registry: %s is missing" % REGISTRY_PATH, file=sys.stderr)
            return 1
        if REGISTRY_PATH.read_bytes() != data:
            print("derive_registry: %s differs from a fresh derivation" % REGISTRY_PATH, file=sys.stderr)
            return 1
        print("registry ok: digest %s" % reg["digest"])
        return 0
    REGISTRY_PATH.parent.mkdir(parents=True, exist_ok=True)
    REGISTRY_PATH.write_bytes(data)
    print("wrote %s (digest %s)" % (REGISTRY_PATH.relative_to(ROOT), reg["digest"]))
    return 0


if __name__ == "__main__":
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass
    sys.exit(main())
