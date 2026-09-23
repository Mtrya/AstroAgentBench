# Reviewer 1 Rebuttal Draft

Thank you for the careful review. We are glad the verifier-backed evaluation, the task-formulation vs solution-construction taxonomy, and the seven-family scope are seen as useful. We respond to the main concerns below.

**NLP/EMNLP relevance.** Space mission planning is the domain environment; the NLP research object is language-mediated task formulation and adaptation: how agents transform natural-language specifications and documentation into executable task models, revise them through feedback, and transfer textual procedures and prior experience. This places AstroReason-Bench in the lineage of WebArena, SWE-bench, and ScienceWorld, which study language agents through situated interaction, while extending that research to scientific planning under physical constraints. Our trace analysis distinguishes task-contract misformulation from solution-construction failure, and our procedure and memory ablations test how language-encoded knowledge changes behavior. We will foreground this framing in the introduction.

**Scale and uncertainty.** We agree that five held-out cases per family only support an initial evaluation rather than fine-grained rankings. To report our case variation transparently, the table below reports mean normalized score [95% paired case-bootstrap CI].

| System | AEOSSP | Regional | Relay | Revisit | SatNet | SPOT-5 | Stereo |
|---|---:|---:|---:|---:|---:|---:|---:|
| Claude | 58.5 [29.1,73.9] | 21.2 [20.7,22.2] | 12.3 [0.0,36.8] | 76.5 [73.7,78.8] | 60.4 [29.2,79.4] | 44.0 [11.1,76.8] | 19.2 [0.3,55.7] |
| Codex | 72.9 [69.9,76.1] | 72.1 [60.0,80.4] | 64.9 [55.8,77.7] | 69.6 [61.9,76.0] | 69.5 [61.8,77.1] | 61.9 [44.6,82.2] | 68.9 [33.6,93.7] |
| Kimi | 72.0 [69.4,74.1] | 73.2 [67.4,77.4] | 57.8 [42.8,72.6] | 73.4 [69.8,78.1] | 66.1 [58.9,75.0] | 61.9 [44.6,82.2] | 0.3 [0.0,0.8] |
| OC+DPSK | 71.4 [69.1,73.7] | 35.8 [24.2,44.9] | 35.7 [11.6,59.8] | 71.0 [70.0,71.9] | 60.2 [50.1,70.4] | 60.9 [44.0,82.2] | 13.0 [0.0,39.0] |
| OC+MiniMax | 36.4 [16.6,52.7] | 17.7 [10.0,24.8] | 0.0 [0.0,0.0] | 0.0 [0.0,0.0] | 37.5 [16.6,55.8] | 37.5 [7.2,71.1] | 0.0 [0.0,0.0] |

The intervals support broad gaps but not close rankings. On Regional Coverage, Kimi's interval [67.4,77.4] is separated from Claude, OC+DPSK, and OC+MiniMax; wide overlap elsewhere marks comparisons that require more cases. We will present Table 3 as an initial evaluation rather than a closed leaderboard. Anonymous Data and Software ZIPs are already attached to the submission, they include cases, generators, verifiers, and solver references; we will also release detailed experiment code and exact traces to support larger evaluations.

**Solver baselines and cross-family interpretation.** We read this concern as having two parts. First, on baseline quality, no solver row is a simple heuristic: each is an established solver reference, an adopted open-source implementation, a reimplementation of a published method, or a canonical published/challenge result. We do not label these rows "optimal" because every family contains NP-hard scheduling, coverage, routing, or design subproblems, so no oracle optimum is available.

On cross-family interpretation, agent scores are normalized directly from verified family-native mission metrics under fixed family scoring rules; solver scores do not enter this calculation. Thus reference-solver strength cannot explain an agent's 80-versus-50 cross-family difference. Such scores profile performance under each family's mission-value rubric; solver-relative gaps compare solution quality only within a family. We will state these interpretations explicitly and use native metrics and traces to explain family-specific strengths and failures.

**Related work and baseline length.** On related work, we agree it's long and will shorten it. On baselines, we would appreciate clarification: the main text currently gives a compact one-paragraph inventory of solver-reference names, with all per-family details already in Appendix D. We are unsure whether the concern is length or presentation; a short pointer to what to change would help us act on this comment.

**Normalized score interpretability.** The full aggregation rule is already in Appendix C and the family-native metrics are in Table 12. For example, Claude's AEOSSP score of 58.45 corresponds to 5/5 valid submissions, weighted coverage ratio 0.570, coverage ratio 0.594 (59.4% of targets covered), 9477s turnaround time, and 16.5 kWh power consumption. We'll also add a running example which will include how verifier produces family-native metrics and how they are aggregated into normalized scores in the camera-ready version.

**Spelling.** We will also fix the specialized/specialised spelling inconsistency noted by the reviewer.
