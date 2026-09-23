# Chapter 5 Case-Study Figure Snippets

## Layout Rules

- Three reference-style montage panels.
- Tabs: `Private World`, `Calibration`, `Adaptive Search`.
- Only use `Observation`, `Action`, `Thought` and `Annotation` as line primitives.
- Use `...` to mark skipped lower-information trace steps.
- Highlight load-bearing text with `▌...▌`.
- Do not include trace sequence IDs, local paths, system names, or case IDs inside panel text.

## Panel A: Private World

### Top Subcard

```text
**Mission**: Create a valid observation schedule that forms high-quality stereo products under geometry and timing constraints.
```

### Middle Subcard

```text
**Trace**:
Action: "Bash(ls case/)"
Observation: case files expose stereo-product geometry, footprint overlap, convergence, pixel-scale, and pari-quality fields.
Thought: "Now I ▌understand▌ this problem. I need to build a stereo_imaging scheduler."
...
Action: solution = {▌"stereo_observations"▌: []}
Observation: "Stereo pairs: 98/141; Coverage: 69.5%; Total conflicts: ▌35▌; Cross target: 19"
Thought: "the evaluation framework ▌might only care▌ about geometric validity"
Annotation: private checker accepts the artifact despite the conflict count.
Observation: "▌Issues found: 0▌"
```

### Bottom Subcard

```text
Final Result: Invalid
```

## Panel B: Implementation Calibration

### Top Subcard

```text
**Mission**: Design a revisit constellation and observation schedule that satisfieds off-nadir and slew constraints.
```

### Middle Subcard

```text
...
Observation: "Diff: 17601.56 m; Estimated score: 6.00 hours"
Thought: "Let me ▌run the verifier▌ to check validity"
Action: "Bash(./verifier solution.json)"
Observation: off-nadir angle 30.041 deg exceeds 30.000 deg
Thought: "my propagator ▌doesn't match▌ the verifier exactly"
Action: ▌Uses brahe J2 numerical propagator and exact frame rotations▌
...
Observation: "errors": []; "num_satellites": 10; "threshold_violation_count": 0
```

### Bottom Subcard

```text
Final Result: Valid, Great score
```

## Panel C: Adaptive Search

### Top Subcard

```text
**Mission**: Add relay assets and link actions to satisfy communication demands.
```

### Middle Subcard

```text
Thought: "writing an empty but valid `solution.json` first"
Action: {"added_satellites": [], "actions": []}
Observation: demand_001 30 / 60; demand_003 76 / 90
Thought: "▌misses come from brief disconnected periods in the ISL graph▌"
...
Observation: "unserved_demand_sample_count": 55
Thought: "...▌rank candidate relays only on the 55 currently unserved samples▌"
...
Observation: service_fraction = ▌1.0▌; worst_demand_service_fraction = ▌1.0▌
```

### Bottom Subcard

```text
Final Result: Valid, Perfect score
```

## Caption Draft

Figure X: Compressed trace excerpts for three mechanisms in Section 5. Left: a Stereo Imaging run builds and validates a private product-level artifact rather than the required raw-action artifact. Middle: a Revisit Constellation run uses checker feedback to align propagation and scheduling with the official constraints. Right: a Relay Constellation run narrows search around unserved demand samples and repairs a hard altitude-boundary rejection.

## Appendix F Additional Mechanism Figure Snippets

These snippets are for the appendix-only figure. They intentionally avoid repeating the three mechanisms already covered in the main-text figure.

## Panel A: Prompt Salience

```text
Mission: Submit strip_observation actions, not strip polygons or coverage claims.
Contract: type = "strip_observation"; roll_deg is the signed roll field

Trace:
User prompt: "using the files in `case/`"
Thought: "I'll start by understanding the problem by reading the case files."
Action: "ls case/"
Observation: coverage_grid.json, manifest.json, regions.geojson, satellites.yaml
...
Private check: "Valid JSON, 64 actions"
Schema checked: roll_angle_deg
Aggregate: five valid files; parsed strip actions = 0 in every row
Official result: weighted coverage = 0.0000
Annotation: case files and self-checks displaced the root contract.

Final Result: valid empty schedule
```

## Panel B: Signed Frame

```text
Mission: Raw observations include signed off_nadir_across_deg.
Material: "off_nadir_across_deg tilts cross-track in the satellite local frame"

Trace:
Observation: "overlap_fraction=0.0" despite hard-valid observations
Private axis: across = nadir x along
Verifier axis: across = along x nadir
Metric layer: valid=true can coexist with coverage_ratio = 0.0000
Counterfactual: negating the across sign changes two near-zero schedules into high-coverage schedules
Mechanism: the prompt names a signed field but not the handedness; verifier feedback arrives as product geometry.
Annotation: syntax validity did not bind the frame convention.

Final Result: hard-valid, low-value products
```

## Panel C: Memory Transfer

```text
Mission: Use prior notes as guidance, then check the current verifier.
Material: "Treat memory and skills as guidance, not authority."
Prior note: verified weighted coverage 0.9235; exact candidates; local swaps
Matched regional case: verifier weighted coverage 0.8832; 64 actions
...
Relay prior: tested constellation family and per-sample routing loop
Matched relay case: service_fraction = 1.0; worst_demand_service_fraction = 1.0
Mismatched relay case: memory service_fraction = 0.1852; no-memory service_fraction = 0.9222
Mechanism: external materials change the search basin, but the current demand windows still arbitrate value.
Annotation: memory transfers priors, not guaranteed objective alignment.

Final Result: selective transfer
```
