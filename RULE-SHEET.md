# IML (I-Lang Machine Layer) 0.4 rule sheet

IML is a machine spelling of I-Lang operation chains; this sheet is enough to read and write IML 0.4. Every verb root, key code, entity mark and alias comes from `registry/iml-registry-0.2.json` (digest prefix `88d05d0839c1`): use the file, never a guess. The full rules are in `SPEC-IML-0.4.md`.

## 1. Two shapes

Message, one line: `#iml/0.4/<12 lowercase hex> <chain>`. Document: the header alone on the first line, then one chain per line; no blank line, no trailing space, no second header. Lines end with `\n` (`\r\n` accepted). The hex is the registry digest prefix; ops are separated by exactly one space. Write `#iml/0.4/`; read `#iml/0.3/` the same way, no flag. `#iml/0.2/` is the old surface (`Φ`, `Ω`, `→`): E502.

## 2. Reading an op (IML to I-Lang)

- `$` is OUT: may carry modifiers; no target or verb reference (`$@`, `$:` E300); must be the last op.
- Otherwise the first two characters, each A-Z or 0-9, are the verb root (registry; unknown E304).

Next `@` opens a target: `@` plus two such characters is a registered entity mark (registry); `@{NAME}` is the custom entity `@NAME`; a registered name in that form (`@{PREV}`) is E200.

Next `:` opens a verb reference, after `BT` (BATC) only: two such characters, a verb root (registry; unknown E304); print `[BATC:VERB]`. `:` after another root, `BT:` without such a root, or a target after the reference: E300.

Then modifiers: `kk=value` pairs separated by `,`; a key is two lowercase letters (registry; unknown E302); a value runs to the next `,` or space outside quotes, or to the end of the line. Value kinds, by first character:

- `"`: quoted; escapes `\"` `\\` `\n`; the content is the unescaped text, spaces and commas included. A raw control character (U+0000 to U+001F, U+007F, U+0085, U+2028, U+2029) inside quotes is E300.
- `@`: entity reference, the two target forms; it becomes `@NAME`.
- `~`: value code; none exist: E303; `~` with nothing after it is E300.
- `$`: reserved: E303.
- anything else: bare; copy it exactly (`007` stays `007`). `:` is content anywhere, and after the first character so are `$ @ ~ = > # { } Φ Ω →`. `"` or `\` inside is E303; whitespace inside is E300.

## 3. Writing I-Lang (canonical print)

`[VERB:@TARGET|k=v,k=v]=>[VERB|k=v]=>[Ω]`. Verb by canon name; OUT as `[Ω]` or `[Ω|k=v]`; a verb reference as `[BATC:VERB]`, never `Π` or an alias. Omit `:@TARGET` without a target, and `|` with the list without modifiers. Ops joined by `=>`, on one line. A value prints bare unless empty, containing whitespace or one of `, | ] [ " \`, or starting with `@`; else quoted with the escapes above. `= > :` are content. An entity reference prints `@NAME`. No whitespace anywhere; a document prints one line per chain, in order.

## 4. Writing IML (I-Lang to IML)

Input: `[VERB(:@TARGET)?(|k=v,k=v)?]` joined by `=>`; whitespace around the chain or a dangling `=>` is E300. A line whose first non-blank characters are `=>` continues the chain above it: drop its leading whitespace and join (trailing whitespace is E300). With no chain above it (at the start, or after a blank line, which ends a chain) it is E300 "orphan `=>` continuation: no preceding operation line". Parse the joined text as one line. A bare value runs to the next `,` `|` or `]`; `[ " \` inside it E303; whitespace inside it or a `|` after it E300. An alias means its verb (registry).

- Verb or alias to its root (registry; unknown E304). `[OUT]` and `[Ω]` become `$`, with no target.
- `@TARGET`: registered, `@` plus its mark; custom, `@{NAME}`; the name must match `[A-Z][A-Z0-9_]*` (else E200).
- `[BATC:VERB]` or `[Π:VERB]` (canon §3.9; BATC only: elsewhere a target without `@` is E300): `BT:` plus the verb's root, an alias meaning its verb (`[Π:Σ]` is `BT:MR`); unknown (`REED`, `read`) E304; OUT or `Ω` E502. `[BATC:@SRC]` is an entity target; `[BATC|op=READ]` is a string modifier (`BTop=READ`); never convert one into the other.
- Key to its code (registry; unknown E302); keys keep their order, separated by `,`.
- Value: a bare `@NAME` is an entity reference, `@` plus mark or `@{NAME}`. Otherwise take the content (unescape a quoted string): bare if not empty, without `, " \` or whitespace, and not starting with `~ @ $ "`; else quoted with the escapes. Never change the characters.
- Header `#iml/0.4/` plus the digest prefix, then the ops joined by one space on one line, whatever the source layout, and nothing else. Document: the header alone on the first line, then one chain per line, in order.

## 5. Outside the subset

Report E502 and stop: a `::` declaration, `T[...]`, `PARALLEL{}`, a comment or anything after the chain, a second chain on one I-Lang line, OUT with a target, `$` before the last op, OUT or `Ω` as a verb reference, no `#iml/` header, a well-shaped header with another version or digest, a second header in a document. Conditionals, parallel groups, DAGs, error handling and retry have no chain syntax in the canon and none in IML.

## 6. On error

Stop at the first error. Report the code and the 0-based character offset (compiling: also the op index; a multi-line chain: its first line, the offset in the joined text). Never guess a root, key, mark or verb; never repair, reorder or drop a value. Six codes, no other:

- E300 syntax: every case marked E300 above, plus: bad header shape (judged before the version and the digest), unterminated quote, bad escape, empty value, missing `=`, two spaces between ops, a tab, a blank line in a document, a header with no chain, a second line after a message line, `Φ Ω →` or any other stray character in a syntax position.
- E304 unknown root, verb or verb reference (`OT` included). E302 unknown key code or key. E200 unknown mark or bad entity name.
- E303 invalid value, as above; a value starting with `~` or `@` is judged as a code or an entity reference.
- E502 outside the subset, as in section 5.

## 7. Example

I-Lang `[LIST:@LOCAL|mch=*.md]=>[Π:READ]=>[Σ]=>[Ω]` is the message `#iml/0.4/88d05d0839c1 LS@LCmc=*.md BT:RD MR $`.
