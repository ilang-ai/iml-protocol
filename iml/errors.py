"""IML codec errors. Codes reuse SPEC.md section 9 (SPEC-IML-0.5.md section 7, unchanged since 0.2).

The codec fails closed: the first error stops it. An error carries the code, a message,
the 0-based character offset into the input where it was detected (None when there is
no text input, e.g. when compiling an AST built by hand), where an operation is known,
the 0-based index of that operation in the chain, and, for an error of the document
writer's checks (compile_doc and decompile_doc read the canonical print back), the 0-based
index of the top-level document item it belongs to (`item`), at whose first source line
the command line reports it.
"""

CODES = {
    "E200": "Entity Not Found",
    "E300": "Syntax Error",
    "E302": "Invalid Modifier",
    "E303": "Invalid Value",
    "E304": "Unknown Verb",
    "E502": "Unsupported Format",
}


class IMLError(Exception):
    def __init__(self, code, message, offset=None, op_index=None, item=None):
        if code not in CODES:
            raise ValueError("unknown error code %r" % code)
        super().__init__(message)
        self.code = code
        self.message = message
        self.offset = offset
        self.op_index = op_index
        self.item = item

    def __str__(self):
        where = []
        if self.offset is not None:
            where.append("offset %d" % self.offset)
        if self.op_index is not None:
            where.append("op %d" % self.op_index)
        tail = " (" + ", ".join(where) + ")" if where else ""
        return "%s %s: %s%s" % (self.code, CODES[self.code], self.message, tail)

    def __repr__(self):
        return "IMLError(%r, %r, offset=%r, op_index=%r)" % (
            self.code, self.message, self.offset, self.op_index)
