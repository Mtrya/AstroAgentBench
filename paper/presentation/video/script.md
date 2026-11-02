# AstroAgentBench — 10-minute talk script (AACL-IJCNLP 2026)

Target: 10:00 total, with a 10-second closing buffer. Pace ≈ 120–130 words/min; the narration is ~1,240 words. Slide numbers refer to `slides/build/slides.pdf`. Times are cumulative targets, not hard cuts: if a section runs long, compress the next one, but never rush slides 8–11, which carry the results and analysis. The setup section (slides 4–7) is deliberately compressed so that the results and analysis receive the larger share of the talk.

Delivery notes (live talk): use the mouse as a virtual laser pointer; pause ~1.5 s after each slide change; let the audience absorb the figure before speaking about it. The recording checklist at the end covers the pre-recorded format, where the pointer note still helps viewers follow the figures.

---

## Slide 1 — Title (0:00 → 0:25)

Hello everyone, and thank you for joining this talk. On behalf of my colleagues at Fudan University, the Shanghai Innovation Institute, and the OpenMOSS Team, I am delighted to present AstroAgentBench: Evaluating Agentic Planning on Space Mission Planning Tasks. This is joint work with Xinchi Chen, Jingjing Gong, Xuanjing Huang, and Xipeng Qiu.

## Slide 2 — Hook: "How should these satellites spend the next 12 hours?" (0:25 → 1:25)

Consider a constellation of Earth-observation satellites, each planning its next twelve hours. A target stays in sight for only a few minutes per orbit pass. Every slew toward the next target burns both time and battery power, and the energy and memory budgets are shared across the entire schedule, so each observation the agent accepts trades off against every other. This is where language-model fluency becomes dangerous. A plan that reads perfectly well can send a satellite to a target after its window has closed, or drain the battery hours before the horizon ends. And once the plan is uplinked, it is final. The central question of this work is therefore concrete: can an LLM agent compute a plan that survives contact with orbital physics?

*Point at the three panels as the scenario unfolds: observe, turn, observe again. Pause for one second after the closing question before advancing.*

## Slide 3 — Why a new benchmark (1:25 → 2:10)

Three gaps motivate this benchmark. First, LLM-for-Space evaluations remain fragmented across task formulations, simulators, and success criteria. Second, a fluent artifact is rarely checked against a physically grounded, deterministic verifier. Third, a plan can satisfy the schema and still observe nothing of value, so validity alone is too weak. These gaps become three questions. Can agents pass external feasibility checks, rather than merely describe plausible strategies? When a plan is valid, how close does it come to specialized solver references? And which system conditions, such as verifier use, domain guidance, and accumulated experience, explain the variation?

## Slide 4 — Benchmark overview (2:10 → 2:50)

Each mission comes as a self-contained case: mission files, documentation, scientific libraries, and a required solution schema. The agent then works as an aerospace engineer rather than filling in a template. It reads the brief, writes and runs its own code, and constructs the planning procedure from scratch, producing an executable artifact such as an observation timeline, an antenna schedule, or a constellation design. After the run, an independent verifier re-simulates the plan, checks feasibility, and scores its mission value. The full suite contains 116 cases across seven families.

*Trace the left-to-right flow once with the pointer: case package → agent → artifact → verifier checklist.*

## Slide 5 — Seven families (2:50 → 3:30)

The seven families span four kinds of planning decisions. For Earth observation, AEOSSP schedules agile point observations, SPOT-5 selects photographs, Regional Coverage builds roll-only strips, and Stereo Imaging forms stereo products. SatNet allocates ground-station contacts. Revisit Constellation designs a constellation for revisit performance, and Relay Constellation augments a network with new satellites and link plans. Input scale ranges from eight photographs to eighteen thousand grid cells. Orbits come from real CelesTrak TLE snapshots, and SatNet and SPOT-5 are normalized from published benchmarks.

## Slide 6 — Evaluation contract (3:30 → 4:25)

How do we score such a plan? Evaluation has two layers. First, validity: the artifact must arrive and parse, and the verifier then reconstructs the plan over the mission horizon, recomputing time windows, geometry, and resource budgets. Only valid plans reach the second layer, where family-native metrics such as coverage or service are normalized to a zero-to-one-hundred scale. Missing or invalid plans score zero. On one AEOSSP test case, Claude Opus completes over two-thirds of all requested observations within the energy budget and earns a score of 70.9. On a fifth case, the same system submitted an empty schedule, which scored zero and pulled its five-case mean down to 58.45. Every plan is judged first on validity, then on value.

## Slide 7 — Setup (4:25 → 4:55)

Next, we evaluate five agent systems: Claude Code with Claude Opus 4.6, Codex CLI with GPT-5.4, Kimi CLI with Kimi K2.6, and OpenCode with MiniMax M2.7 and DeepSeek V4 Pro. A system couples the model with its harness and workspace, because the model alone does not solve mission planning. Each run receives two hours on eight CPU cores, and the artifact is scored afterwards without human repair.

## Slide 8 — Main results (4:55 → 5:35)

So, what happens when these systems face the held-out cases? Here is the core finding: agents can plan for real. The best agent row beats the solver reference on four of seven families, yet performance remains highly uneven. The matrix reports mean normalized score per family over five cases, with the best solver reference marked by a dashed line. Read it column by column, within a family rather than across families. Two systems, Codex and Kimi, are verifier-valid on all thirty-five cases.

*Point at the dashed solver marks on AEOSSP and SatNet, then at the gap on Stereo Imaging.*

## Slide 9 — Reading the results (5:35 → 6:25)

Three readings follow from this matrix. First, validity is achievable: two systems are valid on all thirty-five cases. But valid does not mean valuable, because even fully valid systems leave large score gaps. Second, the best agent row beats the solver reference on four of seven families, by up to 7.9 points on SatNet, and stays within 3 points on AEOSSP. Third, capability is uneven: Regional Coverage and Stereo Imaging still lag by thirteen to twenty-seven points. And no single agent dominates. Kimi leads Regional Coverage yet scores near zero on Stereo Imaging, while Claude leads Revisit Constellation but struggles on Relay.

## Slide 10 — Failure modes (6:25 → 7:15)

These averages hide important failure patterns. Trace evidence separates two layers. Task-formulation failures arise when the system builds a self-imposed task: an inferred schema, a hallucinated objective. On Stereo Imaging, one run produced valid observations whose footprints never formed stereo products, and its local validation accepted what the official verifier rejects. Solution-construction failures arise when the task is understood but the run cannot build, improve, and preserve a high-value plan, through weak search, brittle code, or late verifier use. Across all 175 runs, 12.6 percent end invalid, 9.1 percent submit a valid artifact that scores zero, and 22.3 percent commit to an artifact before reading the task contract.

*Slow down for the three percentages; they are the slide's payload.*

## Slide 11 — Trace evidence (7:15 → 8:05)

Three traces make this concrete. On the left, a Stereo Imaging run constructs a private world, with its own product schema and validation, and ends invalid with zero score. In the center, a Revisit run writes its own orbital model, and the verifier reports an off-nadir error just four-hundredths of a degree beyond the thirty-degree limit. The run then repairs its propagation and frame handling until they match the benchmark. On the right, a Relay run writes an empty but valid solution first, then targets the fifty-five unserved demand samples, reaching full service while preserving that valid incumbent.

## Slide 12 — Success mechanisms (8:05 → 8:40)

What do strong runs do differently? Two mechanisms stand out. First, implementation calibration: agent-written code is repaired against verifier disagreement before it is trusted. Second, case-adaptive search: the run finds this case's bottleneck and keeps its best verified plan. The table agrees: systems that call the verifier in every case group align their hand-built solvers with the official model, while the shaded cells mark runs where calibration never happened. Strong runs synthesize the search policy during the run.

## Slide 13 — Ablations (8:40 → 9:10)

Can we help the agent from the outside? Ablations tell the same story from the other side. Injecting human-written procedures, or memory distilled from prior runs, helps conditionally, by up to twenty-four points when DeepSeek reads Codex's prior notes on Regional Coverage. Support helps precisely when it supplies the missing formulation, calibration, or search discipline. It never replaces them.

## Slide 14 — Takeaways (9:10 → 9:50)

To conclude: agentic space mission planning shows nontrivial ability and clear brittleness. AstroAgentBench gives the community executable mission planning with external verification and graded mission value, and it shows that success tracks verifier-calibrated implementations and disciplined, case-adaptive search, which is an agent-system property. Everything is public: code, cases, verifiers, solver references, and run traces. We welcome collaborators on new task families, and we invite you to try your own agent system and submit results. Thank you.

*(10-second closing buffer; do not fill it.)*

---

# Recording and submission notes

**Delivery mode.** The narration above is written for a live talk. For the submitted video, record it as a standalone performance; the pointer note remains useful because it tells viewers where to look.

**Setup (from the conference instructions):** quiet room; clean backdrop; key light in front, slightly off-center; medium close-up framing (shoulders to head); avoid stripes/checks; silence phone and notifications; use any headset/USB/lavalier microphone rather than the laptop mic; if wearing glasses, check light reflection first. Webcam overlay position is free (bottom-right is the default convention).

**Recording on Linux:** the conference recommends OBS (<https://obsproject.com/>). Record the slides fullscreen at 1920×1080 plus the webcam as a separate track or file; for a clean white backdrop, run the webcam recording through `replace_background.py` (`uv run --with torch --with torchvision --with numpy python replace_background.py webcam.mkv webcam-white.mp4`) and overlay it bottom-right (`ffmpeg -i slides.mp4 -i webcam-white.mp4 -filter_complex "[1:v]scale=480:-1[wm];[0:v][wm]overlay=W-w-40:H-h-40" -c:a aac out.mp4`). Export mp4. PowerPoint recording or ScreenPal are the officially suggested routes on Windows/macOS if you record on another machine; any tool is accepted as long as the format is mp4/avi/mov/m4v, ≤ 1 GB (Underline broadcasts at max 1920p).

**Submission:** upload via the Paperform link from the instructions; latest submission wins. File naming: `AACL 2026_<paper-id>` prefix for video, poster, and slides (e.g., `AACL 2026_main-239`). Confirm the paper ID before naming.

**Checklist before recording:** rehearse slides 8–11 timing (they carry the results); verify slide PDF is the current build; do a 30-second audio test and watch it back for mic level and room echo.
