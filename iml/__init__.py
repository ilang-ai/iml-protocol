"""IML (I-Lang Machine Layer) reference codec, release 0.5.0: the declaration layer.

    from iml import parse_L2, print_L2, compile, decompile, parse_doc, print_doc, compile_doc, decompile_doc
    chain = parse_L2("[READ:@GH|path=readme.md]=>[XLAT|lng=zh]=>[FMT|fmt=md]=>[Ω]")
    message = compile(chain)            # "#iml/0.5/<12 hex> RD@GHpt=readme.md XLln=zh FMfm=md $"
    assert decompile(message) == chain  # L1, chains
    doc = parse_doc("::ILANG::v5.0\\n::GENE{verify_first|conf:confirmed}\\n  T:check_before_execute\\n")
    iml_text = compile_doc(doc)         # header, `"::ILANG::v5.0"`, `:GN"verify_first|conf:confirmed"`, ` "T:check_before_execute"`
    assert decompile_doc(iml_text) == doc                               # L1, documents
    assert print_doc(doc).endswith("::GENE{verify_first|conf:confirmed}\\n  T:check_before_execute")
    decompile("#iml/0.4/88d05d0839c1 RD@GHpt=readme.md XLln=zh FMfm=md $")  # a 0.4 (or 0.3) header, chains only
    decompile("#iml/0.2/88d05d0839c1 RDΦGHpt=readme.md→XLln=zh→FMfm=md→Ω", version="0.2")  # the 0.2 surface, read only

Standard library only. Two registries, both derived from the I-Lang canon at the pinned
commit by tools/derive_registry.py: registry/iml-registry-0.5.json (the default: the chain
tables plus the 49 declarations with their codes; digest 7e29fae7f5ea...) and
registry/iml-registry-0.2.json (the chain registry of 0.2, 0.3 and 0.4, unchanged, digest
88d05d0839c1...). 0.5 carries a whole raw I-Lang document: declarations with their block
shapes and bodies, and every other line as exact text (SPEC-IML-0.5.md).
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

__version__ = "0.5.0"

__all__ = [
    "Chain", "Op", "Value", "compile", "compile_document", "decompile", "is_document",
    "parse_L2", "print_L2", "DEFAULT_VERSION", "VERSIONS",
    "Text", "Decl", "parse_doc", "print_doc", "compile_doc", "decompile_doc",
    "IMLError", "CODES", "Registry", "RegistryError", "load_registry", "default_registry",
    "__version__",
]
