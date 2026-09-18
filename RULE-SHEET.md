# IML (I-Lang Machine Layer) 0.2 rule sheet

IML is a one-line spelling of one I-Lang operation chain. This sheet is enough to turn an IML message back into I-Lang and an I-Lang chain into IML. Every verb root, key code and entity mark comes from `registry/iml-registry-0.2.json`. Use the file, never a guess. The full rules are in `SPEC-IML-0.2.md`.

## 1. Message shape

`#iml/0.2/<12 lowercase hex> <chain>`: header, one space, chain. The hex is the registry digest prefix. The chain is ops joined by `→` (U+2192). No other whitespace anywhere.

## 2. Reading an op (IML to I-Lang)

Look at the first character of the op.

- `Ω` (U+03A9): the verb OUT. It may carry modifiers and must be the last op.
- Otherwise the first two characters, each `A-Z` or `0-9`, are the verb root. Registry: root to verb name.

Then, if the next character is `Φ` (U+03A6), a target follows: `Φ` plus two characters `A-Z` or `0-9` is a registered entity mark (registry: mark to `@NAME`); `Φ{NAME}` is the custom entity `@NAME`.

Then modifiers, if any: `kk=value` pairs separated by `,`. A key is exactly two lowercase letters (registry: code to key name). A value runs to the next `,` or `→` outside quotes, or to the end of the message.

Value kinds, by first character:

- `"`: quoted string, escapes `\"` `\\` `\n`; the content is the unescaped text.
- `Φ`: entity reference, same two forms as a target; it becomes `@NAME`.
- `~`: value code. 0.2 has no codes: report E303.
- anything else: bare. Copy the characters exactly (`007` stays `007`, `true` stays `true`).

## 3. Writing I-Lang (canonical print)

`[VERB:@TARGET|k=v,k=v]=>[VERB|k=v]=>[Ω]`. Verb by canon name. OUT as `[Ω]` or `[Ω|k=v]`. No target: omit `:@TARGET`. No modifiers: omit `|` and the list. Ops joined by `=>`. A value prints bare unless its content contains whitespace or one of `, | ] [ " \ = >` or starts with `@`; then quote it with the escapes above. An entity reference prints `@NAME`. No whitespace anywhere.

## 4. Writing IML (I-Lang to IML)

Input: `[VERB(:@TARGET)?(|k=v,k=v)?]` joined by `=>`, one chain. Aliases mean their verb: Σ MERGE, Δ DIFF, φ FILT, ∇ SORT, λ MAP, ∂ SPLIT, μ STAT, ψ SENT, ξ HASH, ζ CMPR, θ XLAT, Ω OUT, Π BATC.

- Verb, or its alias, to the root from the registry. `[OUT]` and `[Ω]` both become `Ω`, with no target.
- `@TARGET`: registered, `Φ` plus its mark; custom, `Φ{NAME}`. The name must match `[A-Z][A-Z0-9_]*`.
- Key to its code from the registry. Keys keep their order, separated by `,`.
- Value: a bare `@NAME` is an entity reference, written `Φ` plus mark or `Φ{NAME}`. Otherwise take the content (unescape a quoted string) and write it bare if it is not empty, contains none of `,` `→` `"` `\` whitespace, and does not start with `~` `Φ` `"`; otherwise quote it with the escapes. Never change the characters.
- Header from the registry. Ops joined by `→`. Nothing else in the message.

## 5. Outside the subset

Report E502 and stop: a `::` declaration, `T[...]`, `PARALLEL{}` or `||`, a conditional, a loop, a comment, a verb in the target slot (`[Π:READ]`), OUT with a target, `Ω` before the last op, a second chain, anything after the chain, a missing or wrong header (version not 0.2, digest not the registry's).

## 6. On error

Stop at the first error. Report the code and the 0-based character offset (when compiling, also the op index). Never guess a root, key, mark or verb. Never repair, reorder or drop a value.

- E300 syntax: bad header shape, unterminated quote, bad escape, empty value, stray character, missing `=`.
- E304 unknown root or verb (`OT` included).
- E302 unknown key code or key.
- E200 unknown mark, or an entity name that fails `[A-Z][A-Z0-9_]*`.
- E303 invalid value: a `~code`, a reserved character inside a bare value, a bare value starting with `~` `Φ` `"`.
- E502 outside the subset, as in section 5.

## 7. Example

I-Lang: `[READ:@GH|path=readme.md]=>[XLAT|lng=zh]=>[FMT|fmt=md]=>[Ω]`

IML: `#iml/0.2/88d05d0839c1 RDΦGHpt=readme.md→XLln=zh→FMfm=md→Ω`

The codes here are hand-derived by the registry algorithm; the registry file is authoritative. `88d05d0839c1` is the digest prefix of the registry file at the pin.

Read back: `RD` READ; `ΦGH` @GH; `pt=readme.md` path, bare; `→`; `XL` XLAT, no target; `ln=zh` lng; `→`; `FM` FMT; `fm=md` fmt; `→`; `Ω` OUT; end. Print: the I-Lang line above.
