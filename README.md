# IML: I-Lang Machine Layer (Experimental Draft)

A machine form of I-Lang v4.x operation chains and, since 0.5, of whole I-Lang documents, with fixed-width codes derived from the canon, designed to be compiled from and decompiled back to readable I-Lang. IML (I-Lang Machine Layer) sits under I-Lang, which carries the meaning, and rides inside whatever transport carries the message. It replaces neither.

- **Status:** experimental. 0.5 is the current version: [SPEC-IML-0.5.md](SPEC-IML-0.5.md). It carries a whole raw I-Lang document, declarations included: the declaration names of the canon get two-character codes derived like the verb roots, the block structure (shapes, spans, opaque blocks, one level of nesting, body lines) becomes explicit line structure, and an operation line in a declaration body is coded as a chain; what the canon does not tokenize, such as the content between the braces of a header, is carried as exact text. It follows the owner's decision of 2026-09-18: the canon is not changed, and IML registers nothing of its own. The header becomes `#iml/0.5/`, with the digest of a second registry file; 0.4 and 0.3 headers are still read, for chains. 0.4 ([SPEC-IML-0.4.md](SPEC-IML-0.4.md)) added the two flow forms the canon defines for operation chains, 0.3 ([SPEC-IML-0.3.md](SPEC-IML-0.3.md)) respelled the surface and 0.2 ([SPEC-IML-0.2.md](SPEC-IML-0.2.md)) was the first implemented version; all three stay as records, and the codec reads the 0.2 surface on request and writes 0.5 only. Draft 0.1 is archived under `drafts/` as the dated record. What stays open, and the gates for 1.0, are in [ROADMAP.md](ROADMAP.md).
- **Canon:** the I-Lang protocol is specified in [ilang-ai/ilang-spec](https://github.com/ilang-ai/ilang-spec). IML registers no verb, modifier key, entity or declaration of its own; its vocabulary, the declaration codes included, is derived from that canon at a pinned commit.
- **Creator:** [Long Quan Zhu](https://orcid.org/0009-0004-4540-8082) (Max, @SUN). iLang Inc.
- **License:** MIT.
- **Citation:** [CITATION.cff](CITATION.cff); Zenodo archives each release from 0.2.2 on. Concept DOI [10.5281/zenodo.22823285](https://doi.org/10.5281/zenodo.22823285) (all versions); 0.2.2 is [10.5281/zenodo.22823286](https://doi.org/10.5281/zenodo.22823286).

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.22823285.svg)](https://doi.org/10.5281/zenodo.22823285)

## What is in this repository

| Path | What it is |
|------|------------|
| `SPEC-IML-0.5.md` | The 0.5 specification: the owner's decision and the canon audit, the two registry files and the declarations table, the document grammar and its first-character dispatch, headers and versions, declarations and texts (shapes, spans, opaque blocks, body lines, nesting), the canonical print of a document, the laws and the validator as oracle, error codes, measurement, and the points where IML is stricter than the validator. |
| `SPEC-IML-0.4.md` | The 0.4 specification, unchanged, as the record of the flow forms (the batch shorthand, multi-line chains); its chain rules still apply to every chain. |
| `SPEC-IML-0.3.md` | The 0.3 specification, unchanged, as the record of the ASCII surface and the document form; a 0.3 header is read by the 0.5 codec for chains. |
| `SPEC-IML-0.2.md` | The 0.2 specification, unchanged, as the record of the surface the codec still reads with `--version 0.2`. |
| `RULE-SHEET.md` | The short sheet a model is given to read and write IML 0.5: 2,596 tokens under cl100k_base. |
| `registry/iml-registry-0.5.json` | The registry of 0.5: the tables of the 0.2 file unchanged, plus the 49 declaration codes derived from the canon's declaration registry (PATCH-2 §1.5 and §1.6) and the two tolerated annotations, which get no code. Digest `7e29fae7f5ea…`, carried in every 0.5 header. |
| `registry/iml-registry-0.2.json` | The chain registry of 0.2, 0.3 and 0.4, kept byte for byte: 87 verb roots and one mark for OUT (`$` since 0.3, `Ω` in 0.2), 49 key codes, 25 entity marks, empty value-code tables. Digest `88d05d0839c1…`, the one a 0.4 or 0.3 header names. |
| `canon/` | The four canon files at commit 127ba56 that the registries are derived from, with `canon/PIN` (commit and sha256 of each file). |
| `tools/derive_registry.py` | Derives both registry files from `canon/` and, with `--check`, verifies that the committed files reproduce. |
| `iml/` | The reference codec, standard library only: `python -m iml compile [--document]` (one chain per line; with `--document`, a whole raw I-Lang document), `decompile [--version 0.2]` (reads a 0.5 header, and a 0.4 or 0.3 header for chains, by default), `roundtrip`, `check-registry`. |
| `corpus/` | 72 golden chains (`golden/*.ilang`) with their expected IML on the 0.3 surface (`golden-0.3/`) and on the 0.2 surface (`golden/*.iml`, the record); the 0.4 and 0.5 golden corpora below; 266 malformed inputs with their expected error codes, 79 of them added in 0.5.0 (77 document cases and 2 message cases) and 19 in 0.5.1 (17 document cases and 2 message cases). |
| `corpus/golden-0.4/` | 36 chains as pairs `NNN.ilang` and `NNN.iml`, six of the sources written on several lines, and one document pair `doc-01.ilang` and `doc-01.iml`; the batch shorthand, the modifier form, entity targets on BATC, LOOP, WAIT and CHEK as plain operations, values containing `:`, and the canon §10.7 workflow chains. |
| `corpus/golden-0.5/` | 20 I-Lang documents as pairs `NNN.ilang` and `NNN.iml`, each opening with a `::ILANG::` marker: canon text kept verbatim where the canon has it (PATCH-2 Appendix A, the agent blueprint; the SPEC.md §10.2 to §10.7 examples; PATCH-2's own `::GRAMMAR`, `::BODY` and `::REGISTRY` blocks), the forms of SPEC.md §6 and §7, and documents written in the canon's shapes for the rest: declarations the vendored canon has no example of (BUDGET, RUBRIC, FALLBACK, DIM, SCHEMA, CASE), a timeline with temporal prefixes and binds, a `::MODULE::NAME` span, an `::UNTRUSTED` opaque block, `::CLAUSE` and `::JUDGE` blocks with flush-left bodies, preamble tag lines, annotation lines, colophon prose, body chains with continuation lines and nested declarations with bodies of their own. All 49 declaration names and all four shapes occur. |
| `tests/` | `python -m unittest discover -s tests`: 153 tests. Among them: the declarations table derived from the canon and cross-checked against the validator; the 20 golden documents under the laws and the validator; 2,000 generated documents under L1 and L2 with the validator on every source and print, and 1,000 mutated ones; the document cases of the malformed corpus against the validator; the inputs of the review of v0.5.0, a chain of 20,000 lines joined in linear time among them; and the 0.4 tests, 10,000 generated chains included. |
| `tools/measure.py`, `measurements/` | Bytes, characters, cl100k_base and o200k_base tokens: for the golden chains, the I-Lang canonical print, the IML message and document, a JSON baseline and the IML 0.2 message; for the golden documents, the I-Lang source as written, its canonical print and the IML 0.5 document; and the rule sheet. `measurements/0.5-2026-09-18.md` is the current report; the 0.2, 0.3 and 0.4 reports stay as the records. |
| `drafts/IML-draft-0.1.md` | The first draft, filed 2026-09-12, kept unchanged below its banner. Reviewed 2026-09-18; the banner records what did not hold. |
| `ROADMAP.md` | The scope of 0.2 to 0.5, what stays gated on chain syntax in the canon, what of the canon is still open after 0.5, what belongs to the envelope, the gates for 1.0, and the rule for any efficiency claim. |
| `LICENSE` | MIT. |

Nothing here is normative for I-Lang. A change to I-Lang goes through ilang-spec.

## What IML is

An I-Lang v4.x operation chain such as

```
[READ:@GH|path=readme.md]=>[XLAT|lng=zh]=>[FMT|fmt=md]=>[Ω]
```

has one machine form that a codec produces and a codec reads back to the same chain:

```
#iml/0.5/7e29fae7f5ea RD@GHpt=readme.md XLln=zh FMfm=md $
```

Since 0.5 a whole I-Lang document has one machine form as well. This one is canon SPEC.md §10.7:

```
::ACTIVATE{build_feature}
  ON:user_request
::RULE{scope>2hr⇒activate_plan_breakdown}

[PLAN:@SRC|len=5-15]=>[Ω]

::PROGRESS{date:2026-04-20|done:plan_approved|next:build_auth}

[CREA:@LOCAL|path=auth/login.go]=>[TEST]=>[REVW]=>[Ω]
[CREA:@LOCAL|path=auth/register.go]=>[TEST]=>[REVW]=>[Ω]

::PROGRESS{date:2026-04-20|done:auth_module|next:deploy}

[DPLO:@WORKER]=>[CHEK|whr=status:200]=>[Ω]

::LESSON{id:go_middleware|type:build|scope:project|conf:confirmed}
  Auth middleware must be registered before route handlers.
```

Its IML 0.5 document, the header alone on the first line:

```
#iml/0.5/7e29fae7f5ea
:AC"build_feature"
 "ON:user_request"
:RL"scope>2hr⇒activate_plan_breakdown"
PL@SRle=5-15 $
:PR"date:2026-04-20|done:plan_approved|next:build_auth"
CE@LCpt=auth/login.go TS RV $
CE@LCpt=auth/register.go TS RV $
:PR"date:2026-04-20|done:auth_module|next:deploy"
DP@WR CKwh=status:200 $
:LS"id:go_middleware|type:build|scope:project|conf:confirmed"
 "Auth middleware must be registered before route handlers."
```

A declaration line starts with `:` and a two-character code from the declarations table (`:AC` ACTIVATE, `:RL` RULE, `:PR` PROGRESS, `:LS` LESSON), followed by the content between its braces as quoted text; a line that starts with one space belongs to the declaration above it (`ON:user_request`, the lesson's prose line); every other line here is a chain, spelled as in 0.4. Decompile prints the document back without its blank lines, which are layout, and the pinned canon validator reads the print with 0 errors.

The codec is deterministic. The vocabulary (verb roots, key codes, entity marks, declaration codes) is a table derived from the I-Lang canon by a fixed algorithm, so IML never has to invent a word, and the header carries the digest of that table. On the 0.2 surface the first chain above read `#iml/0.2/88d05d0839c1 RDΦGHpt=readme.md→XLln=zh→FMfm=md→Ω`; 0.3 kept the codes and changed only the three marks and the place of the header, and 0.4 and 0.5 keep that surface.

0.4 added the two flow forms the canon defines for operation chains, and only those: the batch shorthand of canon §3.9, `[BATC:READ]` or `[Π:READ]`, which compiles to `BT:RD`, and chains written on several lines, each continuation line beginning with `=>` (canon PATCH-2 §1.7). Conditionals, parallel groups, DAGs, error handling and retry were checked against the canon and its validator (`SPEC-IML-0.4.md` §0.3): they are not operation-chain syntax in the canon, and therefore they are not in IML, which defines no construct of its own.

0.5 adds the declaration layer, which the canon does define: the declaration registry of PATCH-2 §1.5 and §1.6, the block shapes and body line forms of PATCH-2 §1.1 and §1.2, and the document marker, temporal prefix and MODULE form of §1.7, read as the canon's grammar validator reads a raw document. Where the canon gives a structure a code or a form, IML codes it or makes it explicit; where the canon leaves text untokenized, IML carries the text exactly. The validator is the oracle: every golden and generated document the codec accepts lints with 0 errors, as written and as printed back, and the few points where IML refuses what the validator accepts are listed in `SPEC-IML-0.5.md` §9.1.

Draft 0.1 wrote the idea down as four axioms. The review of 2026-09-18 found that, as written, the first three do not hold: the value abbreviation scheme is not injective, two character substitutions are lossy, values have no delimiting or escaping, and the control-flow constructs have no I-Lang v4.x form to decompile to. Version 0.2 therefore narrowed the promise to what can be tested: a stated subset of I-Lang (linear pipelines) that round-trips at the AST level, a vocabulary derived from the canon, and a reference codec with a golden corpus. Version 0.3 kept that promise and respelled the surface; version 0.4 kept it and widened the subset by what the canon defines for chains; version 0.5 keeps it and carries what the canon defines for documents.

## What IML does not claim

- **Not lossless in general.** The specification states exactly which subset of I-Lang round-trips, and tests it. Outside that subset nothing is promised.
- **Not "read the same by any model".** Determinism belongs to the codec. How a model reads IML is measured, not asserted, and no figure of that kind is published without the test set, the scoring rule and the endpoints used.
- **No token or cost saving.** Any such figure is published only with the corpus, the tokenizer, and the two baselines it is compared against (I-Lang v4 text, and JSON with schema), including the cost of the rule sheet a model has to be given. The tables below are measurements, not that figure.
- **No security of its own.** Authority, signing and encryption belong to the envelope and transport that carry a message. A receiver treats an IML message as untrusted input under I-Lang v4.0 until the envelope says otherwise.

## Using the codec

Python 3.10 or later, standard library only. Input is I-Lang chains on standard input or in a file, one per line, or one per line with continuation lines beginning with `=>`; with `--document`, a whole raw I-Lang document. Input is UTF-8, and the command line drops every leading byte order mark: Windows PowerShell 5.1 puts one in front of text it pipes as UTF-8, and two when `[Console]::InputEncoding` and `$OutputEncoding` are both set to UTF-8; the library functions stay strict.

```
$ echo '[READ:@GH|path=readme.md]=>[XLAT|lng=zh]=>[FMT|fmt=md]=>[Ω]' | python -m iml compile
#iml/0.5/7e29fae7f5ea RD@GHpt=readme.md XLln=zh FMfm=md $

$ echo '[LIST:@LOCAL|mch=*.md]=>[Π:READ]=>[Σ]=>[Ω]' | python -m iml compile
#iml/0.5/7e29fae7f5ea LS@LCmc=*.md BT:RD MR $

$ printf '[DPLO:@WORKER]\n  =>[CHEK|whr=status:200]\n  =>[Ω]\n' | python -m iml compile
#iml/0.5/7e29fae7f5ea DP@WR CKwh=status:200 $

$ echo '#iml/0.5/7e29fae7f5ea LS@LCmc=*.md BT:RD MR $' | python -m iml decompile
[LIST:@LOCAL|mch=*.md]=>[BATC:READ]=>[MERGE]=>[Ω]

$ printf '::ILANG::v5.0\n::GENE{verify_first|conf:confirmed}\n  T:check_before_execute\n  [READ:@SRC]=>[Ω]\n' | python -m iml compile --document
#iml/0.5/7e29fae7f5ea
"::ILANG::v5.0"
:GN"verify_first|conf:confirmed"
 "T:check_before_execute"
 RD@SR $

$ printf '#iml/0.5/7e29fae7f5ea\n:GN"verify_first|conf:confirmed"\n "T:check_before_execute"\n RD@SR $\n' | python -m iml decompile
::GENE{verify_first|conf:confirmed}
  T:check_before_execute
  [READ:@SRC]=>[Ω]

$ echo '#iml/0.4/88d05d0839c1 RD@GHpt=readme.md XLln=zh FMfm=md $' | python -m iml decompile
[READ:@GH|path=readme.md]=>[XLAT|lng=zh]=>[FMT|fmt=md]=>[Ω]

$ echo '#iml/0.2/88d05d0839c1 RDΦGHpt=readme.md→XLln=zh→FMfm=md→Ω' | python -m iml decompile --version 0.2
[READ:@GH|path=readme.md]=>[XLAT|lng=zh]=>[FMT|fmt=md]=>[Ω]

$ echo '::GENE{verify_first}' | python -m iml compile
<stdin>:1: E502 Unsupported Format: carried in the document form: compile --document (a declaration or any other line that is not an operation chain has no message form) (offset 0)

$ echo '[READ:@GH|paths=x]' | python -m iml compile
<stdin>:1: E302 Invalid Modifier: unknown modifier key 'paths' (offset 10, op 0)
```

`decompile` decides the form by the first line: a header alone opens a document, printed as one I-Lang document; a header followed by a chain is a message, and every non-empty line is then one message. `compile` writes 0.5 only and reports an error at the chain's first line; a declaration given to it without `--document` is E502. A 0.4 or 0.3 header is read for chains without a flag; a 0.2 header is refused (E502) unless `--version 0.2` is passed.

The codec fails closed: an unknown verb, key, entity mark, verb reference, value code, declaration name or declaration code, a missing or mismatched header, a blank line or a second header inside a document, an orphan `=>` line, a `=>` line under a line break that stands inside an operation, a line of a document that matches no I-Lang production, or a construct outside what the specification carries stops it with one of six error codes taken from I-Lang SPEC.md §9. It never guesses and never rewrites a value or a text.

## What was measured

On the same 72-chain golden corpus, the same encodings (tiktoken 0.14.0, named encodings and not any vendor's billing) and the same JSON baseline.

0.2 (`measurements/0.2-2026-09-18.md`, regenerated for 0.2.1):

| form | bytes | chars | cl100k_base | o200k_base |
|------|---:|---:|---:|---:|
| I-Lang canonical print | 4462 | 4395 | 2040 | 2134 |
| IML 0.2 message | 4964 | 4504 | 2761 | 2606 |
| JSON baseline | 8334 | 8330 | 3195 | 3262 |

0.3 (`measurements/0.3-2026-09-18.md`):

| form | bytes | chars | cl100k_base | o200k_base |
|------|---:|---:|---:|---:|
| I-Lang canonical print | 4462 | 4395 | 2040 | 2134 |
| IML 0.3 message (one header per chain) | 4506 | 4502 | 2438 | 2437 |
| IML 0.3 document (one header for the 72 chains) | 3015 | 3011 | 1315 | 1313 |
| JSON baseline | 8334 | 8330 | 3195 | 3262 |

In 0.2 each message carried a 21-character header and one space, and `Φ`, `Ω` and `→` are multibyte and cost about one extra token each under cl100k_base (about half under o200k_base); that is what 0.3 changed. The 0.3 message is still above the I-Lang canonical print in tokens on this corpus; the 0.3 document, which pays the header once, is below it. The rule sheet costs cl100k_base tokens on top, as measured at each release tag in `measurements/0.5-2026-09-18.md`: 1,364 at v0.2.0, 1,619 at v0.2.1 and v0.2.2, 1,792 at v0.3.0, 1,767 at v0.3.1, 1,796 at v0.4.0, 1,798 at v0.4.1 and 2,596 at v0.5.0; counting the v0.3.0 sheet once, 1,315 + 1,792 is above the corpus's I-Lang print (2,040), and the sheet is paid once per model context, so whether a context comes out ahead depends on how many chains it carries. The reply is not measured: the codec makes no model calls. 0.4 changed no figure of this 72-chain corpus: its header differs from the 0.3 header by one digit, which both encodings tokenise to the same count, and the `corpus/golden-0.4/` chains are measured in `measurements/0.4-2026-09-18.md`.

0.5 (`measurements/0.5-2026-09-18.md`): on the 20 golden documents of `corpus/golden-0.5/` the IML 0.5 documents total 5,526 `cl100k_base` tokens (5,500 `o200k_base`), the I-Lang sources as written 5,246 (5,187) and their canonical prints 5,345 (5,290); in bytes, 15,210, 15,235 and 15,378. On this corpus the IML document is above both I-Lang forms in tokens. The 0.5 header is one token longer than the 0.4 header under both encodings, because its digest differs, so each chain message costs one token more than in 0.4 (72 chains: 2,510 `cl100k_base` against 2,438) and a document one token more in all (1,316 against 1,315). The 0.5 rule sheet is 2,596 `cl100k_base` tokens, under a ceiling raised from 1,800 to 2,600 for the declaration table and the document rules; 0.5.1 leaves it unchanged.

That is the measurement; the efficiency gate in ROADMAP.md stands unchanged and is not met.

## Naming

Write `IML (I-Lang Machine Layer)` on first mention. IML is a representation layer under I-Lang; it is not a transport.

## Versions

| Version | State |
|---------|-------|
| 0.1 | Archived draft, filed 2026-09-12. Not implemented. |
| 0.2 | Released 2026-09-18 as v0.2.0: specification, registry, reference codec, corpora, measurement. |
| 0.2.1 | Released 2026-09-18 as v0.2.1, a fix release: `.gitattributes` pins LF; the I-Lang bare-value character set, the header shape and raw control characters inside quotes are fixed in the codec and stated in the specification (§12 lists the sections); 15 malformed cases added; measurement regenerated. Message form and registry unchanged. |
| 0.2.2 | Released 2026-09-18 as v0.2.2: citation metadata (CITATION.cff, .zenodo.json) for the Zenodo archive. Message form and registry unchanged. |
| 0.3.0 | Released 2026-09-18 as v0.3.0: the ASCII surface (`@`, `$`, one space) and the document form with one header for many chains; `SPEC-IML-0.3.md`; `corpus/golden-0.3/`; 41 malformed cases added; measurement before and after. The 0.2 surface is read behind `--version 0.2`. Registry, AST, round-trip law and error codes unchanged. |
| 0.3.1 | Released 2026-09-18 as v0.3.1, a fix release after an adversarial review of a clean clone: U+0085 is a control character; the bare-value rule says any Unicode whitespace; the grammar shows the optional final line terminator; the per-mark token cost is the measured figure; the rule sheet names three cases it had left out; the CLI reports an empty document and the header line correctly. Message form, registry and error codes unchanged. |
| 0.4.0 | Released 2026-09-18 as v0.4.0: flow within the canon. The batch shorthand `[BATC:VERB]` and `[Π:VERB]` of canon §3.9 (a verb reference on BATC only, `BT:RD`); multi-line chains joined on compile (canon PATCH-2 §1.7); the three definitions the roadmap demanded, written from canon text; the header `#iml/0.4/`, a 0.3 header read without a flag; `SPEC-IML-0.4.md`; `corpus/golden-0.4/` (36 chains and one document pair); 29 malformed cases added, 2 removed (`[Π:READ]` and `[BATC:READ]`, valid in 0.4; the forms now open `corpus/golden-0.4/` as 001 and 002) and 2 re-coded (`=>[READ]` from E502 to E300, `[READ] [FMT]` from E300 to E502), 161 in all; `measurements/0.4-2026-09-18.md`. Conditionals, parallel groups, DAGs, error handling and retry are not chain syntax in the canon and so not in IML. Registry, value rules, canonical print, round-trip law and error codes unchanged; the AST gains one field. |
| 0.4.1 | Released 2026-09-18 as v0.4.1, a fix release after an adversarial review of a clean clone, whose random testing broke no law: a continuation line is joined only after a closed operation (0.4.0 compiled `[READ\|whr="abc` followed by `=>def"]` to `RDwh=abc=>def`), and a line of whitespace only ends a chain; the writers refuse a control character other than a newline in a hand-built value (E300); the command line drops one leading byte order mark and reports input that is not valid UTF-8 as E300 where it printed a traceback; the two messages that follow the validator carry its backticks; the specification corrects three rows of its canon audit, drops the ordering claims of its first definition, lists the spellings that the validator accepts and IML refuses, and states that a 0.3 header is read with the 0.4 grammar; 7 malformed cases added, 168 in all; the rule sheet is 1,798 cl100k_base tokens; the continuous integration run fails on a tracked `.pyc`. Message form, registry, AST and error codes unchanged. |
| 0.5.0 | Released 2026-09-18 as v0.5.0: the declaration layer, after the owner's decision of the same day (the canon is not changed; IML carries the canon's declaration layer in machine form, derives everything from the canon and registers nothing of its own). A whole raw I-Lang document in the document form; the 49 names of the canon's declaration registry coded in `registry/iml-registry-0.5.json` (digest `7e29fae7f5ea…`), the 0.2 registry kept byte for byte; block structure explicit, body operation lines as chains, the rest as exact text; the header `#iml/0.5/`, 0.4 and 0.3 headers read for chains; `SPEC-IML-0.5.md` with the points where IML is stricter than the validator; `corpus/golden-0.5/` (20 documents); 79 malformed cases added, 247 in all; 144 tests; `measurements/0.5-2026-09-18.md`; the rule sheet is 2,596 `cl100k_base` tokens. The chain registry, the chain subset, the message form and the six error codes unchanged. |
| 0.5.1 | Released 2026-09-18 as v0.5.1, a fix release after an adversarial review of a clean clone of v0.5.0, which ran 43,500 generated documents and 15,000 grammar-built IML texts and broke no law on anything the codec compiled: a full-width colon that a same-line trailing token hides in a header, and a one-operation chain in preamble position whose print is a tag line (`[Σ]`), are refused where they stand (E300) instead of at the canonical check; a declaration or text line in a 0.4 or 0.3 message is E502, as in a document; an error of the canonical check is reported at the first source line of its item, never at line 0; continuation lines are joined in linear time (a chain of 20,000 lines took about 43 s); the command line drops every leading byte order mark; the specification states what layout is, restricts L2 to parsed or decoded ASTs and lists in §9.1 the operation lines outside the 0.4 subset that the validator lets pass; the rule-sheet rows of the measurement report are measured from the release tags; 19 malformed cases added, 266 in all; 153 tests; the rule sheet is unchanged, 2,596 cl100k_base tokens. Message form, registries and digests, AST and error codes unchanged. |
