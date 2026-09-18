"""Command line: python -m iml <command> [option] [FILE]

  compile [--document] [FILE]
                          read I-Lang chains and print one IML 0.4 message per chain;
                          with --document, print one document: the header alone on the
                          first line, then one chain per line. A chain is one line, or
                          one line followed by continuation lines whose first non-blank
                          characters are `=>` (canon PATCH-2 section 1.7); a blank line
                          ends a chain. An error is reported at the chain's first line,
                          with the offset counted in the joined text
  decompile [--version V] [FILE]
                          read IML and print canonical I-Lang, one line per chain. The
                          form is decided by the first line: a header alone opens a
                          document, and every following line is one chain; a header
                          followed by a chain is a message, and every non-empty line is
                          then one message. V is 0.4 (default; the same reader reads a
                          0.3 header, so 0.3 is not a value of V) or 0.2 (the 0.2
                          surface, read only: one message per line)
  roundtrip FILE          for every I-Lang chain (continuation lines joined as in
                          compile): parse -> compile -> decompile -> compare; print the
                          IML message and the canonical I-Lang; then the same for the
                          document of all chains; exit 1 on any failure
  check-registry [PATH]   load the registry, verify its digest, print the counts

FILE `-` or no FILE reads standard input. Input is UTF-8; `\\r\\n` is accepted as a line
end. Blank lines are skipped in I-Lang input (where they end a chain) and in a stream
of messages; inside a document a blank line is an error. The codec fails closed: the
first error stops the command with exit code 1 and `<file>:<line>: <error>` on
standard error.
"""

import sys

from . import __version__
from .codec import DEFAULT_VERSION, VERSIONS, compile, compile_document, decompile, is_document, surface
from .errors import IMLError
from .l2 import CONTINUATION, parse_L2, print_L2
from .registry import RegistryError, default_registry, load_registry


def read_text(path):
    if path is None or path == "-":
        data = sys.stdin.buffer.read().decode("utf-8")
        name = "<stdin>"
    else:
        with open(path, "rb") as f:
            data = f.read().decode("utf-8")
        name = path
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
    continues the current chain (canon PATCH-2 section 1.7, the validator's B8 rule):
    its leading whitespace is stripped and the rest is appended to the chain's text;
    trailing whitespace stays in the text and is E300 in parse_L2 as before. A blank
    line ends the current chain. A continuation line with no current chain (the first
    non-blank line of the input, or the first after a blank line) is an orphan: it is
    kept as its own entry, stripped, so that parse_L2 reports it at its own line as
    E300 "orphan `=>` continuation: no preceding operation line"; it opens no chain.
    So a chain's line number is its first line and an error offset counts in the
    joined text."""
    out = []
    open_chain = False
    for no, line in enumerate(data.split("\n"), start=1):
        if line.endswith("\r"):
            line = line[:-1]
        if not line:
            open_chain = False
            continue
        stripped = line.lstrip()
        if stripped.startswith(CONTINUATION):
            if open_chain:
                first, text = out[-1]
                out[-1] = (first, text + stripped)
            else:
                out.append((no, stripped))
            continue
        out.append((no, line))
        open_chain = True
    return out


def report(name, no, err):
    print("%s:%d: %s" % (name, no, err), file=sys.stderr)


def cmd_compile(path, document):
    name, data = read_text(path)
    chains = join_chain_lines(data)
    if not document:
        for no, text in chains:
            try:
                print(compile(parse_L2(text)))
            except IMLError as e:
                report(name, no, e)
                return 1
        return 0
    asts = []
    for no, text in chains:
        try:
            asts.append(parse_L2(text))
        except IMLError as e:
            report(name, no, e)
            return 1
    if not asts:
        report(name, 1, IMLError("E300", "no I-Lang chain to compile: a document carries at least one chain", 0))
        return 1
    print(compile_document(asts))
    return 0


def cmd_decompile(path, version):
    name, data = read_text(path)
    if version == DEFAULT_VERSION and is_document(data):
        try:
            chains = decompile(data)
        except IMLError as e:
            no = data.count("\n", 0, e.offset) + 1 if e.offset is not None else 1
            report(name, no, e)
            return 1
        for chain in chains:
            print(print_L2(chain))
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
    chains = join_chain_lines(data)
    failed = 0
    asts = []
    for no, text in chains:
        try:
            ast = parse_L2(text)
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
        asts.append(ast)
    if asts:
        try:
            document = compile_document(asts)
            back = decompile(document)
            ok = back == asts and compile_document(back) == document
        except IMLError as e:
            report(name, 0, e)
            return 1
        print("document %s (%d chains under one header, %d lines)"
              % ("OK" if ok else "FAIL", len(asts), document.count("\n") + 1))
        if not ok:
            failed += 1
    print("%d chain(s), %d failure(s)" % (len(chains), failed))
    return 1 if failed else 0


def cmd_check_registry(path):
    try:
        reg = load_registry(path) if path else default_registry()
    except RegistryError as e:
        print("registry: %s" % e, file=sys.stderr)
        return 1
    roots = sum(1 for v in reg.verbs if v in reg.verb_root)
    print("registry %s" % (reg.path or "<default>"))
    print("registry version %s (the vocabulary of 0.2, unchanged in 0.3 and 0.4)" % reg.version)
    print("canon commit %s" % reg.commit)
    print("verbs %d (roots %d, OUT has none), aliases %d, keys %d, entities %d"
          % (len(reg.verbs), roots, len(reg.aliases), len(reg.keys), len(reg.entities)))
    print("digest %s" % reg.digest)
    print("header %s" % reg.header)
    for v in sorted(surface(DEFAULT_VERSION).reads - {DEFAULT_VERSION}, reverse=True):
        print("header %s (read by the default reader)" % reg.header_for(v))
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
            stream.reconfigure(encoding="utf-8")
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
    except RegistryError as e:
        print("registry: %s" % e, file=sys.stderr)
        return 1
    except OSError as e:
        print("cannot read input: %s" % e, file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
