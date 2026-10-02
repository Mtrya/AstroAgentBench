---
name: translate-docs
description: Translate technical documentation (benchmark READMEs, contracts, dataset cards) from English into zh_CN under docs/i18n/zh_CN/, preserving structure, code identifiers, and domain terminology.
---

## When to use

- Translating an English document into `docs/i18n/zh_CN/`
- Refreshing a translation after its English source changed
- Extending coverage to another in-scope document

## Scope

Run `python3 scripts/check_i18n_sync.py --all --format json` to list every in-scope
document. Documents that are deliberately never translated are listed in
`EXCLUDED_PREFIXES`, `EXCLUDED_FILES`, and `_is_vendored_dataset_paper` in
`scripts/check_i18n_sync.py`:

- `experiments/evaluate/instructions/*.md` and `AGENTS.md` / `CLAUDE.md` are inputs
  to agents. Translating them changes what an agent is told, and therefore changes
  benchmark scores and breaks reproducibility against published results.
- `benchmarks/<name>/dataset/*.md` (other than its `README.md`) holds vendored
  upstream papers, which are third-party copyrighted text.
- `tests/fixtures/`, `docs/internal/`, `.agents/`, `.claude/`, `vendor/`,
  `CONTRIBUTING.md`, `scripts/BRAHE_SKILL.md`, and the generated brahe PR template.

Never translate an excluded document. If one seems to need it, raise it instead.

## Before you start

1. Read the English source.
2. Read `docs/i18n/zh_CN/_TERMS.md`. It is the single source of truth for
   zh_CN terminology. Every term listed there must be rendered exactly as
   specified, and its 备注 column explains why — read it before "improving" a
   term. If a term you need is absent, add it with its reasoning rather than
   inventing an ad-hoc synonym.
3. Check whether a translation already exists at
   `docs/i18n/zh_CN/<same repo-relative path>`. The mapping is a pure mirror.

## Core rules

### 1. Code identifiers are never translated

Every inline code span in the source must appear **verbatim** in the translation.
This is mechanically enforced: `scripts/check_i18n_sync.py` requires the source's
inline code spans to be a subset of the translation's.

Keep in English: JSON/YAML keys and identifier values, CLI commands and flags,
file and directory paths, metric and field names, package and module names, API
names, and mathematical identifiers.

This is not a formality. These documents are dense in runnable commands such as
`python -m benchmarks.<name>.<entrypoint_pkg>.run ...` and paths such as
`dataset/cases/<split>/<case_id>/`. Replacing a `<placeholder>` with a concrete
value, or translating `coverage_ratio`, produces a Chinese document that looks
authoritative and cannot be copy-pasted.

Fenced code blocks are not covered by the checker, but they must still match the
current English source byte-for-byte: copy them over, including the info string
and any comments inside. Never translate their contents. If a prior translation
translated a comment or shows a stale value, restore the English block from the
current source — a translation that documents a command the repository no longer
accepts is worse than one that is merely out of date.

### 2. Translate for the reader, not word-for-word

Chinese technical prose should not read as a transliteration of English
sentences. Reorder clauses, break up long sentences, and prefer the constructions
Chinese technical writing actually uses.

Then read the draft critically and remove translation artifacts:

- Noun strings strung together with no connective, where English used a relative
  clause
- Passive voice carried over where Chinese would use an active construction
- Redundant measure words, especially 一次的、进行一个、的的
- Over-translated connectives: 此外、然而、因此 used where a full stop would read better
- Latin punctuation and spacing in Chinese text

Read the result aloud in your head. If a sentence makes you think harder than the
English did, rewrite it rather than defending it.

### 3. Structure is preserved, headings are translated

Keep the document's section structure, tables, lists, and code blocks. Translate
heading text naturally — a heading is not required to match the English word for
word. Do not add or remove sections to make the translation look tidier.

Tables keep their columns and row order. Translate cell prose; leave code spans
alone per rule 1.

### 4. Link back to the English source

Start the translation with a language switch. The link must resolve: count the
`../` segments from the destination file's own directory back up to the repository
root, then down to the English source. Depth differs per destination, and a wrong
depth produces a link that silently points nowhere.

| Destination | Link |
|---|---|
| `docs/i18n/zh_CN/README.md` | `../../../README.md` |
| `docs/i18n/zh_CN/docs/benchmark_contract.md` | `../../../../docs/benchmark_contract.md` |
| `docs/i18n/zh_CN/benchmarks/satnet/README.md` | `../../../../../benchmarks/satnet/README.md` |

The English documents do not link to their translations, so this is the only way a
reader arrives from the other direction.

### 5. Stamp the source hash

Immediately after the H1, add the comment below. Compute the hash of the *English
source file*:

```markdown
<!-- i18n-source-sha256: <sha256 of the English file, 64 lowercase hex chars> -->
```

```bash
python3 -c "import hashlib,pathlib,sys;print(hashlib.sha256(pathlib.Path(sys.argv[1]).read_bytes()).hexdigest())" <english path>
```

The stamp tells the checker whether the translation still reflects its source. An
unstamped or stale translation is reported on every pull request that touches the
source. Refresh the stamp whenever you revise the translation.

## Workflow

```text
For each file:
  1. Read the English source
  2. Read docs/i18n/zh_CN/_TERMS.md
  3. Translate or patch the existing translation
  4. Re-read for translation artifacts (rule 2)
  5. Verify every inline code span survived verbatim (rule 1)
  6. Add the language switch (rule 4) and the source hash stamp (rule 5)
  7. Run: python3 scripts/check_i18n_sync.py --base-ref <base sha> --format markdown
  8. Confirm it reports nothing for the files you touched
```

Patching beats retranslating. A translation that is one or two sections behind is
much cheaper to bring forward than to rewrite, and it preserves terminology that
was already reviewed.

## Verification checklist

- [ ] `_TERMS.md` consulted; every term rendered as the glossary specifies
- [ ] No inline code span altered, added placeholders substituted, or identifiers translated
- [ ] Fenced code blocks match the current English source byte-for-byte
- [ ] Language switch present and resolving to the English source
- [ ] `<!-- i18n-source-sha256: ... -->` present and current
- [ ] `scripts/check_i18n_sync.py` reports nothing for the touched documents
- [ ] Draft re-read for translation artifacts

## Example prompt

> Use the `translate-docs` skill to bring `benchmarks/<name>/README.md` up to date in
> Chinese. Read `docs/i18n/zh_CN/_TERMS.md` first and follow the glossary strictly,
> keep every inline code span verbatim, patch the existing translation rather than
> rewriting it, add the language switch and a fresh source hash stamp, and confirm
> `scripts/check_i18n_sync.py` reports nothing for that file.