# Reviewer 3 Rebuttal Draft

Thank you for the encouraging review. We appreciate that you recognize the motivation of extending language-agent benchmarks beyond web/coding tasks into physics-constrained planning, and that you find the validity/value evaluation and trace-level analysis useful.

**Experimental scope and extensibility.** We agree that five held-out cases per family and five evaluated systems limit generalization. We will therefore present Table 3 as a first evaluation and scope its conclusions to the systems tested.

We thank the reviewer for suggesting locally deployed models. During rebuttal, we evaluated OpenCode + Qwen3.6-27B, a self-hosted open-weight model, on SPOT-5 over three repetitions of the five held-out cases.

| Repetition | Case 8 | Case 28 | Case 1021 | Case 1403 | Case 1506 |
|---:|---:|---:|---:|---:|---:|
| 1 | 100.00 | 0.00 | 54.80 | 0.00 | 64.36 |
| 2 | 100.00 | 34.37 | 0.00 | 0.00 | 0.00 |
| 3 | 100.00 | 34.37 | 0.00 | 35.60 | 0.00 |

On SPOT-5, the self-hosted 27B system performs in the lower range of the evaluated systems, adding open-weight coverage without changing the main empirical picture.

Model coverage is only one part of the concern. We also agree that the five systems use general-purpose CLI scaffolds rather than specialized research architectures. Within these systems, the procedure-injection and memory-accumulation studies examine how two forms of agent support affect planning performance. Broader frontier-model replication and architecture coverage remain expensive, so we will release the complete benchmark and evaluation framework for groups with greater model access to scale this evaluation.

**Engineering fidelity.** AstroReason-Bench targets preliminary mission design and planning, where TLE/SGP4 propagation is an industry-standard modeling choice. AEOSSP, Stereo Imaging, and Regional Coverage use real catalogued satellites from frozen TLEs and propagate their states with SGP4; Revisit and Relay use deterministic J2 propagation for constellation architecture search. The verifiers reconstruct frame conversion, visibility, pointing, slew, energy, link geometry, and routing from submitted decisions. This provides substantially more physical and operational structure than scheduling evaluations based only on precomputed opportunities or two-body/J2 observation dynamics, while retaining reproducible automatic evaluation. We will state the mission design and planning target more prominently and distinguish it from full engineering complexity.
