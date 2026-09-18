# IML roadmap

Versions are triggered by gates, not by dates. Each released version is an immutable tag.

## 0.2, the first implementable version

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
13. Measurement reported per tokenizer, in bytes, characters and tokens, including the rule sheet and the reply.

## Deferred to 0.3

Conditionals, loops, parallel groups and DAGs; error handling and retry; MCP and A2A adapters. Before any of these enters a draft, three definitions must exist: the loop body and its termination; the source of truth for a condition (I-Lang `EVAL` returns a map, not a boolean); and the meaning of Ω inside a branch.

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
