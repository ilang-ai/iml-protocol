"""tools/measure.py: the tool runs, and the committed 0.5 report reproduces.

0.6 made the 0.6 registry the default, and the report this tool writes is the 0.5
measurement (SPEC-IML-0.5.md section 8; SPEC-IML-0.6.md: the measurement stands). The tool
therefore writes every form it labels 0.5 with the frozen 0.5 registry and names that
registry in its report. Checked here against measurements/0.5-2026-09-18.md, row for row, in
bytes and characters; tokens are not compared (tiktoken is optional, and the tests run
without it). And, since 0.6.2, RULE-SHEET.md does not outgrow the size last recorded for it."""

import contextlib
import importlib.util
import io
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from iml import default_registry  # noqa: E402

REPORT = ROOT / "measurements" / "0.5-2026-09-18.md"
README = ROOT / "README.md"
SHEET = ROOT / "RULE-SHEET.md"
# RULE-SHEET.md as last recorded (README.md, the RULE-SHEET.md row): bytes and characters, at 0.6.2
SHEET_RECORDED = (8795, 8765)
RULE_SHEET = "## Rule sheet"
ON_DISK = "RULE-SHEET.md (as on disk)"


def load_measure_module():
    spec = importlib.util.spec_from_file_location("measure", ROOT / "tools" / "measure.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def tables(text):
    """{heading: [the cells of each table row below it]} of a report."""
    out, heading = {}, None
    for line in text.split("\n"):
        if line.startswith("#"):
            heading = line
        elif line.startswith("|"):
            out.setdefault(heading, []).append([c.strip() for c in line.strip("|").split("|")])
    return out


def bytes_and_chars(row):
    """The label of a row of the committed report and, of every four unit cells (bytes,
    chars, cl100k_base, o200k_base), the first two."""
    return [row[0]] + [c for k, c in enumerate(row[1:]) if k % 4 < 2]


class TestMeasure(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tool = load_measure_module()
        cls.tool.load_tokenizers = lambda: ({}, ["tokens were not measured: this run compares bytes and characters"])
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "0.5-rerun.md"
            with contextlib.redirect_stdout(io.StringIO()):
                cls.status = cls.tool.main(["--date", "2026-09-18", "--out", str(out)])
            cls.rerun = out.read_text(encoding="utf-8")
        cls.committed = REPORT.read_text(encoding="utf-8")

    def test_the_report_names_the_registry_that_wrote_it(self):
        """0.6.1: the tool crashed at 0.6.0 (the frozen 0.5 corpus against the 0.6 default). What the
        report labels 0.5 is written with the frozen 0.5 registry: title, registry file, digests, canon
        commit and the quoted headers are those of the committed report, and nothing of 0.6 is in it."""
        self.assertEqual(self.status, 0)
        reg = default_registry()
        rerun, committed = self.rerun.split("\n"), self.committed.split("\n")
        self.assertEqual(rerun[0], committed[0])                                   # the title
        self.assertEqual(rerun[2], committed[2])                                   # corpora, registries, digests, canon commit
        self.assertIn("`registry/iml-registry-0.5.json`, digest `%s`" % reg.prev.digest[:12], rerun[2])
        forms = [ln for ln in rerun if ln.startswith("Forms, per")]
        self.assertEqual(forms, [ln for ln in committed if ln.startswith("Forms, per")])
        self.assertTrue(len(forms) == 2 and reg.prev.header + " " in forms[1])
        self.assertNotIn(reg.header, self.rerun)                                   # no 0.6 header under a 0.5 label
        self.assertNotIn(reg.digest[:12], self.rerun)

    def test_the_committed_report_reproduces_in_bytes_and_characters(self):
        committed, rerun = tables(self.committed), tables(self.rerun)
        self.assertEqual(list(rerun), list(committed))
        rows = 0                                           # rows of figures: a table less its two head rows
        for heading in committed:
            if heading != RULE_SHEET:
                self.assertEqual(rerun[heading], [bytes_and_chars(r) for r in committed[heading]], heading)
                rows += len(rerun[heading]) - 2
        # the rule sheet: on disk it is the sheet of this release, so that row is new; the record rows are read from
        # the release tags with git, and a tag that cannot be read where the tests run gives a row that says so
        record = {r[0]: r[1:] for r in map(bytes_and_chars, committed[RULE_SHEET][2:])}
        sheet = {r[0]: r[1:] for r in rerun[RULE_SHEET][2:]}
        tags = ["RULE-SHEET.md at tag `%s`" % t for t in self.tool.RULE_SHEET_TAGS]
        self.assertEqual(list(sheet), [ON_DISK] + tags)
        read = [t for t in tags if sheet[t] != [self.tool.NOT_MEASURED] * 2]
        for t in read:
            if t in record:
                self.assertEqual(sheet[t], record[t], t)
                rows += 1
        at_051 = "RULE-SHEET.md at tag `v0.5.1`"          # the sheet the committed report measured on disk
        if at_051 in read:
            self.assertEqual(sheet[at_051], record[ON_DISK])
            rows += 1
        print("\nmeasure: %d of the %d rows of figures of %s reproduce in bytes and characters (%d of %d rule-sheet tags"
              " could be read here)" % (rows, sum(len(t) - 2 for t in committed.values()), REPORT.name, len(read), len(tags)))


class TestRuleSheetSize(unittest.TestCase):
    """0.6.2, after the audit of v0.6.0: the rule sheet stands under a ceiling of 2,600 cl100k_base tokens
    (SPEC-IML-0.5.md section 8) and no test held it, so the sheet of 0.6.0 grew 156 bytes past the measured
    0.5 sheet without being measured. Its size as last recorded stands in README.md in bytes and characters;
    for 0.6 tokens were not measured (tiktoken was not installed where 0.6.2 was prepared). A sheet larger
    than the record fails here: measure it again (tools/measure.py; with tiktoken for the ceiling) and move
    the record in README.md and SHEET_RECORDED together."""

    def test_the_rule_sheet_does_not_outgrow_its_recorded_size(self):
        data = SHEET.read_bytes()
        size = (len(data), len(data.decode("utf-8")))
        for unit, got, recorded in zip(("bytes", "characters"), size, SHEET_RECORDED):
            self.assertLessEqual(got, recorded, "RULE-SHEET.md is %d %s, recorded %d: measure it again and move the"
                                 " record (README.md, SHEET_RECORDED)" % (got, unit, recorded))
        stated = "%s bytes and %s characters" % ("{:,}".format(SHEET_RECORDED[0]), "{:,}".format(SHEET_RECORDED[1]))
        self.assertIn(stated, README.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
