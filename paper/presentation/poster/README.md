# AstroAgentBench conference poster

An A0 portrait poster built around a space-mission illustration, independent feasibility and value checks, the seven-family results, and the mechanisms observed in strong runs.

## Build

From the repository root, with Pillow installed in the project environment and `rsvg-convert` on `PATH`:

```bash
.venv/bin/python paper/presentation/poster/render.py
```

The renderer uses saved local assets and requires no image-generation service or network connection. Outputs are `build/poster.svg` (editable master), `build/poster.pdf` (841 × 1189 mm), and `build/poster.png` (screen preview). The PDF has embedded fonts. The SVG embeds its artwork and fonts and groups content into named layers; applications that do not honor embedded SVG fonts can use the included font files. Build intermediates are under `build/`.

Rendering dependencies used for this version: Python 3.13, Pillow 12.2.0, librsvg 2.63.4, Cairo 1.18.6, and Pango 1.58.2. The bundled Noto fonts are licensed under SIL OFL 1.1; see `fonts/LICENSE.txt`. The renderer supplies a local Fontconfig configuration, without installing fonts system-wide.

## Edit

- `scene.json` owns the title, mission targets, satellite placements, observation times, access windows, and result values. Change target coordinates to move the target and both observation footprints and cones together. Change an observation time to update the spacecraft label and scheduled time marker together.
- `render.py` owns typography, positions, vector geometry, and page composition. The plot, validity spotlight, and count of families exceeding the reference are derived from the same result data.
- `artwork/` contains the saved generated Earth background and transparent satellite sprite, their generation prompts, and a vector conversion of the existing project logo. The same spacecraft sprite is reused for both observations. The shared project QR is converted to vector modules during the build.
- `design/` retains the approved composition study and its prompt for visual comparison. It is a design reference, not the scientific result figure.

Text, plots, orbits, observation cones, footprints, timing, icons, and the QR are editable vectors. The Earth and spacecraft are raster artwork; the poster is not an entirely vector illustration. The Earth background is 1448 × 1086 pixels, approximately 69 pixels per inch at its placed width; the quantitative and textual elements remain resolution-independent.

Direct edits to the SVG in a vector editor are possible but are overwritten on rebuilding. Transfer changes into the scene data or renderer when they need to survive future builds. Identical inputs produce identical SVG source; PDF metadata and rasterization can vary across renderer versions and environments.

## Scientific scope

The orbital scene and its timing are schematic, not physical simulation outputs. Both satellites observe the same target; overlap and viewing angle illustrate product-level stereo value. Local verifier feedback belongs to planner construction, while the final submitted plan receives independent evaluation. No arrow represents live spacecraft control.

The 35 agent-system means and seven reference means are transcribed from the manuscript's main-results table, with five held-out cases per family. The reference is the best available reference score selected per case and then averaged, not a certified optimum or a single uniformly chosen solver. The 35/35 spotlight is overall validity; 68.91 and 0.25 are the corresponding five-case Stereo Imaging means. The mechanism strip summarizes trace observations and is not a causal ablation claim.

Before submission, inspect the exported PDF and use the local conference-named copy in the presentation submission directory. No upload is performed by the renderer.
