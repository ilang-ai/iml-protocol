"""IML 0.2 AST, compile (AST -> IML text) and decompile (IML text -> AST).

Grammar (design 0.2 section 2):

    message   := header " " chain
    header    := "#iml/0.2/" HEX12
    chain     := op ("→" op)*
    op        := (ROOT target? | "Ω") mods?
    target    := "Φ" (MARK | "{" NAME "}")
    mods      := kv ("," kv)*
    kv        := KEY "=" value
    value     := quoted | entityref | code | bare

Every scalar keeps its lexeme: a type is a validation tag, never a rewrite. Quoting is
spelling: a `quoted` and a `bare` value with the same content are the same AST value.
Entity references in value position are a distinct kind. The codec fails closed.
"""

import re

from .errors import IMLError
from .registry import default_registry

ARROW = "→"
PHI = "Φ"
OMEGA = "Ω"
RE_NAME = re.compile(r"[A-Z][A-Z0-9_]*")
RE_ROOT = re.compile(r"[A-Z0-9]{2}")
RE_MARK = re.compile(r"[A-Z0-9]{2}")
RE_KEYCODE = re.compile(r"[a-z]{2}")
RE_CODE = re.compile(r"[a-z0-9]+")
RE_HEADER = re.compile(r"#iml/([0-9]+\.[0-9]+)/")

VALUE_KINDS = ("bare", "quoted", "entity", "code")


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


def scan_quoted(text, i, what="quoted value"):
    """Read a quoted value starting at text[i] == '"'. Return (content, index after the
    closing quote). Escapes: \\" \\\\ \\n. Anything else after a backslash is E300; a raw
    newline is E300 (a message is one line); a missing closing quote is E300."""
    n = len(text)
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
        if c == "\n":
            raise IMLError("E300", "raw newline inside %s" % what, j)
        buf.append(c)
        j += 1
    raise IMLError("E300", "unterminated %s" % what, i)


def check_no_whitespace(text, start=0):
    """E300 at the first whitespace character outside a quoted value at or after start.
    A quote opens a value only right after `=` (SPEC.md 2.4 spelling)."""
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
            elif c == "\n":
                raise IMLError("E300", "raw newline inside quoted value", k)
            continue
        if c == '"' and k > 0 and text[k - 1] == "=":
            quoted = True
            continue
        if c.isspace():
            raise IMLError("E300", "whitespace is not allowed outside a quoted value", k)


def iml_bareable(content):
    """True when content may be written as an IML bare value: not empty, none of
    `,` `→` `"` `\\` or whitespace, and not starting with `~`, `Φ` or `"`."""
    if not content or content[0] in ('~', PHI, '"'):
        return False
    for c in content:
        if c in (",", ARROW, '"', "\\") or c.isspace():
            return False
    return True


# ---------------------------------------------------------------------- compile
def compile(chain, registry=None):
    """AST -> IML message text (header from the loaded registry). Strict: an unknown
    verb is E304, an unknown key E302, a bad entity name E200, OUT not last E502."""
    reg = registry or default_registry()
    if not isinstance(chain, Chain) or not chain.ops:
        raise IMLError("E300", "a chain carries at least one operation", op_index=0)
    last = len(chain.ops) - 1
    parts = []
    for idx, op in enumerate(chain.ops):
        if op.verb == "OUT":
            if idx != last:
                raise IMLError("E502", "OUT may appear only as the last operation", op_index=idx)
            if op.target is not None:
                raise IMLError("E502", "OUT with a target is not representable in IML 0.2", op_index=idx)
            s = OMEGA
        else:
            root = reg.verb_root.get(op.verb)
            if root is None:
                raise IMLError("E304", "unknown verb %r" % op.verb, op_index=idx)
            s = root
            if op.target is not None:
                s += _compile_entity(op.target, reg, idx)
        if op.mods:
            kvs = []
            for key, val in op.mods:
                code = reg.key_code.get(key)
                if code is None:
                    raise IMLError("E302", "unknown modifier key %r" % key, op_index=idx)
                kvs.append(code + "=" + _compile_value(val, key, reg, idx))
            s += ",".join(kvs)
        parts.append(s)
    return reg.header + " " + ARROW.join(parts)


def _compile_entity(name, reg, idx):
    if not isinstance(name, str) or not RE_NAME.fullmatch(name):
        raise IMLError("E200", "entity name %r does not match [A-Z][A-Z0-9_]*" % (name,), op_index=idx)
    mark = reg.entity_mark.get(name)
    if mark:
        return PHI + mark
    return PHI + "{" + name + "}"


def _compile_value(val, key, reg, idx):
    if not isinstance(val, Value):
        raise IMLError("E303", "modifier value is not a Value", op_index=idx)
    if val.kind == "entity":
        return _compile_entity(val.text, reg, idx)
    if val.kind == "code":
        if val.text not in reg.value_codes.get(key, {}):
            raise IMLError("E303", "value code ~%s is not in the table of key %s" % (val.text, key), op_index=idx)
        return "~" + val.text
    if iml_bareable(val.text):
        return val.text
    return quote(val.text)


# -------------------------------------------------------------------- decompile
def decompile(text, registry=None):
    """IML message text -> AST. Refuses a message without a header, with another
    version, or with a digest prefix that is not the loaded registry's (E502)."""
    reg = registry or default_registry()
    if not isinstance(text, str) or not text.startswith("#iml/"):
        raise IMLError("E502", "no IML header (`#iml/0.2/<12 hex>` expected)", 0)
    m = RE_HEADER.match(text)
    if not m:
        raise IMLError("E300", "bad header shape", len("#iml/"))
    if m.group(1) != reg.version:
        raise IMLError("E502", "unsupported IML version %s (this codec reads %s)" % (m.group(1), reg.version), len("#iml/"))
    p = m.end()
    hex12 = text[p:p + 12]
    if not re.fullmatch(r"[0-9a-f]{12}", hex12):
        raise IMLError("E300", "bad header shape: 12 lowercase hex characters expected", p)
    if text[p + 12:p + 13] != " ":
        raise IMLError("E300", "bad header shape: one space expected after the header", p + 12)
    if hex12 != reg.digest[:12]:
        raise IMLError("E502", "registry digest mismatch: message %s, registry %s" % (hex12, reg.digest[:12]), p)
    i = p + 13
    check_no_whitespace(text, i)
    n = len(text)
    if i >= n:
        raise IMLError("E300", "empty chain", i)
    ops = []
    idx = 0
    while True:
        if i >= n:
            raise IMLError("E300", "missing operation after `%s`" % ARROW, i, idx)
        c = text[i]
        target = None
        if c == OMEGA:
            verb = "OUT"
            i += 1
            if i < n and text[i] == PHI:
                raise IMLError("E300", "%s takes no target" % OMEGA, i, idx)
        else:
            root = text[i:i + 2]
            if not RE_ROOT.fullmatch(root):
                raise IMLError("E300", "stray character: a verb root [A-Z0-9]{2} or %s expected" % OMEGA, i, idx)
            verb = reg.root_verb.get(root)
            if verb is None:
                raise IMLError("E304", "unknown verb root %r" % root, i, idx)
            i += 2
            if i < n and text[i] == PHI:
                target, i = _scan_entity(text, i, reg, idx)
        mods = []
        if i < n and "a" <= text[i] <= "z":
            while True:
                code = text[i:i + 2]
                if not RE_KEYCODE.fullmatch(code):
                    raise IMLError("E300", "stray character: a key code [a-z]{2} expected", i, idx)
                if text[i + 2:i + 3] != "=":
                    raise IMLError("E300", "modifier lacks `=`", i + 2, idx)
                key = reg.code_key.get(code)
                if key is None:
                    raise IMLError("E302", "unknown key code %r" % code, i, idx)
                i += 3
                if i >= n or text[i] in ("," , ARROW):
                    raise IMLError("E300", "empty value for key %s" % key, i, idx)
                c = text[i]
                if c == '"':
                    content, i = scan_quoted(text, i)
                    val = Value("quoted", content)
                elif c == PHI:
                    name, i = _scan_entity(text, i, reg, idx)
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
                else:
                    j = i
                    while j < n and text[j] != "," and text[j] != ARROW:
                        j += 1
                    raw = text[i:j]
                    for k, ch in enumerate(raw):
                        if ch in ('"', "\\"):
                            raise IMLError("E303", "reserved character `%s` in bare value" % ch, i + k, idx)
                    val = Value("bare", raw)
                    i = j
                mods.append((key, val))
                if i >= n:
                    break
                if text[i] == ",":
                    i += 1
                    if i >= n or text[i] in (",", ARROW):
                        raise IMLError("E300", "missing modifier after `,`", i, idx)
                    continue
                if text[i] == ARROW:
                    break
                raise IMLError("E300", "stray character after value", i, idx)
        ops.append(Op(verb, target, mods))
        if i >= n:
            break
        if text[i] == ARROW:
            if verb == "OUT":
                raise IMLError("E502", "%s (OUT) may appear only as the last operation" % OMEGA, i, idx)
            i += 1
            idx += 1
            continue
        raise IMLError("E300", "stray character %r" % text[i], i, idx)
    return Chain(ops)


def _scan_entity(text, i, reg, idx):
    """Read `Φ` MARK or `Φ{NAME}` at text[i]. Return (entity name, index after it)."""
    n = len(text)
    if text[i + 1:i + 2] == "{":
        j = text.find("}", i + 2)
        if j < 0:
            raise IMLError("E300", "unterminated custom entity `%s{`" % PHI, i, idx)
        name = text[i + 2:j]
        if not RE_NAME.fullmatch(name):
            raise IMLError("E200", "entity name %r does not match [A-Z][A-Z0-9_]*" % name, i + 2, idx)
        if name in reg.entity_mark:
            raise IMLError("E200", "registered entity %s is written by its mark %s%s, not as a custom entity"
                           % (name, PHI, reg.entity_mark[name]), i, idx)
        return name, j + 1
    mark = text[i + 1:i + 3]
    if not RE_MARK.fullmatch(mark):
        raise IMLError("E300", "stray character: an entity mark [A-Z0-9]{2} or `{NAME}` expected after %s" % PHI, i + 1, idx)
    name = reg.mark_entity.get(mark)
    if name is None:
        raise IMLError("E200", "unknown entity mark %r" % mark, i + 1, idx)
    return name, i + 3
