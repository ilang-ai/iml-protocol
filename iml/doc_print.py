"""print_doc: the canonical I-Lang print of a document AST (SPEC-IML-0.5.md section 5).

Items in order, one construct per line group, no `---`. A Text prints its text; a Chain
its 0.4 canonical print on one line; a Decl `[T[<prefix>] ]::NAME[::SUB]` and then:
  brace    `{head}` (`{addr}{head}` for a double-brace narrative), then its body lines
           indented two spaces: a Text, a chain on one line, a nested declaration at two
           spaces with its own body at four. A same-line trailing body token of the source
           prints as the first body line; a flush-left body prints indented.
  set      `{` (or `{addr}{`), the content lines at two spaces, `}` alone at the header's
           indent (column 0 at top level)
  wrapped  `{head` (or `{addr}{head`), the content lines at two spaces, the last one
           followed by `}`; when the last line's text is empty, a bare `}` at the
           header's indent
  opaque   `{head}`, the opaque lines verbatim (no indentation added), the delimiter alone

One blank line, and only there: between a top-level declaration of shape brace with an
empty body and a following top-level Text that is a body form (a tag line or a temporal
bind, PATCH-2 1.1 FLUSH-LEFT-BODY). Without it that line would bind as the declaration's
flush-left body on reading, and the print would not read back to the same AST.

The print does not validate: compile_doc and decompile_doc check that the print of an AST
reads back to that AST (iml.doc_codec).
"""

from .codec import Chain
from .doc_ast import Decl, Text
from .doc_lex import RE_DELIMITER, is_body_form
from .errors import IMLError
from .l2 import print_L2
from .registry import default_registry

INDENT = "  "


def print_doc(items, registry=None):
    """Document AST -> canonical I-Lang text, lines joined by `\\n`, no final newline."""
    return "\n".join(print_doc_lines(items, registry)[0])


def print_doc_lines(items, registry=None):
    """(lines, owner): the printed lines and, for each, the index of the item it belongs to
    (a separating blank line belongs to the item after it)."""
    reg = registry or default_registry()
    verbs = frozenset(reg.verbs) | frozenset(reg.aliases)
    out, owner = [], []
    prev = None
    for k, item in enumerate(items):
        if (isinstance(prev, Decl) and prev.shape == "brace" and not prev.body
                and isinstance(item, Text) and is_body_form(item.text, verbs)):
            out.append("")
            owner.append(k)
        printed = print_item(item, "", k)
        out.extend(printed)
        owner.extend([k] * len(printed))
        prev = item
    return out, owner


def print_item(item, indent="", index=None):
    if isinstance(item, Text):
        return [indent + item.text]
    if isinstance(item, Chain):
        return [indent + print_L2(item)]
    if isinstance(item, Decl):
        return decl_lines(item, indent, index)
    raise IMLError("E300", "item %s is not a Chain, a Decl or a Text: %r" % (index, item))


def header_line(d):
    s = ""
    if d.prefix is not None:
        s = "T[%s] " % d.prefix
    s += "::" + d.name
    if d.sub is not None:
        s += "::" + d.sub
    if d.addr is not None:
        s += "{" + d.addr + "}"
    if d.shape in ("brace", "opaque"):
        return s + "{" + d.head + "}"
    if d.shape == "set":
        return s + "{"
    return s + "{" + d.head


def decl_lines(d, indent="", index=None):
    out = [indent + header_line(d)]
    inner = indent + INDENT
    if d.shape == "brace":
        for b in d.body:
            out.extend(print_item(b, inner, index))
    elif d.shape == "set":
        out.extend(inner + t for t in d.lines)
        out.append(indent + "}")
    elif d.shape == "wrapped":
        if not d.lines:
            raise IMLError("E300", "item %s: a wrapped ::%s carries at least its closing line" % (index, d.name))
        out.extend(inner + t for t in d.lines[:-1])
        out.append(indent + "}" if d.lines[-1] == "" else inner + d.lines[-1] + "}")
    else:
        dm = RE_DELIMITER.search("{" + d.head + "}")
        if not dm:
            raise IMLError("E300", "item %s: an opaque ::%s header names no `delimiter:`" % (index, d.name))
        out.extend(d.lines)
        out.append(indent + dm.group(1))
    return out
