# IML (I-Lang Machine Layer) 0.2

::STATE{@SPEC, id:IML-0.2, revision:0.2.1, layer:machine, status:adopted, date:2026-09-18}
::STATE{@SPEC, canon:ilang-ai/ilang-spec, canon_pin:127ba56, canon_commit:127ba56f4eb1f35c2951d4aec4b7bd22831119ff, canon_version:v4.2.0}
::STATE{@SPEC, registers_nothing:true, verbs_derived:88, aliases_derived:13, keys_derived:49, entities_derived:25, value_code_tables:empty}
::STATE{@SPEC, replaces:drafts/IML-draft-0.1.md, scope_fixed_by:ROADMAP.md, subset:linear_pipelines}
::STATE{@SPEC, authors:Long_Quan_Zhu(Max/@SUN)+CC(@CLAUDE), orcid:0009-0004-4540-8082}

Purpose: IML (I-Lang Machine Layer) is a machine form of one I-Lang operation chain, with fixed-width codes derived from the canon. A codec compiles a chain in the supported subset to one line of IML and decompiles that line back to the chain. This document is the specification of version 0.2. It fixes the subset (§0), the registry and its derivation (§1), the lexical grammar and its segmentation rule (§2), the message header (§3), the treatment of OUT and of the Greek aliases (§4), the canonical I-Lang print (§5), the round-trip law (§6), the error codes (§7), the measurement report (§8), and what lies outside 0.2 (§9). The worked example is §10, the repository layout §11 and the revision history §12.

IML sits under I-Lang. I-Lang carries the meaning; IML is a spelling of it that a codec produces and reads. IML registers no verb, no modifier key, no entity, no declaration and no error code. Every code in an IML message is derived by a fixed algorithm from a name in the I-Lang canon at the pinned commit, and the derived table is a file in this repository. The registry file is authoritative for every code. Where a code appears in this text it is hand-derived by the algorithm of §1, and the file corrects the text, not the other way round.

What 0.2 promises is stated in §6 and tested: a chain in the subset round-trips at the AST level for the supported subset. Nothing is promised outside the subset. No efficiency figure is claimed; §8 says what is measured and how it is reported. Draft 0.1 is archived under `drafts/` and is not a specification. ROADMAP.md fixes the scope of 0.2 and what is deferred.

Notation: `Φ` is U+03A6, `Ω` is U+03A9, `→` is U+2192. Grammar is written in EBNF; `;` starts a comment. A section number without a document name (§2.4, §3, §4, §5, §9) refers to the canon `SPEC.md`; v4.1 §4.4.1, §4.4.2 and §5.4 refer to `SPEC-v4.1-MEDIA-PROFILE.md`.

---

## 0. Scope

One IML message carries one I-Lang operation chain on one line. The chain is a sequence of operations `[VERB(:TARGET)?(|mods)?]` joined by the pipe operator `=>`, with at least one operation.

The supported subset:

- Verbs: the 88 canon verbs of §3 and the 13 Greek aliases of §3.10. An alias means its verb.
- Target: a registered entity `@NAME` (25 registered: 8 core, 6 external, 8 role, 3 media) or a custom entity whose name matches `[A-Z][A-Z0-9_]*` (§5.3). A verb in the target slot, the `[Π:VERB]` and `[BATC:VERB]` form of §3.9, is not supported in 0.2 (E502).
- Modifiers: the 29 core keys of §4 and the 20 media profile keys of v4.1 §4.4.2, written `key=value` and separated by commas (§4: "Multiple modifiers separated by commas"). `|` separates the verb or the target from the modifier list and has no other place in an operation. The dialect that separates modifiers with `|` is not accepted: a bare value ends at `|`, and a `|` that follows a value is a stray character (§7, E300). The codec checks that a key is registered. It does not check the media gating of v4.1 §4.4.1: whether a profile key is in force for the target is I-Lang semantics, reported by the canon validator, not by the codec.
- Values: the forms of §2.4: barewords, quoted strings with the escapes `\"` `\\` `\n`, numbers, booleans, and entity references `@NAME`.
- OUT, alias `Ω`, may appear only as the last operation of the chain. It is not required.

Not supported in 0.2, reported as E502: declarations (`::`), temporal prefixes `T[...]`, `PARALLEL{}` and `||`, conditionals, loops, more than one chain in one message, comments, and anything after the chain.

::CLAUSE{SCOPE|conf:confirmed|scope:iml-0.2}
T:one_message=one_operation_chain_on_one_line|at_least_one_operation
T:verbs=88_canon+13_greek_aliases|alias_means_its_verb
T:target=registered_entity_25|or_custom_entity_name_upper_first_then_upper_digit_underscore
T:modifiers=29_core+20_media_profile|key=value|comma_separated|pipe_only_between_target_and_modifiers
T:values=SPEC.md_§2.4|bareword|quoted_with_escapes|number|boolean|entity_reference
T:OUT_or_Ω_only_as_the_last_operation|not_required
T:media_gating_not_checked_by_the_codec|left_to_I-Lang_semantics
A:verb_in_the_target_slot⇒E502
A:declaration|temporal_prefix|parallel|conditional|loop|comment|second_chain|trailing_text⇒E502
A:pipe_between_modifiers⇒E300

---

## 1. Registry

### 1.1 Sources and pin

The registry is derived from the canon at the pin by `tools/derive_registry.py` and written to `registry/iml-registry-0.2.json`. IML registers nothing of its own. The sources are vendored under `canon/`, and `canon/PIN` records the commit and the sha256 of each file:

- `SPEC.md`: verbs, aliases, core modifiers, entity tiers 1 and 2, and tier 3 by reference.
- `archive/SPEC-v5.0-PATCH-2.md`: the table of the role tier (tier 3), which `SPEC.md` §5.3 incorporates by reference rather than printing. Its eight names in table order are `@SYSTEM @RUNTIME @GRADER @USER @SELF @AGENT @TASK @TOOL`, the order the validator's `TIER3` also carries.
- `SPEC-v4.1-MEDIA-PROFILE.md`: the 20 media profile keys (§4.4.2) and entity tier 4 (§5.4).
- `ilang_grammar_validator.py`: cross-check only. Its `VERBS`, `ALIASES`, `MODIFIERS`, `MEDIA_PROFILE` and `TIER1` to `TIER4` must equal the parsed sets. The derivation aborts on any difference.

### 1.2 Order

The order of items is the order of first appearance in the canon tables: the §3 verb tables top to bottom (§3.1 to §3.9); the §4 modifier table; the §5 entity tables, tier 1, then tier 2, then tier 3; then the v4.1 §4.4.2 profile keys and the §5.4 media entities. Codes are assigned first come, first served, so the order is part of the derivation.

### 1.3 Code assignment

Every code is deterministic and comes from the letters and digits of the name: the name is upper-cased and every character outside `[A-Z0-9]` is dropped. A consonant is any letter that is not A, E, I, O, U, and any digit.

For a name whose first character is F, the candidates are tried in this order:

1. F followed by each consonant after it, left to right;
2. F followed by each remaining character after it (the vowels), left to right;
3. F followed by A to Z;
4. AA to ZZ.

The first candidate not yet used in the same table is taken.

- Verb root: exactly 2 characters, upper case, one table over the 88 verbs in order. OUT gets no root: OUT is written `Ω` (§4) and takes no candidate.
- Key code: exactly 2 characters, lower case, one table over the 49 keys (the core 29 first, then the media 20).
- Entity mark: exactly 2 characters, upper case, one table over the 25 registered entities in tier order. Custom entities have no mark; they are written `Φ{NAME}`.
- Value codes (`~code`): one closed table per key. In 0.2 every table is empty. The grammar for `~code` exists so that the message form does not change when tables are filled in a later version.

The three tables are separate. A root and a mark may coincide, since both are two characters of `[A-Z0-9]`; the `Φ` prefix tells a mark from a root, and a key code is lower case. No letter begins more than 26 names in any table, so stage 4 is never reached in 0.2. OUT is the only verb beginning with O and takes no root, so no root is `OT` (§4).

### 1.4 Registry file

`registry/iml-registry-0.2.json` is JSON, UTF-8, `\n` line ends, object members sorted. The `verbs`, `keys` and `entities` lists keep canon order. Members:

- `iml_version`
- `canon.commit`, and `canon.files` mapping each file name to its sha256
- `verbs`: a list of `{name, root}` in order (OUT carries no root: its `root` is null, §4)
- `aliases`: alias to verb, 13 entries
- `keys`: a list of `{name, code, tier}`, tier `core` or `media`
- `entities`: a list of `{name, mark, tier}`, tier 1, 2, 3 or 4
- `value_codes`: `{key: {}}` for every key
- `digest`: sha256 hex of the JSON serialised with `digest` absent, `sort_keys`, separators `(",", ":")`, `ensure_ascii` false

The message header carries the first 12 hex characters of `digest`. At the pin the digest begins `88d05d0839c1`; the file is authoritative, and a registry rebuilt from `canon/` by `tools/derive_registry.py` reproduces it.

### 1.5 Hand-derived codes used in this document

Applying §1.3 by hand to the canon tables at the pin gives the codes below. They are used in the examples of §2, §4 and §10. They are hand-derived; the registry file is authoritative, and where the file differs, the file is right.

| Name | Table | Code | How |
|------|-------|------|-----|
| READ | verb | RD | stage 1, first consonant |
| XLAT | verb | XL | stage 1 |
| FMT | verb | FM | stage 1 |
| MERGE | verb | MR | stage 1 |
| FILT | verb | FL | stage 1 |
| CNT | verb | CT | stage 1, second consonant; CN taken by CONV |
| LOG | verb | LG | stage 1 |
| BATC | verb | BT | stage 1 |
| @GH | entity | GH | stage 1 |
| @PREV | entity | PR | stage 1 |
| @LOG | entity | LG | stage 1; same two characters as the verb LOG, separate table |
| path | key | pt | stage 1 |
| lng | key | ln | stage 1 |
| fmt | key | fm | stage 1 |
| src | key | sr | stage 1 |
| whr | key | wh | stage 1 |
| len | key | le | stage 2; ln taken by lng |
| srt | key | sa | stage 3; sr taken by src, st by sty |

::CLAUSE{REGISTRY|conf:confirmed|scope:iml-0.2}
T:derived_from_canon_at_127ba56_by_tools/derive_registry.py|written_to_registry/iml-registry-0.2.json
T:iml_registers_nothing|every_code_is_derived_from_a_canon_name
T:item_order=first_appearance_in_the_canon_tables|codes_first_come_first_served
T:verb_root=2_upper|key_code=2_lower|entity_mark=2_upper|custom_entity_has_no_mark
T:OUT_has_no_root|written_Ω
T:value_code_tables=one_per_key|all_empty_in_0.2
T:digest=sha256_of_the_registry_json_without_its_digest_member|header_carries_the_first_12_hex
T:registry_file_authoritative_for_every_code|codes_in_this_text_are_hand_derived
A:validator_sets_differ_from_the_parsed_sets⇒derivation_aborts
A:code_taken_from_this_text_over_the_registry_file⇒drift

---

## 2. Lexical structure and segmentation

IML text is UTF-8, one line, no whitespace except the single space after the header. Reserved characters: `Φ` (U+03A6), `Ω` (U+03A9), `→` (U+2192), `~`, `,`, `=`, `"`, `\`, `{`, `}`, `#`, and whitespace.

### 2.1 Grammar

```
message   := header " " chain
header    := "#iml/0.2/" HEX12                      ; HEX12 = 12 lowercase hex chars = registry digest prefix
chain     := op ("→" op)*
op        := (ROOT target? | "Ω") mods?
ROOT      := [A-Z0-9]{2}                             ; a verb root from the registry
target    := "Φ" (MARK | "{" NAME "}")
MARK      := [A-Z0-9]{2}                             ; a registered entity mark
NAME      := [A-Z][A-Z0-9_]*                         ; a custom entity name, same rule as I-Lang @NAME
mods      := kv ("," kv)*
kv        := KEY "=" value
KEY       := [a-z]{2}                                ; a key code from the registry
value     := quoted | entityref | code | bare
quoted    := '"' (escape | [^"\\])* '"'              ; escape := "\" ( '"' | "\" | "n" )   (SPEC.md §2.4); no raw control character, see below
entityref := "Φ" (MARK | "{" NAME "}")
code      := "~" [a-z0-9]+                           ; looked up in value_codes[key]; 0.2: always E303
bare      := [^,→"\\ \t\r\n]+  and does not start with "~", "Φ", "\"", and is not empty
```

A raw control character inside a quoted value, U+0000 to U+001F, U+007F, U+2028 or U+2029, is E300, in IML input and in I-Lang input alike; a newline is written only as the escape `\n`.

### 2.2 Segmentation

Segmentation needs no lookahead: a root is always exactly two upper-case or digit characters at the start of an op; a target always starts with `Φ`; a key is always exactly two lower-case letters followed by `=`; a value ends at the next `,` or `→` outside quotes, or at the end of the message.

Reading an op from its first character: `Ω` is OUT; otherwise the first two characters are the root. After the root, `Φ` opens the target, a lower-case letter opens the modifier list, `→` opens the next op, and the end of the message ends the chain. After a target the same three continuations apply. In value position the first character decides the kind: `"` quoted, `Φ` entity reference, `~` code, anything else bare.

The `bare` production governs what a bare value may contain: any character except `,`, `→`, `"`, `\` and whitespace, with `~`, `Φ` and `"` excluded from the first position only. So `=`, `{`, `}`, `#`, `Ω`, `@`, and `~` or `Φ` after the first character are content inside a bare value. Segmentation never reads them, because a value ends only at `,`, `→` or the end of the message. `@` is not reserved in IML: a bare IML value beginning with `@` is a string, not a reference, and prints quoted in I-Lang (§5).

### 2.3 Typing

Every scalar keeps its lexeme. The AST records for each value its kind, one of `bare`, `quoted`, `entity`, `code`, and its text. Numbers and booleans are barewords whose text is preserved: `007` stays `007`, `1.0` stays `1.0`, `true` stays `true`. The codec never rewrites a value; a type is a validation tag, not a transformation. A `quoted` value's content is its unescaped text. `quoted` and `bare` values with the same content are the same AST value: quoting is spelling (§6). Duplicate keys in one operation are kept in order; the codec does not check them.

### 2.4 Entity references in value position

An entity reference in value position is a distinct kind. A bare value starting with `@` in I-Lang is always read as an entity reference; the name must match `[A-Z][A-Z0-9_]*` (E200 otherwise). A registered name compiles to `Φ` and its mark; a custom name compiles to `Φ{NAME}`; both decompile to `@NAME`. One form per meaning holds here too: a registered name written in the custom form, `Φ{PREV}`, is E200, in target position and in value position alike. With the hand-derived codes of §1.5:

| I-Lang | IML |
|--------|-----|
| `src=@PREV` | `sr=ΦPR` |
| `src=@MYDATA` | `sr=Φ{MYDATA}` |

### 2.5 Value spelling on compile

Compile writes an AST value by its kind. `entity`: `Φ` and the mark, or `Φ{NAME}`. `code`: `~` and the code; no I-Lang input yields this kind in 0.2, so compile never writes it. `bare` or `quoted`: bare when the content satisfies the `bare` production, otherwise quoted, with `"`, `\` and newline escaped as in §2.4. Compile never writes whitespace outside a quoted value.

::CLAUSE{LEXICAL|conf:confirmed|scope:iml-0.2}
T:utf8|one_line|no_whitespace_except_the_single_space_after_the_header
T:reserved=phi_omega_arrow_tilde_comma_equals_quote_backslash_braces_hash_whitespace
T:segmentation_without_lookahead|root_2_upper_at_op_start|target_starts_with_phi|key_2_lower_then_equals|value_ends_at_comma_or_arrow_outside_quotes
T:bare_production_governs_bare_content|first_position_excludes_tilde_phi_quote
T:every_scalar_keeps_its_lexeme|kind=bare|quoted|entity|code|type_is_a_validation_tag
T:duplicate_keys_kept_in_order|not_checked_by_the_codec
T:entity_reference_in_value_position_is_its_own_kind
T:compile_writes_bare_when_the_content_satisfies_bare|else_quoted_with_§2.4_escapes
A:codec_rewrites_a_value⇒violates_this_section
A:raw_control_character_inside_a_quoted_value⇒E300
A:value_starting_with_tilde_or_phi⇒read_as_code_or_entity_reference|judged_by_that_rule

---

## 3. Message header

The header is `#iml/0.2/` followed by 12 lowercase hex characters, followed by one space. The 12 characters are the first 12 of the registry digest (§1.4).

Decompile reads the header in this order. A message that does not begin with `#iml/` has no header: E502. Otherwise the header must match `^#iml/([0-9]+\.[0-9]+)/([0-9a-f]{12}) `: two digit groups joined by one dot, a slash, exactly 12 lowercase hex characters, one space. A message that begins with `#iml/` but does not match has a bad shape: E300; so `#iml/2/…`, upper-case hex, a hex run of another length, and a missing space are E300. A matched header whose version is not `0.2` is E502, and a matched header whose 12 characters are not the loaded registry's is E502. The shape is judged before the version and the digest: `#iml/0.1/` followed by upper-case hex is E300, not E502. Two spaces after the header match the pattern at the first space; the second space is then a stray character in the chain, E300. Compile always writes the header from the loaded registry.

::CLAUSE{HEADER|conf:confirmed|scope:iml-0.2}
T:header=#iml/0.2/+12_lowercase_hex+one_space
T:hex=the_first_12_characters_of_the_registry_digest
T:read_order=no_#iml/_prefix⇒E502|prefix_without_the_shape⇒E300|shape_with_another_version⇒E502|shape_with_another_digest⇒E502
T:compile_always_writes_the_header_from_the_loaded_registry
A:no_header|version_other_than_0.2|digest_prefix_mismatch⇒E502
A:header_present_with_a_bad_shape⇒E300

---

## 4. OUT and aliases

One byte form per meaning. Every Greek alias in I-Lang input means its verb and is encoded as that verb's root: with the hand-derived codes of §1.5, `Σ` compiles to `MR`, `φ` to `FL`, `Π` to `BT`. Decompile prints the verb by its canon name, never by an alias, with one exception.

OUT is the one verb encoded by a Greek letter: `Ω`, because that is its canon alias and the message terminator. `Ω` may carry modifiers (`Ωfm=json`) and may appear only as the last op (E502 otherwise). `OUT` has no two-character root; `→OT` is E304. In I-Lang input `[OUT]` and `[Ω]` are two spellings of the same operation; both compile to `Ω`, and decompile prints `[Ω]` (§5).

The `op` production gives `Ω` no target slot. An I-Lang `[OUT:@X]` or `[Ω:@X]` is outside the subset (E502).

::CLAUSE{OUT-ALIAS|conf:confirmed|scope:iml-0.2}
T:one_byte_form_per_meaning
T:greek_alias_in_input_means_its_verb|encoded_as_that_verb_root
T:OUT_is_the_one_verb_encoded_by_a_greek_letter|Ω=its_canon_alias_and_the_message_terminator
T:Ω_may_carry_modifiers|no_target_slot|only_as_the_last_op
T:decompile_prints_OUT_in_the_Ω_form
A:two_character_root_for_OUT⇒E304
A:Ω_before_the_last_op⇒E502
A:OUT_with_a_target_in_input⇒E502

---

## 5. Canonical I-Lang print (decompile output)

### 5.1 Print

The form is `[VERB:@TARGET|k=v,k=v]=>[...]`. Verbs print by canon name. OUT prints as `[Ω]`, with modifiers `[Ω|k=v]`. Targets print `@NAME`. An operation without a target omits `:@TARGET`; an operation without modifiers omits `|` and the list.

A value prints bare when its content is not empty, contains no whitespace, none of `,` `|` `]` `[` `"` `\`, and does not start with `@`. `=` and `>` are content: `whr=score>80` (the example of draft 0.1, which the canon validator accepts) and `whr=lvl:fatal` (canon §10.1) print bare. Otherwise it prints quoted with the §2.4 escapes. An entity reference prints `@NAME`. No whitespace anywhere.

### 5.2 Accepted input

`parse_L2` reads a chain in the subset of §0. It accepts the canonical form and three spellings of it: a Greek alias for a verb, `[OUT]` for `[Ω]`, and quotes around a value whose content could print bare. A bare value in I-Lang input runs to the next `,`, `|` or `]`; a `|` there is a stray character (E300, §0). Inside a bare value `[`, `"` and `\` are E303 and whitespace is E300; `=` and `>` are content. Content with `,` `|` `]` `[` `"` `\` or whitespace is written quoted (§2.4: quoted strings carry spaces or special characters). A bare value beginning with `@` is an entity reference (§2.4). Whitespace outside a quoted value is a stray character (E300); so are whitespace before or after the chain, and a dangling `=>` at the end of the chain.

::CLAUSE{PRINT|conf:confirmed|scope:iml-0.2}
T:verb_by_canon_name|OUT_as_Ω|target_as_@NAME|modifiers_key=value_comma_separated|ops_joined_by_the_pipe_operator
T:value_bare_iff_not_empty|no_whitespace|none_of_comma_pipe_brackets_quote_backslash|not_starting_with_@|equals_and_greater_than_are_content|else_quoted_with_§2.4_escapes
T:entity_reference_prints_@NAME
T:no_whitespace_anywhere
T:parse_accepts_the_canonical_form_plus_three_spellings|alias|OUT_word|quotes_around_bare_content
A:print_reproduces_the_input_spelling⇒not_canonical
A:whitespace_outside_quotes_in_input⇒E300
A:whitespace_before_or_after_the_chain|dangling_pipe_operator⇒E300
A:bracket_quote_or_backslash_inside_a_bare_value⇒E303

---

## 6. Round-trip law

Let `parse_L2` read canon I-Lang into the AST, `print_L2` write it, `compile` be AST to IML text, and `decompile` be IML text to AST.

- L1 (AST fidelity): for every I-Lang chain x in the subset, `decompile(compile(parse_L2(x))) == parse_L2(x)`. AST equality compares the verb, the target (by name), the modifier keys in order, and the value, kind-normalised: `bare` and `quoted` compare by content, `entity` by name, `code` by code.
- L2 (canonical text): `print_L2` is idempotent, `print_L2(parse_L2(print_L2(a))) == print_L2(a)`, and `compile(decompile(m)) == m` for every IML message m that the codec itself produced.
- L3 (original bytes): not promised. Quotes, alias spelling (`Σ` against `MERGE`), and `[OUT]` against `[Ω]` are spelling.

Tests:

- A golden corpus, hand-written, of at least 60 chains covering every verb at least once, every key at least once, every registered entity, custom entities, quoted values with each escape, numbers like `007`, booleans, entity references in values, `Ω` with and without modifiers, and chains of length 1 to 8.
- A malformed corpus of at least 40 inputs with expected error codes.
- A generator with `random.Random(20260918)` producing 10,000 chains over the registry. The generator is not the oracle. The oracle for L2 legality is the vendored canon validator, run on the printed I-Lang of a 500-sample.

::CLAUSE{ROUNDTRIP|conf:confirmed|scope:iml-0.2}
T:L1=decompile(compile(parse_L2(x)))==parse_L2(x)|for_every_chain_in_the_subset
T:AST_equality=verb+target_name+modifier_keys_in_order+value_kind_normalised
T:L2=print_L2_idempotent|compile(decompile(m))==m_for_every_codec_produced_m
T:L3_not_promised|quotes+alias_spelling+OUT_against_Ω_are_spelling
T:tests=golden_corpus_60_or_more|malformed_corpus_40_or_more|generator_seed_20260918_10000_chains
T:generator_is_not_the_oracle|oracle=vendored_canon_validator_on_printed_I-Lang|500_sample
A:round_trip_claimed_outside_the_subset⇒unsupported_claim
A:original_bytes_claimed⇒contradicts_L3

---

## 7. Errors

The codec fails closed; the first error stops it. Codes reuse §9 of the canon. The codec raises these six codes and no other.

| Code | Canon name | Raised when |
|------|------------|-------------|
| E300 | Syntax Error | bad header shape (§3); unterminated quote; bad escape; raw control character inside a quoted value; empty value; stray character, a `|` between modifiers included; missing `=`; whitespace in a bare value; whitespace before or after the chain; a dangling `=>` |
| E304 | Unknown Verb | unknown root (decompile) or unknown verb (compile), `OT` included |
| E302 | Invalid Modifier | unknown key code (decompile) or unknown key (compile) |
| E200 | Entity Not Found | unknown registered mark; an entity name that does not match `[A-Z][A-Z0-9_]*` |
| E303 | Invalid Value | bare value containing `,` `|` `]` `[` `"` `\` (§5.1); `~code` not in the key's table (always, in 0.2) |
| E502 | Unsupported Format | no header; wrong version; digest mismatch; declaration or other construct outside the subset; OUT not last; `[Π:VERB]` form; more than one chain |

Reading of the table. A raw control character (U+0000 to U+001F, U+007F, U+2028, U+2029) is E300 wherever it appears in a value, bare or quoted; a newline is only ever the escape `\n` inside quotes. In I-Lang input a bare value ends at `,`, `|` or `]`, so of the E303 set only `[`, `"` and `\` can stand inside one; a `|` that follows a value is a stray character, E300 (§0). In IML a bare value ends at `,` or `→`, and `"` or `\` inside it is E303 (§2.1). A value that starts with `~` or `Φ` is not a bare value: it is read as a code or as an entity reference and judged by that rule (E303 for a code outside its table, E200 or E300 for a malformed reference); a value that starts with `"` is a quoted value. A character that no production admits at its position, outside a value, is a stray character, E300; so is an op that starts with neither `Ω` nor two characters of `[A-Z0-9]`. Two characters of `[A-Z0-9]` that are not a root in the registry are E304. On the header, §3 gives the split between E502 and E300.

Error objects carry `code`, `message`, `offset` (0-based character index into the input) and, for compile, the operation index.

::CLAUSE{ERRORS|conf:confirmed|scope:iml-0.2}
T:fail_closed|the_first_error_stops_the_codec
T:codes=SPEC.md_§9|E300+E304+E302+E200+E303+E502|no_other_code
T:error_object=code+message+offset_0_based_char_index|compile_adds_the_operation_index
A:unknown_root_key_or_mark_guessed_or_skipped⇒violates_fail_closed
A:error_code_registered_by_IML⇒contradicts_registers_nothing

---

## 8. Measurement

`tools/measure.py` writes `measurements/0.2-YYYY-MM-DD.md`. For each golden chain it records bytes (UTF-8), characters, and tokens under `cl100k_base` and `o200k_base` (tiktoken 0.14.0, offline cache), for three forms: the I-Lang canonical print (§5), the IML message, and a JSON form `{"c":[{"v":"READ","t":"@SRC","m":{"path":"x"}}]}`, compact with no spaces, the one JSON mapping used as a baseline and stated as such. It also records the cost of `RULE-SHEET.md` in the same units. The report gives totals and per-form means.

No percentage is called a saving; the table is the table. The report states the tokenizer scope: named encodings, not any vendor's billing. If tiktoken is missing, the tool writes bytes and characters and says that tokens were not measured (§11).

::CLAUSE{MEASURE|conf:confirmed|scope:iml-0.2}
T:tools/measure.py_writes_measurements/0.2-YYYY-MM-DD.md
T:per_golden_chain=bytes_utf8+characters+tokens_cl100k_base+tokens_o200k_base|tiktoken_0.14.0_offline_cache
T:three_forms=I-Lang_canonical_print|IML_message|compact_JSON_baseline_stated_as_the_one_mapping_used
T:rule_sheet_cost_in_the_same_units|totals+per_form_means
T:tokenizer_scope=named_encodings|not_a_vendor_billing
A:percentage_called_a_saving⇒violates_the_ROADMAP_gate
A:figure_published_without_corpus_tokenizer_and_both_baselines⇒unsupported_claim

---

## 9. Outside 0.2

Not in 0.2. The constructs listed at the end of §0 are outside the subset and a 0.2 codec reports them as E502.

Deferred to 0.3 (ROADMAP.md): conditionals, loops, parallel groups and DAGs; error handling and retry; MCP and A2A adapters. Before any of these enters a draft, three definitions must exist: the loop body and its termination; the source of truth for a condition (I-Lang `EVAL` returns a map, not a boolean); and the meaning of `Ω` inside a branch.

Belongs to the envelope, not to IML: authority, signing, encryption, effect enforcement and version negotiation. Where a signature is used it covers the detached raw bytes of the message. A receiver treats an IML message as untrusted input under I-Lang v4.0 until the envelope says otherwise.

Not planned: serialising OpenAPI schemas; variable-length verb coding; outreach to transport or platform vendors.

Later versions. A value-code table may be filled in a later version (§1.3). A message written under 0.2 keeps its meaning, because a literal is never marked and a code is always marked.

Claims. ROADMAP.md gates the efficiency claim: on at least 1000 real instruction chains and at least three tokenizers, total IML tokens, rule sheet and retries included, below both I-Lang v4 text and JSON with schema. Until that gate is met no saving is claimed anywhere. The 1.0 gate is two independent codecs passing each other's corpora, a public conformance corpus, and a core frozen for 90 days with no blocking defect.

::CLAUSE{OUTSIDE-0.2|conf:confirmed|scope:iml-0.2}
T:deferred_to_0.3=conditionals+loops+parallel_groups+DAGs|error_handling_and_retry|MCP_and_A2A_adapters
T:before_a_0.3_draft=loop_body_and_termination|source_of_truth_for_a_condition|meaning_of_Ω_inside_a_branch
T:envelope=authority+signing+encryption+effect_enforcement+version_negotiation|signature_covers_the_detached_raw_bytes
T:receiver_treats_an_IML_message_as_untrusted_input_under_v4.0_until_the_envelope_says_otherwise
T:not_planned=OpenAPI_schema_serialisation|variable_length_verb_coding|vendor_outreach
T:efficiency_claim_gated_by_ROADMAP|no_saving_claimed_until_the_gate_is_met
A:0.3_construct_read_by_a_0.2_codec⇒E502
A:security_property_attributed_to_IML⇒belongs_to_the_envelope

---

## 10. Worked example

All codes below are hand-derived (§1.5); the registry file is authoritative for every code. `88d05d0839c1` is the first 12 hex characters of the registry digest at the pin; the registry file is authoritative and a rebuilt registry must reproduce it.

### 10.1 The README chain

I-Lang:

```
[READ:@GH|path=readme.md]=>[XLAT|lng=zh]=>[FMT|fmt=md]=>[Ω]
```

IML:

```
#iml/0.2/88d05d0839c1 RDΦGHpt=readme.md→XLln=zh→FMfm=md→Ω
```

Reading the message after the header: `RD` is a root, READ; `Φ` opens a target, `GH` is a mark, `@GH`; `p` opens the modifier list, `pt` is a key, `path`, `=`, then a value running to `→`, `readme.md`, bare; `→` opens the next op; `XL` is XLAT with no target; `ln=zh` is `lng=zh`; `→`; `FM` is FMT; `fm=md` is `fmt=md`; `→`; `Ω` is OUT with no modifiers, and the message ends. Decompile prints the I-Lang line above unchanged.

### 10.2 Custom entity, entity reference, quoted value, modifiers on OUT

I-Lang:

```
[READ:@MYDATA|src=@PREV,whr="a, b"]=>[Ω|fmt=json]
```

IML:

```
#iml/0.2/88d05d0839c1 RDΦ{MYDATA}sr=ΦPR,wh="a, b"→Ωfm=json
```

`@MYDATA` is custom, so it is written `Φ{MYDATA}`. `@PREV` in value position is an entity reference, kind `entity`, written `ΦPR`. The content `a, b` contains `,` and a space, so it is quoted in both forms. `Ω` carries `fm=json` and is the last op.

### 10.3 Alias in input

I-Lang input, from the canon §10.1:

```
[φ:@LOG|whr=lvl:fatal]=>[CNT]=>[Ω]
```

IML:

```
#iml/0.2/88d05d0839c1 FLΦLGwh=lvl:fatal→CT→Ω
```

`φ` means FILT and is encoded as FILT's root. `lvl:fatal` contains no special character and stays bare. `LG` here is the mark of `@LOG`; at the start of an op the same two characters would be the root of the verb LOG, and the `Φ` prefix keeps the two apart. Decompile prints `[FILT:@LOG|whr=lvl:fatal]=>[CNT]=>[Ω]`: the alias is spelling (§6, L3) and the canonical print uses the verb name.

::CLAUSE{EXAMPLE|conf:confirmed|scope:iml-0.2}
T:codes_hand_derived_by_§1.3|registry_file_authoritative
T:digest_prefix_at_the_pin=88d05d0839c1|registry_file_authoritative
T:decompile_prints_the_I-Lang_line_unchanged|alias_input_prints_by_verb_name
A:digest_prefix_copied_from_this_text⇒E502_against_the_real_registry

---

## 11. Repository layout (non-normative)

The executable form of §1, §6 and §7 lives beside this document:

- `SPEC-IML-0.2.md` (this text) and `RULE-SHEET.md` (the rule sheet, at most 1,800 tokens under `cl100k_base`)
- `canon/`: vendored `SPEC.md`, `archive/SPEC-v5.0-PATCH-2.md`, `SPEC-v4.1-MEDIA-PROFILE.md`, `ilang_grammar_validator.py` at the pin, and `canon/PIN`
- `tools/derive_registry.py` and `registry/iml-registry-0.2.json`
- `iml/__init__.py`, `iml/registry.py`, `iml/l2.py`, `iml/codec.py`, `iml/errors.py`, `iml/__main__.py` (CLI: `compile`, `decompile`, `roundtrip`, `check-registry`)
- `corpus/golden/*.ilang` with `*.iml` (expected), and `corpus/malformed/cases.json`
- `tests/test_registry.py`, `tests/test_codec.py`, `tests/test_roundtrip.py`, `tests/test_malformed.py` (stdlib unittest, `python -m unittest discover -s tests`)
- `tools/measure.py` and `measurements/0.2-2026-09-18.md`
- `.github/workflows/test.yml` (python 3.12: derive check and unittest)
- `.gitattributes` (LF for every text file)

Python 3.10 or later. Standard library only for the codec and the tests; tiktoken only in `tools/measure.py`, and optional there. All files LF line ends, UTF-8, no BOM; `.gitattributes` pins LF for every text file, so a Windows clone made with `core.autocrlf=true` keeps the sha256 of `canon/` and `tools/derive_registry.py --check` passes. `LICENSE` and `drafts/` are not touched; `README.md` and `ROADMAP.md` are updated at every release.

::CLAUSE{FILES|conf:confirmed|scope:iml-0.2}
T:python_3.10_or_later|standard_library_only_for_codec_and_tests|tiktoken_only_in_tools/measure.py_and_optional
T:LF_line_ends|UTF-8|no_BOM|.gitattributes_pins_LF
T:README_and_ROADMAP_updated_at_every_release
T:non_normative|the_registry_file_and_the_corpora_are_the_executable_form_of_§1_§6_§7
A:LICENSE_or_drafts_edited_by_0.2_work⇒out_of_scope

---

## 12. Revision history

- 0.2.0 (2026-09-18): first implemented version.
- 0.2.1 (2026-09-18): clarifications in §0 §2 §3 §5 §7 §11; the message form and the registry are unchanged (digest 88d05d0839c1…).

::CLAUSE{REVISIONS|conf:confirmed|scope:iml-0.2}
T:0.2.1=clarifications_in_§0_§2_§3_§5_§7_§11|message_form_unchanged|registry_unchanged|digest_88d05d0839c1
A:revision_changes_the_message_form_or_the_registry⇒a_new_version_not_a_revision
