# EMNLP Outline - Current Source of Truth

**Working title:** *AstroReason-Bench: Evaluating Agentic Planning on Space Mission Planning Tasks*

**Status:** The main paper is drafted and page-fit. The 8-page content body ends at Conclusion. Limitations, Ethical considerations, references, and appendices follow outside the main content budget.

**Framing:** Benchmark resource paper with in-depth analysis. AstroReason-Bench is the contribution; evaluated agent systems, solver references, ablations, and case studies are probes used to characterize the benchmark.

**Do not use this file as public prose.** It is an internal coordination outline. Public paper text must not expose local paths, experiment directory names, run IDs, internal solver IDs, branch names, issue numbers, or image-generation/plugin details.

## Locked Decisions

- Resource-paper framing, not an AstroAgent system paper.
- Public benchmark name: AstroReason-Bench.
- All seven task families remain in the main paper.
- Main result combines agent-system evaluation and solver references.
- Main ablations: procedure injection and memory accumulation.
- Results are attributed to evaluated agent systems, not base models alone.
- Main paper should stay stable unless an appendix cross-reference or hard inconsistency requires a minimal fix.
- Limitations cover held-out scale and LLM API cost, solver references as anchors rather than optima, targeted ablation coverage, and one sampled difficulty regime.
- Ethical considerations cover dual-use risk, non-operational benchmark boundaries, safety against direct reliance on current agents, public/license-respecting sources, and no human-subject data.

## Current Main-Paper Structure

1. **Introduction:** Motivation from space mission planning, modern LLM agents, research questions, AstroReason-Bench, empirical preview, and contributions.
2. **Related Work:** LLM-based agents; space mission planning and LLM-for-space work; agent benchmarks.
3. **AstroReason-Bench:** Overview, feasibility constraints, construction pipeline, evaluation protocol, and agent-system setup.
4. **Experiments:** Common execution budget, five public agent systems, solver-reference baselines, and main result table.
5. **In-Depth Analysis:** What fails, what succeeds, and ablations. Current §5 uses two failure layers, two success mechanisms, Figure 2 trace evidence, Table 4 verifier-use evidence, and Figure 3 ablation summary.
6. **Conclusion:** Restates benchmark contribution and central empirical pattern without new evidence.
7. **Limitations:** Unnumbered.
8. **Ethical considerations:** Unnumbered.

## Main Claims To Preserve

1. Current LLM agent systems can produce verifier-valid executable plans on many cases, but validity and mission value are distinct.
2. Solver-relative quality is family-dependent. Agents approach or exceed available solver references on some families and remain separated on others.
3. Failures separate into task-formulation failures and solution-construction failures.
4. Strong runs use verifier-calibrated implementations and case-adaptive search with incumbent preservation.
5. Domain procedures and memory help only when they supply the active missing layer.
6. Claims are system-level and source-grounded. Do not imply intrinsic model-only limits.

## Figures And Tables In Main Paper

- **Figure 1:** Overview figure at top of page 2.
- **Table 1:** Per-case input scale.
- **Table 2:** Evaluation layers.
- **Table 3:** Mean normalized score by method and task family.
- **Figure 2:** Trace excerpts for failure and success mechanisms.
- **Table 4:** Verifier-call frequency.
- **Figure 3:** Workspace-support ablations for OpenCode + DeepSeek V4 Pro and OpenCode + MiniMax M2.7 on Regional Coverage and Relay Constellation.

## Required Appendices

The appendix currently has nine sections in this order. Target roughly 25-40 appendix pages if the evidence supports it. Use equations and compact tables where they improve precision.

### Appendix A: Benchmark Landscape

**Role:** Position AstroReason-Bench against neighboring solver-facing satellite benchmarks, symbolic or temporal planning benchmarks, and remote-sensing agent benchmarks.

**Grounding:** Related-work sources in `references.bib` and the comparison categories already used in Table A.1.

### Appendix B: Physical and Astrodynamics Models

**Role:** Shared physical substrate before task-specific contracts. Cover propagation, frames, access geometry, pointing/footprints, slew and settling, energy, communication/routing, and compact-model caveats.

**Grounding:** `benchmarks/<family>/README.md`, verifier/source code, and related physical-model code. The appendix may inspect `/home/betelgeuse/Projects/AstroReason-Bench/` directly.

### Appendix C: Task Contracts and Metrics

**Role:** Family-by-family task definition. For each family, define submitted artifact, schema-level expectations, hard constraints, native metrics, and normalized reporting scores.

**Grounding:** `benchmarks/<family>/README.md`, verifier/source code, and `experiments/` for normalized score definitions. Put normalized score material here, not in Appendix B.

### Appendix D: Solver Baselines

**Role:** Make Table 3 interpretable. Describe per-family solver-reference abstractions, sources/citations, objectives, normalized scoring, best/second-best row construction, and why SPOT-5 has one solver-reference row.

**Grounding:** `solvers/`, solver configs/reports, `experiments/main_solver/`, and `results/main_solver/`. The underlying problems are combinatorial, so describe solver rows as available reference anchors rather than certified optima.

### Appendix E: Agent Environment

**Role:** Define evaluated agent system, workspace contents, run budget, feedback channel, system configuration, and base runtime.

**Grounding:** `runtimes/base/` and `experiments/`.

### Appendix F: Representative Prompt Fragments

**Role:** Provide compact excerpts of the agent-facing contract, shared workspace rules, library guidance, task prompts, and injected procedures that are needed to interpret trace behavior.

**Grounding:** Public prompt/task materials used in the evaluated runs. Prompt files used to create figures remain private context and must not be mentioned in paper prose.

### Appendix G: Family-Native Metrics and Ablations

**Role:** Provide raw family-native metrics behind Table 3 and the full system-level rows promised by §5.3. Cover procedure injection and memory accumulation with compact result tables and notes on what each table reports.

**Grounding:** `experiments/main_agentic/`, `experiments/main_solver/`, `experiments/skill_injection/`, `experiments/memory_accumulation/`, related reports, and result artifacts.

### Appendix H: Temporal-Robustness Check

**Role:** Record the AEOSSP shifted-horizon check that tests whether the main comparison is tied to one orbital epoch.

**Grounding:** Existing temporal-robustness reports and aggregate rows. Do not rerun agent harnesses.

### Appendix I: Additional Case Studies

**Role:** Provide paper-facing trace evidence for the mechanisms in §5. Include 4-6 concise, mechanism-indexed case studies, not a trace dump.

**Mechanisms to cover:** prompt salience and contract closure, signed-frame binding, procedure granularity, memory-prior transfer, and canonical deliverable handoff.

**Grounding:** Use `/home/betelgeuse/Projects/AstroReason-Bench/.agents/skills/trace-case-study/SKILL.md`, `experiments/`, reports, traces, and `/home/betelgeuse/Projects/AstroReason-Bench/results/`. The figure `figures/chapter5_case_study_v1.png` may be included only after its snippets and numbers are verified against reports or traces. Prompt files used to create figures are private context only and must not be mentioned in paper prose.

## Appendix Writing Rules

- Edit `paper.tex` directly; keep scratch evidence in `/tmp/astroreason_appendix_evidence.md`.
- If source conflicts are found, create or update `AstroAgent_EMNLP/CONFLICTS_SPOTTED.md`.
- Do not run agent harnesses or regenerate agent traces.
- Solver experiments may be run only if strictly necessary after existing solver reports, configs, source, and results are checked.
- Use existing `references.bib` keys first; add BibTeX only when necessary.
- Preserve or consistently update appendix labels, especially `app:benchmark-landscape`, `app:physical-models`, `app:task-contracts`, `app:solver-baselines`, `app:agent-workspace`, `app:prompt-fragments`, `app:ablation-results`, `app:temporal-robustness`, and `app:additional-case-studies`.
- Use public system names and public task-family names in the paper. Keep local evidence paths out of public prose.
- Compile with `latexmk -pdf -interaction=nonstopmode paper.tex` and inspect warnings, references, table/figure placement, TODOs, and `pdftotext` output.
