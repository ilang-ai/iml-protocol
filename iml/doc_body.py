"""Body lines of a declaration (SPEC-IML-0.5.md section 4.5), read as the pinned validator
reads them (consume_body, body_line, classify_body_line; PATCH-2 1.1 and 1.2), with the
points where IML is stricter (SPEC-IML-0.5.md section 9):

- a `=>` continuation joins only the operation line directly above it, after that line's
  own continuations, and only when that text ends with `]` outside quotes; a `=>` body line
  anywhere else is E300 (the validator keeps a body's last operation across lines, and
  accepts an orphan `=>` line silently in a prose-body declaration);
- a nested declaration (B7) takes the brace form on one line, `sub` on MODULE only, and
  its own body carries B1 to B6 lines only;
- a same-line trailing body token that starts with `::` or `=>` is E300.

_BodyReader is a mixin of iml.doc_parse.DocParser, which provides lines, starts, reg,
verbs, the carried-text check and the error helper.
"""

from .doc_ast import Decl, Text
from .doc_lex import (MSG_BODY_BRACKET, MSG_BODY_ORPHAN, MSG_BODY_PROSE, MSG_CONTINUATION_SEPARATED,
                      MSG_DOUBLE, MSG_NESTED_B8, MSG_NESTED_FORM, MSG_NESTED_TWO_SEGMENTS,
                      MSG_NESTED_UNREGISTERED, MSG_NESTING, MSG_TRAILING_CONTINUATION, MSG_TRAILING_DECL,
                      MSG_UNTERMINATED, RE_DECL_HEAD, RE_DOC_MARKER, RE_DOUBLE_INLINE, RE_KEY,
                      RE_TAG_LINE, RE_TAG_TEXT, RE_TEMPORAL_BIND, RE_TEMPORAL_NOTE, RE_TEMPORAL_PREFIX,
                      find_close, is_body_form, is_operation_line, mask_quoted)
from .errors import IMLError
from .l2 import ChainJoiner, parse_L2


def indent_of(line):
    return len(line) - len(line.lstrip())


class _BodyReader:
    # ------------------------------------------------------------ one body
    def read_body(self, i, name, header_indent, trailing, trailing_off):
        """The body of the declaration whose header is line i: the same-line trailing
        token (if any) first, then the indented or flush-left lines. Returns (items, next
        line index)."""
        items = []
        if trailing:
            if trailing.startswith("::"):
                raise IMLError("E300", MSG_TRAILING_DECL, trailing_off)
            if trailing.startswith("=>"):
                raise IMLError("E300", MSG_TRAILING_CONTINUATION, trailing_off)
            if trailing.startswith("[") and is_operation_line(trailing, self.verbs):
                items.append(self.parse_chain_text(trailing, [(0, trailing_off)], i))
            else:
                items.append(self.classify(i, name, trailing, trailing_off))
        self.body_op_seen = False            # the validator's consume_body resets its state here
        lines, n = self.lines, len(self.lines)
        j, regime = i + 1, None
        while j < n:
            line = lines[j]
            s = line.strip()
            if not s:
                if regime != "indent":
                    break                    # a flush-left body ends at the first blank line
                k = j + 1
                while k < n and not lines[k].strip():
                    k += 1
                if k < n and indent_of(lines[k]) > header_indent:
                    j = k
                    continue
                break
            ind = indent_of(line)
            if ind > header_indent:
                if regime == "flush":
                    break
                regime = "indent"
                j = self.body_line(j, name, s, ind, header_indent, items)
                continue
            if regime == "indent" or ind != header_indent:
                break
            if s.startswith("::") or RE_TEMPORAL_PREFIX.match(s) or RE_DOC_MARKER.match(s):
                break
            if is_body_form(s, self.verbs):
                regime = "flush"
                items.append(self.classify(j, name, s, self.line_off(j)))
                j += 1
                continue
            break
        return items, j

    def body_line(self, j, name, s, ind, header_indent, items):
        """One indented body line; a B8 line takes its continuation lines, a B7 line its
        own deeper lines. Returns the next line index."""
        if s.startswith("::"):
            nm = RE_DECL_HEAD.match(s)
            nested_name = nm.group(1) if nm else "?"
            if nm and nested_name in self.tolerated:
                items.append(self.text(s, self.line_off(j)))
                return j + 1
            if not nm or nested_name not in self.nestable:
                raise IMLError("E300", MSG_NESTED_UNREGISTERED % nested_name, self.line_off(j))
            decl, k = self.nested(j, s, nm, ind)
            items.append(decl)
            return k
        if s.startswith("[") and is_operation_line(s, self.verbs):
            chain, k = self.join_chain(j, s, header_indent)
            items.append(chain)
            self.body_op_seen = True
            return k
        items.append(self.classify(j, name, s, self.line_off(j)))
        return j + 1

    # ------------------------------------------------------------ B7
    def nested(self, j, s, nm, ind):
        name, sub, rest = nm.group(1), nm.group(2), nm.group(3)
        off = self.line_off(j)
        if name in self.double:
            nrest = s[2 + len(name):].strip()
            if not RE_DOUBLE_INLINE.match(nrest):
                raise IMLError("E300", MSG_DOUBLE % name, off)
        self.check_entities(s, off)
        if sub and name != "MODULE":
            raise IMLError("E300", MSG_NESTED_TWO_SEGMENTS % (name, sub), off)
        rest = (rest or "").strip()
        if not rest.startswith("{"):
            raise IMLError("E300", MSG_NESTED_FORM % name, off)
        addr = None
        if name in self.double:
            c1 = rest.index("}")
            addr, head = rest[1:c1], rest[c1 + 2:-1]
        else:
            if rest.count("{") - rest.count("}") > 0:
                raise IMLError("E300", MSG_NESTED_FORM % name, off)
            close = find_close(rest)
            if rest[close + 1:].strip():
                raise IMLError("E300", MSG_NESTED_FORM % name, off)
            head = rest[1:close]
        if addr is not None:
            self.check_carried(addr, "the addressing of nested ::%s" % name, off)
        self.check_carried(head, "the header of nested ::%s" % name, off)
        lines, n = self.lines, len(self.lines)
        body, k = [], j + 1
        while k < n:
            ln = lines[k]
            t = ln.strip()
            if not t or indent_of(ln) <= ind:
                break
            if t.startswith("::"):
                raise IMLError("E300", MSG_NESTING, self.line_off(k))
            if t.startswith("=>") and not self.body_op_seen and name not in self.prose:
                raise IMLError("E300", MSG_BODY_ORPHAN % name, self.line_off(k))   # the validator rejects it too
            if t.startswith("=>") or (t.startswith("[") and is_operation_line(t, self.verbs)):
                raise IMLError("E300", MSG_NESTED_B8 % name, self.line_off(k))
            body.append(self.classify(k, name, t, self.line_off(k)))
            k += 1
        return Decl(name, sub, None, addr, "brace", head, body), k

    # ------------------------------------------------------------ B1 to B6
    def classify(self, j, parent, s, off):
        """A body line that is neither B7 nor B8, by its first token (PATCH-2 1.2
        BODY-SET). Returns a Text or raises."""
        if RE_TEMPORAL_BIND.match(s) or RE_TEMPORAL_NOTE.match(s) or s.startswith("→"):
            return self.text(s, off)
        if s.startswith(("T:", "A:")):
            self.check_entities(s, off)
            return self.text(s, off)
        if s.startswith("=>"):
            raise IMLError("E300", MSG_CONTINUATION_SEPARATED if self.body_op_seen else MSG_BODY_ORPHAN % parent, off)
        if s.startswith("["):
            ms = mask_quoted(s)
            if RE_TAG_LINE.match(ms) or RE_TAG_TEXT.match(ms) or parent in self.prose:
                return self.text(s, off)
            raise IMLError("E300", MSG_BODY_BRACKET % s[:60], off)
        if RE_KEY.match(s):
            self.check_entities(s, off)
            return self.text(s, off)
        if parent in self.prose:
            return self.text(s, off)
        raise IMLError("E300", MSG_BODY_PROSE % (parent, s[:50]), off)

    # ------------------------------------------------------------ B8 and top-level chains
    def join_chain(self, i, s, header_indent):
        """The operation line i (stripped text s) and the `=>` lines directly below it,
        joined as the 0.4.1 rule joins them (SPEC-IML-0.4.md section 2.6). At top level
        (header_indent None) a continuation line may stand at any indentation; in a body it
        must stay in the body. The join is linear in the length of the chain (ChainJoiner).
        Returns (Chain, next line index)."""
        lines, n = self.lines, len(self.lines)
        joiner, segs = ChainJoiner(s), [(0, self.line_off(i))]
        j = i + 1
        while j < n:
            ln = lines[j]
            t = ln.strip()
            if not t.startswith("=>"):
                break
            if header_indent is not None and indent_of(ln) <= header_indent:
                break
            if not joiner.closed():
                raise IMLError("E300", MSG_UNTERMINATED, self.line_off(j))
            segs.append((joiner.length, self.line_off(j)))
            joiner.add(t)
            j += 1
        return self.parse_chain_text(joiner.text(), segs, i), j

    def parse_chain_text(self, text, segs, i):
        try:
            chain = parse_L2(text, self.reg)
        except IMLError as e:
            off = e.offset
            if off is not None:
                base, src = segs[0]
                for jp, so in segs:
                    if jp <= off:
                        base, src = jp, so
                off = src + (off - base)
            raise IMLError(e.code, e.message, off, e.op_index) from None
        self.chain_lines.append((i + 1, chain))
        return chain
