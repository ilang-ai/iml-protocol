"""IML (I-Lang Machine Layer) 0.2 reference codec.

    from iml import parse_L2, print_L2, compile, decompile
    chain = parse_L2("[READ:@GH|path=readme.md]=>[XLAT|lng=zh]=>[FMT|fmt=md]=>[Ω]")
    message = compile(chain)            # "#iml/0.2/<12 hex> RDΦGHpt=readme.md→XLln=zh→FMfm=md→Ω"
    assert decompile(message) == chain  # L1
    assert print_L2(chain) == "[READ:@GH|path=readme.md]=>[XLAT|lng=zh]=>[FMT|fmt=md]=>[Ω]"

Standard library only. The registry is registry/iml-registry-0.2.json, derived from the
I-Lang canon at the pinned commit by tools/derive_registry.py.
"""

from .codec import Chain, Op, Value, compile, decompile
from .errors import CODES, IMLError
from .l2 import parse_L2, print_L2
from .registry import Registry, RegistryError, default_registry, load_registry

__version__ = "0.2"

__all__ = [
    "Chain", "Op", "Value", "compile", "decompile", "parse_L2", "print_L2",
    "IMLError", "CODES", "Registry", "RegistryError", "load_registry", "default_registry",
    "__version__",
]
