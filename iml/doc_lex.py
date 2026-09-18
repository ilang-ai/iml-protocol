"""The line-level rules of the pinned canon validator, restated for the document reader
(SPEC-IML-0.5.md section 4). The codec imports nothing from canon/: every pattern below is
a copy of the validator's constant of the same name (canon/ilang_grammar_validator.py at
the pin), and tests/test_doc_lex.py checks each one against the validator itself.

What they decide (the validator's reading, PATCH-2 section 1):
  RE_DOC_MARKER       `::ILANG::<version>[::<name>]`, the document marker (1.7)
  RE_DECL_HEAD        `::NAME` or `::NAME::SUB` and the rest of the header line
  RE_TEMPORAL_PREFIX  `T[n]` whitespace `::...` (1.7, temporal_prefix)
  RE_TEMPORAL_BIND    `T[n]=value`
  RE_TEMPORAL_NOTE    `T[x]`, `T[a]→T[b]`, `PARALLEL{...}`, then anything: an opaque note
  RE_TAG_LINE         one or more `[TAG]` / `[TAG:value]` groups and nothing else
  RE_TAG_TEXT         `[TAG] text` (B5 form 1)
  RE_KEY              `KEY:` (B2, B3, B4)
  RE_ENTITY_TOKEN     an `@` token in a structural position (after `{` `:` `|` `,` `→` `=`)
  mask_quoted         blanks the inside of a quoted value (v3.0 2.4) so its commas, pipes,
                      equals signs and brackets are not read as structure
"""

import re

RE_DOC_MARKER = re.compile(r"^::ILANG::\S+$")
RE_DECL_HEAD = re.compile(r"^::([A-Z][A-Z0-9_]*)(?:::([A-Z][A-Z0-9_]*))?(.*)$")
RE_BAD_DECL_HEAD = re.compile(r"^::(\S*)")
RE_TEMPORAL_PREFIX = re.compile(r"^(T\[[^\]]+\])\s+(::.*)$")
RE_TEMPORAL_BIND = re.compile(r"^T\[[^\]]+\]=\S+")
RE_TEMPORAL_NOTE = re.compile(r"^(T\[[^\]]+\](→T\[[^\]]+\])?|PARALLEL\{[^}]*\})(\s.*)?$")
RE_TAG_LINE = re.compile(r"^(\[[A-Z][A-Z0-9_\-]*(?::[^\[\]]*)?\])+$")
RE_TAG_TEXT = re.compile(r"^\[[A-Z][A-Z0-9_\-]*(?::[^\[\]]*)?\](\s+\S.*)?$")
RE_KEY = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*):(.*)$")
RE_ENTITY_TOKEN = re.compile(r"(?<=[{:|,→=])@([A-Za-z][A-Za-z0-9_\-]*)")
RE_BRACKET_GROUPS = re.compile(r"\[([^\[\]]*)\]")
# written inline in the validator's parse_construct and body_line
RE_DELIMITER = re.compile(r"delimiter:([^|}\s]+)")
RE_DOUBLE_INLINE = re.compile(r"^\{[^{}]*\}\{.*\}\s*$")
RE_DOUBLE_SPAN = re.compile(r"^\{[^{}]*\}\{[^}]*$")
STRUCTURAL_CHARS = ("::", "[", "{", "}", "|", "⇒", "=>")
FULLWIDTH_PIPE = "｜"     # ｜
FULLWIDTH_COLON = "："    # ：


def mask_quoted(s):
    """The validator's mask_quoted: blank the inside of quoted values so a comma, pipe,
    equals sign or bracket in a value is not read as structure. A quote opens a value only
    right after `=`, `:` or `,`; escapes stay inside. Positions are kept. A line with an
    unterminated quoted value is returned unmasked."""
    out, quoted, escaped = [], False, False
    for k, ch in enumerate(s):
        if quoted:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == '"':
                quoted = False
                out.append(ch)
                continue
            out.append("_")
            continue
        if ch == '"' and k > 0 and s[k - 1] in "=:,":
            quoted = True
        out.append(ch)
    return s if quoted else "".join(out)


def head_of(s):
    """The head of the first bracket group of s (read on the masked line), or ""."""
    m = RE_BRACKET_GROUPS.search(mask_quoted(s))
    if not m:
        return ""
    return re.split(r"[:|]", m.group(1), maxsplit=1)[0].strip()


def is_operation_line(s, verbs):
    """A `[` line read as an operation: `]=>` in the masked line, or a verb or alias head."""
    return "]=>" in mask_quoted(s) or head_of(s) in verbs


def is_body_form(s, verbs):
    """B1 to B5 and `T[n]=` shapes, the lines that bind as a flush-left body (PATCH-2 1.1
    FLUSH-LEFT-BODY). An operation (B8) and a `=>` line are not among them."""
    if s.startswith(("T:", "A:")):
        return True
    if s.startswith("["):
        ms = mask_quoted(s)
        return bool((RE_TAG_LINE.match(ms) or RE_TAG_TEXT.match(ms)) and head_of(s) not in verbs)
    return bool(RE_KEY.match(s)) or bool(RE_TEMPORAL_BIND.match(s))


def bad_entity(s):
    """(offset, `@name`) of the first entity token in a structural position whose first
    letter is lower case (PATCH-2 2.2, E300), or None."""
    for tok in RE_ENTITY_TOKEN.finditer(s):
        if tok.group(1)[0].islower():
            return tok.start(), "@" + tok.group(1)
    return None


def fullwidth_message(rest):
    """The validator's full-width separator message for a header rest (PATCH-2 1.3), or None."""
    if FULLWIDTH_PIPE in rest:
        return "full-width ｜ as structural separator (§1.3) — use ASCII `|`"
    if FULLWIDTH_COLON in rest:
        for seg in rest.strip("{}").split("|"):
            if FULLWIDTH_COLON in seg and ":" not in seg:
                return "full-width ： as structural separator (§1.3) — use ASCII `:`"
    return None


def find_close(rest):
    """Index of the brace matching the first `{` of rest (depth counted over every brace),
    or -1."""
    depth = 0
    for k, ch in enumerate(rest):
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return k
    return -1


# ------------------------------------------------------------ messages
# The validator's wordings (backticks and section signs as it prints them), used where the
# codec reports the same case; the IML-only cases (SPEC-IML-0.5.md section 9) follow.
MSG_MARKER_POSITION = "::ILANG document marker may only open or close a document (\u00a71.7)"
MSG_ORPHAN = "orphan `=>` continuation: no preceding operation line"
MSG_BRACKET_LINE = "bracket line is neither tag nor operation: %s"
MSG_NO_PRODUCTION = "line matches no I-Lang production: %s"
MSG_MALFORMED_HEADER = "malformed declaration header: %s"
MSG_MALFORMED_MARKER = "malformed ::ILANG document marker: %s"
MSG_TWO_SEGMENTS = "::%s::%s \u2014 only ::MODULE takes a two-segment name (\u00a71.7)"
MSG_UNREGISTERED = ("::%s is not in the declaration registry (32 structural + 13 narrative,"
                    " PATCH-2 \u00a71.5/\u00a71.6)")
MSG_ENTITY = "entity `%s` violates @[A-Z][A-Z0-9_]* (\u00a72.2)"
MSG_LACKS_BRACE = "::%s header lacks `{`"
MSG_DOUBLE = "::%s requires double-brace form ::VERB{addressing}{content} (v3.0 \u00a77)"
MSG_SPAN_OPEN = "::%s brace span never closes"
MSG_NESTED_UNREGISTERED = "nested ::%s is not a registered declaration"
MSG_NESTING = "declaration nesting exceeds one level (\u00a71.2 B7)"
MSG_BODY_ORPHAN = "orphan `=>` continuation in ::%s body: no preceding operation line (\u00a71.7)"
MSG_BODY_BRACKET = "bracket body line is neither B5 tag nor B8 operation: %s"
MSG_BODY_PROSE = "B6 prose body line inside non-prose ::%s (\u00a71.2 B6): %s"
# IML only: stricter than the validator (SPEC-IML-0.5.md section 9) or the codec's own
MSG_UNTERMINATED = ("continuation after an unterminated operation line: the text above a `=>` line "
                    "must end with `]` outside a quoted value")
MSG_CONTINUATION_SEPARATED = ("a `=>` continuation joins only the operation line directly above it"
                              " (after that line's own continuations): a blank or another line stands between")
MSG_OPAQUE_OPEN = "::UNTRUSTED opaque block never closes: no line `%s` before the end of the document"
MSG_OPAQUE_TRAILING = "a same-line trailing body token after an ::UNTRUSTED header with a delimiter is not carried"
MSG_SET_HEADER = ("::%s set-span header carries text before its final `{`: a set span opens with the"
                  " header alone (`::NAME{`, or `::NAME{addressing}{` for a double-brace narrative)")
MSG_TRAILING_DECL = ("a same-line trailing body token that starts with `::` is not carried:"
                     " write the declaration on its own line")
MSG_TRAILING_CONTINUATION = "a same-line trailing body token cannot be a `=>` continuation"
MSG_NESTED_TWO_SEGMENTS = "nested ::%s::%s: only ::MODULE takes a two-segment name (\u00a71.7)"
MSG_NESTED_FORM = ("nested ::%s: a nested declaration takes the brace form on one line"
                   " (`::NAME{...}`, no span, no text after the closing brace)")
MSG_NESTED_B8 = ("the body of nested ::%s carries B1 to B6 lines only: an operation line (B8) or a `=>`"
                 " line there is not carried")
MSG_CONTROL = "raw control character U+%04X in %s (IML quoted strings have no escape for it)"
MSG_BOM = "a byte order mark (U+FEFF) at the head of the input: the command line drops one, the library does not"
