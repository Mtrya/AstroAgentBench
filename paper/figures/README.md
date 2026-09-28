# Paper figures

The SVG files are editable vector masters. The matching PDF exports are used by `paper.tex`, so ordinary pdfLaTeX compilation does not require SVG conversion tools. The original PNGs remain available for comparison.

| Figure | SVG master | PDF export |
| --- | --- | --- |
| Benchmark overview | [Overview SVG](chapter1_overview_v10.svg) | [Overview PDF](chapter1_overview_v10.pdf) |
| Agent trace mechanisms | [Trace SVG](chapter5_case_study_v1.svg) | [Trace PDF](chapter5_case_study_v1.pdf) |
| Procedure injection | [Procedure SVG](chapter5_ablation_a_v3.svg) | [Procedure PDF](chapter5_ablation_a_v3.pdf) |
| Memory accumulation | [Memory SVG](chapter5_ablation_b_v3.svg) | [Memory PDF](chapter5_ablation_b_v3.pdf) |
| Prompt and material mechanisms | [Appendix SVG](appendix_case_study_prompt_material_v1.svg) | [Appendix PDF](appendix_case_study_prompt_material_v1.pdf) |

The overview is a schematic of the benchmark workflow, with an illustrative schedule. The trace panels preserve their excerpts and numerical values in `trace_panels.json`. The sixteen ablation deltas in `ablation_deltas.csv` reproduce the figures' displayed one-decimal differences between five-case mean scores. Hatching and direct labels distinguish chart series in addition to color.

## Regeneration

From the repository root, using the project environment:

```bash
.venv/bin/python paper/figures/generate_vectors.py
```

The generator uses Matplotlib and Pillow from the project environment, the Liberation Serif font, Fontconfig's `fc-match`, and `rsvg-convert` from librsvg. It writes five SVGs and their vector PDF exports. Use `--output-dir /path/to/output` to inspect alternate exports. Generation reads only the adjacent figure text and chart data; it does not execute benchmark experiments. The overview's inline icons are [Material Symbols](https://fonts.google.com/icons) path data (Apache-2.0), embedded directly in the generator.

Text remains selectable in the SVG and PDF exports. The diagrams use a 160 mm canvas with body text above 8 points at the manuscript's full text width; the chart labels are 8.5 points on a 3.15-inch canvas. If the figures are resized, check their final text size and layout in the compiled paper.
