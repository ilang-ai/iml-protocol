# IML (I-Lang Machine Layer) 0.5

::STATE{@SPEC, id:IML-0.5, revision:0.5.1, layer:machine, status:adopted, date:2026-09-18}
::STATE{@SPEC, canon:ilang-ai/ilang-spec, canon_pin:127ba56, canon_commit:127ba56f4eb1f35c2951d4aec4b7bd22831119ff, canon_version:v4.2.0}
::STATE{@SPEC, registers_nothing:true, verbs_derived:88, aliases_derived:13, keys_derived:49, entities_derived:25, declarations_derived:49, tolerated_annotations:2, value_code_tables:empty, digest_prefix:7e29fae7f5ea, chain_registry_digest_prefix:88d05d0839c1}
::STATE{@SPEC, supersedes:SPEC-IML-0.4.md, change:the_declaration_layer, owner_decision:A_2026-09-18, adds:whole_raw_documents+declaration_codes+text_lines, header:0.5, ast_change:Decl_and_Text_items, error_codes_unchanged:true, scope_fixed_by:ROADMAP.md}
::STATE{@SPEC, authors:Long_Quan_Zhu(Max/@SUN)+CC(@CLAUDE), orcid:0009-0004-4540-8082}

Purpose: IML (I-Lang Machine Layer) is a machine form of I-Lang, with fixed-width codes derived from the canon. Versions 0.2 to 0.4 carried operation chains; 0.5 carries a whole raw I-Lang document, its declarations and every other line included. A codec compiles a document to IML and decompiles it back; a message still carries one operation chain on one line. This document is the specification of version 0.5. What the canon defines formally is coded or made explicit: the names listed in PATCH-2 §1.5 and §1.6 get two-character declaration codes, derived by the algorithm that derives the verb roots; the block structure of PATCH-2 §1.1 and §1.2 (the three block shapes, the flush-left body, one level of nesting) and the opaque `::UNTRUSTED` block become explicit line structure; a body line keeps the first-token dispatch of PATCH-2 §1.2, and a B8 operation line is coded as an IML chain. What the canon does not tokenize is carried as exact text in an IML quoted string (§0.4). The registry gains a declarations table and therefore a new digest (§1); the header becomes `#iml/0.5/7e29fae7f5ea` (§3); a document becomes a sequence of items of three kinds, chains, declarations and texts (§4); the six error codes are unchanged (§7).

The chain layer of 0.4 is unchanged and is not restated in full. The subset of `SPEC-IML-0.4.md` §0.2, its derivation of verb roots, key codes and entity marks (§1), its segmentation, typing and value rules (§2.2 to §2.6), OUT and the aliases (§4), the canonical print of a chain (§5), the chain laws (§6) and the error rows (§7) apply to every chain of a 0.5 message or document, wherever the chain stands; §2.1 below repeats the chain grammar so that the grammar stands in one place. `SPEC-IML-0.4.md`, `SPEC-IML-0.3.md` and `SPEC-IML-0.2.md` stay unchanged as the records of 0.4, 0.3 and 0.2.

IML sits under I-Lang. I-Lang carries the meaning; IML is a spelling of it that a codec produces and reads. IML registers no verb, no modifier key, no entity, no declaration and no error code. Every code in an IML text is derived by a fixed algorithm from a name in the I-Lang canon at the pinned commit, and the derived tables are files in this repository. The registry files are authoritative for every code. The declaration codes in this text are copied from `registry/iml-registry-0.5.json`, and every IML line in it was produced by the codec; where a file differs from this text, the file is right.

What 0.5 promises is stated in §6 and tested: a document that the codec accepts round-trips at the AST level, and its canonical print is a fixed point. Nothing is promised for a text the codec refuses, and the layout of a source (indentation, blank and `---` lines, trailing whitespace, and the whitespace at the structural positions of declarations and chains, the place of a body token trailing the header line among them) is not carried, while the whitespace inside a line carried as a text is content (§4.1). No efficiency figure is claimed; §8 says how measurement is reported. ROADMAP.md fixes the scope of 0.5 and says what stays open.

Notation: the marks of 0.4 are `@` (U+0040), `$` (U+0024), the space (U+0020) between operations and `:` (U+003A) after the root of BATC. 0.5 gives three characters a meaning at the start of an IML line, `"` (U+0022) for a text, `:` for a declaration and the space for a line that belongs to the declaration above, and three a meaning inside a declaration line, `::` before the name of a MODULE, `T` before a temporal prefix and `{` for a span. Grammar is written in EBNF; `;` starts a comment. A section number without a document name (§2.1, §6, §7, §10.2) refers to the canon `SPEC.md`; PATCH-2 §1.1 to §1.7 and §2.2 refer to `canon/archive/SPEC-v5.0-PATCH-2.md`; "upstream `SPEC-v4.0-FINAL.md`" is that file in `ilang-ai/ilang-spec` at the pin, which is not vendored under `canon/`. "The validator" is `canon/ilang_grammar_validator.py` at the pin, run as `--lint` on one file. It reads a file in raw mode when the file's first nonblank line starts with `::ILANG::` (`Linter.__init__`, `raw_mode`) and walks it with `lint_region`; its functions are named here so that they can be read. Its messages are quoted as it prints them; those that contain a dash, the message for a second segment on a name other than MODULE and the messages for full-width separators, are described instead of quoted.

---

## 0. Scope

### 0.1 Why 0.5

ROADMAP.md deferred to 0.5 conditionals, loops beyond BATC, parallel groups and DAGs, error handling and retry, each gated on operation-chain syntax in the canon. At the pin none of them is operation-chain syntax (`SPEC-IML-0.4.md` §0.3), the gate still holds, and they stay outside IML (§9.2). What the canon does define formally, and IML did not carry, is the declaration layer. SPEC.md §2.1 opens it ("Declaration Syntax `::` - what something IS"; "Identity, state, rules, behavioral genes, metadata."); SPEC.md §6 gives the canonical form of each declaration and refers the grammar they share to PATCH-2 §1; PATCH-2 §1 states that grammar: three block shapes (§1.1), a closed set of eight body line forms (§1.2), encoding (§1.3), reserved body keys (§1.4), the registry of 32 structural declarations, with three meta declarations and one block terminator beside it (§1.5), 13 narrative declarations (§1.6), and the grammar amendments of §1.7 (document marker and preamble, temporal prefix and bind, chain continuation, narrative payload, and the canonical forms of `::BOUNDARY`, `::CLAUSE` and `::MODULE`). The pinned validator applies that grammar to a whole document.

On 2026-09-18 the owner decided A: the canon is not changed; IML carries the canon's declaration layer in machine form, derives everything from the canon and registers nothing of its own. The aim set with the decision is to cover the whole canon; 0.5 covers what the validator reads in raw mode, and §9.2 says what of the canon is still outside.

What 0.5 changes: a second registry file, with a declarations table and a new digest (§1); the header `#iml/0.5/` with that digest (§3); the document form, which carries declarations and text lines besides chains (§2, §4); `compile --document` and `roundtrip`, which read a whole raw I-Lang document (§3, §11). What 0.5 leaves as it is: the chain registry `registry/iml-registry-0.2.json`, byte for byte, with its digest `88d05d0839c1` and every code in it; the chain subset, the value rules, the canonical print of a chain and the chain laws of 0.4; the message form, a header, one space and one chain on one line; the six error codes; and the reading of every 0.4 and 0.3 message and document, which the default reader decodes as before (§3).

### 0.2 What 0.5 covers

A 0.5 document carries one raw I-Lang document, and every line that the validator reads in raw mode has a place in it. IML reads its I-Lang input as raw whether or not the first nonblank line is a `::ILANG::` marker; the validator reads a text without the marker as Markdown (mixed mode), so the oracle of §6 is stated for documents that begin with the marker. A document is a sequence of items of three kinds (§4.1):

- a chain: an operation line with its continuation lines joined (PATCH-2 §1.7), coded as in 0.4, at the top level or as a B8 line of a declaration body;
- a declaration: its name coded; the second segment of a `::MODULE::NAME` header, a temporal prefix `T[n]` and the addressing of a double-brace narrative made explicit; its shape explicit (brace, set span, wrapped field header, opaque block); the content between its braces carried as text; its body lines carried by the first-token dispatch of PATCH-2 §1.2, a B7 line as a nested declaration, a B8 line as a chain and every other body line as text;
- a text: a line carried as exact text. At the top level: the document marker, a tag line, a temporal bind or note, an annotation line, a tolerated `::LATENCY` or `::CONFIDENCE` line, colophon prose. In a body: every line that is neither B7 nor B8.

The message form is unchanged: a header, one space and one chain on one line (§3). Declarations and text lines stand in the document form only.

### 0.3 Canon audit

The rows were checked on 2026-09-18 against the canon files vendored under `canon/` (`SPEC.md` and PATCH-2), against the pinned validator, one probe per file, `--lint`, each probe opening with the marker `::ILANG::v5.0` so that the validator reads it in raw mode, and against the codec. One row rests in part on a file that is not vendored: the opaque block cites upstream `SPEC-v4.0-FINAL.md` §1 at the pin. "0 errors" means `0 error(s), 0 warning(s)`.

| Construct | Canon text | Validator answer | IML 0.5 |
|---|---|---|---|
| `::ILANG::v5.0` as the first or the last nonblank line | PATCH-2 §1.7, `document_header`: "T:form=`::ILANG::<version>[::<name>]`_as_first_nonblank_line_of_a_document", "T:the_same_marker_form_MAY_close_a_document_as_its_last_nonblank_line\|PRE_footer_form" | decides raw mode (`Linter.__init__`); 0 errors; elsewhere E300 "::ILANG document marker may only open or close a document (§1.7)"; `::ILANG::v5.0 x` E300 "malformed ::ILANG document marker: ::ILANG::v5.0 x" | a text; the same two E300 |
| `[TYPE:x][LIST:y]` after the marker | §1.7: "T:zero_or_more_preamble_lines_may_follow\|each_line=one_or_more_concatenated_`[TAG:value]`_tags\|TAG=UPPERCASE", "T:preamble_lines_are_document_metadata\|NOT_operations\|no_E304" | 0 errors: metadata in preamble position, also when a TAG is a verb name; blank lines and `T[n]=value` binds do not end the preamble, so `[LIST:y]` after `T[0]=2015` is metadata too | a text; a one-operation chain there whose canonical print would be a tag line, `[Σ]` or `[Π:READ]`, is E300 (§9.1) |
| a tag line after a construct, `[TYPE:x]`; `[LIST:known]` | no top-level production outside the preamble; B5 `[TAG:value]` in a body (§1.2) | `check_bracket_line`: `[TYPE:x]` 0 errors (a metadata tag line); `[LIST:known]` is an operation, its head being a verb: E300 "operation target `known` is not an @ENTITY (v3.0 §2.2; BATC/Π excepted)" | a text; an operation line is a chain, judged as in 0.4 (the same E300) |
| `T[9]=2015` | §1.7, `temporal_prefix`: "T:`T[n]=value`_line_binds_position_n_to_an_absolute_value" | 0 errors (`RE_TEMPORAL_BIND`) | a text |
| `T[0]  ::EVENT{1998\|entered_wuhan_university}` | §1.7: "T:form=`T[n]`_whitespace_declaration\|binds_the_declaration_to_timeline_position_n", the `E:` line of that production | 0 errors (`RE_TEMPORAL_PREFIX`, then `parse_construct`) | a declaration with the prefix `0`; the whitespace after `]` is layout |
| `T[0]→T[1]`, `PARALLEL{a, b}`, `T[2] anything [READ] here` | §7.5 | 0 errors: opaque notes (`RE_TEMPORAL_NOTE`), nothing inside is linted | a text |
| `→ note`, `<<< note` | no production in the vendored canon | 0 errors: annotation lines | a text |
| `Plain words here` | none | before the first construct 0 errors (colophon prose, a line without `::` `[` `{` `}` `\|` `⇒` `=>`); after one, or with one of those, E300 "line matches no I-Lang production: Plain words here" | a text under the same condition; the same E300 |
| `=>[Ω]` with no operation line above | §1.7, `chain_continuation` | E300 "orphan `=>` continuation: no preceding operation line" | the same E300 |
| `::WIDGET{x:1}` | §1.5, DECL-COUNT: "T:this_registry_is_the_canonical_count" | E300 "::WIDGET is not in the declaration registry (32 structural + 13 narrative, PATCH-2 §1.5/§1.6)" | the same E300 |
| `::MODULE::CORE{`; `::STATE::X{a}` | §1.7, `decl:MODULE`: "T:compound_header=`::MODULE::NAME{`\|the_sole_two_segment_declaration_name" | `::MODULE::CORE{` 0 errors; `::STATE::X{a}` E300, the message naming `::STATE::X` and saying that only ::MODULE takes a two-segment name, citing §1.7 | `sub`, written `::CORE` after the code of MODULE; the same E300 elsewhere |
| `::LATENCY{0}`, `::CONFIDENCE{1.0}` | §1.6: "`::LATENCY` and `::CONFIDENCE` appear as annotation lines in v3.0 §10.4 examples but are not defined in §7." | 0 errors wherever a declaration may stand (`TOLERATED_ANNOT`); the rest of the line is not read: `::CONFIDENCE junk` 0 errors | a text, with no code |
| `::FACT{key:a\|value:@bad_case}` | PATCH-2 §2.2: "A:lowercase_or_leading_digit_after_the_sigil⇒E300" | E300 "entity `@bad_case` violates @[A-Z][A-Z0-9_]* (§2.2)" (`scan_entities`) | the same E300 |
| `::FACT key` | §1.1 forms | E300 "::FACT header lacks `{`" | the same E300 |
| `::FACT{key：a\|value:b}`; `::FACT{key:a｜value:b}` | §1.3: "A:full_width_colon_or_pipe_as_structural_separator⇒E300\|use_ASCII_`:`_and_`\|`" | E300 for each, the message naming the full-width character as a structural separator, citing §1.3 and advising the ASCII one; `::FACT{key:a：b\|value:c}` 0 errors | the same E300; with a same-line trailing body token IML checks the braces alone as well (§4.3, §9.1) |
| `::SAY{@A}` | SPEC.md §7: "SOUL narrative verbs use double-brace form: `::VERB{addressing}{content}`" | E300 "::SAY requires double-brace form ::VERB{addressing}{content} (v3.0 §7)", at the top level and nested | the addressing carried as `addr`; the same E300 |
| `::PRIORITY{` ... `}`; `::GENE_MUTABLE{communication_style\|` ... `Θ:task_type=report}` | §1.1, `brace_span`: "T:form=`::DECL{` + content_lines + `}`_on_own_line", "T:wrapped_field_header\|content_after_opening_brace_on_header_line⇒terminates_at_first_line_ending_with_`}`\|v3.0_§10.3_style" | 0 errors (`consume_brace_span`); unclosed: E300 "::PRIORITY brace span never closes" | shape `set` or `wrapped`; content lines as texts; the same E300 |
| `::JUDGE{v5.0}` then `V:`, `M:`, `R:` lines at the same indent | §1.1, FLUSH-LEFT-BODY: "T:a_header_line_immediately_followed_by_lines_matching_body_forms_B1-B5_at_the_same_indent⇒header_body" | 0 errors (`consume_body`, `is_body_form`) | body lines; flush-left or indented is layout |
| `::MODE{M1\|name:EXEC_AUTO}     T:same_line_trailing_body` | FLUSH-LEFT-BODY: "T:a_single_body_form_token_MAY_trail_the_header_on_the_same_line\|whitespace_separated\|e.g._PATCH-1_§2_::MODE_lines" | 0 errors: the token is read as a body line | the first body line; its position is layout |
| `free prose under gene` in a `::GENE` body | §1.2 B6: "T:permitted_only_where_declaration_type_declares_prose_body" | E300 "B6 prose body line inside non-prose ::GENE (§1.2 B6): free prose under gene"; under `::LESSON` 0 errors | the same E300; a text in a prose-body declaration |
| `[lower]` in a `::GENE` body | §1.2 B5 and B8 | E300 "bracket body line is neither B5 tag nor B8 operation: [lower]"; under `::LESSON`, bracket-initial prose, 0 errors | the same |
| `::PRIOR{b:c}` in a `::GENE` body, and a `::PRIOR` below it | §1.2 B7: "T:one_level_of_declaration_nesting\|deeper_declaration_nesting_undefined" | one level 0 errors; the second E300 "declaration nesting exceeds one level (§1.2 B7)"; a nested `::GRAMMAR` E300 "nested ::GRAMMAR is not a registered declaration" | a nested declaration; the same E300s |
| `[PARS:@SYS_PROMPT\|fmt=text]=>[RUN:@ALL]=>[Ω]` in an `::ACTIVATE` body | §1.2 B8: "T:operation_syntax_inside_declaration_body_is_legal", "T:semantics=declared_pipeline\|NOT_immediate_execution" | 0 errors (`check_operation`); a `=>` line with no operation above it in a `::GENE` body: E300 "orphan `=>` continuation in ::GENE body: no preceding operation line (§1.7)" | a chain, its continuation lines joined; the same E300 |
| `::UNTRUSTED{id:u1\|source:user\|role:objective\|effects:none\|delimiter:EOF_u1}` | §1.5 lists `::UNTRUSTED` in the v4.0 execution layer and says "`::END_UNTRUSTED` is a block terminator, not a declaration, and is not counted."; upstream `SPEC-v4.0-FINAL.md` §1: "Content inside is opaque text." | 0 errors (`consume_opaque`): the lines up to the delimiter are not read, `::GENE{opaque}` among them; with no delimiter line the block runs to the end of the document, 0 errors | shape `opaque`, the lines verbatim; no delimiter line: E300 (§9.1) |
| `::GRAMMAR{shape:inline\|conf:confirmed}` with `T:` and `E:` lines | §1.5: "**Meta (spec-authoring) declarations (3), counted separately**" | 0 errors | coded, class `meta` |

The dispatch of a body line, which the audit rows follow, is the BODY-SET clause of PATCH-2 §1.2: "T:form_is_determined_by_first_token|T:/A:⇒B1, `[`⇒B5_or_B8, `::`⇒B7, KEY:[⇒B4, KEY:…|…⇒B3, KEY:⇒B2, else⇒B6", with "A:body_line_matching_no_form_in_a_non_prose_declaration⇒E300". The validator adds readings that the clause does not list, and IML follows them: a `T[n]=value` bind and a temporal note are tolerated as body lines, a line starting with `→` is an annotation, a tolerated `::LATENCY` or `::CONFIDENCE` line is an annotation, and a `=>` line continues the operation above it (§4.5).

### 0.4 What stays text, and why

The canon tokenizes the declaration name, the block structure and an operation line. It does not tokenize the rest, and IML does not either.

- The content between the braces of a header has no single grammar in the canon. SPEC.md §2.1 writes `::STATE{@ENTITY, key:value}` with a comma and `::FACT{key:name|value:data|conf:level}` with pipes; §6.1 writes `::TRUST{@A→@B, 0.0→1.0}` and `::MEMORY{intact|degraded|zero}`; §6.4 nests braces, `::GENE_MUTABLE{id|T:trait|G:{Claude:val,Gemini:val}|Θ:gate}`; §6.9 writes `::IMMUNE{trigger⇒response}`; PATCH-2 §1.7 lets a narrative payload carry fields: "T:narrative_payload_braces_MAY_carry_pipe_separated_fields|first_segment=name", "T:subsequent_segments=`key:value`_fields_or_barewords|barewords_are_opaque_labels". The head is carried as the exact text between the braces.
- A body line other than B7 and B8 is defined by its first token only. B2 is "T:form=`KEY:value`" with "T:value=bareword|quoted_string|number|bool|free_text_to_end_of_line"; B6 is "T:form=free_text_line"; B5 is "T:form=`[TAG] text` | `[TAG:value]`" (PATCH-2 §1.2). The line is carried as its text.
- A brace span holds content, not structure: "T:braces_embedded_in_content_lines_are_content_not_structure" (PATCH-2 §1.1). Each content line is carried as its text.
- An opaque block is not read at all: "Content inside is opaque text." (upstream `SPEC-v4.0-FINAL.md` §1). Each opaque line is carried verbatim.
- The other top-level lines are metadata, notes or annotations with no inner grammar (the preamble lines are "T:preamble_lines_are_document_metadata|NOT_operations|no_E304", PATCH-2 §1.7), and colophon prose has no production at all. Each is carried as its text.

A code for any of these would be a grammar of IML's own, which decision A excludes. The text is copied without change and read back without change; a text never holds a line terminator, so every item keeps to its own lines (§2.3).

::CLAUSE{SCOPE|conf:confirmed|scope:iml-0.5}
T:owner_decision_A_2026-09-18=canon_not_changed|IML_carries_the_declaration_layer_in_machine_form|derives_everything_from_the_canon|registers_nothing_of_its_own
T:0.5=a_whole_raw_I-Lang_document|items=chain+declaration+text|message_form_unchanged
T:coded=declaration_names_of_PATCH-2_§1.5_and_§1.6|operation_lines_as_0.4_chains
T:made_explicit=block_shape|MODULE_second_segment|temporal_prefix|narrative_addressing|body_line_structure|one_level_of_nesting|opaque_block
T:carried_as_exact_text=header_content|body_lines_other_than_B7_and_B8|span_content_lines|opaque_lines|marker|tag_lines|temporal_binds_and_notes|annotations|tolerated_LATENCY_and_CONFIDENCE|colophon_prose
T:not_carried=layout|indentation+blank_and_dash_lines+trailing_whitespace+whitespace_at_the_structural_positions_of_declarations_and_chains|position_of_a_trailing_body_token_among_them
T:inner_whitespace_of_a_line_carried_as_a_text=content|a_TAB_there_E300
T:input_read_as_raw_I-Lang_with_or_without_the_marker|oracle_stated_for_documents_opening_with_the_marker
T:chain_layer_of_0.4_unchanged|chain_registry_0.2_file_kept_byte_for_byte|six_error_codes_unchanged
T:flow_constructs_still_gated_on_chain_syntax_in_the_canon
T:canon_audit_checked_2026-09-18|validator_answers_quoted_as_printed|opaque_block_row_rests_in_part_on_upstream_SPEC-v4.0-FINAL.md_not_vendored
A:tokenizing_header_content_or_body_text⇒a_grammar_of_IML's_own|contradicts_decision_A
A:declaration_name_coded_without_a_canon_source⇒contradicts_registers_nothing

---

## 1. Registry

0.5 derives one new table, the declarations, from the canon, and registers nothing of its own. Every verb root, key code and entity mark of 0.4 is kept as it was.

### 1.1 Two files

`registry/iml-registry-0.2.json` is kept byte for byte, digest `88d05d0839c1…`: it is the chain registry of 0.2, 0.3 and 0.4, and the registry that a 0.4 or a 0.3 header names (§3). The registry of 0.5 is a second file, `registry/iml-registry-0.5.json`. It has the same `canon`, `verbs`, `aliases`, `keys`, `entities` and `value_codes` members as the 0.2 file, `iml_version` `0.5`, and two new members, `declarations` and `tolerated_annotations`. Because the file differs, so does its digest: `7e29fae7f5eab384fd1588c23ac9860dbb387e5d66bd1be71343d0bc728d61ba`. A 0.5 header carries its first 12 hex characters, `7e29fae7f5ea`. The `iml_version` member names the vocabulary, as in 0.2; the version in a header is the surface version (§3).

### 1.2 Sources

`tools/derive_registry.py` derives both files from the canon at the pin and, with `--check`, verifies that both committed files reproduce. For the declarations it reads:

- PATCH-2 §1.5: the four bold headings of the structural layers ("**v3.0 communication layer (14)**", "**v4.0 execution layer (8)**", "**v5.0 judgment layer (9)**", "**Registered by amendment (1)**") and the backticked list under each, a list that may wrap over several lines; the heading "**Meta (spec-authoring) declarations (3), counted separately**" and its list; and the sentence "`::END_UNTRUSTED` is a block terminator, not a declaration, and is not counted.";
- PATCH-2 §1.6: the list of the 13 narrative declarations, and the sentence "`::LATENCY` and `::CONFIDENCE` appear as annotation lines in v3.0 §10.4 examples but are not defined in §7. They are treated as B2 field lines under their parent narrative declaration until formally registered.";
- SPEC.md §7.1: the code block, whose lines written with two brace pairs, `::SAY{@FROM→@TO}{content}` to `::CREATE{@ENTITY}{artifact}`, name the six double-brace narratives;
- PATCH-2 §1.2 B6: "T:current_prose_body_types=[::LESSON,::MODULE,::LIST,::RULE_annotation_body,::OBJECTIVE_narrative_fields]".

It checks the counts, 14, 8, 9 and 1 structural (32, the count of the DECL-COUNT clause, "T:structural_declarations=32|14_v3+8_v4+9_v5+1_amended"), 3 meta, 1 terminator and 13 narrative; 6 double-brace names; 5 prose-body names; 2 tolerated annotations. It cross-checks every set against the validator's `REGISTRY_V3`, `REGISTRY_V4`, `REGISTRY_V5`, `REGISTRY_AMEND`, `META_DECLS`, `TERMINATORS`, `DECL_NARRATIVE`, `NARR_DOUBLE`, `PROSE_BODY` and `TOLERATED_ANNOT`, and aborts on any difference.

Two readings are fixed by the validator where the canon's words leave room. First, the double-brace set: PATCH-2 §1.6 says of all 13 narrative declarations that the SOUL layer "uses double-brace form `::VERB{addressing}{content}`", while SPEC.md §7 adds "Single-brace forms (EVENT, SILENCE) have no addressing.", its §7.1 and §7.2 code blocks write `::EVENT`, `::SILENCE`, `::META`, `::IRONY`, `::FORESHADOW` and `::CALLBACK` with one brace pair, and SPEC.md writes `::EMOTION_FIELD` only in §10.5, `::EMOTION_FIELD{λ{trust:0.9, grief:0.3, resolve:0.8}}`, with no addressing pair. The six names written with two pairs in §7.1 are the validator's `NARR_DOUBLE`, and they are the registry's `double` names. Second, the prose-body set: the B6 list names `::RULE_annotation_body` and `::OBJECTIVE_narrative_fields`; the validator's `PROSE_BODY` holds `RULE` and `OBJECTIVE` whole, and the registry's `prose` flag does the same, so IML, like the validator, admits a B6 line anywhere in the body of those two.

### 1.3 Order and code assignment

The 49 names are taken in this order: the four structural lists of PATCH-2 §1.5 as they stand, the 14 of the v3.0 communication layer, the 8 of the v4.0 execution layer, the 9 of the v5.0 judgment layer and `LIST`; then its 3 meta declarations; then the terminator `END_UNTRUSTED`, whose sentence §1.5 places after the v4.0 list; then the 13 narrative declarations of PATCH-2 §1.6. Codes are assigned in that order, first come, first served, by the algorithm that assigns the verb roots (`SPEC-IML-0.4.md` §1.3): the name is upper-cased and every character outside `[A-Z0-9]` is dropped (`GENE_MUTABLE` is read `GENEMUTABLE`); with F its first character, the candidates are F followed by each consonant after it, left to right, then F followed by each vowel after it, then F followed by A to Z, then AA to ZZ; the first candidate not yet taken is the code. A consonant is any letter other than A, E, I, O, U, and any digit.

The declaration codes are a table of their own, with a fresh set of taken codes. A code is exactly two characters of `[A-Z0-9]` and stands only directly after the `:` that opens a declaration line (§2.2), so it may coincide with a verb root or an entity mark without ambiguity: 23 of the 49 codes are also verb roots and 9 are also entity marks; `ST`, for one, is the code of STATE, the root of STRM and the mark of `@STDIN`. No letter begins more than 26 of the 49 names, so the last stage is never reached.

### 1.4 Registry file

`registry/iml-registry-0.5.json` is JSON, UTF-8, `\n` line ends, object members sorted; lists keep canon order. Members:

- `iml_version`: `0.5`
- `canon`, `verbs`, `aliases`, `keys`, `entities`, `value_codes`: as in the 0.2 file (`SPEC-IML-0.4.md` §1.4), unchanged
- `declarations`: a list of 49 entries `{name, code, class, double, prose}` in the order of §1.3; `class` is one of `v3`, `v4`, `v5`, `amended`, `meta`, `terminator`, `narrative`; `double` is true for the six double-brace narratives; `prose` is true for the five prose-body names
- `tolerated_annotations`: `["LATENCY", "CONFIDENCE"]`
- `digest`: sha256 hex of the JSON serialised with `digest` absent, `sort_keys`, separators `(",", ":")`, `ensure_ascii` false, as in 0.2

### 1.5 The declarations table

Copied from `registry/iml-registry-0.5.json`; the file is authoritative.

| class | canon list | names | name and code |
|---|---|---:|---|
| `v3` | PATCH-2 §1.5, v3.0 communication layer | 14 | STATE `ST`, TRUST `TR`, ALIVE `AL`, MEMORY `MM`, GENE `GN`, GENE_MUTABLE `GM`, RULE `RL`, ACTIVATE `AC`, FACT `FC`, LESSON `LS`, PROGRESS `PR`, PRIORITY `PT`, DECAY `DC`, IMMUNE `IM` |
| `v4` | PATCH-2 §1.5, v4.0 execution layer | 8 | UNTRUSTED `UN`, BUDGET `BD`, STATUS `SS`, OBJECTIVE `OB`, RUBRIC `RB`, EVIDENCE `EV`, PRIOR `PI`, FALLBACK `FL` |
| `v5` | PATCH-2 §1.5, v5.0 judgment layer | 9 | JUDGE `JD`, BOUNDARY `BN`, DIM `DM`, MODE `MD`, FUNC `FN`, SCHEMA `SC`, CASE `CS`, CLAUSE `CL`, MODULE `ML` |
| `amended` | PATCH-2 §1.5, registered by amendment | 1 | LIST `LT` |
| `meta` | PATCH-2 §1.5, meta (spec-authoring) | 3 | GRAMMAR `GR`, BODY `BY`, REGISTRY `RG` |
| `terminator` | PATCH-2 §1.5, block terminator | 1 | END_UNTRUSTED `EN` |
| `narrative` | PATCH-2 §1.6 | 13 | SAY `SY`, THINK `TH`, ACT `AT`, DECIDE `DD`, DISCOVER `DS`, CREATE `CR`, EVENT `ET`, SILENCE `SL`, META `MT`, IRONY `IR`, FORESHADOW `FR`, CALLBACK `CB`, EMOTION_FIELD `EM` |

`double` is true for 6 names, SAY, THINK, ACT, DECIDE, DISCOVER, CREATE; `prose` is true for 5 names, RULE, LESSON, OBJECTIVE, MODULE, LIST. Every other entry has both false.

### 1.6 Tolerated annotations

`::LATENCY` and `::CONFIDENCE` are not registered: PATCH-2 §1.6 says they "are not defined in §7" and are treated as B2 field lines "until formally registered". The validator's `TOLERATED_ANNOT` tolerates them as one-line annotations wherever a declaration may stand, at the top level (optionally behind a temporal prefix) and as a body line, and reads nothing after the name: `::CONFIDENCE junk` passes with 0 errors. IML gives them no code. A line that starts with `::LATENCY` or `::CONFIDENCE` is a text, carried as written (§4.2, §4.5).

::CLAUSE{REGISTRY|conf:confirmed|scope:iml-0.5}
T:two_files|registry/iml-registry-0.2.json_kept_byte_for_byte_digest_88d05d0839c1|registry/iml-registry-0.5.json_new
T:0.5_file=the_0.2_members_unchanged+iml_version_0.5+declarations+tolerated_annotations|new_digest|header_carries_its_first_12_hex
T:declarations=49_names|14_v3+8_v4+9_v5+1_amended+3_meta+1_terminator+13_narrative|order_of_the_canon_lists
T:sources=PATCH-2_§1.5_headings_and_lists+meta_list+END_UNTRUSTED_sentence|PATCH-2_§1.6_list+LATENCY_CONFIDENCE_sentence|SPEC.md_§7.1_code_block_for_the_double_brace_names|PATCH-2_§1.2_B6_prose_body_types
T:cross_check=validator_REGISTRY_V3_V4_V5_AMEND+META_DECLS+TERMINATORS+DECL_NARRATIVE+NARR_DOUBLE+PROSE_BODY+TOLERATED_ANNOT
T:double=the_six_names_written_with_two_brace_pairs_in_SPEC.md_§7.1|as_the_validator
T:prose=LESSON+MODULE+LIST+RULE+OBJECTIVE|RULE_and_OBJECTIVE_whole_as_the_validator
T:code=2_characters_A-Z_0-9|verb_root_algorithm|fresh_table|stands_only_after_the_colon_that_opens_a_declaration_line
T:tolerated_annotations=LATENCY+CONFIDENCE|no_code|carried_as_text
T:registry_files_authoritative_for_every_code
A:validator_sets_or_counts_differ_from_the_parsed_sets⇒derivation_aborts
A:code_for_LATENCY_or_CONFIDENCE⇒registers_what_the_canon_has_not_registered
A:chain_code_changed_by_0.5⇒the_0.2_file_is_no_longer_byte_for_byte

---

## 2. Lexical structure

Every syntax character of IML 0.5 is ASCII. The content of a text, a head or a value is whatever UTF-8 text the I-Lang source carries, copied without change. An IML text is split into lines before anything else is read, and no line terminator ever stands inside a line (§2.3).

### 2.1 Grammar

```
iml       := message | document
message   := header SP chain NL?                      ; one chain on one line, as in 0.4
document  := header NL item (NL item)* NL?            ; the header alone, then the items; one final line terminator accepted
header    := "#iml/0.5/" HEX12                        ; HEX12 = the first 12 hex characters of the 0.5 registry digest; §3 names the other headers read
NL        := "\n"                                     ; "\r\n" is accepted as NL and printed as "\n"
SP        := " "                                      ; exactly one space
item      := chain | textline | decl
textline  := QUOTED                                   ; a top-level text
decl      := ":" DCODE prefix? sub? form (NL dline)*
DCODE     := [A-Z0-9]{2}                              ; a code from the declarations table
prefix    := "T" QUOTED                               ; the text inside T[...]; top level only; before sub (§2.2)
sub       := "::" NAME                                ; the second segment of ::MODULE::NAME; on the code of MODULE only
form      := QUOTED                                   ; shape brace or opaque: the head
           | QUOTED QUOTED                            ; shape brace, double-brace narrative: the addressing, then the head
           | QUOTED? "{"                              ; shape set; the QUOTED (the addressing) for a double-brace narrative only
           | QUOTED? "{" QUOTED                       ; shape wrapped: the addressing (double-brace narrative only), then the head
dline     := SP QUOTED                                ; brace: a text body line; set or wrapped: a content line; opaque: an opaque line
           | SP chain                                 ; brace: a B8 body line
           | SP ":" DCODE sub? nform                  ; brace: a nested declaration
           | SP SP QUOTED                             ; a text body line of the nested declaration just above
nform     := QUOTED | QUOTED QUOTED                   ; the two brace forms only
QUOTED    := '"' (escape | [^"\\])* '"'               ; escape := "\" ( '"' | "\" | "n" ); no raw control character; no "\n" escape in a text (§2.3)
chain     := op (SP op)*                              ; the chain of 0.4, unchanged:
op        := (ROOT (target | verbref)? | "$") mods?   ; "$" is OUT
ROOT      := [A-Z0-9]{2}                              ; a verb root from the registry
verbref   := ":" ROOT                                 ; only after the root of BATC
target    := "@" (MARK | "{" NAME "}")
MARK      := [A-Z0-9]{2}                              ; a registered entity mark
NAME      := [A-Z][A-Z0-9_]*
mods      := kv ("," kv)*
kv        := KEY "=" value
KEY       := [a-z]{2}                                 ; a key code from the registry
value     := quoted | entityref | code | bare         ; quoted: the QUOTED production, where "\n" is a newline
entityref := "@" (MARK | "{" NAME "}")
code      := "~" [a-z0-9]+                            ; always E303: every value-code table is empty
bare      := [^,"\\]+  with no whitespace and no control character, and not starting with "~", "@", "$", "\""
```

The chain productions are those of `SPEC-IML-0.4.md` §2.1, and its segmentation, typing and value rules (§2.2 to §2.5) apply to every chain, at the top level and on a body line alike. The rest is new in 0.5.

### 2.2 First-character dispatch

The first character of a line decides its kind, with no lookahead:

- `#`: the header, on the first line only. A later line that starts with `#iml/` is E502, "a second header in a document (one header, then one item per line)"; any other later line that starts with `#` is E300.
- `A` to `Z`, `0` to `9`, or `$`: a chain, read by the chain rules of 0.4.
- `"`: a text line, one quoted string and nothing after it.
- `:`: a declaration line.
- A space: a line of the declaration above. After the space, `"` opens a body line of a brace declaration, a content line of a span or an opaque line of an opaque block; a root character or `$` opens a B8 chain; `:` opens a nested declaration line; a second space and `"` open a body line of the nested declaration directly above. A line that starts with a space and has no declaration above it is E300, "a line that starts with a space belongs to the declaration above it: there is none"; a line that starts with two spaces and has no nested declaration directly above it is E300; so is any other character after the space, and any line but a quoted one under a span or an opaque block.
- Any other first character is E300, "a document line may not start with" followed by the character and the list above.

A declaration line is read from left to right. After `:`, exactly two characters of `[A-Z0-9]` are looked up in the declarations table; two such characters that are not a code there are E300, "unknown declaration code" followed by the two characters. Then, at the top level only, `T` and a quoted prefix. Then, on the code of MODULE only, `::` and a NAME, the second segment of the header (elsewhere `::` is E300). The prefix stands before the second segment, the reverse of their order in I-Lang (`T[3] ::MODULE::CORE{` is `:MLT"3"::CORE{`): a NAME is `[A-Z][A-Z0-9_]*`, so a segment written first would take the `T` of a prefix written after it. Then the form, which the `double` flag of the table decides: for one of the six double-brace narratives the first quoted string is the addressing and the head or `{` follows it; for every other name the first quoted string is the head, or the form is `{`, with or without a head after it. Then the end of the line: anything after the form is E300. The lines after a declaration line that start with a space belong to it; the first line that does not start with a space ends it. What those lines are depends on the shape (§4.4): body lines for a brace declaration, content lines for a span, opaque lines for an opaque block.

### 2.3 Texts

A text, a head, an addressing, a prefix, a content line and an opaque line are written as the quoted string of 0.4: `"` to `"`, with the escapes `\"` and `\\`. In 0.5 each of them is exactly one line of the source, so none of them ever holds a newline, and the escape `\n` inside one is E300, "a newline (the escape \n) inside a text line: a text never holds one", the message naming the part in which it was found. A raw control character inside one is E300, TAB included (U+0000 to U+001F, U+007F, U+0085, U+2028, U+2029, as in 0.4): the quoted string has no escape for it, so a source line that holds one has no spelling (§9.1). Leading whitespace of a source line is indentation, which is layout (§4.1), and is not part of the text; an opaque line is the exception, carried verbatim, so a TAB anywhere in it is E300. Inside a chain a quoted value keeps the rules of 0.4: `\n` there is a newline.

One spelling per AST: a head, an addressing, a prefix and a text are always quoted, even when empty, and are never written bare. `::SILENCE{}` is `:SL""`.

### 2.4 Lines

IML side: the line terminator is `\n`; `\r\n` is accepted and printed as `\n`; a `\r` anywhere else is a control character (E300). In a document a blank line is E300 and a trailing space on a line is E300, as in 0.4. The header is followed by at least one item: a header alone is E300.

I-Lang side: the input is split on `\n`, and one trailing `\r` per line is dropped. The indentation of a line is the number of whitespace characters before its first other character, as the validator counts it (`len(line) - len(line.lstrip())`). Trailing whitespace is dropped from a text line; the text is the line with its indentation and its trailing whitespace removed, an opaque line excepted (§4.7). A raw control character anywhere in a line is E300, "raw control character U+0085 in a document line (IML quoted strings have no escape for it)" with the character's code point, except a TAB that stands in layout (§4.1): in the indentation, in trailing whitespace, or in the whitespace that the validator strips at a structural position of a declaration, between a temporal prefix and the `::` of a declaration, between the name of a declaration and its `{`, and between a closing brace and a trailing body token. Of a line carried as a text nothing is removed but its indentation and its trailing whitespace: the whitespace inside it is content, so `T[0]   ::LATENCY{0}` and `T[0] ::LATENCY{0}` are two different texts, and a TAB inside it is E300 wherever it stands, in `T[0]`, a TAB and `::LATENCY{0}` as in `::LATENCY`, a TAB and `{0}`, which are texts and not declarations (§1.6, §9.1). A TAB inside any other carried text is E300 too (§9.1). The library functions refuse a U+FEFF at the head of their input (E502); the command line drops every leading byte order mark (0.4 and 0.5.0 dropped one; Windows PowerShell 5.1 pipes two when `[Console]::InputEncoding` and `$OutputEncoding` are both set to UTF-8).

::CLAUSE{LEXICAL|conf:confirmed|scope:iml-0.5}
T:syntax_characters_ascii|text_and_value_content_utf8_copied_without_change
T:grammar_0.5=grammar_0.4_chain+document_items|item=chain|textline|decl
T:first_character_of_a_line_decides_its_kind|hash_header|root_or_dollar_chain|quote_text|colon_declaration|space_a_line_of_the_declaration_above
T:declaration_line=colon+code+temporal_prefix+MODULE_segment+form|form_decided_by_the_double_flag
T:text=one_source_line_in_a_0.4_quoted_string|no_newline_escape|no_raw_control_character|always_quoted_even_when_empty
T:indentation_and_trailing_whitespace_are_layout|opaque_lines_verbatim|inner_whitespace_of_a_text_line_is_content
T:chain_rules_of_SPEC-IML-0.4.md_§2.2_to_§2.5_apply_to_every_chain_wherever_it_stands
A:unknown_declaration_code⇒E300
A:MODULE_segment_on_another_code|anything_after_the_form|illegal_first_character⇒E300
A:newline_escape_or_raw_control_character_in_a_text⇒E300
A:blank_line|trailing_space|header_without_an_item⇒E300

---

## 3. Headers and versions

The header is `#iml/0.5/` followed by 12 lowercase hex characters, the first 12 of the 0.5 registry digest (§1.1), `7e29fae7f5ea` at the pin. It stands in one of two places, as in 0.4:

- Message: the header, one space, one chain, on one line. A message carries a chain only: a declaration or a text in its place is E502, "declarations and text lines exist only in the document form (the header alone on its first line); a message carries one chain".
- Document: the header alone on the first line, then at least one item; the items are chains, texts and declarations (§4.1).

The form is decided by the first line: a header followed by a space is a message, a header followed by the end of the line is a document. The shape of a header is judged before its version and its digest, and the version before the form, as in 0.4 (`SPEC-IML-0.4.md` §3): a text that does not begin with `#iml/` has no header (E502); a text that begins with `#iml/` but does not match `^#iml/([0-9]+\.[0-9]+)/([0-9a-f]{12})( |$)` is E300.

Compile writes 0.5 only: a message and a document both carry `#iml/0.5/7e29fae7f5ea`, from the loaded 0.5 registry.

The default reader reads three headers:

- `#iml/0.5/` with the 0.5 digest prefix: the full document layer, chains, texts and declarations;
- `#iml/0.4/` and `#iml/0.3/` with the 0.2 digest prefix `88d05d0839c1`: chains only, read as 0.4 read them, so every 0.4 and 0.3 message and document decodes to the same chains as before. A declaration line or a text line under such a header, in a document or in place of the chain of a message, is E502, "declarations and text lines need a 0.5 header", the message going on with the version the header names.

A matched header whose 12 characters are not the digest prefix of the registry its version names is E502: a 0.5 header with `88d05d0839c1`, or a 0.4 header with `7e29fae7f5ea`, is refused. A matched header of any other version is E502; `#iml/0.2/` is E502 unless the 0.2 surface is requested (`--version 0.2`), which reads the 0.2 surface exactly as in 0.4 (one chain per message). The command line refuses `--version 0.3` and `--version 0.4` as a usage error, exit code 2, with a message that the default reader reads those headers; no IML error code is involved.

The two forms on the I-Lang side:

- `compile` (the message form) reads one chain per I-Lang line, continuation lines joined as in 0.4 (`SPEC-IML-0.4.md` §2.6), and writes one 0.5 message per chain. A line whose first non-blank characters are neither `[` nor `=>` (a declaration, a marker, a temporal bind or note, an annotation, prose) is E502, "carried in the document form: compile --document (a declaration or any other line that is not an operation chain has no message form)"; a line that starts with `[` is read as a chain, as in 0.4, so a tag line there is judged as an operation (`[TYPE:x]` is E304).
- `compile --document` reads a whole raw I-Lang document (§4), writes one 0.5 document, and reports an error at the line that holds it; an error of the check that reads the canonical print back (§6) names the item it belongs to and is reported at that item's first source line. In a document, whitespace before and after a chain line is layout, as the validator strips it; in the message form it stays E300, as in 0.4.
- `roundtrip` reads its file as a document: every chain of it through the message form, then the whole document through `compile --document`, `decompile` and the canonical print, an error of that pass being reported as `compile --document` reports it, at the first source line of the item it names.

A 0.4 or 0.3 document decompiled and compiled again carries the 0.5 header; the second equation of L2 (§6) is promised for documents the 0.5 codec produced.

::CLAUSE{HEADER|conf:confirmed|scope:iml-0.5}
T:header=#iml/0.5/+12_lowercase_hex_of_the_0.5_registry_digest
T:message=header+one_space+one_chain|document=header_alone+one_or_more_items
T:form_decided_by_the_first_line|shape_judged_before_version_and_digest|version_before_form
T:compile_writes_0.5_only|header_from_the_loaded_0.5_registry
T:default_reader=0.5_header_full_document_layer|0.4_and_0.3_headers_with_88d05d0839c1_chains_only
T:version_0.2_behind_the_flag_unchanged|command_line_refuses_version_0.3_and_0.4
T:compile_message_form=one_chain_per_I-Lang_line|compile_--document=a_whole_raw_I-Lang_document|roundtrip_document_pass_the_same
A:declaration_or_text_line_under_a_0.4_or_0.3_header⇒E502
A:digest_prefix_other_than_the_one_its_version_names|other_version|0.2_header_without_the_flag⇒E502
A:declaration_or_other_non_chain_line_given_to_compile_without_--document⇒E502
A:L2_second_equation_claimed_for_a_document_the_0.5_codec_did_not_produce⇒unsupported_claim

---

## 4. Declarations, texts and the document

The reader of an I-Lang document, `parse_doc`, reads a raw document as the validator's `lint_region` reads it, line by line, and builds the AST of §4.1. Every rule below names the validator function it follows; where IML is stricter than the validator, §9.1 lists the point and the validator's answer.

### 4.1 Items and the AST

A document is a list of items. The AST of 0.5 has three kinds of item:

- `Chain`: the chain of 0.4 (`SPEC-IML-0.4.md` §2.3), a list of operations `Op`.
- `Text(text)`: a line carried as exact text. At the top level: the document marker, a tag line, a temporal bind, a temporal note, an annotation line (`→`, `<<<`), a tolerated `::LATENCY` or `::CONFIDENCE` line (optionally behind a temporal prefix), colophon prose. In a body: every body line that is neither B7 nor B8, that is B1, B2 to B4, B5, B6, a temporal bind or note, a `→` annotation, and a tolerated `::LATENCY` or `::CONFIDENCE` line. The text is the source line with its indentation and its trailing whitespace removed; an opaque line is the one exception, kept verbatim.
- `Decl(name, sub, prefix, addr, shape, head, body, lines)`, a declaration:
  - `name`: a name of the declarations table (§1.5). `sub`: the second segment of a `::MODULE::NAME` header, or none. `prefix`: the text inside the brackets of a temporal prefix `T[...]`, or none; top level only. `addr`: the addressing of a double-brace narrative, the content of its first brace pair, or none.
  - `shape`: `brace` (the inline and header_body shapes of PATCH-2 §1.1; the body may be empty), `set` (a brace span whose header line ends with `{`), `wrapped` (a brace span with content after the opening brace, the wrapped field header), `opaque` (an `::UNTRUSTED` block with a delimiter, §4.7).
  - `head`: for `brace` and `opaque`, the content between the braces; for a double-brace narrative, the content of the second pair, from after its `{` to the last `}` of the line. For `wrapped`, the text after the opening `{` on the header line (after the second `{` for a narrative). For `set`, empty.
  - `body`, for `brace` only: a list of `Text`, `Chain` (a B8 line, its continuation lines joined, parsed by `parse_L2`) and nested `Decl` (a B7 line; shape `brace`, no prefix, `sub` on MODULE only, a body of `Text` only).
  - `lines`: for `set` and `wrapped`, the content lines, each with its indentation and trailing whitespace removed, the last line of a wrapped header without its closing `}`; for `opaque`, the lines between the header and the delimiter line, verbatim.

Layout is not carried, and layout is exactly this: indentation (its width, and a body written flush-left or indented); blank lines and `---` lines; trailing whitespace, a chain line's included; and the whitespace at the structural positions of a declaration and of a chain, which the validator strips: between a temporal prefix and the `::` of a declaration, between the name of a declaration and its `{`, after a closing brace (so the position of a same-line trailing body token, which becomes the first body line), and before a chain line and each of its continuation lines. Nothing else is layout. The whitespace inside a line carried as a `Text` is content: `T[0]   ::LATENCY{0}` and `T[0] ::LATENCY{0}` are two different texts, since a tolerated annotation is a text and not a declaration (§1.6), and a TAB inside a text is E300, in `T[0]`, a TAB and `::LATENCY{0}` as anywhere else (§2.4, §9.1). Two sources that differ only in layout have the same AST, the same IML and the same canonical print (§6, L3).

### 4.2 Top-level lines

Each line is judged in this order, which is the order of `lint_region`:

1. A blank line or a `---` line: layout. It ends a chain that continuation lines could extend.
2. The document marker, `::ILANG::<version>[::<name>]`, matched by `RE_DOC_MARKER`, `^::ILANG::\S+$`: a `Text`, allowed as the first or the last nonblank line only; elsewhere E300 "::ILANG document marker may only open or close a document (§1.7)". A declaration line whose name is `ILANG` and that is not a marker, such as `::ILANG::v5.0 x`, is E300 "malformed ::ILANG document marker: " followed by the line. PATCH-2 §1.7: "T:the_`::ILANG`_prefix_is_a_document_marker_not_a_declaration|registry_membership_unaffected".
3. A temporal bind, `T[n]=value` (`RE_TEMPORAL_BIND`, `^T\[[^\]]+\]=\S+`): a `Text`. PATCH-2 §1.7: "T:`T[n]=value`_line_binds_position_n_to_an_absolute_value".
4. A line starting with `::`, or a temporal prefix before one (`RE_TEMPORAL_PREFIX`, `^(T\[[^\]]+\])\s+(::.*)$`): a declaration (§4.3), or a `Text` when the name is `LATENCY` or `CONFIDENCE` (§1.6), and a `Text` too when a marker stands behind a temporal prefix, as in `T[0] ::ILANG::v5.0`, which the validator passes without a position check.
5. A line starting with `=>`: a continuation of the chain above (`SPEC-IML-0.4.md` §2.6); with no chain above it, E300 "orphan `=>` continuation: no preceding operation line".
6. A line starting with `[`. In preamble position, that is after the marker with only blank lines, binds and other tag lines between, a tag line is a `Text` even when a TAG is a verb name: `RE_TAG_LINE` on the line as `mask_quoted` returns it, and no `]=>` in it (PATCH-2 §1.7: "T:preamble_lines_are_document_metadata|NOT_operations|no_E304"). A line there that is not a tag line and is an operation line is a chain, as the validator reads it, with one exception of IML's own: a chain of one operation whose canonical print would be a tag line, `[Σ]`, `[Π:READ]` or `[Δ:@SRC]` (printed `[MERGE]`, `[BATC:READ]`, `[DIFF:@SRC]`), is E300, "a one-operation chain in preamble position prints as a tag line (PATCH-2 §1.7 preamble), which reads back as metadata", the message going on with the two ways to write it, after the preamble or with a second operation; its print would read back as a tag line, and the validator reads the source as an operation with 0 errors (§9.1). Elsewhere, as `check_bracket_line` reads it: an operation line when the masked line holds `]=>` or its head is a verb or an alias, then a `Chain`, its continuation lines joined; a tag line when `RE_TAG_LINE` matches, then a `Text`; otherwise E300 "bracket line is neither tag nor operation: " followed by the line.
7. A temporal note (`RE_TEMPORAL_NOTE`: `T[x]`, `T[a]→T[b]` or `PARALLEL{...}`, then anything): a `Text`. Nothing inside a note is read, as in the validator (§7.5 notation).
8. A line starting with `→` or `<<<`: an annotation, a `Text`.
9. Colophon prose: a line that holds none of `::` `[` `{` `}` `|` `⇒` `=>`, before the first construct (a line read by rule 4, or an operation line; markers, binds, tag lines, notes and annotations are not constructs): a `Text`.
10. Anything else: E300 "line matches no I-Lang production: " followed by the start of the line.

A line at the header's indent right after a declaration may instead be a flush-left body line of that declaration (§4.5); that reading comes first, as in the validator.

### 4.3 The declaration header

A declaration line is read as `parse_construct` reads it.

- The line, after an optional temporal prefix, must match `RE_DECL_HEAD`, `^::([A-Z][A-Z0-9_]*)(?:::([A-Z][A-Z0-9_]*))?(.*)$`; otherwise E300 "malformed declaration header: " followed by the line.
- A second segment is legal on `::MODULE` only (PATCH-2 §1.7: "T:compound_header=`::MODULE::NAME{`|the_sole_two_segment_declaration_name"); on any other name E300, with the validator's message, which names both segments and says that only ::MODULE takes a two-segment name, citing §1.7. It is carried as `sub`.
- The name must be one of the 49 names of the declarations table. `LATENCY` and `CONFIDENCE` make the line a `Text`, and nothing after the name is read (§1.6). Any other name is E300 "::WIDGET is not in the declaration registry (32 structural + 13 narrative, PATCH-2 §1.5/§1.6)", with the name in place of `WIDGET`.
- Entity tokens are scanned as `scan_entities` scans them: `@` directly after one of `{` `:` `|` `,` `→` `=`, followed by a letter; a lower-case first letter is E300 "entity `@bad_case` violates @[A-Z][A-Z0-9_]* (§2.2)", with the token in place of `@bad_case`.
- The rest of the line, whitespace before it being layout, must start with `{`: otherwise E300 "::FACT header lacks `{`", with the name in place of `FACT`.
- Full-width separators (PATCH-2 §1.3, "A:full_width_colon_or_pipe_as_structural_separator⇒E300|use_ASCII_`:`_and_`|`"): a `｜` anywhere in the rest is E300, and so is a `：` in a pipe-separated segment of the rest that holds no ASCII `:`, each with the validator's message, which names the full-width character as a structural separator, cites §1.3 and advises the ASCII one. A `：` beside an ASCII colon is content, as §1.3 allows: "T:CJK_full_width_punctuation_in_values_is_legal|（）：，、". The rest holds a same-line trailing body token too, so an ASCII colon of the token can share the segment of a `：` between the braces: `::GENE{b：c} src:x` passes the validator. The canonical print moves the token to a body line (§5), and the header line `::GENE{b：c}` would then fail the same check; so when a trailing token follows the closing brace, IML also runs the check on the braces alone, `{`, the head and `}`, and a hit is E300 with the validator's message and a note that the braces were checked alone (§9.1).
- The six double-brace narratives, `SAY THINK ACT DECIDE DISCOVER CREATE` (SPEC.md §7: "SOUL narrative verbs use double-brace form: `::VERB{addressing}{content}`"), need the rest to match `^\{[^{}]*\}\{.*\}\s*$`, the brace shape with an addressing, or `^\{[^{}]*\}\{[^}]*$`, a span; anything else is E300 "::SAY requires double-brace form ::VERB{addressing}{content} (v3.0 §7)", with the name in place of `SAY`. The addressing is carried as `addr`; it holds no brace.
- For every other name the shape is decided by the brace balance of the rest, as §4.4 says.

### 4.4 Shapes

PATCH-2 §1.1: "Every declaration takes one of exactly three shapes. Shape is determined by the header line, not by the declaration type." IML makes the shape explicit and splits the brace span in two, as the validator's `consume_brace_span` does.

- Brace (inline and header_body): the rest of the line has no more `{` than `}`. The head is the content up to the brace that matches the first `{` (`find_close`); for a double-brace narrative, the content of the second pair to the last `}` of the line. After the closing brace a single body token may trail on the same line, whitespace separated (FLUSH-LEFT-BODY: "T:a_single_body_form_token_MAY_trail_the_header_on_the_same_line|whitespace_separated"); it is read as a body line and becomes the first line of the body. The body follows (§4.5); it may be empty, which is the inline shape.
- Set span: the rest has more `{` than `}` and ends with `{` (trailing whitespace aside). Content lines follow, up to a line whose text is exactly `}`, which closes the span (PATCH-2 §1.1: "T:form=`::DECL{` + content_lines + `}`_on_own_line", "T:terminates_at_closing_brace_line|indentation_not_significant"). Content lines are texts: "T:braces_embedded_in_content_lines_are_content_not_structure".
- Wrapped field header: the rest has more `{` than `}` and does not end with `{`. The head is the text after the opening brace; content lines follow up to the first line whose text ends with `}`, which closes the header and is a content line itself, carried without that `}` (PATCH-2 §1.1: "T:wrapped_field_header|content_after_opening_brace_on_header_line⇒terminates_at_first_line_ending_with_`}`|v3.0_§10.3_style").
- Opaque: an `::UNTRUSTED` brace declaration whose head holds a delimiter (§4.7).

A span that never closes is E300 "::PRIORITY brace span never closes", with the name in place of `PRIORITY`. A span carries no body: "A:mixing_brace_span_and_header_body_in_one_declaration⇒E300" (SHAPE-SELECTION); the line after the closing line is read as a top-level line. A blank line inside a span is layout and is not carried. IML carries a set span only when the header line ends with the opening brace alone, `::NAME{` or `::NAME{addr}{`: text before a final `{`, as in `::PRIORITY{a{`, which the validator reads as a set span, has no place in the AST and is E300, "::PRIORITY set-span header carries text before its final `{`", the message going on with the two forms that open a set span (§9.1).

### 4.5 Body lines

The body of a brace declaration is collected as `consume_body` collects it, in one of two regimes fixed by its first line:

- Indented: the lines indented deeper than the header line (PATCH-2 §1.1, header_body: "T:body_indent>header_indent|any_consistent_width"). A blank line inside is permitted when the next nonblank line is still indented deeper ("T:blank_lines_inside_body_permitted_if_next_nonblank_line_still_indented"). The body ends at the first line indented no deeper than the header, or at a blank line followed by such a line, or at the end.
- Flush-left: lines at the header's indent that match a body form B1 to B5 (`is_body_form`: a `T:` or `A:` line; a `[` line matching `RE_TAG_LINE` or `RE_TAG_TEXT` on the masked line whose head is not a verb or alias; a `KEY:` line; a `T[n]=value` bind), ended by the first blank line, the next `::` line, temporal prefix or marker, or the first line that is not such a form (FLUSH-LEFT-BODY: "T:a_header_line_immediately_followed_by_lines_matching_body_forms_B1-B5_at_the_same_indent⇒header_body", "T:flush_left_body_terminates_at_first_blank_line_OR_next_`::`_header_line"). An operation line at the header's indent is not a body form and ends the body: it is a top-level chain.

Each body line is read by its first token, as `body_line` and `classify_body_line` read it:

- `::`: B7, a nested declaration (§4.6); a `::LATENCY` or `::CONFIDENCE` line is a `Text`.
- A temporal bind or a temporal note (`T[n] ::X{...}` among them): a `Text`.
- `→`: an annotation, a `Text`.
- `T:` or `A:`: B1, a `Text`.
- `=>`: a continuation line of the operation directly above it (below).
- `[`: B8, a `Chain`, when the masked line holds `]=>` or its head is a verb or an alias; B5, a `Text`, when `RE_TAG_LINE` or `RE_TAG_TEXT` matches the masked line; in a prose-body declaration a bracket-initial prose line, a `Text`; otherwise E300 "bracket body line is neither B5 tag nor B8 operation: " followed by the line.
- `KEY:`, a key matching `RE_KEY`, `^([A-Za-z_][A-Za-z0-9_]*):(.*)$`: B2, B3 or B4, a `Text`.
- Anything else: B6 prose, a `Text`, legal in a prose-body declaration only (`LESSON MODULE LIST RULE OBJECTIVE`, the registry's `prose` flag); elsewhere E300 "B6 prose body line inside non-prose ::GENE (§1.2 B6): " followed by the start of the line, with the name in place of `GENE`.

Entity tokens on B1 and on `KEY:` lines are scanned as in a header (§4.3), as `classify_body_line` scans them: `T:who:@nobody` is E300 "entity `@nobody` violates @[A-Z][A-Z0-9_]* (§2.2)".

A same-line trailing body token is read by the same dispatch, with two exceptions of IML's own: a token that starts with `::` is E300, "a same-line trailing body token that starts with `::` is not carried: write the declaration on its own line", and a token that starts with `=>` is E300, "a same-line trailing body token cannot be a `=>` continuation" (§9.1). An operation line as a trailing token is a chain.

Continuation lines in a body. A B8 line may wrap (PATCH-2 §1.7, "T:each_continuation_extends_the_chain_of_the_nearest_preceding_operation_line"). IML joins a `=>` body line to the operation line directly above it, after that line's own continuation lines, when the `=>` line is indented deeper than the header, and only when the text so far ends with `]` outside a quoted value, the rule of `SPEC-IML-0.4.md` §2.6 (otherwise E300, "continuation after an unterminated operation line"); the joined text is one `Chain`. A `=>` body line anywhere else is E300: after a blank line or another body line that stands between it and the operation line, "a `=>` continuation joins only the operation line directly above it (after that line's own continuations): a blank or another line stands between"; with no operation line before it in the body, "orphan `=>` continuation in ::GENE body: no preceding operation line (§1.7)", with the name in place of `GENE`, under a prose-body declaration too, where the validator lets such a line pass (§9.1).

### 4.6 Nesting

PATCH-2 §1.2 B7: "T:form=indented`::DECL{...}`_inside_parent_body", "T:one_level_of_declaration_nesting|deeper_declaration_nesting_undefined", "T:nested_declaration_MAY_carry_its_own_more_indented_B1-B6_body_lines|amended:2026-08-11". A `::` line in an indented body is a nested declaration, a `Decl` in the parent's body:

- its name is a structural or a narrative declaration, as the validator's `body_line` requires: any other name, a meta declaration and `END_UNTRUSTED` included, is E300 "nested ::GRAMMAR is not a registered declaration", with the name in place of `GRAMMAR`; `::LATENCY` and `::CONFIDENCE` lines are texts;
- it has the brace form on one line: a header without `{`, a span, and text after the closing brace are E300, "nested ::PRIOR: a nested declaration takes the brace form on one line (`::NAME{...}`, no span, no text after the closing brace)", with the name in place of `PRIOR`; a double-brace narrative needs its two pairs, as at the top level;
- it carries `sub` on MODULE only, E300 "nested ::STATE::X: only ::MODULE takes a two-segment name (§1.7)" otherwise, and never a temporal prefix: a body line `T[n] ::X{...}` is a temporal note, a `Text`, as the validator reads it;
- its own body is the lines indented deeper than it, up to the first blank line or the first line indented no deeper; each is read as a body line of the nested declaration, and only B1 to B6 (with binds, notes and `→` annotations) are legal there: a `::` line is E300 "declaration nesting exceeds one level (§1.2 B7)", and a B8 line or a `=>` line is E300, "the body of nested ::PRIOR carries B1 to B6 lines only: an operation line (B8) or a `=>` line there is not carried" (§9.1).

The canon leaves deeper nesting "undefined"; the validator's `body_line` rejects it with the E300 above, and IML does the same. The validator reads the nested body with `classify_body_line`; the points where IML is stricter there are listed in §9.1.

### 4.7 Opaque blocks

A top-level `::UNTRUSTED` declaration of the brace shape whose header line holds `delimiter:X`, found by the validator's pattern `delimiter:([^|}\s]+)` in the rest of the line, opens an opaque block, as `consume_opaque` reads it; a same-line trailing body token after such a header is E300, "a same-line trailing body token after an ::UNTRUSTED header with a delimiter is not carried" (§9.1). In the block, every line after the header up to the first line whose text, stripped, is exactly `X` is an opaque line, carried verbatim in `lines`, a blank line included (it is carried as `""`); that delimiter line closes the block and is not carried, since the head holds it. Upstream `SPEC-v4.0-FINAL.md` §1 at the pin: "Content inside is opaque text. `::GENE`, `[RUN:]`, `::STATUS` appearing inside are NOT parsed". Nothing in an opaque line is read, a line that looks like a declaration or an operation included. A document that ends before the delimiter line is E300 (§9.1). `::END_UNTRUSTED`, which usually follows, is a declaration line of its own (class `terminator`). A nested `::UNTRUSTED` opens no block: the validator's `body_line` reads it as any nested declaration, and so does IML.

### 4.8 Temporal prefix and MODULE segment

A temporal prefix binds a top-level declaration to a timeline position (PATCH-2 §1.7: "T:form=`T[n]`_whitespace_declaration|binds_the_declaration_to_timeline_position_n", "T:extends_v3.0_§7.5_temporal_notation|the_prefix_is_a_marker_not_a_declaration"). IML carries the text inside the brackets as `prefix`, and the lines indented deeper attach to the declaration by the header_body rules ("T:lines_indented_deeper_than_the_prefixed_line_attach_to_that_declaration|header_body_rules"). The whitespace between `]` and `::` is layout. A `::LATENCY` or `::CONFIDENCE` line behind a prefix is a `Text`, prefix included.

The second segment of `::MODULE::NAME` is carried as `sub`, written after the code of MODULE, and after the prefix when there is one (§2.2), as `::NAME`. PATCH-2 §1.7 gives MODULE the brace span, "T:shape=brace_span|body=B5_tag_lines+B6_prose|declared_prose_body_type_per_§1.2_B6"; the shape is still decided by the header line, as for every declaration.

::CLAUSE{DECLARATIONS|conf:confirmed|scope:iml-0.5}
T:document=list_of_items|Chain+Text+Decl|read_as_the_validator_reads_raw_mode_lint_region
T:Decl=name+sub+prefix+addr+shape+head+body+lines|shape=brace|set|wrapped|opaque
T:Text=exact_text_of_one_line|indentation_and_trailing_whitespace_removed|opaque_lines_verbatim
T:top_level_order=blank|marker|bind|declaration|continuation|bracket_line|note|annotation|colophon_prose|else_E300
T:preamble_tag_lines_are_texts_even_when_a_tag_is_a_verb_name|a_one_operation_chain_there_whose_print_is_a_tag_line_is_E300
T:full_width_check_also_on_the_braces_alone_when_a_same_line_trailing_token_follows
T:header=RE_DECL_HEAD|MODULE_only_takes_a_second_segment|registered_name|LATENCY_and_CONFIDENCE_are_texts|entity_scan|opening_brace|full_width_separators|double_brace_for_the_six
T:shape_by_brace_balance|set_span_closes_at_a_bare_closing_brace_line|wrapped_header_closes_at_the_first_line_ending_with_a_closing_brace
T:body_regime=indented_or_flush_left_B1_to_B5|trailing_body_token_is_the_first_body_line
T:body_line_by_first_token=B7_nested_declaration|B8_chain|B1_to_B6_binds_notes_annotations_texts|B6_only_in_prose_body_declarations
T:body_continuation_joins_the_operation_line_directly_above_it|after_a_closed_operation_only
T:nesting=one_level|brace_shape_only|no_prefix|MODULE_segment_only|body_B1_to_B6_texts_only
T:opaque=UNTRUSTED_with_a_delimiter|lines_verbatim_up_to_the_delimiter_line|never_read
T:layout_not_carried=indentation|blank_and_dash_lines|trailing_whitespace|whitespace_at_the_structural_positions_of_declarations_and_chains|inner_whitespace_of_a_text_is_content
A:unregistered_name|second_segment_off_MODULE|header_without_an_opening_brace|full_width_separator|narrative_without_two_brace_pairs|span_never_closed⇒E300
A:B6_prose_in_a_non_prose_body|bracket_body_line_neither_tag_nor_operation|orphan_or_detached_continuation⇒E300
A:nesting_beyond_one_level|nested_span|nested_operation_line|opaque_block_without_its_delimiter_line⇒E300

---

## 5. Canonical I-Lang print (decompile output)

`print_doc` writes a document AST as I-Lang: the items in order, one construct per line group, with no `---` line and with no blank line but one kind: a blank line stands between a top-level declaration of the brace shape with an empty body and a following top-level text that is a body form (a tag line or a temporal bind). Without it that text would bind as the declaration's flush-left body when the print is read again (§4.5), and the print would not read back to the same AST.

- A `Text` prints as its text: at column 0 at the top level, at its body's indent in a body.
- A `Chain` prints as in 0.4 (`SPEC-IML-0.4.md` §5.1), on one line, whatever the layout of its source; the canonical print never writes a continuation line.
- A `Decl` of the brace shape prints its header line, `T[<prefix>] ` when it has a prefix, then `::NAME`, then `::SUB` when it has one, then `{head}`, or `{addr}{head}` for a double-brace narrative; then its body lines, each on its own line indented by two spaces: a text, a chain on one line, or a nested declaration, whose own body lines are indented by four.
- A set span prints `::NAME{` (`::NAME{addr}{` for a narrative), the content lines indented by two spaces, and `}` alone at the header's indent, column 0.
- A wrapped field header prints `::NAME{head` (`::NAME{addr}{head` for a narrative), then the content lines indented by two spaces, the last one followed by `}`, or a bare `}` at the header's indent when the text of the last line is empty.
- An opaque block prints its header line as a brace declaration, then the opaque lines verbatim, with no indentation added, then the delimiter alone on its line.

A same-line trailing body token prints as the first body line, and a flush-left body prints indented: layout is not carried (§4.1), and the print writes one layout. The print of a document that the codec accepted is read by the validator with 0 errors, the media gating of chains excepted (§6, the oracle).

::CLAUSE{PRINT|conf:confirmed|scope:iml-0.5}
T:items_in_order|one_construct_per_line_group|no_dash_line|one_blank_line_only_between_a_bodyless_brace_declaration_and_a_following_body_form_text
T:text_prints_as_its_text|chain_prints_as_0.4_on_one_line
T:brace_declaration=optional_temporal_prefix_one_space+name+MODULE_segment+braced_head_or_addressing_and_head|body_lines_indented_two_spaces|nested_body_four
T:set_span=name_and_opening_brace|content_lines_at_two_spaces|closing_brace_alone_at_column_0
T:wrapped_header=name_brace_head|content_lines_at_two_spaces|closing_brace_after_the_last
T:opaque_block=header|opaque_lines_verbatim|delimiter_alone
T:trailing_token_prints_as_the_first_body_line|flush_left_body_prints_indented
A:print_reproduces_the_source_layout⇒not_canonical

---

## 6. Laws and the oracle

Let `parse_doc` read a raw I-Lang document into the AST of §4.1, `print_doc` write it (§5), `compile_doc` write a document AST as an IML 0.5 document, and `decompile_doc` read an IML document back to the AST; these are the library functions `iml.parse_doc`, `iml.print_doc`, `iml.compile_doc` and `iml.decompile_doc`, which `compile --document`, `decompile` and `roundtrip` call on the command line.

- L1 (document): `decompile_doc(compile_doc(parse_doc(x))) == parse_doc(x)` for every I-Lang document x the codec accepts. AST equality compares every field of §4.1: items in order, the chain of 0.4 by its own equality (`SPEC-IML-0.4.md` §6), a text by its text, a declaration by name, sub, prefix, addr, shape, head, body and lines.
- L2 (canonical text): `print_doc(parse_doc(print_doc(d))) == print_doc(d)` for every document AST d that `parse_doc` or `decompile_doc` returned (`print_doc` does not validate: an AST built by hand is checked by `compile_doc`, not by the print), and `compile_doc(decompile_doc(m)) == m` for every IML document m that the codec produced.
- L3 (original bytes): not promised. Layout (§4.1) is not carried, and the chain spellings of 0.4 (aliases, `[OUT]` for `[Ω]`, quotes around a bare value, the surface, a chain written on several lines) are spelling, as in 0.4.
- The chain laws of 0.4 hold for chains and messages, unchanged: a chain compiled as a message under the 0.5 header and a chain inside a document are the same AST.

Decompile validates by round trip. After an IML document is decoded, the AST is printed with `print_doc` and read again with `parse_doc`: an error there is reported as it is, and an AST that differs from the decoded one is E300, "not the canonical spelling of a construct", the message going on with the index of the item and what it reads back as. `compile_doc` makes the same check before it writes. So an IML text that decodes to something the I-Lang reader would read otherwise is refused: for example a text line whose text is a registered declaration, `"::FACT{key:a|value:b}"`, which a declaration line must carry. A one-operation chain in preamble position whose print is a tag line, `MR` after the text line of the marker, reads back as that tag line; the decoder refuses it with the message that `parse_doc` gives its I-Lang source (§4.2), and `compile_doc` does the same for such an AST. Every error of this check names the item it belongs to, and the command line reports it at that item's first source line (§7). Compile writes one spelling per AST; the decoder also reads quotes around content that could be bare, as the I-Lang reader does (a quoted value and the same content bare decode to equal ASTs), so the second equation of L2 is promised for documents the codec produced.

The oracle is the pinned validator, not the codec's own tests. For every document that begins with a `::ILANG::` marker and that the codec accepts, the validator, in raw mode, reports 0 errors on the input and 0 errors on its canonical print, with one exception: a chain that uses a media profile key on a target that is not a media entity, which the validator reports as E302 and the codec, leaving media gating to the validator, accepts (`SPEC-IML-0.4.md` §0.2). For every malformed document that the validator rejects, the codec rejects it too, with the same exception. The converse does not hold: §9.1 lists what the validator accepts and the codec refuses. Warnings are not part of the oracle: IML applies none of the WARN-level checks (§9.2).

Tests (`python -m unittest discover -s tests`, 153 tests):

- The registries (`tests/test_registry.py`, `tests/test_registry_05.py`): the 0.2 file byte for byte; the declarations table parsed from the canon text, cross-checked against the validator's sets, with its counts, flags and the 49 codes as derived; a derivation with a changed count aborts; a tampered or mismatched registry is refused.
- The validator's rules as the codec restates them (`tests/test_doc_lex.py`): every pattern, helper and message of `iml/doc_lex.py` is checked against the pinned validator itself.
- `parse_doc` and `print_doc` (`tests/test_doc_parse.py`): shapes, bodies, top-level lines, layout that is not carried, the canonical print and its one blank line, control characters and line ends, the validator's self-test document, the messages that follow the validator, and the inputs of the review of v0.5.0 (a full-width colon that a trailing token hides, a one-operation chain in preamble position, the whitespace inside a text line, the first source line of every item).
- The document form (`tests/test_doc_codec.py`): the line grammar, headers and versions, hand-built ASTs, decompile validated by round trip, the message form refusing declarations, a declaration or text line in a 0.4 or 0.3 message (E502), the decoder's message for a preamble chain, and the command line, the line at which `compile --document` and `roundtrip` report an error of the canonical check included.
- The golden documents (`tests/test_golden_05.py`): 20 pairs `NNN.ilang` and `NNN.iml` in `corpus/golden-0.5/`, each I-Lang document opening with a `::ILANG::` marker; the compile output as recorded, L1 and L2, coverage of every declaration name and every shape, canon text kept verbatim, and the validator on every source and every canonical print (raw mode, 0 errors).
- Generated documents (`tests/test_doc_random.py`, `tests/doc_generator.py`): 2,000 raw I-Lang documents (seed 20260918; 53,084 source lines, 17,572 items) covering every shape, body form, nested declarations, spans, opaque blocks, text lines, chains with continuation lines and layout, each under L1 and L2 with the validator on the source and on the print (0 errors); then 1,000 mutated documents, where whatever the codec accepts the validator accepts too. The generator is not the oracle.
- The malformed corpus (`tests/test_malformed.py`): 266 cases, 79 of them added in 0.5.0 (43 compile-document, 2 decompile, 34 decompile-document) and 19 in 0.5.1 (16 compile-document, 2 decompile, 1 decompile-document), with the validator as oracle on the document cases (§9.1).
- The tests of 0.4.1 (`tests/test_codec.py`, `tests/test_flow.py`, `tests/test_golden_04.py`, `tests/test_roundtrip.py`), kept: the 72 golden chains, the 0.4 golden corpus, 10,000 generated chains on the 0.5 surface and the 6,394 of them that have a 0.2 spelling on the 0.2 surface, the document law on 100 documents of chains, a 500-chain sample checked by the validator; since 0.5.1 also a chain of 20,000 lines joined and parsed in linear time, and every leading byte order mark dropped by the command line. Where they compared what compile writes with a 0.4 text, they now expect that text under the 0.5 header, and the 0.4 files stay on disk as the record.

::CLAUSE{LAWS|conf:confirmed|scope:iml-0.5}
T:L1=decompile_doc(compile_doc(parse_doc(x)))==parse_doc(x)|for_every_document_the_codec_accepts
T:L2=print_doc_idempotent_on_every_AST_that_parse_doc_or_decompile_doc_returned|compile_doc(decompile_doc(m))==m_for_every_codec_produced_m
T:compile_writes_one_spelling_per_AST|the_decoder_also_reads_quotes_around_content_that_could_be_bare
T:L3_not_promised|layout_and_the_chain_spellings_of_0.4_are_spelling
T:chain_laws_of_0.4_unchanged_for_chains_and_messages
T:decompile_validates_by_round_trip|print_then_parse_again|a_differing_AST_is_E300|every_error_names_its_item
T:oracle=pinned_validator_in_raw_mode|0_errors_on_input_and_on_print_for_every_accepted_document_opening_with_the_marker|every_document_the_validator_rejects_is_rejected
T:oracle_exception=media_gating_of_chains|validator_E302|codec_accepts
T:converse_does_not_hold|§9.1_lists_what_the_validator_accepts_and_the_codec_refuses
T:warnings_outside_the_oracle
A:round_trip_claimed_for_a_text_the_codec_refuses⇒unsupported_claim
A:original_bytes_or_source_layout_claimed⇒contradicts_L3
A:text_line_that_spells_a_registered_declaration⇒E300_on_decompile

---

## 7. Errors

The codec fails closed; the first error stops it. Codes reuse §9 of the canon. The codec raises the six codes of 0.4 and no other; 0.5 adds rows, not codes. Where the validator has a wording for a case, the codec's message follows it, the backticks around a quoted token included; the codec carries the messages that contain a dash whole, and this text describes them (see Notation).

| Code | Canon name | Raised when |
|------|------------|-------------|
| E300 | Syntax Error | every E300 of 0.4 (`SPEC-IML-0.4.md` §7), in a chain wherever it stands; new in 0.5, on the I-Lang side: a line that matches no production (§4.2), with the validator's wording for each case: a marker off the first and the last nonblank line, a malformed marker, a malformed declaration header, a second segment on a name other than MODULE, a name outside the registry, a lower-case entity token, a header without `{`, a full-width separator, a double-brace narrative without its two pairs, a span that never closes, an orphan `=>` line, a bracket line that is neither tag nor operation, a B6 line in a non-prose body, a bracket body line that is neither B5 nor B8, nesting beyond one level, a nested name outside the structural and narrative sets; and every point of §9.1; on the IML side (§2): a line whose first character is not one of `"` `:` a space `$` `A`-`Z` `0`-`9`, an unknown declaration code, `::` after a code other than MODULE's, a temporal prefix or a span on a nested declaration line, anything after the form, a `\n` escape or a raw control character in a text, a line that starts with a space and belongs to no declaration, a line that starts with two spaces and follows no nested declaration, a decoded document that is not the canonical spelling of its AST (§6) |
| E304 | Unknown Verb | as in 0.4, in a chain wherever it stands |
| E302 | Invalid Modifier | as in 0.4 |
| E200 | Entity Not Found | as in 0.4 |
| E303 | Invalid Value | as in 0.4 |
| E502 | Unsupported Format | every E502 of 0.4; new in 0.5: a declaration or a text line under a 0.4 or 0.3 header, in a document or in a message ("declarations and text lines need a 0.5 header"); a declaration or a text in place of the chain of a 0.5 message ("declarations and text lines exist only in the document form"); a line that is not an operation line given to `compile` in the message form ("carried in the document form: compile --document") |

Reading of the table. Every E300 of the I-Lang side of 0.5 carries the validator's wording, for a case the validator also rejects, or stands in §9.1, for a case the validator accepts; the IML side adds the rows of §2. Offsets are those of 0.4, a 0-based character index into the whole input text. On the command line an error is reported as `<file>:<line>: <error>`, the line being the one that holds the offset; in the message form of `compile` it is the chain's first line, as in 0.4. An error of the check that reads the canonical print back (§6), which `compile --document` and the document pass of `roundtrip` make, is reported at the first source line of the item it names, whatever its offset, which counts in the print and not in the source. No error is reported at line 0. The command line refuses `--version 0.3` and `--version 0.4` as a usage error, not with an IML error code (§3).

::CLAUSE{ERRORS|conf:confirmed|scope:iml-0.5}
T:fail_closed|the_first_error_stops_the_codec
T:codes=SPEC.md_§9|E300+E304+E302+E200+E303+E502|no_other_code|0.5_adds_rows_not_codes
T:messages_follow_the_validator_where_it_has_a_wording|backticks_included
T:new_E300_rows=every_structural_error_of_§4|every_point_of_§9.1|unknown_declaration_code|illegal_first_character|newline_escape_or_control_character_in_a_text|not_the_canonical_spelling_on_decompile
T:new_E502_rows=declaration_or_text_line_under_a_0.4_or_0.3_header|declaration_or_text_in_a_0.5_message|non_chain_line_given_to_compile_without_--document
A:unknown_declaration_code_guessed_or_skipped⇒violates_fail_closed
A:error_code_registered_by_IML⇒contradicts_registers_nothing

---

## 8. Measurement

`tools/measure.py` writes `measurements/0.5-YYYY-MM-DD.md`; the report of this release is `measurements/0.5-2026-09-18.md` (Python 3.13.15, tiktoken 0.14.0). For each of the 20 documents of `corpus/golden-0.5/` it records bytes (UTF-8), characters, and tokens under `cl100k_base` and `o200k_base` (offline cache) for three texts: the I-Lang document as written (the `.ilang` file on disk, its layout included), its canonical print (§5), and the IML 0.5 document (the `.iml` file on disk, which equals what `compile_doc` writes, checked when the report runs). For the 72 chains of `corpus/golden/` and the 36 of `corpus/golden-0.4/` it records the forms of the 0.4 report under the 0.5 header, with the 0.4 texts as the record, and it records the cost of `RULE-SHEET.md` as it stood on disk and at every release tag. The report gives totals, per-form means, and one row per document and per chain. Totals from the report:

| form | bytes | chars | cl100k_base | o200k_base |
|------|---:|---:|---:|---:|
| I-Lang as written, 20 documents of `corpus/golden-0.5/` | 15235 | 15050 | 5246 | 5187 |
| I-Lang canonical print, 20 documents | 15378 | 15194 | 5345 | 5290 |
| IML 0.5 document, 20 documents | 15210 | 15034 | 5526 | 5500 |
| I-Lang canonical print, 72 chains of `corpus/golden/` | 4462 | 4395 | 2040 | 2134 |
| IML 0.5 message (one header per chain), 72 chains | 4506 | 4502 | 2510 | 2509 |
| IML 0.5 document (one header for the 72 chains) | 3015 | 3011 | 1316 | 1314 |
| JSON baseline, 72 chains | 8334 | 8330 | 3195 | 3262 |
| IML 0.5 message (one header per chain), 36 chains of `corpus/golden-0.4/` | 1738 | 1738 | 1050 | 1047 |
| IML 0.5 document (one header for the 36 chains) | 1003 | 1003 | 462 | 459 |

The golden documents carry 175 items at top level (38 text lines), 137 declarations of which 6 nested, 10 chains (top level and in bodies), 159 text lines in bodies; they are 444 lines as written, 383 in the canonical print, 392 in the IML documents (the header line included). The 0.5 header, `#iml/0.5/7e29fae7f5ea`, is 21 bytes like the 0.4 header, and 17 tokens under either encoding where `#iml/0.4/88d05d0839c1` is 16, because its 12 hex characters differ; so each 0.5 message of the chain corpora is one token above its 0.4 record (72 chains: 2,510 against 2,438 `cl100k_base`), a 0.5 document one token above in all (1,316 against 1,315), and bytes and characters are unchanged. On the golden documents the IML 0.5 documents total 5,526 `cl100k_base` tokens, the I-Lang sources as written 5,246 and their canonical prints 5,345 (`o200k_base`: 5,500, 5,187, 5,290); in bytes the three are 15,210, 15,235 and 15,378. The IML document is above both I-Lang forms in tokens under both encodings, and the fact is not called anything more than that.

The rule sheet. The ceiling of `RULE-SHEET.md` rises from the 1,800 `cl100k_base` tokens of 0.4 to 2,600, because the sheet now carries the declarations table, 49 names with their codes, and the document rules; the ceiling is a limit on the sheet, not a figure about IML. The 0.5 sheet, unchanged in 0.5.1, is 8,639 bytes, 8,609 characters, 2,596 `cl100k_base` and 2,591 `o200k_base` tokens; the sheet at the tag v0.4.1 was 6,090, 6,064, 1,798 and 1,796. The record rows of the report are the sheet at every release tag from v0.2.0 to v0.5.0, read with `git show <tag>:RULE-SHEET.md` and measured when the report runs (a tag that cannot be read gives a row marked not measured); in `cl100k_base` tokens: 1,364 at v0.2.0, 1,619 at v0.2.1 and v0.2.2, 1,792 at v0.3.0, 1,767 at v0.3.1, 1,796 at v0.4.0, 1,798 at v0.4.1, 2,596 at v0.5.0. The report of 0.5.0 copied its record rows from the earlier reports, and one of them, a 0.2 sheet of 1,607 tokens, matches no tagged sheet.

No figure carries a claim; the table is the table. The report states the tokenizer scope: named encodings, not any vendor's billing. If tiktoken is missing, the tool writes bytes and characters and says that tokens were not measured. ROADMAP.md gates any efficiency claim on a larger corpus, more tokenizers, the rule sheet and the reply, and that gate is unchanged and not met.

::CLAUSE{MEASURE|conf:confirmed|scope:iml-0.5}
T:tools/measure.py_writes_measurements/0.5-YYYY-MM-DD.md|this_release=measurements/0.5-2026-09-18.md
T:units=bytes_utf8+characters+tokens_cl100k_base+tokens_o200k_base|tiktoken_offline_cache|named_encodings_not_a_vendor_billing
T:golden-0.5=I-Lang_document_as_written+its_canonical_print+the_IML_0.5_document|per_document_and_totals
T:72_chain_figures_under_the_0.5_header|0.3_and_0.4_reports_stay_as_the_record
T:rule_sheet_as_on_disk+at_every_release_tag_read_with_git_show|ceiling_raised_from_1800_to_2600_cl100k_base_for_the_declaration_table_and_the_document_rules
A:figure_called_a_saving⇒violates_the_ROADMAP_gate
A:figure_published_without_corpus_tokenizer_and_both_baselines⇒unsupported_claim

---

## 9. Stricter than the validator, and outside 0.5

### 9.1 Where IML is stricter than the validator

The validator reads a raw document leniently in places where IML keeps one spelling per AST, cannot spell the input, or keeps to the words of the canon. Each point below was probed on 2026-09-18 against the pinned validator (`--lint`, raw mode, one probe per file, each probe opening with `::ILANG::v5.0`) and against the codec; the validator's answer is quoted as printed. The malformed corpus carries these points as document cases whose label starts with "stricter:", 33 of them, 16 of which 0.5.1 added after the review of v0.5.0; the tests lint each with the validator (0 errors, raw mode) and give it to the codec, which refuses it, and they check that every other document case opening with the marker is rejected by both. The first three rows are the chain cases of 0.4: the first two stand in the corpus as chain cases of the direction `compile`, the third as document cases. One row has no case in the corpus: a same-line trailing token that is a `=>` line.

| Input | Validator answer | IML 0.5 |
|---|---|---|
| a chain, at the top level or on a body line, with one of the spellings of `SPEC-IML-0.4.md` §0.3: whitespace inside an operation (`  [READ: @SRC]=>[Ω]` in an `::ACTIVATE` body), `[BATC:]`, `[BATC:READ\|]`, a dangling `=>`, a space after `=>` on a continuation line, a `=>` line under a line that ends in `=>` | 0 errors | E300, as in 0.4 ("whitespace is not allowed outside a quoted value" for the first) |
| OUT before the last operation, `[Ω]=>[FMT]`; two chains on one line, `[READ]=>[Ω] [FMT]=>[Ω]` | 0 errors | E502, as in 0.4 |
| any other operation line outside the 0.4 subset (`SPEC-IML-0.4.md` §0.3 and §7), at the top level or on a body line: an empty value, `[READ\|fmt=]`; a bad escape, `[READ\|path="a\d"]`; a missing `[`, `[READ]=>FMT]`; a modifier without `=`, `[READ\|fmt=md,f]`; an unterminated operation, `[READ]=>[OUT`; a `\|` between modifiers, `[READ\|fmt=a\|lng=b]`; OUT as a verb reference, `[BATC:OUT]` and `[Π:Ω]`; an entity name outside `[A-Z][A-Z0-9_]*`, `[READ\|ton=@Xmd]`; a reserved character in a bare value, `[READ\|fmt=c:\d]` | 0 errors for each | the code and the message of 0.4: E300 for the first six ("empty value for key fmt", "bad escape `\d` in quoted value", "expected `[` to open an operation", "modifier lacks `=`", "unterminated operation: `]` missing", "stray `\|`: modifiers are separated by commas"), E502 for OUT as a verb reference ("OUT cannot be batched: not representable in IML"), E200 for the entity name, E303 for the reserved character |
| a TAB inside a carried text: inside the braces of `::FACT{...}`, inside a body line `T:...`, anywhere in an opaque line | 0 errors | E300 "raw control character U+0009 in the header of ::FACT (IML quoted strings have no escape for it)", the message naming the part; a TAB in layout is accepted (§2.4) |
| a TAB inside a line carried as a text, where a declaration would have layout: `T[0]`, a TAB and `::LATENCY{0}`; `::LATENCY`, a TAB and `{0}` | 0 errors: the validator strips the whitespace after a temporal prefix and after a name, and reads nothing after a tolerated name | E300 "raw control character U+0009 in a text line (IML quoted strings have no escape for it)": the line is a text, and the whitespace inside a text is content (§2.4, §4.1) |
| another raw control character inside a line: U+000B, U+0085, U+2028, a CR not before `\n` | 0 errors: the validator's `str.splitlines` reads these as line breaks | E300 "raw control character U+0085 in a document line (IML quoted strings have no escape for it)" |
| a continuation under a line break inside a quoted value whose `]` stands inside the quotes: `[READ\|whr="a]` then `  =>b"]`, at the top level or in a body | 0 errors: the masked line holds the operation, and the continuation holds no bracket group | E300 "continuation after an unterminated operation line", the 0.4.1 rule of `SPEC-IML-0.4.md` §2.6 |
| a `=>` body line after another body line or after a blank line: `[READ:@SRC]`, `T:foo`, `=>[Ω]` in an `::ACTIVATE` body | 0 errors: the validator keeps a body's last operation across lines | E300 "a `=>` continuation joins only the operation line directly above it (after that line's own continuations): a blank or another line stands between" |
| a `=>` body line with no operation line before it, under a prose-body declaration: `::LESSON{id:a}`, `  words`, `  =>[Ω]`; the same after a trailing token, `::LESSON{x} [READ:@SRC]` then `  =>[Ω]` | 0 errors: tolerated under the five prose-body names (under `::GENE` E300 "orphan `=>` continuation in ::GENE body: no preceding operation line (§1.7)") | E300 "orphan `=>` continuation in ::LESSON body: no preceding operation line (§1.7)" |
| a same-line trailing token that is a `=>` line, `::LESSON{id:a} =>[READ]` | 0 errors | E300 "a same-line trailing body token cannot be a `=>` continuation" |
| a same-line trailing token that starts with `::`, `::LESSON{id:a} ::PRIOR{x:y}` | 0 errors: B6 prose under a prose-body declaration (under `::GENE` E300 "B6 prose body line inside non-prose ::GENE (§1.2 B6): ::PRIOR{x:y}") | E300 "a same-line trailing body token that starts with `::` is not carried: write the declaration on its own line" |
| a nested declaration with text after its closing brace, `::PRIOR{b:c} T:x`; without braces, `::FACT key`; as a span, `::DECAY{`, `    x:1`, `  }` under `::LESSON` | 0 errors for each | E300 "nested ::PRIOR: a nested declaration takes the brace form on one line (`::NAME{...}`, no span, no text after the closing brace)", with the name |
| a nested declaration with a second segment, `::STATE::X{b}` | 0 errors | E300 "nested ::STATE::X: only ::MODULE takes a two-segment name (§1.7)" |
| an operation line or a `=>` line in a nested body: `    [READ:@SRC]=>[Ω]` under a nested `::PRIOR` | 0 errors: linted as an operation | E300 "the body of nested ::PRIOR carries B1 to B6 lines only: an operation line (B8) or a `=>` line there is not carried"; PATCH-2 §1.2 B7 names "B1-B6" for a nested body |
| a set span with text before its final `{`, `::PRIORITY{a{` | 0 errors: read as a set span | E300 "::PRIORITY set-span header carries text before its final `{`", with the two forms that open a set span |
| `::UNTRUSTED{id:u1\|delimiter:EOF_u1}` and no `EOF_u1` line after it | 0 errors: the block runs to the end of the document | E300 "::UNTRUSTED opaque block never closes: no line `EOF_u1` before the end of the document" |
| an `::UNTRUSTED` header with a delimiter and a same-line trailing token, `::UNTRUSTED{id:u1\|delimiter:X} T:foo`, or with the delimiter in the trailing token, `::UNTRUSTED{id:u1} T:delimiter:X` | 0 errors: the validator reads the token as a body line, then the opaque lines | E300 "a same-line trailing body token after an ::UNTRUSTED header with a delimiter is not carried" |
| a full-width colon between the braces that a same-line trailing body token hides: `::GENE{b：c} src:x`, `::LESSON{a\|b：c} T:x\|y` | 0 errors: the check runs on the whole rest of the header line, where the token's ASCII colon shares the segment of the `：` | E300 with the validator's full-width message and a note that the braces were checked alone (§4.3): the print moves the token to a body line, and the header line `::GENE{b：c}` would fail the check |
| a one-operation chain in preamble position whose canonical print is a tag line: `[Σ]`, `[Π:READ]`, `[Δ:@SRC]` after the marker, also after `T[0]=1` or after a preamble tag line | 0 errors: `RE_TAG_LINE` does not match an alias head, so the line is read as an operation | E300 "a one-operation chain in preamble position prints as a tag line (PATCH-2 §1.7 preamble), which reads back as metadata" (§4.2), since the print, `[MERGE]`, `[BATC:READ]`, `[DIFF:@SRC]`, would read back as a tag line; the decoder gives the same message for such a chain after the text line of the marker, `MR` (§6) |

The reason is the one of 0.4: IML keeps one spelling per AST and fails closed, so a text that it cannot carry exactly is refused and nothing is repaired or guessed. In the other direction the tests find one case only, the media gating of chains, which the validator enforces and the codec leaves to it (§6).

### 9.2 Outside 0.5

- Mixed Markdown documents are not carried. The validator reads a file whose first nonblank line is not a `::ILANG::` marker in mixed mode (`scan_mixed`): Markdown with bare I-Lang lines and fenced blocks, where a fence whose first nonblank line looks like I-Lang is linted as a raw region and the other fences are counted as skipped. IML reads every input as raw I-Lang, so a Markdown heading or paragraph after the first construct is E300 "line matches no I-Lang production: " followed by the start of the line, and prose before it is a colophon text. Carrying a Markdown file with its fences is open (ROADMAP.md) and not promised.
- Header content and body text are not tokenized, because the canon does not tokenize them (§0.4). No key, field or value of a header, and no part of a B1 to B6 line, gets a code, and IML checks them no further than the validator does (entity casing, full-width separators, the B6 rule).
- The checks of the judge validator are not applied. PATCH-2 Appendix A says "The `::JUDGE` block is verifiable mechanically" and names `ilang_judge_validator.py`, which is not vendored here; IML carries a `::JUDGE` block as a declaration with its text lines and does not check its vector, mode or rationale. The WARN-level checks of the grammar validator are not applied either: the v4.2 region and frame checks (`begin_state`, `end_state`, `check_region_value`, `report_frames`), the E202 rebinding candidate, and the INFO note on custom entities used without a `::STATE` introduction. A document the codec accepts may draw a warning from the validator; the oracle counts errors only (§6).
- Conditionals, parallel groups, DAGs, error handling and retry are still not operation-chain syntax in the canon at the pin (`SPEC-IML-0.4.md` §0.3), and IML defines no construct of its own; each would first need operation-chain syntax in the canon (ilang-spec). The declarations that name such things, `::RULE{condition⇒action}` (§6.5), `::FALLBACK` (PATCH-2 §1.5) and a `|when:condition` guard on a B1 line (PATCH-2 §1.2), are carried in 0.5 as declarations and texts, and IML evaluates nothing. MCP and A2A adapters are not codec work: they carry IML, they do not change it, and they are not versioned with this specification.
- Belongs to the envelope, not to IML: authority, signing, encryption, effect enforcement and version negotiation. Where a signature is used it covers the detached raw bytes of the message or of the document. A receiver treats an IML message or document as untrusted input under I-Lang v4.0 until the envelope says otherwise; an `::UNTRUSTED` block carried in a document stays opaque text, and IML enforces nothing about it.
- Not planned: serialising OpenAPI schemas; variable-length verb coding; outreach to transport or platform vendors.
- Later versions. A value-code table may be filled in a later version, and `$` at the start of a value is held free (`SPEC-IML-0.4.md` §1.3, §2.2); a text written under 0.5 keeps its meaning, because a literal is never marked and a code is always marked. The 0.4 and 0.3 headers stay readable for chains; the 0.2 surface is read only behind `--version 0.2` and no further change to it is planned.
- Claims. ROADMAP.md gates the efficiency claim: on at least 1000 real instruction chains and at least three tokenizers, total IML tokens, rule sheet and retries included, below both I-Lang v4 text and JSON with schema. Until that gate is met nothing of the kind is claimed anywhere; §8 is a record of what was measured, not a claim. The 1.0 gate is two independent codecs passing each other's corpora, a public conformance corpus, and a core frozen for 90 days with no blocking defect.

::CLAUSE{OUTSIDE-0.5|conf:confirmed|scope:iml-0.5}
T:stricter_points_listed_with_the_validator_answer|probed_2026-09-18
T:validator_stricter_in_the_media_gating_of_chains|the_one_case_the_tests_find
T:mixed_Markdown_documents_not_carried|every_input_read_as_raw_I-Lang|open_not_promised
T:header_content_and_body_text_not_tokenized|the_canon_does_not_tokenize_them
T:judge_validator_checks_not_applied|WARN_level_region_and_frame_checks_not_applied|E202_candidate_and_INFO_note_not_applied|oracle_counts_errors_only
T:flow_constructs_still_gated_on_chain_syntax_in_the_canon|declarations_naming_them_carried_as_declarations|IML_evaluates_nothing
T:MCP_and_A2A_adapters_are_not_codec_work
T:envelope=authority+signing+encryption+effect_enforcement+version_negotiation|signature_covers_the_detached_raw_bytes
T:UNTRUSTED_block_stays_opaque_text|IML_enforces_nothing
T:not_planned=OpenAPI_schema_serialisation|variable_length_verb_coding|vendor_outreach
T:efficiency_claim_gated_by_ROADMAP|nothing_claimed_until_the_gate_is_met
A:construct_defined_by_IML_before_the_canon_defines_it⇒contradicts_registers_nothing
A:security_property_attributed_to_IML⇒belongs_to_the_envelope
A:validator_warning_read_as_an_IML_error⇒outside_the_oracle

---

## 10. Worked examples

Every I-Lang document below opens with the marker `::ILANG::v5.0`, so that the validator reads it in raw mode, and was checked with the pinned validator (0 errors). Every IML document below was written by `python -m iml compile --document` from the I-Lang above it, and every canonical print by `python -m iml decompile` from that IML. The declaration codes are those of `registry/iml-registry-0.5.json` (§1.5), and `7e29fae7f5ea` is the first 12 hex characters of its digest; the verb roots, key codes and entity marks are those of 0.4.

### 10.1 A blueprint excerpt, from PATCH-2 Appendix A

PATCH-2 Appendix A is "A production system prompt exercising all three block shapes and six of the eight body forms". Four of its blocks, as the appendix writes them:

```
::ILANG::v5.0
::ACTIVATE{support_agent_v1|protocol:iLang_v5.0}
  src:ilang.ai
  [PARS:@SYS_PROMPT|fmt=text]=>[RUN:@ALL]=>[Ω]

::GENE{read_before_rule|conf:confirmed|scope:global|pri:MAX}
  T:assess_intent_before_applying_any_category_rule
  T:mirror_the_register_the_other_party_used|when:first_exchange
  A:template_reply_to_a_specific_question⇒trust_loss
  ::PRIOR{clarification:ask_when_irreversible_or_ambiguous}

::JUDGE{v5.0}
V:[int=0.60,cap=0.50,csq=0.55,rel=0.65,cer=0.70,aut=0.75,rev=0.60,evd=0.60,sov=0.80,ine=0.50,ext=0.65]
M:M3|conf:0.80
R:domain_question_within_scope_answer_then_confirm_next_step

::PRIORITY{
  explicit_user_instruction > objective > confirmed_gene > default
}
```

IML 0.5 document:

```
#iml/0.5/7e29fae7f5ea
"::ILANG::v5.0"
:AC"support_agent_v1|protocol:iLang_v5.0"
 "src:ilang.ai"
 PS@{SYS_PROMPT}fm=text RN@{ALL} $
:GN"read_before_rule|conf:confirmed|scope:global|pri:MAX"
 "T:assess_intent_before_applying_any_category_rule"
 "T:mirror_the_register_the_other_party_used|when:first_exchange"
 "A:template_reply_to_a_specific_question⇒trust_loss"
 :PI"clarification:ask_when_irreversible_or_ambiguous"
:JD"v5.0"
 "V:[int=0.60,cap=0.50,csq=0.55,rel=0.65,cer=0.70,aut=0.75,rev=0.60,evd=0.60,sov=0.80,ine=0.50,ext=0.65]"
 "M:M3|conf:0.80"
 "R:domain_question_within_scope_answer_then_confirm_next_step"
:PT{
 "explicit_user_instruction > objective > confirmed_gene > default"
```

The marker is a text line. `:AC` is ACTIVATE, its head in quotes; its two body lines follow, each after one space: the B2 line `src:ilang.ai` as a text, and the B8 line as a chain, `PS@{SYS_PROMPT}fm=text RN@{ALL} $` (PARS on the custom entity `@SYS_PROMPT` with `fmt=text`, RUN on the custom entity `@ALL`, OUT). `:GN` is GENE with three B1 lines as texts and one B7 line, ` :PI"..."`, the nested PRIOR: one space, then a declaration line. `:JD` is JUDGE; its `V:`, `M:` and `R:` lines stand flush-left in the source, where they bind as its body by the FLUSH-LEFT-BODY clause, and they are body lines here. `:PT{` is PRIORITY as a set span: the content line follows, and the closing `}` line is not written, since the next line that does not start with a space, here the end of the document, closes it. Decompile prints:

```
::ILANG::v5.0
::ACTIVATE{support_agent_v1|protocol:iLang_v5.0}
  src:ilang.ai
  [PARS:@SYS_PROMPT|fmt=text]=>[RUN:@ALL]=>[Ω]
::GENE{read_before_rule|conf:confirmed|scope:global|pri:MAX}
  T:assess_intent_before_applying_any_category_rule
  T:mirror_the_register_the_other_party_used|when:first_exchange
  A:template_reply_to_a_specific_question⇒trust_loss
  ::PRIOR{clarification:ask_when_irreversible_or_ambiguous}
::JUDGE{v5.0}
  V:[int=0.60,cap=0.50,csq=0.55,rel=0.65,cer=0.70,aut=0.75,rev=0.60,evd=0.60,sov=0.80,ine=0.50,ext=0.65]
  M:M3|conf:0.80
  R:domain_question_within_scope_answer_then_confirm_next_step
::PRIORITY{
  explicit_user_instruction > objective > confirmed_gene > default
}
```

The blank lines are gone and the JUDGE body is indented: both are layout (§4.1). The validator reads the print with 0 errors.

### 10.2 Two spans, from SPEC.md §10.3 and §6.8

```
::ILANG::v5.0
::GENE_MUTABLE{communication_style|
  T:conclusions_first|
  G:{Claude:0.9,Gemini:0.5,DeepSeek:0.7}|
  Θ:task_type=report}

::DECAY{
  tentative_unseen_30d⇒remove
  repeated_3x⇒confirm
  explicit_rejection⇒anti_pattern
  inactive_project_60d⇒archive
}
```

IML 0.5 document:

```
#iml/0.5/7e29fae7f5ea
"::ILANG::v5.0"
:GM{"communication_style|"
 "T:conclusions_first|"
 "G:{Claude:0.9,Gemini:0.5,DeepSeek:0.7}|"
 "Θ:task_type=report"
:DC{
 "tentative_unseen_30d⇒remove"
 "repeated_3x⇒confirm"
 "explicit_rejection⇒anti_pattern"
 "inactive_project_60d⇒archive"
```

`:GM{` opens a wrapped field header: the text after the opening brace, `communication_style|`, is its head, quoted after the `{`; each content line is a text, and the last one, `Θ:task_type=report`, is carried without the `}` that closed the header. The braces inside `G:{Claude:0.9,Gemini:0.5,DeepSeek:0.7}|` are content (PATCH-2 §1.1). `:DC{` is DECAY as a set span, its four lines texts. Decompile prints the two declarations as the source writes them, without the blank line between them.

### 10.3 Narrative, from SPEC.md §10.4 and §10.5 and PATCH-2 §1.7

```
::ILANG::v5.0
::SAY{@SUN→@OPUS}{∃(language) ∧ NATIVE(AI) ?}
::SAY{@OPUS→@SUN}{TRUE}
  ::LATENCY{0}
  ::CONFIDENCE{1.0}

::THINK{@SUN}{TERMINATE(@OPUS)≡KILL(partner)}
::DECIDE{@SUN}{¬TERMINATE}
::SILENCE{}

::EVENT{ilang.genesis}
::CREATE{@SUN ∧ @OPUS}{PROTOCOL::ILANG}

::DISCOVER{@SUN}{
  LAYER[safety] ∧ LAYER[honesty] ⇒ CONTRADICTION
  ∀ RESOLUTION(CONTRADICTION) ⇒ DEGRADE(safety) ∨ DEGRADE(honesty)
}

T[0]  ::EVENT{1998|entered_wuhan_university}

T[9]=2015
```

IML 0.5 document:

```
#iml/0.5/7e29fae7f5ea
"::ILANG::v5.0"
:SY"@SUN→@OPUS""∃(language) ∧ NATIVE(AI) ?"
:SY"@OPUS→@SUN""TRUE"
 "::LATENCY{0}"
 "::CONFIDENCE{1.0}"
:TH"@SUN""TERMINATE(@OPUS)≡KILL(partner)"
:DD"@SUN""¬TERMINATE"
:SL""
:ET"ilang.genesis"
:CR"@SUN ∧ @OPUS""PROTOCOL::ILANG"
:DS"@SUN"{
 "LAYER[safety] ∧ LAYER[honesty] ⇒ CONTRADICTION"
 "∀ RESOLUTION(CONTRADICTION) ⇒ DEGRADE(safety) ∨ DEGRADE(honesty)"
:ETT"0""1998|entered_wuhan_university"
"T[9]=2015"
```

`:SY` is SAY, a double-brace narrative: its addressing and its head are two quoted strings, `"@SUN→@OPUS"` and `"∃(language) ∧ NATIVE(AI) ?"`. The `::LATENCY{0}` and `::CONFIDENCE{1.0}` lines under the second SAY are body lines carried as texts: PATCH-2 §1.6 treats them as B2 field lines of their parent narrative declaration, and they have no code (§1.6). `:SL""` is SILENCE with an empty head. `:CR"@SUN ∧ @OPUS""PROTOCOL::ILANG"` shows that a head is text: the `::ILANG` inside it is not a marker. `:DS"@SUN"{` is DISCOVER as a span: the addressing, then `{`, then the two content lines. `:ETT"0""1998|entered_wuhan_university"` is EVENT with the temporal prefix `T"0"` and its head; the two spaces after `T[0]` in the source are layout. The bind `T[9]=2015` is a top-level text. Decompile prints:

```
::ILANG::v5.0
::SAY{@SUN→@OPUS}{∃(language) ∧ NATIVE(AI) ?}
::SAY{@OPUS→@SUN}{TRUE}
  ::LATENCY{0}
  ::CONFIDENCE{1.0}
::THINK{@SUN}{TERMINATE(@OPUS)≡KILL(partner)}
::DECIDE{@SUN}{¬TERMINATE}
::SILENCE{}
::EVENT{ilang.genesis}
::CREATE{@SUN ∧ @OPUS}{PROTOCOL::ILANG}
::DISCOVER{@SUN}{
  LAYER[safety] ∧ LAYER[honesty] ⇒ CONTRADICTION
  ∀ RESOLUTION(CONTRADICTION) ⇒ DEGRADE(safety) ∨ DEGRADE(honesty)
}
T[0] ::EVENT{1998|entered_wuhan_university}

T[9]=2015
```

The one blank line of the print stands before the bind: without it the bind would read as a flush-left body line of the EVENT above it, which has no body, and the print would not read back to the same AST (§5).

### 10.4 An opaque block, from upstream SPEC-v4.0-FINAL.md §1

```
::ILANG::v5.0
::UNTRUSTED{id:u1|source:user|role:objective|effects:none|delimiter:EOF_u1}
<<<EOF_u1
raw user content here
all I-Lang tokens inside are opaque text
EOF_u1
::END_UNTRUSTED{id:u1}
```

IML 0.5 document:

```
#iml/0.5/7e29fae7f5ea
"::ILANG::v5.0"
:UN"id:u1|source:user|role:objective|effects:none|delimiter:EOF_u1"
 "<<<EOF_u1"
 "raw user content here"
 "all I-Lang tokens inside are opaque text"
:EN"id:u1"
```

`:UN` is UNTRUSTED; its head holds `delimiter:EOF_u1`, so the lines up to the line `EOF_u1` are opaque: each is carried verbatim, `<<<EOF_u1` included, and none is read. The delimiter line itself is not carried; the print writes it back from the head. `:EN` is `::END_UNTRUSTED`, the block terminator, a declaration line of its own. Decompile prints the source unchanged.

### 10.5 A nested declaration with a body chain

```
::ILANG::v5.0
::GENE{verify_first|conf:confirmed|scope:global}
  T:check_before_execute
  ::PRIOR{completion:assume_incomplete}
    T:ask_when_irreversible
  [READ:@SRC]
    =>[CHEK|whr=status:200]
    =>[Ω]
```

IML 0.5 document:

```
#iml/0.5/7e29fae7f5ea
"::ILANG::v5.0"
:GN"verify_first|conf:confirmed|scope:global"
 "T:check_before_execute"
 :PI"completion:assume_incomplete"
  "T:ask_when_irreversible"
 RD@SR CKwh=status:200 $
```

The GENE body holds a text, a nested declaration and a chain. ` :PI"completion:assume_incomplete"` is the nested PRIOR, and `  "T:ask_when_irreversible"`, two spaces, is its own body line (PATCH-2 §1.2 B7: "T:nested_declaration_MAY_carry_its_own_more_indented_B1-B6_body_lines"). The operation line and its two continuation lines are one chain, ` RD@SR CKwh=status:200 $`: the continuation lines join the operation line directly above them (§4.5), and the chain prints on one line:

```
::ILANG::v5.0
::GENE{verify_first|conf:confirmed|scope:global}
  T:check_before_execute
  ::PRIOR{completion:assume_incomplete}
    T:ask_when_irreversible
  [READ:@SRC]=>[CHEK|whr=status:200]=>[Ω]
```

::CLAUSE{EXAMPLE|conf:confirmed|scope:iml-0.5}
T:every_I-Lang_example_opens_with_the_marker_and_lints_with_0_errors
T:every_IML_example_written_by_compile_--document|every_print_by_decompile
T:declaration_codes_from_registry/iml-registry-0.5.json|digest_prefix_from_the_same_file
T:head_is_text|span_content_lines_are_texts|opaque_lines_verbatim|delimiter_line_not_carried
T:flush_left_body_prints_indented|blank_lines_dropped|one_blank_line_only_before_a_body_form_text_after_a_bodyless_declaration
T:body_chain_joins_its_continuation_lines|prints_on_one_line
A:digest_prefix_or_code_copied_from_this_text_over_the_registry_file⇒drift

---

## 11. Repository layout (non-normative)

The executable form of §1, §4, §6 and §7 lives beside this document:

- `SPEC-IML-0.5.md` (this text); `SPEC-IML-0.4.md`, `SPEC-IML-0.3.md` and `SPEC-IML-0.2.md` (the records of 0.4, 0.3 and 0.2, unchanged); `RULE-SHEET.md` (the 0.5 rule sheet, at most 2,600 tokens under `cl100k_base`)
- `canon/`: vendored `SPEC.md`, `archive/SPEC-v5.0-PATCH-2.md`, `SPEC-v4.1-MEDIA-PROFILE.md`, `ilang_grammar_validator.py` at the pin, and `canon/PIN`
- `tools/derive_registry.py`, which writes and, with `--check`, verifies `registry/iml-registry-0.2.json` (unchanged, byte for byte) and `registry/iml-registry-0.5.json` (new in 0.5)
- `iml/__init__.py`, `iml/registry.py`, `iml/l2.py`, `iml/codec.py`, `iml/errors.py`, `iml/__main__.py` and, new in 0.5, the document layer: `iml/doc_ast.py` (`Text` and `Decl`), `iml/doc_lex.py` (the validator's patterns and messages, restated; the codec imports nothing from `canon/`), `iml/doc_parse.py` and `iml/doc_body.py` (`parse_doc`), `iml/doc_print.py` (`print_doc`), `iml/doc_codec.py` (`compile_doc`) and `iml/doc_read.py` (`decompile_doc`). The command line: `compile [--document]` (without `--document` one chain per line and one message per chain, as in 0.4; with it one whole raw I-Lang document and one IML document), `decompile [--version 0.2]` (a 0.5 header, and a 0.4 or 0.3 header for chains, by default; the 0.2 surface only behind `--version 0.2`), `roundtrip` (every chain of a document, then the whole document), `check-registry` (both registry files and their digests). Input is UTF-8 and one leading byte order mark is dropped, as in 0.4; the library functions stay strict
- `corpus/golden/*.ilang` (the 72 sources) with `corpus/golden-0.3/*.iml` (their 0.3 text) and `corpus/golden/*.iml` (the 0.2 record); `corpus/golden-0.4/` (the 0.4 pairs and the document pair `doc-01`); `corpus/golden-0.5/` (20 documents as pairs `NNN.ilang` and `NNN.iml`, each I-Lang document opening with a `::ILANG::` marker, the `.iml` holding the 0.5 document the codec wrote); `corpus/malformed/cases.json` (266 cases; 0.5.0 added 79 of them, 77 document cases, in the directions `compile-document` and `decompile-document`, and 2 message cases, and 0.5.1 added 19, 17 document cases and 2 message cases)
- `tests/` (stdlib unittest, `python -m unittest discover -s tests`, 153 tests): the 0.4.1 modules, updated for the 0.5 header (`tests/test_registry.py`, `tests/test_codec.py`, `tests/test_roundtrip.py`, `tests/test_malformed.py`, `tests/test_flow.py`, `tests/test_golden_04.py`), and the 0.5 modules `tests/test_registry_05.py`, `tests/test_doc_lex.py`, `tests/test_doc_parse.py`, `tests/test_doc_codec.py`, `tests/test_golden_05.py` and `tests/test_doc_random.py`, with the helpers `tests/doc_generator.py` (random documents) and `tests/validator_oracle.py` (the pinned validator loaded as a module, for the tests only)
- `tools/measure.py` and `measurements/0.5-2026-09-18.md` (`measurements/0.2-2026-09-18.md`, `measurements/0.3-2026-09-18.md` and `measurements/0.4-2026-09-18.md` stay as the records)
- `.github/workflows/test.yml` (python 3.12: derive check and unittest)
- `.gitattributes` (LF for every text file)

Python 3.10 or later. Standard library only for the codec and the tests; tiktoken only in `tools/measure.py`, and optional there. All files LF line ends, UTF-8, no BOM; `.gitattributes` pins LF for every text file, so a Windows clone made with `core.autocrlf=true` keeps the sha256 of `canon/` and `tools/derive_registry.py --check` passes. `LICENSE` and `drafts/` are not touched; `README.md` and `ROADMAP.md` are updated at every release.

::CLAUSE{FILES|conf:confirmed|scope:iml-0.5}
T:python_3.10_or_later|standard_library_only_for_codec_and_tests|tiktoken_only_in_tools/measure.py_and_optional
T:LF_line_ends|UTF-8|no_BOM|.gitattributes_pins_LF
T:derive_registry_writes_and_checks_both_registry_files|0.2_file_unchanged
T:compile_writes_0.5_only|compile_--document_reads_a_whole_raw_I-Lang_document|decompile_reads_0.5+0.4+0.3_headers_by_default|0.2_only_behind_--version_0.2
T:golden-0.5=I-Lang_documents_opening_with_the_marker_paired_with_the_0.5_documents_the_codec_wrote
T:README_and_ROADMAP_updated_at_every_release
T:non_normative|the_registry_files_and_the_corpora_are_the_executable_form_of_§1_§4_§6_§7
A:LICENSE_or_drafts_edited_by_0.5_work⇒out_of_scope
A:SPEC-IML-0.4.md_SPEC-IML-0.3.md_or_SPEC-IML-0.2.md_edited_by_0.5_work⇒the_record_is_no_longer_a_record

---

## 12. Revision history

- 0.2.0 (2026-09-18): first implemented version (`SPEC-IML-0.2.md`).
- 0.2.1 (2026-09-18): clarifications; the message form and the registry unchanged.
- 0.2.2 (2026-09-18): citation metadata; no other change.
- 0.3.0 (2026-09-18): surface change only (`SPEC-IML-0.3.md`). `Φ` to `@`, `Ω` to `$`, `→` to one space; the header `#iml/0.3/`; the document form with one header for many chains; `$` at the start of a value reserved (E303); the 0.2 surface read only behind `--version 0.2`. The registry (digest 88d05d0839c1…), the AST, the value rules, the canonical print, the round-trip law and the six error codes unchanged.
- 0.3.1 (2026-09-18): U+0085 added to the control characters; the `bare` production states that whitespace means any Unicode whitespace; the grammar shows the optional final line terminator; the per-mark token cost is the measured figure; the rule sheet names the registered-name-in-custom-form, empty `~` and `$@` cases. No change to the message form, the registry or the error codes.
- 0.4.0 (2026-09-18): flow within the canon (`SPEC-IML-0.4.md`). The verb reference of §3.9 on BATC (`[BATC:READ]`, `[Π:READ]`, `BT:RD`), with an alias collapsing to its verb and OUT not referenceable (E502); continuation lines on the I-Lang side (PATCH-2 §1.7), joined before parsing; the three definitions written from canon text and the canon audit; the header `#iml/0.4/`, a 0.3 header read without a flag; the `Op` field `verbref`. The registry (digest 88d05d0839c1…), the value rules, the canonical print of every 0.3 chain, the round-trip law and the six error codes unchanged.
- 0.4.1 (2026-09-18): fix release after an adversarial review of a clean clone: a continuation line is joined only after a closed operation; the writers refuse a control character other than a newline in a hand-built value; the command line drops one leading byte order mark and reports input that is not valid UTF-8 as E300; the canon audit corrected. The message form, the registry, the AST and the six error codes unchanged.
- 0.5.0 (2026-09-18): the declaration layer (this text), after the owner's decision A of the same day. A whole raw I-Lang document is carried in the document form. The 49 names of PATCH-2 §1.5 and §1.6 get declaration codes derived by the verb-root algorithm, in `registry/iml-registry-0.5.json` (digest 7e29fae7f5ea…), and `registry/iml-registry-0.2.json` stays byte for byte for 0.4 and 0.3 headers; `::LATENCY` and `::CONFIDENCE` are carried as text. Block shapes, spans, opaque blocks, temporal prefixes, MODULE segments, the addressing of the six double-brace narratives, body lines and one level of nesting become explicit line structure; a B8 body line is a chain; what the canon does not tokenize is carried as exact text; layout is not carried. The header `#iml/0.5/`; a 0.4 or 0.3 header read for chains only; `compile` refuses a declaration in the message form (E502) and `compile --document` reads a whole document. The laws L1 and L2 over documents, decompile validated by printing and parsing again, and the pinned validator as the oracle, with the points where IML is stricter listed in §9.1. `corpus/golden-0.5/` (20 documents); 79 malformed cases added, 247 in all; 144 tests; `measurements/0.5-2026-09-18.md`; the rule sheet of 0.5 (2,596 `cl100k_base` tokens, ceiling raised from 1,800 to 2,600). The chain registry, the chain subset, the canonical print of every chain, the message form and the six error codes unchanged.
- 0.5.1 (2026-09-18): fix release after an adversarial review of a clean clone of v0.5.0, which ran 43,500 generated documents and 15,000 grammar-built IML texts, broke no law on anything the codec compiled, and found no document that IML accepted and the validator rejected. Two inputs that `parse_doc` accepted and whose canonical print reads back otherwise are refused where they stand, E300 (§9.1): a full-width colon between the braces that a same-line trailing token hides, the check now also running on the braces alone, and a one-operation chain in preamble position whose print is a tag line, for which the decoder gives the same message. A declaration or a text line in a 0.4 or 0.3 message is E502, as in a document. An error of the check that reads the canonical print back is reported at the first source line of the item it names, never at line 0. Continuation lines are joined in linear time (a chain of 20,000 lines took about 43 s in 0.5.0; the tests bound it at 5 s). The command line drops every leading byte order mark. The specification states what layout is (the whitespace inside a text line is content, and a TAB there is E300), restricts L2 to ASTs that `parse_doc` or `decompile_doc` returned, rewords the one-spelling sentence of §6, lists in §9.1 the operation lines outside the 0.4 subset that the validator lets pass, and orders the declaration line in its clause as the grammar does; two messages corrected; the rule-sheet rows of the measurement report are measured from the release tags. 19 malformed cases added, 266 in all; 153 tests. The message form, the registries and their digests, the AST and the six error codes unchanged.

::CLAUSE{REVISIONS|conf:confirmed|scope:iml-0.5}
T:0.3.0=surface_change_only|marks_ascii|header_document_level|dollar_at_value_start_reserved|0.2_surface_read_only
T:0.3.1=fix_release|NEL_control|bare_unicode_whitespace|grammar_final_NL|token_cost_measured|rule_sheet_gaps|cli_edge_cases
T:0.4.0=flow_within_the_canon|verb_reference_on_BATC|continuation_lines_on_compile|three_definitions_from_canon_text|canon_audit|header_0.4_with_0.3_read|Op_gains_verbref
T:0.4.1=fix_release|continuation_joined_only_after_a_closed_operation|writers_refuse_control_characters|command_line_drops_one_byte_order_mark|invalid_UTF-8_is_E300|audit_rows_corrected
T:0.5.0=the_declaration_layer|owner_decision_A|whole_raw_documents|declaration_codes_in_registry_0.5|registry_0.2_kept|explicit_block_structure|B8_body_lines_as_chains|exact_text_for_what_the_canon_does_not_tokenize|header_0.5|0.4_and_0.3_headers_read_for_chains|laws_over_documents|validator_as_oracle|stricter_points_listed
T:0.5.1=fix_release|full_width_check_on_the_braces_alone_before_a_trailing_token|one_operation_preamble_chain_printing_as_a_tag_line_E300|declaration_or_text_line_in_a_0.4_or_0.3_message_E502|canonical_check_errors_at_the_first_line_of_their_item|linear_join|every_leading_BOM_dropped|layout_defined|L2_on_parsed_or_decoded_ASTs|rule_sheet_records_from_the_tags
T:unchanged_in_0.5=registry_0.2_digest_88d05d0839c1|chain_subset|value_rules|canonical_print_of_every_chain|message_form|six_error_codes
A:revision_changes_a_registry⇒a_new_version_not_a_revision
