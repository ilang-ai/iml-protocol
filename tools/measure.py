#!/usr/bin/env python3
"""Measure the golden corpora and write measurements/0.5-YYYY-MM-DD.md
(SPEC-IML-0.5.md section 8).

Corpora:
  corpus/golden/       the 72 chains of 0.2 and 0.3, unchanged since 0.2, measured under the
                       0.5 header; the same texts under the 0.4 header and the 0.2 surface
                       stand alongside as the record.
  corpus/golden-0.4/   the 36 chains of 0.4 (NNN pairs; sources that may span several
                       lines), measured under the 0.5 header; the 0.4 message on disk
                       (NNN.iml) stands alongside as the record. doc-01 is not measured here.
  corpus/golden-0.5/   the I-Lang documents of 0.5 (NNN.ilang with NNN.iml).

Forms, per chain:
  I-Lang               the canonical print of the parsed chain (print_L2); a source written on
                       several lines prints on one
  IML 0.5 message      the compiled message, header included (one header per chain)
  IML chain line       the chain alone, as it stands on one line of a document
  JSON                 one compact JSON mapping of the same AST, used as the baseline and
                       stated as such: {"c":[{"v":VERB,"t":"@TARGET","r":VERBREF,"m":{key:value}}]}
                       with "t", "r" and "m" omitted when absent, entity references written
                       "@NAME", every other value written as its content string
  IML 0.4 message      the record: the same chain text under the 0.4 header (for golden-0.4,
                       the NNN.iml file as it stands on disk, without its final newline)
  IML 0.2 message      (the 72 only) the record: the 0.2 surface, written with the codec's
                       internal version="0.2" argument
And once per chain corpus: the IML 0.5 document (the header alone on the first line, then
the chains one per line, measured as one text) and the 0.4 record document.

Forms, per document of corpus/golden-0.5/:
  I-Lang as written    the NNN.ilang file as it stands on disk (final newline included)
  I-Lang canonical     print_doc of the parsed document, with one final newline
  IML 0.5 document     the NNN.iml file as it stands on disk (final newline included); it is
                       compile_doc of the parsed document plus one newline, checked here

Units: bytes (UTF-8), characters (code points), tokens under the tiktoken encodings
cl100k_base and o200k_base. The encodings are named encodings and nothing else; they are
not any vendor's billing. tiktoken is optional: when it cannot be imported or an encoding
cannot be loaded, the token columns are left out and the document says so.

Also measured: RULE-SHEET.md as it stands on disk when the tool runs (its first line is
quoted), with the 0.4, 0.3 and 0.2 sheets' figures copied from the earlier reports as the
record. Not measured: the reply; the codec makes no model calls.

Usage: python tools/measure.py [--date YYYY-MM-DD] [--out PATH] [--note TEXT]
"""

import argparse
import datetime
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from iml import (Decl, Text, compile, compile_doc, compile_document, decompile, decompile_doc,  # noqa: E402
                 default_registry, parse_doc, print_doc, print_L2)
from iml.__main__ import join_chain_lines, parse_chain  # noqa: E402

GOLDEN = ROOT / "corpus" / "golden"
GOLDEN_04 = ROOT / "corpus" / "golden-0.4"
GOLDEN_05 = ROOT / "corpus" / "golden-0.5"
RULE_SHEET = ROOT / "RULE-SHEET.md"
ENCODINGS = ["cl100k_base", "o200k_base"]
ILANG, MSG, LINE, JSON_FORM, MSG_04, MSG_02 = ("I-Lang", "IML 0.5 message", "IML chain line", "JSON",
                                               "IML 0.4 message", "IML 0.2 message")
DOC, DOC_04 = "IML 0.5 document", "IML 0.4 document"
SRC, PRINT, IMLDOC = "I-Lang as written", "I-Lang canonical", "IML 0.5 document"
FORMS_72 = [ILANG, MSG, LINE, JSON_FORM, MSG_04, MSG_02]
FORMS_04 = [ILANG, MSG, LINE, JSON_FORM, MSG_04]
FORMS_05 = [SRC, PRINT, IMLDOC]
ROW_LABEL = {
    ILANG: "I-Lang canonical print",
    MSG: "IML 0.5 message (one header per chain)",
    DOC: "IML 0.5 document (one header for the %d chains)",
    JSON_FORM: "JSON baseline",
    MSG_04: "IML 0.4 message (record)",
    DOC_04: "IML 0.4 document (record)",
    MSG_02: "IML 0.2 message (record)",
}
# The earlier rule sheets, from measurements/0.4-2026-09-18.md, 0.3-2026-09-18.md and 0.2-2026-09-18.md.
RULE_SHEET_RECORDS = [
    ("RULE-SHEET.md (0.4.1, record)", {"bytes": 6090, "chars": 6064, "cl100k_base": 1798, "o200k_base": 1796},
     "measurements/0.4-2026-09-18.md"),
    ("RULE-SHEET.md (0.3, record)", {"bytes": 5782, "chars": 5748, "cl100k_base": 1792, "o200k_base": 1794},
     "measurements/0.3-2026-09-18.md"),
    ("RULE-SHEET.md (0.2, record)", {"bytes": 5242, "chars": 5184, "cl100k_base": 1607, "o200k_base": 1599},
     "measurements/0.2-2026-09-18.md"),
]
REPLY_NOTE = "Reply cost: not measured in 0.5, the codec makes no model calls"


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
                m[k] = "@" + v.text if v.kind == "entity" else ("~" + v.text if v.kind == "code" else v.text)
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


def read_sources(directory):
    """[(stem, source text without its final newline, AST)] for the NNN.ilang chain files,
    the source joined as the command line joins it (continuation lines)."""
    out = []
    for path in sorted(directory.glob("[0-9][0-9][0-9].ilang")):
        src = path.read_text(encoding="utf-8").rstrip("\n")
        chains = join_chain_lines(src)
        assert len(chains) == 1, path
        out.append((path.stem, src, parse_chain(chains[0][1])))
    return out


def under(text, reg, version):
    """The same text under the header of an earlier version (the chain digest)."""
    head = reg.header
    assert text.startswith(head)
    return reg.header_for(version) + text[len(head):]


def measure_chains(items, encs, units, forms, reg, iml04=None):
    """Per chain rows and totals; iml04 maps a stem to its 0.4 message on disk (golden-0.4)."""
    rows = []
    for stem, src, ast in items:
        message = compile(ast)
        texts = {ILANG: print_L2(ast), MSG: message, LINE: message.split(" ", 1)[1], JSON_FORM: json_form(ast)}
        if MSG_04 in forms:
            texts[MSG_04] = iml04[stem] if iml04 else under(message, reg, "0.4")
            assert texts[MSG_04] == under(message, reg, "0.4") and decompile(texts[MSG_04]) == ast, stem
        if MSG_02 in forms:
            texts[MSG_02] = compile(ast, version="0.2")
        rows.append((stem, {f: measure(texts[f], encs) for f in forms}))
    asts = [ast for _, _, ast in items]
    document = compile_document(asts)
    assert decompile(document) == asts
    totals = {f: {u: sum(r[f][u] for _, r in rows) for u in units} for f in forms}
    totals[DOC] = measure(document, encs)
    totals[DOC_04] = measure(under(document, reg, "0.4"), encs)
    return rows, totals


def walk(items):
    for it in items:
        yield it
        if isinstance(it, Decl):
            yield from walk(it.body)


def measure_documents(encs, units):
    """Per document rows, totals and the composition of corpus/golden-0.5/."""
    rows, comp = [], {"items": 0, "chains": 0, "decls": 0, "nested": 0, "texts": 0, "body_texts": 0,
                      "lines_src": 0, "lines_print": 0, "lines_iml": 0}
    for path in sorted(GOLDEN_05.glob("[0-9][0-9][0-9].ilang")):
        src = path.read_text(encoding="utf-8")
        iml = path.with_suffix(".iml").read_text(encoding="utf-8")
        items = parse_doc(src)
        assert compile_doc(items) + "\n" == iml and decompile_doc(iml) == items, path
        printed = print_doc(items) + "\n"
        rows.append((path.stem, {SRC: measure(src, encs), PRINT: measure(printed, encs), IMLDOC: measure(iml, encs)}))
        every = list(walk(items))
        comp["items"] += len(items)
        comp["chains"] += sum(1 for x in every if not isinstance(x, (Decl, Text)))
        comp["decls"] += sum(1 for x in every if isinstance(x, Decl))
        comp["nested"] += sum(1 for d in every if isinstance(d, Decl) for b in d.body if isinstance(b, Decl))
        comp["texts"] += sum(1 for x in items if isinstance(x, Text))
        comp["body_texts"] += sum(1 for x in every if isinstance(x, Text)) - sum(1 for x in items if isinstance(x, Text))
        comp["lines_src"] += src.count("\n")
        comp["lines_print"] += printed.count("\n")
        comp["lines_iml"] += iml.count("\n")
    totals = {f: {u: sum(r[f][u] for _, r in rows) for u in units} for f in FORMS_05}
    return rows, totals, comp


def per_table(lines, title, forms, rows, units):
    lines.append("## " + title)
    lines.append("")
    lines.append("| id | " + " | ".join("%s %s" % (f, u) for f in forms for u in units) + " |")
    lines.append("|----|" + "|".join("---:" for _ in forms for _ in units) + "|")
    for stem, r in rows:
        lines.append("| %s | " % stem + " | ".join(str(r[f][u]) for f in forms for u in units) + " |")
    lines.append("")


def main(argv=None):
    p = argparse.ArgumentParser(description="measure the golden corpora in their forms")
    p.add_argument("--date", default=datetime.date.today().isoformat())
    p.add_argument("--out", default=None)
    p.add_argument("--note", default=None, help="one sentence written under the title, e.g. why the report was regenerated")
    a = p.parse_args(argv)
    out = Path(a.out).resolve() if a.out else ROOT / "measurements" / ("0.5-%s.md" % a.date)
    reg = default_registry()
    encs, notes = load_tokenizers()
    units = ["bytes", "chars"] + list(encs)
    items72, items04 = read_sources(GOLDEN), read_sources(GOLDEN_04)
    iml04 = {stem: (GOLDEN_04 / (stem + ".iml")).read_text(encoding="utf-8").rstrip("\n") for stem, _, _ in items04}
    rows72, totals72 = measure_chains(items72, encs, units, FORMS_72, reg)
    rows04, totals04 = measure_chains(items04, encs, units, FORMS_04, reg, iml04)
    rows05, totals05, comp = measure_documents(encs, units)
    n72, n04, n05 = len(items72), len(items04), len(rows05)
    h05, h04 = measure(reg.header, encs), measure(reg.header_for("0.4"), encs)
    L = []
    L += ["# IML 0.5 measurement, %s" % a.date, ""]
    if a.note:
        L += [a.note, ""]
    L.append("Corpora: the %d documents of `corpus/golden-0.5/`, the %d golden chains of `corpus/golden/` (unchanged"
             " since 0.2) and the %d golden chains of `corpus/golden-0.4/`. Registry `registry/iml-registry-0.5.json`,"
             " digest `%s` (the 0.5 header); chain registry `registry/iml-registry-0.2.json`, digest `%s` (the 0.4 and"
             " 0.2 records); canon commit `%s`." % (n05, n72, n04, reg.digest[:12], reg.chain_digest[:12], reg.commit[:12]))
    L += ["Python %s. %s." % (sys.version.split()[0], "; ".join(notes) if notes else "no tokenizer notes"), ""]
    L.append("Units: bytes (UTF-8), characters (code points)"
             + (", tokens under the named tiktoken encodings %s" % ", ".join("`%s`" % e for e in encs) if encs else "")
             + ". Tokenizer scope: the named encodings, not any vendor's billing."
             + (" Tokens were not measured: %s." % "; ".join(x for x in notes if "not measured" in x or "absent" in x)
                if len(encs) < len(ENCODINGS) else ""))
    L.append("")
    L.append("Forms, per document of `corpus/golden-0.5/`: **I-Lang as written** is the `.ilang` file as it stands on"
             " disk, final newline included (blank lines, `---` lines, indentation and trailing whitespace are layout and"
             " counted here); **I-Lang canonical** is `print_doc` of the parsed document with one final newline;"
             " **IML 0.5 document** is the `.iml` file as it stands on disk, final newline included, which equals"
             " `compile_doc` of the parsed document plus one newline (checked when this report ran).")
    L.append("")
    L.append("Forms, per chain: **I-Lang** is the canonical print (`print_L2`); **IML 0.5 message** is the compiled"
             " message including its header `%s ` (one header per chain); **IML chain line** is the chain as it stands"
             " on one line of a document; **JSON** is the one JSON mapping used as baseline, stated here:"
             ' `{"c":[{"v":VERB,"t":"@TARGET","r":VERBREF,"m":{key:value}}]}` compact with no spaces, `t`, `r` and `m`'
             ' omitted when absent, entity references as `"@NAME"`, every other value as its content string. Per chain'
             " corpus: **IML 0.5 document** is the header alone on the first line and then the chains, one per line,"
             " measured as one text. The records: **IML 0.4 message** and **IML 0.4 document**, the same texts under the"
             " 0.4 header `%s ` (for `corpus/golden-0.4/` the message is the `.iml` file on disk, which is that text),"
             " and **IML 0.2 message** (the 72 chains only), the 0.2 surface, header `%s `."
             % (reg.header, reg.header_for("0.4"), reg.header_for("0.2")))
    L += ["", "No figure below carries a claim of any kind; the table is the table (ROADMAP gate: efficiency claim).", ""]
    L += [REPLY_NOTE + " (ROADMAP item 13 lists the reply; it is counted when a model reads IML, not here).", ""]
    L += ["## Headers", ""]
    table(L, "header", units, [("`%s`" % reg.header, [h05[u] for u in units]),
                                ("`%s` (record)" % reg.header_for("0.4"), [h04[u] for u in units])])
    L += ["", "The 0.5 header differs from the 0.4 header in the version digit and in its 12 hex characters, the 0.5"
          " registry's digest. A message carries the header once per chain, a document once.", ""]
    L += ["## The %d documents of `corpus/golden-0.5/`" % n05, "", "### Totals over %d documents" % n05, ""]
    rows = [(f, [totals05[f][u] for u in units]) for f in FORMS_05]
    table(L, "form", units, rows)
    L += ["", "Composition: %d items at top level (%d text lines), %d declarations of which %d nested, %d chains"
          " (top level and in bodies), %d text lines in bodies. Lines: %d as written, %d in the canonical print, %d in"
          " the IML documents (the header line included)."
          % (comp["items"], comp["texts"], comp["decls"], comp["nested"], comp["chains"], comp["body_texts"],
             comp["lines_src"], comp["lines_print"], comp["lines_iml"]), ""]
    L += ["### Means per document, %d documents" % n05, ""]
    table(L, "form", units, [(label, [fmt_mean(t, n05) for t in cells]) for label, cells in rows])
    L.append("")
    for title, n, totals, forms in (("`corpus/golden/`", n72, totals72, FORMS_72), ("`corpus/golden-0.4/`", n04, totals04, FORMS_04)):
        L += ["## The %d chains of %s" % (n, title), "", "### Totals over %d chains" % n, ""]
        order = [ILANG, MSG, DOC, JSON_FORM, MSG_04, DOC_04] + ([MSG_02] if MSG_02 in forms else [])
        rows = [((ROW_LABEL[f] % n) if f == DOC else ROW_LABEL[f], [totals[f][u] for u in units]) for f in order]
        table(L, "form", units, rows)
        differ = [u for u in units if totals[MSG][u] != totals[MSG_04][u] or totals[DOC][u] != totals[DOC_04][u]]
        L += ["", "The 0.5 and 0.4 texts of these chains differ in the header only; %s." % (
            "the counts differ under %s" % ", ".join("`%s`" % u for u in differ) if differ
            else "every count is the same under every unit"), ""]
        L += ["### Means per chain, %d chains" % n, ""]
        table(L, "form", units, [(label, [fmt_mean(t, n) for t in cells]) for label, cells in rows])
        L.append("")
    L += ["## Rule sheet", ""]
    if RULE_SHEET.exists():
        text = RULE_SHEET.read_text(encoding="utf-8")
        r = measure(text, encs)
        L += ["`RULE-SHEET.md` as it stood on disk when this measurement ran, first line `%s`, same units; the earlier"
              " sheets' figures are copied from %s as the record:" % (text.split("\n", 1)[0].strip(),
                                                                    ", ".join("`%s`" % x[2] for x in RULE_SHEET_RECORDS)), ""]
        table(L, "file", units, [("RULE-SHEET.md (as on disk)", [r[u] for u in units])]
              + [(label, [rec.get(u, "-") for u in units]) for label, rec, _ in RULE_SHEET_RECORDS])
    else:
        L.append("`RULE-SHEET.md` was not present when this measurement ran.")
    L.append("")
    per_table(L, "Per document, `corpus/golden-0.5/`", FORMS_05, rows05, units)
    per_table(L, "Per chain, `corpus/golden/`", FORMS_72, rows72, units)
    per_table(L, "Per chain, `corpus/golden-0.4/`", FORMS_04, rows04, units)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(("\n".join(L).rstrip("\n") + "\n").encode("utf-8"))
    try:
        shown = out.relative_to(ROOT)
    except ValueError:            # --out points outside the repository
        shown = out
    print("wrote %s" % shown)
    for label, totals in (("corpus/golden-0.5 (%d documents)" % n05, totals05), ("corpus/golden (%d chains)" % n72, totals72),
                          ("corpus/golden-0.4 (%d chains)" % n04, totals04)):
        print(label)
        for f in totals:
            print("  %-20s " % f + "  ".join("%s=%d" % (u, totals[f][u]) for u in units))
    print(REPLY_NOTE)
    return 0


if __name__ == "__main__":
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass
    sys.exit(main())
