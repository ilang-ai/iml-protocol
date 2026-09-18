"""Command line: python -m iml <command> [option] [FILE]

  compile [--document] [FILE]
                          without --document: read I-Lang chains and print one IML 0.5
                          message per chain. A chain is one line, or one line followed by
                          continuation lines whose first non-blank characters are `=>`
                          (canon PATCH-2 section 1.7); a continuation line is joined only
                          when the text above it ends with `]` outside a quoted value
                          (E300 otherwise); a blank line, or a line of whitespace only,
                          ends a chain. A declaration or any other line that is not a
                          chain is E502: it is carried in the document form. An error is
                          reported at the chain's first line, with the offset counted in
                          the joined text.
                          with --document: read one whole raw I-Lang document (the
                          declaration layer: declarations with their bodies and spans,
                          chains, and every other line the canon admits, as the pinned
                          validator reads a raw document) and print one IML 0.5 document:
                          the header alone on the first line, then one item per line
  decompile [--version V] [FILE]
                          read IML and print canonical I-Lang. The form is decided by the
                          first line: a header alone opens a document, printed as one
                          I-Lang document (a 0.5 document with its declarations; a 0.4 or
                          0.3 document, chains only, one line per chain); a header
                          followed by a chain is a message, and every non-empty line is
                          then one message. V is 0.5 (default; the same reader reads a 0.4
                          and a 0.3 header, so 0.4 and 0.3 are not values of V) or 0.2
                          (the 0.2 surface, read only: one message per line)
  roundtrip FILE          read FILE as an I-Lang document; for every chain in it: parse ->
                          compile -> decompile -> compare, and print the IML message and
                          the canonical I-Lang; then the same for the whole document
                          (compile --document -> decompile -> compare, and the canonical
                          print read back); exit 1 on any failure
  check-registry [PATH]   load the registry (default: the 0.5 registry, paired with the
                          0.2 chain registry), verify the digests, print the counts

FILE `-` or no FILE reads standard input. Input is UTF-8. One leading byte order mark
(EF BB BF, which Windows PowerShell 5.1 puts in front of text it pipes as UTF-8) is
dropped, on standard input and on FILE; the library functions stay strict and refuse a
U+FEFF at the head of their input (E502). Input that is not valid UTF-8 is E300,
reported at line 1 with the byte offset. `\\r\\n` is accepted as a line end. Blank
lines are skipped in I-Lang input (where they end a chain, and where a line of
whitespace only counts as blank) and in a stream of messages; inside an IML document a
blank line is an error. The codec fails closed: the first error stops the command with
exit code 1 and `<file>:<line>: <error>` on standard error.
"""

import sys

from . import __version__
from .codec import DEFAULT_VERSION, VERSIONS, Chain, compile, decompile, is_document, surface
from .doc_ast import Decl, Text
from .doc_codec import compile_doc
from .doc_parse import parse_doc, parse_doc_lines
from .doc_print import print_doc
from .doc_read import decompile_doc
from .errors import IMLError
from .l2 import CONTINUATION, ends_with_closed_operation, parse_L2, print_L2
from .registry import DOCUMENT_LAYER_VERSIONS, RegistryError, default_registry, load_registry


UNTERMINATED = ("continuation after an unterminated operation line: the text above a `=>` line "
                "must end with `]` outside a quoted value")


class InputError(Exception):
    """Input that cannot be read as text. Carries the name of the input and the IMLError
    that main reports at line 1, on the same path as every other error."""

    def __init__(self, name, error):
        super().__init__(str(error))
        self.name = name
        self.error = error


def read_text(path):
    """(name, text) of FILE or of standard input. The bytes are decoded as UTF-8 and one
    leading byte order mark (EF BB BF) is dropped: Windows PowerShell 5.1 puts one in
    front of text it pipes as UTF-8, and some editors save one. Only the command line is
    lenient here; parse_L2 and decompile refuse a U+FEFF (E502). Bytes that are not
    valid UTF-8 raise InputError with E300 and the byte offset in the input as read."""
    if path is None or path == "-":
        raw = sys.stdin.buffer.read()
        name = "<stdin>"
    else:
        with open(path, "rb") as f:
            raw = f.read()
        name = path
    try:
        data = raw.decode("utf-8-sig")
    except UnicodeDecodeError as e:
        # utf-8-sig reports the position after the byte order mark it dropped
        offset = e.start + len(raw) - len(e.object)
        raise InputError(name, IMLError("E300", "input is not valid UTF-8 (byte offset %d)" % offset)) from None
    return name, data


def non_empty_lines(data):
    """(line number, line) for every non-empty line; a trailing CR is dropped."""
    out = []
    for no, line in enumerate(data.split("\n"), start=1):
        if line.endswith("\r"):
            line = line[:-1]
        if line:
            out.append((no, line))
    return out


def join_chain_lines(data):
    """(first line number, chain text) for every I-Lang chain in data, the compile-side
    reading of lines. Lines are split on `\\n` and one trailing CR is dropped per line,
    as in non_empty_lines. A line whose first non-whitespace characters are `=>`
    continues the current chain (canon PATCH-2 section 1.7, `chain_continuation`; the
    validator reads such lines the same way): its leading whitespace is stripped and
    the rest is appended to the chain's text; trailing whitespace stays in the text and
    is E300 in parse_L2 as before.

    A continuation line is joined only when the text collected so far ends with `]`
    outside a quoted value (ends_with_closed_operation: the quote and escape rules of
    parse_L2). Otherwise the line break stood inside an operation, as in
    `[READ|whr="abc` followed by `=>def"]`, and joining would make a chain that no
    single line spells: the chain is refused. Its entry then holds, in place of the
    text, an IMLError E300 "continuation after an unterminated operation line" whose
    offset is the length of the text collected so far (the place of the line break in
    the joined text); parse_chain raises it, so it is reported at the chain's first
    line like any other error of that chain. Further continuation lines of a refused
    chain are dropped with it.

    A blank line ends the current chain, and so does a line of whitespace only, which
    the validator reads as blank too. A continuation line with no current chain (the
    first non-blank line of the input, or the first after a blank line) is an orphan:
    it is kept as its own entry, stripped, so that parse_L2 reports it at its own line
    as E300 "orphan `=>` continuation: no preceding operation line"; it opens no chain.
    So a chain's line number is its first line and an error offset counts in the
    joined text."""
    out = []
    open_chain = False
    for no, line in enumerate(data.split("\n"), start=1):
        if line.endswith("\r"):
            line = line[:-1]
        stripped = line.lstrip()
        if not stripped:                      # blank, or whitespace only
            open_chain = False
            continue
        if stripped.startswith(CONTINUATION):
            if not open_chain:
                out.append((no, stripped))
                continue
            first, text = out[-1]
            if isinstance(text, IMLError):    # the chain is already refused
                continue
            if ends_with_closed_operation(text):
                out[-1] = (first, text + stripped)
            else:
                out[-1] = (first, IMLError("E300", UNTERMINATED, len(text)))
            continue
        out.append((no, line))
        open_chain = True
    return out


def parse_chain(text):
    """parse_L2 on one entry of join_chain_lines. An entry that the join refused holds
    its IMLError in place of the text; it is raised here."""
    if isinstance(text, IMLError):
        raise text
    return parse_L2(text)


NOT_A_CHAIN = ("carried in the document form: compile --document (a declaration or any other line that is not"
               " an operation chain has no message form)")


def report(name, no, err):
    print("%s:%d: %s" % (name, no, err), file=sys.stderr)


def line_of(data, err):
    """The 1-based line of an error's offset in data (line 1 when it has none)."""
    return data.count("\n", 0, err.offset) + 1 if err.offset is not None else 1


def cmd_compile(path, document):
    name, data = read_text(path)
    if document:
        try:
            items = parse_doc(data)
            if not items:
                raise IMLError("E300", "no I-Lang item to compile: a document carries at least one item", 0)
            text = compile_doc(items)
        except IMLError as e:
            report(name, line_of(data, e), e)
            return 1
        print(text)
        return 0
    for no, text in join_chain_lines(data):
        try:
            if isinstance(text, str) and not text.lstrip().startswith(("[", CONTINUATION, "\ufeff")):
                raise IMLError("E502", NOT_A_CHAIN, 0)
            print(compile(parse_chain(text)))
        except IMLError as e:
            report(name, no, e)
            return 1
    return 0


def cmd_decompile(path, version):
    name, data = read_text(path)
    if version == DEFAULT_VERSION and is_document(data):
        try:
            text = print_doc(decompile(data))
        except IMLError as e:
            report(name, line_of(data, e), e)
            return 1
        print(text)
        return 0
    for no, line in non_empty_lines(data):
        try:
            print(print_L2(decompile(line, version=version)))
        except IMLError as e:
            report(name, no, e)
            return 1
    return 0


def cmd_roundtrip(path):
    name, data = read_text(path)
    try:
        items, chain_lines = parse_doc_lines(data)
    except IMLError as e:
        report(name, line_of(data, e), e)
        return 1
    failed = 0
    for no, ast in chain_lines:
        try:
            message = compile(ast)
            back = decompile(message)
            canon = print_L2(ast)
            ok = (back == ast and print_L2(back) == canon and compile(back) == message
                  and print_L2(parse_L2(canon)) == canon)
        except IMLError as e:
            report(name, no, e)
            return 1
        print("%s:%d %s" % (name, no, "OK" if ok else "FAIL"))
        print("  I-Lang  " + canon)
        print("  IML     " + message)
        if not ok:
            failed += 1
    if items:
        try:
            document = compile_doc(items)
            back = decompile_doc(document)
            printed = print_doc(items)
            ok = (back == items and compile_doc(back) == document and parse_doc(printed) == items
                  and print_doc(parse_doc(printed)) == printed)
        except IMLError as e:
            report(name, 0, e)
            return 1
        decls = sum(1 for x in items if isinstance(x, Decl))
        texts = sum(1 for x in items if isinstance(x, Text))
        lines = document.count("\n") + 1
        if decls == texts == 0:
            print("document %s (%d chains under one header, %d lines)" % ("OK" if ok else "FAIL", len(items), lines))
        else:
            print("document %s (%d items under one header: %d chains, %d declarations, %d text lines; %d lines)"
                  % ("OK" if ok else "FAIL", len(items), len(items) - decls - texts, decls, texts, lines))
        if not ok:
            failed += 1
    print("%d chain(s), %d failure(s)" % (len(chain_lines), failed))
    return 1 if failed else 0


def cmd_check_registry(path):
    try:
        reg = load_registry(path) if path else default_registry()
    except RegistryError as e:
        print("registry: %s" % e, file=sys.stderr)
        return 1
    roots = sum(1 for v in reg.verbs if v in reg.verb_root)
    print("registry %s" % (reg.path or "<default>"))
    if reg.has_declarations:
        print("registry version %s (the chain tables of 0.2 plus the declarations table)" % reg.version)
    else:
        print("registry version %s (the chain registry of 0.2, 0.3 and 0.4)" % reg.version)
    print("canon commit %s" % reg.commit)
    print("verbs %d (roots %d, OUT has none), aliases %d, keys %d, entities %d"
          % (len(reg.verbs), roots, len(reg.aliases), len(reg.keys), len(reg.entities)))
    if reg.has_declarations:
        classes = []
        for d in reg.declarations:
            c = reg.decl_class[d]
            if not classes or classes[-1][0] != c:
                classes.append([c, 0])
            classes[-1][1] += 1
        print("declarations %d (%s), tolerated annotations %s"
              % (len(reg.declarations), ", ".join("%s %d" % (c, n) for c, n in classes), ", ".join(reg.tolerated)))
    print("digest %s" % reg.digest)
    if reg.has_declarations:
        print("chain registry digest %s (the one 0.4, 0.3 and 0.2 headers carry)" % reg.chain_digest)
        print("header %s" % reg.header_for(DEFAULT_VERSION))
    for v in sorted(surface(DEFAULT_VERSION).reads - {DEFAULT_VERSION}, reverse=True):
        print("header %s (read by the default reader, chains only)" % reg.header_for(v))
    for v in VERSIONS:
        if v != DEFAULT_VERSION:
            print("header %s (read only, --version %s)" % (reg.header_for(v), v))
    return 0


def parse_args(cmd, rest):
    """Return (file, document, version) or an error message."""
    document = False
    version = DEFAULT_VERSION
    arg = None
    it = iter(rest)
    for a in it:
        if a == "--document" and cmd == "compile":
            document = True
        elif a == "--version" and cmd == "decompile":
            version = next(it, None)
            if version is not None and version not in VERSIONS and version in surface(DEFAULT_VERSION).reads:
                return ("--version %s is not a reader: the default reader (%s) reads a %s header; "
                        "leave the flag out" % (version, DEFAULT_VERSION, version))
            if version not in VERSIONS:
                return "--version takes one of %s" % ", ".join(VERSIONS)
        elif a.startswith("-") and a != "-":
            return "unknown option %r for %s" % (a, cmd)
        elif arg is None:
            arg = a
        else:
            return "too many arguments"
    return arg, document, version


def main(argv=None):
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", newline="\n")
        except (AttributeError, ValueError):
            pass
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__.strip())
        return 0 if argv else 2
    cmd, rest = argv[0], argv[1:]
    if cmd == "--version":
        print("iml %s" % __version__)
        return 0
    if cmd not in ("compile", "decompile", "roundtrip", "check-registry"):
        print("unknown command %r" % cmd, file=sys.stderr)
        print(__doc__.strip(), file=sys.stderr)
        return 2
    parsed = parse_args(cmd, rest)
    if isinstance(parsed, str):
        print(parsed, file=sys.stderr)
        return 2
    arg, document, version = parsed
    try:
        if cmd == "compile":
            return cmd_compile(arg, document)
        if cmd == "decompile":
            return cmd_decompile(arg, version)
        if cmd == "roundtrip":
            if arg is None:
                print("roundtrip needs a FILE", file=sys.stderr)
                return 2
            return cmd_roundtrip(arg)
        return cmd_check_registry(arg)
    except InputError as e:
        report(e.name, 1, e.error)
        return 1
    except RegistryError as e:
        print("registry: %s" % e, file=sys.stderr)
        return 1
    except OSError as e:
        print("cannot read input: %s" % e, file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
