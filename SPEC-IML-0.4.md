# IML (I-Lang Machine Layer) 0.4

::STATE{@SPEC, id:IML-0.4, revision:0.4.1, layer:machine, status:adopted, date:2026-09-18}
::STATE{@SPEC, canon:ilang-ai/ilang-spec, canon_pin:127ba56, canon_commit:127ba56f4eb1f35c2951d4aec4b7bd22831119ff, canon_version:v4.2.0}
::STATE{@SPEC, registers_nothing:true, verbs_derived:88, aliases_derived:13, keys_derived:49, entities_derived:25, value_code_tables:empty, registry_unchanged_since:0.2, digest_prefix:88d05d0839c1}
::STATE{@SPEC, supersedes:SPEC-IML-0.3.md, change:flow_within_the_canon, adds:verb_reference_on_BATC+multi_line_chains_on_compile, header:0.4, ast_change:one_field, error_codes_unchanged:true, scope_fixed_by:ROADMAP.md, subset:linear_pipelines+batch_shorthand}
::STATE{@SPEC, authors:Long_Quan_Zhu(Max/@SUN)+CC(@CLAUDE), orcid:0009-0004-4540-8082}

Purpose: IML (I-Lang Machine Layer) is a machine form of I-Lang operation chains, with fixed-width codes derived from the canon. A codec compiles a chain in the supported subset to one line of IML and decompiles that line back to the chain; a document carries many such lines under one header. This document is the specification of version 0.4. 0.4 widens the supported subset by exactly the two flow forms the canon defines for operation chains, and states what the canon does not define: the batch shorthand `[BATC:VERB]` and `[Π:VERB]` of §3.9, a verb reference in the target slot restricted to BATC, and multi-line operation chains, a line beginning with `=>` continuing the chain above it (PATCH-2 §1.7), accepted on the I-Lang side. Nothing new is registered; the registry and its digest are unchanged; the header becomes `#iml/0.4/88d05d0839c1`; the AST gains one field; the six error codes are unchanged. The registry and its derivation (§1), the value rules (§2.3 to §2.5), the treatment of OUT and of the Greek aliases (§4), the canonical I-Lang print (§5), the round-trip law (§6), the error codes (§7) and the measurement report (§8) are those of 0.3, restated here so that this text stands alone, with the 0.4 additions marked in each section; §0 gains the canon audit and the three definitions that ROADMAP.md demanded before any 0.4 draft, §2.1 gains one production, §2.6 the continuation line, §3 the 0.4 header and the acceptance of a 0.3 header. The worked examples are §10, the repository layout §11 and the revision history §12. `SPEC-IML-0.3.md` and `SPEC-IML-0.2.md` stay unchanged as the records of 0.3 and 0.2.

IML sits under I-Lang. I-Lang carries the meaning; IML is a spelling of it that a codec produces and reads. IML registers no verb, no modifier key, no entity, no declaration and no error code. Every code in an IML message is derived by a fixed algorithm from a name in the I-Lang canon at the pinned commit, and the derived table is a file in this repository. The registry file is authoritative for every code. Where a code appears in this text it is hand-derived by the algorithm of §1, and the file corrects the text, not the other way round.

What 0.4 promises is stated in §6 and tested: a chain in the subset round-trips at the AST level, on one line or inside a document, whether its I-Lang source stood on one line or on several. Nothing is promised outside the subset. No efficiency figure is claimed; §8 says how measurement is reported. Draft 0.1 is archived under `drafts/` and is not a specification. ROADMAP.md fixes the scope of 0.4 and what is deferred.

Notation: the marks are `@` (U+0040), `$` (U+0024), the space (U+0020) and, new in 0.4 and in one position only, `:` (U+003A). The 0.2 marks, named where this text compares surfaces, are `Φ` (U+03A6), `Ω` (U+03A9) and `→` (U+2192). Grammar is written in EBNF; `;` starts a comment. A section number without a document name (§2.2, §3.9, §4, §5, §9) refers to the canon `SPEC.md`; PATCH-2 §1.5 and §1.7 refer to `canon/archive/SPEC-v5.0-PATCH-2.md`; "upstream `SPEC-v4.0-FINAL.md`" is that file in `ilang-ai/ilang-spec` at the pin, which is not vendored under `canon/`; v4.1 §4.4.1, §4.4.2 and §5.4 refer to `SPEC-v4.1-MEDIA-PROFILE.md`. "The validator" is `canon/ilang_grammar_validator.py` at the pin, run as `--lint` on one file; its messages are quoted as it prints them.

---

## 0. Scope

### 0.1 Why 0.4

ROADMAP.md deferred to 0.4 conditionals, loops, parallel groups and DAGs, error handling and retry, and MCP and A2A adapters, and demanded three definitions before any 0.4 draft: the loop body and its termination, the source of truth for a condition, and the meaning of Ω inside a branch. 0.4 was built by first asking the canon what it defines at the level of an operation chain. The answer, checked against `canon/SPEC.md` and the pinned validator on 2026-09-18 and recorded in §0.3, is that the canon defines two flow forms for operation chains and no other: the batch shorthand of §3.9 and the chain continuation of PATCH-2 §1.7. It defines no conditional, no parallel group, no DAG, and no error handling or retry at chain level. Where those words occur in the canon they name declarations (`when:` in §2.3, `::RULE{condition⇒action}` in §6.5, and the v4.0 execution-layer declaration `::FALLBACK`), SOUL-layer narrative notation (§7.5), or the v4.0 PROTOCOL header (`fallback=`, `degrade=`), which is the envelope and stands in upstream `SPEC-v4.0-FINAL.md`, not under `canon/`.

So 0.4 widens the subset by exactly those two forms and writes the three definitions from canon text (§0.4); two of the three conclude that the construct does not exist at chain level. IML defines no construct of its own: a form enters IML when the canon has defined it as operation-chain syntax, and not before. Adapters are not codec work and are no part of this specification.

What 0.4 changes: the header reads `#iml/0.4/`, the `op` production admits a verb reference after the root of BATC, the AST's `Op` gains the field `verbref`, the I-Lang readers join continuation lines before parsing, and a 0.3 header is read without a flag. What 0.4 leaves as it is: the registry and its digest `88d05d0839c1`, the value rules, the canonical print, the round-trip law, the six error codes, and every 0.3 message and document, whose 0.4 text is the 0.3 text with one digit of the header changed. On the 72-chain golden corpus that digit changes no figure of the 0.3 measurement: bytes and characters are the same, and both encodings tokenise `#iml/0.3/88d05d0839c1` and `#iml/0.4/88d05d0839c1` to the same count (§8).

### 0.2 The subset

One IML chain carries one I-Lang operation chain on one line of IML. On the I-Lang side the chain may be written on one line or on several: a line whose first non-blank characters are `=>` continues the chain above it (§2.6). The IML line, the AST and the canonical print are those of the one-line chain. The chain is a sequence of operations `[VERB(:TARGET)?(|mods)?]` joined by the pipe operator `=>`, with at least one operation. A message carries one chain; a document carries one or more chains, one per line, under one header (§3).

The supported subset, 0.3 plus the verb reference:

- Verbs: the 88 canon verbs of §3 and the 13 Greek aliases of §3.10. An alias means its verb.
- Target: a registered entity `@NAME` (25 registered: 8 core, 6 external, 8 role, 3 media) or a custom entity whose name matches `[A-Z][A-Z0-9_]*` (§5.3).
- Verb reference, new in 0.4: on BATC, also reached through its alias Π, and on BATC only, the target slot may hold a verb instead of an entity: `[BATC:READ]`, `[Π:READ]`, `[BATC:Σ]`. §3.9: "in BATC/Π only, the token after `:` is a verb reference, not an entity. This is the sole exception to the standard `[VERB:@ENTITY]` pattern." The reference is a registered verb or alias; an alias collapses to its verb (§4). OUT or Ω as the reference is E502 (§4). `[BATC:@SRC]` stays an entity target, as on every verb. `[BATC:READ|op=FMT]` is accepted as written: the codec does not judge the conflict between the reference and the `op` modifier, and neither does the validator. On every verb other than BATC a target that does not start with `@` is E300, with the validator's wording (§7).
- Modifiers: the 29 core keys of §4 and the 20 media profile keys of v4.1 §4.4.2, written `key=value` and separated by commas (§4: "Multiple modifiers separated by commas"). `|` separates the verb, the target or the verb reference from the modifier list and has no other place in an operation. The dialect that separates modifiers with `|` is not accepted: a bare value ends at `|`, and a `|` that follows a value is a stray character (§7, E300). The codec checks that a key is registered. It does not check the media gating of v4.1 §4.4.1: whether a profile key is in force for the target is I-Lang semantics, reported by the canon validator, not by the codec. The key `op` (§4: "string", "Operation reference (for BATC)") stays a plain string value and is not validated against the verb table, as in the validator.
- Values: the forms of §2.4: barewords, quoted strings with the escapes `\"` `\\` `\n`, numbers, booleans, and entity references `@NAME`.
- OUT, alias `Ω`, may appear only as the last operation of the chain. It is not required.

Not supported, reported as E502: declarations (`::`); the temporal notation of §7.5 (`T[n]`, `T[a]→T[b]`, `PARALLEL{a, b}`); comments and anything after the chain (when a space stands between the chain and the text, the space is a stray character and E300 is reported first, §5.2); more than one chain on one I-Lang line, a space and a second `[` after a chain, with the message "a second operation chain on the line: IML carries one chain per line"; OUT with a target; OUT before the last operation; OUT or Ω as a verb reference. The 0.3 list also named `||`: the canon has no `||` anywhere (`SPEC.md`, the v4.1 profile and PATCH-2 were searched at the pin), so 0.4 drops it from the list; a `|` in a syntax position is a stray character and inside a value it ends a bare value, judged by §2 and §5, and no construct is named by it. Conditionals, parallel groups, DAGs, error handling and retry are not operation-chain syntax in the canon (§0.3), so there is no construct for a codec to support or to refuse; a chain that spells one of them in some other notation fails on that notation under the rules above.

### 0.3 Canon audit

The rows were checked on 2026-09-18 against the canon files vendored under `canon/`, that is `SPEC.md` and, for the chain continuation and the declaration registry, PATCH-2, and against the pinned validator, one probe per file, `--lint`. One row rests in part on a file that is not vendored: the row on error handling cites the v4.0 PROTOCOL header, which stands in upstream `SPEC-v4.0-FINAL.md` at the pin and not under `canon/`. The validator's answers are quoted as printed; "0 errors" means `0 error(s), 0 warning(s)`.

| Construct | Canon text | Validator answer | IML 0.3 | IML 0.4 |
|---|---|---|---|---|
| `=>` sequence | §2.2, the pipe operator | linted | supported | unchanged |
| `[BATC\|op=READ,src=@LOCAL]` | §3.9 batch syntax; key `op` in §4: "string", "Operation reference (for BATC)" | 0 errors; `[BATC\|op=REED]` 0 errors and `[BATC\|op=Σ]` 0 errors: the value is not validated | supported; `op` is a bare string value | unchanged: `op` stays a plain string value, not validated, as in the validator |
| `[Π:READ]`, `[BATC:READ]` | §3.9: "in BATC/Π only, the token after `:` is a verb reference, not an entity. This is the sole exception to the standard `[VERB:@ENTITY]` pattern" | 0 errors; `[BATC:REED]` E304 "BATC verb reference `REED` is not a registered verb or alias"; `[BATC:read]` E304 with `read` in the same wording; `[Π:Σ]` 0 errors (an alias is accepted); `[Π:Ω]` 0 errors; `[Π:@SRC]` 0 errors (an entity target on BATC is accepted); `[BATC:READ\|op=FMT]` 0 errors (the conflict is not checked) | E502 | supported: a verb reference in the target slot on BATC only; unknown or lower-case E304; an alias collapses to its verb; OUT or Ω as the reference E502; `[BATC:@SRC]` stays an entity target; `[BATC:READ\|op=FMT]` accepted as written, the codec does not judge the conflict |
| `[LOOP:READ]` | none | E300 "operation target `READ` is not an @ENTITY (v3.0 §2.2; BATC/Π excepted)" | E300 | E300, same wording |
| multi-line chain, `=>` on the next line | PATCH-2 §1.7, `chain_continuation`: "an_operation_chain_MAY_wrap", "continuation_lines_are_indented_and_begin_with_`=>`", "each_continuation_extends_the_chain_of_the_nearest_preceding_operation_line"; the `E:` line of that production is the canon's one example of a wrapped chain | 0 errors on a three-line chain; in a linted region (raw mode, or a fence opened by an operation line) an orphan `=>` line is E300 "orphan `=>` continuation: no preceding operation line"; as a bare line of a Markdown file the validator reads such a line as background text and does not lint it | not read: each line is one chain | supported on compile (§2.6); an orphan line is E300 with the validator's wording |
| `[LOOP\|...]`, `[WAIT\|...]`, `[CHEK\|...]`, `[EVAL]`, `[DECI]` | verb rows only (§3.3, §3.5) | plain operations | supported as plain operations | unchanged; their semantics stay with the executing model |
| two chains on one line, `[..]=>[Ω] [..]=>[Ω]` | none; the validator's mixed mode lints every bracket group on a line | both chains linted; an unknown verb in the second is E304 "unknown verb `REED` in operation chain" | E300 (the space is a stray character) | still outside: E502 "a second operation chain on the line: IML carries one chain per line"; the document form carries several chains |
| `T[1] [READ:@SRC]=>[Ω]`, `T[a]→T[b]`, `PARALLEL{a, b}` | §7.5, SOUL-layer temporal notation (narrative) | 0 errors, and an unknown verb inside is not reported: the validator reads these as opaque note lines (`RE_TEMPORAL_NOTE`) | E502 | E502; narrative notation, not chain syntax (§9) |
| conditionals in a chain | none; `when:` (§2.3, "conditional trigger") and `::RULE{condition⇒action}` (§6.5) are declaration-level | none | E502 (declarations) | none; §0.4, D2 |
| parallel groups, DAGs in a chain | none | none | none | none; a document's chains are ordered, and a dependency between chains runs through entities (§2.2, source resolution), which is semantics, not syntax |
| error handling, retry | none at chain level; `::FALLBACK` is a v4.0 execution-layer declaration (PATCH-2 §1.5 lists `::PRIOR` `::FALLBACK` under "v4.0 execution layer (8)", and the validator's `REGISTRY_V4` carries FALLBACK): declaration level, not operation-chain syntax; the v4.0 PROTOCOL header `fallback=` and `degrade=` is the envelope, and for it this row rests on upstream `SPEC-v4.0-FINAL.md` at the pin, a file not vendored under `canon/` | `::FALLBACK{v3_only⇒warn}` lints as a registered declaration, 0 errors; `[FALLBACK]` inside a chain is E304 "unknown verb `FALLBACK` in operation chain" | none; a declaration is E502 | none; a declaration is E502 |
| trailing prose, `[..]=>[FMT\|fmt=md] # note` | no comment syntax; the validator's mixed mode tolerates prose | 0 errors | E502 for text after the chain (`[..]=>[Ω]#note`); when a space stands between the chain and the text, the space is a stray character and E300 is reported first | unchanged |
| `[Ω]=>[FMT]` | §3.6, OUT "Mark final output" | 0 errors (not enforced) | E502 (OUT last) | unchanged; IML is stricter here than the validator |
| `[Ω:@OUT]` | §2.2, verb target semantics: "Output verbs (OUT): entity is the final value" | INFO only ("custom entities used without ::STATE introduction") | E502 since 0.2: OUT with a target is not represented (outside the subset; the `op` production gives OUT no target slot, §4) | unchanged; the limit is IML's own, not the canon's |

Accepted by the validator, E300 in IML. The validator lints the tokens of a line and lets pass, with 0 errors, a number of spellings that the codec refuses. Each of these was probed on 2026-09-18 against the pinned validator and against the codec:

- `[BATC:]`, an empty verb reference;
- `[BATC: READ]` and `[BATC:READ ]`, whitespace inside an operation;
- `[BATC:READ|]`, a `|` with no modifier after it;
- `[BATC:READ]=>`, a dangling `=>`;
- a continuation line with a space after its `=>`, as in `  => [Ω]`;
- a `=>` line under a line that itself ends in `=>`.

The reason is one: IML keeps one spelling per chain, admits no whitespace inside a chain, and fails closed, so a text that is not exactly a chain of the subset is E300 and nothing is repaired or guessed (§5.2, §7). One input is refused by both under different codes: an unknown alias is E305 for the validator and E304 for the codec (§7).

### 0.4 The three definitions

D1, the loop body and its termination. The canon's one loop over data is BATC (§3.9: input "list + verb ref", output "list", "Apply verb to each item in list"): the body is the referenced verb applied to each item of the input list, and termination is the end of that list. The canon states no more: that every item is visited once, that the items are visited in order, and that the output list keeps the order of the items are not stated by the canon, and IML promises none of them. §3 opens its tables with the disclaimer "The Input/Output/Side Effect columns describe typical usage, not compiler constraints. AI interprets context to determine exact behavior." Whether the other modifiers of the BATC operation apply to the batch or to each item is not said by the canon, and IML does not decide it. `LOOP` (§3.5: input "list/condition", output "list", "Repeat operation over set") has no body and no termination rule in the canon; IML carries it as a plain operation and promises nothing about termination.

D2, the source of truth for a condition. The canon has no chain-level conditional. What it has: `CHEK` (§3.5, output "bool/map", "Verify condition"), `WAIT` (§3.5, input "condition", output "bool", "Pause for condition"), `EVAL` (§3.3, output "map", "Assess against criteria"), `DECI` (§3.5, output "choice/map", "Choose between options"), and, at declaration level, `when:` (§2.3, "conditional trigger") and `::RULE{condition⇒action}` (§6.5). The canon's own statement about a condition at chain level is §4.2: "`whr` is a condition string, interpreted by the AI contextually". A condition's truth is whatever the executing model reads from that string and from those outputs; IML transports the operations and evaluates nothing. Therefore IML 0.4 defines no conditional construct; one would first need operation-chain syntax in the canon.

D3, Ω inside a branch. There are no branches. Ω marks the final output of its chain (§3.6, "Mark final output"; §2.2, "Output verbs (OUT): entity is the final value") and stands last, the 0.2 rule, kept. In a document each chain ends on its own; a document has as many outputs as chains ending in Ω, and no document-level output is defined.

::CLAUSE{SCOPE|conf:confirmed|scope:iml-0.4}
T:0.4=the_two_flow_forms_the_canon_defines|batch_shorthand_SPEC.md_§3.9|chain_continuation_PATCH-2_§1.7|nothing_else_added
T:registry+digest+value_rules+canonical_print+round_trip_law+six_error_codes_unchanged|AST_gains_one_field_verbref|header_0.4
T:one_chain=one_operation_chain_on_one_IML_line|I-Lang_source_may_wrap_with_continuation_lines|message_carries_one|document_carries_one_or_more_under_one_header
T:verbs=88_canon+13_greek_aliases|alias_means_its_verb
T:target=registered_entity_25|or_custom_entity_name_upper_first_then_upper_digit_underscore
T:verb_reference=verb_in_the_target_slot|on_BATC_only|registered_verb_or_alias|alias_collapses_to_its_verb
T:op_modifier_stays_a_plain_string_value|not_validated_against_the_verb_table|as_the_validator
T:modifiers=29_core+20_media_profile|key=value|comma_separated|pipe_only_before_the_modifier_list
T:values=SPEC.md_§2.4|bareword|quoted_with_escapes|number|boolean|entity_reference
T:OUT_or_Ω_only_as_the_last_operation|not_required
T:canon_audit_checked_2026-09-18|validator_answers_quoted_as_printed|error_handling_row_rests_in_part_on_upstream_SPEC-v4.0-FINAL.md_not_vendored
T:FALLBACK=v4.0_execution_layer_declaration|declaration_level|not_operation_chain_syntax
T:OUT_target_has_a_canon_meaning_SPEC.md_§2.2|not_represented_in_IML_since_0.2|a_limit_of_IML_not_of_the_canon
T:validator_accepts_and_IML_refuses_with_E300=empty_verb_reference|whitespace_inside_an_operation|pipe_without_a_modifier|dangling_pipe_operator|space_after_the_pipe_operator_of_a_continuation_line|continuation_under_a_line_ending_in_the_pipe_operator
T:D1=BATC_is_the_one_loop_over_data|body=referenced_verb_per_item|termination=end_of_the_list|visit_once+item_order+output_order_not_stated_by_the_canon_and_not_promised|LOOP_carried_as_a_plain_operation_with_no_termination_promise
T:D1_disclaimer_SPEC.md_§3=columns_describe_typical_usage_not_compiler_constraints
T:D2=no_chain_level_conditional_in_the_canon|whr_is_a_condition_string_interpreted_by_the_AI_contextually_SPEC.md_§4.2|truth_read_by_the_executing_model_from_CHEK_WAIT_EVAL_DECI|IML_evaluates_nothing
T:D3=no_branches|Ω_marks_the_final_output_of_its_chain_and_stands_last|no_document_level_output
T:double_pipe_dropped_from_the_excluded_list|the_canon_has_no_such_token
A:verb_reference_on_a_verb_other_than_BATC⇒E300
A:OUT_or_Ω_as_a_verb_reference⇒E502
A:declaration|temporal_notation|comment|second_chain_on_one_line|trailing_text|OUT_with_a_target|OUT_before_the_last_operation⇒E502
A:pipe_between_modifiers⇒E300
A:conditional|parallel_group|DAG|error_handling|retry_defined_by_IML_before_the_canon_defines_chain_syntax⇒contradicts_registers_nothing

---

## 1. Registry

The registry of 0.4 is the registry of 0.2, unchanged: the same file, the same derivation, the same digest. 0.4 derives nothing new and registers nothing of its own. A verb reference is encoded with the verb root the registry already carries; no table is added for it.

### 1.1 Sources and pin

The registry is derived from the canon at the pin by `tools/derive_registry.py` and written to `registry/iml-registry-0.2.json`. The file keeps its 0.2 name and its `iml_version` member reads `0.2`: that member names the vocabulary, which 0.4 leaves as it is; the version in a header is the surface version (§3). The sources are vendored under `canon/`, and `canon/PIN` records the commit and the sha256 of each file:

- `SPEC.md`: verbs, aliases, core modifiers, entity tiers 1 and 2, and tier 3 by reference.
- `archive/SPEC-v5.0-PATCH-2.md`: the table of the role tier (tier 3), which `SPEC.md` §5.3 incorporates by reference rather than printing. Its eight names in table order are `@SYSTEM @RUNTIME @GRADER @USER @SELF @AGENT @TASK @TOOL`, the order the validator's `TIER3` also carries. Its §1.7 is also the canon text for the chain continuation of §2.6; the derivation reads nothing from §1.7.
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
- Value codes (`~code`): one closed table per key. Every table is empty in 0.4 as in 0.2. The grammar for `~code` exists so that the message form does not change when tables are filled in a later version.

The three tables are separate. A root and a mark may coincide, since both are two characters of `[A-Z0-9]`; the `@` prefix tells a mark from a root, and a key code is lower case. A verb reference is a root in the verb table, told from a target by the `:` that opens it (§2.2). No letter begins more than 26 names in any table, so stage 4 is never reached. OUT is the only verb beginning with O and takes no root, so no root is `OT` (§4).

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

The header carries the first 12 hex characters of `digest`. At the pin the digest begins `88d05d0839c1`, the same 12 characters as in 0.2 and 0.3; the file is authoritative, and a registry rebuilt from `canon/` by `tools/derive_registry.py` reproduces it.

### 1.5 Hand-derived codes used in this document

Applying §1.3 by hand to the canon tables at the pin gives the codes below. They are used in the examples of §2, §4 and §10. They are hand-derived; the registry file is authoritative, and where the file differs, the file is right.

| Name | Table | Code | How |
|------|-------|------|-----|
| READ | verb | RD | stage 1, first consonant |
| LIST | verb | LS | stage 1 |
| XLAT | verb | XL | stage 1 |
| FMT | verb | FM | stage 1 |
| MERGE | verb | MR | stage 1 |
| FILT | verb | FL | stage 1 |
| SCAN | verb | SC | stage 1 |
| CNT | verb | CT | stage 1, second consonant; CN taken by CONV |
| CHEK | verb | CK | stage 1, second consonant; CH taken by CHNK |
| DPLO | verb | DP | stage 1 |
| LOG | verb | LG | stage 1 |
| LOOP | verb | LP | stage 1 |
| BATC | verb | BT | stage 1 |
| @GH | entity | GH | stage 1 |
| @PREV | entity | PR | stage 1 |
| @LOCAL | entity | LC | stage 1 |
| @LOG | entity | LG | stage 1; same two characters as the verb LOG, separate table |
| @SRC | entity | SR | stage 1 |
| @WORKER | entity | WR | stage 1 |
| path | key | pt | stage 1 |
| lng | key | ln | stage 1 |
| fmt | key | fm | stage 1 |
| src | key | sr | stage 1 |
| whr | key | wh | stage 1 |
| mch | key | mc | stage 1 |
| op | key | op | stage 1; `o` is kept as the first character, `p` is its first consonant |
| len | key | le | stage 2; ln taken by lng |
| srt | key | sa | stage 3; sr taken by src, st by sty |

::CLAUSE{REGISTRY|conf:confirmed|scope:iml-0.4}
T:registry_of_0.4=registry_of_0.2|same_file|same_derivation|same_digest_88d05d0839c1
T:derived_from_canon_at_127ba56_by_tools/derive_registry.py|written_to_registry/iml-registry-0.2.json
T:iml_version_member_0.2=version_of_the_vocabulary|header_carries_the_surface_version
T:iml_registers_nothing|every_code_is_derived_from_a_canon_name|verb_reference_uses_the_verb_root_already_derived
T:item_order=first_appearance_in_the_canon_tables|codes_first_come_first_served
T:verb_root=2_upper|key_code=2_lower|entity_mark=2_upper|custom_entity_has_no_mark
T:OUT_has_no_root|written_$
T:value_code_tables=one_per_key|all_empty_in_0.4
T:digest=sha256_of_the_registry_json_without_its_digest_member|header_carries_the_first_12_hex
T:registry_file_authoritative_for_every_code|codes_in_this_text_are_hand_derived
A:validator_sets_differ_from_the_parsed_sets⇒derivation_aborts
A:code_taken_from_this_text_over_the_registry_file⇒drift
A:registry_changed_by_a_0.4_release⇒a_new_digest_and_a_new_version_not_0.4

---

## 2. Lexical structure and segmentation

Every syntax character of IML 0.4 is ASCII; the content of a value is whatever UTF-8 text the I-Lang value carries, copied without change. Reserved characters: `@`, `$`, `~`, `,`, `=`, `"`, `\`, `{`, `}`, `#`, the space, every other whitespace character, and, new in 0.4, `:`. The `:` rule: `:` is syntax in exactly one position, directly after a root, where it opens a verb reference and is admitted after the root of BATC (`BT`) only. Everywhere else `:` is what it was in 0.3: inside a value it is content (`wh=lvl:fatal`, `wh=status:200`), at the first position of a bare value it is content, and in any other syntax position it is a stray character (E300).

### 2.1 Grammar

```
document  := header NL chain (NL chain)* NL?         ; the header once, then one chain per line; one final line terminator accepted
message   := header SP chain NL?                      ; the one-line form; NL is `\n` or `\r\n`
header    := "#iml/0.4/" HEX12                        ; HEX12 = 12 lowercase hex chars = registry digest prefix; decompile also reads "#iml/0.3/" (§3)
NL        := "\n"                                     ; "\r\n" is accepted as NL and printed as "\n"
SP        := " "                                      ; exactly one space
chain     := op (SP op)*
op        := (ROOT (target | verbref)? | "$") mods?   ; "$" is OUT
ROOT      := [A-Z0-9]{2}                              ; a verb root from the registry
verbref   := ":" ROOT                                 ; only after the root of BATC (`BT`); the ROOT is a registered verb root; `$` (OUT) cannot be referenced
target    := "@" (MARK | "{" NAME "}")
MARK      := [A-Z0-9]{2}                              ; a registered entity mark
NAME      := [A-Z][A-Z0-9_]*                          ; a custom entity name, same rule as I-Lang @NAME
mods      := kv ("," kv)*
kv        := KEY "=" value
KEY       := [a-z]{2}                                 ; a key code from the registry
value     := quoted | entityref | code | bare
quoted    := '"' (escape | [^"\\])* '"'               ; escape := "\" ( '"' | "\" | "n" )   (SPEC.md §2.4); no raw control character
entityref := "@" (MARK | "{" NAME "}")
code      := "~" [a-z0-9]+                            ; looked up in value_codes[key]; 0.4: always E303
bare      := [^,"\\]+  with no whitespace (any character Python str.isspace() reports, U+00A0 and U+3000 included) and no control character, and not starting with "~", "@", "$", "\""
```

The grammar of 0.4 is the grammar of 0.3 plus the `verbref` production and its place in `op`. A raw control character inside a quoted value, U+0000 to U+001F, U+007F, U+0085, U+2028 or U+2029, is E300, in IML input and in I-Lang input alike; a newline is written only as the escape `\n`. So no line terminator ever stands inside a value, and a document is split into lines before any value is read (§2.6).

### 2.2 Segmentation

Segmentation needs no lookahead: a root is always exactly two upper-case or digit characters at the start of an op; a target always starts with `@`; a verb reference always starts with `:` and is always exactly two characters long; a key is always exactly two lower-case letters followed by `=`; a value ends at the next `,` or space outside quotes, or at the end of the line.

Reading an op from its first character: `$` is OUT; otherwise the first two characters are the root. After the root, `@` opens the target, `:` opens a verb reference, a lower-case letter opens the modifier list, a space opens the next op, and the end of the line ends the chain. `:` after a root other than `BT` is E300, with a message that begins "`:` after a root other than BT". After `BT:` exactly two characters of `[A-Z0-9]` follow and are looked up as a verb root: a root not in the registry is E304; `BT:` followed by anything else, the end of the line, a space, a lower-case letter, a single character, or `$`, is E300. After a target or a verb reference the same three continuations apply: a lower-case letter opens the modifier list, a space opens the next op, the end of the line ends the chain; so a target after a verb reference (`BT:RD@SR`) and a verb reference after a target (`BT@SR:RD`) are stray characters, E300. In value position the first character decides the kind: `"` quoted, `@` entity reference, `~` code, `$` reserved (E303), anything else bare.

The `bare` production governs what a bare value may contain: any character except `,`, `"`, `\`, whitespace and control characters, with `~`, `@`, `$` and `"` excluded from the first position only. So `:`, `=`, `>`, `{`, `}`, `#`, and `~`, `@` or `$` after the first character are content inside a bare value, and so are the 0.2 marks `Φ`, `Ω` and `→`, which 0.4 does not reserve. Segmentation never reads them, because a value ends only at `,`, a space or the end of the line. `$` at the first position of a value is reserved for a later version and is E303 in 0.4; a value whose content starts with `$` is written quoted (§2.5). A bare IML value beginning with `@` is an entity reference, so a string whose content begins with `@` is written quoted (`sr="@PREV"`) and prints quoted in I-Lang too (§5).

### 2.3 Typing

Every scalar keeps its lexeme. The AST records for each value its kind, one of `bare`, `quoted`, `entity`, `code`, and its text. Numbers and booleans are barewords whose text is preserved: `007` stays `007`, `1.0` stays `1.0`, `true` stays `true`. The codec never rewrites a value; a type is a validation tag, not a transformation. A `quoted` value's content is its unescaped text. `quoted` and `bare` values with the same content are the same AST value: quoting is spelling (§6). Duplicate keys in one operation are kept in order; the codec does not check them.

The AST of 0.4 is the AST of 0.3 plus one field: an operation `Op` carries `verbref`, either none or a canon verb name (never an alias). `target` and `verbref` are mutually exclusive; both are none on every verb other than BATC, and on BATC at most one of them is set. Equality, hashing and the printed representation of an `Op` include `verbref`. Every 0.3 AST is a 0.4 AST with `verbref` none, object for object. The modifier form `[BATC|op=READ]` sets no `verbref`: its `op` is a string modifier with the value `READ`, and the two spellings are two ASTs (§5.1).

### 2.4 Entity references in value position

An entity reference in value position is a distinct kind. A bare value starting with `@` in I-Lang is always read as an entity reference; the name must match `[A-Z][A-Z0-9_]*` (E200 otherwise). A registered name compiles to `@` and its mark; a custom name compiles to `@{NAME}`; both decompile to `@NAME`. One spelling per AST holds here too (§4): a registered name written in the custom form, `@{PREV}`, is E200, in target position and in value position alike. With the hand-derived codes of §1.5:

| I-Lang | IML 0.4 | IML 0.2 (record) |
|--------|---------|------------------|
| `src=@PREV` | `sr=@PR` | `sr=ΦPR` |
| `src=@MYDATA` | `sr=@{MYDATA}` | `sr=Φ{MYDATA}` |
| `src="@PREV"` (a string) | `sr="@PREV"` | `sr=@PREV` |

### 2.5 Value spelling on compile

Compile writes an AST value by its kind. `entity`: `@` and the mark, or `@{NAME}`. `code`: `~` and the code; no I-Lang input yields this kind in 0.4, so compile never writes it. `bare` or `quoted`: bare when the content satisfies the `bare` production, otherwise quoted, with `"`, `\` and newline escaped as in §2.4. A quoted value may hold spaces and commas; the space is a separator only outside quotes. Compile never writes whitespace outside a quoted value except the one space between ops and the one after a message header.

A control character other than a newline has no spelling. §2.4 of the canon gives an escape to the newline alone, and the readers refuse every raw control character (§2.1), so `compile`, `compile_document` and `print_L2` refuse a `bare` or `quoted` value that holds one: E300, with the operation index. No reader yields such a value; only an AST built by hand can hold it. So every text the writers produce is a text the readers accept.

### 2.6 Lines

IML side, unchanged: a chain ends at the end of its line. The line terminator is `\n`; `\r\n` is accepted as a terminator and printed as `\n`. A `\r` anywhere else is a control character (E300). Since no line terminator can stand inside a value (§2.1), a document is read line by line, and each line is one chain read by the rules above. Trailing spaces on a line are E300: the space after the last op opens an op that is not there. An IML line never continues: there is no continuation line in IML, and `decompile` is unchanged.

I-Lang side, new in 0.4: the readers of I-Lang chains (`compile`, `compile --document`, `roundtrip`) join continuation lines before parsing, by one rule. PATCH-2 §1.7 registers the form: "an_operation_chain_MAY_wrap", "continuation_lines_are_indented_and_begin_with_`=>`", "each_continuation_extends_the_chain_of_the_nearest_preceding_operation_line". The rule:

- The input is split on `\n`, and one trailing `\r` per line is dropped, as before.
- A line whose first non-whitespace characters are `=>` is a continuation line: its leading whitespace is stripped and the rest is appended to the text of the current chain. The canon's one example, the `E:` line of PATCH-2 §1.7, indents a continuation line by two spaces; the reader accepts any leading whitespace, none included, as the validator does. Trailing whitespace on any line stays an error (E300).
- A continuation line is joined only when the text collected so far ends with `]` outside a quoted value, that is when the line break follows a closed operation. Quotes are scanned as `parse_L2` scans them: a quote opens a value right after `=`, a backslash inside it escapes the next character, and the next unescaped quote closes it. Otherwise the line break stood inside an operation, as in `[READ|whr="abc` followed by `  =>def"]`, or in `[READ|whr=abc` followed by `  =>x]`, and joining would make a chain that no single line spells: the chain is refused with E300, "continuation after an unterminated operation line", reported at the chain's first line with the place of the line break as its offset. The 0.4.0 codec joined such lines and compiled them (`RDwh=abc=>def`, `RDwh=abc=>x`); in a linted region the validator rejects both inputs (E300).
- A continuation line with no current chain, that is the first non-blank line of the input or the first line after a blank line, is E300 with the validator's wording, "orphan `=>` continuation: no preceding operation line". A blank line ends the current chain, and a line of whitespace only counts as a blank line, as the validator reads it.
- The joined text is parsed by `parse_L2` exactly as a one-line chain: whitespace before or after it, a dangling `=>`, and every other rule of §5.2 apply to the joined text. Nothing else changes.
- Positions: the chain's line number is the number of its first line; the error offset counts in the joined text.

The AST, the IML line and the canonical print of a chain read from several lines are identical to those of its one-line spelling, so a multi-line source is not distinguishable after compile: the layout of the source is not carried (§6, L3).

::CLAUSE{LEXICAL|conf:confirmed|scope:iml-0.4}
T:syntax_characters_ascii|value_content_utf8_copied_without_change
T:reserved=at_dollar_tilde_comma_equals_quote_backslash_braces_hash_space_whitespace+colon
T:colon_is_syntax_directly_after_a_root_only|admitted_after_BT_only|content_inside_a_value
T:grammar_0.4=grammar_0.3+verbref_production|verbref=colon+registered_verb_root
T:segmentation_without_lookahead|root_2_upper_at_op_start|target_starts_with_at|verbref_starts_with_colon_and_is_2_characters|key_2_lower_then_equals|value_ends_at_comma_or_space_outside_quotes_or_end_of_line
T:bare_production_governs_bare_content|first_position_excludes_tilde_at_dollar_quote
T:0.2_marks_phi_omega_arrow_not_reserved|content_inside_a_bare_value|stray_in_a_syntax_position
T:dollar_at_value_start_reserved_for_a_later_version|E303_in_0.4|written_quoted_on_compile
T:every_scalar_keeps_its_lexeme|kind=bare|quoted|entity|code|type_is_a_validation_tag
T:AST_0.4=AST_0.3+verbref_on_Op|target_and_verbref_mutually_exclusive|equality_includes_verbref
T:duplicate_keys_kept_in_order|not_checked_by_the_codec
T:entity_reference_in_value_position_is_its_own_kind|string_starting_with_at_written_quoted
T:compile_writes_bare_when_the_content_satisfies_bare|else_quoted_with_§2.4_escapes
T:line_terminator=LF|CRLF_accepted_and_printed_as_LF|no_terminator_inside_a_value|IML_lines_never_continue
T:continuation_line=first_non_whitespace_characters_are_the_pipe_operator|leading_whitespace_stripped|appended_to_the_current_chain|joined_only_after_a_closed_operation|blank_or_whitespace_only_line_ends_the_chain
T:closed_operation=the_text_so_far_ends_with_a_closing_bracket_outside_a_quoted_value|quotes_scanned_as_parse_L2_scans_them
T:control_character_other_than_a_newline_has_no_spelling|writers_refuse_what_the_readers_refuse
T:joined_text_parsed_as_a_one_line_chain|line_number=first_line|offset_counts_in_the_joined_text|source_layout_not_carried
A:codec_rewrites_a_value⇒violates_this_section
A:raw_control_character_inside_a_quoted_value⇒E300
A:colon_after_a_root_other_than_BT|BT_colon_without_a_two_character_root|target_after_a_verb_reference⇒E300
A:verb_reference_root_not_in_the_registry⇒E304
A:value_starting_with_tilde_or_at⇒read_as_code_or_entity_reference|judged_by_that_rule
A:trailing_space_on_a_line⇒E300
A:continuation_line_with_no_chain_above_it⇒E300
A:continuation_line_under_a_line_break_inside_an_operation⇒E300
A:control_character_other_than_a_newline_in_an_AST_value_on_compile_or_print⇒E300

---

## 3. Header and the two forms

The header is `#iml/0.4/` followed by 12 lowercase hex characters, the first 12 of the registry digest (§1.4). It stands in one of two places:

- Message: the header, one space, one chain, on one line.
- Document: the header alone on the first line; every following line is one chain. A document carries at least one chain. Decompile of a document yields one I-Lang line per chain, in order.

The form is decided by the first line: a header followed by a space is a message; a header followed by the end of the line is a document. The text may end with one line terminator (`\n` or `\r\n`), which terminates the last line and is not a blank line. In a document a blank line is E300, a trailing space on a line is E300 (§2.6), and a second header line is E502. A chain line without a header, and not inside a document, is E502 (no header). A second line after a message line is E300: a message is one line, and several chains take the document form.

Decompile reads the header in this order. A text that does not begin with `#iml/` has no header: E502. Otherwise the first line must match `^#iml/([0-9]+\.[0-9]+)/([0-9a-f]{12})( |$)`: two digit groups joined by one dot, a slash, exactly 12 lowercase hex characters, then one space or the end of the line. A text that begins with `#iml/` but does not match has a bad shape: E300; so `#iml/4/…`, upper-case hex, a hex run of another length, and a chain glued to the header without a space are E300. A matched header whose version is `0.4` is read by the default reader. So is a matched header whose version is `0.3`, without any flag: the 0.3 surface is the 0.4 surface, the digest is the same, and a 0.3 message or document contains no `:` after a root, so every 0.3 text is a 0.4 text with an older header and decompiles to the same chains as before. The converse is not checked: a 0.3 header is read with the 0.4 grammar, so `#iml/0.3/88d05d0839c1 LS@LC BT:RD $` decodes to `[LIST:@LOCAL]=>[BATC:READ]=>[Ω]`, although no 0.3 writer produced that line and a 0.3 codec answers E300 to it (`:` after a root is a stray character there). The header names what the writer wrote; it selects no grammar in the reader. A matched header whose version is `0.2` is E502 unless the 0.2 surface is requested (`--version 0.2`, §11), and a 0.2 decoder given a 0.3 or 0.4 header reports E502 the same way; the command line refuses `--version 0.3` with a message that the default reader reads 0.3. A matched header of any other version is E502. A matched header whose 12 characters are not the loaded registry's is E502. The shape is judged before the version and the digest, and the version before the form: `#iml/0.2/` followed by a well-formed document is E502, not E300. Two spaces after the header match the pattern at the first space; the chain then starts with a space, which is a stray character, E300. A header alone, with no line after it, is E300 (a document without a chain).

Compile always writes the header from the loaded registry, and writes 0.4 only: `compile` writes a message, `compile_document` writes a document with no final newline (the command line adds one). A 0.3 document decompiled and compiled again carries the 0.4 header; the document law of §6 is promised for documents the 0.4 codec produced.

::CLAUSE{HEADER|conf:confirmed|scope:iml-0.4}
T:header=#iml/0.4/+12_lowercase_hex
T:hex=the_first_12_characters_of_the_registry_digest|same_as_0.2_and_0.3
T:message=header+one_space+one_chain_on_one_line
T:document=header_alone_on_the_first_line+one_chain_per_line|at_least_one_chain|decompiles_to_one_I-Lang_line_per_chain_in_order
T:form_decided_by_the_first_line|one_final_line_terminator_accepted
T:read_order=no_#iml/_prefix⇒E502|prefix_without_the_shape⇒E300|version_0.4_or_0.3⇒read|version_0.2_without_the_flag⇒E502|other_version⇒E502|other_digest⇒E502
T:0.3_header_read_without_a_flag|same_surface_same_digest|no_colon_after_a_root_in_any_0.3_text
T:0.3_header_is_read_with_the_0.4_grammar|a_verb_reference_under_a_0.3_header_decodes|a_0.3_codec_answers_E300_to_that_text|the_header_selects_no_grammar
T:compile_always_writes_the_header_from_the_loaded_registry|writes_0.4_only
A:no_header|0.2_header_without_the_flag|version_other_than_0.3_and_0.4|digest_prefix_mismatch|second_header_in_a_document⇒E502
A:header_present_with_a_bad_shape|blank_line|trailing_space|header_without_a_chain|second_line_after_a_message⇒E300
A:document_law_claimed_for_a_document_the_0.4_codec_did_not_produce⇒unsupported_claim

---

## 4. OUT and aliases

One spelling per AST. The rule collapses the aliases and OUT, and it stops there: the batch shorthand `[BATC:READ]` (`BT:RD`) and the modifier form `[BATC|op=READ]` (`BTop=READ`), which the canon calls equivalent (§3.9), are two ASTs and keep two byte forms (§5.1). Every Greek alias in I-Lang input means its verb and is encoded as that verb's root: with the hand-derived codes of §1.5, `Σ` compiles to `MR`, `φ` to `FL`, `Π` to `BT`. Decompile prints the verb by its canon name, never by an alias, with one exception, OUT.

The same collapse holds for a verb reference, new in 0.4. The verb referenced after `:` on BATC is encoded as its root whether it is written by name or by alias: `[BATC:READ]`, `[Π:READ]` compile to `BT:RD`; `[BATC:Σ]`, `[Π:Σ]` compile to `BT:MR`. The AST records the referenced verb by its canon name, and decompile prints `[BATC:READ]`, `[BATC:MERGE]`: the verb BATC by name, never `Π`, and the reference by name, never an alias (§5.1). The two spellings of one reference are spelling (§6, L3).

OUT is the one verb encoded by a mark instead of a root: `$`, the chain terminator. `$` may carry modifiers (`$fm=json`) and may appear only as the last op (E502 otherwise). `OUT` has no two-character root; `OT` after a space is E304. In I-Lang input `[OUT]` and `[Ω]` are two spellings of the same operation; both compile to `$`, and decompile prints `[Ω]` (§5). The 0.2 surface wrote OUT as `Ω`; on the 0.4 surface, as on 0.3, `Ω` at the start of an op is a stray character (E300), and inside a value it is content (§2.2).

Because OUT has no root, it cannot be referenced: `[BATC:OUT]`, `[BATC:Ω]`, `[Π:Ω]` are E502 with the message "OUT cannot be batched: not representable in IML". The validator accepts `[Π:Ω]` (an alias is a registered alias); IML has no code for it and reports the limit as its own, not as the canon's. On the IML side `BT:$` is E300: the grammar admits only a root after `:` (§2.2).

The `op` production gives `$` no target slot and no verb reference. An I-Lang `[OUT:@X]` or `[Ω:@X]` is outside the subset (E502), and `$@` and `$:` are E300. The canon gives an OUT target a meaning (§2.2: "Output verbs (OUT): entity is the final value"); IML has not represented it since 0.2, and the limit is IML's own.

::CLAUSE{OUT-ALIAS|conf:confirmed|scope:iml-0.4}
T:one_spelling_per_AST|aliases_and_OUT_collapse|batch_shorthand_and_op_modifier_are_two_ASTs
T:greek_alias_in_input_means_its_verb|encoded_as_that_verb_root
T:verb_reference_by_name_or_by_alias_encoded_as_the_verb_root|AST_records_the_canon_name|decompile_prints_BATC_and_the_verb_by_name
T:OUT_is_the_one_verb_encoded_by_a_mark|$=the_chain_terminator|was_Ω_in_0.2
T:$_may_carry_modifiers|no_target_slot|no_verb_reference|only_as_the_last_op
T:decompile_prints_OUT_in_the_Ω_form
A:two_character_root_for_OUT⇒E304
A:$_before_the_last_op⇒E502
A:OUT_with_a_target_in_input⇒E502
A:OUT_or_Ω_as_a_verb_reference⇒E502
A:BT_colon_dollar_on_the_IML_side⇒E300
A:Ω_at_the_start_of_an_op_on_the_0.4_surface⇒E300

---

## 5. Canonical I-Lang print (decompile output)

### 5.1 Print

Unchanged since 0.2, plus the verb reference. The form is `[VERB:@TARGET|k=v,k=v]=>[...]`. Verbs print by canon name. OUT prints as `[Ω]`, with modifiers `[Ω|k=v]`. Targets print `@NAME`. A verb reference prints `[BATC:READ]`: BATC by name, the referenced verb by name, with modifiers `[BATC:READ|k=v]`. `[Π:READ]`, `[BATC:Σ]` and `[Π:Σ]` collapse to that form. An operation without a target or a verb reference omits `:@TARGET`; an operation without modifiers omits `|` and the list.

The modifier form `[BATC|op=READ]` is a different AST, a string modifier `op` with the value `READ`, and prints as written. The canon says the two forms are equivalent (§3.9: `[BATC|op=READ,src=@LOCAL]` applies READ to each item, and "in pipe shorthand, `[Π:READ]` is equivalent"); IML keeps them apart because they are two spellings with two ASTs, and each round-trips to itself: the rule of §4, one spelling per AST, collapses aliases and OUT and does not reach across two ASTs. The codec does not rewrite one into the other and does not judge `[BATC:READ|op=FMT]`.

A value prints bare when its content is not empty, contains no whitespace, none of `,` `|` `]` `[` `"` `\`, and does not start with `@`. `=`, `>` and `:` are content: `whr=score>80` (the example of draft 0.1, which the canon validator accepts) and `whr=lvl:fatal` (canon §10.1) print bare. `$` is content in I-Lang: `fmt=$x` prints bare. Otherwise a value prints quoted with the §2.4 escapes. An entity reference prints `@NAME`. No whitespace anywhere. A document prints one line per chain, in order.

A chain prints on one line whatever the layout of its source: a chain read from several lines (§2.6) prints exactly as its one-line spelling does. The canonical print never writes a continuation line.

### 5.2 Accepted input

`parse_L2` reads a chain in the subset of §0. It accepts the canonical form and four spellings of it: a Greek alias for a verb or for a referenced verb, `[OUT]` for `[Ω]`, `[Π:...]` for `[BATC:...]`, and quotes around a value whose content could print bare; and, before `parse_L2`, the readers join continuation lines (§2.6). A bare value in I-Lang input runs to the next `,`, `|` or `]`; a `|` there is a stray character (E300, §0). Inside a bare value `[`, `"` and `\` are E303 and whitespace is E300; `=`, `>` and `:` are content. Content with `,` `|` `]` `[` `"` `\` or whitespace is written quoted (§2.4: quoted strings carry spaces or special characters). A bare value beginning with `@` is an entity reference (§2.4). In the target slot a token that does not start with `@` is a verb reference on BATC and Π, E304 when it is not a registered verb or alias, `read` included; on every other verb it is E300 with the validator's wording (§7). Whitespace outside a quoted value is a stray character (E300); so are whitespace before or after the joined chain, and a dangling `=>` at the end of it.

::CLAUSE{PRINT|conf:confirmed|scope:iml-0.4}
T:unchanged_since_0.2_plus_the_verb_reference
T:verb_by_canon_name|OUT_as_Ω|target_as_@NAME|verb_reference_as_BATC_colon_verb_name|modifiers_key=value_comma_separated|ops_joined_by_the_pipe_operator
T:modifier_form_BATC_op_is_a_different_AST|prints_as_written|codec_does_not_rewrite_one_form_into_the_other
T:value_bare_iff_not_empty|no_whitespace|none_of_comma_pipe_brackets_quote_backslash|not_starting_with_@|equals_greater_than_colon_and_dollar_are_content|else_quoted_with_§2.4_escapes
T:entity_reference_prints_@NAME
T:no_whitespace_anywhere|one_line_per_chain_whatever_the_source_layout|never_a_continuation_line
T:parse_accepts_the_canonical_form_plus_four_spellings|alias|OUT_word|Π_for_BATC|quotes_around_bare_content|continuation_lines_joined_before_parse
A:print_reproduces_the_input_spelling_or_layout⇒not_canonical
A:whitespace_outside_quotes_in_input⇒E300
A:whitespace_before_or_after_the_chain|dangling_pipe_operator⇒E300
A:bracket_quote_or_backslash_inside_a_bare_value⇒E303
A:non_entity_target_on_a_verb_other_than_BATC⇒E300

---

## 6. Round-trip law

Let `parse_L2` read canon I-Lang into the AST, `print_L2` write it, `compile` be AST to IML message text, `compile_document` be a sequence of ASTs to IML document text, and `decompile` be IML text to the AST (message) or to the sequence of ASTs (document). Let `join` be the continuation-line rule of §2.6, which maps an I-Lang source, on one line or on several, to the one-line text of each chain; `join` is the identity on a one-line chain, and it refuses a source whose line break stands inside an operation (E300, §2.6), which is therefore outside the subset.

- L1 (AST fidelity): for every I-Lang chain x in the subset, `decompile(compile(parse_L2(join(x)))) == parse_L2(join(x))`. L1 is stated over the joined text: the layout of the source is not part of the AST. AST equality compares the verb, the target (by name), the verb reference (by verb name), the modifier keys in order, and the value, kind-normalised: `bare` and `quoted` compare by content, `entity` by name, `code` by code.
- L2 (canonical text): `print_L2` is idempotent, `print_L2(parse_L2(print_L2(a))) == print_L2(a)`, and `compile(decompile(m)) == m` for every IML message m that the codec itself produced.
- L3 (original bytes): not promised. Quotes, alias spelling (`Σ` against `MERGE`, `Π` against `BATC`, `[BATC:Σ]` against `[BATC:MERGE]`), and `[OUT]` against `[Ω]` are spelling; so is the surface: a chain read from its 0.2 record and one read from its 0.3 or 0.4 text are the same AST; and so is the layout: a chain written on several lines and the same chain on one line are the same AST, the same IML line and the same canonical print, and nothing records which was read.
- Document law: for every sequence of chains a1..an in the subset, `decompile(compile_document([a1..an])) == [a1..an]`, and `compile_document(decompile(d)) == d` for every document d that the codec itself produced. A document's chains are independent: the header is shared and nothing else. A 0.3 document decompiles under the default reader to the same chains as before and recompiles with the 0.4 header, so the second equation is promised for 0.4 documents only.

Tests:

- The golden corpus of 0.2 and 0.3, hand-written, 72 chains in `corpus/golden/*.ilang` covering every verb at least once, every key at least once, every registered entity, custom entities, quoted values with each escape, numbers like `007`, booleans, entity references in values, OUT with and without modifiers, and chains of length 1 to 8; `corpus/golden-0.3/*.iml` holds their 0.3 text and `corpus/golden/*.iml` the 0.2 record. Two assertions tie 0.4 to them: the 0.4 message of every golden chain equals its 0.3 `.iml` with the header version changed, and every `corpus/golden-0.3/*.iml` decompiles under the default 0.4 reader to the same canonical text as before.
- A 0.4 golden corpus, `corpus/golden-0.4/`, of at least 24 chains as pairs `NNN.ilang` and `NNN.iml`: the `.ilang` may stand on several lines (continuation lines indented by two spaces, as in the `E:` example of PATCH-2 §1.7), the `.iml` holds the one-line 0.4 message. It covers `[Π:READ]`, `[BATC:READ]`, `[BATC:READ|src=@LOCAL,mch=*.md]`, `[Π:Σ]`, `[BATC:READ|op=FMT]`, `[BATC|op=READ]`, `[BATC:@SRC|op=SCAN]`, `[LOOP|whr=until:done]`, `[WAIT|whr=status:ready]`, `[CHEK|whr=status:200]`, `[LOOP:@LIST|op=READ]`, a value containing `:` next to a verb reference, custom entities, quoted values, and the workflow chains of canon §10.7 written on several lines; plus one document pair, `doc-01.ilang` (several chains, some on several lines, blank lines between) and `doc-01.iml` (the 0.4 document).
- A malformed corpus of at least 40 inputs with expected error codes, each decompile case naming its surface, with at least 14 cases of version `0.4` added: `BT:` (E300), `BT:R` (E300), `BT:rd` (E300), `BT:XX` unknown (E304), `RD:FM` (E300), `BT:RD@SR` (E300), `BT:$` (E300), `[BATC:REED]` (E304), `[BATC:read]` (E304), `[Π:Ω]` (E502), `[LOOP:READ]` (E300), `[BATC:]` (E300), a 0.2 header on the 0.4 reader without the flag (E502), two chains on one I-Lang line (E502 with the message of §0.2). The 0.3 cases that expected E502 for `[Π:VERB]` or `[BATC:VERB]` are valid in 0.4 and leave the malformed corpus. 0.4.1 adds the single-line spellings of §0.3 that the validator accepts (`[BATC:READ ]`, `[BATC:READ|]`, `[BATC:READ]=>`, two `=>` in a row), `[Φ:@GH]` (E304; the validator: E305), and a leading U+FEFF given to `parse_L2` and to `decompile` (E502). A compile case is fed to `parse_L2`, which joins no lines, so this corpus cannot carry a multi-line source; those inputs are tested with the continuation-line rule below.
- A generator with `random.Random(20260918)` producing 10,000 chains over the registry, BATC operations with a verb reference included, run on the 0.4 surface and, for the chains that carry no verb reference, on the 0.2 surface (6,394 of the 10,000 with this seed; the other 3,606 have no 0.2 spelling, and compile must refuse each of them with E502), and the document law on those chains in batches of 100. The generator is not the oracle. The oracle for L2 legality is the vendored canon validator, run on the printed I-Lang of a 500-sample.
- The continuation-line rule on its own: a three-line chain equals its one-line spelling after `join`; an orphan line at the head of the input and after a blank line is E300; a blank line ends a chain, and so does a line of whitespace only; a continuation line under a line break inside an operation is E300 at the chain's first line, for a break inside a quoted value, inside a bare value, and after a `]` that stands inside quotes, while a closed operation whose quoted value holds `]` or an escaped quote joins as before; the header acceptance (a 0.3 header read, a verb reference under it included; a 0.2 header refused; `--version 0.3` refused).
- The writers and the command line, added in 0.4.1: `compile`, `compile_document` and `print_L2` refuse a hand-built value that holds TAB, CR, NUL, DEL, U+0085, U+2028 or U+2029 (E300) and still write the newline as its escape; a file that starts with EF BB BF compiles, decompiles and round-trips, and a second mark is refused; a file that holds the byte E9 is reported as E300 with its byte offset, on standard error, with exit code 1 and no traceback; the two messages taken from the validator are compared with the validator's own output.

::CLAUSE{ROUNDTRIP|conf:confirmed|scope:iml-0.4}
T:L1=decompile(compile(parse_L2(join(x))))==parse_L2(join(x))|for_every_chain_in_the_subset|over_the_joined_text
T:AST_equality=verb+target_name+verb_reference_name+modifier_keys_in_order+value_kind_normalised
T:L2=print_L2_idempotent|compile(decompile(m))==m_for_every_codec_produced_m
T:L3_not_promised|quotes+alias_spelling+OUT_against_Ω+the_surface+the_source_layout_are_spelling
T:document_law=decompile(compile_document(chains))==chains|compile_document(decompile(d))==d_for_0.4_documents|chains_independent_under_one_header
T:tests=golden_72_tied_to_0.4_by_two_assertions|golden-0.4_24_or_more_pairs+one_document_pair|malformed_40_or_more_with_14_or_more_0.4_cases|generator_seed_20260918_10000_chains_with_verb_references|document_law_in_batches_of_100|join_rule_tested_on_its_own|writers_and_command_line_input_tested_since_0.4.1
T:0.2_surface_laws_run_on_the_chains_without_a_verb_reference|6394_of_10000_with_the_committed_seed|the_rest_refused_with_E502
T:generator_is_not_the_oracle|oracle=vendored_canon_validator_on_printed_I-Lang|500_sample
A:round_trip_claimed_outside_the_subset⇒unsupported_claim
A:original_bytes_or_source_layout_claimed⇒contradicts_L3

---

## 7. Errors

The codec fails closed; the first error stops it. Codes reuse §9 of the canon. The codec raises these six codes and no other; 0.4 adds no code. Where the validator has a wording for a case, the codec's message follows it, the backticks around the quoted token included. The validator reports an unknown alias, `[Φ:@GH]`, as E305 (Unknown Alias, §9); the codec reports the same input as E304: it resolves a verb spelling against the 88 names and the 13 aliases in one step, and E305 is not among the six codes it raises.

| Code | Canon name | Raised when |
|------|------------|-------------|
| E300 | Syntax Error | bad header shape (§3); unterminated quote; bad escape; raw control character inside a quoted value; empty value; stray character, a `\|` between modifiers, a tab, or `Φ`, `Ω`, `→` in a syntax position included; missing `=`; whitespace in a bare value; whitespace before or after an I-Lang chain; a dangling `=>`; two spaces between ops; a trailing space; a blank line in a document; a header with no chain after it; a second line after a message line; new in 0.4: `:` after a root other than `BT` (the message begins "`:` after a root other than BT"); `BT:` with no root or a malformed root (the end of the line, a space, a lower-case letter, one character, `$`); a target after a verb reference; a verb reference after a target; `$:`; on the I-Lang side a target that does not start with `@` on a verb other than BATC and Π ("operation target `READ` is not an @ENTITY (v3.0 §2.2; BATC/Π excepted)"); an orphan continuation line ("orphan `=>` continuation: no preceding operation line"); since 0.4.1: a continuation line under a line break inside an operation ("continuation after an unterminated operation line", §2.6); on compile and print, a control character other than a newline in a value of a hand-built AST (§2.5); on the command line, input that is not valid UTF-8 (§11) |
| E304 | Unknown Verb | unknown root (decompile) or unknown verb (compile), `OT` included, and a Greek letter that is no alias, `[Φ:@GH]`, which the validator reports as E305; new in 0.4: an unknown verb reference, `BT:XX` not in the registry, `[BATC:REED]`, `[BATC:read]` ("BATC verb reference `REED` is not a registered verb or alias") |
| E302 | Invalid Modifier | unknown key code (decompile) or unknown key (compile) |
| E200 | Entity Not Found | unknown registered mark; an entity name that does not match `[A-Z][A-Z0-9_]*`; a registered entity in the custom form |
| E303 | Invalid Value | bare value containing `,` `\|` `]` `[` `"` `\` (§5.1); a value starting with `$` (§2.2); `~code` not in the key's table (always, in 0.4) |
| E502 | Unsupported Format | no header; wrong version, a 0.2 header without the flag included; digest mismatch; a second header in a document; declaration or other construct outside the subset (§0.2); OUT not last; OUT with a target; new in 0.4: OUT or Ω as a verb reference ("OUT cannot be batched: not representable in IML"); more than one chain on one I-Lang line ("a second operation chain on the line: IML carries one chain per line") |

Reading of the table. The `[Π:VERB]` and `[BATC:VERB]` form, E502 in 0.3, is in the subset and leaves the E502 row; `||`, named in the 0.3 list, is dropped from it (§0.2). A raw control character (U+0000 to U+001F, U+007F, U+0085, U+2028, U+2029) is E300 wherever it appears in a value, bare or quoted; a newline is only ever the escape `\n` inside quotes. In I-Lang input a bare value ends at `,`, `|` or `]`, so of the E303 set only `[`, `"` and `\` can stand inside one; a `|` that follows a value is a stray character, E300 (§0). In IML a bare value ends at `,` or a space, and `"` or `\` inside it is E303, any other whitespace inside it E300 (§2.1). A value that starts with `~` or `@` is not a bare value: it is read as a code or as an entity reference and judged by that rule (E303 for a code outside its table, E200 or E300 for a malformed reference); a value that starts with `"` is a quoted value; a value that starts with `$` is E303. A character that no production admits at its position, outside a value, is a stray character, E300; so is an op that starts with neither `$` nor two characters of `[A-Z0-9]`. Two characters of `[A-Z0-9]` that are not a root in the registry are E304, after `BT:` as at the start of an op. On the header and the two forms, §3 gives the split between E502 and E300.

Error objects carry `code`, `message`, `offset` (0-based character index into the whole input text, a document included) and, for compile, the operation index; inside a document the operation index counts from the start of its line, and a compile error names the chain. For a chain read from several lines the offset counts in the joined text and the reported line is the chain's first line (§2.6). The command line drops one leading byte order mark (EF BB BF) before it reads, on standard input and on a file, and reports input that is not valid UTF-8 as E300 at line 1, with the byte offset in the message and no character offset. The library functions take text and stay strict: a U+FEFF at the head of their input is E502.

::CLAUSE{ERRORS|conf:confirmed|scope:iml-0.4}
T:fail_closed|the_first_error_stops_the_codec
T:codes=SPEC.md_§9|E300+E304+E302+E200+E303+E502|no_other_code|0.4_adds_none
T:messages_follow_the_validator_where_it_has_a_wording|backticks_included
T:validator_E305_unknown_alias_is_reported_as_E304_by_the_codec
T:error_object=code+message+offset_0_based_char_index_into_the_whole_text|compile_adds_the_operation_index|multi_line_source=first_line+offset_in_the_joined_text
T:new_E300_cases=colon_after_a_root_other_than_BT|BT_colon_without_a_root|target_after_a_verb_reference|non_entity_target_on_another_verb|orphan_continuation_line
T:E300_cases_since_0.4.1=continuation_under_a_line_break_inside_an_operation|control_character_in_a_hand_built_value_on_compile_or_print|command_line_input_that_is_not_valid_UTF-8
T:command_line_drops_one_leading_byte_order_mark|library_functions_refuse_U+FEFF_with_E502
T:new_E304_case=unknown_verb_reference
T:new_E502_cases=OUT_as_a_verb_reference|second_chain_on_one_I-Lang_line
T:left_the_E502_row=batch_shorthand|double_pipe_dropped_from_the_list
A:unknown_root_key_mark_or_verb_reference_guessed_or_skipped⇒violates_fail_closed
A:error_code_registered_by_IML⇒contradicts_registers_nothing

---

## 8. Measurement

`tools/measure.py` writes `measurements/0.4-YYYY-MM-DD.md`; the report of this release is `measurements/0.4-2026-09-18.md` (Python 3.13.15, tiktoken 0.14.0), regenerated for 0.4.1 because the rule sheet changed; the rule sheet row is the one figure that differs from the 0.4.0 report. For each of the 72 golden chains of `corpus/golden/` and each of the 36 chains of `corpus/golden-0.4/` it records bytes (UTF-8), characters, and tokens under `cl100k_base` and `o200k_base` (offline cache), for the I-Lang canonical print (§5; a source written on several lines prints on one line, and its layout is not measured), the IML 0.4 message (header included), the chain line alone as it stands in a document, and a JSON form `{"c":[{"v":"READ","t":"@SRC","r":"READ","m":{"path":"x"}}]}` (compact with no spaces; `t`, `r`, the BATC verb reference, and `m` omitted when absent; the one JSON mapping used as a baseline and stated as such). For the 72 chains it also records, as the record, the IML 0.3 message and document (the same texts under the 0.3 header) and the IML 0.2 message; a verb reference has no 0.2 spelling, so the 0.4 corpus has no 0.2 column. Once per corpus it records the IML 0.4 document, the header and the chain lines measured as one text, and for the document pair `corpus/golden-0.4/doc-01.iml` its size on disk. It records the cost of `RULE-SHEET.md` in the same units, with the 0.3 and 0.2 sheets' figures copied from their reports as the record. The report gives totals and per-form means.

On the 72-chain corpus the 0.4 figures are the 0.3 figures: the 0.4 text of every golden chain is its 0.3 text with one digit of the header changed, bytes and characters are unchanged by that, and both encodings tokenise each of the two headers to 16 tokens, so every count of `measurements/0.3-2026-09-18.md` stands for 0.4 under every unit, and the 0.4 report says so. Totals from the report:

| form | bytes | chars | cl100k_base | o200k_base |
|------|---:|---:|---:|---:|
| I-Lang canonical print, 72 chains | 4462 | 4395 | 2040 | 2134 |
| IML 0.4 message (one header per chain), 72 chains; the 0.3 record is the same | 4506 | 4502 | 2438 | 2437 |
| IML 0.4 document (one header for the 72 chains); the 0.3 record is the same | 3015 | 3011 | 1315 | 1313 |
| JSON baseline, 72 chains | 8334 | 8330 | 3195 | 3262 |
| I-Lang canonical print, 36 chains of `corpus/golden-0.4/` | 1626 | 1594 | 800 | 841 |
| IML 0.4 message (one header per chain), 36 chains | 1738 | 1738 | 1014 | 1011 |
| IML 0.4 document (one header for the 36 chains) | 1003 | 1003 | 461 | 458 |
| JSON baseline, 36 chains | 3314 | 3314 | 1305 | 1343 |

Six of the 36 sources are written on several lines, and 38 verb references occur in that corpus; the document pair `doc-01.iml` (5 chains, 6 lines) is 147 bytes, 147 characters and 69 tokens under either encoding. The rule sheet: `RULE-SHEET.md` (0.4, as revised in 0.4.1) 6090 bytes, 6064 characters, 1798 `cl100k_base`, 1796 `o200k_base` (the 0.4.0 sheet: 6076, 6050, 1796, 1794); the 0.3 sheet 5782, 5748, 1792, 1794; the 0.2 sheet 5242, 5184, 1607, 1599.

No figure carries a claim; the table is the table. The report states the tokenizer scope: named encodings, not any vendor's billing. If tiktoken is missing, the tool writes bytes and characters and says that tokens were not measured (§11). On both corpora the message form is above the I-Lang canonical print in tokens and the document form is below it, as in 0.3, and neither fact is called anything more than that; ROADMAP.md gates any efficiency claim on a larger corpus, more tokenizers, the rule sheet and the reply, and that gate is unchanged and not met.

::CLAUSE{MEASURE|conf:confirmed|scope:iml-0.4}
T:tools/measure.py_writes_measurements/0.4-YYYY-MM-DD.md|this_release=measurements/0.4-2026-09-18.md
T:corpora=72_golden_chains+36_golden-0.4_chains|per_chain=bytes_utf8+characters+tokens_cl100k_base+tokens_o200k_base|tiktoken_0.14.0_offline_cache
T:forms=I-Lang_canonical_print|IML_0.4_message|IML_0.4_chain_line|compact_JSON_baseline_with_r_for_the_verb_reference_stated_as_the_one_mapping_used|0.3_and_0.2_records_for_the_72_chains
T:once_per_corpus=IML_0.4_document_measured_as_one_text|doc-01_measured_on_disk
T:72_chain_figures_of_0.4=the_0.3_figures|header_digit_changes_no_byte_character_or_token_count|report_says_so
T:golden-0.4_totals_cl100k=I-Lang_800|message_1014|document_461|JSON_1305|as_recorded_in_the_report
T:rule_sheet_cost_in_the_same_units|0.4_sheet_1798_cl100k_as_revised_in_0.4.1|0.3_and_0.2_sheet_figures_copied_as_record|totals+per_form_means
T:tokenizer_scope=named_encodings|not_a_vendor_billing
A:figure_called_a_saving⇒violates_the_ROADMAP_gate
A:figure_published_without_corpus_tokenizer_and_both_baselines⇒unsupported_claim

---

## 9. Outside 0.4

Not in 0.4, reported as E502, the precise list: declarations (`::`); the temporal notation of §7.5, `T[n]` before a chain, `T[a]→T[b]` and `PARALLEL{a, b}`, which the validator reads as opaque note lines without linting what stands inside them, and which is SOUL-layer narrative notation, not chain syntax; comments and anything after the chain (the canon has no comment syntax; the validator's mixed mode tolerates prose after a chain, IML does not); more than one chain on one I-Lang line (the document form carries several chains); OUT with a target (`[Ω:@OUT]`, on which the validator reports INFO only); OUT before the last operation (`[Ω]=>[FMT]`, which the validator does not enforce; IML is stricter here); OUT or Ω as a verb reference. Everything else that is not in the subset of §0.2 is E502 as well.

Carried as plain operations, with nothing promised about their semantics: `LOOP`, `WAIT`, `CHEK`, `EVAL`, `DECI` and every other verb that names control or judgment in its row; their meaning stays with the executing model (§0.4).

0.5 candidates, gated on chain syntax in the canon: conditionals, parallel groups, DAGs, error handling, retry. None of them is operation-chain syntax in the canon at the pin (§0.3), and IML defines no construct of its own; each would first need operation-chain syntax in the canon (ilang-spec), and only then a derivation and a corpus here. MCP and A2A adapters are not codec work: they carry IML, they do not change it, and they are not versioned with this specification.

Belongs to the envelope, not to IML: authority, signing, encryption, effect enforcement and version negotiation. Where a signature is used it covers the detached raw bytes of the message or of the document. A receiver treats an IML message as untrusted input under I-Lang v4.0 until the envelope says otherwise.

Not planned: serialising OpenAPI schemas; variable-length verb coding; outreach to transport or platform vendors.

Later versions. A value-code table may be filled in a later version (§1.3), and `$` at the start of a value is held free for a later use (§2.2). A message written under 0.4 keeps its meaning, because a literal is never marked and a code is always marked. The 0.3 surface is the 0.4 surface and a 0.3 header is read without a flag; the 0.2 surface is read only, behind an explicit request, is not written by a 0.4 codec, and no further change to it is planned.

Claims. ROADMAP.md gates the efficiency claim: on at least 1000 real instruction chains and at least three tokenizers, total IML tokens, rule sheet and retries included, below both I-Lang v4 text and JSON with schema. Until that gate is met nothing of the kind is claimed anywhere; §8 is a record of what was measured, not a claim. The 1.0 gate is two independent codecs passing each other's corpora, a public conformance corpus, and a core frozen for 90 days with no blocking defect.

::CLAUSE{OUTSIDE-0.4|conf:confirmed|scope:iml-0.4}
T:E502_list=declarations|temporal_notation_of_§7.5|comments_and_trailing_text|second_chain_on_one_line|OUT_with_a_target|OUT_before_the_last_operation|OUT_as_a_verb_reference
T:temporal_notation_is_narrative_not_chain_syntax|validator_reads_it_as_opaque_note_lines
T:LOOP_WAIT_CHEK_EVAL_DECI_carried_as_plain_operations|semantics_with_the_executing_model
T:0.5_candidates_gated_on_chain_syntax_in_the_canon=conditionals+parallel_groups+DAGs+error_handling+retry
T:MCP_and_A2A_adapters_are_not_codec_work|not_versioned_with_this_specification
T:envelope=authority+signing+encryption+effect_enforcement+version_negotiation|signature_covers_the_detached_raw_bytes
T:receiver_treats_an_IML_message_as_untrusted_input_under_v4.0_until_the_envelope_says_otherwise
T:not_planned=OpenAPI_schema_serialisation|variable_length_verb_coding|vendor_outreach
T:dollar_at_value_start_held_free|0.3_header_read_without_a_flag|0.2_surface_read_only_and_frozen
T:efficiency_claim_gated_by_ROADMAP|nothing_claimed_until_the_gate_is_met
A:0.5_construct_defined_by_IML_before_the_canon_defines_its_chain_syntax⇒contradicts_registers_nothing
A:0.4_header_or_batch_shorthand_read_by_a_0.3_codec⇒E502
A:verb_reference_under_a_0.3_header_read_by_a_0.3_codec⇒E300
A:security_property_attributed_to_IML⇒belongs_to_the_envelope

---

## 10. Worked examples

All codes below are hand-derived (§1.5); the registry file is authoritative for every code. `88d05d0839c1` is the first 12 hex characters of the registry digest at the pin; the registry file is authoritative and a rebuilt registry must reproduce it. Every I-Lang line below was checked with the pinned validator (0 errors).

### 10.1 The batch shorthand, from canon §10.1

I-Lang:

```
[LIST:@LOCAL|mch=*.md]=>[Π:READ]=>[Σ]=>[Ω]
```

IML 0.4 message:

```
#iml/0.4/88d05d0839c1 LS@LCmc=*.md BT:RD MR $
```

Reading the line after the header and its space: `LS` is a root, LIST; `@` opens a target, `LC` is a mark, `@LOCAL`; `m` opens the modifier list, `mc` is a key, `mch`, `=`, then a value running to the space, `*.md`, bare; the space opens the next op; `BT` is BATC; `:` directly after the root `BT` opens a verb reference; `RD` is the root of READ; the space opens the next op; `MR` is MERGE with no target; a space; `$` is OUT, and the line ends. Decompile prints `[LIST:@LOCAL|mch=*.md]=>[BATC:READ]=>[MERGE]=>[Ω]`: `Π` and `Σ` are spelling (§4, §6 L3) and the canonical print uses the verb names.

### 10.2 A verb reference with modifiers

I-Lang:

```
[BATC:READ|src=@LOCAL]=>[Ω]
```

IML 0.4 message:

```
#iml/0.4/88d05d0839c1 BT:RDsr=@LC $
```

After the verb reference `RD` the lower-case `s` opens the modifier list, as it would after a target: `sr=@LC` is `src=@LOCAL`, an entity reference in value position (kind `entity`). `[Π:READ|src=@LOCAL]=>[Ω]` compiles to the same line. Decompile prints the I-Lang line above unchanged.

### 10.3 The modifier form

I-Lang:

```
[BATC|op=READ]=>[Ω]
```

IML 0.4 message:

```
#iml/0.4/88d05d0839c1 BTop=READ $
```

`op` is a key with the code `op`; its value `READ` is a bare string, copied and not validated (§0.2). This is a different AST from 10.2, a string modifier and no verb reference, and it prints as written: `[BATC|op=READ]=>[Ω]`. The codec does not rewrite either form into the other (§5.1).

### 10.4 An entity target on BATC

I-Lang:

```
[BATC:@SRC|op=SCAN]=>[Ω]
```

IML 0.4 message:

```
#iml/0.4/88d05d0839c1 BT@SRop=SCAN $
```

`@` after the root `BT` opens an entity target, as on every verb; only `:` opens a verb reference. `SR` is the mark of `@SRC`; `op=SCAN` is a string modifier. Decompile prints the I-Lang line above unchanged.

### 10.5 A chain of canon §10.7, written here on three lines

I-Lang source:

```
[DPLO:@WORKER]
  =>[CHEK|whr=status:200]
  =>[Ω]
```

The canon prints this chain on one line (§10.7); the three-line layout is this document's, by the continuation form of PATCH-2 §1.7. The reader (§2.6) joins the three lines into `[DPLO:@WORKER]=>[CHEK|whr=status:200]=>[Ω]`, each line break following a closed operation, and parses that text as a one-line chain. IML 0.4 message:

```
#iml/0.4/88d05d0839c1 DP@WR CKwh=status:200 $
```

`DP` is DPLO, `@WR` is `@WORKER`; `CK` is CHEK (the candidate `CH` had gone to CHNK, §1.5); `wh=status:200` is `whr=status:200`, and the `:` inside the value is content, since `:` is syntax only directly after a root (§2). Decompile prints the one-line chain; the three-line layout is not carried (§6, L3). An error in the source is reported at line 1, the chain's first line, with the offset counted in the joined text.

### 10.6 The chains of 10.1, 10.2 and 10.5 as one document

I-Lang source, with 10.1 written on four lines and blank lines between the chains:

```
[LIST:@LOCAL|mch=*.md]
  =>[Π:READ]
  =>[Σ]
  =>[Ω]

[BATC:READ|src=@LOCAL]=>[Ω]

[DPLO:@WORKER]
  =>[CHEK|whr=status:200]
  =>[Ω]
```

IML 0.4 document:

```
#iml/0.4/88d05d0839c1
LS@LCmc=*.md BT:RD MR $
BT:RDsr=@LC $
DP@WR CKwh=status:200 $
```

The first line is the header alone, so the text is a document; each following line is one chain, read as in 10.1, 10.2 and 10.5. A blank line in the source ends a chain, so the `=>` lines that follow `[DPLO:@WORKER]` continue that chain and not the one before the blank line; a blank line inside the IML document would be E300 (§3). Decompile prints three I-Lang lines, in this order:

```
[LIST:@LOCAL|mch=*.md]=>[BATC:READ]=>[MERGE]=>[Ω]
[BATC:READ|src=@LOCAL]=>[Ω]
[DPLO:@WORKER]=>[CHEK|whr=status:200]=>[Ω]
```

Under a `#iml/0.3/88d05d0839c1` header the 0.4 reader reads all three chain lines the same way without a flag: the header selects no grammar (§3). A 0.3 writer could have produced the third line only; the first and the second carry `:` after a root, which no 0.3 text does and which a 0.3 codec refuses (E300).

::CLAUSE{EXAMPLE|conf:confirmed|scope:iml-0.4}
T:codes_hand_derived_by_§1.3|registry_file_authoritative
T:digest_prefix_at_the_pin=88d05d0839c1|registry_file_authoritative
T:every_I-Lang_example_checked_with_the_pinned_validator
T:verb_reference_prints_BATC_colon_verb_name|Π_and_Σ_are_spelling
T:modifier_form_and_verb_reference_form_are_two_ASTs|each_prints_as_written
T:multi_line_source_joined_before_parse|prints_on_one_line|layout_not_carried
T:document_prints_one_line_per_chain|blank_line_in_the_source_ends_a_chain
A:digest_prefix_copied_from_this_text⇒E502_against_the_real_registry

---

## 11. Repository layout (non-normative)

The executable form of §1, §6 and §7 lives beside this document:

- `SPEC-IML-0.4.md` (this text), `SPEC-IML-0.3.md` and `SPEC-IML-0.2.md` (the records of 0.3 and 0.2, unchanged) and `RULE-SHEET.md` (the 0.4 rule sheet, at most 1,800 tokens under `cl100k_base`)
- `canon/`: vendored `SPEC.md`, `archive/SPEC-v5.0-PATCH-2.md`, `SPEC-v4.1-MEDIA-PROFILE.md`, `ilang_grammar_validator.py` at the pin, and `canon/PIN`
- `tools/derive_registry.py` and `registry/iml-registry-0.2.json` (unchanged)
- `iml/__init__.py`, `iml/registry.py`, `iml/l2.py`, `iml/codec.py`, `iml/errors.py`, `iml/__main__.py` (CLI: `compile [--document]`, `decompile [--version 0.2]`, `roundtrip`, `check-registry`); `compile` joins continuation lines and writes 0.4 only, `decompile` decides the form by the first line, reads a 0.4 or a 0.3 header by default and the 0.2 surface only behind `--version 0.2`; in `compile` an error names the chain's first line; input is UTF-8, one leading byte order mark is dropped on standard input and on FILE (Windows PowerShell 5.1 puts one in front of text it pipes as UTF-8), and input that is not valid UTF-8 is E300 at line 1 with the byte offset, while the library functions stay strict
- `corpus/golden/*.ilang` (the 72 sources) with `corpus/golden-0.3/*.iml` (their 0.3 text) and `corpus/golden/*.iml` (the 0.2 record); `corpus/golden-0.4/` (the 0.4 pairs `NNN.ilang` and `NNN.iml`, the `.ilang` on one line or several, and the document pair `doc-01.ilang` and `doc-01.iml`); `corpus/malformed/cases.json` (each decompile case names its surface, the 0.4 cases their version)
- `tests/test_registry.py`, `tests/test_codec.py`, `tests/test_roundtrip.py`, `tests/test_malformed.py` (stdlib unittest, `python -m unittest discover -s tests`), extended for 0.4, and the 0.4 modules `tests/test_flow.py` (the verb reference; the continuation-line rule; the command-line input; the header acceptance, where `TestHeaderAcceptance.test_0_3_header_read_without_a_flag` pins that a verb reference under a 0.3 header decodes, §3) and `tests/test_golden_04.py` (the 0.4 golden corpus and the two corpus assertions of §6)
- `tools/measure.py` and `measurements/0.4-2026-09-18.md` (`measurements/0.2-2026-09-18.md` and `measurements/0.3-2026-09-18.md` stay as the records)
- `.github/workflows/test.yml` (python 3.12: derive check and unittest)
- `.gitattributes` (LF for every text file)

Python 3.10 or later. Standard library only for the codec and the tests; tiktoken only in `tools/measure.py`, and optional there. All files LF line ends, UTF-8, no BOM; `.gitattributes` pins LF for every text file, so a Windows clone made with `core.autocrlf=true` keeps the sha256 of `canon/` and `tools/derive_registry.py --check` passes. `LICENSE` and `drafts/` are not touched; `README.md` and `ROADMAP.md` are updated at every release.

::CLAUSE{FILES|conf:confirmed|scope:iml-0.4}
T:python_3.10_or_later|standard_library_only_for_codec_and_tests|tiktoken_only_in_tools/measure.py_and_optional
T:LF_line_ends|UTF-8|no_BOM|.gitattributes_pins_LF
T:compile_joins_continuation_lines_and_writes_0.4_only|decompile_reads_0.4_and_0.3_by_default|0.2_only_behind_--version_0.2
T:command_line_input=UTF-8|one_leading_byte_order_mark_dropped|input_that_is_not_valid_UTF-8_is_E300_at_line_1|library_functions_strict
T:golden-0.4_pairs_may_be_multi_line_on_the_I-Lang_side|one_line_on_the_IML_side
T:README_and_ROADMAP_updated_at_every_release
T:non_normative|the_registry_file_and_the_corpora_are_the_executable_form_of_§1_§6_§7
A:LICENSE_or_drafts_edited_by_0.4_work⇒out_of_scope
A:SPEC-IML-0.3.md_or_SPEC-IML-0.2.md_edited_by_0.4_work⇒the_record_is_no_longer_a_record

---

## 12. Revision history

- 0.2.0 (2026-09-18): first implemented version (`SPEC-IML-0.2.md`).
- 0.2.1 (2026-09-18): clarifications; the message form and the registry unchanged.
- 0.2.2 (2026-09-18): citation metadata; no other change.
- 0.3.0 (2026-09-18): surface change only (`SPEC-IML-0.3.md`). `Φ` to `@`, `Ω` to `$`, `→` to one space; the header `#iml/0.3/`; the document form with one header for many chains; `$` at the start of a value reserved (E303); the 0.2 surface read only behind `--version 0.2`. The registry (digest 88d05d0839c1…), the AST, the value rules, the canonical print, the round-trip law and the six error codes unchanged.
- 0.3.1 (2026-09-18): U+0085 added to the control characters; the `bare` production states that whitespace means any Unicode whitespace; the grammar shows the optional final line terminator; the per-mark token cost is the measured figure; the rule sheet names the registered-name-in-custom-form, empty `~` and `$@` cases. No change to the message form, the registry or the error codes.
- 0.4.0 (2026-09-18): flow within the canon. The verb reference of §3.9 on BATC (`[BATC:READ]`, `[Π:READ]`, `BT:RD`), with an alias collapsing to its verb and OUT not referenceable (E502); continuation lines on the I-Lang side (PATCH-2 §1.7), joined before parsing, with an orphan line E300 in the validator's wording; the three definitions of §0.4 written from canon text and the canon audit of §0.3; the header `#iml/0.4/`, a 0.3 header read without a flag; the `Op` field `verbref`; `||` dropped from the excluded list; a second chain on one line E502 with its own message. The registry (digest 88d05d0839c1…), the value rules, the canonical print of every 0.3 chain, the round-trip law and the six error codes unchanged; on the 72-chain corpus no figure changes.
- 0.4.1 (2026-09-18): fix release after an adversarial review of a clean clone, whose random testing broke no law. Codec: a continuation line is joined only after a closed operation (§2.6; 0.4.0 joined `[READ|whr="abc` and `  =>def"]` and compiled `RDwh=abc=>def`), and a line of whitespace only is a blank line; `compile`, `compile_document` and `print_L2` refuse a control character other than a newline in a hand-built value (E300, §2.5); the two messages that follow the validator carry its backticks (§7). Command line: one leading byte order mark is dropped, and input that is not valid UTF-8 is E300 where 0.4.0 printed a traceback (§7, §11). Text: `::FALLBACK` is a v4.0 declaration, the PROTOCOL header is cited from an upstream file that is not vendored, and an OUT target has canon text (§0.3); the spellings the validator accepts and IML refuses are listed (§0.3); D1 drops the ordering claims and quotes the disclaimer of §3, D2 quotes §4.2 (§0.4); a 0.3 header is read with the 0.4 grammar (§3); "one spelling per AST" is scoped to aliases and OUT (§4); the validator's E305 is E304 here (§7); the canon's example of a wrapped chain is the `E:` line of PATCH-2 §1.7, not §10. 7 malformed cases added, 168 in all; the continuous integration run fails on a tracked `.pyc`. The message form, the registry (digest 88d05d0839c1…), the AST and the six error codes unchanged.

::CLAUSE{REVISIONS|conf:confirmed|scope:iml-0.4}
T:0.3.0=surface_change_only|marks_ascii|header_document_level|dollar_at_value_start_reserved|0.2_surface_read_only
T:0.3.1=fix_release|NEL_control|bare_unicode_whitespace|grammar_final_NL|token_cost_measured|rule_sheet_gaps|cli_edge_cases
T:0.4.0=flow_within_the_canon|verb_reference_on_BATC|continuation_lines_on_compile|three_definitions_from_canon_text|canon_audit|header_0.4_with_0.3_read|Op_gains_verbref
T:0.4.1=fix_release|continuation_joined_only_after_a_closed_operation|whitespace_only_line_is_blank|writers_refuse_control_characters|validator_wording_with_backticks|command_line_drops_one_byte_order_mark_and_reports_invalid_UTF-8_as_E300|audit_rows_corrected|D1_without_ordering_claims|D2_quotes_§4.2|0.3_header_read_with_the_0.4_grammar|one_spelling_per_AST_scoped|E305_reported_as_E304|message_form+registry+AST+error_codes_unchanged
T:unchanged=registry_digest_88d05d0839c1|value_rules|canonical_print_of_every_0.3_chain|round_trip_law|error_codes|72_chain_figures
A:revision_changes_the_registry⇒a_new_version_not_a_revision
