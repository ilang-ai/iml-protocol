# IML (I-Lang Machine Layer) 0.6

::STATE{@SPEC, id:IML-0.6, revision:0.6.0, layer:machine, status:adopted, date:2026-11-08}
::STATE{@SPEC, canon:ilang-ai/ilang-spec, canon_pin:d1d4367, canon_commit:d1d436733373c6342a74d4865348761320138613, canon_version:v5.0.11}
::STATE{@SPEC, registers_nothing:true, verbs_derived:88, aliases_derived:13, keys_derived:49, entities_derived:25, declarations_derived:50, tolerated_annotations:2, digest_prefix:0fddd3752aad}
::STATE{@SPEC, supersedes:SPEC-IML-0.5.md, change:one_declaration_and_a_registry_file, owner_decision:A_2026-11-08, adds:::EXCLUDE_code_EX+registry_0.6+header_0.6, reads:0.6_0.5_0.4_0.3, grammar_unchanged:true}
::STATE{@SPEC, authors:Long_Quan_Zhu(Max/@SUN)+Claude_Fable_5.1(@FABLE), orcid:0009-0004-4540-8082}

Purpose: 0.6 follows the canon. On 2026-11-08 the canon registered one structural declaration, `::EXCLUDE`, through the §1.5 DECL-COUNT amendment channel (ilang-spec 5.0.11, 33 structural declarations), and `MODULE::MEMORY` gained a COMPLETE line that writes it. IML registers nothing of its own, so the declaration reaches IML the only way it can: a new registry file derived from the canon at the new pin, and a header that names it. Everything else in `SPEC-IML-0.5.md` stands: the grammar, the shapes, the body lines, the laws, the errors, the measurement. This document states only what 0.6 changes.

## 0. Scope

### 0.1 Why 0.6

A header carries the first 12 hex characters of the digest of the registry its documents were written with (§3 of 0.5). Adding a name to the 0.5 table would change that digest and orphan every 0.5 document. So the 0.5 file is frozen, byte for byte, as the registry a `#iml/0.5/` header names; the new table is a new file with a new digest, and compile writes `#iml/0.6/`. The owner chose this on 2026-11-08 (decision A: register the declaration, the three repositories follow).

### 0.2 What 0.6 changes

- One registered declaration: `::EXCLUDE`, class `amended`, code `EX`, inline shape, not a prose-body type. The 49 names and codes of 0.5 are unchanged (§1.3): the new name is appended after `LIST` in the amended class and `EX` was free.
- A third registry file, `registry/iml-registry-0.6.json`, derived from the canon at `d1d4367` (ilang-spec 5.0.11): the chain tables of the 0.2 file unchanged, the canon pin of the new commit, 50 declarations, the two tolerated annotations.
- The header `#iml/0.6/0fddd3752aad`. Compile writes it. The default reader reads `#iml/0.6/`, `#iml/0.5/` (with the frozen 0.5 registry's tables), `#iml/0.4/` and `#iml/0.3/` (chains only). `--version 0.5` writes a 0.5 header from the frozen 0.5 registry; `--version 0.2` is unchanged.
- Nothing in the grammar changes. `::EXCLUDE{<id>|candidates:…|out:…|left:…|conf:…|by:…}` is a brace-shape declaration with pipe-separated fields, coded like any other: `:EX"<id>|candidates:…|…"`.

## 1. Registry

### 1.1 Three files

`registry/iml-registry-0.2.json` (digest `88d05d0839c1…`) is the chain registry of 0.2, 0.3 and 0.4, kept byte for byte. `registry/iml-registry-0.5.json` (digest `7e29fae7f5ea…`) is the declaration registry of 0.5, kept byte for byte: the one a `#iml/0.5/` header names, and the tables a 0.5 document is read with. `registry/iml-registry-0.6.json` (digest `0fddd3752aad…`) is the registry of 0.6 and the default.

The loader pairs the 0.6 file with both: the chain tables (verbs, aliases, keys, entities, value codes) of all three must be equal, the 0.2 digest becomes the chain digest that 0.4, 0.3 and 0.2 headers carry, and the 0.5 digest is the one a 0.5 header carries. The canon pin differs between the files and is recorded in each: 0.2 and 0.5 derive from the canon at 127ba56, 0.6 from the canon at d1d4367.

### 1.2 Sources

`canon/` holds five files at the pin: `SPEC.md`, `SPEC-v4.1-MEDIA-PROFILE.md`, `archive/SPEC-v5.0-PATCH-2.md`, `ilang_grammar_validator.py` and, new in 0.6, `SPEC-v5.0.md`, the current canon whose §1.5 holds the amended registry. `tools/derive_registry.py` reads the declarations for 0.6 from `SPEC-v5.0.md` §1.5 and §1.6 (the four bold headings, now "Registered by amendment (2)", the terminator sentence, the narrative list, the tolerated annotations), the double-brace narratives from `SPEC.md` §7.1 and the prose-body types from PATCH-2 §1.2 B6, exactly as 0.5 read them from the archived PATCH-2; it cross-checks every class against the vendored validator's sets (`REGISTRY_AMEND` is now `LIST`, `EXCLUDE`; `DECL_STRUCTURAL` has 33 names). With `--check` it verifies that the 0.6 file reproduces and that the 0.2 and 0.5 files are the frozen bytes. `canon/127ba56/` keeps `SPEC.md` and `archive/SPEC-v5.0-PATCH-2.md` as they were at the 0.5 pin, because `corpus/golden-0.5/` quotes them verbatim; nothing is derived from them.

### 1.3 Order and codes

The 50 names are taken in the order of 0.5 §1.3 with `EXCLUDE` after `LIST`: the 14 of the v3.0 communication layer, the 8 of the v4.0 execution layer, the 9 of the v5.0 judgment layer, `LIST` and `EXCLUDE`; then the 3 meta declarations; then `END_UNTRUSTED`; then the 13 narrative declarations. Codes are assigned as in 0.5 §1.3 with a fresh set of taken codes; because `EX` was free and every earlier name keeps its position, the 49 codes of 0.5 are unchanged and `EXCLUDE` is `EX`.

### 1.4 Registry file

As 0.5 §1.4, with `iml_version` `0.6`, `declarations` a list of 50 entries, and `canon` the new pin (commit and the sha256 of each of the five files).

## 2. Headers and reading

Compile writes `#iml/0.6/0fddd3752aad`: a message and a document both. The default reader reads four headers: `#iml/0.6/` with the 0.6 digest prefix, the full document layer with the 0.6 tables; `#iml/0.5/` with `7e29fae7f5ea`, the full document layer with the frozen 0.5 tables, so every 0.5 document decodes to the same items as before and a 0.5 document that spelled `:EX` would be refused as it was; `#iml/0.4/` and `#iml/0.3/` with `88d05d0839c1`, chains only. A matched header whose 12 characters are not the digest prefix of the registry its version names is E502, as in 0.5. `--version 0.5` on the command line is a reader of 0.5, 0.4 and 0.3 and writes a 0.5 message header; `--version 0.2` is the old surface, unchanged.

A 0.5 document decompiled and compiled again carries the 0.6 header; compiled with the 0.5 registry passed explicitly (`compile_doc(items, registry=reg.for_version("0.5"))`), it carries the 0.5 header and reproduces its record byte for byte, which is how the 0.5 corpus is tested.

::CLAUSE{HEADER-0.6|conf:confirmed|scope:iml-0.6}
T:header=#iml/0.6/+12_lowercase_hex_of_the_0.6_registry_digest
T:compile_writes_0.6|--version_0.5_writes_0.5_from_the_frozen_0.5_registry|--version_0.2_unchanged
T:default_reader=0.6_and_0.5_headers_full_document_layer_each_with_its_own_tables|0.4_and_0.3_headers_with_88d05d0839c1_chains_only
T:the_0.5_and_0.2_registry_files_are_frozen_byte_for_byte|a_header_names_the_file_it_was_written_with
A:adding_a_name_to_the_0.5_table⇒every_0.5_document_orphaned|refused_by_design
A:a_0.5_header_with_a_0.6_digest_prefix|a_0.6_header_with_a_0.5_prefix⇒E502

## 3. Corpus and tests

`corpus/golden-0.6/` holds the documents that use `::EXCLUDE`, as pairs `NNN.ilang` and `NNN.iml` under the 0.6 header, tested under the laws L1 and L2 and the pinned validator (`tests/test_golden_06.py`). `corpus/golden-0.5/` is unchanged and is tested with the frozen 0.5 registry (`tests/test_golden_05.py`). `tests/test_registry_06.py` checks the table, the codes, the pairing, the derivation and the version-aware reader.

## 4. History

- 0.6.0 (2026-11-08): the canon's 5.0.11 amendment registers `::EXCLUDE` (MODULE::MEMORY COMPLETE: a gap in memory is closed by elimination, never by recall; Mem-Forever 3.2 writes the block); IML derives the 0.6 registry from the canon at d1d4367, freezes the 0.5 file as the registry a 0.5 header names, and writes `#iml/0.6/`. Grammar, laws, errors and measurement as in 0.5.
