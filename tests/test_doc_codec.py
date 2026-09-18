"""The IML 0.5 document form (design-0.5 sections 4, 6 and 7): the examples of section 4
with the derived codes, the line grammar, headers and versions, hand-built ASTs, the
round-trip validation of decompile, and the command line."""

import contextlib
import io
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from iml import (Chain, Decl, IMLError, Op, Text, compile, compile_doc, compile_document, decompile,  # noqa: E402
                 decompile_doc, default_registry, doc_codec, parse_doc, parse_L2, print_doc)
from iml.__main__ import main  # noqa: E402

H5 = "#iml/0.5/7e29fae7f5ea"
H4 = "#iml/0.4/88d05d0839c1"
DESIGN_SRC = """::ILANG::v5.0::SPEC
[TYPE:protocol_specification]
::STATE{@OPUS, role:strategic_review}
::GENE{verify_first|conf:confirmed|scope:global}
  T:check_before_execute
  A:blind_execution⇒fatal
  ::PRIOR{clarification:ask_when_irreversible}
::ACTIVATE{support_agent_v1|protocol:iLang_v5.0}
  [PARS:@SYS_PROMPT|fmt=text]=>[RUN:@ALL]=>[Ω]
::PRIORITY{
  explicit_user_instruction > objective > default
}
::GENE_MUTABLE{communication_style|
  T:conclusions_first|
  Θ:task_type=report}
::SAY{@SUN→@OPUS}{∃(language) ∧ NATIVE(AI) ?}
::DISCOVER{@SUN}{
  LAYER[safety] ∧ LAYER[honesty] ⇒ CONTRADICTION
}
T[0] ::EVENT{1998|entered_wuhan_university}
::MODULE::CORE{
}
"""
DESIGN_IML = H5 + """
"::ILANG::v5.0::SPEC"
"[TYPE:protocol_specification]"
:ST"@OPUS, role:strategic_review"
:GN"verify_first|conf:confirmed|scope:global"
 "T:check_before_execute"
 "A:blind_execution⇒fatal"
 :PI"clarification:ask_when_irreversible"
:AC"support_agent_v1|protocol:iLang_v5.0"
 PS@{SYS_PROMPT}fm=text RN@{ALL} $
:PT{
 "explicit_user_instruction > objective > default"
:GM{"communication_style|"
 "T:conclusions_first|"
 "Θ:task_type=report"
:SY"@SUN→@OPUS""∃(language) ∧ NATIVE(AI) ?"
:DS"@SUN"{
 "LAYER[safety] ∧ LAYER[honesty] ⇒ CONTRADICTION"
:ETT"0""1998|entered_wuhan_university"
:ML::CORE{"""


def run_cli(*args, stdin=None):
    r = subprocess.run([sys.executable, "-m", "iml", *args], cwd=str(ROOT),
                       input=None if stdin is None else stdin.encode("utf-8"), capture_output=True)
    r.stdout = r.stdout.decode("utf-8").replace("\r\n", "\n")
    r.stderr = r.stderr.decode("utf-8").replace("\r\n", "\n")
    return r


class TestDocumentForm(unittest.TestCase):
    def test_design_examples_with_the_derived_codes(self):
        items = parse_doc(DESIGN_SRC)
        self.assertEqual(compile_doc(items), DESIGN_IML)
        self.assertEqual(decompile_doc(DESIGN_IML), items)
        self.assertEqual(decompile(DESIGN_IML), items)
        self.assertEqual(compile_doc(decompile_doc(DESIGN_IML)), DESIGN_IML)
        self.assertEqual(print_doc(decompile_doc(DESIGN_IML)), DESIGN_SRC.rstrip("\n"))

    def test_quoting_and_empty_texts(self):
        items = [Text('say "hi" \\ there'), Decl("SILENCE"), Decl("FACT", head="")]   # colophon prose comes first
        iml = compile_doc(items)
        self.assertEqual(iml.split("\n")[1:], ['"say \\"hi\\" \\\\ there"', ':SL""', ':FC""'])
        self.assertEqual(decompile_doc(iml), items)

    def test_nested_body_lines_and_module_sub(self):
        items = parse_doc("::LESSON{l}\n  ::SAY{@A}{hi}\n    T:x\n  ::MODULE::IN{m}\n    free prose\n  T:y")
        iml = compile_doc(items)
        self.assertEqual(iml.split("\n")[1:], [':LS"l"', ' :SY"@A""hi"', '  "T:x"', ' :ML::IN"m"', '  "free prose"',
                                               ' "T:y"'])
        self.assertEqual(decompile_doc(iml), items)

    def test_chains_only_documents_keep_the_0_4_lines(self):
        chains = [parse_L2("[READ:@GH]=>[Ω]"), parse_L2("[LIST:@LOCAL|mch=*.md]=>[Π:READ]=>[Σ]=>[Ω]")]
        d5 = compile_document(chains)
        self.assertEqual(d5, compile_doc(chains))
        self.assertEqual(d5, H5 + "\nRD@GH $\nLS@LCmc=*.md BT:RD MR $")
        self.assertEqual(decompile(d5), chains)
        self.assertEqual(decompile(H4 + d5[len(H5):]), chains)               # a 0.4 document, same reader
        self.assertEqual(decompile_doc(H4 + d5[len(H5):]), chains)

    def test_headers_and_versions(self):
        reg = default_registry()
        self.assertEqual(reg.header, H5)
        self.assertTrue(compile(parse_L2("[READ]")).startswith(H5 + " "))
        for text, code in ((H4 + '\n:ST"a"', "E502"), ("#iml/0.3/88d05d0839c1\n\"x\"", "E502"),
                           (H4 + "\n RD", "E300"), (H5 + ' :ST"a"', "E502"), (H5 + ' "x"', "E502"),
                           ("#iml/0.5/88d05d0839c1\nRD", "E502"), ("#iml/0.2/88d05d0839c1\nRD", "E502"),
                           (H5, "E300"), (H5 + "\n", "E300"), (H4 + ' :ST"a"', "E502"),
                           ('#iml/0.3/88d05d0839c1 "x"', "E502")):
            with self.assertRaises(IMLError) as cm:
                decompile(text)
            self.assertEqual(cm.exception.code, code, text)
        with self.assertRaises(IMLError) as cm:
            decompile_doc(H5 + " RD")
        self.assertEqual(cm.exception.code, "E502")
        with self.assertRaises(ValueError):
            compile(parse_L2("[READ]"), version="0.4")

    def test_decompile_validates_by_round_trip(self):
        for line, what in (('"::STATE{@A, k:v}"', "Decl"), ('"[READ:@SRC]=>[Ω]"', "Chain")):
            with self.assertRaises(IMLError) as cm:
                decompile_doc(H5 + "\n" + line)
            self.assertEqual(cm.exception.code, "E300")
            self.assertIn("not the canonical spelling", cm.exception.message)
            self.assertIn(what, cm.exception.message)
            self.assertEqual(cm.exception.offset, len(H5) + 1)

    def test_a_preamble_chain_is_refused_with_the_reader_s_message(self):
        """0.5.1: a one-operation chain in preamble position whose print is a tag line; the
        decoder refuses it with the message parse_doc gives the I-Lang source."""
        for chain in ("[MERGE]", "[BATC:READ]", "[DIFF:@SRC]"):
            line = compile(parse_L2(chain)).split(" ", 1)[1]
            iml = H5 + '\n"::ILANG::v5.0"\n' + line
            with self.assertRaises(IMLError) as cm:
                decompile_doc(iml)
            self.assertEqual((cm.exception.code, cm.exception.offset, cm.exception.item), ("E300", iml.rindex("\n") + 1, 1))
            self.assertIn("a one-operation chain in preamble position prints as a tag line", cm.exception.message)
            after = H5 + '\n"::ILANG::v5.0"\n:FC"a:b"\n' + line                 # after the preamble: a chain
            self.assertEqual(decompile_doc(after)[2], parse_L2(chain))
        with self.assertRaises(IMLError) as cm:
            compile_doc([Text("::ILANG::v5.0"), parse_L2("[MERGE]")])
        self.assertEqual((cm.exception.code, cm.exception.item), ("E300", 1))
        self.assertIn("preamble position", cm.exception.message)

    def test_messages_that_name_the_document_parts(self):
        for text, fn, message in ((H5 + '\n"abc', decompile_doc, "unterminated quote in a text line"),
                                  (H5 + '\n:FC"abc', decompile_doc, "unterminated quote in a declaration header"),
                                  ('[READ|path="abc]', parse_L2, "unterminated quoted value"),
                                  (H5, decompile, "header alone: a document carries at least one item line after the header"),
                                  (H4, decompile, "header alone: a document carries at least one chain line after the header"),
                                  (H4 + ' :GN"a"', decompile, "declarations and text lines need a 0.5 header (this message's"
                                   " header is version 0.4)"),
                                  ('#iml/0.3/88d05d0839c1 "x"', decompile, "declarations and text lines need a 0.5 header")):
            with self.subTest(text=text):
                with self.assertRaises(IMLError) as cm:
                    fn(text)
                self.assertTrue(cm.exception.message.startswith(message), cm.exception.message)

    def test_hand_built_asts_are_validated_on_compile(self):
        for items, code in (([], "E300"), ([Text("a\nb")], "E300"), ([Text("a\tb")], "E300"),
                            ([Decl("WIDGET")], "E300"), ([Decl("STATE", sub="X")], "E300"),
                            ([Decl("SAY", head="x")], "E300"), ([Decl("FACT", addr="a", head="x")], "E300"),
                            ([Decl("FACT", shape="set", head="x")], "E300"), ([Decl("FACT", shape="opaque", head="x")], "E300"),
                            ([Decl("GENE", body=[Decl("PRIOR", prefix="1")])], "E300"),
                            ([Decl("GENE", body=[Decl("PRIOR", body=[Chain([Op("READ")])])])], "E300"),
                            ([Decl("GENE", body=[Chain([Op("REED")])])], "E304"),
                            ([Text("::STATE{@A}")], "E300"), ([Decl("FACT"), Text("T:x")], "E300"),
                            ([Decl("GENE_MUTABLE", shape="wrapped", head="x")], "E300")):
            with self.subTest(items=items):
                with self.assertRaises(IMLError) as cm:
                    compile_doc(items)
                self.assertEqual(cm.exception.code, code)
        with self.assertRaises(ValueError):
            Decl("FACT", shape="round")


class TestDocumentCli(unittest.TestCase):
    def test_compile_document_decompile_and_roundtrip(self):
        r = run_cli("compile", "--document", stdin=DESIGN_SRC)
        self.assertEqual((r.returncode, r.stdout), (0, DESIGN_IML + "\n"), r.stderr)
        r = run_cli("decompile", stdin=DESIGN_IML + "\n")
        self.assertEqual((r.returncode, r.stdout), (0, DESIGN_SRC), r.stderr)
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "doc.ilang"
            p.write_bytes(DESIGN_SRC.encode("utf-8"))
            r = run_cli("roundtrip", str(p))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn(":9 OK", r.stdout)
        self.assertIn("document OK (11 items under one header: 0 chains, 9 declarations, 2 text lines; 20 lines)", r.stdout)
        self.assertIn("1 chain(s), 0 failure(s)", r.stdout)

    def test_message_form_refuses_declarations(self):
        r = run_cli("compile", stdin="[READ]\n::STATE{@A, k:v}\n")
        self.assertEqual(r.returncode, 1)
        self.assertEqual(r.stdout, H5 + " RD\n")
        self.assertIn("<stdin>:2: E502", r.stderr)
        self.assertIn("carried in the document form: compile --document", r.stderr)
        r = run_cli("compile", stdin="  [READ]\n")
        self.assertIn("<stdin>:1: E300", r.stderr)                         # leading whitespace, as in 0.4

    def test_errors_name_their_line(self):
        r = run_cli("compile", "--document", stdin="::ILANG::v5.0\n::FACT{a:b}\n::GENE{g}\n  free prose\n")
        self.assertEqual((r.returncode, r.stdout), (1, ""))
        self.assertIn("<stdin>:4: E300 Syntax Error: B6 prose body line inside non-prose ::GENE", r.stderr)
        r = run_cli("decompile", stdin=H5 + '\n:ST"a"\n:ZZ"b"\n')
        self.assertEqual(r.returncode, 1)
        self.assertIn("<stdin>:3: E300", r.stderr)
        self.assertIn("unknown declaration code 'ZZ'", r.stderr)
        r = run_cli("compile", "--document", stdin="\n\n")
        self.assertEqual(r.returncode, 1)
        self.assertIn("a document carries at least one item", r.stderr)

    def test_version_flags(self):
        for v in ("0.3", "0.4"):
            r = run_cli("decompile", "--version", v, stdin="")
            self.assertEqual(r.returncode, 2)
            self.assertIn("default reader", r.stderr)
        r = run_cli("decompile", "--version", "0.5", stdin=H4 + "\nRD\n")
        self.assertEqual((r.returncode, r.stdout), (0, "[READ]\n"), r.stderr)
        r = run_cli("--version")
        self.assertEqual(r.stdout.strip(), "iml 0.5.1")


class TestReportLines(unittest.TestCase):
    """0.5.1: an error of the document writer's check, which reads the canonical print back,
    is reported at the first source line of the item it names, by compile --document and by
    roundtrip; 0.5.0 reported line 1 or a line counted in the print, and roundtrip line 0.
    The check is made to fail by standing in for the reader it calls."""

    SRC = "::ILANG::v5.0\n\n::FACT{a:b}\n::GENE{g}\n  T:x\n  T:y\n[READ]=>[\u03a9]\n"   # items at lines 1, 3, 4, 7

    @staticmethod
    def run_main(args):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = main(args)
        return code, out.getvalue(), err.getvalue()

    def test_errors_of_the_canonical_check_name_the_item_s_first_line(self):
        real = doc_codec.parse_doc

        def reads_back_otherwise(text, reg=None):
            back = real(text, reg)
            back[2] = Decl("GENE", head="other")
            return back

        def fails_in_the_print(text, reg=None):
            raise IMLError("E300", "probe", text.index("T:y"))

        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "doc.ilang"
            p.write_bytes(self.SRC.encode("utf-8"))
            self.assertEqual(self.run_main(["compile", "--document", str(p)])[0], 0)
            for fake, message in ((reads_back_otherwise, "not the canonical spelling of a construct: item 2"),
                                  (fails_in_the_print, "probe")):
                with mock.patch("iml.doc_codec.parse_doc", fake):
                    for args in (["compile", "--document", str(p)], ["roundtrip", str(p)]):
                        with self.subTest(fake=fake.__name__, args=args[0]):
                            code, out, err = self.run_main(args)
                            self.assertEqual(code, 1)
                            self.assertIn("%s:4: E300 Syntax Error: %s" % (p, message), err)
                            self.assertNotIn("%s:0:" % p, err)


if __name__ == "__main__":
    unittest.main()
