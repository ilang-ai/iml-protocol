#!/usr/bin/env python3
"""Derive the IML registries from the vendored I-Lang canon.

Two files are written, both from the same canon text:
  registry/iml-registry-0.2.json   the chain registry of 0.2, 0.3 and 0.4, kept byte for
                                   byte (digest 88d05d0839c1...): verbs, aliases, keys,
                                   entities, value codes
  registry/iml-registry-0.5.json   the same chain tables with iml_version 0.5, plus the
                                   declarations table (49 names, two-character codes) and
                                   the tolerated annotations; a digest of its own

Sources (canon/, pinned by canon/PIN):
  SPEC.md                        verbs (section 3 tables, in order), aliases (3.10),
                                 core modifier keys (section 4), entity tiers 1 and 2
                                 (5.1, 5.2); the double-brace narratives (the 7.1 code
                                 block, forms written `::VERB{..}{..}`)
  archive/SPEC-v5.0-PATCH-2.md   entity tier 3 (section 2.1, the eight role entities;
                                 SPEC.md 5.3 only refers to this table); the declaration
                                 registry (1.5: the four layer lists under their bold
                                 headings, the meta list, the `::END_UNTRUSTED` sentence;
                                 1.6: the narrative list and the LATENCY/CONFIDENCE
                                 sentence); the prose-body types (1.2 B6,
                                 current_prose_body_types)
  SPEC-v4.1-MEDIA-PROFILE.md     media profile keys (4.4.2), entity tier 4 (5.4)
  ilang_grammar_validator.py     cross-check only: its VERBS, ALIASES, MODIFIERS,
                                 MEDIA_PROFILE, TIER1..TIER4, REGISTRY_V3, REGISTRY_V4,
                                 REGISTRY_V5, REGISTRY_AMEND, META_DECLS, TERMINATORS,
                                 DECL_NARRATIVE, NARR_DOUBLE, PROSE_BODY and
                                 TOLERATED_ANNOT must equal the parsed sets

Order of items is the order of first appearance in the canon tables; the declarations
follow the order of design 0.5 section 2 (v3, v4, v5, amended, meta, terminator,
narrative). Codes are assigned first come, first served (design 0.2 section 1); the
declaration codes by the same assign() over the 49 names with a fresh used set, a
namespace of their own. IML registers nothing of its own.

Usage:
  python tools/derive_registry.py            derive and write both registry files
  python tools/derive_registry.py --check    derive again and compare with both files (CI)
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
REGISTRY_05_PATH = ROOT / "registry" / "iml-registry-0.5.json"

IML_VERSION = "0.2"
IML_VERSION_05 = "0.5"
# design 0.5 section 2: the declaration classes in table order, with their counts
DECL_CLASSES = [("v3", 14), ("v4", 8), ("v5", 9), ("amended", 1), ("meta", 3), ("terminator", 1), ("narrative", 13)]
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


RE_DECL_LIST_LINE = re.compile(r"^(`::[A-Z][A-Z0-9_]*`\s*)+$")
RE_DECL_TOKEN = re.compile(r"`::([A-Z][A-Z0-9_]*)`")
RE_BOLD_HEADING = re.compile(r"^\*\*(.+?)\*\*\s*$")
RE_HEADING_COUNT = re.compile(r"\((\d+)\)")
# design 0.5 section 2: the bold headings of PATCH-2 1.5, in table order, and their classes
DECL_HEADINGS = [("v3.0 communication layer", "v3"), ("v4.0 execution layer", "v4"),
                 ("v5.0 judgment layer", "v5"), ("Registered by amendment", "amended"),
                 ("Meta (spec-authoring) declarations", "meta")]


def decl_lists(lines):
    """[(bold heading or None, [names])] for every run of consecutive lines made only of
    backticked `::NAME` tokens (a list may wrap onto several lines). The heading is the
    last bold line seen before the run."""
    out, heading, run = [], None, None
    for line in lines:
        s = line.strip()
        m = RE_BOLD_HEADING.match(s)
        if m:
            heading = m.group(1)
        if RE_DECL_LIST_LINE.match(s):
            if run is None:
                run = []
                out.append((heading, run))
            run.extend(RE_DECL_TOKEN.findall(s))
        else:
            run = None
    return out


def parse_declarations(patch2, spec):
    """The declaration sets of PATCH-2 1.5 and 1.6, the double-brace narratives of
    SPEC.md 7.1 and the prose-body types of PATCH-2 1.2 B6. Returns (classes, double,
    prose, tolerated) where classes is [(class, [names])] in table order."""
    s15 = section(patch2, "### §1.5 ", ["### §1.6 "])
    classes = []
    lists = decl_lists(s15)
    for title, cls in DECL_HEADINGS:
        found = [(h, names) for h, names in lists if h and h.startswith(title)]
        if len(found) != 1:
            fail("PATCH-2 1.5: %d lists under a bold heading starting %r, expected 1" % (len(found), title))
        heading, names = found[0]
        m = RE_HEADING_COUNT.search(heading)
        if not m or int(m.group(1)) != len(names):
            fail("PATCH-2 1.5: heading %r announces %s names, the list has %d"
                 % (heading, m.group(1) if m else "no count", len(names)))
        classes.append((cls, names))
    term = [re.match(r"^`::([A-Z][A-Z0-9_]*)` is a block terminator, not a declaration", l.strip())
            for l in s15]
    term = [m.group(1) for m in term if m]
    if len(term) != 1:
        fail("PATCH-2 1.5: %d `::X` is a block terminator sentences, expected 1" % len(term))
    classes.insert(5, ("terminator", term))
    s16 = section(patch2, "### §1.6 ", ["### §1.7 "])
    narrative = [n for _, names in decl_lists(s16) for n in names]
    m = RE_HEADING_COUNT.search(s16[0])
    if not m or int(m.group(1)) != len(narrative):
        fail("PATCH-2 1.6: heading %r does not announce the %d listed names" % (s16[0], len(narrative)))
    classes.append(("narrative", narrative))
    tol = [re.match(r"^`::([A-Z][A-Z0-9_]*)` and `::([A-Z][A-Z0-9_]*)` appear as annotation lines", l.strip())
           for l in s16]
    tol = [m.groups() for m in tol if m]
    if len(tol) != 1:
        fail("PATCH-2 1.6: %d LATENCY/CONFIDENCE sentences, expected 1" % len(tol))
    tolerated = list(tol[0])
    s71 = section(spec, "### 7.1 ", ["### 7.2 "])
    double = []
    for line in s71:
        m = re.match(r"^::([A-Z][A-Z0-9_]*)\{[^{}]*\}\{", line.strip())
        if m:
            double.append(m.group(1))
    b6 = [l for l in section(patch2, "::BODY{B6|", ["::BODY{B7|"]) if "current_prose_body_types=" in l]
    if len(b6) != 1:
        fail("PATCH-2 1.2 B6: %d current_prose_body_types lines, expected 1" % len(b6))
    m = re.search(r"current_prose_body_types=\[([^\]]*)\]", b6[0])
    if not m:
        fail("PATCH-2 1.2 B6: current_prose_body_types has no [...] list")
    prose = [re.match(r"^::([A-Z][A-Z0-9]*(?:_[A-Z0-9]+)*)", item.strip()).group(1)
             for item in m.group(1).split(",")]
    return classes, double, prose, tolerated


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


VALIDATOR_DECL_SETS = {"v3": "REGISTRY_V3", "v4": "REGISTRY_V4", "v5": "REGISTRY_V5", "amended": "REGISTRY_AMEND",
                       "meta": "META_DECLS", "terminator": "TERMINATORS", "narrative": "DECL_NARRATIVE"}


def derive_declarations():
    """The declarations table and the tolerated annotations of the 0.5 registry."""
    classes, double, prose, tolerated = parse_declarations(canon_text("archive/SPEC-v5.0-PATCH-2.md"),
                                                           canon_text("SPEC.md"))
    names = [n for _, ns in classes for n in ns]
    unique(names, "declarations")
    unique(double + prose + tolerated, "declaration flags")
    counts = [(cls, len(ns)) for cls, ns in classes]
    if counts != DECL_CLASSES:
        fail("declaration counts %s, expected %s" % (counts, DECL_CLASSES))
    if (len(double), len(prose), len(tolerated)) != (6, 5, 2):
        fail("double %d, prose %d, tolerated %d; expected 6, 5, 2" % (len(double), len(prose), len(tolerated)))
    narrative = dict(classes)["narrative"]
    if not set(double) <= set(narrative):
        fail("double-brace forms %s are not all narrative declarations" % sorted(set(double) - set(narrative)))
    if not set(prose) <= set(names):
        fail("prose-body types %s are not all declarations" % sorted(set(prose) - set(names)))
    if set(tolerated) & set(names):
        fail("tolerated annotations %s are registered declarations" % sorted(set(tolerated) & set(names)))
    ns = load_validator_constants()
    for cls, ns_names in classes:
        crosscheck("declarations " + cls, ns_names, ns[VALIDATOR_DECL_SETS[cls]])
    crosscheck("double-brace narratives", double, ns["NARR_DOUBLE"])
    crosscheck("prose-body types", prose, ns["PROSE_BODY"])
    crosscheck("tolerated annotations", tolerated, ns["TOLERATED_ANNOT"])
    codes = assign(names, set())
    table = [{"name": n, "code": codes[n], "class": cls, "double": n in double, "prose": n in prose}
             for cls, ns_names in classes for n in ns_names]
    return table, tolerated


def derive_both():
    """(the 0.2 chain registry, the 0.5 registry). The 0.5 registry carries the same chain
    tables and canon pin under iml_version 0.5, plus declarations and tolerated_annotations."""
    reg02 = derive()
    declarations, tolerated = derive_declarations()
    reg05 = {k: v for k, v in reg02.items() if k != "digest"}
    reg05["iml_version"] = IML_VERSION_05
    reg05["declarations"] = declarations
    reg05["tolerated_annotations"] = tolerated
    reg05["digest"] = digest_of(reg05)
    return reg02, reg05


def serialize(reg):
    return (json.dumps(reg, sort_keys=True, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def print_tables(reg):
    print("ROOTS %d" % sum(1 for v in reg["verbs"] if v["root"]))
    print(" ".join("%s=%s" % (v["name"], v["root"] or "-") for v in reg["verbs"]))
    print("KEYS %d" % len(reg["keys"]))
    print(" ".join("%s=%s" % (k["name"], k["code"]) for k in reg["keys"]))
    print("MARKS %d" % len(reg["entities"]))
    print(" ".join("%s=%s" % (e["name"], e["mark"]) for e in reg["entities"]))
    if "declarations" in reg:
        print("DECLARATIONS %d" % len(reg["declarations"]))
        print(" ".join("%s=%s" % (d["name"], d["code"]) for d in reg["declarations"]))
        print("TOLERATED " + " ".join(reg["tolerated_annotations"]))
    print("DIGEST " + reg["digest"])


def main(argv=None):
    p = argparse.ArgumentParser(description="derive the IML registries (0.2 chain registry, 0.5 registry) from canon/")
    p.add_argument("--check", action="store_true", help="re-derive and compare with both registry files")
    p.add_argument("--tables", action="store_true", help="print name=code tables")
    a = p.parse_args(argv)
    try:
        reg02, reg05 = derive_both()
    except DeriveError as e:
        print("derive_registry: ABORT: %s" % e, file=sys.stderr)
        return 1
    files = [(REGISTRY_PATH, reg02), (REGISTRY_05_PATH, reg05)]
    if a.tables:
        print_tables(reg05)
        print("DIGEST 0.2 " + reg02["digest"])
        return 0
    if a.check:
        bad = 0
        for path, reg in files:
            if not path.exists():
                print("derive_registry: %s is missing" % path, file=sys.stderr)
                bad += 1
            elif path.read_bytes() != serialize(reg):
                print("derive_registry: %s differs from a fresh derivation" % path, file=sys.stderr)
                bad += 1
        if bad:
            return 1
        print("registry ok: %s digest %s; %s digest %s" % (REGISTRY_PATH.name, reg02["digest"],
                                                           REGISTRY_05_PATH.name, reg05["digest"]))
        return 0
    for path, reg in files:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(serialize(reg))
        print("wrote %s (digest %s)" % (path.relative_to(ROOT).as_posix(), reg["digest"]))
    return 0


if __name__ == "__main__":
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass
    sys.exit(main())
