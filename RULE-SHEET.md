# IML (I-Lang Machine Layer) 0.3 rule sheet

IML is a machine spelling of I-Lang operation chains. This sheet is enough to turn IML 0.3 into I-Lang and an I-Lang chain into IML 0.3. Every verb root, key code and entity mark comes from `registry/iml-registry-0.2.json` (unchanged in 0.3; digest prefix `88d05d0839c1`). Use the file, never a guess. The full rules are in `SPEC-IML-0.3.md`.

## 1. Two shapes

Message, one line: `#iml/0.3/<12 lowercase hex> <chain>`: header, one space, chain.

Document: the header alone on the first line, then one chain per line. No blank line, no trailing space, no second header. Lines end with `\n` (`\r\n` accepted).

The hex is the registry digest prefix. A chain is ops separated by exactly one space. A `#iml/0.2/` header is the old surface (`Φ`, `Ω`, `→`): report E502.

## 2. Reading an op (IML to I-Lang)

Look at the first character of the op.

- `$`: the verb OUT. It may carry modifiers and must be the last op.
- Otherwise the first two characters, each `A-Z` or `0-9`, are the verb root. Registry: root to verb name.

Then, if the next character is `@`, a target follows: `@` plus two characters `A-Z` or `0-9` is a registered entity mark (registry: mark to `@NAME`); `@{NAME}` is the custom entity `@NAME`; a registered name in that form (`@{PREV}`) is E200.

Then modifiers, if any: `kk=value` pairs separated by `,`. A key is exactly two lowercase letters (registry: code to key name). A value runs to the next `,` or space outside quotes, or to the end of the line.

Value kinds, by first character:

- `"`: quoted string, escapes `\"` `\\` `\n`; the content is the unescaped text and may hold spaces and commas. A raw control character (U+0000 to U+001F, U+007F, U+0085, U+2028, U+2029) inside quotes is E300; a newline is written `\n`.
- `@`: entity reference, same two forms as a target; it becomes `@NAME`.
- `~`: value code. 0.3 has no codes: report E303; `~` with nothing after it is E300.
- `$`: reserved at the start of a value: report E303.
- anything else: bare. Copy the characters exactly (`007` stays `007`, `true` stays `true`). After the first character `$` `@` `~` `=` `>` `#` `{` `}` and `Φ` `Ω` `→` are content.

## 3. Writing I-Lang (canonical print)

`[VERB:@TARGET|k=v,k=v]=>[VERB|k=v]=>[Ω]`. Verb by canon name. OUT as `[Ω]` or `[Ω|k=v]`. No target: omit `:@TARGET`. No modifiers: omit `|` and the list. Ops joined by `=>`. A value prints bare unless it is empty, contains whitespace or one of `, | ] [ " \`, or starts with `@`; then quote it with the escapes above. `=` and `>` are content: `whr=score>80` prints bare. An entity reference prints `@NAME`. No whitespace anywhere. A document prints one line per chain, in order.

## 4. Writing IML (I-Lang to IML)

Input: `[VERB(:@TARGET)?(|k=v,k=v)?]` joined by `=>`, one chain per line, no whitespace before or after it. A bare value runs to the next `,` `|` or `]`; `=` and `>` are content. Aliases mean their verb: Σ MERGE, Δ DIFF, φ FILT, ∇ SORT, λ MAP, ∂ SPLIT, μ STAT, ψ SENT, ξ HASH, ζ CMPR, θ XLAT, Ω OUT, Π BATC.

- Verb, or its alias, to the root from the registry. `[OUT]` and `[Ω]` both become `$`, with no target.
- `@TARGET`: registered, `@` plus its mark; custom, `@{NAME}`. The name must match `[A-Z][A-Z0-9_]*`.
- Key to its code from the registry. Keys keep their order, separated by `,`.
- Value: a bare `@NAME` is an entity reference, written `@` plus mark or `@{NAME}`. Otherwise take the content (unescape a quoted string) and write it bare if it is not empty, contains none of `,` `"` `\` whitespace, and does not start with `~` `@` `$` `"`; otherwise quote it with the escapes. Never change the characters.
- Header from the registry. Ops joined by one space. Nothing else on the line. Document: the header alone on the first line, then each chain on its own line, in order.

## 5. Outside the subset

Report E502 and stop: a `::` declaration, `T[...]`, `PARALLEL{}` or `||`, a conditional, a loop, a comment, a verb in the target slot (`[Π:READ]`), OUT with a target, `$` before the last op, a second chain on one I-Lang line, anything after the chain, a message without a `#iml/` header, a well-shaped header with another version (`0.2` included) or another digest, a second header in a document.

## 6. On error

Stop at the first error. Report the code and the 0-based character offset (when compiling, also the op index). Never guess a root, key, mark or verb. Never repair, reorder or drop a value.

- E300 syntax: bad header shape (judged before the version and the digest), unterminated quote, bad escape, raw control character in a value, empty value, stray character (a `|` between modifiers, a tab, `Φ` `Ω` `→` in a syntax position), missing `=`, whitespace in a bare value or around a chain, two spaces between ops, a trailing space, a blank line in a document, a header with no chain, a second line after a message line, a dangling `=>`, `$@` in IML (OUT takes no target).
- E304 unknown root or verb (`OT` included).
- E302 unknown key code or key.
- E200 unknown mark, or an entity name that fails `[A-Z][A-Z0-9_]*`.
- E303 invalid value: a `~code`; a value starting with `$`; `[` `"` `\` inside an I-Lang bare value; `"` `\` inside an IML bare value. A value starting with `~` or `@` is read as a code or an entity reference and judged by that rule.
- E502 outside the subset, as in section 5.

## 7. Example

I-Lang: `[READ:@GH|path=readme.md]=>[XLAT|lng=zh]=>[FMT|fmt=md]=>[Ω]`

IML message: `#iml/0.3/88d05d0839c1 RD@GHpt=readme.md XLln=zh FMfm=md $`

The same chain and `[READ:@MYDATA|src=@PREV,whr="a, b"]=>[Ω|fmt=json]` as one document:

```
#iml/0.3/88d05d0839c1
RD@GHpt=readme.md XLln=zh FMfm=md $
RD@{MYDATA}sr=@PR,wh="a, b" $fm=json
```
