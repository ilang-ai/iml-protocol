"""The IML 0.5 document form (SPEC-IML-0.5.md sections 2 and 4): compile_doc (document AST
-> IML text) and decompile_doc (IML text -> document AST).

    document  := header NL item (NL item)* NL?
    header    := "#iml/0.5/" HEX12
    item      := chain | textline | decl
    chain     := op (SP op)*                      ; as 0.4, starts with a root or "$"
    textline  := QUOTED                           ; a top-level Text
    decl      := ":" DCODE prefix? sub? form (NL dline)*
    prefix    := "T" QUOTED                       ; the text inside T[...]
    sub       := "::" NAME                        ; MODULE only
    form      := QUOTED                           ; brace or opaque: head
               | QUOTED QUOTED                    ; brace, double-brace narrative: addr, head
               | QUOTED? "{"                      ; set; the QUOTED (addr) for a double-brace narrative only
               | QUOTED? "{" QUOTED               ; wrapped: addr (double-brace only), then head
    dline     := SP QUOTED                        ; brace: a Text body line; set, wrapped: a content line; opaque: an opaque line
               | SP chain                         ; brace: a B8 body line
               | SP ":" DCODE sub? form1          ; brace: a nested declaration (form1: the two brace forms)
               | SP SP QUOTED                     ; a Text body line of the nested declaration just above
    DCODE     := [A-Z0-9]{2}, a code of the declarations table
    QUOTED    := the 0.4 quoted string, escapes \\" \\\\ \\n, no raw control character; a text,
                 head, addr, prefix or content line never holds a newline (E300)

The prefix stands before the sub (design-0.5 section 4 writes `sub? prefix?`): a NAME is
[A-Z][A-Z0-9_]*, so a sub written first would take the `T` of a prefix after it
(`:ML::CORET"3"{`); written first, the prefix is `T` and a quoted text, and nothing follows a
NAME but a form, which starts with a quote or `{`.

The first character of a line decides its kind: `#` the header, a root character or `$` a
chain, `"` a text line, `:` a declaration, a space a line of the declaration above. Any
other first character is E300. Under a 0.4 or 0.3 header (digest 88d05d0839c1) a document
carries chains only: a text or declaration line there is E502.

Both directions validate by round trip: the AST is printed (iml.doc_print) and read again
(iml.doc_parse). An error there is reported as it is; an AST that reads back as another is
E300, "not the canonical spelling of a construct" (a Text whose text is a registered
declaration, for example, which must be coded as a declaration).
"""

import re

from .codec import Chain, _compile_chain, is_control, quote, surface
from .doc_ast import SHAPES, Decl, Text
from .doc_lex import RE_DELIMITER
from .doc_parse import parse_doc
from .doc_print import print_doc_lines
from .errors import IMLError
from .registry import DOCUMENT_LAYER_VERSIONS, HEADER_VERSION, default_registry

RE_NAME = re.compile(r"[A-Z][A-Z0-9_]*")
RE_DCODE = re.compile(r"[A-Z0-9]{2}")
NOT_CANONICAL = "not the canonical spelling of a construct: item %d reads back from its I-Lang print as %s"


# --------------------------------------------------------------------- compile
def compile_doc(items, registry=None):
    """Document AST -> IML 0.5 document text: the header alone on the first line, then the
    items, lines joined by `\\n`, no final newline. At least one item (E300)."""
    reg = registry or default_registry()
    sf = surface(HEADER_VERSION)
    items = list(items)
    if not items:
        raise IMLError("E300", "a document carries at least one item")
    lines = [reg.header_for(HEADER_VERSION)]
    for k, item in enumerate(items):
        try:
            lines.extend(encode_item(item, reg, sf))
        except IMLError as e:
            raise IMLError(e.code, "item %d: %s" % (k, e.message), e.offset, e.op_index) from None
    check_canonical(items, reg, None)
    return "\n".join(lines)


def q(content, what):
    """The IML quoted spelling of a carried text: no newline, no control character."""
    if not isinstance(content, str):
        raise IMLError("E300", "%s is not a string: %r" % (what, content))
    for c in content:
        if c == "\n":
            raise IMLError("E300", "a newline inside %s: a text never holds one" % what)
        if is_control(c):
            raise IMLError("E300", "raw control character U+%04X inside %s has no spelling" % (ord(c), what))
    return quote(content)


def encode_item(item, reg, sf):
    if isinstance(item, Chain):
        return [_compile_chain(item, reg, sf)]
    if isinstance(item, Text):
        return [q(item.text, "a text line")]
    if isinstance(item, Decl):
        return encode_decl(item, reg, sf, nested=False)
    raise IMLError("E300", "not a Chain, a Decl or a Text: %r" % (item,))


def encode_decl(d, reg, sf, nested):
    code = reg.decl_code.get(d.name)
    if code is None:
        raise IMLError("E300", "::%s is not in the declarations table of the registry" % (d.name,))
    if d.shape not in SHAPES:
        raise IMLError("E300", "unknown shape %r" % (d.shape,))
    s = ":" + code
    if d.prefix is not None:                 # the prefix before the sub: a NAME would swallow the `T` of a prefix after it
        if nested:
            raise IMLError("E300", "a nested declaration takes no temporal prefix")
        s += "T" + q(d.prefix, "a temporal prefix")
    if d.sub is not None:
        if d.name != "MODULE" or not isinstance(d.sub, str) or not RE_NAME.fullmatch(d.sub):
            raise IMLError("E300", "::%s::%r: only ::MODULE takes a second segment [A-Z][A-Z0-9_]*" % (d.name, d.sub))
        s += "::" + d.sub
    if (d.addr is not None) != (d.name in reg.double):
        raise IMLError("E300", "::%s: an addressing text belongs to the six double-brace narratives only" % d.name)
    if d.addr is not None:
        s += q(d.addr, "an addressing text")
    if nested and d.shape != "brace":
        raise IMLError("E300", "a nested declaration takes the brace form")
    if d.shape in ("brace", "opaque"):
        if d.shape == "opaque" and (d.name != "UNTRUSTED" or not RE_DELIMITER.search("{" + d.head + "}")):
            raise IMLError("E300", "an opaque declaration is ::UNTRUSTED with `delimiter:` in its header")
        s += q(d.head, "a declaration header")
    elif d.shape == "set":
        if d.head != "":
            raise IMLError("E300", "a set span carries no header text")
        s += "{"
    else:
        s += "{" + q(d.head, "a declaration header")
    out = [s]
    if d.shape == "brace":
        if d.lines:
            raise IMLError("E300", "a brace declaration carries body items, not lines")
        for b in d.body:
            if isinstance(b, Decl):
                if nested:
                    raise IMLError("E300", "declaration nesting exceeds one level")
                out.extend(" " + x for x in encode_decl(b, reg, sf, nested=True))
            elif isinstance(b, Text):
                out.append(" " + q(b.text, "a body line"))   # a nested body line gets its second space from the parent
            elif isinstance(b, Chain) and not nested:
                out.append(" " + _compile_chain(b, reg, sf))
            else:
                raise IMLError("E300", "a %sbody carries %s only: %r"
                               % ("nested " if nested else "", "Text" if nested else "Text, Chain and Decl", b))
    else:
        if d.body:
            raise IMLError("E300", "a %s declaration carries lines, not body items" % d.shape)
        out.extend(" " + q(t, "a content line") for t in d.lines)
    return out


def check_canonical(items, reg, item_offsets):
    """Print the AST and read it back: an error there is raised as it is (its offset moved
    to the item's IML line when item_offsets is given); an AST that reads back as another
    is E300."""
    lines, owner = print_doc_lines(items, reg)
    printed = "\n".join(lines)
    try:
        back = parse_doc(printed, reg)
    except IMLError as e:
        off = e.offset
        if item_offsets is not None and off is not None:
            k = owner[min(printed.count("\n", 0, off), len(owner) - 1)] if owner else 0
            off = item_offsets[min(k, len(item_offsets) - 1)]
        raise IMLError(e.code, e.message, off, e.op_index) from None
    if back != items:
        k = next((j for j in range(min(len(back), len(items))) if back[j] != items[j]), min(len(back), len(items)))
        k = min(k, len(items) - 1)
        seen = repr(back[k])[:80] if k < len(back) else "nothing"
        raise IMLError("E300", NOT_CANONICAL % (k, seen), item_offsets[k] if item_offsets else None)
    return back
