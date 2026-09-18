"""Canon I-Lang operation chains: parse_L2 (text -> AST) and print_L2 (AST -> canonical
text), design 0.2 sections 0 and 5.

Subset read by parse_L2: one chain on one line, `[VERB(:@TARGET)?(|k=v,k=v)?]` joined
by `=>`. Verbs are the 88 canon names or the 13 Greek aliases (an alias means its verb).
Values are SPEC.md 2.4 barewords, quoted strings with the escapes \\" \\\\ \\n, and
entity references `@NAME`. Nothing else is accepted (E502 for constructs outside the
subset, E300 for malformed text).

Canonical print: `[VERB:@TARGET|k=v,k=v]=>[...]`, verbs by canon name, OUT as `[Ω]`,
values bare when the content is a bareword without whitespace or `,` `|` `]` `[` `"` `\\`
`=` `>` and not starting with `@`, otherwise quoted. No whitespace anywhere.
"""

from .codec import (Chain, Op, Value, RE_NAME, OMEGA, quote, scan_quoted,
                    check_no_whitespace)
from .errors import IMLError
from .registry import default_registry

ILANG_RESERVED_IN_BARE = set(',|][ "\\=>')


def ilang_bareable(content):
    if not content or content[0] == "@":
        return False
    for c in content:
        if c in ILANG_RESERVED_IN_BARE or c.isspace():
            return False
    return True


def print_value(val):
    if val.kind == "entity":
        return "@" + val.text
    if val.kind == "code":
        raise IMLError("E303", "a value code ~%s has no I-Lang spelling" % val.text)
    return val.text if ilang_bareable(val.text) else quote(val.text)


def print_L2(chain):
    parts = []
    for op in chain.ops:
        s = OMEGA if op.verb == "OUT" else op.verb
        if op.target is not None:
            s += ":@" + op.target
        if op.mods:
            s += "|" + ",".join(k + "=" + print_value(v) for k, v in op.mods)
        parts.append("[" + s + "]")
    return "=>".join(parts)


def parse_L2(text, registry=None):
    reg = registry or default_registry()
    if not isinstance(text, str) or not text:
        raise IMLError("E300", "empty input", 0)
    if text[0] != "[":
        raise IMLError("E502", "outside the 0.2 subset: an operation chain starts with `[` (seen %r)" % text[:12], 0)
    check_no_whitespace(text)
    n = len(text)
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
                if verb == "BATC":
                    raise IMLError("E502", "the [BATC:VERB] / [Π:VERB] form is not supported in 0.2", i, idx)
                raise IMLError("E300", "operation target %r is not an @ENTITY" % ttext, i, idx)
            name = ttext[1:]
            if not RE_NAME.fullmatch(name):
                raise IMLError("E200", "entity name %r does not match [A-Z][A-Z0-9_]*" % ttext, i, idx)
            if verb == "OUT":
                raise IMLError("E502", "OUT with a target is not representable in IML 0.2", i, idx)
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
                        if ch in ('"', "\\"):
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
        ops.append(Op(verb, target, mods))
        if i >= n:
            break
        if text.startswith("=>", i):
            if verb == "OUT":
                raise IMLError("E502", "OUT may appear only as the last operation", i, idx)
            i += 2
            idx += 1
            if i >= n:
                raise IMLError("E300", "missing operation after `=>`", i, idx)
            continue
        raise IMLError("E502", "outside the 0.2 subset: text after the operation chain (seen %r)" % text[i:i + 12], i, idx)
    return Chain(ops)
