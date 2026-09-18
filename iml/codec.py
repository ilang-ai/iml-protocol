"""IML AST, compile (AST -> IML text) and decompile (IML text -> AST).

One AST, two surfaces (SPEC-IML-0.3.md section 2; SPEC-IML-0.2.md section 2 for 0.2):

    0.3, written and read                     0.2, read only (version="0.2")
    document  := header NL chain (NL chain)*  (no document form)
    message   := header SP chain              message := header " " chain
    header    := "#iml/0.3/" HEX12            header  := "#iml/0.2/" HEX12
    chain     := op (SP op)*                  chain   := op ("→" op)*
    op        := (ROOT target? | "$") mods?   op      := (ROOT target? | "Ω") mods?
    target    := "@" (MARK | "{" NAME "}")    target  := "Φ" (MARK | "{" NAME "}")
    mods      := kv ("," kv)*
    kv        := KEY "=" value
    value     := quoted | entityref | code | bare
    entityref := "@" (MARK | "{" NAME "}")    entityref := "Φ" (MARK | "{" NAME "}")
    bare      := no `,` `"` `\\` whitespace or control character; first character not
                 `~` `@` `$` `"`             (0.2: not `~` `Φ` `"`; `→` excluded anywhere)

The registry, the AST, the value rules, the round-trip law and the six error codes are
the same under both surfaces; only the reserved characters, the separator and the header
differ. Every scalar keeps its lexeme: a type is a validation tag, never a rewrite.
Quoting is spelling: a `quoted` and a `bare` value with the same content are the same
AST value. Entity references in value position are a distinct kind. The codec fails
closed: the first error stops it, with a 0-based character offset into the input.

compile writes 0.3. The keyword `version="0.2"` on compile exists for the tests and the
0.2 record (corpus/golden/*.iml); the command line does not expose it. decompile reads
0.3 by default and 0.2 with version="0.2"; a header of the other version is E502.
"""

import re

from .errors import IMLError
from .registry import HEADER_VERSION, default_registry

RE_NAME = re.compile(r"[A-Z][A-Z0-9_]*")
RE_ROOT = re.compile(r"[A-Z0-9]{2}")
RE_MARK = re.compile(r"[A-Z0-9]{2}")
RE_KEYCODE = re.compile(r"[a-z]{2}")
RE_CODE = re.compile(r"[a-z0-9]+")
# 0.3: applied to the first line; a space opens a message, the end of the line a document
RE_HEADER = re.compile(r"^#iml/([0-9]+\.[0-9]+)/([0-9a-f]{12})( |$)")
RE_DOCUMENT_FIRST_LINE = re.compile(r"^#iml/[0-9]+\.[0-9]+/[0-9a-f]{12}(?:\r\n|\n|$)")

VALUE_KINDS = ("bare", "quoted", "entity", "code")


class Surface:
    """The reserved characters of one version. phi opens a target or an entity
    reference, omega is OUT, sep separates operations. reserved_in_bare are the
    characters a bare value may not contain (besides whitespace and control characters);
    first_excluded are the characters a bare value may not start with; first_reserved
    is the subset of those that opens no other kind and is E303 (0.3: `$`)."""

    __slots__ = ("version", "phi", "omega", "sep", "sep_name", "document",
                 "reserved_in_bare", "first_excluded", "first_reserved")

    def __init__(self, version, phi, omega, sep, sep_name, document, first_reserved):
        self.version = version
        self.phi = phi
        self.omega = omega
        self.sep = sep
        self.sep_name = sep_name
        self.document = document
        self.reserved_in_bare = frozenset((",", '"', "\\", sep))
        self.first_excluded = frozenset(("~", phi, '"')) | frozenset(first_reserved)
        self.first_reserved = frozenset(first_reserved)


SURFACES = {
    "0.3": Surface("0.3", "@", "$", " ", "the space between operations", True, "$"),
    "0.2": Surface("0.2", "\u03a6", "\u03a9", "\u2192", "`\u2192`", False, ""),
}
DEFAULT_VERSION = HEADER_VERSION
VERSIONS = tuple(SURFACES)
assert DEFAULT_VERSION in SURFACES


def surface(version):
    sf = SURFACES.get(version)
    if sf is None:
        raise ValueError("unknown IML surface version %r (known: %s)" % (version, ", ".join(VERSIONS)))
    return sf


# -------------------------------------------------------------------------- AST
class Value:
    """A modifier value. kind is the spelling seen (bare, quoted, entity, code); text is
    the content (unescaped for quoted; the name without `@` for entity; the code without
    `~` for code). Equality is kind-normalised: bare and quoted compare by content."""

    __slots__ = ("kind", "text")

    def __init__(self, kind, text):
        if kind not in VALUE_KINDS:
            raise ValueError("unknown value kind %r" % kind)
        self.kind = kind
        self.text = text

    @property
    def norm_kind(self):
        return "string" if self.kind in ("bare", "quoted") else self.kind

    def __eq__(self, other):
        return (isinstance(other, Value) and self.norm_kind == other.norm_kind
                and self.text == other.text)

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash((self.norm_kind, self.text))

    def __repr__(self):
        return "Value(%r, %r)" % (self.kind, self.text)


class Op:
    """One operation: canon verb name, target entity name (without `@`) or None, and
    the modifiers as a tuple of (key, Value) pairs in order."""

    __slots__ = ("verb", "target", "mods")

    def __init__(self, verb, target=None, mods=()):
        self.verb = verb
        self.target = target
        self.mods = tuple(mods)

    def __eq__(self, other):
        return (isinstance(other, Op) and self.verb == other.verb
                and self.target == other.target and self.mods == other.mods)

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash((self.verb, self.target, self.mods))

    def __repr__(self):
        return "Op(%r, %r, %r)" % (self.verb, self.target, self.mods)


class Chain:
    __slots__ = ("ops",)

    def __init__(self, ops=()):
        self.ops = tuple(ops)

    def __eq__(self, other):
        return isinstance(other, Chain) and self.ops == other.ops

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self.ops)

    def __repr__(self):
        return "Chain(%r)" % (self.ops,)

    def __len__(self):
        return len(self.ops)


# ------------------------------------------------------------------ text helpers
def quote(content):
    """Quoted spelling with the SPEC.md 2.4 escapes."""
    return '"' + content.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n") + '"'


def is_control(c):
    """True for a character that may not appear raw inside a quoted value: U+0000 to
    U+001F, U+007F, U+2028 and U+2029. A newline is written as the escape \\n."""
    return c < " " or c == "\x7f" or c == "\u2028" or c == "\u2029"


def scan_quoted(text, i, what="quoted value", end=None):
    """Read a quoted value starting at text[i] == '"'. Return (content, index after the
    closing quote). Escapes: \\" \\\\ \\n. Anything else after a backslash is E300; a raw
    control character (is_control) is E300, so a newline is only ever the escape \\n;
    a missing closing quote is E300. Reading stops at end (default: the end of text)."""
    n = len(text) if end is None else end
    buf = []
    j = i + 1
    while j < n:
        c = text[j]
        if c == "\\":
            if j + 1 >= n:
                break
            e = text[j + 1]
            if e == '"':
                buf.append('"')
            elif e == "\\":
                buf.append("\\")
            elif e == "n":
                buf.append("\n")
            else:
                raise IMLError("E300", "bad escape `\\%s` in %s" % (e, what), j)
            j += 2
            continue
        if c == '"':
            return "".join(buf), j + 1
        if is_control(c):
            raise IMLError("E300", "raw control character U+%04X inside %s (a newline is written \\n)" % (ord(c), what), j)
        buf.append(c)
        j += 1
    raise IMLError("E300", "unterminated %s" % what, i)


def check_no_whitespace(text, start=0):
    """E300 at the first whitespace character outside a quoted value at or after start.
    A quote opens a value only right after `=` (SPEC.md 2.4 spelling). Used by the
    I-Lang reader and by the 0.2 surface, where no whitespace is allowed in a chain."""
    quoted = escaped = False
    for k in range(start, len(text)):
        c = text[k]
        if quoted:
            if escaped:
                escaped = False
            elif c == "\\":
                escaped = True
            elif c == '"':
                quoted = False
            elif is_control(c):
                raise IMLError("E300", "raw control character U+%04X inside quoted value" % ord(c), k)
            continue
        if c == '"' and k > 0 and text[k - 1] == "=":
            quoted = True
            continue
        if c.isspace():
            raise IMLError("E300", "whitespace is not allowed outside a quoted value", k)


def iml_bareable(content, version=DEFAULT_VERSION):
    """True when content may be written as a bare value on the given surface: not
    empty, none of the surface's reserved characters, no whitespace or control
    character, and not starting with one of its first-position exclusions
    (0.3: `~` `@` `$` `"`; 0.2: `~` `Φ` `"`)."""
    sf = surface(version)
    if not content or content[0] in sf.first_excluded:
        return False
    for c in content:
        if c in sf.reserved_in_bare or c.isspace() or is_control(c):
            return False
    return True


# ---------------------------------------------------------------------- compile
def compile(chain, registry=None, version=DEFAULT_VERSION):
    """AST -> IML message text: header, one space, chain. Strict: an unknown verb is
    E304, an unknown key E302, a bad entity name E200, OUT not last E502. version
    selects the surface; the command line writes 0.3 only."""
    reg = registry or default_registry()
    sf = surface(version)
    return reg.header_for(sf.version) + " " + _compile_chain(chain, reg, sf)


def compile_document(chains, registry=None):
    """ASTs -> IML 0.3 document text: the header alone on the first line, then one chain
    per line, lines joined by `\\n`, no final newline. At least one chain (E300)."""
    reg = registry or default_registry()
    sf = surface(DEFAULT_VERSION)
    chains = list(chains)
    if not chains:
        raise IMLError("E300", "a document carries at least one chain")
    lines = [reg.header_for(sf.version)]
    for k, chain in enumerate(chains):
        try:
            lines.append(_compile_chain(chain, reg, sf))
        except IMLError as e:
            raise IMLError(e.code, "chain %d: %s" % (k, e.message), e.offset, e.op_index) from None
    return "\n".join(lines)


def _compile_chain(chain, reg, sf):
    if not isinstance(chain, Chain) or not chain.ops:
        raise IMLError("E300", "a chain carries at least one operation", op_index=0)
    last = len(chain.ops) - 1
    parts = []
    for idx, op in enumerate(chain.ops):
        if op.verb == "OUT":
            if idx != last:
                raise IMLError("E502", "OUT may appear only as the last operation", op_index=idx)
            if op.target is not None:
                raise IMLError("E502", "OUT with a target is not representable in IML", op_index=idx)
            s = sf.omega
        else:
            root = reg.verb_root.get(op.verb)
            if root is None:
                raise IMLError("E304", "unknown verb %r" % op.verb, op_index=idx)
            s = root
            if op.target is not None:
                s += _compile_entity(op.target, reg, sf, idx)
        if op.mods:
            kvs = []
            for key, val in op.mods:
                code = reg.key_code.get(key)
                if code is None:
                    raise IMLError("E302", "unknown modifier key %r" % key, op_index=idx)
                kvs.append(code + "=" + _compile_value(val, key, reg, sf, idx))
            s += ",".join(kvs)
        parts.append(s)
    return sf.sep.join(parts)


def _compile_entity(name, reg, sf, idx):
    if not isinstance(name, str) or not RE_NAME.fullmatch(name):
        raise IMLError("E200", "entity name %r does not match [A-Z][A-Z0-9_]*" % (name,), op_index=idx)
    mark = reg.entity_mark.get(name)
    if mark:
        return sf.phi + mark
    return sf.phi + "{" + name + "}"


def _compile_value(val, key, reg, sf, idx):
    if not isinstance(val, Value):
        raise IMLError("E303", "modifier value is not a Value", op_index=idx)
    if val.kind == "entity":
        return _compile_entity(val.text, reg, sf, idx)
    if val.kind == "code":
        if val.text not in reg.value_codes.get(key, {}):
            raise IMLError("E303", "value code ~%s is not in the table of key %s" % (val.text, key), op_index=idx)
        return "~" + val.text
    if iml_bareable(val.text, sf.version):
        return val.text
    return quote(val.text)


# -------------------------------------------------------------------- decompile
def is_document(text):
    """True when the first line of text is a header alone (the document form)."""
    return isinstance(text, str) and RE_DOCUMENT_FIRST_LINE.match(text) is not None


def decompile(text, registry=None, version=DEFAULT_VERSION):
    """IML text -> AST. The form is decided by the first line: a header followed by one
    space and a chain is a message and returns one Chain; a header alone on the first
    line (0.3 only) opens a document, and every following line is one chain: the result
    is a list of Chain, in order. One final line terminator (`\\n` or `\\r\\n`) is
    accepted on either form; a blank line, a trailing space and a second header in a
    document are errors.

    The header is read in this order: no `#iml/` prefix is E502 (no header); a prefix
    that does not have the shape `#iml/<digits>.<digits>/<12 lowercase hex>` followed
    by a space or the end of the line is E300; a shaped header of another version, or
    with a digest prefix that is not the loaded registry's, is E502."""
    reg = registry or default_registry()
    sf = surface(version)
    if not isinstance(text, str) or not text.startswith("#iml/"):
        raise IMLError("E502", "no IML header (`%s` expected)" % reg.header_for(sf.version), 0)
    if not sf.document:
        return _decompile_line_02(text, reg, sf)
    length = len(text)
    nl = text.find("\n")
    line_end = length if nl < 0 else nl
    if nl >= 0 and line_end > 0 and text[line_end - 1] == "\r":
        line_end -= 1
    m = RE_HEADER.match(text, 0, line_end)
    if not m:
        raise IMLError("E300", "bad header shape: `#iml/<digits>.<digits>/<12 lowercase hex>` followed by one space "
                       "(message) or the end of the line (document) expected", len("#iml/"))
    _check_version_and_digest(m, reg, sf)
    if m.group(3) == " ":
        i = m.end()
        if nl >= 0 and nl + 1 < length:
            raise IMLError("E300", "text after the message line: a message is one line; a document puts "
                           "the header alone on its first line", nl + 1)
        if i >= line_end:
            raise IMLError("E300", "empty chain", i)
        return _scan_chain(text, i, line_end, reg, sf)
    if nl < 0:
        raise IMLError("E300", "header alone: a document carries at least one chain line after the header", length)
    chains = []
    start = nl + 1
    while start < length:
        nl2 = text.find("\n", start)
        end = length if nl2 < 0 else nl2
        seg_end = end - 1 if (nl2 >= 0 and end > start and text[end - 1] == "\r") else end
        if seg_end == start:
            raise IMLError("E300", "blank line in a document", start)
        if text.startswith("#iml/", start):
            raise IMLError("E502", "a second header in a document (one header, then one chain per line)", start)
        chains.append(_scan_chain(text, start, seg_end, reg, sf))
        if nl2 < 0:
            break
        start = nl2 + 1
    if not chains:
        raise IMLError("E300", "a document carries at least one chain line after the header", length)
    return chains


def _check_version_and_digest(m, reg, sf):
    if m.group(1) != sf.version:
        hint = ""
        if m.group(1) in SURFACES:
            hint = "; the %s surface is read with version=%r (`--version %s` on the command line)" % (
                m.group(1), m.group(1), m.group(1))
        raise IMLError("E502", "unsupported IML version %s (this decoder reads %s)%s"
                       % (m.group(1), sf.version, hint), len("#iml/"))
    if m.group(2) != reg.digest[:12]:
        raise IMLError("E502", "registry digest mismatch: message %s, registry %s" % (m.group(2), reg.digest[:12]), m.start(2))


def _decompile_line_02(text, reg, sf):
    """The 0.2 surface, as the 0.2.1 codec read it: one line, no whitespace outside
    quotes, ops joined by `→`. The header shape is judged on the first line, the version
    next (a 0.3 header is E502), and then the one form this surface has: header, one
    space, one chain, nothing after it on the line and no line after it."""
    length = len(text)
    nl = text.find("\n")
    line_end = length if nl < 0 else nl
    if nl >= 0 and line_end > 0 and text[line_end - 1] == "\r":
        line_end -= 1
    m = RE_HEADER.match(text, 0, line_end)
    if not m:
        raise IMLError("E300", "bad header shape: `#iml/<digits>.<digits>/<12 lowercase hex>` and one space expected", len("#iml/"))
    _check_version_and_digest(m, reg, sf)
    if m.group(3) != " ":
        raise IMLError("E300", "header alone: the 0.2 surface has one form, header, one space and one chain on one line", line_end)
    i = m.end()
    check_no_whitespace(text, i)
    if i >= length:
        raise IMLError("E300", "empty chain", i)
    return _scan_chain(text, i, length, reg, sf)


def _scan_chain(text, i, n, reg, sf, idx=0):
    """Read one chain from text[i:n]. Offsets in errors are into text."""
    phi, omega, sep = sf.phi, sf.omega, sf.sep
    ops = []
    while True:
        if i >= n:
            raise IMLError("E300", "missing operation after %s" % sf.sep_name, i, idx)
        c = text[i]
        target = None
        if c == omega:
            verb = "OUT"
            i += 1
            if i < n and text[i] == phi:
                raise IMLError("E300", "`%s` (OUT) takes no target" % omega, i, idx)
        else:
            root = text[i:min(i + 2, n)]
            if not RE_ROOT.fullmatch(root):
                raise IMLError("E300", "stray character: a verb root [A-Z0-9]{2} or `%s` expected" % omega, i, idx)
            verb = reg.root_verb.get(root)
            if verb is None:
                raise IMLError("E304", "unknown verb root %r" % root, i, idx)
            i += 2
            if i < n and text[i] == phi:
                target, i = _scan_entity(text, i, n, reg, sf, idx)
        mods = []
        if i < n and "a" <= text[i] <= "z":
            while True:
                code = text[i:min(i + 2, n)]
                if not RE_KEYCODE.fullmatch(code):
                    raise IMLError("E300", "stray character: a key code [a-z]{2} expected", i, idx)
                if text[i + 2:min(i + 3, n)] != "=":
                    raise IMLError("E300", "modifier lacks `=`", i + 2, idx)
                key = reg.code_key.get(code)
                if key is None:
                    raise IMLError("E302", "unknown key code %r" % code, i, idx)
                i += 3
                if i >= n or text[i] == "," or text[i] == sep:
                    raise IMLError("E300", "empty value for key %s" % key, i, idx)
                c = text[i]
                if c == '"':
                    content, i = scan_quoted(text, i, end=n)
                    val = Value("quoted", content)
                elif c == phi:
                    name, i = _scan_entity(text, i, n, reg, sf, idx)
                    val = Value("entity", name)
                elif c == "~":
                    j = i + 1
                    while j < n and RE_CODE.fullmatch(text[j]):
                        j += 1
                    code_text = text[i + 1:j]
                    if not code_text:
                        raise IMLError("E300", "empty value code after `~`", i, idx)
                    if code_text not in reg.value_codes.get(key, {}):
                        raise IMLError("E303", "value code ~%s is not in the table of key %s" % (code_text, key), i, idx)
                    val = Value("code", code_text)
                    i = j
                elif c in sf.first_reserved:
                    raise IMLError("E303", "a bare value may not start with `%s` (reserved); such a value is written quoted" % c, i, idx)
                else:
                    j = i
                    while j < n and text[j] != "," and text[j] != sep:
                        j += 1
                    raw = text[i:j]
                    for k, ch in enumerate(raw):
                        if is_control(ch):
                            raise IMLError("E300", "raw control character U+%04X in bare value" % ord(ch), i + k, idx)
                        if ch.isspace():
                            raise IMLError("E300", "whitespace inside a bare value", i + k, idx)
                        if ch == '"' or ch == "\\":
                            raise IMLError("E303", "reserved character `%s` in bare value" % ch, i + k, idx)
                    val = Value("bare", raw)
                    i = j
                mods.append((key, val))
                if i >= n:
                    break
                if text[i] == ",":
                    i += 1
                    if i >= n or text[i] == "," or text[i] == sep:
                        raise IMLError("E300", "missing modifier after `,`", i, idx)
                    continue
                if text[i] == sep:
                    break
                raise IMLError("E300", "stray character after value", i, idx)
        ops.append(Op(verb, target, mods))
        if i >= n:
            break
        if text[i] == sep:
            if verb == "OUT":
                raise IMLError("E502", "`%s` (OUT) may appear only as the last operation" % omega, i, idx)
            i += 1
            idx += 1
            continue
        raise IMLError("E300", "stray character %r" % text[i], i, idx)
    return Chain(ops)


def _scan_entity(text, i, n, reg, sf, idx):
    """Read phi MARK or phi{NAME} at text[i]. Return (entity name, index after it)."""
    phi = sf.phi
    if text[i + 1:min(i + 2, n)] == "{":
        j = text.find("}", i + 2, n)
        if j < 0:
            raise IMLError("E300", "unterminated custom entity `%s{`" % phi, i, idx)
        name = text[i + 2:j]
        if not RE_NAME.fullmatch(name):
            raise IMLError("E200", "entity name %r does not match [A-Z][A-Z0-9_]*" % name, i + 2, idx)
        if name in reg.entity_mark:
            raise IMLError("E200", "registered entity %s is written by its mark %s%s, not as a custom entity"
                           % (name, phi, reg.entity_mark[name]), i, idx)
        return name, j + 1
    mark = text[i + 1:min(i + 3, n)]
    if not RE_MARK.fullmatch(mark):
        raise IMLError("E300", "stray character: an entity mark [A-Z0-9]{2} or `{NAME}` expected after `%s`" % phi, i + 1, idx)
    name = reg.mark_entity.get(mark)
    if name is None:
        raise IMLError("E200", "unknown entity mark %r" % mark, i + 1, idx)
    return name, i + 3
