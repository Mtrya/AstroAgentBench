#!/usr/bin/env python3
"""Rebuild the paper's editable SVG figures and vector PDF exports."""

from __future__ import annotations

import argparse
import csv
from functools import lru_cache
from html import escape
import json
import math
from pathlib import Path
import re
import subprocess

from PIL import ImageFont


HERE = Path(__file__).resolve().parent
SERIF = "Liberation Serif"
INK = "#16293d"
BLUE = "#17558b"
PURPLE = "#655fa5"
WIDTH = 1200
BODY = 22


@lru_cache(maxsize=None)
def font(size: int, bold: bool = False, italic: bool = False):
    style = "Bold Italic" if bold and italic else "Bold" if bold else "Italic" if italic else "Regular"
    path = subprocess.check_output(
        ["fc-match", "-f", "%{file}", f"{SERIF}:style={style}"], text=True
    ).strip()
    return ImageFont.truetype(path, size)


class SVG:
    def __init__(self, width, height, title, description, width_mm=160):
        self.width, self.height = width, height
        self.parts = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width_mm}mm" '
            f'height="{width_mm * height / width:.4f}mm" viewBox="0 0 {width} {height}" '
            'role="img" aria-labelledby="title description">',
            f"<title id=\"title\">{escape(title)}</title>",
            f"<desc id=\"description\">{escape(description)}</desc>",
        ]
        self.rect(0, 0, width, height, "#ffffff", stroke="none")

    def rect(self, x, y, w, h, fill="#ffffff", stroke="#9daabb", radius=0, sw=1.5):
        self.parts.append(
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{radius}" '
            f'fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>'
        )

    def line(self, x1, y1, x2, y2, color="#a4afba", width=1.5, dash=None):
        extra = f' stroke-dasharray="{dash}"' if dash else ""
        self.parts.append(
            f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" '
            f'stroke="{color}" stroke-width="{width}"{extra}/>'
        )

    def path(self, d, fill="none", stroke=BLUE, sw=2):
        self.parts.append(
            f'<path d="{d}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" '
            'stroke-linejoin="round" stroke-linecap="round"/>'
        )

    def circle(self, x, y, radius, fill, stroke=BLUE, sw=2):
        self.parts.append(
            f'<circle cx="{x}" cy="{y}" r="{radius}" fill="{fill}" '
            f'stroke="{stroke}" stroke-width="{sw}"/>'
        )

    def text(self, x, y, text, size=BODY, bold=False, italic=False, color=INK, anchor="start"):
        self.parts.append(
            f'<text x="{x:.3f}" y="{y:.3f}" font-family="{SERIF}" font-size="{size}" '
            f'font-weight="{"bold" if bold else "normal"}" '
            f'font-style="{"italic" if italic else "normal"}" '
            f'fill="{color}" text-anchor="{anchor}" xml:space="preserve">{escape(text)}</text>'
        )

    def save(self, path):
        path.write_text("\n".join(self.parts + ["</svg>"]) + "\n")


# Material Symbols (outlined, Apache-2.0) path data on the 960-unit grid.
ICONS = {
    "account_tree": "M600-120v-120H440v-400h-80v120H80v-320h280v120h240v-120h280v320H600v-120h-80v320h80v-120h280v320H600ZM160-760v160-160Zm520 400v160-160Zm0-400v160-160Zm0 160h120v-160H680v160Zm0 400h120v-160H680v160ZM160-600h120v-160H160v160Z",
    "battery_full": "M320-80q-17 0-28.5-11.5T280-120v-640q0-17 11.5-28.5T320-800h80v-80h160v80h80q17 0 28.5 11.5T680-760v640q0 17-11.5 28.5T640-80H320Z",
    "build": "M686-132 444-376q-20 8-40.5 12t-43.5 4q-100 0-170-70t-70-170q0-36 10-68.5t28-61.5l146 146 72-72-146-146q29-18 61.5-28t68.5-10q100 0 170 70t70 170q0 23-4 43.5T584-516l244 242q12 12 12 29t-12 29l-84 84q-12 12-29 12t-29-12Zm29-85 27-27-256-256q18-20 26-46.5t8-53.5q0-60-38.5-104.5T386-758l74 74q12 12 12 28t-12 28L332-500q-12 12-28 12t-28-12l-74-74q9 57 53.5 95.5T360-440q26 0 52-8t47-25l256 256ZM472-488Z",
    "calendar_month": "M200-80q-33 0-56.5-23.5T120-160v-560q0-33 23.5-56.5T200-800h40v-80h80v80h320v-80h80v80h40q33 0 56.5 23.5T840-720v560q0 33-23.5 56.5T760-80H200Zm0-80h560v-400H200v400Zm0-480h560v-80H200v80Zm0 0v-80 80Zm280 240q-17 0-28.5-11.5T440-440q0-17 11.5-28.5T480-480q17 0 28.5 11.5T520-440q0 17-11.5 28.5T480-400Zm-160 0q-17 0-28.5-11.5T280-440q0-17-11.5-28.5T320-480q17 0 28.5 11.5T360-440q0 17-11.5 28.5T320-400Zm320 0q-17 0-28.5-11.5T600-440q0-17-11.5-28.5T640-480q17 0 28.5 11.5T680-440q0 17-11.5 28.5T640-400ZM480-240q-17 0-28.5-11.5T440-280q0-17 11.5-28.5T480-320q17 0 28.5 11.5T520-280q0 17-11.5 28.5T480-240Zm-160 0q-17 0-28.5-11.5T280-280q0-17-11.5-28.5T320-320q17 0 28.5 11.5T360-280q0 17-11.5 28.5T320-240Zm320 0q-17 0-28.5-11.5T600-280q0-17-11.5-28.5T640-320q17 0 28.5 11.5T680-280q0 17-11.5 28.5T640-240Z",
    "code": "M320-240 80-480l240-240 57 57-184 184 183 183-56 56Zm320 0-57-57 184-184-183-183 56-56 240 240-240 240Z",
    "computer": "M40-120v-80h880v80H40Zm120-120q-33 0-56.5-23.5T80-320v-440q0-33 23.5-56.5T160-840h640q33 0 56.5 23.5T880-760v440q0 33-23.5 56.5T800-240H160Zm0-80h640v-440H160v440Zm0 0v-440 440Z",
    "data_object": "M560-160v-80h120q17 0 28.5-11.5T720-280v-80q0-38 22-69t58-44v-14q-36-13-58-44t-22-69v-80q0-17-11.5-28.5T680-720H560v-80h120q50 0 85 35t35 85v80q0 17 11.5 28.5T840-560h40v160h-40q-17 0-28.5 11.5T800-360v80q0 50-35 85t-85 35H560Zm-280 0q-50 0-85-35t-35-85v-80q0-17-11.5-28.5T120-400H80v-160h40q17 0 28.5-11.5T160-600v-80q0-50 35-85t85-35h120v80H280q-17 0-28.5 11.5T240-680v80q0 38-22 69t-58 44v14q36 13 58 44t22 69v80q0 17 11.5 28.5T280-240h120v80H280Z",
    "database": "M480-120q-151 0-255.5-46.5T120-280v-400q0-66 105.5-113T480-840q149 0 254.5 47T840-680v400q0 67-104.5 113.5T480-120Zm0-479q89 0 179-25.5T760-679q-11-29-100.5-55T480-760q-91 0-178.5 25.5T200-679q14 30 101.5 55T480-599Zm0 199q42 0 81-4t74.5-11.5q35.5-7.5 67-18.5t57.5-25v-120q-26 14-57.5 25t-67 18.5Q600-528 561-524t-81 4q-42 0-82-4t-75.5-11.5Q287-543 256-554t-56-25v120q25 14 56 25t66.5 18.5Q358-408 398-404t82 4Zm0 200q46 0 93.5-7t87.5-18.5q40-11.5 67-26t32-29.5v-98q-26 14-57.5 25t-67 18.5Q600-328 561-324t-81 4q-42 0-82-4t-75.5-11.5Q287-343 256-354t-56-25v99q5 15 31.5 29t66.5 25.5q40 11.5 88 18.5t94 7Z",
    "flag": "M200-120v-680h360l16 80h224v400H520l-16-80H280v280h-80Zm300-440Zm86 160h134v-240H510l-16-80H280v240h290l16 80Z",
    "folder": "M160-160q-33 0-56.5-23.5T80-240v-480q0-33 23.5-56.5T160-800h240l80 80h320q33 0 56.5 23.5T880-640v400q0 33-23.5 56.5T800-160H160Zm0-80h640v-400H160v480Zm0 0v-480 480Z",
    "inventory_2": "M200-80q-33 0-56.5-23.5T120-160v-451q-18-11-29-28.5T80-680v-120q0-33 23.5-56.5T160-880h640q33 0 56.5 23.5T880-800v120q0 23-11 40.5T840-611v451q0 33-23.5 56.5T760-80H200Zm0-520v440h560v-440H200Zm-40-80h640v-120H160v120Zm200 280h240v-80H360v80Zm120 20Z",
    "menu_book": "M560-564v-68q33-14 67.5-21t72.5-7q26 0 51 4t49 10v64q-24-9-48.5-13.5T700-600q-38 0-73 9.5T560-564Zm0 220v-68q33-14 67.5-21t72.5-7q26 0 51 4t49 10v64q-24-9-48.5-13.5T700-380q-38 0-73 9t-67 27Zm0-110v-68q33-14 67.5-21t72.5-7q26 0 51 4t49 10v64q-24-9-48.5-13.5T700-490q-38 0-73 9.5T560-454ZM260-320q47 0 91.5 10.5T440-278v-394q-41-24-87-36t-93-12q-36 0-71.5 7T120-692v396q35-12 69.5-18t70.5-6Zm260 42q44-21 88.5-31.5T700-320q36 0 70.5 6t69.5 18v-396q-33-14-68.5-21t-71.5-7q-47 0-93 12t-87 36v394Zm-40 118q-48-38-104-59t-116-21q-42 0-82.5 11T100-198q-21 11-40.5-1T40-234v-482q0-11 5.5-21T62-752q46-24 96-36t102-12q58 0 113.5 15T480-740q51-30 106.5-45T700-800q52 0 102 12t96 36q11 5 16.5 15t5.5 21v482q0 23-19.5 35t-40.5 1q-37-20-77.5-31T700-240q-60 0-116 21t-104 59ZM280-494Z",
    "monitoring": "M120-120v-80l80-80v160h-80Zm160 0v-240l80-80v320h-80Zm160 0v-320l80 81v239h-80Zm160 0v-239l80-80v319h-80Zm160 0v-400l80-80v480h-80ZM120-327v-113l280-280 160 160 280-280v113L560-447 400-607 120-327Z",
    "orbit": "M240-100q-58 0-99-41t-41-99q0-58 41-99t99-41q58 0 99 41t41 99q0 22-6.5 42.5T354-159v-27q30 13 62 19.5t64 6.5q134 0 227-93t93-227h80q0 83-31.5 156T763-197q-54 54-127 85.5T480-80q-45 0-88-9.5T309-118q-16 9-33.5 13.5T240-100Zm0-80q25 0 42.5-17.5T300-240q0-25-17.5-42.5T240-300q-25 0-42.5 17.5T180-240q0 25 17.5 42.5T240-180Zm240-160q-58 0-99-41t-41-99q0-58 41-99t99-41q58 0 99 41t41 99q0 58-41 99t-99 41ZM80-480q0-83 31.5-156T197-763q54-54 127-85.5T480-880q45 0 88 9.5t83 28.5q16-9 33.5-13.5T720-860q58 0 99 41t41 99q0 58-41 99t-99 41q-58 0-99-41t-41-99q0-22 6.5-42.5T606-801v27q-30-13-62-19.5t-64-6.5q-134 0-227 93t-93 227H80Zm640-180q25 0 42.5-17.5T780-720q0-25-17.5-42.5T720-780q-25 0-42.5 17.5T660-720q0 25 17.5 42.5T720-660ZM240-240Zm480-480Z",
    "output": "M200-120q-33 0-56.5-23.5T120-200v-560q0-33 23.5-56.5T200-840h560q33 0 56.5 23.5T840-760v80h-80v-80H200v560h560v-80h80v80q0 33-23.5 56.5T760-120H200Zm480-160-56-56 103-104H360v-80h367L624-624l56-56 200 200-200 200Z",
    "psychology": "M240-80v-172q-57-52-88.5-121.5T120-520q0-150 105-255t255-105q125 0 221.5 73.5T827-615l52 205q5 19-7 34.5T840-360h-80v120q0 33-23.5 56.5T680-160h-80v80h-80v-160h160v-200h108l-38-155q-23-91-98-148t-172-57q-116 0-198 81t-82 197q0 60 24.5 114t69.5 96l26 24v208h-80Zm254-360Zm-54 80h80l6-50q8-3 14.5-7t11.5-9l46 20 40-68-40-30q2-8 2-16t-2-16l40-30-40-68-46 20q-5-5-11.5-9t-14.5-7l-6-50h-80l-6 50q-8 3-14.5 7t-11.5 9l-46-20-40 68 40 30q-2 8-2 16t2 16l-40 30 40 68 46-20q5 5 11.5 9t14.5 7l6 50Zm40-100q-25 0-42.5-17.5T420-520q0-25 17.5-42.5T480-580q25 0 42.5 17.5T540-520q0 25-17.5 42.5T480-460Z",
    "public": "M480-80q-83 0-156-31.5T197-197q-54-54-85.5-127T80-480q0-83 31.5-156T197-763q54-54 127-85.5T480-880q83 0 156 31.5T763-763q54 54 85.5 127T880-480q0 83-31.5 156T763-197q-54 54-127 85.5T480-80Zm-40-82v-78q-33 0-56.5-23.5T360-320v-40L168-552q-3 18-5.5 36t-2.5 36q0 121 79.5 212T440-162Zm276-102q20-22 36-47.5t26.5-53q10.5-27.5 16-56.5t5.5-59q0-98-54.5-179T600-776v16q0 33-23.5 56.5T520-680h-80v80q0 17-11.5 28.5T400-560h-80v80h240q17 0 28.5 11.5T600-440v120h40q26 0 47 15.5t29 40.5Z",
    "satellite": "M240-280h480L570-480 450-320l-90-120-120 160Zm0-200q100 0 170-70t70-170h-68q0 72-50 122t-122 50v68Zm0-136q43 0 72.5-30.5T342-720H240v104Zm-40 496q-33 0-56.5-23.5T120-200v-560q0-33 23.5-56.5T200-840h560q33 0 56.5 23.5T840-760v560q0 33-23.5 56.5T760-120H200Zm0-80h560v-560H200v560Zm0 0v-560 560Z",
    "satellite_alt": "M560-32v-80q117 0 198.5-81.5T840-392h80q0 75-28.5 140.5t-77 114q-48.5 48.5-114 77T560-32Zm0-160v-80q50 0 85-35t35-85h80q0 83-58.5 141.5T560-192ZM222-57q-15 0-30-6t-27-17L23-222q-11-12-17-27t-6-30q0-16 6-30.5T23-335l127-127q23-23 57-23.5t57 22.5l50 50 28-28-50-50q-23-23-23-56t23-56l57-57q23-23 56.5-23t56.5 23l50 50 28-28-50-50q-23-23-23-56.5t23-56.5l127-127q12-12 27-18t30-6q15 0 29.5 6t26.5 18l142 142q12 11 17.5 25.5T895-730q0 15-5.5 30T872-673L745-546q-23 23-56.5 23T632-546l-50-50-28 28 50 50q23 23 22.5 56.5T603-405l-56 56q-23 23-56.5 23T434-349l-50-50-28 28 50 50q23 23 22.5 57T405-207L278-80q-11 11-25.5 17T222-57Zm0-79 42-42-142-142-42 42 142 142Zm85-85 42-42-142-142-42 42 142 142Zm184-184 56-56-142-142-56 56 142 142Zm198-198 42-42-142-142-42 42 142 142Zm85-85 42-42-142-142-42 42 142 142ZM448-504Z",
    "schedule": "m612-292 56-56-148-148v-184h-80v216l172 172ZM480-80q-83 0-156-31.5T197-197q-54-54-85.5-127T80-480q0-83 31.5-156T197-763q54-54 127-85.5T480-880q83 0 156 31.5T763-763q54 54 85.5 127T880-480q0 83-31.5 156T763-197q-54 54-127 85.5T480-80Zm0-400Zm0 320q133 0 226.5-93.5T800-480q0-133-93.5-226.5T480-800q-133 0-226.5 93.5T160-480q0 133 93.5 226.5T480-160Z",
    "smart_toy": "M160-360q-50 0-85-35t-35-85q0-50 35-85t85-35v-80q0-33 23.5-56.5T240-760h120q0-50 35-85t85-35q50 0 85 35t35 85h120q33 0 56.5 23.5T800-680v80q50 0 85 35t35 85q0 50-35 85t-85 35v160q0 33-23.5 56.5T720-120H240q-33 0-56.5-23.5T160-200v-160Zm200-80q25 0 42.5-17.5T420-500q0-25-17.5-42.5T360-560q-25 0-42.5 17.5T300-500q0 25 17.5 42.5T360-440Zm240 0q25 0 42.5-17.5T660-500q0-25-17.5-42.5T600-560q-25 0-17.5 42.5T600-440ZM320-280h320v-80H320v80Zm-80 80h480v-480H240v480Zm240-240Z",
    "target": "M480-80q-83 0-156-31.5T197-197q-54-54-85.5-127T80-480q0-83 31.5-156T197-763q54-54 127-85.5T480-880q83 0 156 31.5T763-763q54 54 85.5 127T880-480q0 83-31.5 156T763-197q-54 54-127 85.5T480-80Zm0-80q134 0 227-93t93-227q0-134-93-227t-227-93q-134 0-227 93t-93 227q0 134 93 227t227 93Zm0-80q-100 0-170-70t-70-170q0-100 70-170t170-70q100 0 170 70t70 170q0 100-70 170t-170 70Zm0-80q66 0 113-47t47-113q0-66-47-113t-113-47q-66 0-113 47t-47 113q0 66 47 113t113 47Zm0-80q-33 0-56.5-23.5T400-480q0-33 23.5-56.5T480-560q33 0 56.5 23.5T560-480q0 33-23.5 56.5T480-400Z",
    "task_alt": "M480-80q-83 0-156-31.5T197-197q-54-54-85.5-127T80-480q0-83 31.5-156T197-763q54-54 127-85.5T480-880q65 0 123 19t107 53l-58 59q-38-24-81-37.5T480-800q-133 0-226.5 93.5T160-480q0 133 93.5 226.5T480-160q133 0 226.5-93.5T800-480q0-18-2-36t-6-35l65-65q11 32 17 66t6 70q0 83-31.5 156T763-197q-54 54-127 85.5T480-80Zm-56-216L254-466l56-56 114 114 400-401 56 56-456 457Z",
    "terminal": "M160-160q-33 0-56.5-23.5T80-240v-480q0-33 23.5-56.5T160-800h640q33 0 56.5 23.5T880-720v480q0 33-23.5 56.5T800-160H160Zm0-80h640v-400H160v400Zm140-40-56-56 103-104-104-104 57-56 160 160-160 160Zm180 0v-80h240v80H480Z",
    "tune": "M440-120v-240h80v80h320v80H520v80h-80Zm-320-80v-80h240v80H120Zm160-160v-80H120v-80h160v-80h80v240h-80Zm160-80v-80h400v80H440Zm160-160v-240h80v80h160v80H680v80h-80Zm-480-80v-80h400v80H120Z",
    "upload_file": "M440-200h80v-167l64 64 56-57-160-160-160 160 57 56 63-63v167ZM240-80q-33 0-56.5-23.5T160-160v-640q0-33 23.5-56.5T240-880h320l240 240v480q0 33-23.5 56.5T720-80H240Zm280-520v-200H240v640h480v-440H520ZM240-800v200-200 640-640Z",
}


def icon(svg, name, x, y, size=18, color=INK):
    """Draw a Material Symbols icon centered at (x, y)."""
    svg.parts.append(
        f'<g transform="translate({x - size / 2:.2f},{y + size / 2:.2f}) '
        f'scale({size / 960:.4f})" fill="{color}" stroke="none">'
        f'<path d="{ICONS[name]}"/></g>')


LABELS = (
    "Mission:", "Material:", "Trace:", "Action:", "Observation:", "Thought:",
    "Final Result:", "Case package:", "Mission brief:", "Local workspace:",
    "Scientific:", "Astrodynamics:", "Optimization:",
)


def paragraphs(text):
    """Reflow prose while retaining separate trace events and demand rows."""
    result = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        if (
            not result or line.startswith(LABELS + ("Annotation:", "demand_"))
            or line in ("...", '..."')
            or result[-1] in ("...", '..."')
        ):
            result.append(line)
        else:
            result[-1] += " " + line
    return result


def flow(svg, text, x, y, width, highlights=(), size=BODY):
    """Lay out selectable text with prefix labels and substring highlights."""
    for para in paragraphs(text):
        italic = para.startswith("Annotation:")
        label = next((s for s in LABELS if para.startswith(s)), "")
        bold_end = len(label)
        marked = set()
        for phrase in highlights:
            phrase = re.sub(r"\s+", " ", phrase)
            start = para.find(phrase)
            while start >= 0:
                marked.update(range(start, start + len(phrase)))
                start = para.find(phrase, start + len(phrase))

        def measure(a, b):
            cut = max(a, min(b, bold_end))
            return (
                font(size, True, italic).getlength(para[a:cut])
                + font(size, False, italic).getlength(para[cut:b])
            )

        start = 0
        while start < len(para):
            end = start + 1
            while end <= len(para) and measure(start, end) <= width:
                end += 1
            end -= 1
            if end < len(para):
                space = para.rfind(" ", start, end + 1)
                if space > start:
                    end = space
            if end <= start:
                raise ValueError(f"Text column too narrow for {para!r}")
            if svg is not None:
                cursor = x
                a = start
                while a < end:
                    style = (a < bold_end, a in marked)
                    b = a + 1
                    while b < end and (b < bold_end, b in marked) == style:
                        b += 1
                    segment = para[a:b]
                    length = font(size, style[0], italic).getlength(segment)
                    if style[1]:
                        svg.rect(cursor - 1, y - size * .82, length + 2, size * 1.05, "#ffed99", "none", 1)
                    svg.text(cursor, y, segment, size, style[0], italic, "#53606a" if italic else INK)
                    cursor += length
                    a = b
            y += size * 1.18
            start = end
            while start < len(para) and para[start] == " ":
                start += 1
        y += 7
    return y


def trace_figure(stem, panels, output):
    panel_width = 384
    inner = panel_width - 30
    prepared = []
    for panel in panels:
        context, trace = panel["text"].split("\n\nTrace:\n", 1)
        trace, result = trace.rsplit("\n\nFinal Result: ", 1)
        prepared.append((context, "Trace:\n" + trace, "Final Result: " + result))
    context_top = 92
    context_end = max(flow(None, context, 0, context_top, inner) for context, _, _ in prepared)
    trace_top = context_end + 25
    trace_end = max(flow(None, trace, 0, trace_top, inner) for _, trace, _ in prepared)
    result_top = trace_end + 30
    result_end = max(flow(None, result, 0, result_top, inner - 12) for _, _, result in prepared)
    height = round(result_end + 24)
    description = "\n\n".join(panel["title"] + "\n" + panel["text"] for panel in panels)
    title = "Agent trace mechanisms" if stem.startswith("chapter5") else "Prompt and material mechanisms"
    svg = SVG(WIDTH, height, title, description)
    for i, (panel, blocks) in enumerate(zip(panels, prepared)):
        x = 8 + i * 400
        svg.rect(x, 28, panel_width, height - 38, ["#f4f8ef", "#eef6fc", "#fff6eb"][i], "#8e98a3")
        title_width = min(panel_width - 24, font(29, True).getlength(panel["title"]) + 34)
        svg.rect(x + (panel_width - title_width) / 2, 8, title_width, 46, PURPLE, "none", 7)
        svg.text(x + panel_width / 2, 40, panel["title"], 29, True, color="#ffffff", anchor="middle")
        flow(svg, blocks[0], x + 15, context_top, inner, panel["highlights"])
        svg.line(x + 15, context_end + 2, x + panel_width - 15, context_end + 2, dash="6 4")
        flow(svg, blocks[1], x + 15, trace_top, inner, panel["highlights"])
        svg.line(x + 15, trace_end + 1, x + panel_width - 15, trace_end + 1, dash="6 4")
        positive = (stem.startswith("chapter5") and i > 0) or (not stem.startswith("chapter5") and i == 2)
        svg.rect(x + 10, result_top - 21, panel_width - 20, result_end - result_top + 28,
                 "#e0f0e0" if positive else "#fce5e5", "#bfc6c9")
        flow(svg, blocks[2], x + 21, result_top, inner - 12)
    svg.save(output / f"{stem}.svg")


def checkmark(svg, x, y, r=15):
    svg.circle(x, y, r, "#33964c", "#227238", 1.3)
    svg.path(f"M {x-r*.5} {y} l {r*.32} {r*.34} l {r*.68} {-r*.75}", stroke="#ffffff", sw=4)


def earth(svg, x, y):
    """Wireframe globe with an orbit passing behind/in front and a satellite on it."""
    a, b, tilt = 88, 27, math.radians(-23)

    def orbit(deg):
        px, py = a * math.cos(math.radians(deg)), b * math.sin(math.radians(deg))
        return (x + px * math.cos(tilt) - py * math.sin(tilt),
                y + px * math.sin(tilt) + py * math.cos(tilt))

    svg.parts.append(
        f'<ellipse cx="{x}" cy="{y}" rx="{a}" ry="{b}" fill="none" stroke="{BLUE}" '
        f'stroke-width="2" transform="rotate(-23 {x} {y})"/>')
    svg.circle(x, y, 53, "#d9ecf8", BLUE, 2.5)
    svg.parts.append(f'<ellipse cx="{x}" cy="{y}" rx="30" ry="53" fill="none" stroke="#7eaccf" stroke-width="1.5"/>')
    svg.parts.append(f'<ellipse cx="{x}" cy="{y}" rx="12" ry="53" fill="none" stroke="#7eaccf" stroke-width="1.5"/>')
    svg.parts.append(f'<ellipse cx="{x}" cy="{y}" rx="53" ry="17" fill="none" stroke="#7eaccf" stroke-width="1.5"/>')
    front = [orbit(deg) for deg in range(0, 361) if orbit(deg)[1] > y + 0.5]
    svg.path("M " + " L ".join(f"{px:.1f} {py:.1f}" for px, py in front), "none", BLUE, 2)
    sx, sy = orbit(-40)
    svg.parts.append(
        f'<g transform="translate({sx:.1f},{sy:.1f}) rotate(-18)">'
        f'<rect x="-31" y="-9" width="22" height="18" rx="2" fill="#7eaccf" stroke="{BLUE}" stroke-width="2"/>'
        f'<line x1="-20" y1="-9" x2="-20" y2="9" stroke="{BLUE}" stroke-width="1.2"/>'
        f'<rect x="9" y="-9" width="22" height="18" rx="2" fill="#7eaccf" stroke="{BLUE}" stroke-width="2"/>'
        f'<line x1="20" y1="-9" x2="20" y2="9" stroke="{BLUE}" stroke-width="1.2"/>'
        f'<rect x="-8" y="-12" width="16" height="24" rx="4" fill="#ffffff" stroke="{BLUE}" stroke-width="2.2"/>'
        f'<line x1="0" y1="12" x2="0" y2="19" stroke="{BLUE}" stroke-width="2"/>'
        f'<circle cx="0" cy="21.5" r="2.6" fill="{BLUE}"/>'
        '</g>')


def gauge(svg, x, y, r=27):
    """Semicircular score meter with three bands and a needle; diameter baseline at y."""
    def point(deg, radius):
        a = math.radians(deg)
        return x + radius * math.cos(a), y - radius * math.sin(a)

    for a0, a1, color in [(180, 120, "#cd6b5c"), (120, 60, "#e0a33e"), (60, 0, "#33964c")]:
        x0, y0 = point(a0, r)
        x1, y1 = point(a1, r)
        svg.parts.append(
            f'<path d="M {x0:.1f} {y0:.1f} A {r} {r} 0 0 1 {x1:.1f} {y1:.1f}" '
            f'fill="none" stroke="{color}" stroke-width="7" stroke-linecap="butt"/>')
    nx, ny = point(52, r - 8)
    svg.line(x, y, nx, ny, INK, 3)
    svg.circle(x, y, 4, "#ffffff", INK, 2)


def overview(output):
    svg = SVG(WIDTH, 978, "AstroAgentBench workflow",
              "Schematic: a mission handoff supplies a case and workspace; an LLM agent constructs an executable plan; an independent verifier checks validity and reports mission value. Schedule rows are illustrative.")
    for x, title in [(8, "Problem Setup"), (418, "Agent Planning"), (828, "External Evaluation")]:
        svg.rect(x, 8, 364, 958, "#f2f7fc", BLUE, 10, 2)
        svg.rect(x, 8, 364, 50, BLUE, "none", 9)
        svg.rect(x, 36, 364, 22, BLUE, "none")
        svg.text(x+182, 43, title, 30, True, color="#ffffff", anchor="middle")
    for x in [378, 788]:
        svg.path(f"M {x} 464 h 19 v -13 l 17 24 -17 24 v -13 h -19 Z", BLUE, "none")

    earth(svg, 100, 139)
    svg.text(208, 123, "Mission", 27, True)
    svg.text(208, 154, "context", 27, True)
    svg.text(208, 187, "Earth observation", 22)
    svg.rect(24, 219, 332, 102, "#ffffff", "#a9bfd3", 8)
    flow(svg, "Plan an Earth observation mission under constraints - here are the handoff docs.", 38, 245, 304)

    def card(x, y, h, title, text, title_icon=None, item_icons=()):
        svg.rect(x, y, 332, h, "#ffffff", "#a9bfd3", 7)
        if title_icon:
            tw = font(25, True).getlength(title)
            icon(svg, title_icon, x + 166 - tw / 2 - 19, y + 21, 19, BLUE)
        svg.text(x+166, y+28, title, 25, True, color=BLUE, anchor="middle")
        svg.line(x+12, y+39, x+320, y+39, "#d4e0ea")
        end = y+65
        for i, line in enumerate(text.splitlines()):
            if i < len(item_icons) and item_icons[i]:
                icon(svg, item_icons[i], x+26, end-8, 17)
                end = flow(svg, line, x+44, end, 272)
            else:
                end = flow(svg, line, x+14, end, 304)
        bottom = end - BODY * 1.18 - 7 + BODY * .3
        if bottom > y+h-2:
            raise ValueError(f"Overview card overflow: {title}: {bottom} > {y+h}")

    card(24, 338, 240, "Agent Workspace",
         "Case package: mission.yaml, satellites.yaml, targets.yaml\n"
         "Mission brief: targets, horizon, orbit\n"
         "Local workspace: case files, skills, documentation, verifier",
         title_icon="folder", item_icons=["inventory_2", "flag", "account_tree"])
    card(24, 608, 170, "Toolbox",
         "Scientific: numpy, pandas\nAstrodynamics: brahe, poliastro\nOptimization: ortools, pulp",
         title_icon="build", item_icons=["monitoring", "orbit", "tune"])
    card(24, 808, 142, "Environment",
         "Code execution\nLocal data and ephemerides\nOutputs and artifacts",
         title_icon="computer", item_icons=["terminal", "database", "output"])

    # Agent icon and its construction loop.
    agent_label = "LLM Agent"
    agent_x = 600 - (64 + 19 + font(29, True).getlength(agent_label)) / 2
    icon(svg, "smart_toy", agent_x + 32, 118, 64, BLUE)
    svg.text(agent_x + 83, 134, agent_label, 29, True, color=BLUE)
    for y, label, ic in zip([184, 218, 280, 314], [
        "Read handoff docs and case files", "Reason over constraints and trade-offs",
        "Write / adapt code and execute", "Construct executable plan artifact",
    ], ["menu_book", "psychology", "code", "task_alt"]):
        icon(svg, ic, 448, y-8, 17)
        flow(svg, label, 463, y, 300)
    card(434, 336, 155, "Physical Feasibility",
         "Visibility windows\nSlew / timing limits\nEnergy and storage",
         title_icon="satellite")
    card(434, 510, 155, "Mission Value",
         "Target priority\nCoverage / revisit\nResource efficiency",
         title_icon="target")
    svg.rect(434, 684, 332, 265, "#ffffff", "#a9bfd3", 7)
    icon(svg, "calendar_month",
         600 - font(25, True).getlength("Planning Artifacts") / 2 - 19, 706, 19, BLUE)
    svg.text(600, 713, "Planning Artifacts", 25, True, color=BLUE, anchor="middle")
    svg.line(446, 723, 754, 723, "#d4e0ea")
    svg.text(600, 742, "Illustrative schedule", 22, italic=True, anchor="middle")
    cols = [444, 521, 591, 659, 756]
    for a, b, label in zip(cols, cols[1:], ["Time", "Asset", "Target", "Action"]):
        svg.rect(a, 754, b-a, 32, "#e6eff8", "#a9bfd3", sw=1)
        svg.text((a+b)/2, 777, label, 22, True, anchor="middle")
    rows = [
        (["Apr 14", "09:20"], ["SAT-1"], ["T-07"], ["Image"]),
        (["Apr 14", "10:05"], ["SAT-2"], ["GS-", "Madrid"], ["Downlink"]),
        (["Apr 15", "13:40"], ["SAT-1"], ["T-03"], ["Image"]),
    ]
    for i, row in enumerate(rows):
        y = 786 + i * 52
        for a, b, lines in zip(cols, cols[1:], row):
            svg.rect(a, y, b-a, 52, "#ffffff", "#a9bfd3", sw=1)
            for k, label in enumerate(lines):
                svg.text((a+b)/2, y+22+k*23, label, 22, anchor="middle")

    card(844, 80, 188, "Independent verifier",
         "Checks the submitted plan against the task contract.\nReports validity and mission value.",
         title_icon="satellite_alt")
    svg.rect(844, 286, 332, 384, "#ffffff", "#a9bfd3", 7)
    svg.text(1010, 320, "Evaluation Checklist", 25, True, color=BLUE, anchor="middle")
    svg.line(856, 329, 1164, 329, "#d4e0ea")
    for i, ((label, detail), ic) in enumerate(zip([
        ("Submission", "received"), ("Schema", "valid"), ("Timing", "feasible"),
        ("Geometry", "feasible"), ("Resources", "within limits"),
    ], ["upload_file", "data_object", "schedule", "public", "battery_full"])):
        y = 344+i*62
        svg.rect(858, y, 304, 54, "#f8fbfd", "#c3d2df", 5, 1)
        icon(svg, ic, 876, y+27, 19)
        svg.text(893, y+23, label, 22, True)
        svg.text(893, y+46, detail, 22)
        checkmark(svg, 1140, y+27, 14)
    svg.rect(844, 690, 332, 259, "#ffffff", "#a9bfd3", 7)
    svg.text(1010, 722, "Results", 25, True, color=BLUE, anchor="middle")
    svg.line(856, 729, 1164, 729, "#d4e0ea")
    svg.text(1010, 768, "Family-native mission metrics", 22, True, anchor="middle")
    svg.text(1010, 799, "completion, coverage, efficiency", 22, anchor="middle")
    svg.line(856, 822, 1164, 822, "#d4e0ea")
    checkmark(svg, 904, 871, 17)
    svg.text(904, 917, "Validity", 24, True, anchor="middle")
    gauge(svg, 1056, 888, 26)
    svg.text(1056, 917, "Normalized score", 24, True, color=BLUE, anchor="middle")
    svg.save(output / "chapter1_overview_v10.svg")


def ablations(output):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    plt.rcParams.update({
        "font.family": SERIF, "font.size": 8.5,
        "axes.labelsize": 8.5, "xtick.labelsize": 8.5, "ytick.labelsize": 8.5,
        "legend.fontsize": 8.5, "svg.fonttype": "none",
        "svg.hashsalt": "astroagentbench-paper", "hatch.linewidth": .65,
    })
    with (HERE / "ablation_deltas.csv").open() as handle:
        data = list(csv.DictReader(handle))
    groups = [("Regional", "OC+DS"), ("Regional", "OC+MM"), ("Relay", "OC+DS"), ("Relay", "OC+MM")]
    for panel, stem, conditions, colors, hatches in [
        ("procedure", "chapter5_ablation_a_v3", ["Compact", "Procedure pack"], ["#a7c6df", "#347d90"], ["...", "//"]),
        ("memory", "chapter5_ablation_b_v3", ["Codex-derived", "DeepSeek-derived"], ["#2776a6", "#8daacc"], ["xx", "++"]),
    ]:
        fig, ax = plt.subplots(figsize=(3.15, 2.55))
        fig.subplots_adjust(left=.355, right=.98, top=.75, bottom=.18)
        values = {(r["family"], r["system"], r["condition"]):float(r["mean_score_delta"])
                  for r in data if r["panel"] == panel}
        ys = np.array([0., 1., 2.45, 3.45])
        for j, (condition, color, hatch) in enumerate(zip(conditions, colors, hatches)):
            scores = [values[family, system, condition] for family, system in groups]
            y = ys + (j-.5)*.32
            ax.barh(y, scores, height=.30, label=condition, color=color, hatch=hatch,
                    edgecolor="#344654", linewidth=.65, zorder=3)
            for pos, score in zip(y, scores):
                ax.text(score+.4, pos, f"+{score:.1f}", va="center", ha="left", fontsize=8.5)
        ax.set_yticks(ys, [f"{family} / {system}" for family, system in groups])
        ax.invert_yaxis()
        ax.set_xlim(0, 31.5)
        ax.set_xticks([0, 10, 20, 30])
        ax.set_xlabel("Mean score delta (points)", labelpad=5)
        ax.xaxis.grid(True, color="#d9dee3", linewidth=.6)
        ax.axhline(1.725, color="#d9dee3", linewidth=.6)
        ax.set_axisbelow(True)
        ax.tick_params(axis="y", length=0, pad=4)
        ax.tick_params(axis="x", width=.65, length=3)
        ax.spines[["top","right"]].set_visible(False)
        ax.spines["left"].set_color("#7c8790")
        ax.spines["bottom"].set_color("#7c8790")
        ax.spines["left"].set_linewidth(.7)
        ax.spines["bottom"].set_linewidth(.7)
        ax.legend(loc="lower left", bbox_to_anchor=(0, 1.06), frameon=False, borderaxespad=0,
                  handlelength=1.5, labelspacing=.25)
        fig.savefig(output / f"{stem}.svg", metadata={"Date":None, "Creator":"AstroAgentBench"})
        plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=HERE)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    overview(args.output_dir)
    for stem, panels in json.loads((HERE / "trace_panels.json").read_text()).items():
        trace_figure(stem, panels, args.output_dir)
    ablations(args.output_dir)
    stems = ["chapter1_overview_v10", "chapter5_case_study_v1",
             "appendix_case_study_prompt_material_v1", "chapter5_ablation_a_v3", "chapter5_ablation_b_v3"]
    for stem in stems:
        subprocess.run(["rsvg-convert", "--format", "pdf", "--output",
                        str(args.output_dir / f"{stem}.pdf"), str(args.output_dir / f"{stem}.svg")], check=True)
        print(args.output_dir / f"{stem}.svg")


if __name__ == "__main__":
    main()
