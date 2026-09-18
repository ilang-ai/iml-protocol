# IML roadmap

Versions are triggered by gates, not by dates. Each released version is an immutable tag.

## 0.2, the first implementable version

Released 2026-09-18 as v0.2.0; fix release v0.2.1 the same day (see the record). Every item below is in the repository; README.md says where.

Scope, and nothing beyond it:

1. A registry derived from the I-Lang canon at a pinned commit (88 verbs, 29 core modifier keys, the entity tiers), carrying that commit's digest. IML registers nothing of its own.
2. Segmentation rules written into the specification: verb roots, key codes and entity marks are told apart by rule, not by convention.
3. String and code kept apart: quoted literals as in I-Lang §2.4; a value abbreviation is a marked code (`~code`) and a literal is never marked, so a table can grow without changing the meaning of any earlier message.
4. Every scalar keeps its original lexeme; a type is a validation tag, never a rewrite.
5. An entity reference in value position is a distinct type.
6. One byte form per meaning: aliases collapse to one encoding.
7. Every message carries its version and the digest of the registry it was written against.
8. Linear pipelines ending in Ω, and only those.
9. Round-trip law: for every I-Lang document in the supported subset, I-Lang → IML → I-Lang is identity at the AST level (types, keys, value content, entity identity), and the law is tested.
10. An unknown root, key or entity is an error; the codec fails closed.
11. One reference codec.
12. A golden corpus and a malformed corpus, disjoint from any prompt material used for evaluation.
13. Measurement reported per tokenizer, in bytes, characters and tokens, including the rule sheet and the reply (the reply is not measured in 0.2: the codec makes no model calls).

## 0.3, ASCII surface and document-level header

Released 2026-09-18 as v0.3.0. A change of the surface only, made after the 0.2 measurement (item 13 above): on the 72-chain golden corpus the 0.2 message cost 2,761 cl100k_base tokens against 2,040 for the I-Lang canonical print, because every message paid a 17-token header and because `Φ`, `Ω` and `→` are multibyte marks that cost about one extra token each under cl100k_base.

Scope, and nothing beyond it:

1. The three marks become one ASCII character each: `Φ` to `@`, `Ω` to `$`, `→` to one space. `$` at the start of a value is reserved (E303); such a value is written quoted.
2. The header `#iml/0.3/<12 hex>` may stand once at the head of a document, followed by one chain per line, as well as once on a message line. Both forms decompile; the form is decided by the first line. A blank line, a trailing space or a second header inside a document is an error.
3. The 0.2 surface is read only, behind `--version 0.2`, for the corpora already published; the codec writes 0.3 only. A header of the other version is E502 in both directions.
4. Everything else is unchanged: the registry and its digest `88d05d0839c1`, the AST, the value rules, the canonical print, the round-trip law, the six error codes, the subset.
5. Measured before and after on the same corpus and encodings (`measurements/0.3-2026-09-18.md`): 0.3 message 2,438 cl100k_base tokens with one header per chain, 0.3 document 1,315 with one header for the 72 chains, I-Lang canonical print 2,040, JSON baseline 3,195; the rule sheet 1,792. The figures are the figures; the efficiency gate below is unchanged and not met.

## 0.4, flow within the canon

Released 2026-09-18 as v0.4.0; fix release v0.4.1 the same day (see the record). The three definitions that the 0.3 roadmap demanded before any 0.4 draft were written first, from canon text, and two of them found that the construct does not exist at chain level. 0.4 then widened the subset by exactly the two flow forms the canon defines for operation chains, and nothing else. `SPEC-IML-0.4.md` §0.3 records what was checked and §0.4 the definitions.

Scope, and nothing beyond it:

1. The verb reference of canon §3.9 on BATC: `[BATC:READ]` and `[Π:READ]` compile to `BT:RD`; an alias collapses to its verb; OUT cannot be referenced (E502); on any other verb a target that is not an entity stays E300 with the validator's wording. `[BATC|op=READ]` stays a string modifier, and the codec does not convert one form into the other.
2. Multi-line chains on compile: a line whose first non-blank characters are `=>` continues the chain above it (PATCH-2 §1.7); the joined text is parsed as a one-line chain, so the AST, the IML line and the canonical print are those of the one-line spelling, and an orphan `=>` line is E300 in the validator's wording. Since 0.4.1 a line is joined only after a closed operation, that is when the text so far ends with `]` outside a quoted value (E300 otherwise), and a line of whitespace only ends a chain as a blank line does. IML lines never continue.
3. The three definitions, written from canon text: the loop body and its termination (BATC is the canon's one loop over data, the referenced verb applied per item and terminating at the end of the list; LOOP has no body or termination rule in the canon and is carried as a plain operation); the source of truth for a condition (the canon has no chain-level conditional; CHEK, WAIT, EVAL and DECI return values that the executing model reads, and IML evaluates nothing); Ω inside a branch (there are no branches; Ω marks the final output of its chain and stands last).
4. The header `#iml/0.4/88d05d0839c1`; a 0.3 header is read without a flag (same surface, same digest), and it is read with the 0.4 grammar: `#iml/0.3/88d05d0839c1 LS@LC BT:RD $` decodes, while a 0.3 codec answers E300 to that text, so the header names the writer and selects no grammar; a 0.2 header stays behind `--version 0.2`; compile writes 0.4 only. The registry and its digest, the value rules, the canonical print, the round-trip law and the six error codes are unchanged; the AST gains one field.
5. Checked against the canon files vendored under `canon/` and the pinned validator, and found absent from operation-chain syntax: conditionals (`when:` and `::RULE` are declaration-level), parallel groups and DAGs (`PARALLEL{}` and `T[a]→T[b]` are §7.5 narrative notation, which the validator reads as opaque note lines), error handling and retry (`::FALLBACK` is a v4.0 execution-layer declaration; the v4.0 PROTOCOL header's `fallback=` and `degrade=` are the envelope and stand in upstream `SPEC-v4.0-FINAL.md` at the pin, which is not vendored under `canon/`), and the token `||`, which the canon does not contain and which 0.4 drops from the excluded list. Two chains on one I-Lang line stay outside (E502 with its own message); the document form carries several chains.
6. Measured on the 72-chain golden corpus: 0.4 changes no figure of the 0.3 measurement, because the header differs by one digit and both encodings tokenise the two headers to the same count; the `corpus/golden-0.4/` chains are measured in `measurements/0.4-2026-09-18.md`. The figures are the figures; the efficiency gate below is unchanged and not met.

## 0.5, the declaration layer

Released 2026-09-18 as v0.5.0. On 2026-09-18 the owner decided A: the canon is not changed; IML carries the canon's declaration layer in machine form, derives everything from the canon and registers nothing of its own. The aim set with the decision is to cover the whole canon. 0.5 takes the part of the canon that is formally defined beyond operation chains, the declaration layer of SPEC.md §2.1 and §6 with the grammar of PATCH-2 §1, as the pinned validator reads it in raw mode; `SPEC-IML-0.5.md` §0.3 records what was checked.

Scope, and nothing beyond it:

1. A whole raw I-Lang document is carried in the document form, every line that the validator reads in raw mode included. The message form stays a header and one chain on one line.
2. The 49 names of PATCH-2 §1.5 and §1.6 (32 structural, 3 meta, the block terminator `::END_UNTRUSTED`, 13 narrative) get two-character codes by the verb-root algorithm, in a second registry file, `registry/iml-registry-0.5.json`, whose digest begins `7e29fae7f5ea`; every set is cross-checked against the validator. `::LATENCY` and `::CONFIDENCE`, which the canon has not registered, get no code and are carried as text. `registry/iml-registry-0.2.json` stays byte for byte, for 0.4 and 0.3 headers.
3. Block structure made explicit: the shapes of PATCH-2 §1.1 (brace, set span, wrapped field header), the opaque `::UNTRUSTED` block, the `::MODULE::NAME` segment, the temporal prefix, the addressing of the six double-brace narratives, body lines by their first token (PATCH-2 §1.2) and one level of nesting. A B8 body line is a chain, its continuation lines joined.
4. What the canon does not tokenize is carried as exact text: the content between the braces of a header, body lines other than B7 and B8, span content lines, opaque lines, and the other top-level lines (marker, tag lines, temporal binds and notes, annotations, colophon prose). Layout is not carried.
5. The header `#iml/0.5/7e29fae7f5ea`; a 0.4 or 0.3 header with `88d05d0839c1` is read for chains only, and a declaration or text line under it is E502; `compile` refuses a declaration in the message form (E502), and `compile --document` reads a whole document.
6. The laws L1 and L2 over documents; decompile prints the decoded document and reads it again; the pinned validator is the oracle, on every golden and generated document, input and canonical print. Where IML is stricter than the validator, `SPEC-IML-0.5.md` §9.1 lists the point with the validator's answer. The six error codes are unchanged.
7. Measured (`measurements/0.5-2026-09-18.md`): on the 20 golden documents the IML 0.5 documents are 5,526 `cl100k_base` tokens against 5,246 for the I-Lang sources as written and 5,345 for their canonical prints; the 0.5 header is one token longer than the 0.4 header, so the 72-chain message total is 2,510 (0.4: 2,438) and the document 1,316 (0.4: 1,315). The rule-sheet ceiling rises from 1,800 to 2,600 `cl100k_base` tokens for the declaration table and the document rules; the sheet is 2,596. The figures are the figures; the efficiency gate below is unchanged and not met.

## Deferred, and what of the canon stays open

Conditionals, loops beyond BATC, parallel groups and DAGs, error handling and retry. Each needs operation-chain syntax in the canon (ilang-spec) before a draft here: IML defines no construct of its own, and at the pinned commit none of these is chain syntax (`SPEC-IML-0.4.md` §0.3). The three definitions written for 0.4 stand until the canon changes.

What of the canon 0.5 leaves uncovered, stated as open and not promised for any version: mixed Markdown documents (the validator's mixed mode, which lints the I-Lang fences and the bare I-Lang lines of a Markdown file; IML reads every input as raw I-Lang); the tokenization of header content and of body text, to which the canon gives no grammar of their own; the checks of the judge validator (`ilang_judge_validator.py`, named in PATCH-2 Appendix A and not vendored here) and the WARN-level region and frame checks of v4.2, which IML does not apply.

MCP and A2A adapters are not codec work: they carry IML and do not change it, and they are not versioned with the specification.

## Belongs to the envelope, not to IML

Authority, signing, encryption, effect enforcement and version negotiation. Where a signature is used it covers the detached raw bytes of the message.

## Not planned

Serialising OpenAPI schemas; variable-length verb coding; outreach to transport or platform vendors.

## Gates

| Gate | Condition | If not met |
|------|-----------|------------|
| Efficiency claim | On at least 1000 real instruction chains and at least three tokenizers, total IML tokens, rule sheet and retries included, are below both I-Lang v4 text and JSON with schema. | No saving is claimed anywhere. |
| 1.0 | Two independent codecs pass each other's corpora; the conformance corpus is public; the core has been frozen for 90 days with no blocking defect. | Stays below 1.0. |
| 2.0 | Only for a breaking change that a measured need requires. | |

## Record

| Date | Event |
|------|-------|
| 2026-09-12 | Draft 0.1 filed. |
| 2026-09-18 | Draft 0.1 reviewed: six blocking defects; 0.2 scope fixed as above. |
| 2026-09-18 | Repository opened. |
| 2026-09-18 | 0.2 released as v0.2.0: specification, registry derived from ilang-spec 127ba56, reference codec, 72 golden and 76 malformed cases, measurement report. On the golden corpus IML is longer than the I-Lang canonical print in bytes, characters and tokens. |
| 2026-09-18 | 0.2.1 released as v0.2.1, a fix release after an adversarial review of a clean clone: `.gitattributes` pins LF so a Windows clone keeps the canon sha256; the I-Lang bare-value character set, the header shape and raw control characters inside quotes are fixed in the codec and stated in the specification; 15 malformed cases added; the measurement regenerated. The message form and the registry are unchanged (digest `88d05d0839c1`). |
| 2026-09-18 | 0.2.2 released as v0.2.2: citation metadata for the Zenodo archive; no other change. |
| 2026-09-18 | 0.3.0 released as v0.3.0: ASCII surface (`@`, `$`, one space) and the document form with one header for many chains; `SPEC-IML-0.3.md`, the 0.3 rule sheet, `corpus/golden-0.3/`, 41 malformed cases added, the 0.2 surface read behind `--version 0.2`, measurement before and after. On the golden corpus the 0.3 message is 2,438 cl100k_base tokens (0.2: 2,761; I-Lang print: 2,040) and the 0.3 document 1,315. The registry and its digest are unchanged. |
| 2026-09-18 | 0.3.1 released as v0.3.1, a fix release after an adversarial review of a clean clone: control-character set, Unicode whitespace in the bare rule, grammar line terminators, measured per-mark token cost, rule-sheet gaps, CLI edge cases. Message form and registry unchanged. |
| 2026-09-18 | 0.4.0 released as v0.4.0: flow within the canon. The verb reference of canon §3.9 on BATC (`[BATC:READ]`, `BT:RD`), multi-line chains joined on compile (PATCH-2 §1.7), the three definitions written from canon text, the header `#iml/0.4/` with a 0.3 header read without a flag; `SPEC-IML-0.4.md`, the 0.4 rule sheet, `corpus/golden-0.4/` (36 chains and one document pair), 29 malformed cases added, 2 removed (`[Π:READ]` and `[BATC:READ]`, valid in 0.4; the forms now open `corpus/golden-0.4/` as 001 and 002) and 2 re-coded (`=>[READ]` from E502 to E300, `[READ] [FMT]` from E300 to E502), 161 in all, `measurements/0.4-2026-09-18.md`. Conditionals, parallel groups, DAGs, error handling and retry were checked against the canon and the pinned validator and are not chain syntax there, so not in IML. The registry and its digest are unchanged; on the 72-chain corpus no figure changes. |
| 2026-09-18 | 0.4.1 released as v0.4.1, a fix release after an adversarial review of a clean clone; its random testing (24,000 chains, 5,000 IML lines, 480 documents) broke no law. Codec: a continuation line is joined only after a closed operation, a line of whitespace only ends a chain, and the writers refuse a control character other than a newline in a hand-built value. Command line: one leading byte order mark is dropped, and input that is not valid UTF-8 is E300 where 0.4.0 printed a traceback. Specification: three rows of the canon audit corrected (`::FALLBACK` is a v4.0 declaration and the PROTOCOL header is cited from an upstream file that is not vendored; an OUT target has canon text; the canon's example of a wrapped chain is the `E:` line of PATCH-2 §1.7), the ordering claims of the first definition removed, the spellings that the validator accepts and IML refuses listed, a 0.3 header read with the 0.4 grammar stated. 7 malformed cases added, 168 in all; the rule sheet is 1,798 cl100k_base tokens and the measurement report is regenerated; the continuous integration run fails on a tracked `.pyc`. Message form, registry, AST and error codes unchanged. |
| 2026-09-18 | 0.5.0 released as v0.5.0: the declaration layer, after the owner's decision A of the same day (the canon is not changed; IML carries the canon's declaration layer in machine form, derives everything from the canon and registers nothing of its own). Whole raw I-Lang documents in the document form; the 49 declaration codes derived from PATCH-2 §1.5 and §1.6 in `registry/iml-registry-0.5.json` (digest `7e29fae7f5ea`), the 0.2 registry kept byte for byte; `SPEC-IML-0.5.md`, the 0.5 rule sheet (2,596 `cl100k_base` tokens, ceiling 2,600), `corpus/golden-0.5/` (20 documents), 79 malformed cases added, 247 in all, 144 tests, `measurements/0.5-2026-09-18.md`. On the golden documents the IML documents are 5,526 `cl100k_base` tokens against 5,246 for the I-Lang sources as written. The chain registry, the chain subset, the message form and the six error codes are unchanged. |
