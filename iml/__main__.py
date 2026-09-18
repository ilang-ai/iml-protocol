"""Command line: python -m iml <command> [option] [FILE]

  compile [--document] [FILE]
                          read I-Lang chains (one per line) and print one IML 0.3 message
                          per line; with --document, print one document: the header alone
                          on the first line, then one chain per line
  decompile [--version V] [FILE]
                          read IML and print canonical I-Lang, one line per chain. The
                          form is decided by the first line: a header alone opens a
                          document, and every following line is one chain; a header
                          followed by a chain is a message, and every non-empty line is
                          then one message. V is 0.3 (default) or 0.2 (the 0.2 surface,
                          read only: one message per line)
  roundtrip FILE          for every I-Lang line: parse -> compile -> decompile -> compare;
                          print the IML message and the canonical I-Lang; then the same
                          for the document of all lines; exit 1 on any failure
  check-registry [PATH]   load the registry, verify its digest, print the counts

FILE `-` or no FILE reads standard input. Input is UTF-8; `\\r\\n` is accepted as a line
end. Blank lines are skipped in I-Lang input and in a stream of messages; inside a
document a blank line is an error. The codec fails closed: the first error stops the
command with exit code 1 and `<file>:<line>: <error>` on standard error.
"""

import sys

from . import __version__
from .codec import DEFAULT_VERSION, VERSIONS, compile, compile_document, decompile, is_document
from .errors import IMLError
from .l2 import parse_L2, print_L2
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


def report(name, no, err):
    print("%s:%d: %s" % (name, no, err), file=sys.stderr)


def cmd_compile(path, document):
    name, data = read_text(path)
    lines = non_empty_lines(data)
    if not document:
        for no, line in lines:
            try:
                print(compile(parse_L2(line)))
            except IMLError as e:
                report(name, no, e)
                return 1
        return 0
    asts = []
    for no, line in lines:
        try:
            asts.append(parse_L2(line))
        except IMLError as e:
            report(name, no, e)
            return 1
    if asts:
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
    lines = non_empty_lines(data)
    failed = 0
    asts = []
    for no, line in lines:
        try:
            ast = parse_L2(line)
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
    print("%d chain(s), %d failure(s)" % (len(lines), failed))
    return 1 if failed else 0


def cmd_check_registry(path):
    try:
        reg = load_registry(path) if path else default_registry()
    except RegistryError as e:
        print("registry: %s" % e, file=sys.stderr)
        return 1
    roots = sum(1 for v in reg.verbs if v in reg.verb_root)
    print("registry %s" % (reg.path or "<default>"))
    print("registry version %s (the vocabulary of 0.2, unchanged in 0.3)" % reg.version)
    print("canon commit %s" % reg.commit)
    print("verbs %d (roots %d, OUT has none), aliases %d, keys %d, entities %d"
          % (len(reg.verbs), roots, len(reg.aliases), len(reg.keys), len(reg.entities)))
    print("digest %s" % reg.digest)
    print("header %s" % reg.header)
    for v in VERSIONS:
        if v != DEFAULT_VERSION:
            print("header %s (read only)" % reg.header_for(v))
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
