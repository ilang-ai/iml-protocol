#!/usr/bin/env python3
"""Measure the golden corpus in three forms and write measurements/0.2-YYYY-MM-DD.md
(design 0.2 section 8).

Forms, per golden chain:
  I-Lang   the canonical print of the parsed chain (print_L2)
  IML      the compiled message, header included
  JSON     one compact JSON mapping of the same AST, used as the baseline and stated as
           such: {"c":[{"v":VERB,"t":"@TARGET","m":{key:value}}]} with "t" and "m"
           omitted when absent, entity references written "@NAME", every other value
           written as its content string (lexemes kept: 007 stays "007").
Units: bytes (UTF-8), characters (code points), tokens under the tiktoken encodings
cl100k_base and o200k_base. The encodings are named encodings and nothing else; they
are not any vendor's billing. tiktoken is optional: when it cannot be imported or an
encoding cannot be loaded (offline cache missing), the token columns are left out and
the document says so.

Also measured: RULE-SHEET.md at the repository root, when it exists.

Usage: python tools/measure.py [--date YYYY-MM-DD] [--out PATH]
"""

import argparse
import datetime
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from iml import compile, default_registry, parse_L2, print_L2  # noqa: E402

GOLDEN = ROOT / "corpus" / "golden"
RULE_SHEET = ROOT / "RULE-SHEET.md"
ENCODINGS = ["cl100k_base", "o200k_base"]
FORMS = ["I-Lang", "IML", "JSON"]


def json_form(chain):
    ops = []
    for op in chain.ops:
        o = {"v": op.verb}
        if op.target is not None:
            o["t"] = "@" + op.target
        if op.mods:
            m = {}
            for k, v in op.mods:
                if v.kind == "entity":
                    m[k] = "@" + v.text
                elif v.kind == "code":
                    m[k] = "~" + v.text
                else:
                    m[k] = v.text
            o["m"] = m
        ops.append(o)
    return json.dumps({"c": ops}, ensure_ascii=False, separators=(",", ":"))


def load_tokenizers():
    """Return ({name: encoder}, [notes]). Missing pieces are reported, never faked."""
    notes = []
    try:
        import tiktoken
    except Exception as e:  # ImportError or a broken install
        return {}, ["tiktoken could not be imported (%s: %s); tokens were not measured" % (type(e).__name__, e)]
    notes.append("tiktoken %s" % getattr(tiktoken, "__version__", "unknown"))
    encs = {}
    for name in ENCODINGS:
        try:
            encs[name] = tiktoken.get_encoding(name)
        except Exception as e:
            notes.append("encoding %s could not be loaded (%s: %s); its column is absent" % (name, type(e).__name__, e))
    return encs, notes


def measure(text, encs):
    row = {"bytes": len(text.encode("utf-8")), "chars": len(text)}
    for name, enc in encs.items():
        row[name] = len(enc.encode(text, disallowed_special=()))
    return row


def fmt_mean(total, n):
    return "%.2f" % (total / n) if n else "-"


def main(argv=None):
    p = argparse.ArgumentParser(description="measure the golden corpus in three forms")
    p.add_argument("--date", default=datetime.date.today().isoformat())
    p.add_argument("--out", default=None)
    a = p.parse_args(argv)
    out = Path(a.out) if a.out else ROOT / "measurements" / ("0.2-%s.md" % a.date)

    reg = default_registry()
    encs, notes = load_tokenizers()
    units = ["bytes", "chars"] + list(encs)

    rows = []
    for path in sorted(GOLDEN.glob("*.ilang")):
        src = path.read_text(encoding="utf-8").rstrip("\n")
        ast = parse_L2(src)
        forms = {"I-Lang": print_L2(ast), "IML": compile(ast), "JSON": json_form(ast)}
        rows.append((path.stem, {f: measure(t, encs) for f, t in forms.items()}))
    n = len(rows)
    totals = {f: {u: sum(r[f][u] for _, r in rows) for u in units} for f in FORMS}

    lines = []
    lines.append("# IML 0.2 measurement, %s" % a.date)
    lines.append("")
    lines.append("Corpus: the %d golden chains in `corpus/golden/` (registry digest `%s`, canon commit `%s`)."
                 % (n, reg.digest[:12], reg.commit[:12]))
    lines.append("Python %s. %s." % (sys.version.split()[0], "; ".join(notes) if notes else "no tokenizer notes"))
    lines.append("")
    lines.append("Units: bytes (UTF-8), characters (code points)"
                 + (", tokens under the named tiktoken encodings %s" % ", ".join("`%s`" % e for e in encs) if encs else "")
                 + ". Tokenizer scope: the named encodings, not any vendor's billing."
                 + (" Tokens were not measured: %s." % "; ".join(x for x in notes if "not measured" in x or "absent" in x)
                    if len(encs) < len(ENCODINGS) else ""))
    lines.append("")
    lines.append("Forms: **I-Lang** is the canonical print (`print_L2`); **IML** is the compiled message including its"
                 " header `%s `; **JSON** is the one JSON mapping used as baseline, stated here:"
                 ' `{"c":[{"v":VERB,"t":"@TARGET","m":{key:value}}]}` compact with no spaces, `t` and `m` omitted'
                 ' when absent, entity references as `"@NAME"`, every other value as its content string.' % reg.header)
    lines.append("")
    lines.append("No figure below is called a saving; the table is the table (ROADMAP gate: efficiency claim).")
    lines.append("")
    lines.append("## Totals over %d chains" % n)
    lines.append("")
    lines.append("| form | " + " | ".join(units) + " |")
    lines.append("|------|" + "|".join("---:" for _ in units) + "|")
    for f in FORMS:
        lines.append("| %s | " % f + " | ".join(str(totals[f][u]) for u in units) + " |")
    lines.append("")
    lines.append("## Means per chain")
    lines.append("")
    lines.append("| form | " + " | ".join(units) + " |")
    lines.append("|------|" + "|".join("---:" for _ in units) + "|")
    for f in FORMS:
        lines.append("| %s | " % f + " | ".join(fmt_mean(totals[f][u], n) for u in units) + " |")
    lines.append("")
    lines.append("## Rule sheet")
    lines.append("")
    if RULE_SHEET.exists():
        text = RULE_SHEET.read_text(encoding="utf-8")
        r = measure(text, encs)
        lines.append("`RULE-SHEET.md` (the text a model is given before it reads IML), same units:")
        lines.append("")
        lines.append("| file | " + " | ".join(units) + " |")
        lines.append("|------|" + "|".join("---:" for _ in units) + "|")
        lines.append("| RULE-SHEET.md | " + " | ".join(str(r[u]) for u in units) + " |")
    else:
        lines.append("`RULE-SHEET.md` was not present when this measurement ran; the rule sheet is still to be"
                     " measured (规则卡待测). Re-run `python tools/measure.py` once it exists.")
    lines.append("")
    lines.append("## Per chain")
    lines.append("")
    head = "| id | " + " | ".join("%s %s" % (f, u) for f in FORMS for u in units) + " |"
    lines.append(head)
    lines.append("|----|" + "|".join("---:" for _ in FORMS for _ in units) + "|")
    for stem, r in rows:
        lines.append("| %s | " % stem + " | ".join(str(r[f][u]) for f in FORMS for u in units) + " |")
    lines.append("")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(("\n".join(lines) + "\n").encode("utf-8"))
    print("wrote %s" % out.relative_to(ROOT))
    for f in FORMS:
        print("%-7s " % f + "  ".join("%s=%d" % (u, totals[f][u]) for u in units))
    return 0


if __name__ == "__main__":
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass
    sys.exit(main())
