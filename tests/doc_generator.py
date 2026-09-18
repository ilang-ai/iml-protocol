"""Random raw I-Lang documents for the document laws and the oracle (design-0.5 section 10).

The generator is not the oracle: it writes source text that stays inside what the canon
validator accepts (0 errors in raw mode) and what IML carries, and the tests check the
laws on whatever parse_doc reads from it. It covers every block shape (inline and
header_body, set and wrapped spans, single and double brace, opaque blocks), every body
form (B1 to B8, binds, notes, annotations, tolerated annotations, nested declarations
with their own bodies), temporal prefixes, MODULE::NAME, preamble tags, colophon prose,
top-level texts, chains with continuation lines, and layout (indentation widths, TABs as
indentation, flush-left bodies, same-line trailing tokens, blank and `---` lines, trailing
whitespace). Chains come from the 0.4 chain generator of tests/test_roundtrip.py."""

import random

from iml import default_registry
from iml.doc_lex import bad_entity, is_body_form
from test_roundtrip import Generator as ChainGenerator

WORDS = ("verify first check scope global project session trust memory event build deploy review "
         "judge mode case clause prior budget status rubric lesson list rule report draft").split()
TAGS = ("NOTE", "WHAT", "WHY", "TYPE", "SCOPE", "LANG", "LAYER", "SEE", "TODO")   # none is a verb (DESC and TAG are)
PREAMBLE_TAGS = TAGS + ("LIST", "READ", "SET", "DESC")     # verb names are tags in the preamble only
KEYS = ("ON", "ACCEPT", "NON_GOALS", "src", "target", "reason_note", "S", "E", "R")
ENTITIES = ("@SUN", "@OPUS", "@SELF", "@USER", "@TASK", "@SKY", "@SPEC_2")
TOP_CLASSES = ("v3", "v4", "v5", "amended", "meta", "terminator", "narrative")
NEST_CLASSES = ("v3", "v4", "v5", "amended", "narrative")
INDENTS = ("  ", "    ", "\t", "  \t")
PADS = ("", "", "", " ", "\t")


def split_ops(chain):
    """The operations of a one-line chain (a `]=>` outside quotes separates two), so that
    the chain can be written with continuation lines."""
    parts, start, quoted, escaped = [], 0, False, False
    for k, c in enumerate(chain):
        if quoted:
            if escaped:
                escaped = False
            elif c == "\\":
                escaped = True
            elif c == '"':
                quoted = False
        elif c == '"' and k > 0 and chain[k - 1] == "=":
            quoted = True
        elif c == "]" and chain.startswith("]=>", k):
            parts.append(chain[start:k + 1])
            start = k + 3
    parts.append(chain[start:])
    return parts


class DocGenerator:
    def __init__(self, seed):
        self.rng = random.Random(seed)
        self.chains = ChainGenerator(seed + 1)
        reg = default_registry()
        self.top = [d for d in reg.declarations if reg.decl_class[d] in TOP_CLASSES]
        self.nest = [d for d in reg.declarations if reg.decl_class[d] in NEST_CLASSES]
        self.double, self.prose = reg.double, reg.prose
        self.verbs = frozenset(reg.verbs) | frozenset(reg.aliases)

    # ---------------------------------------------------------------- pieces
    def w(self, n=1):
        return "_".join(self.rng.choice(WORDS) for _ in range(n))

    def head(self):
        return self.rng.choice(("%s, %s:%s" % (self.rng.choice(ENTITIES), self.w(), self.w()),
                                "%s|conf:confirmed|scope:%s" % (self.w(2), self.w()),
                                "%s⇒%s" % (self.w(2), self.w().upper()),
                                "%s|G:{Claude:0.9,Gemini:0.5}|Θ:%s" % (self.w(), self.w()), "",
                                "key:%s|value:%s %s|conf:3/5" % (self.w(), self.w(), self.w())))

    def addr(self):
        return self.rng.choice(("@SUN→@OPUS", "@SUN", "@SUN ∧ @OPUS", "", "@A→@B"))

    def header(self, name, prefix=""):
        sub = "::" + self.rng.choice(("CORE", "DEMO")) if name == "MODULE" and self.rng.random() < 0.5 else ""
        hd = "{%s}{%s}" % (self.addr(), self.w()) if name in self.double else "{%s}" % self.head()
        return prefix + "::" + name + sub + self.rng.choice(("", "", " ")) + hd

    def chain(self, header_safe=False):
        """A chain; header_safe keeps it fit to trail a declaration header on its line (no
        brace, which would change the header's shape, and no `@` token the header's entity
        scan would refuse)."""
        while True:
            c = self.chains.chain()
            if not header_safe or ("{" not in c and "}" not in c and not bad_entity(c)):
                return c

    def body_text(self, parent):
        """One B1 to B6 line (binds, notes and annotations included) for the given parent."""
        kinds = ["b1", "b1", "b2", "b3", "b4", "b5", "bind", "note", "annot"]
        if parent in self.prose:
            kinds += ["b6", "b6", "sic"]
        k = self.rng.choice(kinds)
        if k == "b1":
            return self.rng.choice(("T:%s" % self.w(2), "T:%s|when:%s" % (self.w(), self.w()),
                                    "A:%s⇒%s" % (self.w(), self.w()), "T:%s %s" % (self.rng.choice(ENTITIES), self.w())))
        if k == "b2":
            return "%s:%s" % (self.rng.choice(KEYS), self.rng.choice((self.w(), " %s and %s" % (self.w(), self.w()))))
        if k == "b3":
            return "M:M%d|conf:0.%d" % (self.rng.randint(1, 8), self.rng.randint(10, 99))
        if k == "b4":
            return "V:[int=0.%d,cap=0.%d]" % (self.rng.randint(10, 99), self.rng.randint(10, 99))
        if k == "b5":
            return self.rng.choice(("[%s] %s text" % (self.rng.choice(TAGS), self.w()),
                                    "[%s:%s]" % (self.rng.choice(TAGS), self.w()),
                                    "[%s:%s][%s]" % (self.rng.choice(TAGS), self.w(), self.rng.choice(TAGS))))
        if k == "bind":
            return "T[%d]=%d" % (self.rng.randint(0, 9), self.rng.randint(1990, 2030))
        if k == "note":
            return self.rng.choice(("T[%d] %s" % (self.rng.randint(0, 9), self.w()), "T[a]→T[b] sequence",
                                    "PARALLEL{a, b} simultaneous"))
        if k == "annot":
            return "→ " + self.w(2)
        if k == "b6":
            return "%s %s is prose." % (self.w().capitalize(), self.w())
        return "[sic] %s bracket-initial prose" % self.w()

    def flush_text(self, parent):
        while True:
            t = self.body_text(parent)
            if is_body_form(t, self.verbs):
                return t

    # ---------------------------------------------------------------- blocks
    def nested(self, ind):
        name = self.rng.choice(self.nest)
        out = [ind + self.header(name)]
        deeper = ind + self.rng.choice(("  ", "\t", "    "))
        out.extend(deeper + self.body_text(name) for _ in range(self.rng.choice((0, 0, 1, 2, 3))))
        return out

    def body(self, name, ind):
        out = []
        for _ in range(self.rng.randint(1, 5)):
            r = self.rng.random()
            if r < 0.15:
                parts = split_ops(self.chain())
                out.append(ind + parts[0])
                out.extend(ind + self.rng.choice(("  ", "    ", "\t")) + "=>" + p for p in parts[1:])
            elif r < 0.30:
                out.extend(self.nested(ind))
            elif r < 0.36:
                out.append(ind + self.rng.choice(("::LATENCY{%d}" % self.rng.randint(0, 9), "::CONFIDENCE{1.0}")))
            elif r < 0.42 and out:
                out.append(self.rng.choice(("", " ")))            # a blank line inside an indented body
                out.append(ind + self.body_text(name))
            else:
                out.append(ind + self.body_text(name))
        return out

    def brace_decl(self, prefix=""):
        name = self.rng.choice(self.top)
        lines = [self.header(name, prefix)]
        style = self.rng.choice(("none", "indent", "indent", "flush", "trailing"))
        if name in self.double and style in ("flush", "trailing"):
            style = "indent"                                     # a double-brace header ends with its brace
        if style == "none":
            return lines
        if style == "flush":
            return lines + [self.flush_text(name) for _ in range(self.rng.randint(1, 3))]
        if style == "trailing":
            token = self.body_text(name) if self.rng.random() < 0.6 else self.chain(header_safe=True)
            lines[0] += self.rng.choice((" ", "   ", "\t")) + token
            if self.rng.random() < 0.5:
                return lines
        return lines + self.body(name, self.rng.choice(INDENTS))

    def span_decl(self):
        name = self.rng.choice(self.top)
        double = name in self.double
        open_ = "::" + name + ("::CORE" if name == "MODULE" else "") + ("{%s}{" % self.addr() if double else "{")
        content = ["%s > %s > %s" % (self.w(), self.w(), self.w()), "%s⇒%s" % (self.w(), self.w()),
                   "[WHAT] %s" % self.w(), "LAYER[%s] ∧ LAYER[%s]" % (self.w(), self.w()),
                   "SURFACE: %s = %s" % (self.w(), self.w())]
        body = [self.rng.choice(("  ", "")) + self.rng.choice(content) for _ in range(self.rng.randint(0, 3))]
        if self.rng.random() < 0.5:
            return [open_] + body + [self.rng.choice(("}", "  }"))]
        last = self.rng.choice(("  %s}" % self.w(), "}", "  Θ:%s=%s}" % (self.w(), self.w())))
        return [open_ + self.w() + "|"] + [ln + "|" for ln in body] + [last]

    def opaque(self):
        delim = "EOF_" + self.w().upper()
        lines = ["::UNTRUSTED{id:u%d|source:user|delimiter:%s}" % (self.rng.randint(1, 9), delim)]
        for _ in range(self.rng.randint(0, 4)):
            lines.append(self.rng.choice(("<<<" + delim, "::GENE{%s}" % self.w(), "  [READ:@SRC] %s" % self.w(), "",
                                          "free %s  " % self.w())))
        lines.append(self.rng.choice((delim, "  " + delim)))
        return lines

    def top_text(self):
        return self.rng.choice(("[%s:%s]" % (self.rng.choice(TAGS), self.w()),
                                "T[%d]=%d" % (self.rng.randint(0, 20), self.rng.randint(1990, 2030)),
                                "T[%d] %s" % (self.rng.randint(0, 9), self.w()), "→ " + self.w(2),
                                "<<<EOF_%s" % self.w(), "::LATENCY{%d}" % self.rng.randint(0, 5),
                                "T[%d] ::CONFIDENCE{0.9}" % self.rng.randint(0, 5)))

    def pad(self, block):
        return [line + self.rng.choice(PADS) if line.strip() else line for line in block]

    # ---------------------------------------------------------------- document
    def document(self):
        rng = self.rng
        lines = [rng.choice(("::ILANG::v5.0", "::ILANG::v5.0::SPEC", "::ILANG::v4.0"))]
        lines += ["".join("[%s:%s]" % (rng.choice(PREAMBLE_TAGS), self.w()) for _ in range(rng.randint(1, 3)))
                  for _ in range(rng.choice((0, 0, 1, 2)))]
        lines += ["%s %s by %s" % (self.w().capitalize(), self.w(), self.w()) for _ in range(rng.choice((0, 0, 1)))]
        for k in range(rng.randint(3, 10)):
            r = rng.random() if k else rng.random() * 0.62      # the first block is a construct: the preamble ends there
            if r < 0.40:
                block = self.pad(self.brace_decl())
            elif r < 0.50:
                block = self.pad(self.brace_decl(prefix="T[%d]%s" % (rng.randint(0, 9), rng.choice((" ", "  ", "\t")))))
            elif r < 0.62:
                block = self.pad(self.span_decl())
            elif r < 0.68:
                block = self.opaque()                            # verbatim lines: no padding
            elif r < 0.84:
                parts = split_ops(self.chain())
                if rng.random() < 0.5:
                    block = [parts[0]] + [rng.choice(("  ", "")) + "=>" + p for p in parts[1:]]
                else:
                    block = ["=>".join(parts)]
                block = self.pad(block)
            else:
                block = self.pad([self.top_text()])
            lines += block
            if rng.random() < 0.3:
                lines.append(rng.choice(("", "---", "  ")))
        if rng.random() < 0.3:
            lines.append("::ILANG::v5.0::END")
        return "\n".join(lines) + "\n"
