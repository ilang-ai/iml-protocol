"""Command line: python -m iml <command> [FILE]

  compile [FILE]          read I-Lang chains (one per line) and print one IML message per line
  decompile [FILE]        read IML messages (one per line) and print canonical I-Lang per line
  roundtrip FILE          for every I-Lang line: parse -> compile -> decompile -> compare;
                          print the IML and the canonical I-Lang; exit 1 on any failure
  check-registry [PATH]   load the registry, verify its digest, print the counts

FILE `-` or no FILE reads standard input. Input is UTF-8; a trailing CR is dropped from
every line; blank lines are skipped. The codec fails closed: the first error stops the
command with exit code 1 and `<file>:<line>: <error>` on standard error.
"""

import sys

from . import __version__
from .codec import compile, decompile
from .errors import IMLError
from .l2 import parse_L2, print_L2
from .registry import RegistryError, default_registry, load_registry


def read_lines(path):
    if path is None or path == "-":
        data = sys.stdin.buffer.read().decode("utf-8")
        name = "<stdin>"
    else:
        with open(path, "rb") as f:
            data = f.read().decode("utf-8")
        name = path
    out = []
    for no, line in enumerate(data.split("\n"), start=1):
        if line.endswith("\r"):
            line = line[:-1]
        if line:
            out.append((no, line))
    return name, out


def cmd_compile(path):
    name, lines = read_lines(path)
    for no, line in lines:
        try:
            print(compile(parse_L2(line)))
        except IMLError as e:
            print("%s:%d: %s" % (name, no, e), file=sys.stderr)
            return 1
    return 0


def cmd_decompile(path):
    name, lines = read_lines(path)
    for no, line in lines:
        try:
            print(print_L2(decompile(line)))
        except IMLError as e:
            print("%s:%d: %s" % (name, no, e), file=sys.stderr)
            return 1
    return 0


def cmd_roundtrip(path):
    name, lines = read_lines(path)
    failed = 0
    for no, line in lines:
        try:
            ast = parse_L2(line)
            message = compile(ast)
            back = decompile(message)
            canon = print_L2(ast)
            ok = (back == ast and print_L2(back) == canon and compile(back) == message
                  and print_L2(parse_L2(canon)) == canon)
        except IMLError as e:
            print("%s:%d: %s" % (name, no, e), file=sys.stderr)
            return 1
        print("%s:%d %s" % (name, no, "OK" if ok else "FAIL"))
        print("  I-Lang  " + canon)
        print("  IML     " + message)
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
    print("iml_version %s" % reg.version)
    print("canon commit %s" % reg.commit)
    print("verbs %d (roots %d, OUT has none), aliases %d, keys %d, entities %d"
          % (len(reg.verbs), roots, len(reg.aliases), len(reg.keys), len(reg.entities)))
    print("digest %s" % reg.digest)
    print("header %s" % reg.header)
    return 0


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
    if len(rest) > 1:
        print("too many arguments", file=sys.stderr)
        return 2
    arg = rest[0] if rest else None
    try:
        if cmd == "compile":
            return cmd_compile(arg)
        if cmd == "decompile":
            return cmd_decompile(arg)
        if cmd == "roundtrip":
            if arg is None:
                print("roundtrip needs a FILE", file=sys.stderr)
                return 2
            return cmd_roundtrip(arg)
        if cmd == "check-registry":
            return cmd_check_registry(arg)
    except RegistryError as e:
        print("registry: %s" % e, file=sys.stderr)
        return 1
    except OSError as e:
        print("cannot read input: %s" % e, file=sys.stderr)
        return 1
    print("unknown command %r" % cmd, file=sys.stderr)
    print(__doc__.strip(), file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
