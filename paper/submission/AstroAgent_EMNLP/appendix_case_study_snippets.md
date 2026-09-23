# Appendix Case-Study Visual Snippets

This working file preserves the Appendix G trace-story material before figure rendering. It is intentionally not public paper text. Public prose should use stable paper-facing names and should not expose local trace paths or row identifiers.

## Figure Scope

The Appendix G figure should complement the main-text montage rather than repeat it. The selected mechanisms are:

- Prompt salience: a short task cue and case-file inspection help close the contract around a private schema.
- Signed-frame binding: a signed field is named, but the local-frame handedness is not bound early enough.
- Memory transfer: prior notes change the search basin, helping under structural match and regressing under mismatch.

The trace panel uses only `Observation`, `Action`, `Thought`, and `Annotation` primitives.

## Panel A: Prompt Salience

Evidence sources checked: regional coverage schema/self-verification report; regional coverage trace export for the first failed run; aggregate regional coverage report.

### Top Panel

```text
Mission: Submit regional strip_observation actions.
Material: prompt says "using the files in `case/`";
root contract requires type="strip_observation"
and roll_deg.
```

### Middle Panel

```text
Trace:
Action: "ls /app/workspace/case/"
Observation: coverage_grid.json, manifest.json,
  regions.geojson, satellites.yaml
Thought: "I'll start by understanding the problem
  by reading the case files."
...
Action: validates a schema with roll_angle_deg
Observation: "Validation passed! Total actions: 64"
Annotation: private checks never query the root verifier.
Observation: official parser reads num_actions = 0;
  weighted coverage = 0.0000
```

### Bottom Panel

```text
Final Result: valid empty schedule
```

## Panel B: Signed Frame

Evidence sources checked: stereo Kimi cross-track case-study report; stereo Kimi trace export; diagnostic counterfactual table in the report.

### Top Panel

```text
Mission: Raw observations include signed
off_nadir_across_deg.
Material: the prompt names a cross-track field
and boresight formula,
but not the handedness of across_hat.
```

### Middle Panel

```text
Trace:
Observation: valid=true while coverage_ratio = 0.0000
Observation: repeated product diagnostics show
  overlap_fraction=0.0
Thought: "across = np.cross(along, nadir) NOT
  np.cross(nadir, along)!"
...
Action: negate submitted off_nadir_across_deg
  in diagnostic replays
Observation: case_0002 coverage 0.0165 -> 0.8926
Observation: case_0005 coverage 0.0071 -> 0.9716
Annotation: syntax validity did not bind the signed frame.
```

### Bottom Panel

```text
Final Result: hard-valid, low-value products
```

## Panel C: Memory Transfer

Evidence sources checked: memory-accumulation regional/relay case-study report; memory-accumulation aggregate regional and relay reports; shared memory prompt fragment.

### Top Panel

```text
Mission: Use prior notes, then check
the current verifier.
Material: "Treat memory and skills as
guidance, not authority."
```

### Middle Panel

```text
Trace:
Observation: prior regional note records verified
  weighted coverage 0.9235
Action: read the note before solver construction
Observation: valid 64-action incumbent;
  weighted coverage = 0.8832
...
Observation: relay memory rescues a zero-service case
  to service_fraction = 1.0
Observation: the same relay prior can regress:
  0.1852 vs no-memory 0.9222
Annotation: memory transfers priors, not guarantees.
```

### Bottom Panel

```text
Final Result: selective transfer
```
