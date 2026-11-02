#!/usr/bin/env python3
"""Composite a webcam recording onto a solid background (default: pure white).

Frames are matted one by one with Robust Video Matting (RVM, MobileNetV3
backbone), whose recurrent states keep the matte temporally stable. The audio
track is passed through and re-encoded to AAC.

The webcam image is downscaled before matting. In the final talk video the
webcam appears only as a small corner overlay, so a processing width well
below the recording resolution is enough and keeps CPU-only runs tractable.

Usage (CPU-only torch wheels; drop the index flags if you have a GPU):
    uv run --with torch --with torchvision --with numpy \
        --index-url https://download.pytorch.org/whl/cpu \
        --extra-index-url https://pypi.org/simple \
        --index-strategy unsafe-best-match \
        python replace_background.py webcam.mkv webcam-white.mp4

First run downloads the model weights via torch.hub (network required once).
"""

import argparse
import subprocess
import sys

import numpy as np


def probe(path):
    out = subprocess.run(
        ["ffprobe", "-v", "quiet", "-select_streams", "v:0",
         "-show_entries", "stream=width,height,r_frame_rate",
         "-of", "csv=p=0", path],
        capture_output=True, text=True, check=True).stdout.strip()
    w, h, rate = out.split(",")
    num, den = rate.split("/")
    return int(w), int(h), float(num) / float(den)


def even(n):
    return int(round(n / 2.0)) * 2


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("input", help="webcam recording (any ffmpeg-readable format)")
    ap.add_argument("output", help="output video, e.g. webcam-white.mp4")
    ap.add_argument("--width", type=int, default=640,
                    help="processing and output width in pixels (default: 640)")
    ap.add_argument("--color", default="255,255,255",
                    help="background color as R,G,B (default: 255,255,255)")
    ap.add_argument("--downsample-ratio", type=float, default=0.5,
                    help="internal matting resolution factor (default: 0.5)")
    args = ap.parse_args()

    import torch

    src_w, src_h, fps = probe(args.input)
    out_w = even(args.width)
    out_h = even(src_h * args.width / src_w)
    bg = np.array([int(c) for c in args.color.split(",")], dtype=np.float32)
    print(f"{args.input}: {src_w}x{src_h} @ {fps:.3f} fps -> {out_w}x{out_h}, "
          f"background {tuple(bg.astype(int))}", file=sys.stderr)

    model = torch.hub.load("PeterL1n/RobustVideoMatting", "mobilenetv3",
                           pretrained=True, trust_repo=True)
    model.eval()

    decoder = subprocess.Popen(
        ["ffmpeg", "-v", "error", "-i", args.input,
         "-vf", f"scale={out_w}:{out_h}", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
        stdout=subprocess.PIPE)
    encoder = subprocess.Popen(
        ["ffmpeg", "-y", "-v", "error",
         "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{out_w}x{out_h}",
         "-r", f"{fps:.6f}", "-i", "-",
         "-i", args.input, "-map", "0:v:0", "-map", "1:a:0?",
         "-c:v", "libx264", "-preset", "medium", "-crf", "18",
         "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k", args.output],
        stdin=subprocess.PIPE)

    frame_size = out_w * out_h * 3
    bg_t = torch.from_numpy(bg / 255.0).view(1, 3, 1, 1)
    rec = [None] * 4
    n = 0
    with torch.no_grad():
        while True:
            buf = decoder.stdout.read(frame_size)
            if len(buf) < frame_size:
                break
            frame = np.frombuffer(buf, dtype=np.uint8).reshape(out_h, out_w, 3).copy()
            src = torch.from_numpy(frame).permute(2, 0, 1).unsqueeze(0).float() / 255.0
            fgr, pha, *rec = model(src, *rec, args.downsample_ratio)
            comp = fgr * pha + bg_t * (1.0 - pha)
            out = (comp[0].permute(1, 2, 0) * 255.0).byte().numpy()
            encoder.stdin.write(out.tobytes())
            n += 1
            if n % 100 == 0:
                print(f"  {n} frames ({n / fps:.1f}s)", file=sys.stderr)

    encoder.stdin.close()
    encoder.wait()
    decoder.stdout.close()
    decoder.wait()
    if encoder.returncode != 0 or decoder.returncode != 0:
        sys.exit("ffmpeg failed")
    print(f"done: {n} frames -> {args.output}", file=sys.stderr)


if __name__ == "__main__":
    main()
