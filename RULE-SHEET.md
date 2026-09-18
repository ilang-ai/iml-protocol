# IML (I-Lang Machine Layer) 0.5 rule sheet

IML is a machine spelling of I-Lang chains and documents; this sheet is enough to read and write IML 0.5. Verb roots, key codes, entity marks, aliases and declaration codes come from `registry/iml-registry-0.5.json` (digest prefix `7e29fae7f5ea`): use the file, never a guess. Full rules: `SPEC-IML-0.5.md`.

## 1. Two shapes

Message, one line: `#iml/0.5/<12 lowercase hex> <chain>`. Document: the header alone on the first line, then the items of section 5; no blank line, no trailing space, no second header. Lines end with `\n` (`\r\n` accepted). The hex is the registry digest prefix; ops are separated by exactly one space. Write `#iml/0.5/`. Also read `#iml/0.4/` and `#iml/0.3/` (prefix `88d05d0839c1`): chains only, else E502. `#iml/0.2/` is the old surface (`Φ`, `Ω`, `→`): E502.

## 2. Reading an op (IML to I-Lang)

- `$` is OUT: may carry modifiers; no target or verb reference (`$@`, `$:` E300); must be the last op.
- Otherwise the first two characters, each A-Z or 0-9, are the verb root (registry; unknown E304).

Next `@` opens a target: `@` plus two such characters is a registered entity mark (registry); `@{NAME}` is the custom entity `@NAME`; a registered name in that form (`@{PREV}`) is E200.

Next `:` opens a verb reference, after `BT` (BATC) only: two such characters, a verb root (registry; unknown E304); print `[BATC:VERB]`. `:` after another root, `BT:` without such a root, or a target after the reference: E300.

Then modifiers: `kk=value` pairs separated by `,`; a key is two lowercase letters (registry; unknown E302); a value runs to the next `,` or space outside quotes, or to the line end. Value kinds, by first character:

- `"`: quoted; escapes `\"` `\\` `\n`; the content is the unescaped text, spaces and commas included. A raw control character (U+0000 to U+001F, U+007F, U+0085, U+2028, U+2029) inside quotes is E300.
- `@`: entity reference, the two target forms; it becomes `@NAME`.
- `~`: value code; none exist: E303; `~` with nothing after it is E300.
- `$`: reserved: E303.
- anything else: bare; copy it exactly (`007` stays `007`). `:` is content anywhere, and after the first character so are `$ @ ~ = > # { } Φ Ω →`. `"` or `\` inside is E303; whitespace inside is E300.

## 3. Writing I-Lang (canonical print)

`[VERB:@TARGET|k=v,k=v]=>[VERB|k=v]=>[Ω]`. Verb by canon name; OUT as `[Ω]` or `[Ω|k=v]`; a verb reference as `[BATC:VERB]`, never `Π` or an alias. Without a target omit `:@TARGET`; without modifiers omit `|` and the list. Ops joined by `=>`, on one line. A value prints bare unless empty, containing whitespace or one of `, | ] [ " \`, or starting with `@`; else quoted with the escapes above. `= > :` are content. An entity reference prints `@NAME`. No whitespace anywhere in a chain. Documents: section 5.

## 4. Writing IML (I-Lang to IML)

Input: `[VERB(:@TARGET)?(|k=v,k=v)?]` joined by `=>`; whitespace around the chain or a dangling `=>` is E300. A line whose first non-blank characters are `=>` continues the chain above it: drop its leading whitespace and join (trailing whitespace is E300); the text so far must end with `]` outside quotes, else E300. With no chain above it (a blank or whitespace-only line ends a chain) it is E300 "orphan `=>` continuation: no preceding operation line". Parse the joined text as one line. A bare value runs to the next `,` `|` or `]`; `[ " \` inside it E303; whitespace inside it or a `|` after it E300. An alias means its verb (registry).

- Verb or alias to its root (registry; unknown E304). `[OUT]` and `[Ω]` become `$`, with no target.
- `@TARGET`: registered, `@` plus its mark; custom, `@{NAME}`; the name must match `[A-Z][A-Z0-9_]*` (else E200).
- `[BATC:VERB]` or `[Π:VERB]` (canon §3.9; BATC only: elsewhere a target without `@` is E300): `BT:` plus the verb's root, an alias meaning its verb; unknown (`REED`, `read`) E304; OUT or `Ω` E502. `[BATC:@SRC]` is an entity target; `[BATC|op=READ]` is a string modifier (`BTop=READ`); never convert one into the other.
- Key to its code (registry; unknown E302); keys keep their order, separated by `,`.
- Value: a bare `@NAME` is an entity reference, `@` plus mark or `@{NAME}`. Otherwise take the content (unescape a quoted string): bare if not empty, without `, " \` or whitespace, and not starting with `~ @ $ "`; else quoted with the escapes. Never change the characters.
- Header `#iml/0.5/` plus the digest prefix, then the ops joined by one space on one line whatever the source layout, nothing else.

## 5. Documents

A line's first character decides it: A-Z, 0-9 or `$` a chain; `"` a text; `:` a declaration; a space a line of the declaration above; else E300. Texts, heads, addressings, prefixes: quoted strings, escapes `\"` `\\` only (`\n` or a raw control character, TAB included: E300), `""` when empty.

From I-Lang (blank and `---` lines and whitespace around a line are layout):

- `"text"`: the `::ILANG::` marker (first or last line only), `[TAG:value]` lines, `T[n]=value`, `T[a]→T[b]`, `PARALLEL{...}`, lines starting `→` or `<<<`, `::LATENCY`, `::CONFIDENCE`, prose without `:: [ { } | ⇒ =>` before the first declaration or operation.
- An operation line and its `=>` lines: a chain.
- `T[n] ::NAME::SUB{head}`: `:`, code, `T"n"`, `::SUB` (MODULE only), `"head"`, each part when present. SAY THINK ACT DECIDE DISCOVER CREATE take `{addr}{head}`: `"addr""head"`. Unknown name or code: E300.
- Set span `::NAME{`, lines, `}`: `{` (a narrative `"addr"{`), then each line ` "text"`. Wrapped `::NAME{head`, lines, the last ending in `}`: `{"head"`, then the lines, the last without `}`.
- `::UNTRUSTED{...delimiter:X...}`: the lines before the line `X`, verbatim, each ` "line"`.
- Body (lines indented deeper, or `T:` `A:` `KEY:` `[TAG]` `T[n]=` lines at the header's indent; a token after the header comes first): ` "text"` for those, binds, notes, `→` lines, prose (only under LESSON MODULE LIST RULE OBJECTIVE, else E300); ` <chain>` for an operation line (a `=>` line joins the line directly above); ` :<code>"head"` for a nested `::NAME{head}` (one level, brace form only), its body lines `  "text"`.

To I-Lang: `T[n] ::NAME::SUB{head}`, body indented two spaces, nested body four; span `::NAME{`, lines, `}`; wrapped `::NAME{head`, lines, `}` after the last; opaque: header, lines verbatim, `X`. No blank line, except one between a declaration with no body and a next `[TAG]` or `T[n]=` text line.

Codes: STATE ST, TRUST TR, ALIVE AL, MEMORY MM, GENE GN, GENE_MUTABLE GM, RULE RL, ACTIVATE AC, FACT FC, LESSON LS, PROGRESS PR, PRIORITY PT, DECAY DC, IMMUNE IM, UNTRUSTED UN, BUDGET BD, STATUS SS, OBJECTIVE OB, RUBRIC RB, EVIDENCE EV, PRIOR PI, FALLBACK FL, JUDGE JD, BOUNDARY BN, DIM DM, MODE MD, FUNC FN, SCHEMA SC, CASE CS, CLAUSE CL, MODULE ML, LIST LT, GRAMMAR GR, BODY BY, REGISTRY RG, END_UNTRUSTED EN, SAY SY, THINK TH, ACT AT, DECIDE DD, DISCOVER DS, CREATE CR, EVENT ET, SILENCE SL, META MT, IRONY IR, FORESHADOW FR, CALLBACK CB, EMOTION_FIELD EM.

## 6. Outside

Report E502 and stop: anything but one chain per line on `compile` without `--document` or in a message; a comment or anything after a chain, a second chain on one line, OUT with a target, `$` before the last op, OUT or `Ω` as a verb reference; no `#iml/` header, a well-shaped header with another version or digest, a second header. Conditionals, parallel groups, DAGs, error handling and retry have no chain syntax in the canon and none in IML.

## 7. On error

Stop at the first error. Report the code and the 0-based character offset (compiling: also the op index; a multi-line chain: its first line, the offset in the joined text). Never guess a root, key, mark, verb or code; never repair, reorder or drop anything. Six codes only:

- E300 syntax: every case marked E300 above, plus: bad header shape (judged before the version and the digest), unterminated quote, bad escape, empty value, missing `=`, two spaces between ops, a tab, a blank line in a document, a header with nothing after it, a second line after a message line, `Φ Ω →` or any other stray character in a syntax position, and in a document every structure error the canon validator reports as E300.
- E304 unknown root, verb or verb reference (`OT` included). E302 unknown key code or key. E200 unknown mark or bad entity name.
- E303 invalid value, as above; a value starting with `~` or `@` is judged as a code or an entity reference.
- E502 outside, as in section 6.

## 8. Example

I-Lang:

```
::GENE{verify_first}
  [READ:@SRC]=>[Ω]
```

IML 0.5 document:

```
#iml/0.5/7e29fae7f5ea
:GN"verify_first"
 RD@SR $
```
