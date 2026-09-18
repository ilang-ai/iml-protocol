# IML: I-Lang Machine Layer (Experimental Draft)

A machine form of I-Lang v4.x operation chains, with fixed-width codes derived from the canon, designed to be compiled from and decompiled back to readable I-Lang. IML (I-Lang Machine Layer) sits under I-Lang, which carries the meaning, and rides inside whatever transport carries the message. It replaces neither.

- **Status:** experimental. 0.3 is the current version: [SPEC-IML-0.3.md](SPEC-IML-0.3.md). It changes the surface of a message only, after what 0.2 measured: the marks are ASCII (`@`, `$`, one space between operations) and a document form carries one header for many chains. The registry derived from the I-Lang canon at commit 127ba56 (v4.2.0), the AST, the round-trip law and the error codes are those of 0.2. 0.2 ([SPEC-IML-0.2.md](SPEC-IML-0.2.md)) was the first implemented version and stays as the record; the codec reads its surface on request and writes 0.3 only. Draft 0.1 is archived under `drafts/` as the dated record. What is deferred to 0.4 and the gates for 1.0 are in [ROADMAP.md](ROADMAP.md).
- **Canon:** the I-Lang protocol is specified in [ilang-ai/ilang-spec](https://github.com/ilang-ai/ilang-spec). IML registers no verb, modifier key, entity or declaration of its own; its vocabulary is derived from that canon at a pinned commit.
- **Creator:** [Long Quan Zhu](https://orcid.org/0009-0004-4540-8082) (Max, @SUN). iLang Inc.
- **License:** MIT.
- **Citation:** [CITATION.cff](CITATION.cff); Zenodo archives each release from 0.2.2 on. Concept DOI [10.5281/zenodo.22823285](https://doi.org/10.5281/zenodo.22823285) (all versions); 0.2.2 is [10.5281/zenodo.22823286](https://doi.org/10.5281/zenodo.22823286).

## What is in this repository

| Path | What it is |
|------|------------|
| `SPEC-IML-0.3.md` | The 0.3 specification: subset, registry derivation, grammar and segmentation on the ASCII surface, the message and document forms, header, OUT and aliases, canonical print, round-trip law, error codes, measurement. |
| `SPEC-IML-0.2.md` | The 0.2 specification, unchanged, as the record of the surface the codec still reads with `--version 0.2`. |
| `RULE-SHEET.md` | The short sheet a model is given to read and write IML 0.3: 1,792 tokens under cl100k_base. |
| `registry/iml-registry-0.2.json` | The registry derived from the canon, unchanged since 0.2: 87 verb roots and one mark for OUT (`$` in 0.3, `Ω` in 0.2), 49 key codes, 25 entity marks, empty value-code tables. Digest `88d05d0839c1…`, carried in every header. |
| `canon/` | The four canon files at commit 127ba56 that the registry is derived from, with `canon/PIN` (commit and sha256 of each file). |
| `tools/derive_registry.py` | Derives the registry from `canon/` and, with `--check`, verifies the committed file reproduces it. |
| `iml/` | The reference codec, standard library only: `python -m iml compile [--document]`, `decompile [--version 0.2]`, `roundtrip`, `check-registry`. |
| `corpus/` | 72 golden chains (`golden/*.ilang`) with their expected IML on the 0.3 surface (`golden-0.3/`) and on the 0.2 surface (`golden/*.iml`, the record); 132 malformed inputs with their expected error codes, each naming its surface. |
| `tests/` | `python -m unittest discover -s tests`: 53 tests, including 10,000 generated chains under the round-trip law on both surfaces, the document law on 100 generated documents, and a 500-chain sample checked by the canon validator. |
| `tools/measure.py`, `measurements/` | Bytes, characters, cl100k_base and o200k_base tokens for the I-Lang canonical print, the IML 0.3 message, the IML 0.3 document, a JSON baseline and the IML 0.2 message, on the golden corpus. The 0.2 report stays as the record. |
| `drafts/IML-draft-0.1.md` | The first draft, filed 2026-09-12, kept unchanged below its banner. Reviewed 2026-09-18; the banner records what did not hold. |
| `ROADMAP.md` | The scope of 0.2 and 0.3, what is deferred to 0.4, what belongs to the envelope, the gates for 1.0, and the rule for any efficiency claim. |
| `LICENSE` | MIT. |

Nothing here is normative for I-Lang. A change to I-Lang goes through ilang-spec.

## What IML is

An I-Lang v4.x operation chain such as

```
[READ:@GH|path=readme.md]=>[XLAT|lng=zh]=>[FMT|fmt=md]=>[Ω]
```

has one machine form that a codec produces and a codec reads back to the same chain:

```
#iml/0.3/88d05d0839c1 RD@GHpt=readme.md XLln=zh FMfm=md $
```

Many chains share one header in the document form: the header alone on the first line, then one chain per line.

```
#iml/0.3/88d05d0839c1
RD@GHpt=readme.md XLln=zh FMfm=md $
RD@{MYDATA}sr=@PR,wh="a, b" $fm=json
```

The codec is deterministic. The vocabulary (verb roots, key codes, entity marks) is a table derived from the I-Lang canon by a fixed algorithm, so IML never has to invent a word, and the header carries the digest of that table. On the 0.2 surface the same first chain read `#iml/0.2/88d05d0839c1 RDΦGHpt=readme.md→XLln=zh→FMfm=md→Ω`; 0.3 keeps the codes and changes only the three marks and the place of the header.

Draft 0.1 wrote the idea down as four axioms. The review of 2026-09-18 found that, as written, the first three do not hold: the value abbreviation scheme is not injective, two character substitutions are lossy, values have no delimiting or escaping, and the control-flow constructs have no I-Lang v4.x form to decompile to. Version 0.2 therefore narrowed the promise to what can be tested: a stated subset of I-Lang (linear pipelines) that round-trips at the AST level, a vocabulary derived from the canon, and a reference codec with a golden corpus. Version 0.3 keeps that promise and respells the surface.

## What IML does not claim

- **Not lossless in general.** The specification states exactly which subset of I-Lang round-trips, and tests it. Outside that subset nothing is promised.
- **Not "read the same by any model".** Determinism belongs to the codec. How a model reads IML is measured, not asserted, and no figure of that kind is published without the test set, the scoring rule and the endpoints used.
- **No token or cost saving.** Any such figure is published only with the corpus, the tokenizer, and the two baselines it is compared against (I-Lang v4 text, and JSON with schema), including the cost of the rule sheet a model has to be given. The tables below are measurements, not that figure.
- **No security of its own.** Authority, signing and encryption belong to the envelope and transport that carry a message. A receiver treats an IML message as untrusted input under I-Lang v4.0 until the envelope says otherwise.

## Using the codec

Python 3.10 or later, standard library only. Input is one I-Lang chain per line on standard input or in a file.

```
$ echo '[READ:@GH|path=readme.md]=>[XLAT|lng=zh]=>[FMT|fmt=md]=>[Ω]' | python -m iml compile
#iml/0.3/88d05d0839c1 RD@GHpt=readme.md XLln=zh FMfm=md $

$ echo '#iml/0.3/88d05d0839c1 RD@GHpt=readme.md XLln=zh FMfm=md $' | python -m iml decompile
[READ:@GH|path=readme.md]=>[XLAT|lng=zh]=>[FMT|fmt=md]=>[Ω]

$ printf '[READ:@GH|path=readme.md]=>[XLAT|lng=zh]=>[FMT|fmt=md]=>[Ω]\n[READ:@MYDATA|src=@PREV,whr="a, b"]=>[Ω|fmt=json]\n' | python -m iml compile --document
#iml/0.3/88d05d0839c1
RD@GHpt=readme.md XLln=zh FMfm=md $
RD@{MYDATA}sr=@PR,wh="a, b" $fm=json

$ echo '#iml/0.2/88d05d0839c1 RDΦGHpt=readme.md→XLln=zh→FMfm=md→Ω' | python -m iml decompile --version 0.2
[READ:@GH|path=readme.md]=>[XLAT|lng=zh]=>[FMT|fmt=md]=>[Ω]

$ echo '[READ:@GH|paths=x]' | python -m iml compile
<stdin>:1: E302 Invalid Modifier: unknown modifier key 'paths' (offset 10, op 0)
```

`decompile` decides the form by the first line: a header alone opens a document and every following line is a chain; a header followed by a chain is a message, and every non-empty line is then one message. `compile` writes 0.3 only. A 0.2 header given to the 0.3 decoder is refused (E502) unless `--version 0.2` is passed.

The codec fails closed: an unknown verb, key, entity mark or value code, a missing or mismatched header, a blank line or a second header inside a document, or a construct outside the subset stops it with one of six error codes taken from I-Lang SPEC.md §9. It never guesses and never rewrites a value.

## What 0.2 and 0.3 measured

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

In 0.2 each message carried a 21-character header and one space, and `Φ`, `Ω` and `→` are multibyte and tokenize into two or three tokens each; that is what 0.3 changed. The 0.3 message is still above the I-Lang canonical print in tokens on this corpus; the 0.3 document, which pays the header once, is below it. The rule sheet costs 1,792 cl100k_base tokens on top (0.2: 1,607). The reply is not measured: the codec makes no model calls. That is the measurement; the efficiency gate in ROADMAP.md stands unchanged and is not met.

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
