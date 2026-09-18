# IML: I-Lang Machine Layer (Experimental Draft)

A compact machine form of I-Lang v4.x operation chains, designed to be compiled from and decompiled back to readable I-Lang. IML (I-Lang Machine Layer) sits under I-Lang, which carries the meaning, and rides inside whatever transport carries the message. It replaces neither.

- **Status:** experimental draft. Draft 0.1 is archived here as the dated record and is not a specification. 0.2 is the first version intended to be implemented; its scope is fixed in [ROADMAP.md](ROADMAP.md).
- **Canon:** the I-Lang protocol is specified in [ilang-ai/ilang-spec](https://github.com/ilang-ai/ilang-spec). IML registers no verb, modifier key, entity or declaration of its own; its vocabulary is derived from that canon at a pinned commit.
- **Creator:** [Long Quan Zhu](https://orcid.org/0009-0004-4540-8082) (Max, @SUN). iLang Inc.
- **License:** MIT.

## What is in this repository

| Path | What it is |
|------|------------|
| `drafts/IML-draft-0.1.md` | The first draft, filed 2026-09-12, kept unchanged below its banner. Reviewed 2026-09-18; the banner records what did not hold. |
| `ROADMAP.md` | The scope of 0.2, what is deferred to 0.3, what belongs to the envelope, the gates for 1.0, and the rule for any efficiency claim. |
| `LICENSE` | MIT. |

Nothing here is normative for I-Lang. A change to I-Lang goes through ilang-spec.

## What IML is

An I-Lang v4.x operation chain such as

```
[READ:@GH|path=readme.md]=>[XLAT|lng=zh]=>[FMT|fmt=md]=>[Ω]
```

is meant to have one short machine form that a codec produces and a codec reads back to the same chain. The codec is deterministic. The vocabulary (verb roots, key codes, entity marks) is a table derived from the I-Lang canon, so IML never has to invent a word.

Draft 0.1 wrote the idea down as four axioms. The review of 2026-09-18 found that, as written, the first three do not hold: the value abbreviation scheme is not injective, two character substitutions are lossy, values have no delimiting or escaping, and the control-flow constructs have no I-Lang v4.x form to decompile to. Version 0.2 therefore narrows the promise to what can be tested: a stated subset of I-Lang (linear pipelines) that round-trips at the AST level, a vocabulary derived from the canon, and a reference codec with a golden corpus.

## What IML does not claim

- **Not lossless in general.** 0.2 states exactly which subset of I-Lang round-trips, and tests it. Outside that subset nothing is promised.
- **Not "read the same by any model".** Determinism belongs to the codec. How a model reads IML is measured, not asserted, and no figure of that kind is published without the test set, the scoring rule and the endpoints used.
- **No token or cost saving.** Any such figure is published only with the corpus, the tokenizer, and the two baselines it is compared against (I-Lang v4 text, and JSON with schema), including the cost of the rule sheet a model has to be given.
- **No security of its own.** Authority, signing and encryption belong to the envelope and transport that carry a message. A receiver treats an IML message as untrusted input under I-Lang v4.0 until the envelope says otherwise.

## Naming

Write `IML (I-Lang Machine Layer)` on first mention. IML is a representation layer under I-Lang; it is not a transport.

## Versions

| Version | State |
|---------|-------|
| 0.1 | Archived draft, filed 2026-09-12. Not implemented. |
| 0.2 | Scope fixed 2026-09-18, see ROADMAP.md. In preparation. |
