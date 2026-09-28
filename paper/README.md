# AstroAgentBench manuscript

This directory contains the available manuscript source and the figures and tables needed to build it. It uses the final camera-ready layout with full author metadata. The project name has been updated to AstroAgentBench.

## Build

Use a TeX distribution with pdfLaTeX, BibTeX, latexmk, and the packages requested by `paper.tex`, including `inconsolata` and `fvextra`. From this directory:

```bash
latexmk -pdf -interaction=nonstopmode -halt-on-error -outdir=build paper.tex
```

The compiled document is `build/paper.pdf`. The included bibliography, ACL style files, and vector PDF figures are sufficient; no experiment execution or figure regeneration is needed.

Only the manuscript's required figure versions are included. The result tables remain in the source. The ACL style files retain their upstream notices.

The five figures have editable SVG masters and matching PDF exports, with the original PNGs preserved. See [figure sources and regeneration](figures/README.md).
