"""IML (I-Lang Machine Layer) reference codec, release 0.6.2: the declaration layer under the 0.6 header.

    from iml import parse_L2, print_L2, compile, decompile, parse_doc, print_doc, compile_doc, decompile_doc
    chain = parse_L2("[READ:@GH|path=readme.md]=>[XLAT|lng=zh]=>[FMT|fmt=md]=>[Ω]")
    message = compile(chain)            # "#iml/0.6/<12 hex> RD@GHpt=readme.md XLln=zh FMfm=md $"
    assert decompile(message) == chain  # L1, chains
    doc = parse_doc("::ILANG::v5.0\\n::GENE{verify_first|conf:confirmed}\\n  T:check_before_execute\\n")
    iml_text = compile_doc(doc)         # header, `"::ILANG::v5.0"`, `:GN"verify_first|conf:confirmed"`, ` "T:check_before_execute"`
    assert decompile_doc(iml_text) == doc                               # L1, documents
    assert print_doc(doc).endswith("::GENE{verify_first|conf:confirmed}\\n  T:check_before_execute")
    decompile("#iml/0.4/88d05d0839c1 RD@GHpt=readme.md XLln=zh FMfm=md $")  # a 0.4 (or 0.3) header, chains only
    decompile("#iml/0.2/88d05d0839c1 RDΦGHpt=readme.md→XLln=zh→FMfm=md→Ω", version="0.2")  # the 0.2 surface, read only

Standard library only. Three registries, derived from the I-Lang canon by
tools/derive_registry.py: registry/iml-registry-0.6.json (the default, derived at the commit
of canon/PIN: the chain tables plus the 50 declarations with their codes; digest
ba5fde00dd69...), registry/iml-registry-0.5.json (the declaration registry of 0.5, 49
declarations, frozen: a 0.5 header names it and a 0.5 document is read with its tables;
digest 7e29fae7f5ea...) and registry/iml-registry-0.2.json (the chain registry of 0.2, 0.3
and 0.4, frozen; digest 88d05d0839c1...). compile and compile_doc write the 0.6 header.
Since 0.5 IML carries a whole raw I-Lang document: declarations with their block shapes and
bodies, and every other line as exact text (SPEC-IML-0.5.md; SPEC-IML-0.6.md states what 0.6
changes).
"""

from .codec import (DEFAULT_VERSION, VERSIONS, Chain, Op, Value, compile, compile_document,
                    decompile, is_document)
from .doc_ast import Decl, Text
from .doc_codec import compile_doc
from .doc_parse import parse_doc
from .doc_print import print_doc
from .doc_read import decompile_doc
from .errors import CODES, IMLError
from .l2 import parse_L2, print_L2
from .registry import Registry, RegistryError, default_registry, load_registry

__version__ = "0.6.2"

__all__ = [
    "Chain", "Op", "Value", "compile", "compile_document", "decompile", "is_document",
    "parse_L2", "print_L2", "DEFAULT_VERSION", "VERSIONS",
    "Text", "Decl", "parse_doc", "print_doc", "compile_doc", "decompile_doc",
    "IMLError", "CODES", "Registry", "RegistryError", "load_registry", "default_registry",
    "__version__",
]
