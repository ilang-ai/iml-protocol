# IML: I-Lang Machine Layer (Experimental Draft)

A compact machine form of I-Lang v4.x operation chains, designed to be compiled from and decompiled back to readable I-Lang. IML (I-Lang Machine Layer) sits under I-Lang, which carries the meaning, and rides inside whatever transport carries the message. It replaces neither.

- **Status:** experimental. 0.2 is the first implemented version: [SPEC-IML-0.2.md](SPEC-IML-0.2.md), a registry derived from the I-Lang canon at commit 127ba56 (v4.2.0), a reference codec, golden and malformed corpora, and a measurement report. Draft 0.1 is archived under `drafts/` as the dated record. What is deferred to 0.3 and the gates for 1.0 are in [ROADMAP.md](ROADMAP.md).
- **Canon:** the I-Lang protocol is specified in [ilang-ai/ilang-spec](https://github.com/ilang-ai/ilang-spec). IML registers no verb, modifier key, entity or declaration of its own; its vocabulary is derived from that canon at a pinned commit.
- **Creator:** [Long Quan Zhu](https://orcid.org/0009-0004-4540-8082) (Max, @SUN). iLang Inc.
- **License:** MIT.

## What is in this repository

| Path | What it is |
|------|------------|
| `SPEC-IML-0.2.md` | The 0.2 specification: subset, registry derivation, grammar and segmentation, header, OUT and aliases, canonical print, round-trip law, error codes, measurement. |
| `RULE-SHEET.md` | The short sheet a model is given to read and write IML: 1,350 tokens under cl100k_base. |
| `registry/iml-registry-0.2.json` | The registry derived from the canon: 88 verb roots (OUT is `Ω`), 49 key codes, 25 entity marks, empty value-code tables. Digest `88d05d0839c1…`, carried in every message header. |
| `canon/` | The four canon files at commit 127ba56 that the registry is derived from, with `canon/PIN` (commit and sha256 of each file). |
| `tools/derive_registry.py` | Derives the registry from `canon/` and, with `--check`, verifies the committed file reproduces it. |
| `iml/` | The reference codec, standard library only: `python -m iml compile`, `decompile`, `roundtrip`, `check-registry`. |
| `corpus/` | 72 golden chains with their expected IML; 76 malformed inputs with their expected error codes. |
| `tests/` | `python -m unittest discover -s tests`: 40 tests, including 10,000 generated chains under the round-trip law and a 500-chain sample checked by the canon validator. |
| `tools/measure.py`, `measurements/` | Bytes, characters, cl100k_base and o200k_base tokens for the I-Lang canonical print, the IML message and a JSON baseline, on the golden corpus. |
| `drafts/IML-draft-0.1.md` | The first draft, filed 2026-09-12, kept unchanged below its banner. Reviewed 2026-09-18; the banner records what did not hold. |
| `ROADMAP.md` | The scope of 0.2, what is deferred to 0.3, what belongs to the envelope, the gates for 1.0, and the rule for any efficiency claim. |
| `LICENSE` | MIT. |

Nothing here is normative for I-Lang. A change to I-Lang goes through ilang-spec.

## What IML is

An I-Lang v4.x operation chain such as

```
[READ:@GH|path=readme.md]=>[XLAT|lng=zh]=>[FMT|fmt=md]=>[Ω]
```

has one machine form that a codec produces and a codec reads back to the same chain:

```
#iml/0.2/88d05d0839c1 RDΦGHpt=readme.md→XLln=zh→FMfm=md→Ω
```

The codec is deterministic. The vocabulary (verb roots, key codes, entity marks) is a table derived from the I-Lang canon by a fixed algorithm, so IML never has to invent a word, and the header carries the digest of that table.

Draft 0.1 wrote the idea down as four axioms. The review of 2026-09-18 found that, as written, the first three do not hold: the value abbreviation scheme is not injective, two character substitutions are lossy, values have no delimiting or escaping, and the control-flow constructs have no I-Lang v4.x form to decompile to. Version 0.2 therefore narrows the promise to what can be tested: a stated subset of I-Lang (linear pipelines) that round-trips at the AST level, a vocabulary derived from the canon, and a reference codec with a golden corpus.

## What IML does not claim

- **Not lossless in general.** 0.2 states exactly which subset of I-Lang round-trips, and tests it. Outside that subset nothing is promised.
- **Not "read the same by any model".** Determinism belongs to the codec. How a model reads IML is measured, not asserted, and no figure of that kind is published without the test set, the scoring rule and the endpoints used.
- **No token or cost saving.** Any such figure is published only with the corpus, the tokenizer, and the two baselines it is compared against (I-Lang v4 text, and JSON with schema), including the cost of the rule sheet a model has to be given.
- **No security of its own.** Authority, signing and encryption belong to the envelope and transport that carry a message. A receiver treats an IML message as untrusted input under I-Lang v4.0 until the envelope says otherwise.

## Using the codec

Python 3.10 or later, standard library only. Input is one I-Lang chain per line on standard input or in a file.

```
$ echo '[READ:@GH|path=readme.md]=>[XLAT|lng=zh]=>[FMT|fmt=md]=>[Ω]' | python -m iml compile
#iml/0.2/88d05d0839c1 RDΦGHpt=readme.md→XLln=zh→FMfm=md→Ω

$ echo '#iml/0.2/88d05d0839c1 RDΦGHpt=readme.md→XLln=zh→FMfm=md→Ω' | python -m iml decompile
[READ:@GH|path=readme.md]=>[XLAT|lng=zh]=>[FMT|fmt=md]=>[Ω]

$ echo '[READ:@GH|paths=x]' | python -m iml compile
<stdin>:1: E302 Invalid Modifier: unknown modifier key 'paths' (offset 10, op 0)
```

The codec fails closed: an unknown verb, key, entity mark or value code, a missing or mismatched header, or a construct outside the 0.2 subset stops it with one of six error codes taken from I-Lang SPEC.md §9. It never guesses and never rewrites a value.

## What 0.2 measured

On the 72-chain golden corpus (`measurements/0.2-2026-09-18.md`, tiktoken 0.14.0, named encodings and not any vendor's billing):

| form | bytes | chars | cl100k_base | o200k_base |
|------|---:|---:|---:|---:|
| I-Lang canonical print | 4464 | 4397 | 2040 | 2134 |
| IML message | 4964 | 4504 | 2761 | 2606 |
| JSON baseline | 8334 | 8330 | 3195 | 3262 |

IML is longer than the I-Lang canonical print in every unit on this corpus: each message carries a 23-character header, and `Φ`, `Ω` and `→` are multibyte and tokenize poorly. The rule sheet costs 1,350 cl100k_base tokens on top. That is the measurement; no saving is claimed, and the efficiency gate in ROADMAP.md stands unchanged.

## Naming

Write `IML (I-Lang Machine Layer)` on first mention. IML is a representation layer under I-Lang; it is not a transport.

## Versions

| Version | State |
|---------|-------|
| 0.1 | Archived draft, filed 2026-09-12. Not implemented. |
| 0.2 | Released 2026-09-18 as v0.2.0: specification, registry, reference codec, corpora, measurement. |
