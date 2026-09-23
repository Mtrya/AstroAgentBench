# Reviewer 2 Rebuttal Draft

Thank you for the positive and constructive review. We appreciate that you recognize the automatic verifier-backed evaluation, absence of manual repair, empirical analysis of agent performance, and controlled studies of verifier usage, procedure injection, and memory accumulation.

**Benchmark contribution.** The paper is primarily a benchmark and evaluation contribution. We view this as the intended contribution: AstroReason-Bench provides the task substrate: seven executable planning families, independent verifiers, and solver references that make both validity and mission value checkable. We then use this substrate to study how current language-agent systems behave under physically grounded planning: where they fail, when verifier feedback helps, etc.

**Model versus harness/scaffold.** We agree that the main table is an agent-system comparison, not a model-only leaderboard. The systems differ in model and harness. The intended claim is therefore system-level: the table measures complete language-agent systems under the same benchmark contract and time budget. We will make the claim clearer.

Beyond the system-level comparison in Table 3, our controlled studies provide partial component-level attribution by varying individual scaffold factors. For OpenCode+DPSK, the procedure pack improves Regional Coverage by 19.46 normalized points; Codex-derived memory improves Regional Coverage by 24.28 points, and DeepSeek-derived memory improves Relay Constellation by 18.53 points. These experiments do not exhaust the full model x harness x prompt matrix, but they identify how procedure support and accumulated experience contribute to the observed system-level behavior.

We will release cases, generators, verifiers, solver references, experiment code, and exact traces to enable future work to run stricter model-only or harness-only comparisons on the same task substrate.
