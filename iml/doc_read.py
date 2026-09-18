"""decompile_doc: IML document text to the document AST (SPEC-IML-0.5.md sections 2 and 4;
the grammar is in iml.doc_codec). read_document is also what iml.codec.decompile calls for
the document form, under a 0.5 header and under a 0.4 or 0.3 one (chains only there).
"""

from .codec import RE_HEADER, _check_version_and_digest, _scan_chain, scan_quoted, surface
from .doc_ast import Decl, Text
from .doc_codec import RE_DCODE, RE_NAME, check_canonical
from .doc_lex import RE_DELIMITER
from .errors import IMLError
from .registry import DOCUMENT_LAYER_VERSIONS, HEADER_VERSION, default_registry

QUOTE = '"'


class _Builder:
    """A declaration while its lines are read."""
    __slots__ = ("name", "sub", "prefix", "addr", "shape", "head", "body", "lines", "nested")

    def __init__(self, name, sub, prefix, addr, shape, head):
        self.name, self.sub, self.prefix, self.addr, self.shape, self.head = name, sub, prefix, addr, shape, head
        self.body, self.lines, self.nested = [], [], None

    def finish(self):
        body = [b.finish() if isinstance(b, _Builder) else b for b in self.body]
        return Decl(self.name, self.sub, self.prefix, self.addr, self.shape, self.head, body, self.lines)


def decompile_doc(text, registry=None):
    """IML document text -> list of items (Chain, Decl, Text). The header stands alone on
    the first line: a 0.5 header reads the whole document layer, a 0.4 or 0.3 header
    (digest 88d05d0839c1) chains only. A message is E502 here (decompile reads it)."""
    reg = registry or default_registry()
    sf = surface(HEADER_VERSION)
    if not isinstance(text, str) or not text.startswith("#iml/"):
        raise IMLError("E502", "no IML header (`%s` expected)" % reg.header_for(sf.version), 0)
    nl = text.find("\n")
    line_end = len(text) if nl < 0 else nl
    if nl >= 0 and line_end > 0 and text[line_end - 1] == "\r":
        line_end -= 1
    m = RE_HEADER.match(text, 0, line_end)
    if not m:
        raise IMLError("E300", "bad header shape: `#iml/<digits>.<digits>/<12 lowercase hex>` alone on the first"
                       " line expected", len("#iml/"))
    _check_version_and_digest(m, reg, sf)
    if m.group(3) == " ":
        raise IMLError("E502", "a message, not a document: decompile_doc reads the header alone on its first line"
                       " (decompile reads a message)", m.end() - 1)
    if nl < 0:
        raise IMLError("E300", "header alone: a document carries at least one item line after the header", len(text))
    return read_document(text, nl, m.group(1), reg, sf)


def read_document(text, nl, version, reg, sf):
    """The lines after a document header; text[nl] ends the header line."""
    full = version in DOCUMENT_LAYER_VERSIONS
    items, offsets = [], []
    cur = None
    length, start = len(text), nl + 1
    while start < length:
        nl2 = text.find("\n", start)
        end = length if nl2 < 0 else nl2
        seg_end = end - 1 if (nl2 >= 0 and end > start and text[end - 1] == "\r") else end
        if seg_end == start:
            raise IMLError("E300", "blank line in a document", start)
        if text.startswith("#iml/", start):
            raise IMLError("E502", "a second header in a document (one header, then one item per line)", start)
        c = text[start]
        if not full:
            if c == QUOTE or c == ":":
                raise IMLError("E502", "declarations and text lines need a 0.5 header (this document's header"
                               " is version %s)" % version, start)
            items.append(_scan_chain(text, start, seg_end, reg, sf))
            offsets.append(start)
        elif c == QUOTE:
            t, k = read_q(text, start, seg_end, "a text line")
            at_end(k, seg_end)
            items.append(Text(t))
            offsets.append(start)
            cur = None
        elif c == ":":
            cur = read_decl_line(text, start, seg_end, reg, nested=False)
            items.append(cur)
            offsets.append(start)
        elif c == " ":
            if cur is None:
                raise IMLError("E300", "a line that starts with a space belongs to the declaration above it:"
                               " there is none", start)
            read_dline(text, start, seg_end, cur, reg, sf)
        elif c == "$" or "A" <= c <= "Z" or "0" <= c <= "9":
            items.append(_scan_chain(text, start, seg_end, reg, sf))
            offsets.append(start)
            cur = None
        else:
            raise IMLError("E300", "a document line may not start with %r: `#` the header, a verb root or `$` a"
                           " chain, a quote a text line, `:` a declaration, a space a line of the declaration"
                           " above" % c, start)
        if nl2 < 0:
            break
        start = nl2 + 1
    if not items:
        raise IMLError("E300", "a document carries at least one item line after the header", nl)
    for x, off in zip(items, offsets):
        if isinstance(x, _Builder) and x.shape == "wrapped" and not x.lines:
            raise IMLError("E300", "a wrapped ::%s carries at least its closing line (a line after the header)"
                           % x.name, off)
    items = [x.finish() if isinstance(x, _Builder) else x for x in items]
    if full:
        check_canonical(items, reg, offsets)
    return items


def at_end(k, end):
    if k != end:
        raise IMLError("E300", "text after the quoted text on its line", k)


def read_q(text, j, end, what):
    """A QUOTED at text[j]; E300 when it holds a newline escape."""
    if j >= end or text[j] != QUOTE:
        raise IMLError("E300", "%s is written quoted" % what, j)
    content, k = scan_quoted(text, j, what, end)
    if "\n" in content:
        raise IMLError("E300", "a newline (the escape \\n) inside %s: a text never holds one" % what, j)
    return content, k


def read_decl_line(text, i, end, reg, nested):
    """`:` DCODE prefix? sub? form, at text[i] == ":"."""
    code = text[i + 1:min(i + 3, end)]
    if not RE_DCODE.fullmatch(code):
        raise IMLError("E300", "a declaration code [A-Z0-9]{2} expected after `:` (seen %r)" % code, i + 1)
    name = reg.code_decl.get(code)
    if name is None:
        raise IMLError("E300", "unknown declaration code %r" % code, i + 1)
    j = i + 3
    sub = prefix = addr = None
    if j < end and text[j] == "T":           # the prefix comes before the sub (a NAME would swallow its `T`)
        if nested:
            raise IMLError("E300", "a nested declaration takes no temporal prefix", j)
        prefix, j = read_q(text, j + 1, end, "a temporal prefix")
    if text.startswith("::", j):
        m = RE_NAME.match(text, j + 2, end)
        if not m:
            raise IMLError("E300", "a name [A-Z][A-Z0-9_]* expected after `::`", j + 2)
        if name != "MODULE":
            raise IMLError("E300", "::%s::%s: only ::MODULE takes a two-segment name (§1.7)" % (name, m.group(0)), j)
        sub, j = m.group(0), m.end()
    if name in reg.double:
        if j >= end or text[j] != QUOTE:
            raise IMLError("E300", "::%s is a double-brace narrative: its addressing text comes first, quoted" % name, j)
        addr, j = read_q(text, j, end, "an addressing text")
    if j < end and text[j] == "{":
        if nested:
            raise IMLError("E300", "a nested declaration takes the brace form: no span", j)
        j += 1
        if j == end:
            shape, head = "set", ""
        else:
            shape = "wrapped"
            head, j = read_q(text, j, end, "a declaration header")
    else:
        head, j = read_q(text, j, end, "a declaration header")
        opaque = not nested and name == "UNTRUSTED" and RE_DELIMITER.search("{" + head + "}")
        shape = "opaque" if opaque else "brace"
    if j != end:
        raise IMLError("E300", "text after the declaration header", j)
    return _Builder(name, sub, prefix, addr, shape, head)


def read_dline(text, start, end, cur, reg, sf):
    """One line that starts with a space, for the declaration cur."""
    i = start + 1
    if i >= end:
        raise IMLError("E300", "a declaration line carries a text, a chain or a nested declaration after its space", i)
    c = text[i]
    if cur.shape != "brace":
        t, k = read_q(text, i, end, "an opaque line" if cur.shape == "opaque" else "a content line")
        at_end(k, end)
        cur.lines.append(t)
    elif c == QUOTE:
        t, k = read_q(text, i, end, "a body line")
        at_end(k, end)
        cur.body.append(Text(t))
        cur.nested = None
    elif c == ":":
        cur.nested = read_decl_line(text, i, end, reg, nested=True)
        cur.body.append(cur.nested)
    elif c == " ":
        if cur.nested is None:
            raise IMLError("E300", "a line that starts with two spaces is a body line of the nested declaration"
                           " just above it: there is none", start)
        t, k = read_q(text, i + 1, end, "a nested body line")
        at_end(k, end)
        cur.nested.body.append(Text(t))
    elif c == "$" or "A" <= c <= "Z" or "0" <= c <= "9":
        cur.body.append(_scan_chain(text, i, end, reg, sf))
        cur.nested = None
    else:
        raise IMLError("E300", "a declaration line may not continue with %r after its space" % c, i)
