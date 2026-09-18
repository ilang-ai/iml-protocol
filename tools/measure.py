#!/usr/bin/env python3
"""Measure the golden corpora and write measurements/0.4-YYYY-MM-DD.md
(SPEC-IML-0.4.md section 8).

Corpora:
  corpus/golden/       the 72 chains of 0.2 and 0.3, unchanged in 0.4. Their 0.4 message is
                       the 0.3 record under the 0.4 header, so the report measures both
                       texts and states whether any count differs.
  corpus/golden-0.4/   the chains of 0.4 (NNN pairs: verb references, sources that may span
                       several lines); doc-01, the document pair, is measured as it stands
                       on disk.

Forms, per golden chain:
  I-Lang               the canonical print of the parsed chain (print_L2); a source written
                       on several lines prints on one
  IML 0.4 message      the compiled message, header included (one header per chain)
  IML 0.4 chain line   the chain alone, as it stands on one line of a document
  JSON                 one compact JSON mapping of the same AST, used as the baseline and
                       stated as such: {"c":[{"v":VERB,"t":"@TARGET","r":VERBREF,"m":{key:value}}]}
                       with "t", "r" and "m" omitted when absent, entity references written
                       "@NAME", every other value written as its content string
                       (lexemes kept: 007 stays "007")
  IML 0.3 message      (the 72 only) the 0.3 record: the same text under the 0.3 header
  IML 0.2 message      (the 72 only) the 0.2 surface of the same chain, written with the
                       codec's internal version="0.2" argument, kept alongside as the
                       record; a verb reference has no 0.2 spelling, so the 0.4 corpus has
                       no 0.2 column
And once per corpus:
  IML 0.4 document     the header alone on the first line, then the chains one per line,
                       measured as one text (the header is paid once); for the 72 also the
                       0.3 document, the same text under the 0.3 header
Units: bytes (UTF-8), characters (code points), tokens under the tiktoken encodings
cl100k_base and o200k_base. The encodings are named encodings and nothing else; they
are not any vendor's billing. tiktoken is optional: when it cannot be imported or an
encoding cannot be loaded (offline cache missing), the token columns are left out and
the document says so.

Also measured: RULE-SHEET.md at the repository root as it stands on disk when the tool
runs (its first line is quoted, so the reader knows which sheet was measured), with the
0.3 and 0.2 sheets' figures copied from the earlier reports as the record. Not measured:
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

from iml import compile, compile_document, decompile, default_registry, print_L2  # noqa: E402
from iml.__main__ import join_chain_lines, parse_chain  # noqa: E402

GOLDEN = ROOT / "corpus" / "golden"
GOLDEN_04 = ROOT / "corpus" / "golden-0.4"
RULE_SHEET = ROOT / "RULE-SHEET.md"
ENCODINGS = ["cl100k_base", "o200k_base"]
ILANG, MSG, LINE, JSON_FORM, MSG_03, MSG_02 = ("I-Lang", "IML 0.4 message", "IML 0.4 chain line", "JSON",
                                              "IML 0.3 message", "IML 0.2 message")
DOC, DOC_03 = "IML 0.4 document", "IML 0.3 document"
FORMS_72 = [ILANG, MSG, LINE, JSON_FORM, MSG_03, MSG_02]
FORMS_04 = [ILANG, MSG, LINE, JSON_FORM]
ROW_LABEL = {
    ILANG: "I-Lang canonical print",
    MSG: "IML 0.4 message (one header per chain)",
    DOC: "IML 0.4 document (one header for the %d chains)",
    JSON_FORM: "JSON baseline",
    MSG_03: "IML 0.3 message (record: the same text under the 0.3 header)",
    DOC_03: "IML 0.3 document (record: the same text under the 0.3 header)",
    MSG_02: "IML 0.2 message (record)",
}
# The earlier rule sheets, from measurements/0.3-2026-09-18.md and measurements/0.2-2026-09-18.md.
RULE_SHEET_RECORDS = [
    ("RULE-SHEET.md (0.3, record)", {"bytes": 5782, "chars": 5748, "cl100k_base": 1792, "o200k_base": 1794},
     "measurements/0.3-2026-09-18.md"),
    ("RULE-SHEET.md (0.2, record)", {"bytes": 5242, "chars": 5184, "cl100k_base": 1607, "o200k_base": 1599},
     "measurements/0.2-2026-09-18.md"),
]
REPLY_NOTE = "Reply cost: not measured in 0.4, the codec makes no model calls"


def json_form(chain):
    ops = []
    for op in chain.ops:
        o = {"v": op.verb}
        if op.target is not None:
            o["t"] = "@" + op.target
        if op.verbref is not None:
            o["r"] = op.verbref
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


def units_of(row, units):
    return ", ".join("%d %s" % (row[u], u) for u in units)


def table(lines, head, units, rows):
    lines.append("| %s | " % head + " | ".join(units) + " |")
    lines.append("|------|" + "|".join("---:" for _ in units) + "|")
    for label, cells in rows:
        lines.append("| %s | " % label + " | ".join(str(c) for c in cells) + " |")


def to03(text04):
    """The same text under the 0.3 header (the record form of a 0.4 text without a verb reference)."""
    assert text04.startswith("#iml/0.4/")
    return "#iml/0.3/" + text04[len("#iml/0.4/"):]


def read_sources(directory):
    """[(stem, source text without its final newline, AST)] for the NNN.ilang files, the
    source joined as the command line joins it (continuation lines)."""
    out = []
    for path in sorted(directory.glob("[0-9][0-9][0-9].ilang")):
        src = path.read_text(encoding="utf-8").rstrip("\n")
        chains = join_chain_lines(src)
        assert len(chains) == 1, path
        out.append((path.stem, src, parse_chain(chains[0][1])))
    return out


def measure_corpus(items, encs, units, forms, with_records):
    rows = []
    for stem, src, ast in items:
        message = compile(ast)
        texts = {ILANG: print_L2(ast), MSG: message, LINE: message.split(" ", 1)[1], JSON_FORM: json_form(ast)}
        if with_records:
            texts[MSG_03] = to03(message)
            texts[MSG_02] = compile(ast, version="0.2")
        rows.append((stem, {f: measure(texts[f], encs) for f in forms}))
    asts = [ast for _, _, ast in items]
    document = compile_document(asts)
    assert decompile(document) == asts
    totals = {f: {u: sum(r[f][u] for _, r in rows) for u in units} for f in forms}
    totals[DOC] = measure(document, encs)
    if with_records:
        assert decompile(to03(document)) == asts
        totals[DOC_03] = measure(to03(document), encs)
    return rows, totals, document


def main(argv=None):
    p = argparse.ArgumentParser(description="measure the golden corpora in their forms")
    p.add_argument("--date", default=datetime.date.today().isoformat())
    p.add_argument("--out", default=None)
    p.add_argument("--note", default=None, help="one sentence written under the title, e.g. why the report was regenerated")
    a = p.parse_args(argv)
    out = Path(a.out).resolve() if a.out else ROOT / "measurements" / ("0.4-%s.md" % a.date)

    reg = default_registry()
    encs, notes = load_tokenizers()
    units = ["bytes", "chars"] + list(encs)

    items72 = read_sources(GOLDEN)
    items04 = read_sources(GOLDEN_04)
    n72, n04 = len(items72), len(items04)
    rows72, totals72, document72 = measure_corpus(items72, encs, units, FORMS_72, True)
    rows04, totals04, document04 = measure_corpus(items04, encs, units, FORMS_04, False)
    header_line = measure(reg.header, encs)
    multi_line = sum(1 for _, src, _ in items04 if "\n" in src)
    refs = sum(1 for _, _, ast in items04 for op in ast.ops if op.verbref is not None)
    doc01_path = GOLDEN_04 / "doc-01.iml"
    doc01 = doc01_path.read_text(encoding="utf-8").rstrip("\n") if doc01_path.exists() else None
    if doc01 is not None:
        doc01_chains = decompile(doc01)
        doc01_row = measure(doc01, encs)

    same = {}
    for u in units:
        same[u] = (totals72[MSG][u] == totals72[MSG_03][u], totals72[DOC][u] == totals72[DOC_03][u])
    differing = [u for u in units if not all(same[u])]

    lines = []
    lines.append("# IML 0.4 measurement, %s" % a.date)
    lines.append("")
    if a.note:
        lines.append(a.note)
        lines.append("")
    lines.append("Corpora: the %d golden chains in `corpus/golden/` (unchanged since 0.2) and the %d golden chains"
                 " in `corpus/golden-0.4/` (registry digest `%s`, canon commit `%s`)."
                 % (n72, n04, reg.digest[:12], reg.commit[:12]))
    lines.append("Python %s. %s." % (sys.version.split()[0], "; ".join(notes) if notes else "no tokenizer notes"))
    lines.append("")
    lines.append("Units: bytes (UTF-8), characters (code points)"
                 + (", tokens under the named tiktoken encodings %s" % ", ".join("`%s`" % e for e in encs) if encs else "")
                 + ". Tokenizer scope: the named encodings, not any vendor's billing."
                 + (" Tokens were not measured: %s." % "; ".join(x for x in notes if "not measured" in x or "absent" in x)
                    if len(encs) < len(ENCODINGS) else ""))
    lines.append("")
    lines.append("Forms: **I-Lang** is the canonical print (`print_L2`); a source written on several lines"
                 " (continuation lines starting with `=>`) prints on one line, and the source layout is not measured."
                 " **IML 0.4 message** is the compiled message including its header `%s ` (one header per chain)."
                 " **IML 0.4 document** is the header alone on the first line and then the chains, one per line,"
                 " measured as one text (the header is paid once); in the per-chain tables the column *IML 0.4 chain"
                 " line* is each chain as it stands on its line of the document, without the header. **JSON** is the"
                 " one JSON mapping used as baseline, stated here:"
                 ' `{"c":[{"v":VERB,"t":"@TARGET","r":VERBREF,"m":{key:value}}]}` compact with no spaces, `t`, `r`'
                 ' (the BATC verb reference, new in 0.4) and `m` omitted when absent, entity references as `"@NAME"`,'
                 " every other value as its content string. For the %d chains of `corpus/golden/` two records stand"
                 " alongside: **IML 0.3 message** and **IML 0.3 document**, the same texts under the 0.3 header"
                 " `%s ` (what 0.3 wrote for these chains, which carry no verb reference), and **IML 0.2 message**,"
                 " the 0.2 surface (header `%s `), written with the codec's internal `version=\"0.2\"` argument."
                 " A verb reference has no 0.2 spelling, so the 0.4 corpus has no 0.2 column."
                 % (reg.header, n72, reg.header_for("0.3"), reg.header_for("0.2")))
    lines.append("")
    lines.append("No figure below carries a claim of any kind; the table is the table (ROADMAP gate: efficiency claim).")
    lines.append("")
    lines.append(REPLY_NOTE + " (ROADMAP item 13 lists the reply; it is counted when a model reads IML, not here).")
    lines.append("")
    lines.append("## The %d chains of `corpus/golden/`" % n72)
    lines.append("")
    lines.append("### Totals over %d chains" % n72)
    lines.append("")
    rows = [(ROW_LABEL[ILANG], [totals72[ILANG][u] for u in units]),
            (ROW_LABEL[MSG], [totals72[MSG][u] for u in units]),
            (ROW_LABEL[DOC] % n72, [totals72[DOC][u] for u in units]),
            (ROW_LABEL[JSON_FORM], [totals72[JSON_FORM][u] for u in units]),
            (ROW_LABEL[MSG_03], [totals72[MSG_03][u] for u in units]),
            (ROW_LABEL[DOC_03], [totals72[DOC_03][u] for u in units]),
            (ROW_LABEL[MSG_02], [totals72[MSG_02][u] for u in units])]
    table(lines, "form", units, rows)
    lines.append("")
    lines.append("The document is %d lines: the header line `%s` (%s) and %d chain lines; its total is the header"
                 " line, %d newlines and the chain lines measured together, so it is not the sum of the chain-line"
                 " column (a tokenizer may merge a newline with its neighbours)."
                 % (n72 + 1, reg.header, units_of(header_line, units), n72, n72))
    lines.append("")
    if differing:
        lines.append("The 0.4 and 0.3 texts of these chains differ in the header digit only (`0.4` for `0.3`), and the"
                     " counts differ under %s: the message and document rows above give both."
                     % ", ".join("`%s`" % u for u in differing))
    else:
        lines.append("The 0.4 and 0.3 texts of these chains differ in the header digit only (`0.4` for `0.3`), and every"
                     " count above is the same for both: the 0.4 message and document rows repeat the 0.3 report's"
                     " figures for this corpus, under every unit.")
    lines.append("")
    lines.append("### Means per chain, %d chains" % n72)
    lines.append("")
    rows = [(label, [fmt_mean(total, n72) for total in cells]) for label, cells in rows]
    table(lines, "form", units, rows)
    lines.append("")
    lines.append("## The %d chains of `corpus/golden-0.4/`" % n04)
    lines.append("")
    lines.append("### Totals over %d chains" % n04)
    lines.append("")
    rows = [(ROW_LABEL[ILANG], [totals04[ILANG][u] for u in units]),
            (ROW_LABEL[MSG], [totals04[MSG][u] for u in units]),
            (ROW_LABEL[DOC] % n04, [totals04[DOC][u] for u in units]),
            (ROW_LABEL[JSON_FORM], [totals04[JSON_FORM][u] for u in units])]
    table(lines, "form", units, rows)
    lines.append("")
    lines.append("The document is %d lines (the header line and %d chain lines), measured as one text as above."
                 " %d of the %d sources are written on several lines and %d BATC verb references occur in the"
                 " corpus; the I-Lang row is the canonical one-line print of every chain."
                 % (n04 + 1, n04, multi_line, n04, refs))
    if doc01 is not None:
        lines.append("")
        lines.append("`corpus/golden-0.4/doc-01.iml`, the document pair (%d chains, %d lines), as it stands on disk"
                     " without its final newline: %s." % (len(doc01_chains), doc01.count("\n") + 1, units_of(doc01_row, units)))
    lines.append("")
    lines.append("### Means per chain, %d chains" % n04)
    lines.append("")
    rows = [(label, [fmt_mean(total, n04) for total in cells]) for label, cells in rows]
    table(lines, "form", units, rows)
    lines.append("")
    lines.append("## Rule sheet")
    lines.append("")
    if RULE_SHEET.exists():
        text = RULE_SHEET.read_text(encoding="utf-8")
        r = measure(text, encs)
        first = text.split("\n", 1)[0].strip()
        lines.append("`RULE-SHEET.md` (the text a model is given before it reads IML) as it stood on disk when this"
                     " measurement ran, first line `%s`, same units; the 0.3 and 0.2 sheets' figures are copied from"
                     " `%s` and `%s` as the record:" % (first, RULE_SHEET_RECORDS[0][2], RULE_SHEET_RECORDS[1][2]))
        lines.append("")
        table(lines, "file", units, [("RULE-SHEET.md (as on disk)", [r[u] for u in units])]
              + [(label, [record.get(u, "-") for u in units]) for label, record, _ in RULE_SHEET_RECORDS])
    else:
        lines.append("`RULE-SHEET.md` was not present when this measurement ran; the rule sheet is still to be"
                     " measured. Re-run `python tools/measure.py` once it exists.")
    lines.append("")
    for title, forms, rows_ in (("Per chain, `corpus/golden/`", FORMS_72, rows72),
                                ("Per chain, `corpus/golden-0.4/`", FORMS_04, rows04)):
        lines.append("## " + title)
        lines.append("")
        lines.append("| id | " + " | ".join("%s %s" % (f, u) for f in forms for u in units) + " |")
        lines.append("|----|" + "|".join("---:" for _ in forms for _ in units) + "|")
        for stem, r in rows_:
            lines.append("| %s | " % stem + " | ".join(str(r[f][u]) for f in forms for u in units) + " |")
        lines.append("")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(("\n".join(lines) + "\n").encode("utf-8"))
    try:
        shown = out.relative_to(ROOT)
    except ValueError:            # --out points outside the repository
        shown = out
    print("wrote %s" % shown)
    for label, totals, n in (("corpus/golden", totals72, n72), ("corpus/golden-0.4", totals04, n04)):
        print("%s (%d chains)" % (label, n))
        for f in totals:
            print("  %-18s " % f + "  ".join("%s=%d" % (u, totals[f][u]) for u in units))
    print(REPLY_NOTE)
    return 0


if __name__ == "__main__":
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass
    sys.exit(main())
