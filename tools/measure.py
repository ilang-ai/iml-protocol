#!/usr/bin/env python3
"""Measure the golden corpus and write measurements/0.3-YYYY-MM-DD.md
(SPEC-IML-0.3.md section 8).

Forms, per golden chain:
  I-Lang               the canonical print of the parsed chain (print_L2)
  IML 0.3 message      the compiled message, header included (one header per chain)
  IML 0.3 chain line   the chain alone, as it stands on one line of a document
  JSON                 one compact JSON mapping of the same AST, used as the baseline and
                       stated as such: {"c":[{"v":VERB,"t":"@TARGET","m":{key:value}}]}
                       with "t" and "m" omitted when absent, entity references written
                       "@NAME", every other value written as its content string
                       (lexemes kept: 007 stays "007")
  IML 0.2 message      the 0.2 surface of the same chain, written with the codec's
                       internal version="0.2" argument, kept alongside as the record
And once for the whole corpus:
  IML 0.3 document     the header alone on the first line, then the chains one per line,
                       measured as one text (the header is paid once)
Units: bytes (UTF-8), characters (code points), tokens under the tiktoken encodings
cl100k_base and o200k_base. The encodings are named encodings and nothing else; they
are not any vendor's billing. tiktoken is optional: when it cannot be imported or an
encoding cannot be loaded (offline cache missing), the token columns are left out and
the document says so.

Also measured: RULE-SHEET.md at the repository root, when it exists, with the 0.2 rule
sheet's figures copied from measurements/0.2-2026-09-18.md as the record. Not measured:
the reply. The codec makes no model calls, so there is no reply to measure; the report
says so.

Usage: python tools/measure.py [--date YYYY-MM-DD] [--out PATH] [--note TEXT]
"""

import argparse
import datetime
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from iml import compile, compile_document, decompile, default_registry, parse_L2, print_L2  # noqa: E402

GOLDEN = ROOT / "corpus" / "golden"
RULE_SHEET = ROOT / "RULE-SHEET.md"
ENCODINGS = ["cl100k_base", "o200k_base"]
FORMS = ["I-Lang", "IML 0.3 message", "IML 0.3 chain line", "JSON", "IML 0.2 message"]
DOCUMENT = "IML 0.3 document"
TOTAL_ROWS = ["I-Lang", "IML 0.3 message", DOCUMENT, "JSON", "IML 0.2 message"]
ROW_LABEL = {
    "I-Lang": "I-Lang canonical print",
    "IML 0.3 message": "IML 0.3 message (one header per chain)",
    DOCUMENT: "IML 0.3 document (one header for the 72 chains)",
    "JSON": "JSON baseline",
    "IML 0.2 message": "IML 0.2 message (record)",
}
# The 0.2 rule sheet, from measurements/0.2-2026-09-18.md (0.2.1 regeneration).
RULE_SHEET_02_RECORD = {"bytes": 5242, "chars": 5184, "cl100k_base": 1607, "o200k_base": 1599}
RULE_SHEET_02_SOURCE = "measurements/0.2-2026-09-18.md"
REPLY_NOTE = "Reply cost: not measured in 0.3, the codec makes no model calls"


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


def table(lines, head, units, rows):
    lines.append("| %s | " % head + " | ".join(units) + " |")
    lines.append("|------|" + "|".join("---:" for _ in units) + "|")
    for label, cells in rows:
        lines.append("| %s | " % label + " | ".join(str(c) for c in cells) + " |")


def main(argv=None):
    p = argparse.ArgumentParser(description="measure the golden corpus in four forms")
    p.add_argument("--date", default=datetime.date.today().isoformat())
    p.add_argument("--out", default=None)
    p.add_argument("--note", default=None, help="one sentence written under the title, e.g. why the report was regenerated")
    a = p.parse_args(argv)
    out = Path(a.out).resolve() if a.out else ROOT / "measurements" / ("0.3-%s.md" % a.date)

    reg = default_registry()
    encs, notes = load_tokenizers()
    units = ["bytes", "chars"] + list(encs)

    rows = []
    asts = []
    for path in sorted(GOLDEN.glob("*.ilang")):
        src = path.read_text(encoding="utf-8").rstrip("\n")
        ast = parse_L2(src)
        asts.append(ast)
        message = compile(ast)
        forms = {
            "I-Lang": print_L2(ast),
            "IML 0.3 message": message,
            "IML 0.3 chain line": message.split(" ", 1)[1],
            "JSON": json_form(ast),
            "IML 0.2 message": compile(ast, version="0.2"),
        }
        rows.append((path.stem, {f: measure(t, encs) for f, t in forms.items()}))
    n = len(rows)
    document = compile_document(asts)
    assert decompile(document) == asts
    totals = {f: {u: sum(r[f][u] for _, r in rows) for u in units} for f in FORMS}
    totals[DOCUMENT] = measure(document, encs)
    header_line = measure(reg.header, encs)

    lines = []
    lines.append("# IML 0.3 measurement, %s" % a.date)
    lines.append("")
    if a.note:
        lines.append(a.note)
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
    lines.append("Forms: **I-Lang** is the canonical print (`print_L2`). **IML 0.3 message** is the compiled message"
                 " including its header `%s ` (one header per chain). **IML 0.3 document** is the header alone on the"
                 " first line and then the %d chains, one per line, measured as one text (the header is paid once);"
                 " in the per-chain table the column *IML 0.3 chain line* is each chain as it stands on its line of the"
                 " document, without the header. **JSON** is the one JSON mapping used as baseline, stated here:"
                 ' `{"c":[{"v":VERB,"t":"@TARGET","m":{key:value}}]}` compact with no spaces, `t` and `m` omitted'
                 ' when absent, entity references as `"@NAME"`, every other value as its content string.'
                 " **IML 0.2 message** is the same chain on the 0.2 surface (header `%s `), written with the codec's"
                 " internal `version=\"0.2\"` argument and kept alongside as the record." % (reg.header, n, reg.header_for("0.2")))
    lines.append("")
    lines.append("No figure below carries a claim of any kind; the table is the table (ROADMAP gate: efficiency claim).")
    lines.append("")
    lines.append(REPLY_NOTE + " (ROADMAP item 13 lists the reply; it is counted when a model reads IML, not here).")
    lines.append("")
    lines.append("## Totals over %d chains" % n)
    lines.append("")
    table(lines, "form", units, [(ROW_LABEL[f], [totals[f][u] for u in units]) for f in TOTAL_ROWS])
    lines.append("")
    lines.append("The document is %d lines: the header line `%s` (%s) and %d chain lines; its total is the header"
                 " line, %d newlines and the chain lines measured together, so it is not the sum of the chain-line"
                 " column (a tokenizer may merge a newline with its neighbours)."
                 % (n + 1, reg.header, ", ".join("%d %s" % (header_line[u], u) for u in units), n, n))
    lines.append("")
    lines.append("## Means per chain")
    lines.append("")
    table(lines, "form", units, [(ROW_LABEL[f], [fmt_mean(totals[f][u], n) for u in units]) for f in TOTAL_ROWS])
    lines.append("")
    lines.append("## Rule sheet")
    lines.append("")
    if RULE_SHEET.exists():
        text = RULE_SHEET.read_text(encoding="utf-8")
        r = measure(text, encs)
        lines.append("`RULE-SHEET.md` (the text a model is given before it reads IML), same units; the 0.2 sheet's"
                     " figures are copied from `%s` as the record:" % RULE_SHEET_02_SOURCE)
        lines.append("")
        table(lines, "file", units, [
            ("RULE-SHEET.md (0.3)", [r[u] for u in units]),
            ("RULE-SHEET.md (0.2, record)", [RULE_SHEET_02_RECORD.get(u, "-") for u in units]),
        ])
    else:
        lines.append("`RULE-SHEET.md` was not present when this measurement ran; the rule sheet is still to be"
                     " measured. Re-run `python tools/measure.py` once it exists.")
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
    try:
        shown = out.relative_to(ROOT)
    except ValueError:            # --out points outside the repository
        shown = out
    print("wrote %s" % shown)
    for f in TOTAL_ROWS:
        print("%-20s " % f + "  ".join("%s=%d" % (u, totals[f][u]) for u in units))
    print(REPLY_NOTE)
    return 0


if __name__ == "__main__":
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass
    sys.exit(main())
