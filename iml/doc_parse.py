"""parse_doc: a raw I-Lang document to the document AST (SPEC-IML-0.5.md section 4).

Every document is read as the pinned validator reads a raw document (lint_region,
parse_construct, consume_brace_span, consume_opaque; PATCH-2 section 1), with or without
the `::ILANG::` marker, and fails closed with the validator's wording where it has one.
Lines are split on `\\n` and one `\\r` before it is dropped. A raw control character is
E300 anywhere except a TAB in layout (indentation, trailing whitespace, and the whitespace
the validator strips: between a temporal prefix and `::`, between a declaration name and
its `{`, between a closing brace and a trailing body token); a TAB inside carried text is
E300, and a line carried as a text keeps the whitespace inside it as content, so a TAB
there is E300 too (`T[0]`, a TAB and `::LATENCY{0}`). A U+FEFF at the head of the input
is E502 (the command line drops every leading one). Two readings are IML's own
(SPEC-IML-0.5.md section 9.1), because the canonical print would read back otherwise: with
a same-line trailing body token the full-width check also runs on the braces alone, and a
one-operation chain in preamble position whose print is a tag line is E300.

parse_doc returns a list of items (Chain, Decl, Text). parse_doc_lines also returns the
chains with the numbers of their first lines, for the command line's roundtrip report, and
the first line number of every top-level item, at which the command line reports an error
of the canonical check that names that item.
"""

from .codec import is_control
from .doc_ast import Decl, Text
from .doc_body import _BodyReader, indent_of
from .doc_lex import (MSG_BOM, MSG_BRACKET_LINE, MSG_CONTROL, MSG_DOUBLE, MSG_ENTITY, MSG_FULLWIDTH_TRAILING,
                      MSG_LACKS_BRACE, MSG_MALFORMED_HEADER, MSG_MALFORMED_MARKER, MSG_MARKER_POSITION,
                      MSG_NO_PRODUCTION, MSG_OPAQUE_OPEN, MSG_OPAQUE_TRAILING, MSG_ORPHAN, MSG_PREAMBLE_CHAIN,
                      MSG_SET_HEADER, MSG_SPAN_OPEN, MSG_TWO_SEGMENTS, MSG_UNREGISTERED, RE_BAD_DECL_HEAD,
                      RE_DECL_HEAD, RE_DELIMITER, RE_DOC_MARKER, RE_DOUBLE_INLINE, RE_DOUBLE_SPAN, RE_TAG_LINE,
                      RE_TEMPORAL_BIND, RE_TEMPORAL_NOTE, RE_TEMPORAL_PREFIX, STRUCTURAL_CHARS, bad_entity,
                      find_close, fullwidth_message, is_operation_line, is_tag_line, mask_quoted)
from .errors import IMLError
from .l2 import print_L2
from .registry import default_registry

NESTABLE_CLASSES = ("v3", "v4", "v5", "amended", "narrative")   # the validator's DECL_STRUCTURAL | DECL_NARRATIVE


def parse_doc(text, registry=None):
    """I-Lang document text -> list of items (Chain, Decl, Text)."""
    return DocParser(text, registry).parse()


def parse_doc_lines(text, registry=None):
    """(items, [(first line number, Chain)] for every chain of the document, top level and
    body, in document order, [first line number of every top-level item]); line numbers
    are 1-based."""
    p = DocParser(text, registry)
    items = p.parse()
    return items, p.chain_lines, p.item_lines


class DocParser(_BodyReader):
    def __init__(self, text, registry=None):
        self.reg = reg = registry or default_registry()
        if not reg.has_declarations:
            raise ValueError("registry %s carries no declarations table: the document layer needs the 0.5 registry"
                             % reg.version)
        if not isinstance(text, str):
            raise IMLError("E300", "a document is text", 0)
        if text.startswith("\ufeff"):
            raise IMLError("E502", MSG_BOM, 0)
        self.verbs = frozenset(reg.verbs) | frozenset(reg.aliases)
        self.registered = frozenset(reg.declarations)
        self.nestable = frozenset(d for d in reg.declarations if reg.decl_class[d] in NESTABLE_CLASSES)
        self.tolerated = frozenset(reg.tolerated)
        self.double, self.prose = reg.double, reg.prose
        self.lines, self.starts = [], []
        pos = 0
        for seg in text.split("\n"):
            line = seg[:-1] if seg.endswith("\r") else seg
            for k, c in enumerate(line):
                if c != "\t" and is_control(c):
                    raise IMLError("E300", MSG_CONTROL % (ord(c), "a document line"), pos + k)
            self.lines.append(line)
            self.starts.append(pos)
            pos += len(seg) + 1
        self.chain_lines = []
        self.item_lines = []
        self.body_op_seen = False

    # ------------------------------------------------------------ helpers
    def line_off(self, i):
        return self.starts[i] + indent_of(self.lines[i])

    def check_carried(self, piece, what, off):
        """E300 for a TAB (or any control character) inside a carried text."""
        for k, c in enumerate(piece):
            if is_control(c):
                line_i = max(j for j in range(len(self.starts)) if self.starts[j] <= off)
                at = self.lines[line_i].find(piece, off - self.starts[line_i]) if piece else -1
                raise IMLError("E300", MSG_CONTROL % (ord(c), what),
                               (self.starts[line_i] + at + k) if at >= 0 else off)

    def text(self, s, off):
        self.check_carried(s, "a text line", off)
        return Text(s)

    def check_entities(self, s, off):
        bad = bad_entity(s)
        if bad:
            raise IMLError("E300", MSG_ENTITY % bad[1], off + bad[0])

    # ------------------------------------------------------------ top level
    def parse(self):
        lines, n = self.lines, len(self.lines)
        nonblank = [j for j in range(n) if lines[j].strip()]
        first_nb = nonblank[0] if nonblank else -1
        last_nb = nonblank[-1] if nonblank else -1
        items = []
        seen_construct = in_preamble = False
        i = 0
        while i < n:
            s = lines[i].strip()
            off = self.line_off(i)
            if not s or s == "---":
                i += 1
                continue
            self.item_lines.append(i + 1)         # every other line opens one item or raises
            if RE_DOC_MARKER.match(s):
                if i == first_nb:
                    in_preamble = True
                elif i != last_nb:
                    raise IMLError("E300", MSG_MARKER_POSITION, off)
                items.append(self.text(s, off))
                i += 1
                continue
            if RE_TEMPORAL_BIND.match(s):
                items.append(self.text(s, off))
                i += 1
                continue
            in_preamble_here, in_preamble = in_preamble, False
            if s.startswith("::") or RE_TEMPORAL_PREFIX.match(s):
                seen_construct = True
                item, i = self.construct(i)
                items.append(item)
                continue
            if s.startswith("=>"):
                raise IMLError("E300", MSG_ORPHAN, off)
            if s.startswith("["):
                ms = mask_quoted(s)
                if in_preamble_here and is_tag_line(s):
                    in_preamble = True            # a preamble tag line: metadata, even when TAG is a verb name
                    items.append(self.text(s, off))
                    i += 1
                    continue
                if is_operation_line(s, self.verbs):
                    seen_construct = True
                    chain, j = self.join_chain(i, s, None)
                    if in_preamble_here and len(chain.ops) == 1 and is_tag_line(print_L2(chain)):
                        # `[Σ]`, `[Π:READ]`: the print, `[MERGE]`, `[BATC:READ]`, would read back as a tag line
                        raise IMLError("E300", MSG_PREAMBLE_CHAIN, off)
                    items.append(chain)
                    i = j
                    continue
                if RE_TAG_LINE.match(ms):
                    items.append(self.text(s, off))
                    i += 1
                    continue
                raise IMLError("E300", MSG_BRACKET_LINE % s[:60], off)
            if (RE_TEMPORAL_NOTE.match(s) or s.startswith("→") or s.startswith("<<<")
                    or (not seen_construct and not any(c in s for c in STRUCTURAL_CHARS))):
                items.append(self.text(s, off))
                i += 1
                continue
            raise IMLError("E300", MSG_NO_PRODUCTION % s[:60], off)
        return items

    # ------------------------------------------------------------ one construct
    def construct(self, i):
        """The `::` construct at line i, optionally behind a temporal prefix. Returns (item,
        next line index)."""
        line = self.lines[i]
        stripped = line.strip()
        header_indent = indent_of(line)
        off = self.starts[i] + header_indent
        pm = RE_TEMPORAL_PREFIX.match(stripped)
        decl_text = pm.group(2) if pm else stripped
        base = off + (pm.start(2) if pm else 0)
        prefix = pm.group(1)[2:-1] if pm else None
        m = RE_DECL_HEAD.match(decl_text)
        if not m:
            bad = RE_BAD_DECL_HEAD.match(decl_text)
            raise IMLError("E300", MSG_MALFORMED_HEADER % (bad.group(0) if bad else decl_text)[:60], off)
        name, sub, rest = m.group(1), m.group(2), m.group(3)
        if name == "ILANG":
            if not RE_DOC_MARKER.match(decl_text):
                raise IMLError("E300", MSG_MALFORMED_MARKER % decl_text[:60], off)
            return self.text(stripped, off), i + 1      # a marker behind a temporal prefix: the validator passes it
        if sub and name != "MODULE":
            raise IMLError("E300", MSG_TWO_SEGMENTS % (name, sub), off)
        if name not in self.registered:
            if name in self.tolerated:
                return self.text(stripped, off), i + 1  # ::LATENCY, ::CONFIDENCE (PATCH-2 1.6)
            raise IMLError("E300", MSG_UNREGISTERED % name, off)
        self.check_entities(decl_text, base)
        rest = rest.strip() if rest else ""
        rest_off = base + decl_text.rindex(rest) if rest else base
        if not rest.startswith("{"):
            raise IMLError("E300", MSG_LACKS_BRACE % name, off)
        fw = fullwidth_message(rest)
        if fw:
            raise IMLError("E300", fw, rest_off)
        if prefix is not None:
            self.check_carried(prefix, "a temporal prefix", off)
        if name in self.double:
            c1 = rest.find("}")
            if RE_DOUBLE_INLINE.match(rest):
                addr, head = rest[1:c1], rest[c1 + 2:-1]
                self.check_carried(addr, "the addressing of ::%s" % name, rest_off)
                self.check_carried(head, "the header of ::%s" % name, rest_off)
                body, j = self.read_body(i, name, header_indent, "", off)
                return Decl(name, sub, prefix, addr, "brace", head, body), j
            if RE_DOUBLE_SPAN.match(rest):
                return self.span(i, name, sub, prefix, rest[1:c1], rest[c1 + 2:], rest_off)
            raise IMLError("E300", MSG_DOUBLE % name, off)
        if rest.count("{") - rest.count("}") > 0:
            return self.span(i, name, sub, prefix, None, rest[1:], rest_off)
        close = find_close(rest)
        head, trailing = rest[1:close], rest[close + 1:].strip()
        self.check_carried(head, "the header of ::%s" % name, rest_off)
        if trailing:
            # the validator checks the whole rest, where an ASCII colon of the token can hide a
            # full-width one of the braces; the print moves the token to a body line
            fw = fullwidth_message("{" + head + "}")
            if fw:
                raise IMLError("E300", fw + MSG_FULLWIDTH_TRAILING, rest_off)
        dm = RE_DELIMITER.search(rest) if name == "UNTRUSTED" else None
        if dm:
            if trailing:
                raise IMLError("E300", MSG_OPAQUE_TRAILING, off)
            lines, j = self.opaque(i + 1, dm.group(1), off)
            return Decl(name, sub, prefix, None, "opaque", head, (), lines), j
        trailing_off = self.starts[i] + len(line.rstrip()) - len(trailing)
        body, j = self.read_body(i, name, header_indent, trailing, trailing_off)
        return Decl(name, sub, prefix, None, "brace", head, body), j

    def span(self, i, name, sub, prefix, addr, after, rest_off):
        """A brace span (PATCH-2 1.1 brace_span): after is the text after the opening brace
        (the second brace for a double-brace narrative). A set span (the header line ends
        with `{`) is closed by a line that is exactly `}`; a wrapped field header by the
        first line ending with `}`."""
        # the validator: a set span when the header line ends with `{` (nothing after the
        # opening brace, or text ending in `{`); IML carries the first only
        wrapped = not (after == "" or after.endswith("{"))
        if not wrapped and after != "":
            raise IMLError("E300", MSG_SET_HEADER % name, rest_off)
        if addr is not None:
            self.check_carried(addr, "the addressing of ::%s" % name, rest_off)
        head = after if wrapped else ""
        self.check_carried(head, "the header of ::%s" % name, rest_off)
        lines, n = self.lines, len(self.lines)
        content, j = [], i + 1
        while j < n:
            t = lines[j].strip()
            if t == "}" or (wrapped and t.endswith("}")):
                if wrapped:
                    content.append(t[:-1])
                    self.check_carried(t[:-1], "a span line", self.line_off(j))
                return Decl(name, sub, prefix, addr, "wrapped" if wrapped else "set", head, (), content), j + 1
            if t:
                self.check_carried(t, "a span line", self.line_off(j))
                content.append(t)
            j += 1
        raise IMLError("E300", MSG_SPAN_OPEN % name, self.line_off(i))

    def opaque(self, j, delimiter, off):
        """Opaque lines, verbatim, up to the line whose stripped text is the delimiter
        (consume_opaque). A block with no delimiter line is E300 in IML; the validator
        consumes to the end of the document."""
        out, n = [], len(self.lines)
        while j < n:
            if self.lines[j].strip() == delimiter:
                return out, j + 1
            self.check_carried(self.lines[j], "an opaque line", self.starts[j])
            out.append(self.lines[j])
            j += 1
        raise IMLError("E300", MSG_OPAQUE_OPEN % delimiter, off)
