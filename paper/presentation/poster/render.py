#!/usr/bin/env python3
"""Build the illustrated A0 poster from saved artwork and editable scene data."""

import argparse
import base64
from contextlib import contextmanager
from functools import lru_cache
from html import escape
import json
import os
from pathlib import Path
import subprocess
import xml.etree.ElementTree as ET

from PIL import Image, ImageFont


ROOT = Path(__file__).resolve().parent
NAVY = "#102C45"
TEAL = "#008F98"
AMBER = "#AB681A"
MUTED = "#52677A"
PAPER = "#FCFAF5"
SERIF = "Noto Serif"
SANS = "Noto Sans"


@lru_cache
def font(size, family=SANS, weight=400, italic=False):
    face = "Italic" if italic else ("Bold" if weight >= 700 else "SemiBold" if weight >= 600 else "Regular")
    return ImageFont.truetype(str(ROOT / "fonts" / f"{family.replace(' ', '')}-{face}.ttf"), round(size))


def uri(path):
    suffix = path.suffix.lower()
    mime = {".png": "image/png", ".svg": "image/svg+xml", ".ttf": "font/ttf"}[suffix]
    return f"data:{mime};base64," + base64.b64encode(path.read_bytes()).decode()


class Poster:
    def __init__(self):
        self.items = []
        self.text_bounds = []

    def add(self, markup):
        self.items.append(markup)

    @contextmanager
    def group(self, name, **attrs):
        self.add(f'<g id="{name}" inkscape:groupmode="layer" inkscape:label="{name}" {self.attrs(attrs)}>')
        yield
        self.add("</g>")

    @staticmethod
    def attrs(attrs):
        return " ".join(f'{k.replace("_", "-")}="{escape(str(v), quote=True)}"' for k, v in attrs.items())

    def rect(self, x, y, w, h, fill, **attrs):
        self.add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}" {self.attrs(attrs)}/>')

    def line(self, x1, y1, x2, y2, color=TEAL, width=2, **attrs):
        self.add(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="{width}" {self.attrs(attrs)}/>')

    def path(self, d, fill="none", stroke=TEAL, width=2, **attrs):
        self.add(f'<path d="{d}" fill="{fill}" stroke="{stroke}" stroke-width="{width}" {self.attrs(attrs)}/>')

    def circle(self, x, y, r, fill, **attrs):
        self.add(f'<circle cx="{x}" cy="{y}" r="{r}" fill="{fill}" {self.attrs(attrs)}/>')

    def text(self, x, y, value, size=24, fill=NAVY, weight=400, family=SANS, anchor="start", italic=False, **attrs):
        value = str(value)
        measured = font(size, family, weight, italic)
        length = measured.getlength(value)
        left = x - (length if anchor == "end" else length / 2 if anchor == "middle" else 0)
        bbox = measured.getbbox(value, anchor="ls")
        self.text_bounds.append({"text": value, "bounds": [left, y + bbox[1], left + length, y + bbox[3]]})
        style = ' font-style="italic"' if italic else ""
        self.add(f'<text xml:space="preserve" x="{x}" y="{y}" font-family="{family}" font-size="{size}" font-weight="{weight}" text-anchor="{anchor}" fill="{fill}"{style} {self.attrs(attrs)}>{escape(value)}</text>')

    def lines(self, x, y, values, size=24, leading=None, **attrs):
        for i, value in enumerate(values):
            self.text(x, y + i * (leading or size * 1.35), value, size=size, **attrs)

    def image(self, path, x, y, w, h, **attrs):
        self.add(f'<image x="{x}" y="{y}" width="{w}" height="{h}" xlink:href="{uri(path)}" {self.attrs(attrs)}/>')

    def marker(self, x, y, shape, color, r=6, **attrs):
        a = self.attrs(attrs)
        if shape == "circle":
            self.circle(x, y, r, color, stroke=PAPER, stroke_width=1, **attrs)
        elif shape == "diamond":
            self.path(f"M{x},{y-r-1} l{r+1},{r+1} l{-r-1},{r+1} l{-r-1},{-r-1} Z", color, PAPER, 1, **attrs)
        elif shape == "square":
            self.rect(x-r, y-r, r*2, r*2, color, stroke=PAPER, stroke_width=1, **attrs)
        elif shape == "triangle":
            self.path(f"M{x},{y-r-1} l{r+1},{r*2+1} h{-2*r-2} Z", color, PAPER, 1, **attrs)
        elif shape == "plus":
            self.add(f'<path d="M{x-r},{y} H{x+r} M{x},{y-r} V{y+r}" stroke="{color}" stroke-width="3.5" {a}/>')


def definitions(p):
    css = []
    for family, face, weight, style in [(SANS, "Regular", 400, "normal"), (SANS, "SemiBold", 600, "normal"), (SANS, "Bold", 700, "normal"), (SERIF, "Bold", 700, "normal"), (SERIF, "Italic", 400, "italic")]:
        source = uri(ROOT / "fonts" / f"{family.replace(' ', '')}-{face}.ttf")
        css.append(f"@font-face {{font-family:'{family}';font-weight:{weight};font-style:{style};src:url('{source}')}}")
    p.add('<defs><style>' + "\n".join(css) + '</style>')
    p.add('<clipPath id="hero-clip"><rect x="48" y="420" width="1060" height="808" rx="7"/></clipPath>')
    p.add('<linearGradient id="hero-shade" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#001529" stop-opacity=".28"/><stop offset=".5" stop-color="#001529" stop-opacity="0"/><stop offset="1" stop-color="#001529" stop-opacity=".55"/></linearGradient>')
    for name, color in [("teal", TEAL), ("navy", NAVY), ("light", "#75E3DF")]:
        p.add(f'<marker id="arrow-{name}" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M1,1 L9,5 L1,9" fill="none" stroke="{color}" stroke-width="1.7"/></marker>')
    p.add('</defs>')


def header(p, scene):
    with p.group("Identity and research question"):
        logo = ET.parse(ROOT / "artwork/logo.svg").getroot()
        p.add('<g transform="translate(42 8) scale(.47)">')
        for element in logo:
            p.add(ET.tostring(element, encoding="unicode"))
        p.add('</g>')
        p.text(1634, 73, "AACL-IJCNLP 2026", 30, family=SERIF, weight=700, anchor="end")
        p.text(48, 183, scene["title"], 79, family=SERIF, weight=700)
        p.line(1027, 201, 1463, 201, "#D39A46", 4)
        p.text(50, 239, scene["subtitle"], 34, weight=600)
        p.text(50, 283, "Weiyi Wang¹˒⁵   Xinchi Chen¹˒³˒⁴˒⁵†   Jingjing Gong²˒⁵   Xuanjing Huang¹˒⁴   Xipeng Qiu¹˒²˒³˒⁴˒⁵†", 26, weight=600)
        p.text(50, 315, "¹ Institute of Trustworthy Embodied AI, Fudan University    ² Shanghai Innovation Institute", 19)
        p.text(50, 341, "³ Shanghai Key Laboratory of Multimodal Embodied AI    ⁵ OpenMOSS Team", 19)
        p.text(50, 367, "⁴ College of Computer Science and Artificial Intelligence, Fudan University", 19)
        p.text(1634, 367, "† Corresponding authors", 18, fill=MUTED, anchor="end")
        p.line(51, 387, 51, 406, TEAL, 5)
        p.text(69, 403, "Executable plans, checked against orbital geometry, timing, and resource constraints.", 25, fill=NAVY, weight=600)


def clock(minute):
    return f"{9 + minute // 60:02}:{minute % 60:02}"


def space_scene(p, scene):
    with p.group("Space mission illustration", clip_path="url(#hero-clip)"):
        p.image(ROOT / "artwork/earth.png", 48, 420, 1060, 808, preserveAspectRatio="xMidYMid slice")
        p.rect(48, 420, 1060, 808, "url(#hero-shade)")
        p.text(84, 466, "Space makes planning physical.", 32, fill="white", weight=700, family=SERIF)
        p.text(84, 497, "Illustrative geometry and timing; not a simulated mission", 19, fill="#BED5DF")
        p.path("M87,752 C242,580 716,560 1060,752", stroke="#75E3DF", width=2.5, stroke_dasharray="13 10", marker_end="url(#arrow-light)")
        for obs in scene["observations"]:
            ox, oy = scene["targets"][obs["target"]]
            dx, dy = obs["footprint_offset"]
            corners = [(ox+dx-64, oy+dy-25), (ox+dx+34, oy+dy-45), (ox+dx+64, oy+dy+25), (ox+dx-34, oy+dy+45)]
            cx, cy = obs["camera"]
            cone = f'M{cx},{cy} L{corners[0][0]},{corners[0][1]} L{corners[2][0]},{corners[2][1]} Z'
            p.path(cone, fill=obs["color"], stroke=obs["color"], width=1.5, fill_opacity=".11", stroke_opacity=".6", id=f'beam-{obs["id"]}')
            polygon = "M" + " L".join(f"{x},{y}" for x,y in corners) + " Z"
            p.path(polygon, fill=obs["color"], stroke=obs["color"], width=3, fill_opacity=".18", id=f'footprint-{obs["id"]}')
            p.image(ROOT / "artwork/satellite.png", *obs["sprite"])
            p.text(obs["sprite"][0] + 135, obs["sprite"][1]+30, f'Sat {obs["id"]} · {clock(obs["minute"])}', 22, fill="white", weight=600, anchor="middle")
        for name, (x, y) in scene["targets"].items():
            p.circle(x, y, 6, "#FFF4CE", stroke="#163A51", stroke_width=2, id=f'target-{name}')
            p.text(x+14, y+7, f"Target {name}", 22, fill="white", weight=700, stroke="#06263C", stroke_width=2, paint_order="stroke")
        for n, x, y, text in [(1, 96, 802, ["Moving orbits,", "brief access windows"]), (2, 553, 547, ["Coupled pointing,", "power & storage"]), (3, 827, 886, ["Stereo products", "need two views"] )]:
            p.circle(x, y-9, 19, "#F3C66F")
            p.text(x, y, n, 24, weight=700, anchor="middle")
            p.lines(x+32, y-2, text, 25, leading=32, fill="white", weight=600, stroke="#06263C", stroke_width=2, paint_order="stroke")
        # The schedule uses the very same observation records as the beams.
        p.rect(78, 1037, 596, 166, "#06263C", fill_opacity=".94", stroke="#6E9FAF", stroke_width=1, rx=8)
        target_names = ", ".join(dict.fromkeys(o["target"] for o in scene["observations"]))
        p.text(98, 1068, f"Schedule for target {target_names}", 23, fill="white", weight=600, id="schedule-title")
        x0, width = 192, 435
        for i, obs in enumerate(scene["observations"]):
            y = 1101 + 38*i
            p.text(98, y+5, f'Sat {obs["id"]}', 20, fill="white")
            p.line(x0, y, x0+width, y, "#5C7A8C", 1)
            a,b = obs["window"]
            p.rect(x0+a/40*width, y-9, (b-a)/40*width, 18, obs["color"], fill_opacity=".22", stroke=obs["color"], stroke_width=1.5)
            p.rect(x0+(obs["minute"]-1)/40*width, y-9, width/20, 18, obs["color"], id=f'scheduled-{obs["id"]}')
        for minute in (0,10,20,30,40):
            p.text(x0+minute/40*width, 1176, clock(minute), 17, fill="#DAE7EB", anchor="middle")
        p.text(98, 1200, "Outline: access window · filled: scheduled observation", 16, fill="#BED5DF")
        p.rect(698, 1037, 382, 166, "#06263C", fill_opacity=".94", stroke="#6E9FAF", stroke_width=1, rx=8)
        p.text(718, 1068, "The product matters", 23, fill="white", weight=600)
        p.path("M732,1111 l83,-21 l20,43 l-83,21 Z", "#65DDD4", "#65DDD4", 2, fill_opacity=".15")
        p.path("M769,1107 l83,-21 l20,43 l-83,21 Z", "#FFCC73", "#FFCC73", 2, fill_opacity=".15")
        p.circle(800, 1121, 4, "white")
        p.lines(899, 1111, ["Overlap +", "viewing angle"], 20, fill="white")
        p.text(718, 1182, "Two views form a stereo product", 19, fill="#DAE7EB")


def icon(p, kind, x, y, size=52, color=TEAL):
    with p.group(f"icon-{kind}-{x}-{y}", transform=f"translate({x} {y}) scale({size/52})", stroke_linecap="round", stroke_linejoin="round"):
        if kind == "file":
            p.path("M12,4 H32 L43,15 V47 H12 Z M32,4 V16 H43 M20,26 H35 M20,34 H35", stroke=color, width=2.5)
        elif kind == "code":
            p.rect(4, 7, 44, 32, "none", stroke=color, stroke_width=2.5, rx=3)
            p.path("M1,45 H51 M19,17 l-6,6 l6,6 M33,17 l6,6 l-6,6 M28,15 l-5,16", stroke=color, width=2.5)
        elif kind == "search":
            p.circle(22, 21, 15, "none", stroke=color, stroke_width=3)
            p.line(33, 33, 47, 47, color, 4)
        elif kind == "check":
            p.rect(9, 8, 34, 41, "none", stroke=color, stroke_width=2.5, rx=3)
            p.rect(18, 3, 16, 9, PAPER, stroke=color, stroke_width=2.5, rx=2)
            p.path("M16,24 l4,4 l7,-8 M29,25 H36 M16,38 l4,4 l7,-8 M29,39 H36", stroke=color, width=2.5)


def workflow(p):
    with p.group("Planning and independent evaluation"):
        p.text(1148, 452, "HOW THE BENCHMARK WORKS", 21, fill=TEAL, weight=700)
        boxes = [(486,80,"#EAF0F0","Mission files + goals","file"), (620,106,"#FAEDD7",None,"code"), (802,72,"#EAF0F0","Submitted plan","file"), (940,84,"#DDEEF0","Independent evaluation","check")]
        for y,h,fill,label,kind in boxes:
            w = 348 if kind == "code" else 486
            p.rect(1148, y, w, h, fill, rx=8)
            icon(p, kind, 1164, y+(h-44)/2, 44, AMBER if kind=="code" else NAVY)
            if label:
                p.text(1221, y+h/2+8, label, 25 if kind!="check" else 24, weight=600)
            else:
                p.lines(1221, y+43, ["Agent builds", "a planner"], 29, leading=37, weight=700)
        for start,end in [(566,613),(726,795),(874,933)]:
            p.line(1378, start+8, 1378, end-8, NAVY, 2, marker_end="url(#arrow-navy)")
        p.path("M1508,630 C1589,597 1597,725 1510,718", stroke=TEAL, width=2.2, marker_end="url(#arrow-teal)")
        p.lines(1566, 650, ["Local", "verifier", "feedback"], 18, leading=25, anchor="middle", weight=600, fill=TEAL)
        p.path("M1378,1024 V1040 H1262 V1060 M1378,1040 H1512 V1060", stroke=NAVY, width=2)
        for x, title, body in [(1148,"Feasible?",["Time · geometry", "resources"]),(1396,"Valuable?",["Coverage · service", "product quality"])]:
            p.rect(x,1060,238,114,"#F7EDDB",rx=8)
            p.text(x+119,1099,title,31,fill=AMBER,weight=700,family=SERIF,anchor="middle")
            p.lines(x+119,1130,body,21,leading=27,anchor="middle")
        p.text(1391,1211,"Planned before execution.",26,family=SERIF,italic=True,anchor="middle")
        p.line(1148,1228,1634,1228,"#A9C6C8",1.5)


def breadth(p):
    with p.group("Task breadth"):
        p.text(48, 1280, "7 task families", 32, fill=AMBER, weight=700, family=SERIF)
        p.line(316,1254,316,1290,"#ACB9BE",1)
        p.text(345,1280,"Observation scheduling · Imaging · Constellation design · Relay networks",25,weight=600)
        p.text(48,1322,"116 cases  /  35 held-out cases  /  5 agent systems",23,fill=MUTED)
        p.line(48,1346,1634,1346,"#BBC8CB",1.5)


def evidence(p, data):
    systems = data["systems"]
    with p.group("Quantitative results"):
        p.text(48,1414,"Valid plans can still accomplish little.",51,weight=700,family=SERIF)
        p.text(48,1455,"Mean normalized score · 5 held-out cases per family · higher is better",22,fill=MUTED)
        for i, system in enumerate(systems):
            x = 65 + (i%3)*350
            y = 1492 + (i//3)*58
            p.marker(x,y+8,system["shape"],system["color"],8)
            p.lines(x+21,y,system["legend"],19,leading=24,weight=600)
        p.line(765,1540,765,1564,NAVY,4)
        p.lines(786,1550,["Best solver reference", "per-case best, then mean"],18,leading=23)
        x0,width,y0,step = 241,844,1616,48
        p.rect(48,y0+6*step-24,1055,48,"#E8F0EF",rx=4)
        for tick in range(0,101,20):
            x=x0+tick/100*width
            p.line(x,y0-27,x,y0+6*step+27,"#CDD7D9",1)
            p.text(x,1953,tick,19,fill=MUTED,anchor="middle")
        for row,family in enumerate(data["families"]):
            y=y0+row*step
            p.text(221,y+7,family,23,weight=600,anchor="end")
            for i,system in enumerate(systems):
                value = system["scores"][row]
                p.marker(x0+value/100*width,y+(i-2)*6,system["shape"],system["color"],6.5,id=f'point-{system["id"]}-{family}',data_score=value)
            value=data["reference"][row]
            p.line(x0+value/100*width,y-17,x0+value/100*width,y+17,NAVY,4,id=f'reference-{family}',data_score=value)
        p.text(663,1983,"Mean normalized score",20,fill=MUTED,anchor="middle")
        p.line(1135,1463,1135,2008,"#BCCED0",1.5)
        stereo = data["families"].index("Stereo")
        selected = [next(s for s in systems if s["id"]==name) for name in ("codex","kimi")]
        if len({s["valid"] for s in selected}) != 1:
            raise ValueError("The shared-validity spotlight requires equal validity counts")
        p.text(1172,1496,"Both valid on",30,weight=700,family=SERIF)
        p.text(1172,1555,f'{selected[0]["valid"]}/35 cases',48,fill=AMBER,weight=700,family=SERIF)
        p.text(1172,1611,"Stereo Imaging mean score",24,weight=600)
        for x,s in zip((1172,1434),selected):
            p.text(x,1695,f'{s["scores"][stereo]:.2f}',68,weight=700,family=SERIF)
            p.marker(x+8,1726,s["shape"],s["color"],7)
            p.lines(x+25,1732,s["legend"],21,leading=28,weight=600)
        p.lines(1172,1811,["Feasibility alone does not", "measure mission value."],26,leading=35,weight=600)
        wins = sum(max(s["scores"][i] for s in systems)>ref for i,ref in enumerate(data["reference"]))
        p.text(1172,1921,f"{wins} / {len(data['families'])}",57,fill=AMBER,weight=700,family=SERIF)
        p.lines(1372,1887,["families: best agent", "mean exceeds the", "solver reference"],21,leading=28)
        p.text(1172,1978,"Family leaders differ across systems.",20,fill=MUTED)
        p.text(48,2025,"Agent runs: 2 h · 8 CPU cores · 32 GB RAM. Invalid or missing submissions score zero.",19,fill=MUTED)
        p.text(48,2052,"Solver references are quality anchors, not certified optima. Results: paper Table 3.",19,fill=MUTED)


def mechanisms(p):
    with p.group("Trace mechanisms and takeaway"):
        p.line(48,2077,1634,2077,"#A9C6C8",1.5)
        p.text(48,2128,"What strong runs do differently",41,weight=700,family=SERIF)
        p.text(1634,2128,"Observed in high-scoring traces",21,fill=MUTED,anchor="end")
        for x,kind,lines in [(82,"code",["Calibrate the", "implementation"]),(640,"search",["Search the", "case-specific bottleneck"]),(1217,"check",["Preserve the best", "verified plan"])]:
            p.circle(x+30,2191,46,"#E6F0EB")
            icon(p,kind,x+3,2163,54)
            p.lines(x+95,2180,lines,27,leading=35,weight=600)
        for x in (539,1116):
            p.line(x,2191,x+54,2191,TEAL,2.5,marker_end="url(#arrow-teal)")
        p.line(49,2264,49,2288,"#D39A46",5)
        p.text(66,2285,"Space mission planning tests whether agents turn physical constraints into useful decisions.",27,family=SERIF,italic=True)


def footer(p, scene):
    with p.group("Project resources"):
        p.line(48,2310,1487,2310,"#A9C6C8",1)
        p.text(50,2344,"Cases · verifiers · solver references · run traces",22,weight=600)
        p.add(f'<a xlink:href="{escape(scene["project_url"], quote=True)}">')
        p.text(845,2344,"github.com/Mtrya/AstroAgentBench",25,fill=AMBER,weight=700)
        p.add('</a>')
        # Keep the original QR data, but represent its modules as crisp vectors.
        qr = Image.open(ROOT.parent / "assets/qr_github.png").convert("RGBA").convert("L")
        # The source was generated at ten pixels per module with a two-module quiet zone.
        if qr.width % 10 or qr.width != qr.height:
            raise ValueError("Unexpected dimensions for the shared project QR")
        modules=qr.width//10
        side=100
        scale=side/modules
        x,y=1534,2258
        p.rect(x-8,y-8,side+16,side+16,"white")
        pieces=[]
        for row in range(modules):
            for col in range(modules):
                if qr.getpixel((col*10+5,row*10+5))<128:
                    pieces.append(f'M{col},{row}h1v1h-1z')
        p.add(f'<a xlink:href="{escape(scene["project_url"], quote=True)}"><path id="project-qr" d="{"".join(pieces)}" fill="{NAVY}" transform="translate({x} {y}) scale({scale})"/></a>')


def build(scene, output):
    output.mkdir(parents=True,exist_ok=True)
    p=Poster()
    p.add('<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape" width="841mm" height="1189mm" viewBox="0 0 1682 2378">')
    p.add('<title>AstroAgentBench: Evaluating Agentic Planning on Space Mission Planning Tasks</title>')
    p.add('<desc>A0 conference poster. Illustrative orbital planning scene, independently verified mission plans, seven-family results, and trace mechanisms.</desc>')
    definitions(p)
    p.rect(0,0,1682,2378,PAPER)
    header(p,scene)
    space_scene(p,scene)
    workflow(p)
    breadth(p)
    evidence(p,scene["results"])
    mechanisms(p)
    footer(p,scene)
    p.add('</svg>')
    outside=[t for t in p.text_bounds if t["bounds"][0]<30 or t["bounds"][1]<15 or t["bounds"][2]>1652 or t["bounds"][3]>2363]
    if outside:
        raise ValueError(f"Text exceeds poster safe area: {outside}")
    (output/"poster.svg").write_text("\n".join(p.items),encoding="utf-8")
    (output/"text-bounds.json").write_text(json.dumps(p.text_bounds,indent=2),encoding="utf-8")
    config=output/"fonts.conf"
    config.write_text(f'<?xml version="1.0"?><!DOCTYPE fontconfig SYSTEM "urn:fontconfig:fonts.dtd"><fontconfig><dir>{escape(str(ROOT/"fonts"))}</dir><cachedir>{escape(str(output/"font-cache"))}</cachedir></fontconfig>')
    env={**os.environ,"FONTCONFIG_FILE":str(config)}
    for args in [("--format","pdf","--output",str(output/"poster.pdf")),("--width","1682","--output",str(output/"poster.png"))]:
        subprocess.run(["rsvg-convert",*args,str(output/"poster.svg")],env=env,check=True)
    print(f"Built {output/'poster.svg'}, poster.pdf, poster.png")


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scene",type=Path,default=ROOT/"scene.json")
    parser.add_argument("--output-dir",type=Path,default=ROOT/"build")
    args=parser.parse_args()
    build(json.loads(args.scene.read_text()),args.output_dir.resolve())
