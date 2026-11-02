# AACL-IJCNLP 2026 presentation material

Conference-mandated material for the paper, built from the same assets and numbers as the manuscript. Requirements come from `../aacl_ijcnlp_instructions.pdf` (submission via Underline; slides/poster PDF/PPT/PPTX up to 20 MB; video up to 1 GB; poster prints A0 portrait).

## Contents

- `slides/slides.tex` — 16:9 Beamer deck, 14 slides for the 10-minute talk. Build: `latexmk -pdf -interaction=nonstopmode -halt-on-error -outdir=build slides.tex` → `build/slides.pdf`.
- `poster/` — illustrated A0 portrait poster with an editable SVG master. From the repository root, run `.venv/bin/python paper/presentation/poster/render.py` to create `poster/build/poster.svg`, `poster/build/poster.pdf`, and `poster/build/poster.png`. See `poster/README.md` for dependencies, assets, and editing instructions.
- `video/` — the 10-minute talk: `script.md` (verbatim English narration, ~1,240 words ≈ 10 min at ~120–130 wpm, with per-slide timing, delivery notes, and recording/submission checklist) and `replace_background.py`, which composites a webcam recording onto a pure-white background (Robust Video Matting) before it is overlaid on the slides. Local recordings and processed outputs (`*.mkv`, `*.webm`, `*-white.mp4`) are gitignored.
- `assets/` — shared figures: paper figure exports, promotion images from the `main` branch (`docs/assets/`), the project logo, and QR codes (regenerate with `qrencode -o qr_x.png -s 10 -m 2 "<url>"`).

## Submission checklist

1. Files in `submit/` are named per the instructions (`AACL 2026_main-239_*`; ID confirmed, main-conference long paper → 10-minute video).
2. Video: record slides fullscreen at 1920×1080 with webcam overlay (bottom-right default) following `video/script.md` — on Linux use OBS; for a clean white backdrop, run the webcam track through `video/replace_background.py` first; export mp4 ≤ 1 GB.
3. Upload all three through the Paperform link in the instructions; the speaker information/release form is the same form. The latest submission replaces earlier ones.
4. `submit/form-texts.md` holds the abstract, keywords, and short-bio texts the form asks for.
