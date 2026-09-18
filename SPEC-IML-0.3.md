# IML (I-Lang Machine Layer) 0.3

::STATE{@SPEC, id:IML-0.3, revision:0.3.0, layer:machine, status:adopted, date:2026-09-18}
::STATE{@SPEC, canon:ilang-ai/ilang-spec, canon_pin:127ba56, canon_commit:127ba56f4eb1f35c2951d4aec4b7bd22831119ff, canon_version:v4.2.0}
::STATE{@SPEC, registers_nothing:true, verbs_derived:88, aliases_derived:13, keys_derived:49, entities_derived:25, value_code_tables:empty, registry_unchanged_since:0.2, digest_prefix:88d05d0839c1}
::STATE{@SPEC, supersedes:SPEC-IML-0.2.md, change:surface_only, surface:ascii, header:document_level, scope_fixed_by:ROADMAP.md, subset:linear_pipelines}
::STATE{@SPEC, authors:Long_Quan_Zhu(Max/@SUN)+CC(@CLAUDE), orcid:0009-0004-4540-8082}

Purpose: IML (I-Lang Machine Layer) is a machine form of I-Lang operation chains, with fixed-width codes derived from the canon. A codec compiles a chain in the supported subset to one line of IML and decompiles that line back to the chain; a document carries many such lines under one header. This document is the specification of version 0.3. 0.3 changes the surface of a message and nothing else: the marks are ASCII (`@` opens a target or an entity reference, `$` is OUT, one space separates operations), and the header may stand once at the head of a document instead of once on every line. The subset (§0), the registry and its derivation (§1), the value rules (§2.3 to §2.5), the treatment of OUT and of the Greek aliases (§4), the canonical I-Lang print (§5), the round-trip law (§6), the error codes (§7), the measurement report (§8) and what lies outside (§9) are those of 0.2, restated here so that this text stands alone; §2.1, §2.2, §2.6 and §3 replace their 0.2 counterparts. The worked examples are §10, the repository layout §11 and the revision history §12. `SPEC-IML-0.2.md` stays unchanged as the record of 0.2.

IML sits under I-Lang. I-Lang carries the meaning; IML is a spelling of it that a codec produces and reads. IML registers no verb, no modifier key, no entity, no declaration and no error code. Every code in an IML message is derived by a fixed algorithm from a name in the I-Lang canon at the pinned commit, and the derived table is a file in this repository. The registry file is authoritative for every code. Where a code appears in this text it is hand-derived by the algorithm of §1, and the file corrects the text, not the other way round.

What 0.3 promises is stated in §6 and tested: a chain in the subset round-trips at the AST level, on one line or inside a document. Nothing is promised outside the subset. No efficiency figure is claimed; §0.1 records what was measured before and after the surface change, and §8 says how measurement is reported. Draft 0.1 is archived under `drafts/` and is not a specification. ROADMAP.md fixes the scope of 0.3 and what is deferred.

Notation: the 0.3 marks are `@` (U+0040), `$` (U+0024) and the space (U+0020). The 0.2 marks, named where this text compares the two surfaces, are `Φ` (U+03A6), `Ω` (U+03A9) and `→` (U+2192). Grammar is written in EBNF; `;` starts a comment. A section number without a document name (§2.4, §3, §4, §5, §9) refers to the canon `SPEC.md`; v4.1 §4.4.1, §4.4.2 and §5.4 refer to `SPEC-v4.1-MEDIA-PROFILE.md`.

---

## 0. Scope

### 0.1 Why 0.3

The 0.2 measurement on the 72-chain golden corpus (`measurements/0.2-2026-09-18.md`) put the IML message at 2,761 `cl100k_base` tokens against 2,040 for the I-Lang canonical print. Two causes were measured on the same corpus: the per-message header `#iml/0.2/88d05d0839c1 ` costs 17 tokens on every one of the 72 messages, and `Φ`, `Ω` and `→` are multibyte characters that each cost about one extra token under `cl100k_base` and about half a token under `o200k_base` (measured over the 308 marks of the corpus: 323 and 169 extra tokens). 0.3 replaces the three marks by one ASCII character each (`@`, `$`, the space) and lets the header stand once at the head of a document, so that it is paid once per document rather than once per chain. Measured after the change on the same corpus, the same encodings and the same JSON baseline (`measurements/0.3-2026-09-18.md`):

| form | bytes | chars | cl100k_base | o200k_base |
|------|---:|---:|---:|---:|
| I-Lang canonical print | 4462 | 4395 | 2040 | 2134 |
| IML 0.2 message (one header per chain) | 4964 | 4504 | 2761 | 2606 |
| IML 0.3 message (one header per chain) | 4506 | 4502 | 2438 | 2437 |
| IML 0.3 document (one header for the 72 chains) | 3015 | 3011 | 1315 | 1313 |
| JSON baseline | 8334 | 8330 | 3195 | 3262 |

The 0.3 rule sheet costs 1,792 `cl100k_base` tokens (0.2: 1,607). The figures are the figures: the message form is still above the I-Lang print in tokens on this corpus, the document form is below it, and neither is called anything more than that. ROADMAP.md gates any efficiency claim on a larger corpus, more tokenizers, the rule sheet and the reply; that gate is unchanged and not met.

### 0.2 The subset

One IML chain carries one I-Lang operation chain on one line. The chain is a sequence of operations `[VERB(:TARGET)?(|mods)?]` joined by the pipe operator `=>`, with at least one operation. A message carries one chain; a document carries one or more chains, one per line, under one header (§3).

The supported subset, unchanged since 0.2:

- Verbs: the 88 canon verbs of §3 and the 13 Greek aliases of §3.10. An alias means its verb.
- Target: a registered entity `@NAME` (25 registered: 8 core, 6 external, 8 role, 3 media) or a custom entity whose name matches `[A-Z][A-Z0-9_]*` (§5.3). A verb in the target slot, the `[Π:VERB]` and `[BATC:VERB]` form of §3.9, is not supported (E502).
- Modifiers: the 29 core keys of §4 and the 20 media profile keys of v4.1 §4.4.2, written `key=value` and separated by commas (§4: "Multiple modifiers separated by commas"). `|` separates the verb or the target from the modifier list and has no other place in an operation. The dialect that separates modifiers with `|` is not accepted: a bare value ends at `|`, and a `|` that follows a value is a stray character (§7, E300). The codec checks that a key is registered. It does not check the media gating of v4.1 §4.4.1: whether a profile key is in force for the target is I-Lang semantics, reported by the canon validator, not by the codec.
- Values: the forms of §2.4: barewords, quoted strings with the escapes `\"` `\\` `\n`, numbers, booleans, and entity references `@NAME`.
- OUT, alias `Ω`, may appear only as the last operation of the chain. It is not required.

Not supported, reported as E502: declarations (`::`), temporal prefixes `T[...]`, `PARALLEL{}` and `||`, conditionals, loops, more than one chain on one I-Lang line, comments, and anything after the chain.

::CLAUSE{SCOPE|conf:confirmed|scope:iml-0.3}
T:0.3=surface_change_only|marks_ascii|header_at_document_level|registry+AST+laws+errors_unchanged_since_0.2
T:measured_reason=0.2_message_2761_cl100k_against_I-Lang_2040|header_17_tokens_per_message|multibyte_marks_2_to_3_tokens_each
T:measured_after=0.3_message_2438|0.3_document_1315|same_corpus_same_encodings|no_claim_attached
T:one_chain=one_operation_chain_on_one_line|message_carries_one|document_carries_one_or_more_under_one_header
T:verbs=88_canon+13_greek_aliases|alias_means_its_verb
T:target=registered_entity_25|or_custom_entity_name_upper_first_then_upper_digit_underscore
T:modifiers=29_core+20_media_profile|key=value|comma_separated|pipe_only_between_target_and_modifiers
T:values=SPEC.md_§2.4|bareword|quoted_with_escapes|number|boolean|entity_reference
T:OUT_or_Ω_only_as_the_last_operation|not_required
T:media_gating_not_checked_by_the_codec|left_to_I-Lang_semantics
A:verb_in_the_target_slot⇒E502
A:declaration|temporal_prefix|parallel|conditional|loop|comment|second_chain_on_one_line|trailing_text⇒E502
A:pipe_between_modifiers⇒E300
A:figure_of_§0.1_quoted_as_a_saving⇒violates_the_ROADMAP_gate

---

## 1. Registry

The registry of 0.3 is the registry of 0.2, unchanged: the same file, the same derivation, the same digest. 0.3 derives nothing new and registers nothing of its own.

### 1.1 Sources and pin

The registry is derived from the canon at the pin by `tools/derive_registry.py` and written to `registry/iml-registry-0.2.json`. The file keeps its 0.2 name and its `iml_version` member reads `0.2`: that member names the vocabulary, which 0.3 leaves as it is; the version in a header is the surface version (§3). The sources are vendored under `canon/`, and `canon/PIN` records the commit and the sha256 of each file:

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

- Verb root: exactly 2 characters, upper case, one table over the 88 verbs in order. OUT gets no root: OUT is written `$` (§4) and takes no candidate.
- Key code: exactly 2 characters, lower case, one table over the 49 keys (the core 29 first, then the media 20).
- Entity mark: exactly 2 characters, upper case, one table over the 25 registered entities in tier order. Custom entities have no mark; they are written `@{NAME}`.
- Value codes (`~code`): one closed table per key. Every table is empty in 0.3 as in 0.2. The grammar for `~code` exists so that the message form does not change when tables are filled in a later version.

The three tables are separate. A root and a mark may coincide, since both are two characters of `[A-Z0-9]`; the `@` prefix tells a mark from a root, and a key code is lower case. No letter begins more than 26 names in any table, so stage 4 is never reached. OUT is the only verb beginning with O and takes no root, so no root is `OT` (§4).

### 1.4 Registry file

`registry/iml-registry-0.2.json` is JSON, UTF-8, `\n` line ends, object members sorted. The `verbs`, `keys` and `entities` lists keep canon order. Members:

- `iml_version`: `0.2`, the version of the vocabulary (§1.1)
- `canon.commit`, and `canon.files` mapping each file name to its sha256
- `verbs`: a list of `{name, root}` in order (OUT carries no root: its `root` is null, §4)
- `aliases`: alias to verb, 13 entries
- `keys`: a list of `{name, code, tier}`, tier `core` or `media`
- `entities`: a list of `{name, mark, tier}`, tier 1, 2, 3 or 4
- `value_codes`: `{key: {}}` for every key
- `digest`: sha256 hex of the JSON serialised with `digest` absent, `sort_keys`, separators `(",", ":")`, `ensure_ascii` false

The header carries the first 12 hex characters of `digest`. At the pin the digest begins `88d05d0839c1`, the same 12 characters as in 0.2; the file is authoritative, and a registry rebuilt from `canon/` by `tools/derive_registry.py` reproduces it.

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
| @SRC | entity | SR | stage 1 |
| path | key | pt | stage 1 |
| lng | key | ln | stage 1 |
| fmt | key | fm | stage 1 |
| src | key | sr | stage 1 |
| whr | key | wh | stage 1 |
| len | key | le | stage 2; ln taken by lng |
| srt | key | sa | stage 3; sr taken by src, st by sty |

::CLAUSE{REGISTRY|conf:confirmed|scope:iml-0.3}
T:registry_of_0.3=registry_of_0.2|same_file|same_derivation|same_digest_88d05d0839c1
T:derived_from_canon_at_127ba56_by_tools/derive_registry.py|written_to_registry/iml-registry-0.2.json
T:iml_version_member_0.2=version_of_the_vocabulary|header_carries_the_surface_version
T:iml_registers_nothing|every_code_is_derived_from_a_canon_name
T:item_order=first_appearance_in_the_canon_tables|codes_first_come_first_served
T:verb_root=2_upper|key_code=2_lower|entity_mark=2_upper|custom_entity_has_no_mark
T:OUT_has_no_root|written_$
T:value_code_tables=one_per_key|all_empty_in_0.3
T:digest=sha256_of_the_registry_json_without_its_digest_member|header_carries_the_first_12_hex
T:registry_file_authoritative_for_every_code|codes_in_this_text_are_hand_derived
A:validator_sets_differ_from_the_parsed_sets⇒derivation_aborts
A:code_taken_from_this_text_over_the_registry_file⇒drift
A:registry_changed_by_a_surface_release⇒a_new_digest_and_a_new_version_not_0.3

---

## 2. Lexical structure and segmentation

Every syntax character of IML 0.3 is ASCII; the content of a value is whatever UTF-8 text the I-Lang value carries, copied without change. Reserved characters: `@`, `$`, `~`, `,`, `=`, `"`, `\`, `{`, `}`, `#`, the space, and every other whitespace character.

### 2.1 Grammar

```
document  := header NL chain (NL chain)* NL?         ; the header once, then one chain per line; one final line terminator accepted
message   := header SP chain NL?                      ; the one-line form; NL is `\n` or `\r\n`
header    := "#iml/0.3/" HEX12                        ; HEX12 = 12 lowercase hex chars = registry digest prefix
NL        := "\n"                                     ; "\r\n" is accepted as NL and printed as "\n"
SP        := " "                                      ; exactly one space
chain     := op (SP op)*
op        := (ROOT target? | "$") mods?               ; "$" is OUT
ROOT      := [A-Z0-9]{2}                              ; a verb root from the registry
target    := "@" (MARK | "{" NAME "}")
MARK      := [A-Z0-9]{2}                              ; a registered entity mark
NAME      := [A-Z][A-Z0-9_]*                          ; a custom entity name, same rule as I-Lang @NAME
mods      := kv ("," kv)*
kv        := KEY "=" value
KEY       := [a-z]{2}                                 ; a key code from the registry
value     := quoted | entityref | code | bare
quoted    := '"' (escape | [^"\\])* '"'               ; escape := "\" ( '"' | "\" | "n" )   (SPEC.md §2.4); no raw control character
entityref := "@" (MARK | "{" NAME "}")
code      := "~" [a-z0-9]+                            ; looked up in value_codes[key]; 0.3: always E303
bare      := [^,"\\]+  with no whitespace (any character Python str.isspace() reports, U+00A0 and U+3000 included) and no control character, and not starting with "~", "@", "$", "\""
```

A raw control character inside a quoted value, U+0000 to U+001F, U+007F, U+0085, U+2028 or U+2029, is E300, in IML input and in I-Lang input alike; a newline is written only as the escape `\n`. So no line terminator ever stands inside a value, and a document is split into lines before any value is read (§2.6).

### 2.2 Segmentation

Segmentation needs no lookahead: a root is always exactly two upper-case or digit characters at the start of an op; a target always starts with `@`; a key is always exactly two lower-case letters followed by `=`; a value ends at the next `,` or space outside quotes, or at the end of the line.

Reading an op from its first character: `$` is OUT; otherwise the first two characters are the root. After the root, `@` opens the target, a lower-case letter opens the modifier list, a space opens the next op, and the end of the line ends the chain. After a target the same three continuations apply. In value position the first character decides the kind: `"` quoted, `@` entity reference, `~` code, `$` reserved (E303), anything else bare.

The `bare` production governs what a bare value may contain: any character except `,`, `"`, `\`, whitespace and control characters, with `~`, `@`, `$` and `"` excluded from the first position only. So `=`, `>`, `{`, `}`, `#`, and `~`, `@` or `$` after the first character are content inside a bare value, and so are the 0.2 marks `Φ`, `Ω` and `→`, which 0.3 does not reserve. Segmentation never reads them, because a value ends only at `,`, a space or the end of the line. `$` at the first position of a value is reserved for a later version and is E303 in 0.3; a value whose content starts with `$` is written quoted (§2.5). A bare IML value beginning with `@` is an entity reference, so a string whose content begins with `@` is written quoted (`sr="@PREV"`) and prints quoted in I-Lang too (§5).

### 2.3 Typing

Every scalar keeps its lexeme. The AST records for each value its kind, one of `bare`, `quoted`, `entity`, `code`, and its text. Numbers and booleans are barewords whose text is preserved: `007` stays `007`, `1.0` stays `1.0`, `true` stays `true`. The codec never rewrites a value; a type is a validation tag, not a transformation. A `quoted` value's content is its unescaped text. `quoted` and `bare` values with the same content are the same AST value: quoting is spelling (§6). Duplicate keys in one operation are kept in order; the codec does not check them. The AST of 0.3 is the AST of 0.2, object for object.

### 2.4 Entity references in value position

An entity reference in value position is a distinct kind. A bare value starting with `@` in I-Lang is always read as an entity reference; the name must match `[A-Z][A-Z0-9_]*` (E200 otherwise). A registered name compiles to `@` and its mark; a custom name compiles to `@{NAME}`; both decompile to `@NAME`. One form per meaning holds here too: a registered name written in the custom form, `@{PREV}`, is E200, in target position and in value position alike. With the hand-derived codes of §1.5:

| I-Lang | IML 0.3 | IML 0.2 (record) |
|--------|---------|------------------|
| `src=@PREV` | `sr=@PR` | `sr=ΦPR` |
| `src=@MYDATA` | `sr=@{MYDATA}` | `sr=Φ{MYDATA}` |
| `src="@PREV"` (a string) | `sr="@PREV"` | `sr=@PREV` |

### 2.5 Value spelling on compile

Compile writes an AST value by its kind. `entity`: `@` and the mark, or `@{NAME}`. `code`: `~` and the code; no I-Lang input yields this kind in 0.3, so compile never writes it. `bare` or `quoted`: bare when the content satisfies the `bare` production, otherwise quoted, with `"`, `\` and newline escaped as in §2.4. A quoted value may hold spaces and commas; the space is a separator only outside quotes. Compile never writes whitespace outside a quoted value except the one space between ops and the one after a message header.

### 2.6 Lines

A chain ends at the end of its line. The line terminator is `\n`; `\r\n` is accepted as a terminator and printed as `\n`. A `\r` anywhere else is a control character (E300). Since no line terminator can stand inside a value (§2.1), a document is read line by line, and each line is one chain read by the rules above. Trailing spaces on a line are E300: the space after the last op opens an op that is not there.

::CLAUSE{LEXICAL|conf:confirmed|scope:iml-0.3}
T:syntax_characters_ascii|value_content_utf8_copied_without_change
T:reserved=at_dollar_tilde_comma_equals_quote_backslash_braces_hash_space_whitespace
T:segmentation_without_lookahead|root_2_upper_at_op_start|target_starts_with_at|key_2_lower_then_equals|value_ends_at_comma_or_space_outside_quotes_or_end_of_line
T:bare_production_governs_bare_content|first_position_excludes_tilde_at_dollar_quote
T:0.2_marks_phi_omega_arrow_not_reserved|content_inside_a_bare_value|stray_in_a_syntax_position
T:dollar_at_value_start_reserved_for_a_later_version|E303_in_0.3|written_quoted_on_compile
T:every_scalar_keeps_its_lexeme|kind=bare|quoted|entity|code|type_is_a_validation_tag|AST_same_as_0.2
T:duplicate_keys_kept_in_order|not_checked_by_the_codec
T:entity_reference_in_value_position_is_its_own_kind|string_starting_with_at_written_quoted
T:compile_writes_bare_when_the_content_satisfies_bare|else_quoted_with_§2.4_escapes
T:line_terminator=LF|CRLF_accepted_and_printed_as_LF|no_terminator_inside_a_value
A:codec_rewrites_a_value⇒violates_this_section
A:raw_control_character_inside_a_quoted_value⇒E300
A:value_starting_with_tilde_or_at⇒read_as_code_or_entity_reference|judged_by_that_rule
A:trailing_space_on_a_line⇒E300

---

## 3. Header and the two forms

The header is `#iml/0.3/` followed by 12 lowercase hex characters, the first 12 of the registry digest (§1.4). It stands in one of two places:

- Message: the header, one space, one chain, on one line. This is the 0.2 shape with the 0.3 version and surface.
- Document: the header alone on the first line; every following line is one chain. A document carries at least one chain. Decompile of a document yields one I-Lang line per chain, in order.

The form is decided by the first line: a header followed by a space is a message; a header followed by the end of the line is a document. The text may end with one line terminator (`\n` or `\r\n`), which terminates the last line and is not a blank line. In a document a blank line is E300, a trailing space on a line is E300 (§2.6), and a second header line is E502. A chain line without a header, and not inside a document, is E502 (no header). A second line after a message line is E300: a message is one line, and several chains take the document form.

Decompile reads the header in this order. A text that does not begin with `#iml/` has no header: E502. Otherwise the first line must match `^#iml/([0-9]+\.[0-9]+)/([0-9a-f]{12})( |$)`: two digit groups joined by one dot, a slash, exactly 12 lowercase hex characters, then one space or the end of the line. A text that begins with `#iml/` but does not match has a bad shape: E300; so `#iml/3/…`, upper-case hex, a hex run of another length, and a chain glued to the header without a space are E300. A matched header whose version is not `0.3` is E502, a `0.2` header included: the 0.2 surface is read only on request (`--version 0.2`, §11), and a 0.2 decoder given a 0.3 header reports E502 the same way. A matched header whose 12 characters are not the loaded registry's is E502. The shape is judged before the version and the digest, and the version before the form: `#iml/0.2/` followed by a well-formed document is E502, not E300. Two spaces after the header match the pattern at the first space; the chain then starts with a space, which is a stray character, E300. A header alone, with no line after it, is E300 (a document without a chain).

Compile always writes the header from the loaded registry: `compile` writes a message, `compile_document` writes a document with no final newline (the command line adds one).

::CLAUSE{HEADER|conf:confirmed|scope:iml-0.3}
T:header=#iml/0.3/+12_lowercase_hex
T:hex=the_first_12_characters_of_the_registry_digest|same_as_0.2
T:message=header+one_space+one_chain_on_one_line
T:document=header_alone_on_the_first_line+one_chain_per_line|at_least_one_chain|decompiles_to_one_I-Lang_line_per_chain_in_order
T:form_decided_by_the_first_line|one_final_line_terminator_accepted
T:read_order=no_#iml/_prefix⇒E502|prefix_without_the_shape⇒E300|shape_with_another_version⇒E502|shape_with_another_digest⇒E502
T:compile_always_writes_the_header_from_the_loaded_registry
A:no_header|version_other_than_0.3|0.2_header|digest_prefix_mismatch|second_header_in_a_document⇒E502
A:header_present_with_a_bad_shape|blank_line|trailing_space|header_without_a_chain|second_line_after_a_message⇒E300

---

## 4. OUT and aliases

One byte form per meaning. Every Greek alias in I-Lang input means its verb and is encoded as that verb's root: with the hand-derived codes of §1.5, `Σ` compiles to `MR`, `φ` to `FL`, `Π` to `BT`. Decompile prints the verb by its canon name, never by an alias, with one exception.

OUT is the one verb encoded by a mark instead of a root: `$`, the chain terminator. `$` may carry modifiers (`$fm=json`) and may appear only as the last op (E502 otherwise). `OUT` has no two-character root; `OT` after a space is E304. In I-Lang input `[OUT]` and `[Ω]` are two spellings of the same operation; both compile to `$`, and decompile prints `[Ω]` (§5). The 0.2 surface wrote OUT as `Ω`; on the 0.3 surface `Ω` at the start of an op is a stray character (E300), and inside a value it is content (§2.2).

The `op` production gives `$` no target slot. An I-Lang `[OUT:@X]` or `[Ω:@X]` is outside the subset (E502), and `$@` is E300.

::CLAUSE{OUT-ALIAS|conf:confirmed|scope:iml-0.3}
T:one_byte_form_per_meaning
T:greek_alias_in_input_means_its_verb|encoded_as_that_verb_root
T:OUT_is_the_one_verb_encoded_by_a_mark|$=the_chain_terminator|was_Ω_in_0.2
T:$_may_carry_modifiers|no_target_slot|only_as_the_last_op
T:decompile_prints_OUT_in_the_Ω_form
A:two_character_root_for_OUT⇒E304
A:$_before_the_last_op⇒E502
A:OUT_with_a_target_in_input⇒E502
A:Ω_at_the_start_of_an_op_on_the_0.3_surface⇒E300

---

## 5. Canonical I-Lang print (decompile output)

### 5.1 Print

Unchanged since 0.2. The form is `[VERB:@TARGET|k=v,k=v]=>[...]`. Verbs print by canon name. OUT prints as `[Ω]`, with modifiers `[Ω|k=v]`. Targets print `@NAME`. An operation without a target omits `:@TARGET`; an operation without modifiers omits `|` and the list.

A value prints bare when its content is not empty, contains no whitespace, none of `,` `|` `]` `[` `"` `\`, and does not start with `@`. `=` and `>` are content: `whr=score>80` (the example of draft 0.1, which the canon validator accepts) and `whr=lvl:fatal` (canon §10.1) print bare. `$` is content in I-Lang: `fmt=$x` prints bare. Otherwise a value prints quoted with the §2.4 escapes. An entity reference prints `@NAME`. No whitespace anywhere. A document prints one line per chain, in order.

### 5.2 Accepted input

`parse_L2` reads a chain in the subset of §0. It accepts the canonical form and three spellings of it: a Greek alias for a verb, `[OUT]` for `[Ω]`, and quotes around a value whose content could print bare. A bare value in I-Lang input runs to the next `,`, `|` or `]`; a `|` there is a stray character (E300, §0). Inside a bare value `[`, `"` and `\` are E303 and whitespace is E300; `=` and `>` are content. Content with `,` `|` `]` `[` `"` `\` or whitespace is written quoted (§2.4: quoted strings carry spaces or special characters). A bare value beginning with `@` is an entity reference (§2.4). Whitespace outside a quoted value is a stray character (E300); so are whitespace before or after the chain, and a dangling `=>` at the end of the chain.

::CLAUSE{PRINT|conf:confirmed|scope:iml-0.3}
T:unchanged_since_0.2
T:verb_by_canon_name|OUT_as_Ω|target_as_@NAME|modifiers_key=value_comma_separated|ops_joined_by_the_pipe_operator
T:value_bare_iff_not_empty|no_whitespace|none_of_comma_pipe_brackets_quote_backslash|not_starting_with_@|equals_greater_than_and_dollar_are_content|else_quoted_with_§2.4_escapes
T:entity_reference_prints_@NAME
T:no_whitespace_anywhere|document_prints_one_line_per_chain
T:parse_accepts_the_canonical_form_plus_three_spellings|alias|OUT_word|quotes_around_bare_content
A:print_reproduces_the_input_spelling⇒not_canonical
A:whitespace_outside_quotes_in_input⇒E300
A:whitespace_before_or_after_the_chain|dangling_pipe_operator⇒E300
A:bracket_quote_or_backslash_inside_a_bare_value⇒E303

---

## 6. Round-trip law

Let `parse_L2` read canon I-Lang into the AST, `print_L2` write it, `compile` be AST to IML message text, `compile_document` be a sequence of ASTs to IML document text, and `decompile` be IML text to the AST (message) or to the sequence of ASTs (document).

- L1 (AST fidelity): for every I-Lang chain x in the subset, `decompile(compile(parse_L2(x))) == parse_L2(x)`. AST equality compares the verb, the target (by name), the modifier keys in order, and the value, kind-normalised: `bare` and `quoted` compare by content, `entity` by name, `code` by code.
- L2 (canonical text): `print_L2` is idempotent, `print_L2(parse_L2(print_L2(a))) == print_L2(a)`, and `compile(decompile(m)) == m` for every IML message m that the codec itself produced.
- L3 (original bytes): not promised. Quotes, alias spelling (`Σ` against `MERGE`), and `[OUT]` against `[Ω]` are spelling; so is the surface: a chain read from its 0.2 record and one read from its 0.3 text are the same AST.
- Document law: for every sequence of chains a1..an in the subset, `decompile(compile_document([a1..an])) == [a1..an]`, and `compile_document(decompile(d)) == d` for every document d that the codec itself produced. A document's chains are independent: the header is shared and nothing else.

Tests:

- A golden corpus, hand-written, of at least 60 chains covering every verb at least once, every key at least once, every registered entity, custom entities, quoted values with each escape, numbers like `007`, booleans, entity references in values, OUT with and without modifiers, and chains of length 1 to 8. The sources are `corpus/golden/*.ilang`; the expected 0.3 text is `corpus/golden-0.3/*.iml`, and `corpus/golden/*.iml` is the 0.2 record, read with the 0.2 surface. Three chains spell one value differently on the two surfaces (a string starting with `@` is quoted only in 0.3; the values `Φ` and `→arrow` are quoted only in 0.2), and a fourth carries `Ω` as bare content on both, which a character map must not touch; for every other chain the 0.3 text is the 0.2 text under the map `Φ` to `@`, `Ω` to `$`, `→` to the space, and the tests check both facts.
- A malformed corpus of at least 40 inputs with expected error codes, each decompile case naming its surface. The 0.3 cases include a version mismatch in both directions, a blank line in a document, a second header, `$` at the start of a value, a trailing space, and `Φ`, `Ω`, `→` in syntax positions of a 0.3 message.
- A generator with `random.Random(20260918)` producing 10,000 chains over the registry, run on both surfaces, and the document law on those chains in batches of 100. The generator is not the oracle. The oracle for L2 legality is the vendored canon validator, run on the printed I-Lang of a 500-sample.

::CLAUSE{ROUNDTRIP|conf:confirmed|scope:iml-0.3}
T:L1=decompile(compile(parse_L2(x)))==parse_L2(x)|for_every_chain_in_the_subset
T:AST_equality=verb+target_name+modifier_keys_in_order+value_kind_normalised
T:L2=print_L2_idempotent|compile(decompile(m))==m_for_every_codec_produced_m
T:L3_not_promised|quotes+alias_spelling+OUT_against_Ω+the_surface_are_spelling
T:document_law=decompile(compile_document(chains))==chains|compile_document(decompile(d))==d|chains_independent_under_one_header
T:tests=golden_corpus_60_or_more_on_both_surfaces|malformed_corpus_40_or_more_with_the_0.3_list|generator_seed_20260918_10000_chains_both_surfaces|document_law_in_batches_of_100
T:generator_is_not_the_oracle|oracle=vendored_canon_validator_on_printed_I-Lang|500_sample
A:round_trip_claimed_outside_the_subset⇒unsupported_claim
A:original_bytes_claimed⇒contradicts_L3

---

## 7. Errors

The codec fails closed; the first error stops it. Codes reuse §9 of the canon. The codec raises these six codes and no other; 0.3 adds no code.

| Code | Canon name | Raised when |
|------|------------|-------------|
| E300 | Syntax Error | bad header shape (§3); unterminated quote; bad escape; raw control character inside a quoted value; empty value; stray character, a `|` between modifiers, a tab, or `Φ`, `Ω`, `→` in a syntax position included; missing `=`; whitespace in a bare value; whitespace before or after an I-Lang chain; a dangling `=>`; two spaces between ops; a trailing space; a blank line in a document; a header with no chain after it; a second line after a message line |
| E304 | Unknown Verb | unknown root (decompile) or unknown verb (compile), `OT` included |
| E302 | Invalid Modifier | unknown key code (decompile) or unknown key (compile) |
| E200 | Entity Not Found | unknown registered mark; an entity name that does not match `[A-Z][A-Z0-9_]*`; a registered entity in the custom form |
| E303 | Invalid Value | bare value containing `,` `|` `]` `[` `"` `\` (§5.1); a value starting with `$` (§2.2); `~code` not in the key's table (always, in 0.3) |
| E502 | Unsupported Format | no header; wrong version, a 0.2 header included; digest mismatch; a second header in a document; declaration or other construct outside the subset; OUT not last; `[Π:VERB]` form; more than one chain on one I-Lang line |

Reading of the table. A raw control character (U+0000 to U+001F, U+007F, U+0085, U+2028, U+2029) is E300 wherever it appears in a value, bare or quoted; a newline is only ever the escape `\n` inside quotes. In I-Lang input a bare value ends at `,`, `|` or `]`, so of the E303 set only `[`, `"` and `\` can stand inside one; a `|` that follows a value is a stray character, E300 (§0). In IML a bare value ends at `,` or a space, and `"` or `\` inside it is E303, any other whitespace inside it E300 (§2.1). A value that starts with `~` or `@` is not a bare value: it is read as a code or as an entity reference and judged by that rule (E303 for a code outside its table, E200 or E300 for a malformed reference); a value that starts with `"` is a quoted value; a value that starts with `$` is E303. A character that no production admits at its position, outside a value, is a stray character, E300; so is an op that starts with neither `$` nor two characters of `[A-Z0-9]`. Two characters of `[A-Z0-9]` that are not a root in the registry are E304. On the header and the two forms, §3 gives the split between E502 and E300.

Error objects carry `code`, `message`, `offset` (0-based character index into the whole input text, a document included) and, for compile, the operation index; inside a document the operation index counts from the start of its line, and a compile error names the chain.

::CLAUSE{ERRORS|conf:confirmed|scope:iml-0.3}
T:fail_closed|the_first_error_stops_the_codec
T:codes=SPEC.md_§9|E300+E304+E302+E200+E303+E502|no_other_code|0.3_adds_none
T:error_object=code+message+offset_0_based_char_index_into_the_whole_text|compile_adds_the_operation_index
T:new_E300_cases=two_spaces|trailing_space|blank_line|header_without_chain|second_line_after_a_message|0.2_marks_in_syntax_positions
T:new_E303_case=value_starting_with_dollar
T:new_E502_cases=0.2_header|second_header_in_a_document
A:unknown_root_key_or_mark_guessed_or_skipped⇒violates_fail_closed
A:error_code_registered_by_IML⇒contradicts_registers_nothing

---

## 8. Measurement

`tools/measure.py` writes `measurements/0.3-YYYY-MM-DD.md`. For each golden chain it records bytes (UTF-8), characters, and tokens under `cl100k_base` and `o200k_base` (tiktoken 0.14.0, offline cache), for the I-Lang canonical print (§5), the IML 0.3 message (header included), the chain line alone as it stands in a document, a JSON form `{"c":[{"v":"READ","t":"@SRC","m":{"path":"x"}}]}` (compact with no spaces, the one JSON mapping used as a baseline and stated as such), and, as the record, the IML 0.2 message of the same chain. Once for the whole corpus it records the IML 0.3 document, the header and the 72 chain lines measured as one text. It also records the cost of `RULE-SHEET.md` in the same units, with the 0.2 sheet's figures copied from the 0.2 report as the record. The report gives totals and per-form means.

No figure carries a claim; the table is the table. The report states the tokenizer scope: named encodings, not any vendor's billing. If tiktoken is missing, the tool writes bytes and characters and says that tokens were not measured (§11).

::CLAUSE{MEASURE|conf:confirmed|scope:iml-0.3}
T:tools/measure.py_writes_measurements/0.3-YYYY-MM-DD.md
T:per_golden_chain=bytes_utf8+characters+tokens_cl100k_base+tokens_o200k_base|tiktoken_0.14.0_offline_cache
T:forms=I-Lang_canonical_print|IML_0.3_message|IML_0.3_chain_line|compact_JSON_baseline_stated_as_the_one_mapping_used|IML_0.2_message_as_record
T:once_per_corpus=IML_0.3_document_measured_as_one_text
T:rule_sheet_cost_in_the_same_units|0.2_sheet_figures_copied_as_record|totals+per_form_means
T:tokenizer_scope=named_encodings|not_a_vendor_billing
A:figure_called_a_saving⇒violates_the_ROADMAP_gate
A:figure_published_without_corpus_tokenizer_and_both_baselines⇒unsupported_claim

---

## 9. Outside 0.3

Not in 0.3. The constructs listed at the end of §0.2 are outside the subset and a 0.3 codec reports them as E502. 0.3 widens nothing: it changes how a chain is spelled, not what a chain may say.

Deferred to 0.4 (ROADMAP.md): conditionals, loops, parallel groups and DAGs; error handling and retry; MCP and A2A adapters. Before any of these enters a draft, three definitions must exist: the loop body and its termination; the source of truth for a condition (I-Lang `EVAL` returns a map, not a boolean); and the meaning of `Ω` inside a branch.

Belongs to the envelope, not to IML: authority, signing, encryption, effect enforcement and version negotiation. Where a signature is used it covers the detached raw bytes of the message or of the document. A receiver treats an IML message as untrusted input under I-Lang v4.0 until the envelope says otherwise.

Not planned: serialising OpenAPI schemas; variable-length verb coding; outreach to transport or platform vendors.

Later versions. A value-code table may be filled in a later version (§1.3), and `$` at the start of a value is held free for a later use (§2.2). A message written under 0.3 keeps its meaning, because a literal is never marked and a code is always marked. The 0.2 surface is read only, behind an explicit request; it is not written by a 0.3 codec, and no further change to it is planned.

Claims. ROADMAP.md gates the efficiency claim: on at least 1000 real instruction chains and at least three tokenizers, total IML tokens, rule sheet and retries included, below both I-Lang v4 text and JSON with schema. Until that gate is met nothing of the kind is claimed anywhere; §0.1 is a record of what was measured, not a claim. The 1.0 gate is two independent codecs passing each other's corpora, a public conformance corpus, and a core frozen for 90 days with no blocking defect.

::CLAUSE{OUTSIDE-0.3|conf:confirmed|scope:iml-0.3}
T:0.3_widens_nothing|spelling_changed_not_what_a_chain_may_say
T:deferred_to_0.4=conditionals+loops+parallel_groups+DAGs|error_handling_and_retry|MCP_and_A2A_adapters
T:before_a_0.4_draft=loop_body_and_termination|source_of_truth_for_a_condition|meaning_of_Ω_inside_a_branch
T:envelope=authority+signing+encryption+effect_enforcement+version_negotiation|signature_covers_the_detached_raw_bytes
T:receiver_treats_an_IML_message_as_untrusted_input_under_v4.0_until_the_envelope_says_otherwise
T:not_planned=OpenAPI_schema_serialisation|variable_length_verb_coding|vendor_outreach
T:dollar_at_value_start_held_free|0.2_surface_read_only_and_frozen
T:efficiency_claim_gated_by_ROADMAP|nothing_claimed_until_the_gate_is_met
A:0.4_construct_read_by_a_0.3_codec⇒E502
A:security_property_attributed_to_IML⇒belongs_to_the_envelope

---

## 10. Worked examples

All codes below are hand-derived (§1.5); the registry file is authoritative for every code. `88d05d0839c1` is the first 12 hex characters of the registry digest at the pin; the registry file is authoritative and a rebuilt registry must reproduce it.

### 10.1 The README chain

I-Lang:

```
[READ:@GH|path=readme.md]=>[XLAT|lng=zh]=>[FMT|fmt=md]=>[Ω]
```

IML 0.3 message:

```
#iml/0.3/88d05d0839c1 RD@GHpt=readme.md XLln=zh FMfm=md $
```

Reading the line after the header and its space: `RD` is a root, READ; `@` opens a target, `GH` is a mark, `@GH`; `p` opens the modifier list, `pt` is a key, `path`, `=`, then a value running to the space, `readme.md`, bare; the space opens the next op; `XL` is XLAT with no target; `ln=zh` is `lng=zh`; a space; `FM` is FMT; `fm=md` is `fmt=md`; a space; `$` is OUT with no modifiers, and the line ends. Decompile prints the I-Lang line above unchanged. The 0.2 record of the same chain is `#iml/0.2/88d05d0839c1 RDΦGHpt=readme.md→XLln=zh→FMfm=md→Ω`.

### 10.2 Custom entity, entity reference, quoted value, modifiers on OUT

I-Lang:

```
[READ:@MYDATA|src=@PREV,whr="a, b"]=>[Ω|fmt=json]
```

IML 0.3 message:

```
#iml/0.3/88d05d0839c1 RD@{MYDATA}sr=@PR,wh="a, b" $fm=json
```

`@MYDATA` is custom, so it is written `@{MYDATA}`. `@PREV` in value position is an entity reference, kind `entity`, written `@PR`. The content `a, b` contains `,` and a space, so it is quoted in both forms; the space inside the quotes does not separate ops. `$` carries `fm=json` and is the last op.

### 10.3 Alias in input

I-Lang input, from the canon §10.1:

```
[φ:@LOG|whr=lvl:fatal]=>[CNT]=>[Ω]
```

IML 0.3 message:

```
#iml/0.3/88d05d0839c1 FL@LGwh=lvl:fatal CT $
```

`φ` means FILT and is encoded as FILT's root. `lvl:fatal` contains no special character and stays bare. `LG` here is the mark of `@LOG`; at the start of an op the same two characters would be the root of the verb LOG, and the `@` prefix keeps the two apart. Decompile prints `[FILT:@LOG|whr=lvl:fatal]=>[CNT]=>[Ω]`: the alias is spelling (§6, L3) and the canonical print uses the verb name.

### 10.4 The three chains as one document

```
#iml/0.3/88d05d0839c1
RD@GHpt=readme.md XLln=zh FMfm=md $
RD@{MYDATA}sr=@PR,wh="a, b" $fm=json
FL@LGwh=lvl:fatal CT $
```

The first line is the header alone, so the text is a document; each following line is one chain, read as in 10.1 to 10.3. Decompile prints three I-Lang lines, in this order:

```
[READ:@GH|path=readme.md]=>[XLAT|lng=zh]=>[FMT|fmt=md]=>[Ω]
[READ:@MYDATA|src=@PREV,whr="a, b"]=>[Ω|fmt=json]
[FILT:@LOG|whr=lvl:fatal]=>[CNT]=>[Ω]
```

### 10.5 Values that the surface change respells

I-Lang `[FMT|fmt="@x",len=$y,sty=a$b,ton=a→b]` is `#iml/0.3/88d05d0839c1 FMfm="@x",le="$y",st=a$b,tn=a→b`: a string beginning with `@` or `$` is quoted, `$` after the first character is content, and `→` is content. On the 0.2 surface the same chain was `FMfm=@x,le=$y,st=a$b,tn="a→b"`. Both decompile to the same AST and print the same I-Lang line, `[FMT|fmt="@x",len=$y,sty=a$b,ton=a→b]`.

::CLAUSE{EXAMPLE|conf:confirmed|scope:iml-0.3}
T:codes_hand_derived_by_§1.3|registry_file_authoritative
T:digest_prefix_at_the_pin=88d05d0839c1|registry_file_authoritative
T:decompile_prints_the_I-Lang_line_unchanged|alias_input_prints_by_verb_name|document_prints_one_line_per_chain
T:respelled_values=string_starting_with_at_or_dollar_quoted|dollar_and_arrow_inside_are_content
A:digest_prefix_copied_from_this_text⇒E502_against_the_real_registry

---

## 11. Repository layout (non-normative)

The executable form of §1, §6 and §7 lives beside this document:

- `SPEC-IML-0.3.md` (this text), `SPEC-IML-0.2.md` (the record of 0.2, unchanged) and `RULE-SHEET.md` (the 0.3 rule sheet, at most 1,800 tokens under `cl100k_base`)
- `canon/`: vendored `SPEC.md`, `archive/SPEC-v5.0-PATCH-2.md`, `SPEC-v4.1-MEDIA-PROFILE.md`, `ilang_grammar_validator.py` at the pin, and `canon/PIN`
- `tools/derive_registry.py` and `registry/iml-registry-0.2.json` (unchanged)
- `iml/__init__.py`, `iml/registry.py`, `iml/l2.py`, `iml/codec.py`, `iml/errors.py`, `iml/__main__.py` (CLI: `compile [--document]`, `decompile [--version 0.2]`, `roundtrip`, `check-registry`); `compile` writes 0.3 only, `decompile` decides the form by the first line and reads the 0.2 surface only behind `--version 0.2`
- `corpus/golden/*.ilang` (the sources) with `corpus/golden-0.3/*.iml` (expected, 0.3) and `corpus/golden/*.iml` (the 0.2 record), and `corpus/malformed/cases.json` (each decompile case names its surface)
- `tests/test_registry.py`, `tests/test_codec.py`, `tests/test_roundtrip.py`, `tests/test_malformed.py` (stdlib unittest, `python -m unittest discover -s tests`)
- `tools/measure.py` and `measurements/0.3-2026-09-18.md` (`measurements/0.2-2026-09-18.md` stays as the record)
- `.github/workflows/test.yml` (python 3.12: derive check and unittest)
- `.gitattributes` (LF for every text file)

Python 3.10 or later. Standard library only for the codec and the tests; tiktoken only in `tools/measure.py`, and optional there. All files LF line ends, UTF-8, no BOM; `.gitattributes` pins LF for every text file, so a Windows clone made with `core.autocrlf=true` keeps the sha256 of `canon/` and `tools/derive_registry.py --check` passes. `LICENSE` and `drafts/` are not touched; `README.md` and `ROADMAP.md` are updated at every release.

::CLAUSE{FILES|conf:confirmed|scope:iml-0.3}
T:python_3.10_or_later|standard_library_only_for_codec_and_tests|tiktoken_only_in_tools/measure.py_and_optional
T:LF_line_ends|UTF-8|no_BOM|.gitattributes_pins_LF
T:compile_writes_0.3_only|decompile_reads_0.2_only_behind_--version_0.2
T:README_and_ROADMAP_updated_at_every_release
T:non_normative|the_registry_file_and_the_corpora_are_the_executable_form_of_§1_§6_§7
A:LICENSE_or_drafts_edited_by_0.3_work⇒out_of_scope
A:SPEC-IML-0.2.md_edited_by_0.3_work⇒the_record_is_no_longer_a_record

---

## 12. Revision history

- 0.2.0 (2026-09-18): first implemented version (`SPEC-IML-0.2.md`).
- 0.2.1 (2026-09-18): clarifications; the message form and the registry unchanged.
- 0.2.2 (2026-09-18): citation metadata; no other change.
- 0.3.0 (2026-09-18): surface change only. `Φ` to `@`, `Ω` to `$`, `→` to one space; the header `#iml/0.3/`; the document form with one header for many chains; `$` at the start of a value reserved (E303); the 0.2 surface read only behind `--version 0.2`. The registry (digest 88d05d0839c1…), the AST, the value rules, the canonical print, the round-trip law and the six error codes are unchanged; §0.1 records the measurement before and after.
- 0.3.1 (2026-09-18): U+0085 added to the control characters (the canon validator reads it as a line break); the `bare` production states that whitespace means any Unicode whitespace; the grammar shows the optional final line terminator that §3 already accepted; the per-mark token cost in §0 is the measured figure; the rule sheet names the registered-name-in-custom-form, empty `~` and `$@` cases. No change to the message form, the registry or the error codes.

::CLAUSE{REVISIONS|conf:confirmed|scope:iml-0.3}
T:0.3.0=surface_change_only|marks_ascii|header_document_level|dollar_at_value_start_reserved|0.2_surface_read_only
T:0.3.1=fix_release|NEL_control|bare_unicode_whitespace|grammar_final_NL|token_cost_measured|rule_sheet_gaps|cli_edge_cases
T:unchanged=registry_digest_88d05d0839c1|AST|value_rules|canonical_print|round_trip_law|error_codes
A:revision_changes_the_registry_or_the_AST⇒a_new_version_not_a_revision
