"""Builds every SVG the profile README references.

  python scripts/build_profile.py             static + dynamic cards into ./assets (needs GH_TOKEN)
  python scripts/build_profile.py --static    static cards + now card, no network
  python scripts/build_profile.py --offline   everything from sample data into ./build/preview
  --date YYYY-MM-DD                            pin the day used to rotate the now/quote card
"""
import argparse
import json
import os
import shutil
import sys
from datetime import date, datetime, timezone
from pathlib import Path

import fixtures
import github_api
import render

ROOT = Path(__file__).resolve().parent.parent


def load(name):
    return json.loads((ROOT / "data" / name).read_text(encoding="utf-8"))


def write(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")
    print(f"  wrote {path.relative_to(ROOT)}")


def build_static(out):
    profile, projects = load("profile.json"), load("projects.json")
    static = out / "assets" / "static"
    write(static / "hero.svg", render.hero(profile))
    write(static / "divider.svg", render.divider())
    write(static / "stack.svg", render.stack(profile))
    for p in projects["systems"]:
        write(static / "projects" / f'{p["slug"]}.svg', render.system_card(p))
    for p in projects["research"]:
        write(static / "projects" / f'{p["slug"]}.svg', render.research_card(p))


def rotation(day):
    """Deterministic daily pick, so reruns on the same day are no-ops."""
    now_items, quotes = load("now.json"), load("quotes.json")
    n = day.toordinal()
    return now_items[n % len(now_items)], quotes[(n * 7 + 3) % len(quotes)]


def build_now(out, day):
    """Needs only data/, so every mode builds it."""
    entry, quote = rotation(day)
    write(out / "assets" / "generated" / "now.svg", render.now_card(entry, quote, day))


def build_dynamic(out, gh):
    profile = load("profile.json")
    gen = out / "assets" / "generated"
    write(gen / "stats.svg", render.stats_card(gh, profile))
    write(gen / "streak.svg", render.streak_card(gh))
    write(gen / "contributions.svg", render.contributions_card(gh))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument("--static", action="store_true", help="static cards only")
    mode.add_argument("--offline", action="store_true", help="render a preview from sample data")
    ap.add_argument("--date", type=date.fromisoformat, help="rotation date (default: today, UTC)")
    args = ap.parse_args()
    day = args.date or datetime.now(timezone.utc).date()

    if args.offline:
        out = ROOT / "build" / "preview"
        print(f"offline preview -> {out.relative_to(ROOT)}")
        build_static(out)
        build_now(out, day)
        build_dynamic(out, fixtures.sample(day))
        shutil.copy(ROOT / "README.md", out / "README.md")
        print(f"open {(out / 'README.md').relative_to(ROOT)} in a Markdown preview")
        return

    build_static(ROOT)
    build_now(ROOT, day)
    if args.static:
        return
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if not token:
        sys.exit("GH_TOKEN is not set. Use --static or --offline to build without it.")
    login = os.environ.get("GH_LOGIN") or load("profile.json")["login"]
    build_dynamic(ROOT, github_api.fetch(login, token))


if __name__ == "__main__":
    main()
