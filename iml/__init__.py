"""IML (I-Lang Machine Layer) reference codec, release 0.3.0.

    from iml import parse_L2, print_L2, compile, compile_document, decompile
    chain = parse_L2("[READ:@GH|path=readme.md]=>[XLAT|lng=zh]=>[FMT|fmt=md]=>[Ω]")
    message = compile(chain)            # "#iml/0.3/<12 hex> RD@GHpt=readme.md XLln=zh FMfm=md $"
    assert decompile(message) == chain  # L1
    assert print_L2(chain) == "[READ:@GH|path=readme.md]=>[XLAT|lng=zh]=>[FMT|fmt=md]=>[Ω]"
    document = compile_document([chain, chain])   # one header line, then one chain per line
    assert decompile(document) == [chain, chain]  # a document decompiles to a list, in order
    decompile("#iml/0.2/<12 hex> RDΦGHpt=readme.md→XLln=zh→FMfm=md→Ω", version="0.2")  # the 0.2 surface, read only

Standard library only. The registry is registry/iml-registry-0.2.json, derived from the
I-Lang canon at the pinned commit by tools/derive_registry.py and unchanged in 0.3
(digest 88d05d0839c1...). 0.3 changes the surface only: ASCII marks (`@`, `$`, one
space between operations) and a document form that pays the header once.
"""

from .codec import (DEFAULT_VERSION, VERSIONS, Chain, Op, Value, compile, compile_document,
                    decompile, is_document)
from .errors import CODES, IMLError
from .l2 import parse_L2, print_L2
from .registry import Registry, RegistryError, default_registry, load_registry

__version__ = "0.3.1"

__all__ = [
    "Chain", "Op", "Value", "compile", "compile_document", "decompile", "is_document",
    "parse_L2", "print_L2", "DEFAULT_VERSION", "VERSIONS",
    "IMLError", "CODES", "Registry", "RegistryError", "load_registry", "default_registry",
    "__version__",
]
