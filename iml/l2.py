"""Canon I-Lang operation chains: parse_L2 (text -> AST) and print_L2 (AST -> canonical
text), SPEC-IML-0.4.md sections 0 and 5.

Subset read by parse_L2: one chain on one line, `[VERB(:@TARGET)?(|k=v,k=v)?]` joined
by `=>`, and, for BATC alone, the batch shorthand `[BATC:VERB]` / `[Π:VERB]` (SPEC.md
section 3.9: in BATC/Π only, the token after `:` is a verb reference, not an entity).
Verbs are the 88 canon names or the 13 Greek aliases; an alias means its verb, as a
verb reference too (`[Π:Σ]` is `[BATC:MERGE]`). Values are SPEC.md 2.4 barewords,
quoted strings with the escapes \\" \\\\ \\n, and entity references `@NAME`. Nothing
else is accepted (E502 for constructs outside the subset, E300 for malformed text).

A bare value runs to the next `,` `|` or `]`. Inside it `[` `"` `\\` are E303 and
whitespace is E300; `=`, `>` and `:` are content (`whr=score>80`, `whr=lvl:fatal`).
Leading or trailing whitespace on the line, a dangling `=>`, a raw control character
inside a quoted value, and a line that starts with `=>` (an orphan continuation: the
command line joins continuation lines before parsing, see
iml.__main__.join_chain_lines) are E300. A second chain on the line, `[..]=>[Ω] [..]`,
is E502; any other whitespace outside quotes is E300.

Canonical print: `[VERB:@TARGET|k=v,k=v]=>[...]`, verbs by canon name, OUT as `[Ω]`, a
verb reference as `[BATC:READ]`, values bare when the content is a bareword without
whitespace or `,` `|` `]` `[` `"` `\\` and not starting with `@`, otherwise quoted. No
whitespace anywhere; a chain read from several source lines prints on one line. A value
that holds a control character other than a newline has no I-Lang spelling: print_L2
refuses it (E300) instead of writing a text that parse_L2 would refuse.

ends_with_closed_operation is the condition under which the command line joins a
continuation line to the text above it (SPEC-IML-0.4.md section 2.6); ChainJoiner applies
it line by line in linear time, for the compile side and for the document reader.
"""

from .codec import (BATCH_VERB, Chain, Op, Value, RE_NAME, quote, scan_quoted,
                    first_whitespace_outside_quotes, is_control)
from .errors import IMLError
from .registry import default_registry

OMEGA = "Ω"                              # the canon alias of OUT (SPEC.md 3.10), printed as [Ω]
ILANG_RESERVED_IN_BARE = set(',|][ "\\')   # `=`, `>` and `:` are content
ILANG_E303_IN_BARE = ('[', '"', "\\")        # `,` `|` `]` end the value instead
CONTINUATION = "=>"                          # the pipe operator; a line starting with it continues a chain
NOT_AN_ENTITY = "operation target `%s` is not an @ENTITY (v3.0 \u00a72.2; BATC/Π excepted)"   # the validator's wording


def ilang_bareable(content):
    if not content or content[0] == "@":
        return False
    for c in content:
        if c in ILANG_RESERVED_IN_BARE or c.isspace() or is_control(c):
            return False
    return True


def print_value(val, op_index=None):
    """The I-Lang spelling of one AST value. A control character other than a newline
    (written as the escape \\n) has no spelling: parse_L2 refuses it raw, inside quotes and
    outside, and SPEC.md section 2.4 has no escape for it. A hand-built AST that holds
    one is E300 here, instead of a text the reader would refuse."""
    if val.kind == "entity":
        return "@" + val.text
    if val.kind == "code":
        raise IMLError("E303", "a value code ~%s has no I-Lang spelling" % val.text, op_index=op_index)
    for c in val.text:
        if c != "\n" and is_control(c):
            raise IMLError("E300", "control character U+%04X in a value has no spelling "
                           "(only a newline has an escape, \\n)" % ord(c), op_index=op_index)
    return val.text if ilang_bareable(val.text) else quote(val.text)


class ChainJoiner:
    """An operation line and its continuation lines, collected in linear time: the quote
    and escape state of ends_with_closed_operation is kept from piece to piece, so no
    piece is scanned twice, and the pieces are joined once, by text(). length is the
    length of the text collected so far (the offset at which the next piece starts)."""
    __slots__ = ("parts", "length", "quoted", "escaped", "prev")

    def __init__(self, first=""):
        self.parts, self.length = [], 0
        self.quoted = self.escaped = False
        self.prev = ""
        if first:
            self.add(first)

    def add(self, piece):
        quoted, escaped, prev = self.quoted, self.escaped, self.prev
        for c in piece:
            if quoted:
                if escaped:
                    escaped = False
                elif c == "\\":
                    escaped = True
                elif c == '"':
                    quoted = False
            elif c == '"' and prev == "=":
                quoted = True
            prev = c
        self.quoted, self.escaped, self.prev = quoted, escaped, prev
        self.parts.append(piece)
        self.length += len(piece)

    def closed(self):
        """ends_with_closed_operation of the text collected so far."""
        return not self.quoted and self.prev == "]"

    def text(self):
        return "".join(self.parts)


def ends_with_closed_operation(text):
    """True when text ends with `]` outside a quoted value, that is when the text so far
    is closed by an operation and a continuation line may be joined to it. Quotes are
    scanned by the rules parse_L2 applies (first_whitespace_outside_quotes): a quote opens
    a value only right after `=`, a backslash inside it escapes the next character, and
    the next unescaped quote closes it. Nothing is judged here but the end of the text.
    The joiners use ChainJoiner, which keeps this state across lines."""
    return ChainJoiner(text).closed()


def print_L2(chain):
    parts = []
    for idx, op in enumerate(chain.ops):
        s = OMEGA if op.verb == "OUT" else op.verb
        if op.target is not None:
            s += ":@" + op.target
        elif op.verbref is not None:
            s += ":" + op.verbref
        if op.mods:
            s += "|" + ",".join(k + "=" + print_value(v, idx) for k, v in op.mods)
        parts.append("[" + s + "]")
    return "=>".join(parts)


def parse_L2(text, registry=None):
    reg = registry or default_registry()
    if not isinstance(text, str) or not text:
        raise IMLError("E300", "empty input", 0)
    if text[0].isspace():
        raise IMLError("E300", "leading whitespace before the operation chain", 0)
    if text[-1].isspace():
        raise IMLError("E300", "trailing whitespace after the operation chain", len(text) - 1)
    if text.startswith(CONTINUATION):
        raise IMLError("E300", "orphan `=>` continuation: no preceding operation line", 0)
    if text[0] != "[":
        raise IMLError("E502", "outside the supported subset: an operation chain starts with `[` (seen %r)" % text[:12], 0)
    n = len(text)
    k = first_whitespace_outside_quotes(text)
    if k is not None:
        j = k
        while j < n and text[j].isspace():
            j += 1
        if text[k - 1] == "]" and j < n and text[j] == "[":
            raise IMLError("E502", "a second operation chain on the line: IML carries one chain per line", k)
        raise IMLError("E300", "whitespace is not allowed outside a quoted value", k)
    i = 0
    ops = []
    idx = 0
    while True:
        if text[i] != "[":
            raise IMLError("E300", "expected `[` to open an operation", i, idx)
        i += 1
        j = i
        while j < n and text[j] not in ":|]":
            j += 1
        if j >= n:
            raise IMLError("E300", "unterminated operation: `]` missing", i - 1, idx)
        spelling = text[i:j]
        if not spelling:
            raise IMLError("E300", "missing verb", i, idx)
        verb = reg.resolve_verb(spelling)
        if verb is None:
            raise IMLError("E304", "unknown verb %r" % spelling, i, idx)
        i = j
        target = None
        verbref = None
        if text[i] == ":":
            i += 1
            j = i
            while j < n and text[j] not in "|]":
                j += 1
            if j >= n:
                raise IMLError("E300", "unterminated operation: `]` missing", i, idx)
            ttext = text[i:j]
            if not ttext:
                raise IMLError("E300", "empty target after `:`", i, idx)
            if ttext[0] != "@":
                if verb != BATCH_VERB:
                    raise IMLError("E300", NOT_AN_ENTITY % ttext, i, idx)
                ref = reg.resolve_verb(ttext)
                if ref is None:
                    # the validator's wording
                    raise IMLError("E304", "BATC verb reference `%s` is not a registered verb or alias" % ttext, i, idx)
                if ref == "OUT":
                    raise IMLError("E502", "OUT cannot be batched: not representable in IML", i, idx)
                verbref = ref
            else:
                name = ttext[1:]
                if not RE_NAME.fullmatch(name):
                    raise IMLError("E200", "entity name %r does not match [A-Z][A-Z0-9_]*" % ttext, i, idx)
                if verb == "OUT":
                    raise IMLError("E502", "OUT with a target is not representable in IML", i, idx)
                target = name
            i = j
        mods = []
        if text[i] == "|":
            i += 1
            while True:
                j = i
                while j < n and text[j] not in "=,]|":
                    j += 1
                if j >= n:
                    raise IMLError("E300", "unterminated operation: `]` missing", i, idx)
                if text[j] != "=":
                    raise IMLError("E300", "modifier lacks `=`", i, idx)
                key = text[i:j]
                if not key:
                    raise IMLError("E300", "empty modifier key", i, idx)
                if key not in reg.key_code:
                    raise IMLError("E302", "unknown modifier key %r" % key, i, idx)
                i = j + 1
                if i >= n:
                    raise IMLError("E300", "unterminated operation: `]` missing", i, idx)
                c = text[i]
                if c == '"':
                    content, i = scan_quoted(text, i)
                    val = Value("quoted", content)
                elif c == "@":
                    j = i + 1
                    while j < n and text[j] not in ",]|":
                        j += 1
                    name = text[i + 1:j]
                    if not RE_NAME.fullmatch(name):
                        raise IMLError("E200", "entity name %r does not match [A-Z][A-Z0-9_]*" % text[i:j], i, idx)
                    val = Value("entity", name)
                    i = j
                else:
                    j = i
                    while j < n and text[j] not in ",]|":
                        j += 1
                    raw = text[i:j]
                    if not raw:
                        raise IMLError("E300", "empty value for key %s" % key, i, idx)
                    for k, ch in enumerate(raw):
                        if is_control(ch):
                            raise IMLError("E300", "raw control character U+%04X in bare value" % ord(ch), i + k, idx)
                        if ch in ILANG_E303_IN_BARE:
                            raise IMLError("E303", "reserved character `%s` in bare value" % ch, i + k, idx)
                    val = Value("bare", raw)
                    i = j
                if i >= n:
                    raise IMLError("E300", "unterminated operation: `]` missing", i, idx)
                mods.append((key, val))
                if text[i] == ",":
                    i += 1
                    continue
                if text[i] == "]":
                    break
                if text[i] == "|":
                    raise IMLError("E300", "stray `|`: modifiers are separated by commas", i, idx)
                raise IMLError("E300", "stray character after value", i, idx)
        if text[i] != "]":
            raise IMLError("E300", "expected `]`", i, idx)
        i += 1
        ops.append(Op(verb, target, mods, verbref))
        if i >= n:
            break
        if text.startswith(CONTINUATION, i):
            if verb == "OUT":
                raise IMLError("E502", "OUT may appear only as the last operation", i, idx)
            i += 2
            idx += 1
            if i >= n:
                raise IMLError("E300", "missing operation after `=>`", i, idx)
            continue
        raise IMLError("E502", "outside the supported subset: text after the operation chain (seen %r)" % text[i:i + 12], i, idx)
    return Chain(ops)
