"""Synthetic GitHub data for offline previews. Never written to assets/."""
import random
from datetime import date, timedelta


def sample(today, seed=7):
    rng = random.Random(seed)
    start = today - timedelta(days=3 * 365)
    history, d = {}, start
    while d <= today:
        weekday_bias = 0.35 if d.weekday() >= 5 else 0.75
        history[d.isoformat()] = rng.randint(1, 12) if rng.random() < weekday_bias else 0
        d += timedelta(days=1)

    # Last 53 Sunday-aligned weeks, levels by quartile of non-zero days.
    first = today - timedelta(days=(today.weekday() + 1) % 7 + 52 * 7)
    days = [first + timedelta(days=i) for i in range((today - first).days + 1)]
    counts = sorted(history[x.isoformat()] for x in days if history[x.isoformat()])
    q = [counts[len(counts) * k // 4] for k in (1, 2, 3)] if counts else [1, 2, 3]

    def level(c):
        return 0 if c == 0 else 1 + sum(c > t for t in q)

    calendar = [
        [{"date": x.isoformat(), "count": history[x.isoformat()], "level": level(history[x.isoformat()])}
         for x in days[i:i + 7]]
        for i in range(0, len(days), 7)
    ]
    year_total = sum(c["count"] for w in calendar for c in w)
    return {
        "login": "sample",
        "created_at": start.isoformat(),
        "year": {"contributions": year_total, "commits": int(year_total * 0.8), "prs": 42,
                 "reviews": 17, "issues": 9, "private": 0},
        "calendar": calendar,
        "history": history,
        "stars": 37,
        "repos": 64,
        "languages": {"Python": 900_000, "TypeScript": 420_000, "Go": 260_000,
                      "C++": 180_000, "JavaScript": 150_000, "Jupyter Notebook": 2_000_000},
    }
