"""The document layer's AST (SPEC-IML-0.5.md section 4): Text and Decl. A document is a
list of items, each a Chain (iml.codec), a Decl or a Text.

Text(text): a line carried as exact text. At top level: the document marker, a tag line,
a temporal bind, a temporal note, an annotation (`→`, `<<<`), a tolerated annotation
declaration (`::LATENCY`, `::CONFIDENCE`, optionally behind a temporal prefix), colophon
prose. In a body: every body line that is neither a nested declaration (B7) nor an
operation (B8). The text is the stripped line; indentation and trailing whitespace are
layout. It never holds a newline or another control character.

Decl(name, sub, prefix, addr, shape, head, body, lines): one declaration.
  name    a canon declaration name (the 49 of the 0.5 registry)
  sub     the second segment of `::MODULE::NAME`, or None
  prefix  the text inside a temporal prefix `T[...]`, or None (top level only)
  addr    the addressing text of a double-brace narrative (`::SAY{addr}{...}`), or None
  shape   "brace" (inline or header_body; body may be empty), "set" (a set span, the
          header ends with `{` and a bare `}` line closes it), "wrapped" (a wrapped field
          header, closed by the first line ending with `}`), "opaque" (`::UNTRUSTED` with
          `delimiter:X`, followed by opaque lines up to the line `X`)
  head    brace and opaque: the content between the braces (the second pair for a
          double-brace narrative); wrapped: the text after the opening brace on the header
          line; set: ""
  body    brace only: a tuple of Text, Chain and nested Decl (shape brace, no prefix, sub
          on MODULE only, a body of Text only)
  lines   set and wrapped: the stripped content lines (for wrapped, the last one without
          its closing `}`); opaque: the verbatim lines between the header and the
          delimiter line; () otherwise

Layout is not carried: blank lines, `---` lines, indentation widths, flush-left against
indented bodies, the position of a same-line trailing body token, and the whitespace
between a temporal prefix and `::`.
"""

SHAPES = ("brace", "set", "wrapped", "opaque")


class Text:
    __slots__ = ("text",)

    def __init__(self, text):
        self.text = text

    def __eq__(self, other):
        return isinstance(other, Text) and self.text == other.text

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(("Text", self.text))

    def __repr__(self):
        return "Text(%r)" % (self.text,)


class Decl:
    __slots__ = ("name", "sub", "prefix", "addr", "shape", "head", "body", "lines")

    def __init__(self, name, sub=None, prefix=None, addr=None, shape="brace", head="", body=(), lines=()):
        if shape not in SHAPES:
            raise ValueError("unknown declaration shape %r (known: %s)" % (shape, ", ".join(SHAPES)))
        self.name = name
        self.sub = sub
        self.prefix = prefix
        self.addr = addr
        self.shape = shape
        self.head = head
        self.body = tuple(body)
        self.lines = tuple(lines)

    def _key(self):
        return (self.name, self.sub, self.prefix, self.addr, self.shape, self.head, self.body, self.lines)

    def __eq__(self, other):
        return isinstance(other, Decl) and self._key() == other._key()

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(("Decl",) + self._key())

    def __repr__(self):
        return ("Decl(%r, sub=%r, prefix=%r, addr=%r, shape=%r, head=%r, body=%r, lines=%r)"
                % (self.name, self.sub, self.prefix, self.addr, self.shape, self.head, self.body, self.lines))
