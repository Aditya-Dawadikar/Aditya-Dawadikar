"""SVG renderers. Static cards take data/*.json; dynamic cards take GitHub data."""
import math
import random
from datetime import date, timedelta

from theme import (
    BG, BORDER, CYAN, FAINT, HEAT, PURPLE, SERIES,
    chips, esc, panel, svg, text_w, tile, typed, wrap,
)

# ---------------------------------------------------------------- static


def hero(profile):
    W, H = 840, 240
    defs = (
        '<pattern id="grid" width="24" height="24" patternUnits="userSpaceOnUse">'
        '<path d="M24 0H0V24" fill="none" stroke="#111823"/></pattern>'
        '<linearGradient id="scan" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0" stop-color="{CYAN}" stop-opacity="0"/>'
        f'<stop offset=".5" stop-color="{CYAN}" stop-opacity=".06"/>'
        f'<stop offset="1" stop-color="{CYAN}" stop-opacity="0"/></linearGradient>'
    )
    css = (
        ".scan{transform:translateY(-90px);animation:scan 8s linear infinite}"
        "@keyframes scan{from{transform:translateY(-90px)}to{transform:translateY(260px)}}"
        ".core{animation:breathe 4s ease-in-out infinite}"
        "@keyframes breathe{50%{opacity:.45}}"
    )
    defs += (
        '<radialGradient id="core"><stop offset="0" stop-color="#ffffff" stop-opacity=".9"/>'
        f'<stop offset=".25" stop-color="{CYAN}" stop-opacity=".5"/>'
        f'<stop offset="1" stop-color="{PURPLE}" stop-opacity="0"/></radialGradient>'
    )
    particle_css, particles = particle_field(690, 136)
    css += particle_css

    body = (
        panel(W, H, profile["terminal_title"])
        + f'<g clip-path="url(#frame)"><rect x="1" y="33" width="{W - 2}" height="{H - 34}" fill="url(#grid)"/>'
        f'<rect class="scan" x="0" y="0" width="{W}" height="80" fill="url(#scan)"/></g>'
        + '<text x="40" y="74" font-size="14"><tspan class="cyan">$</tspan>'
        f'<tspan class="muted" dx="8">whoami</tspan></text>'
        + f'<text x="40" y="122" font-size="38" class="b accent">{esc(profile["name"])}</text>'
        + f'<text x="40" y="156" font-size="16">{esc(" · ".join(profile["roles"]))}</text>'
        + f'<text x="40" y="182" font-size="13" class="muted">{esc(profile["education"])}</text>'
        + '<text x="40" y="216" font-size="14" class="cyan">$</text>'
        + '<rect class="cursor" x="56" y="204" width="8" height="15"/>'
        + particles
    )
    label = f'{profile["name"]}: {", ".join(profile["roles"])}. {profile["education"]}.'
    return svg(W, H, body, label, css, defs)


def particle_field(cx, cy, n=64, seed=11):
    """Particles orbiting a central attractor, drawn on a tilted disk.

    Each orbit is a base ellipse plus one integer-frequency epicycle, so the
    path closes on itself and loops seamlessly. Period grows as r^1.5
    (Kepler), so inner particles overtake outer ones. Each particle drags two
    fading ghosts along the same keyframes for a short trail.
    """
    rng = random.Random(seed)
    tilt, flatten, steps = math.radians(-16), 0.58, 40
    css, marks = [], []
    for i in range(n):
        r = 16 + 92 * rng.random() ** 0.8
        a = r * rng.uniform(0.06, 0.2)
        k = rng.choice((-3, -2, 3, 4, 5))
        ph, ph2 = rng.uniform(0, 2 * math.pi), rng.uniform(0, 2 * math.pi)
        frames = []
        for s in range(steps + 1):
            t = 2 * math.pi * s / steps
            x = r * math.cos(t + ph) + a * math.cos(k * t + ph2)
            y = (r * math.sin(t + ph) + a * math.sin(k * t + ph2)) * flatten
            px = cx + x * math.cos(tilt) - y * math.sin(tilt)
            py = cy + x * math.sin(tilt) + y * math.cos(tilt)
            frames.append(f"{100 * s / steps:.2f}%{{transform:translate({px:.1f}px,{py:.1f}px)}}")
        css.append(f"@keyframes o{i}{{{''.join(frames)}}}")
        start = frames[0].split("{", 1)[1].rstrip("}")
        dur = 6 + 22 * (r / 108) ** 1.5
        offset = rng.uniform(0, dur)
        color = CYAN if rng.random() < 0.6 else PURPLE
        size = rng.uniform(1.0, 2.6)
        for g, (lag, op, shrink) in enumerate(((0.0, 0.95, 1.0), (0.018, 0.4, 0.75), (0.036, 0.15, 0.55))):
            marks.append(
                f'<circle r="{size * shrink:.2f}" fill="{color}" opacity="{op}" '
                f'style="{start};animation:o{i} {dur:.2f}s linear -{offset - lag * dur:.2f}s infinite"/>'
            )
    core = (f'<circle class="core" cx="{cx}" cy="{cy}" r="22" fill="url(#core)"/>'
            f'<circle cx="{cx}" cy="{cy}" r="2.2" fill="#ffffff"/>')
    return "".join(css), f'<g clip-path="url(#frame)">{core}{"".join(marks)}</g>'


def divider():
    W, H = 840, 16
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" aria-hidden="true">'
        '<defs><linearGradient id="d" x1="0" y1="0" x2="1" y2="0">'
        f'<stop offset="0" stop-color="{CYAN}" stop-opacity="0"/>'
        f'<stop offset=".35" stop-color="{CYAN}" stop-opacity=".6"/>'
        f'<stop offset=".65" stop-color="{PURPLE}" stop-opacity=".6"/>'
        f'<stop offset="1" stop-color="{PURPLE}" stop-opacity="0"/></linearGradient></defs>'
        f'<rect x="0" y="7.5" width="{W}" height="1" fill="url(#d)"/>'
        f'<rect x="{W / 2 - 4}" y="4" width="8" height="8" transform="rotate(45 {W / 2} 8)" fill="{BG}" stroke="{CYAN}"/>'
        "</svg>\n"
    )


def stack(profile):
    W = 840
    rows = profile["stack"]
    H = 56 + len(rows) * 36 + 8
    body = [panel(W, H, "stack --grouped")]
    y = 52
    for row in rows:
        body.append(f'<text x="28" y="{y + 15}" font-size="12" class="purple">{esc(row["group"])}</text>')
        markup, _ = chips(150, y, row["items"], W - 28, size=12)
        body.append(markup)
        y += 36
    label = "Tech stack: " + "; ".join(f'{r["group"]}: {", ".join(r["items"])}' for r in rows)
    return svg(W, H, "".join(body), label)


def system_card(p):
    """Full-width card: identity and stack on the left, metric tiles on the right."""
    W, H = 840, 200
    left_w = 440
    body = [panel(W, H, f'~/systems/{p["slug"]}')]
    body.append(f'<text x="28" y="68" font-size="22" class="b accent">{esc(p["name"])}</text>')
    y = 94
    for line in wrap(p["summary"], 13, left_w)[:2]:
        body.append(f'<text x="28" y="{y}" font-size="13">{esc(line)}</text>')
        y += 20
    markup, _ = chips(28, y - 2, p["tags"], 28 + left_w, size=11)
    body.append(markup)
    if p.get("note"):
        body.append(f'<text x="28" y="{H - 20}" font-size="11" class="muted">// {esc(p["note"])}</text>')

    metrics = p["metrics"][:4]
    tw, th, gap = 150, 58, 12
    x0, y0 = W - 28 - (2 * tw + gap), 50
    for i, m in enumerate(metrics):
        cx = x0 + (i % 2) * (tw + gap)
        cy = y0 + (i // 2) * (th + gap)
        body.append(tile(cx, cy, tw, th, m["value"], m["label"], "cyan" if i % 2 == 0 else "purple"))

    label = f'{p["name"]}: {p["summary"]} ' + "; ".join(f'{m["label"]}: {m["value"]}' for m in metrics)
    return svg(W, H, "".join(body), label)


def research_card(p):
    """Half-width card for research and open-source work."""
    W, H = 410, 220
    body = [panel(W, H, f'~/{p["kind"]}/{p["slug"]}')]
    body.append(f'<text x="24" y="64" font-size="19" class="b accent">{esc(p["name"])}</text>')
    y = 88
    for line in wrap(p["summary"], 12, W - 48)[:3]:
        body.append(f'<text x="24" y="{y}" font-size="12">{esc(line)}</text>')
        y += 18
    tw, th, gap = (W - 48 - 10) / 2, 58, 10
    for i, m in enumerate(p["metrics"][:2]):
        body.append(tile(24 + i * (tw + gap), H - 24 - th, round(tw), th, m["value"], m["label"],
                         "cyan" if i == 0 else "purple"))
    label = f'{p["name"]}: {p["summary"]} ' + "; ".join(f'{m["label"]}: {m["value"]}' for m in p["metrics"])
    return svg(W, H, "".join(body), label)


# ---------------------------------------------------------------- dynamic


def now_card(entry, quote, day):
    W, x, size, lh = 840, 28, 14, 24
    val_x = x + 118
    parts, t, y = [], 0.2, 64

    def line(inner, plain, dy=lh):
        nonlocal t, y
        m, t = typed(x, y, inner, plain, size, t)
        parts.append(m)
        y += dy

    cmd = f"now --date {day.isoformat()}"
    line(f'<tspan class="cyan">$</tspan><tspan dx="8">{esc(cmd)}</tspan>', "$ " + cmd)
    for key in ("focus", "thinking"):
        for i, chunk in enumerate(wrap(entry[key], size, W - val_x - 28)):
            head = f'<tspan class="purple">› {key}</tspan>' if i == 0 else ""
            line(f'{head}<tspan x="{val_x}">{esc(chunk)}</tspan>', f"› {key:<13}{chunk}")
    y += 10
    line('<tspan class="cyan">$</tspan><tspan dx="8">fortune --engineering</tspan>', "$ fortune --engineering")
    for chunk in wrap(f'"{quote["text"]}"', size, W - 2 * x - 16):
        line(f'<tspan x="{x + 16}" font-style="italic">{esc(chunk)}</tspan>', "  " + chunk)
    line(f'<tspan x="{x + 16}" class="muted">— {esc(quote["author"])}</tspan>', "  — " + quote["author"], lh + 6)
    parts.append(f'<text x="{x}" y="{y}" font-size="{size}" class="cyan">$</text>'
                 f'<rect class="cursor" x="{x + 16}" y="{y - 12}" width="8" height="15"/>')
    H = y + 24

    label = f'Now: {entry["focus"]}. Thinking about {entry["thinking"]}. Quote: "{quote["text"]}" by {quote["author"]}.'
    return svg(W, H, panel(W, H, "now.sh") + "".join(parts), label)


def _short(d, today):
    return f"{d:%b} {d.day}" if d.year == today.year else f"{d:%b} {d.day} {d.year}"


def stats_card(gh, profile):
    W, H = 410, 240
    y1 = gh["year"]
    rows = [
        ("contributions · 12 mo", y1["contributions"]),
        ("commits · 12 mo", y1["commits"]),
        ("pull requests · 12 mo", y1["prs"]),
        ("code reviews · 12 mo", y1["reviews"]),
        ("stars earned", gh["stars"]),
        ("public repositories", gh["repos"]),
    ]
    body = [panel(W, H, "stats.json")]
    y = 60
    for i, (k, v) in enumerate(rows):
        body.append(f'<text x="24" y="{y}" font-size="12" class="muted">{esc(k)}</text>')
        body.append(f'<text x="{W - 24}" y="{y}" font-size="13" text-anchor="end" '
                    f'class="b {"cyan" if i % 2 == 0 else "purple"}">{v:,}</text>')
        y += 22

    exclude = set(profile.get("languages_exclude", []))
    langs = {k: v for k, v in gh["languages"].items() if k not in exclude}
    total = sum(langs.values()) or 1
    top = sorted(langs.items(), key=lambda kv: -kv[1])[:4]
    bx, bw, by = 24, W - 48, 200
    body.append(f'<rect x="{bx}" y="{by}" width="{bw}" height="6" rx="3" fill="{FAINT}"/>')
    cx = bx
    for i, (name, size) in enumerate(top):
        w = bw * size / total
        body.append(f'<rect x="{cx:.1f}" y="{by}" width="{w:.1f}" height="6" fill="{SERIES[i]}"/>')
        cx += w
    lx = bx
    for i, (name, size) in enumerate(top):
        pct = f"{name} {100 * size / total:.0f}%"
        body.append(f'<circle cx="{lx + 4}" cy="{by + 22}" r="3.5" fill="{SERIES[i]}"/>'
                    f'<text x="{lx + 12}" y="{by + 26}" font-size="10" class="muted">{esc(pct)}</text>')
        lx += 12 + text_w(pct, 10) + 14
    label = "GitHub stats: " + ", ".join(f"{k} {v:,}" for k, v in rows) + ". Top languages: " + ", ".join(
        f"{n} {100 * s / total:.0f}%" for n, s in top)
    return svg(W, H, "".join(body), label)


def streaks(history):
    """history: {iso date: count}. Returns (current, current_start, longest, longest_range)."""
    days = {date.fromisoformat(k): v for k, v in history.items()}
    today = max(days)
    d, run, best, best_rng, start = min(days), 0, 0, None, None
    while d <= today:
        if days.get(d, 0) > 0:
            start = d if run == 0 else start
            run += 1
            if run > best:
                best, best_rng = run, (start, d)
        else:
            run = 0
        d += timedelta(days=1)
    # Today still in progress: a streak ending yesterday is still current.
    d = today if days.get(today, 0) > 0 else today - timedelta(days=1)
    cur, cur_end = 0, d
    while days.get(d, 0) > 0:
        cur += 1
        d -= timedelta(days=1)
    cur_rng = (d + timedelta(days=1), cur_end) if cur else None
    return today, cur, cur_rng, best, best_rng


def streak_card(gh):
    W, H = 410, 240
    today, cur, cur_rng, best, best_rng = streaks(gh["history"])
    total = sum(gh["history"].values())
    since = date.fromisoformat(gh["created_at"])

    def rng(r):
        if not r:
            return "—"
        a, b = r
        if a.year == b.year != today.year:
            return f"{a:%b} {a.day} – {b:%b} {b.day}, {b.year}"
        return f"{_short(a, today)} – {_short(b, today)}"

    cx, cy, r = W / 2, 126, 44
    circ = 2 * 3.14159 * r
    css = (f".ring{{stroke-dasharray:{circ:.1f};stroke-dashoffset:0;"
           f"animation:draw 1.6s ease-out both}}@keyframes draw{{from{{stroke-dashoffset:{circ:.1f}}}}}")
    body = [
        panel(W, H, "streak.log"),
        f'<line x1="{W / 3:.0f}" y1="70" x2="{W / 3:.0f}" y2="190" stroke="{BORDER}"/>',
        f'<line x1="{2 * W / 3:.0f}" y1="70" x2="{2 * W / 3:.0f}" y2="190" stroke="{BORDER}"/>',
        # total
        f'<text x="{W / 6:.0f}" y="126" font-size="22" text-anchor="middle" class="b cyan">{total:,}</text>',
        f'<text x="{W / 6:.0f}" y="150" font-size="11" text-anchor="middle">total</text>',
        f'<text x="{W / 6:.0f}" y="168" font-size="10" text-anchor="middle" class="muted">since {since.year}</text>',
        # current
        f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{BORDER}" stroke-width="3"/>',
        f'<circle class="ring" cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="url(#accent)" stroke-width="3" '
        f'stroke-linecap="round" transform="rotate(-90 {cx} {cy})"/>',
        f'<text x="{cx}" y="{cy + 10}" font-size="30" text-anchor="middle" class="b accent">{cur}</text>',
        f'<text x="{cx}" y="{cy + 70}" font-size="11" text-anchor="middle">current streak</text>',
        f'<text x="{cx}" y="{cy + 88}" font-size="9.5" text-anchor="middle" class="muted">{esc(rng(cur_rng))}</text>',
        # longest
        f'<text x="{5 * W / 6:.0f}" y="126" font-size="22" text-anchor="middle" class="b purple">{best}</text>',
        f'<text x="{5 * W / 6:.0f}" y="150" font-size="11" text-anchor="middle">longest</text>',
        f'<text x="{5 * W / 6:.0f}" y="168" font-size="9.5" text-anchor="middle" class="muted">{esc(rng(best_rng))}</text>',
    ]
    label = (f"Contribution streak: current {cur} days, longest {best} days, "
             f"{total:,} total contributions since {since.year}.")
    return svg(W, H, "".join(body), label, css)


def contributions_card(gh):
    W, H = 840, 222
    cell, gap = 11, 3
    step = cell + gap
    weeks = gh["calendar"][-53:]
    x0 = (W - len(weeks) * step) / 2 + 12
    y0 = 88
    body = [panel(W, H, "contributions --last 12mo")]
    total = gh["year"]["contributions"]
    body.append(f'<text x="{x0}" y="60" font-size="12" class="muted">'
                f'<tspan class="b cyan">{total:,}</tspan> contributions in the last year</text>')
    for row, name in ((1, "Mon"), (3, "Wed"), (5, "Fri")):
        body.append(f'<text x="{x0 - 8}" y="{y0 + row * step + 9}" font-size="9" text-anchor="end" class="muted">{name}</text>')

    last_month = None
    for col, week in enumerate(weeks):
        first = date.fromisoformat(week[0]["date"])
        if first.month != last_month and col < len(weeks) - 2:
            if last_month is not None or first.day <= 7:
                body.append(f'<text x="{x0 + col * step}" y="{y0 - 8}" font-size="9" class="muted">{first:%b}</text>')
            last_month = first.month
        for d in week:
            dd = date.fromisoformat(d["date"])
            row = (dd.weekday() + 1) % 7  # Sunday first, as on GitHub
            body.append(f'<rect x="{x0 + col * step}" y="{y0 + row * step}" width="{cell}" height="{cell}" '
                        f'rx="2" fill="{HEAT[d["level"]]}"/>')

    lx = x0 + len(weeks) * step - gap - 5 * step - 34
    ly = y0 + 7 * step + 16
    body.append(f'<text x="{lx - 6}" y="{ly + 9}" font-size="9" text-anchor="end" class="muted">less</text>')
    for i, c in enumerate(HEAT):
        body.append(f'<rect x="{lx + i * step}" y="{ly}" width="{cell}" height="{cell}" rx="2" fill="{c}"/>')
    body.append(f'<text x="{lx + 5 * step + 4}" y="{ly + 9}" font-size="9" class="muted">more</text>')
    label = f"Contribution heatmap: {total:,} contributions in the last year."
    return svg(W, H, "".join(body), label)
