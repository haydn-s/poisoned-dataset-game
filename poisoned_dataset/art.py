"""Procedural moon-colony artwork: inked outlines, chipped paint, gouache grain.

Characters follow key art exhibit A (the visor robots); rendering follows exhibit B
(hand-inked, painterly, scuffed). Every mark is seeded, so kits reproduce exactly
and stay editable as vector source. Text is kept outside filters to print crisply.
"""

import struct
import zlib
from base64 import b64encode
from functools import lru_cache
from hashlib import sha256
from html import escape
from math import cos, hypot, pi, sin

from .core import rng_for

INK = "#2a1c14"
C = {
    "paper": "#f3e8d0", "paper_dk": "#e2d1ae", "amber": "#e7a443", "amber_lt": "#f6c66a",
    "amber_dk": "#a9662a", "red": "#c63d2f", "red_dk": "#8c2a21", "blue": "#2f62b0",
    "blue_dk": "#1d3d76", "stripe": "#f1e4c6", "metal": "#8f8a7e", "metal_dk": "#55514a",
    "metal_lt": "#c4bfb2", "mustard": "#e2ad35", "mustard_dk": "#a5741c", "shell": "#ece3d0",
    "orange": "#e0632a", "orange_dk": "#a8441d", "visor": "#18171c", "eye": "#ffd54a",
    "night": "#0e1a3d", "earth": "#3b78c8", "land": "#6fa35a", "moon": "#aeadb9",
    "slate": "#3b302a", "teal": "#2f7f74", "rust": "#8a4a2a",
}
SANS = "'Inter Display', Inter, 'Helvetica Neue', Arial, sans-serif"
MONO = "'JetBrains Mono', 'DejaVu Sans Mono', ui-monospace, monospace"

DEFS_BASE = f"""<svg width="0" height="0" style="position:absolute" aria-hidden="true"><defs>
<filter id="paint" x="-6%" y="-6%" width="112%" height="112%" color-interpolation-filters="sRGB">
<feTurbulence type="fractalNoise" baseFrequency=".035" numOctaves="2" seed="7" result="w"/>
<feDisplacementMap in="SourceGraphic" in2="w" scale="2.6" xChannelSelector="R" yChannelSelector="G"/></filter>
<filter id="glow" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="9"/></filter>
<filter id="blur" x="-20%" y="-20%" width="140%" height="140%"><feGaussianBlur stdDeviation="5"/></filter>
<linearGradient id="shade" x1="0" y1="0" x2="1" y2="1">
<stop offset="0" stop-color="#fff6dc" stop-opacity=".34"/><stop offset=".42" stop-color="#fff" stop-opacity="0"/>
<stop offset=".7" stop-color="{INK}" stop-opacity=".08"/><stop offset="1" stop-color="{INK}" stop-opacity=".5"/></linearGradient>
<radialGradient id="shop" cx=".45" cy=".3" r=".85"><stop offset="0" stop-color="#f9d488"/>
<stop offset=".55" stop-color="#e3a04a"/><stop offset="1" stop-color="#94592a"/></radialGradient>
<linearGradient id="floor" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#c98a40"/>
<stop offset="1" stop-color="#7d4b22"/></linearGradient>
<linearGradient id="night" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#091230"/>
<stop offset=".7" stop-color="#1d3770"/><stop offset="1" stop-color="#2f4f8f"/></linearGradient>
<linearGradient id="fade" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#e9ad58"/>
<stop offset="1" stop-color="#e9ad58" stop-opacity="0"/></linearGradient>
<radialGradient id="lamp"><stop offset="0" stop-color="#fff1b8" stop-opacity=".95"/>
<stop offset=".4" stop-color="#ffc35a" stop-opacity=".45"/><stop offset="1" stop-color="#ff9d2e" stop-opacity="0"/></radialGradient>
<radialGradient id="earthshade" cx=".7" cy=".3" r=".9"><stop offset=".45" stop-color="#000" stop-opacity="0"/>
<stop offset="1" stop-color="#050a1c" stop-opacity=".85"/></radialGradient>
</defs></svg>"""


def _png(width: int, height: int, rgba: bytearray) -> bytes:
    rows = b"".join(b"\x00" + bytes(rgba[y * width * 4:(y + 1) * width * 4]) for y in range(height))
    chunk = lambda kind, data: (struct.pack(">I", len(data)) + kind + data
                                + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF))
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(rows, 9)) + chunk(b"IEND", b""))


@lru_cache(maxsize=1)
def grain_tile(size: int = 192) -> str:
    """A seamless gouache tile: ink specks plus pale brush mottling, as a PNG data URI.

    One shared image keeps PDFs small; per-element noise filters rasterise heavily.
    """
    r = rng("grain")
    octaves = []
    for cells in (4, 12, 48, 96):
        lattice = [[r.random() for _ in range(cells)] for _ in range(cells)]
        octaves.append((cells, lattice))

    def noise(x, y, cells, lattice):
        gx, gy = x * cells / size, y * cells / size
        x0, y0 = int(gx), int(gy)
        tx, ty = gx - x0, gy - y0
        tx, ty = tx * tx * (3 - 2 * tx), ty * ty * (3 - 2 * ty)
        a, b = lattice[y0 % cells][x0 % cells], lattice[y0 % cells][(x0 + 1) % cells]
        c, d = lattice[(y0 + 1) % cells][x0 % cells], lattice[(y0 + 1) % cells][(x0 + 1) % cells]
        return (a + (b - a) * tx) * (1 - ty) + (c + (d - c) * tx) * ty

    px = bytearray(size * size * 4)
    for y in range(size):
        for x in range(size):
            coarse = .6 * noise(x, y, *octaves[0]) + .4 * noise(x, y, *octaves[1])
            fine = .55 * noise(x, y, *octaves[2]) + .45 * noise(x, y, *octaves[3])
            i = (y * size + x) * 4
            if fine > .66:
                px[i:i + 4] = (42, 28, 20, min(200, int((fine - .66) * 700)))
            elif coarse > .55:
                px[i:i + 4] = (255, 244, 220, min(28, int((coarse - .55) * 160)))
    return "data:image/png;base64," + b64encode(_png(size, size, px)).decode("ascii")


def defs() -> str:
    """Shared filters, gradients and the grain tile; include once per HTML document."""
    return DEFS_BASE.replace("</defs>", f'<image id="grain" href="{grain_tile()}" width="64" height="64"/></defs>')


def grain(shape, key: str, opacity: float = 1) -> str:
    """Tile the shared gouache image over a shape, clipped to it.

    Repeated <use> of one image lets Chromium embed it once; patterns re-embed per use.
    """
    d, (x, y, w, h) = shape
    i = uid("grain", d, key)
    x0, y0 = int(x // 64) * 64, int(y // 64) * 64
    tiles = "".join(f'<use href="#grain" x="{tx}" y="{ty}"/>'
                    for ty in range(y0, int(y + h) + 1, 64) for tx in range(x0, int(x + w) + 1, 64))
    return (f'<clipPath id="{i}"><path d="{d}"/></clipPath>'
            f'<g clip-path="url(#{i})" opacity="{opacity}">{tiles}</g>')


def box(w, h):
    return f"M0 0H{f(w)}V{f(h)}H0Z", (0, 0, w, h)


def uid(*parts: object) -> str:
    return "u" + sha256(repr(parts).encode("utf-8")).hexdigest()[:10]


def rng(*parts: object):
    return rng_for(0, "art", *parts)


def f(x: float) -> str:
    return f"{x:.1f}".rstrip("0").rstrip(".")


def rrect(x, y, w, h, r):
    r = min(r, w / 2, h / 2)
    return (f"M{f(x + r)} {f(y)}H{f(x + w - r)}A{f(r)} {f(r)} 0 0 1 {f(x + w)} {f(y + r)}"
            f"V{f(y + h - r)}A{f(r)} {f(r)} 0 0 1 {f(x + w - r)} {f(y + h)}H{f(x + r)}"
            f"A{f(r)} {f(r)} 0 0 1 {f(x)} {f(y + h - r)}V{f(y + r)}A{f(r)} {f(r)} 0 0 1 {f(x + r)} {f(y)}Z",
            (x, y, w, h))


def circle(cx, cy, r):
    return (f"M{f(cx - r)} {f(cy)}A{f(r)} {f(r)} 0 1 0 {f(cx + r)} {f(cy)}"
            f"A{f(r)} {f(r)} 0 1 0 {f(cx - r)} {f(cy)}Z", (cx - r, cy - r, 2 * r, 2 * r))


def capsule(x1, y1, x2, y2, r):
    length = hypot(x2 - x1, y2 - y1) or 1
    nx, ny = -(y2 - y1) / length * r, (x2 - x1) / length * r
    d = (f"M{f(x1 + nx)} {f(y1 + ny)}L{f(x2 + nx)} {f(y2 + ny)}A{f(r)} {f(r)} 0 0 0 {f(x2 - nx)} {f(y2 - ny)}"
         f"L{f(x1 - nx)} {f(y1 - ny)}A{f(r)} {f(r)} 0 0 0 {f(x1 + nx)} {f(y1 + ny)}Z")
    return d, (min(x1, x2) - r, min(y1, y2) - r, abs(x2 - x1) + 2 * r, abs(y2 - y1) + 2 * r)


def poly(*points):
    xs, ys = [p[0] for p in points], [p[1] for p in points]
    return ("M" + "L".join(f"{f(x)} {f(y)}" for x, y in points) + "Z",
            (min(xs), min(ys), max(xs) - min(xs), max(ys) - min(ys)))


def blob(r, cx, cy, size, n=7):
    pts = []
    for k in range(n):
        a = 2 * pi * k / n + r.uniform(-.35, .35)
        d = size * r.uniform(.4, 1)
        pts.append((cx + d * cos(a), cy + d * sin(a) * r.uniform(.55, 1)))
    return "M" + "L".join(f"{f(x)} {f(y)}" for x, y in pts) + "Z"


def wear(key, box, chips=5, size=5.0, scuffs=3):
    """Paint chips showing bare metal, dirt specks, and dry scratches inside box."""
    r, (x, y, w, h), out = rng("wear", key), box, []
    for _ in range(chips):
        cx, cy, s = x + r.random() * w, y + r.random() * h, size * r.uniform(.5, 1.3)
        out.append(f'<path d="{blob(r, cx, cy, s)}" fill="{C["metal_lt"]}" stroke="{INK}" '
                   f'stroke-width=".8" stroke-opacity=".75"/>')
        if r.random() < .5:
            out.append(f'<path d="{blob(r, cx + s * .2, cy + s * .2, s * .45)}" fill="{C["rust"]}" opacity=".7"/>')
    for _ in range(scuffs):
        sx, sy, a = x + r.random() * w, y + r.random() * h, r.uniform(-.6, .6)
        ln = size * r.uniform(1.5, 3)
        out.append(f'<path d="M{f(sx)} {f(sy)}l{f(ln * cos(a))} {f(ln * sin(a))}" stroke="#fff8e6" '
                   f'stroke-width=".9" stroke-linecap="round" opacity=".55"/>')
    for _ in range(chips * 2):
        out.append(f'<circle cx="{f(x + r.random() * w)}" cy="{f(y + r.random() * h)}" '
                   f'r="{f(r.uniform(.4, 1.1))}" fill="{INK}" opacity=".35"/>')
    return "".join(out)


def clipped(d, content, key, evenodd=False):
    i, rule = uid("clip", d, key), ' clip-rule="evenodd"' if evenodd else ""
    return f'<clipPath id="{i}"><path d="{d}"{rule}/></clipPath><g clip-path="url(#{i})">{content}</g>'


def hatch(shape, color, period=22.0, width=11.0, angle=-38.0, key="", evenodd=False):
    """Parallel bands clipped to a shape. Vector geometry, unlike SVG patterns,
    which Chromium rasterises separately for every use when printing."""
    d, (x, y, w, h) = shape
    cx, cy, reach = x + w / 2, y + h / 2, hypot(w, h) / 2 + period
    lines = "".join(f"M{f(cx + o)} {f(cy - reach)}V{f(cy + reach)}"
                    for o in [k * period for k in range(-int(reach / period) - 1, int(reach / period) + 2)])
    return clipped(d, f'<path d="{lines}" transform="rotate({f(angle)} {f(cx)} {f(cy)})" stroke="{color}" '
                      f'stroke-width="{f(width)}"/>', ("hatch", key), evenodd)


def part(shape, fill, key, chips=4, size=5.0, lw=2.4, shade=True, extra=""):
    """A painted body part: base colour, details, wear, light, then the ink line."""
    d, box = shape
    inner = extra + wear(key, box, chips, size) if chips else extra
    return (f'<path d="{d}" fill="{fill}"/>' + (clipped(d, inner, key) if inner else "")
            + (f'<path d="{d}" fill="url(#shade)"/>' if shade else "")
            + f'<path d="{d}" fill="none" stroke="{INK}" stroke-width="{lw}" stroke-linejoin="round"/>')


def painted(content):
    return f'<g filter="url(#paint)">{content}</g>'


def text(x, y, s, size, fill=INK, weight=800, anchor="middle", family=SANS, spacing=0, extra=""):
    return (f'<text x="{f(x)}" y="{f(y)}" font-family="{family}" font-size="{f(size)}" font-weight="{weight}" '
            f'fill="{fill}" text-anchor="{anchor}" letter-spacing="{spacing}" {extra}>{escape(s)}</text>')


def para(x, y, s, size, width, lead=1.32, weight=500, fill=INK, anchor="start", family=SANS):
    """Greedy word wrap into tspans (approximate metrics; keep copy short). Returns (svg, lines)."""
    per, lines, line = width / (size * .53), [], ""
    for word in s.split():
        if line and len(line) + 1 + len(word) > per:
            lines.append(line)
            line = word
        else:
            line = f"{line} {word}".strip()
    lines.append(line)
    spans = "".join(f'<tspan x="{f(x)}" dy="{f(0 if i == 0 else size * lead)}">{escape(t)}</tspan>'
                    for i, t in enumerate(lines))
    return (f'<text x="{f(x)}" y="{f(y)}" font-family="{family}" font-size="{f(size)}" font-weight="{weight}" '
            f'fill="{fill}" text-anchor="{anchor}">{spans}</text>', len(lines))


# --- Cargo: the three binary features drawn as one consistent visual grammar ---------

def pod(cx, cy, r, color, striped, key):
    dark = C["red_dk"] if color == C["red"] else C["blue_dk"]
    body, band_top, band_bot = circle(cx, cy, r), cy - r * .5, cy + r * .5
    strap = lambda y0, t: (f"M{f(cx - r)} {f(y0)}Q{f(cx)} {f(y0 + r * .14)} {f(cx + r)} {f(y0)}"
                           f"V{f(y0 + t)}Q{f(cx)} {f(y0 + t + r * .14)} {f(cx - r)} {f(y0 + t)}Z")
    band = (f"M{f(cx - r)} {f(band_top + r * .16)}Q{f(cx)} {f(band_top + r * .3)} {f(cx + r)} {f(band_top + r * .16)}"
            f"V{f(band_bot)}Q{f(cx)} {f(band_bot + r * .14)} {f(cx - r)} {f(band_bot)}Z")
    inner = hatch((band, (cx - r, band_top, 2 * r, band_bot - band_top + r * .14)), C["stripe"], key=key) if striped else ""
    inner += (f'<path d="{strap(band_top, r * .16)}" fill="{C["metal"]}" stroke="{INK}" stroke-width="1.6"/>'
              f'<path d="{strap(band_bot, r * .16)}" fill="{C["metal"]}" stroke="{INK}" stroke-width="1.6"/>'
              f'<path d="{circle(cx - r * .38, cy - r * .42, r * .5)[0]}" fill="#fff" opacity=".12"/>'
              f'<path d="{circle(cx + r * .3, cy + r * .35, r * .85)[0]}" fill="{dark}" opacity=".35"/>')
    latch = rrect(cx + r * .52, cy - r * .62, r * .2, r * 1.24, r * .05)
    handle = (f'<path d="M{f(cx - r * .3)} {f(cy - r * .93)}V{f(cy - r * 1.18)}H{f(cx + r * .3)}V{f(cy - r * .93)}" '
              f'fill="none" stroke="{INK}" stroke-width="{f(r * .17)}" stroke-linejoin="round"/>'
              f'<path d="M{f(cx - r * .3)} {f(cy - r * .93)}V{f(cy - r * 1.18)}H{f(cx + r * .3)}V{f(cy - r * .93)}" '
              f'fill="none" stroke="{C["metal"]}" stroke-width="{f(r * .09)}" stroke-linejoin="round"/>')
    return (handle + part(body, color, key + "pod", 7, r * .09, extra=inner)
            + part(latch, C["metal"], key + "latch", 1, r * .05, lw=1.6)
            + "".join(f'<circle cx="{f(cx + r * .62)}" cy="{f(cy + k * r * .45)}" r="{f(r * .035)}" fill="{INK}"/>'
                      for k in (-1, 0, 1)))


def crate(cx, cy, s, color, striped, key):
    dark = C["red_dk"] if color == C["red"] else C["blue_dk"]
    x, y = cx - s / 2, cy - s / 2
    panel = rrect(x + s * .11, y + s * .11, s * .78, s * .78, s * .04)
    inner = (f'<path d="{panel[0]}" fill="{dark}" opacity=".28"/>'
             f'<path d="{rrect(x + s * .14, y + s * .14, s * .72, s * .72, s * .03)[0]}" fill="{color}"/>')
    if striped:
        inner += hatch(poly((x, cy - s * .16), (x + s, cy - s * .16), (x + s, cy + s * .16), (x, cy + s * .16)),
                       C["stripe"], key=key)
    inner += (f'<path d="M{f(x + s * .14)} {f(y + s * .14)}h{f(s * .72)}" stroke="#fff" stroke-opacity=".2" stroke-width="2"/>'
              f'<rect x="{f(x + s * .6)}" y="{f(y)}" width="{f(s * .4)}" height="{f(s)}" fill="{dark}" opacity=".22"/>')
    caps = "".join(part(poly((px, py), (px + sx * s * .26, py), (px + sx * s * .26, py + sy * s * .09),
                             (px + sx * s * .09, py + sy * s * .09), (px + sx * s * .09, py + sy * s * .26),
                             (px, py + sy * s * .26)), C["metal"], f"{key}cap{sx}{sy}", 1, s * .03, lw=1.6)
                   + f'<circle cx="{f(px + sx * s * .05)}" cy="{f(py + sy * s * .05)}" r="{f(s * .016)}" fill="{INK}"/>'
                   for px, py, sx, sy in ((x, y, 1, 1), (x + s, y, -1, 1), (x, y + s, 1, -1), (x + s, y + s, -1, -1)))
    slot = (f'<path d="{rrect(cx - s * .14, y + s * .035, s * .28, s * .055, s * .027)[0]}" fill="{INK}"/>')
    return part(rrect(x, y, s, s, s * .06), color, key + "crate", 8, s * .045, extra=inner) + caps + slot


def pallet(cx, y, w, key):
    x, out = cx - w / 2, []
    out.append(part(rrect(x, y, w, w * .1, 3), C["mustard"], key + "deck", 3, w * .02, lw=2))
    for k in range(3):
        bx = x + w * (.04 + k * .38)
        out.append(part(rrect(bx, y + w * .1, w * .16, w * .1, 2), C["mustard_dk"], f"{key}leg{k}", 1, w * .02, lw=1.8))
    out.append("".join(f'<circle cx="{f(x + w * t)}" cy="{f(y + w * .05)}" r="1.6" fill="{INK}"/>'
                       for t in (.08, .5, .92)))
    return "".join(out)


def cargo(red: int, round_: int, striped: int, key: str = "", night: bool = False) -> str:
    """A 226 x 162 illustration panel: one cargo item on a pallet in the shop."""
    color = C["red"] if red else C["blue"]
    key = f"{key}{red}{round_}{striped}"
    if night:
        bg = ('<rect width="226" height="162" fill="url(#night)"/>' + stars("bg" + key, 226, 110, 26)
              + f'<path d="M0 112Q40 96 78 108T150 100T226 110V162H0Z" fill="{C["moon"]}"/>'
              f'<path d="M0 124Q60 114 120 122T226 120V162H0Z" fill="#8e8ea0"/>'
              f'<ellipse cx="44" cy="134" rx="16" ry="4" fill="#6f6f84"/><ellipse cx="190" cy="140" rx="11" ry="3" fill="#6f6f84"/>'
              f'<circle cx="196" cy="30" r="15" fill="{C["earth"]}"/><path d="M188 24q6-6 12 0t4 10q-6 4-10-2z" fill="{C["land"]}"/>'
              f'<circle cx="196" cy="30" r="15" fill="url(#earthshade)"/>')
    else:
        bg = (f'<rect width="226" height="162" fill="url(#shop)"/>'
              f'<path d="M0 118H226V162H0Z" fill="url(#floor)"/>'
              f'<path d="M0 118H226" stroke="{INK}" stroke-width="1.4" opacity=".6"/>'
              f'<path d="M14 18h34v92h-34zM178 30h34v80h-34z" fill="#7a4520" opacity=".22"/>'
              f'<path d="M14 50h34M14 82h34M178 58h34M178 86h34" stroke="#5c3418" stroke-width="2" opacity=".3"/>'
              f'<ellipse cx="113" cy="40" rx="70" ry="44" fill="url(#lamp)" opacity=".55"/>')
    shadow = f'<ellipse cx="113" cy="148" rx="68" ry="7" fill="{INK}" opacity=".35"/>'
    item = (pod(113, 78, 50, color, striped, key) if round_ else crate(113, 80, 96, color, striped, key))
    return bg + painted(shadow + pallet(113, 128, 120, key) + item) + grain(box(226, 162), "panel", .45 if night else 1)


def stars(key, w, h, n):
    r = rng("stars", key)
    return "".join(f'<circle cx="{f(r.random() * w)}" cy="{f(r.random() * h)}" r="{f(r.uniform(.4, 1.3))}" '
                   f'fill="#fff6dc" opacity="{f(r.uniform(.4, 1))}"/>' for _ in range(n))


def cargo_icon(red: int, round_: int, striped: int, size: float = 40) -> str:
    """A flat mini version for manifests and rule cards (centred on 0,0)."""
    color, s = (C["red"] if red else C["blue"]), size
    clip_d = circle(0, 0, s / 2)[0] if round_ else rrect(-s / 2, -s / 2, s, s, s * .08)[0]
    band = poly((-s, -s * .17), (s, -s * .17), (s, s * .17), (-s, s * .17))
    stripes = clipped(clip_d, hatch(band, C["stripe"], s * .26, s * .13, key="icon"), ("icon", round_)) if striped else ""
    return (f'<path d="{clip_d}" fill="{color}"/>{stripes}'
            f'<path d="{clip_d}" fill="none" stroke="{INK}" stroke-width="{f(max(1.4, s * .05))}"/>')


# --- Tags: labels are hang-tags, separate from the cargo they describe --------------

def tag_path(w, h):
    c, hr = h * .32, h * .12
    hole = circle(c * 1.15, h / 2, hr)[0]
    return f"M{f(c)} 0H{f(w)}V{f(h)}H{f(c)}L0 {f(h - c)}V{f(c)}Z{hole}"


def tag(label: str, w: float = 160, h: float = 55, key: str = "", blank: bool = False,
        mirror: bool = False, outline: bool = True) -> str:
    """A STORE (light) or RECYCLE (dark) hang-tag; icon and tone differ, not just colour.

    mirror puts the hole on the right, as on the back half of a fold-over tag.
    """
    store = label == "STORE"
    fill, ink = (C["paper"], INK) if store or blank else (C["slate"], C["paper"])
    edge = f'stroke="{INK}" stroke-width="2"' if outline else ""
    body = (f'<path d="{tag_path(w, h)}" fill="{fill}" fill-rule="evenodd" {edge}/>'
            f'<circle cx="{f(h * .32 * 1.15)}" cy="{f(h / 2)}" r="{f(h * .16)}" fill="none" '
            f'stroke="{C["metal"]}" stroke-width="{f(h * .06)}"/>'
            + grain((tag_path(w, h), (0, 0, w, h)), "tag", 1 if fill == C["paper"] else .4))
    if mirror:
        body = f'<g transform="translate({f(w)} 0) scale(-1 1)">{body}</g>'
    if blank:
        return painted(body)
    ic = icon("store" if store else "recycle", ink, h * .5)
    left, right = (h * .2, w - h * 1.4) if mirror else (h * 1.42, w - h * .18)
    icon_x = w - h * 1.24 if mirror else h * .74
    fit = f'textLength="{f(right - left)}" lengthAdjust="spacingAndGlyphs"'
    return (painted(body) + f'<g transform="translate({f(icon_x)} {f(h * .25)})">{ic}</g>'
            + text((left + right) / 2, h * .67, label, h * .42, ink, 900, extra=fit))


def icon(name: str, color: str = INK, size: float = 24) -> str:
    k = size / 24
    paths = {
        "store": "M3 13h18v8H3zM12 2v8M8 6.5l4 4 4-4",
        "recycle": "M6.5 9.5A7 7 0 0 1 18 7M17.5 14.5A7 7 0 0 1 6 17M18 2.5V7h-4.5M6 21.5V17h4.5",
        "audit": "M10 3a7 7 0 1 0 0 14a7 7 0 1 0 0-14M15 15l6 6M6.5 8.5a4 4 0 0 1 4-2.5",
        "check": "M4 12.5l5 5L20 6",
        "round": "M12 3a9 9 0 1 0 0 18a9 9 0 1 0 0-18",
        "square": "M3.5 3.5h17v17h-17z",
        "striped": "M3.5 3.5h17v17h-17zM3.5 14L14 3.5M8 20.5L20.5 8M3.5 8.5l5-5M14 20.5l6.5-6.5",
        "plain": "M3.5 3.5h17v17h-17z",
        "lock": "M6 11h12v10H6zM8.5 11V7.5a3.5 3.5 0 0 1 7 0V11",
    }
    return (f'<g transform="scale({k:.3f})"><path d="{paths[name]}" fill="none" '
            f'stroke="{color}" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/></g>')


def swatch(red: int, size: float = 24) -> str:
    k = size / 24
    return (f'<g transform="scale({k:.3f})"><circle cx="12" cy="12" r="9" fill="{C["red"] if red else C["blue"]}" '
            f'stroke="{INK}" stroke-width="2.2"/></g>')


def hexagon(cx, cy, r):
    pts = [(cx + r * cos(pi / 6 + k * pi / 3), cy + r * sin(pi / 6 + k * pi / 3)) for k in range(6)]
    return poly(*pts)


def hexbolt(face: str, r: float = 50, number: int = 0) -> str:
    """An audit token: an AUDIT nut that flips to its VERIFIED side when spent (centred on 0,0)."""
    verified = face == "VERIFIED"
    fill = C["teal"] if verified else C["mustard"]
    ink = C["paper"] if verified else INK
    art = painted(part(hexagon(0, 0, r), fill, "hex" + face, 4, r * .06, lw=2.6) + grain(hexagon(0, 0, r), "hex")
                  + f'<path d="{circle(0, 0, r * .62)[0]}" fill="none" stroke="{INK}" stroke-width="1.6" opacity=".55"/>')
    glyph = icon("check" if verified else "audit", ink, r * .7)
    return (art + f'<g transform="translate({f(-r * .35)} {f(-r * .72)})">{glyph}</g>'
            + text(0, r * .3, face, r * .21 if verified else r * .27, ink, 900, spacing=1)
            + (text(0, r * .56, f"TOKEN {number}", r * .14, ink, 700, spacing=1) if number else ""))


# --- Characters: exhibit A's cast, painted in exhibit B's hand -----------------------

def eyes(left, right, rx, ry, look, lids, glow=C["eye"]):
    out = []
    for (ex, ey), lid in zip((left, right), lids):
        out.append(f'<ellipse cx="{f(ex)}" cy="{f(ey)}" rx="{f(rx)}" ry="{f(ry)}" fill="{glow}"/>'
                   f'<circle cx="{f(ex + look[0])}" cy="{f(ey + look[1])}" r="{f(rx * .48)}" fill="{C["visor"]}"/>'
                   f'<circle cx="{f(ex + look[0] - rx * .2)}" cy="{f(ey + look[1] - rx * .22)}" r="{f(rx * .14)}" fill="#fff"/>')
        if lid:
            out.append(f'<path d="{lid}" fill="{C["visor"]}"/>')
    return "".join(out)


def hand(x, y, s, key, holding=""):
    fingers = "".join(part(capsule(x + s * (.12 + .26 * k), y + s * .2, x + s * (.12 + .26 * k), y - s * .28, s * .13),
                           C["metal_dk"], f"{key}f{k}", 0, lw=1.6) for k in range(3))
    return holding + fingers + part(rrect(x - s * .05, y, s * .9, s * .7, s * .22), C["metal_dk"], key + "palm", 1, s * .08,
                                    lw=1.8)


def mallory(key: str = "m") -> str:
    """The big shell-white robot with orange panels, a visor face and shifty eyes.

    Drawn in a -40,-50 280 x 340 box, facing right, hand on chin, holding a tag aloft.
    """
    o = []
    # Treads and hips.
    o.append(part(rrect(52, 236, 128, 40, 18), C["metal_dk"], key + "tread", 3, 4))
    for k, wx in enumerate((76, 116, 156)):
        o.append(part(circle(wx, 256, 15), C["metal"], f"{key}w{k}", 1, 3, lw=2)
                 + f'<circle cx="{wx}" cy="256" r="4.5" fill="{INK}"/>')
    o.append(part(rrect(78, 218, 76, 24, 8), C["metal_dk"], key + "hip", 1, 3))
    # Raised arm (drawn behind the torso) with a tag pinched in the fist.
    o.append(part(capsule(54, 150, 8, 112, 12), C["shell"], key + "ua", 2, 3))
    o.append(part(circle(8, 110, 10), C["metal_dk"], key + "elb", 0))
    o.append(part(capsule(8, 110, 0, 54, 11), C["shell"], key + "fa", 2, 3,
                  extra=f'<rect x="-14" y="74" width="30" height="9" fill="{C["orange"]}"/>'))
    held = (f'<g transform="translate(-6 46) rotate(-118)">{tag("", 64, 26, key + "t", blank=True)}</g>')
    o.append(hand(-14, 30, 30, key + "lh", held))
    # Torso with orange hazard panels and a chest port.
    chest = (f'<path d="M52 170L100 128H128L52 196Z" fill="{C["orange"]}"/>'
             f'<path d="M52 205L118 145V160L52 220Z" fill="{C["orange"]}"/>'
             f'<rect x="150" y="196" width="22" height="18" fill="{C["orange"]}"/>')
    o.append(part(rrect(50, 128, 132, 100, 34), C["shell"], key + "torso", 6, 4.5, extra=chest))
    o.append(part(circle(124, 186, 13), C["metal"], key + "port", 0, lw=2)
             + f'<circle cx="124" cy="186" r="5" fill="{C["eye"]}" opacity=".85"/>')
    o.append(part(circle(56, 146, 20), C["orange"], key + "lsh", 2, 3))
    o.append(part(rrect(98, 110, 36, 24, 6), C["metal_dk"], key + "neck", 0))
    # Head: helmet, orange corner panel, visor with scheming eyes, ear disc, antenna.
    head = []
    head.append(f'<path d="M171 18L184 -24" stroke="{INK}" stroke-width="5" stroke-linecap="round"/>'
                f'<path d="M171 18L184 -24" stroke="{C["metal"]}" stroke-width="2.2" stroke-linecap="round"/>')
    head.append(part(circle(185, -27, 6), C["red"], key + "ant", 0, lw=2))
    panel = (f'<path d="M140 14H196V58Q170 54 150 34Z" fill="{C["orange"]}"/>'
             f'<path d="M36 92Q60 100 74 122H36Z" fill="{C["orange"]}"/>')
    head.append(part(rrect(36, 12, 160, 108, 32), C["shell"], key + "helm", 7, 5, extra=panel))
    lids = ("M66 40L122 62L122 38L66 38Z", "M126 60L184 46L184 38L126 38Z")
    visor = (eyes((97, 72), (152, 72), 17, 19, (7, 3), lids)
             + '<path d="M60 44Q66 36 80 36" stroke="#fff" stroke-width="3" stroke-linecap="round" opacity=".25"/>')
    head.append(part(rrect(52, 30, 132, 76, 22), C["visor"], key + "visor", 0, shade=False, extra=visor))
    head.append(part(circle(36, 70, 18), C["orange"], key + "ear", 1, 3)
                + part(circle(36, 70, 8), C["metal_dk"], key + "earc", 0, lw=1.6))
    o.append(f'<g transform="rotate(-5 116 70)">{"".join(head)}</g>')
    # Chin arm crossing in front, fingers to the visor.
    o.append(part(circle(176, 146, 20), C["orange"], key + "rsh", 2, 3))
    o.append(part(capsule(178, 150, 186, 204, 12), C["shell"], key + "rua", 2, 3))
    o.append(part(circle(186, 206, 10), C["metal_dk"], key + "relb", 0))
    o.append(part(capsule(186, 206, 140, 140, 12), C["shell"], key + "rfa", 2, 3,
                  extra=f'<path d="M150 160L170 150L176 160L156 172Z" fill="{C["orange"]}"/>'))
    o.append(hand(120, 122, 30, key + "rh"))
    return painted("".join(o))


def sorter(key: str = "s", reach: bool = True, holding: str = "") -> str:
    """The small mustard tread-bot with a visor, big earnest eyes and a claw antenna.

    Drawn in a -10,-40 210 x 220 box, facing left, one arm reaching right.
    """
    o = []
    o.append(part(rrect(18, 140, 112, 34, 16), C["metal_dk"], key + "tread", 3, 4))
    for k, wx in enumerate((40, 74, 108)):
        o.append(part(circle(wx, 157, 12), C["metal"], f"{key}w{k}", 1, 3, lw=1.8)
                 + f'<circle cx="{wx}" cy="157" r="3.5" fill="{INK}"/>')
    o.append(part(capsule(42, 106, 18, 126, 7), C["mustard"], key + "la", 1, 3))
    o.append(part(rrect(38, 90, 72, 54, 12), C["mustard"], key + "body", 4, 4,
                  extra=f'<rect x="50" y="110" width="48" height="14" fill="{C["mustard"]}"/>'
                        + hatch(rrect(50, 110, 48, 14, 1), INK, 10, 5, 45, key)))
    o.append(part(rrect(64, 78, 20, 16, 4), C["metal_dk"], key + "neck", 0))
    if reach:
        o.append(part(circle(108, 102, 8), C["metal_dk"], key + "sh", 0))
        o.append(part(capsule(108, 102, 142, 92, 7), C["mustard"], key + "ua", 1, 3))
        o.append(part(capsule(142, 92, 172, 78, 6), C["mustard"], key + "fa", 1, 3))
        o.append(holding)
        o.append(f'<path d="M172 78l12-6M172 78l13 5" stroke="{INK}" stroke-width="6" stroke-linecap="round"/>'
                 f'<path d="M172 78l12-6M172 78l13 5" stroke="{C["metal"]}" stroke-width="2.6" stroke-linecap="round"/>')
    o.append(f'<path d="M108 14L120 -26" stroke="{INK}" stroke-width="4.5" stroke-linecap="round"/>'
             f'<path d="M108 14L120 -26" stroke="{C["metal"]}" stroke-width="2" stroke-linecap="round"/>'
             f'<path d="M113 -30q7-10 14-2M120 -26q2 -9 10-8" fill="none" stroke="{INK}" stroke-width="3.2" stroke-linecap="round"/>')
    o.append(part(rrect(14, 10, 120, 76, 22), C["mustard"], key + "head", 5, 4.5,
                  extra=f'<path d="M14 64Q40 74 60 86H14Z" fill="{C["mustard_dk"]}" opacity=".5"/>'))
    lids = ("M38 28L72 34L72 26L38 26Z", "M78 34L112 28L112 26L78 26Z")
    o.append(part(rrect(26, 22, 96, 52, 15), C["visor"], key + "visor", 0, shade=False,
                  extra=eyes((56, 50), (92, 50), 13, 15, (-5, 1), lids)
                  + '<path d="M34 34Q38 28 48 28" stroke="#fff" stroke-width="2.4" stroke-linecap="round" opacity=".25"/>'))
    o.append(part(circle(12, 50, 11), C["metal_dk"], key + "ear", 0)
             + f'<circle cx="12" cy="50" r="4" fill="{C["mustard"]}"/>')
    return painted("".join(o))


# --- Places ------------------------------------------------------------------------

def porthole(R: float, key: str = "p") -> str:
    """A riveted round window onto the Moon with Earth rising (centred on 0,0)."""
    r = rng("porthole", key)
    view = (f'<rect x="{f(-R)}" y="{f(-R)}" width="{f(2 * R)}" height="{f(2 * R)}" fill="url(#night)"/>'
            + f'<g transform="translate({f(-R)} {f(-R)})">{stars(key, 2 * R, R * 1.2, int(R / 2.5))}</g>')
    ex, ey, er = R * .34, -R * .44, R * .27
    view += (f'<circle cx="{f(ex)}" cy="{f(ey)}" r="{f(er * 1.08)}" fill="#7fb4ff" opacity=".25"/>'
             f'<circle cx="{f(ex)}" cy="{f(ey)}" r="{f(er)}" fill="{C["earth"]}"/>'
             + "".join(f'<path d="{blob(r, ex + r.uniform(-.5, .5) * er, ey + r.uniform(-.5, .5) * er, er * r.uniform(.2, .4))}" '
                       f'fill="{C["land"] if k % 3 else "#f2efe6"}"/>' for k in range(6))
             + f'<circle cx="{f(ex)}" cy="{f(ey)}" r="{f(er)}" fill="url(#earthshade)"/>')
    ridge = [(-R, R * .12)] + [(-R + 2 * R * k / 9, R * (.02 + .16 * r.random())) for k in range(1, 9)] + [(R, R * .1)]
    view += (f'<path d="M{" L".join(f"{f(x)} {f(y)}" for x, y in ridge)} L{f(R)} {f(R)} L{f(-R)} {f(R)}Z" fill="{C["moon"]}"/>'
             f'<path d="M{f(-R)} {f(R * .42)}Q0 {f(R * .3)} {f(R)} {f(R * .45)}V{f(R)}H{f(-R)}Z" fill="#8f8ea2"/>'
             + "".join(f'<ellipse cx="{f(r.uniform(-.8, .8) * R)}" cy="{f(r.uniform(.25, .85) * R)}" rx="{f(rx)}" '
                       f'ry="{f(rx * .28)}" fill="#6e6d82" stroke="#c9c8d4" stroke-width="1.2"/>'
                       for rx in (r.uniform(.06, .16) * R for _ in range(7)))
             + f'<path d="M{f(-R * .9)} {f(-R * .2)}L{f(-R * .2)} {f(-R * .9)}L{f(0)} {f(-R * .9)}L{f(-R * .9)} 0Z" '
               f'fill="#fff" opacity=".07"/>')
    ring = (part(circle(0, 0, R * 1.16), C["metal"], key + "ring", 6, R * .04, lw=3)
            + "".join(f'<circle cx="{f(R * 1.08 * cos(k * pi / 6))}" cy="{f(R * 1.08 * sin(k * pi / 6))}" '
                      f'r="{f(R * .028)}" fill="{INK}"/>' for k in range(12)))
    return painted(ring + clipped(circle(0, 0, R)[0], view, key)
                   + f'<path d="{circle(0, 0, R)[0]}" fill="none" stroke="{INK}" stroke-width="3"/>')


def lamp(x, y, key):
    return (f'<circle cx="{x}" cy="{y + 26}" r="70" fill="url(#lamp)" opacity=".8"/>'
            + painted(f'<path d="M{x} -20V{y}" stroke="{INK}" stroke-width="3"/>'
                      + part(poly((x - 16, y + 18), (x - 9, y), (x + 9, y), (x + 16, y + 18)), C["metal_dk"], key, 1)
                      + f'<ellipse cx="{x}" cy="{y + 19}" rx="12" ry="4" fill="#fff1b8"/>'))


def claw(x, y, key):
    return painted(f'<path d="M{x} -20V{y}" stroke="{INK}" stroke-width="7"/><path d="M{x} -20V{y}" '
                   f'stroke="{C["metal"]}" stroke-width="3"/>'
                   + part(rrect(x - 14, y, 28, 18, 4), C["metal_dk"], key + "c", 1)
                   + part(poly((x - 12, y + 18), (x - 24, y + 44), (x - 14, y + 56), (x - 10, y + 50), (x - 16, y + 42),
                               (x - 4, y + 22)), C["mustard_dk"], key + "l", 0, lw=2)
                   + part(poly((x + 12, y + 18), (x + 24, y + 44), (x + 14, y + 56), (x + 10, y + 50), (x + 16, y + 42),
                               (x + 4, y + 22)), C["mustard_dk"], key + "r", 0, lw=2))


def shelves(x, y, w, h, key):
    r, o = rng("shelf", key), [f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="#6b3d1c" opacity=".35"/>']
    for k in range(4):
        sy = y + h * (k + 1) / 4
        o.append(f'<rect x="{x}" y="{f(sy - 4)}" width="{w}" height="5" fill="#4a2a14" opacity=".55"/>')
        cx = x + 6
        while cx < x + w - 24:
            bw, bh = r.uniform(18, 34), r.uniform(14, h / 4 - 10)
            tone = r.choice(("#a76c35", "#8b5a30", "#b98a4a", "#7c6a58", "#9b4a32", "#4d5d77"))
            o.append(f'<rect x="{f(cx)}" y="{f(sy - 4 - bh)}" width="{f(bw)}" height="{f(bh)}" fill="{tone}" '
                     f'stroke="{INK}" stroke-width="1.2" opacity=".75"/>')
            cx += bw + r.uniform(3, 10)
    return "".join(o)


def bin_(x, y, key):
    """Exhibit A's ore bin: an olive tub of moon rock and blue crystal."""
    r, rocks = rng("bin", key), []
    for k in range(9):
        cx, cy = x + 12 + k * 12 + r.uniform(-3, 3), y - 2 + r.uniform(-6, 3)
        tone = "#8fd3ff" if k % 3 == 1 else r.choice(("#8d8a86", "#a29f98", "#77736d"))
        rocks.append(f'<path d="{blob(r, cx, cy, r.uniform(7, 11), 6)}" fill="{tone}" stroke="{INK}" stroke-width="1.4"/>')
    tub = poly((x, y), (x + 120, y), (x + 112, y + 46), (x + 8, y + 46))
    return painted("".join(rocks) + part(tub, "#8c9a3a", key, 4, 4,
                                         extra=f'<path d="M{x} {y + 9}H{x + 120}" stroke="{INK}" stroke-width="1.4" opacity=".6"/>'))


def logo(dark: bool = False) -> str:
    """The title on two hang-tags; the second one hangs askew, as if swapped. 640 x 260 box."""
    top = f'<path d="{tag_path(600, 120)}" fill="{C["paper"]}" fill-rule="evenodd" stroke="{INK}" stroke-width="4"/>'
    low = f'<path d="{tag_path(470, 100)}" fill="{C["slate"]}" fill-rule="evenodd" stroke="{INK}" stroke-width="4"/>'
    t1 = (f'<g transform="translate(20 20) rotate(-3)">{painted(top + grain((tag_path(600, 120), (0, 0, 600, 120)), "logo"))}'
          + text(338, 92, "POISONED", 92, INK, 900, spacing=4) + "</g>")
    t2 = (f'<g transform="translate(150 132) rotate(4)">{painted(low + grain((tag_path(470, 100), (0, 0, 470, 100)), "logo"))}'
          + text(270, 78, "DATASET", 74, C["paper"], 900, spacing=8) + "</g>")
    string = (f'<path d="M0 0Q30 40 64 70M64 70Q120 150 190 182" fill="none" '
              f'stroke="{C["paper"] if dark else INK}" stroke-width="3" opacity=".85"/>')
    return string + t1 + t2


def cover_scene(key: str = "cover") -> str:
    """Key art after exhibits A and B on a 900 x 600 canvas; the top-left stays clear for the title."""
    held = f'<g transform="translate(176 80) rotate(84)">{tag("", 54, 22, key + "st", blank=True)}</g>'
    pod_art = painted(pallet(113, 128, 120, key + "p1") + pod(113, 78, 50, C["red"], 1, key + "pod"))
    crate_art = painted(pallet(113, 128, 120, key + "p2") + crate(113, 80, 96, C["blue"], 0, key + "crate"))
    return "".join([
        '<rect width="900" height="600" fill="url(#shop)"/>',
        shelves(14, 200, 220, 230, key + "a"), shelves(640, 330, 250, 100, key + "b"),
        '<path d="M0 46H900M0 58H900" stroke="#5c3418" stroke-width="7" opacity=".5"/>',
        lamp(300, 40, key + "l1"), lamp(520, 30, key + "l2"),
        f'<g transform="translate(690 175)">{porthole(125, key)}</g>',
        claw(872, 116, key + "claw"),
        '<path d="M0 430H900V600H0Z" fill="url(#floor)"/>',
        f'<path d="M0 430H900" stroke="{INK}" stroke-width="2" opacity=".5"/>',
        "".join(f'<path d="M{450 + k * 130} 430L{450 + k * 260} 600" stroke="#5c3418" '
                f'stroke-width="1.5" opacity=".35"/>' for k in range(-4, 5)),
        f'<g transform="translate(36 245) scale(1.15)">{mallory(key + "m")}</g>',
        f'<g transform="translate(160 318) scale(1.6)">{pod_art}</g>',
        f'<g transform="translate(600 300) scale(1.45)">{crate_art}</g>',
        f'<g transform="translate(500 300) scale(1.2)">{sorter(key + "s", holding=held)}</g>',
        bin_(452, 486, key + "bin"),
        f'<g filter="url(#blur)" opacity=".9">{crate(70, 590, 150, "#3b3a4f", 0, key + "f1")}'
        f'{crate(850, 575, 140, "#5a3528", 0, key + "f2")}</g>',
        grain(box(900, 600), "cover"),
    ])


def scene_svg(w: float, h: float, body: str, label: str = "") -> str:
    aria = f'role="img" aria-label="{escape(label)}"' if label else 'aria-hidden="true"'
    return f'<svg viewBox="0 0 {f(w)} {f(h)}" {aria}>{body}</svg>'
