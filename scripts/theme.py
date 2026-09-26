"""Palette and shared SVG primitives for the profile assets.

Everything here renders inside GitHub's <img> sandbox: no scripts, no web
fonts, CSS-only animation, and all motion disabled under reduced-motion.
"""
import html
import textwrap

FONT = "ui-monospace, SFMono-Regular, 'SF Mono', Menlo, Consolas, 'Liberation Mono', monospace"

BG = "#0a0e14"
SURFACE = "#0f141c"
BORDER = "#1c2330"
GRID = "#111823"
TEXT = "#e6edf3"
MUTED = "#8b949e"
FAINT = "#3b4452"
CYAN = "#22d3ee"
PURPLE = "#a78bfa"

# Language bar series and contribution heat ramp (luminance increases per level).
SERIES = [CYAN, PURPLE, "#38bdf8", "#e879f9"]
HEAT = ["#161b22", "#3b2a6b", "#5b4bb0", "#3fa7d6", CYAN]

# Approximate advance width of a monospace glyph, in em.
CHAR_W = 0.61

CSS = f"""
svg{{fill:{TEXT}}}
text{{font-family:{FONT}}}
.muted{{fill:{MUTED}}}
.faint{{fill:{FAINT}}}
.cyan{{fill:{CYAN}}}
.purple{{fill:{PURPLE}}}
.accent{{fill:url(#accent)}}
.b{{font-weight:700}}
.cursor{{fill:{CYAN};animation:blink 1.1s steps(1) infinite}}
.caret{{fill:{CYAN};opacity:0}}
.sweep{{transform:translateX(-240px);animation:sweep 7s ease-in-out infinite}}
@keyframes blink{{50%{{opacity:0}}}}
@keyframes caret{{from{{opacity:.85;transform:translateX(0)}}to{{opacity:.85;transform:translateX(var(--w))}}}}
@keyframes sweep{{from{{transform:translateX(-240px)}}to{{transform:translateX(1080px)}}}}
@media (prefers-reduced-motion:reduce){{*{{animation:none!important}}}}
"""


def esc(value):
    return html.escape(str(value), quote=True)


def text_w(s, size):
    return len(s) * size * CHAR_W


def wrap(s, size, max_w):
    return textwrap.wrap(s, max(10, int(max_w // (size * CHAR_W))))


def fit(s, size, max_w):
    """Largest font size <= size at which s fits in max_w."""
    return min(size, max_w / max(1, len(s) * CHAR_W))


def svg(w, h, body, label, css="", defs=""):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
        f'viewBox="0 0 {w} {h}" role="img" aria-label="{esc(label)}">'
        f"<title>{esc(label)}</title>"
        "<defs>"
        '<linearGradient id="accent" x1="0" y1="0" x2="1" y2="0">'
        f'<stop offset="0" stop-color="{CYAN}"/><stop offset="1" stop-color="{PURPLE}"/>'
        "</linearGradient>"
        '<linearGradient id="glow" x1="0" y1="0" x2="1" y2="0">'
        f'<stop offset="0" stop-color="{CYAN}" stop-opacity="0"/>'
        f'<stop offset=".5" stop-color="{CYAN}" stop-opacity=".9"/>'
        f'<stop offset="1" stop-color="{PURPLE}" stop-opacity="0"/>'
        "</linearGradient>"
        f'<clipPath id="frame"><rect x="0.5" y="0.5" width="{w - 1}" height="{h - 1}" rx="10"/></clipPath>'
        f"{defs}</defs>"
        f"<style>{CSS}{css}</style>"
        f"{body}</svg>\n"
    )


def panel(w, h, title):
    """Dark terminal window: frame, title bar, and a light sweep on the separator."""
    dots = "".join(f'<circle cx="{18 + i * 14}" cy="16" r="4" fill="{FAINT}"/>' for i in range(3))
    return (
        f'<rect x="0.5" y="0.5" width="{w - 1}" height="{h - 1}" rx="10" fill="{BG}" stroke="{BORDER}"/>'
        f"{dots}"
        f'<text x="{w / 2}" y="20" text-anchor="middle" font-size="11" class="muted">{esc(title)}</text>'
        f'<line x1="1" y1="32.5" x2="{w - 1}" y2="32.5" stroke="{BORDER}"/>'
        f'<g clip-path="url(#frame)"><rect class="sweep" x="0" y="32" width="200" height="1" fill="url(#glow)"/></g>'
    )


def chip(x, y, label, size=11, cls=""):
    """Returns (width, markup) for a small outlined tag."""
    w = text_w(label, size) + 16
    markup = (
        f'<rect x="{x:.1f}" y="{y}" width="{w:.1f}" height="{size + 11}" rx="4" fill="{SURFACE}" stroke="{BORDER}"/>'
        f'<text x="{x + 8:.1f}" y="{y + size + 4}" font-size="{size}" class="{cls}">{esc(label)}</text>'
    )
    return w, markup


def chips(x, y, labels, max_x, size=11, gap=8, cls=""):
    """Lays chips left to right, wrapping at max_x. Returns (markup, bottom_y)."""
    out, cx, cy = [], x, y
    for label in labels:
        w = text_w(label, size) + 16
        if cx + w > max_x and cx > x:
            cx, cy = x, cy + size + 11 + gap
        _, m = chip(cx, cy, label, size, cls)
        out.append(m)
        cx += w + gap
    return "".join(out), cy + size + 11


def typed(x, y, inner, plain, size, delay):
    """A text line with a caret that sweeps across it once. Returns (markup, end_time).

    The text itself is never hidden: the caret rests at opacity 0 and only
    exists while its animation runs, so any renderer that skips or freezes
    animation still shows the full line.
    """
    w = text_w(plain, size)
    dur = max(0.3, min(1.6, len(plain) * 0.03))
    markup = (
        f'<text x="{x}" y="{y}" font-size="{size}">{inner}</text>'
        f'<rect class="caret" x="{x}" y="{y - size + 2:.1f}" width="{size * CHAR_W:.1f}" height="{size + 1}" '
        f'style="--w:{w:.1f}px;animation:caret {dur:.2f}s steps({max(1, len(plain))}) {delay:.2f}s"/>'
    )
    return markup, delay + dur + 0.1


def tile(x, y, w, h, value, label, cls="cyan"):
    size = fit(value, 20, w - 20)
    return (
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" fill="{SURFACE}" stroke="{BORDER}"/>'
        f'<text x="{x + 10}" y="{y + 27}" font-size="{size:.1f}" class="b {cls}">{esc(value)}</text>'
        f'<text x="{x + 10}" y="{y + h - 11}" font-size="10.5" class="muted">{esc(label)}</text>'
    )
