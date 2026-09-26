"""Fetches contribution and repository data from the GitHub GraphQL API.

Standard library only. Returns the same shape as fixtures.sample() so the
renderers never know where their data came from.
"""
import json
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone

API = "https://api.github.com/graphql"

LEVELS = {"NONE": 0, "FIRST_QUARTILE": 1, "SECOND_QUARTILE": 2, "THIRD_QUARTILE": 3, "FOURTH_QUARTILE": 4}

OVERVIEW = """
query($login: String!) {
  user(login: $login) {
    createdAt
    contributionsCollection {
      totalCommitContributions
      totalPullRequestContributions
      totalPullRequestReviewContributions
      totalIssueContributions
      restrictedContributionsCount
      contributionCalendar {
        totalContributions
        weeks { contributionDays { date contributionCount contributionLevel } }
      }
    }
  }
}"""

REPOS = """
query($login: String!, $cursor: String) {
  user(login: $login) {
    repositories(first: 100, after: $cursor, ownerAffiliations: OWNER, isFork: false, privacy: PUBLIC) {
      pageInfo { hasNextPage endCursor }
      nodes {
        stargazerCount
        languages(first: 10, orderBy: {field: SIZE, direction: DESC}) { edges { size node { name } } }
      }
    }
  }
}"""

YEAR = """
query($login: String!, $from: DateTime!, $to: DateTime!) {
  user(login: $login) {
    contributionsCollection(from: $from, to: $to) {
      contributionCalendar { weeks { contributionDays { date contributionCount } } }
    }
  }
}"""


def _query(token, query, variables, attempts=3):
    body = json.dumps({"query": query, "variables": variables}).encode()
    req = urllib.request.Request(API, data=body, headers={
        "Authorization": f"bearer {token}",
        "Content-Type": "application/json",
        "User-Agent": "profile-refresh",
    })
    for attempt in range(attempts):
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                payload = json.load(resp)
            if payload.get("errors"):
                raise RuntimeError(f"GraphQL error: {payload['errors']}")
            return payload["data"]
        except (urllib.error.URLError, TimeoutError) as exc:
            if isinstance(exc, urllib.error.HTTPError) and exc.code in (401, 403):
                raise RuntimeError(f"GitHub rejected the token ({exc.code}); check GH_TOKEN.") from exc
            if attempt == attempts - 1:
                raise
            time.sleep(2 ** attempt * 3)


def _iso(dt):
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def fetch(login, token):
    user = _query(token, OVERVIEW, {"login": login})["user"]
    if user is None:
        raise RuntimeError(f"No GitHub user named {login!r}.")
    cc = user["contributionsCollection"]
    created = datetime.fromisoformat(user["createdAt"].replace("Z", "+00:00"))
    now = datetime.now(timezone.utc)

    calendar = [
        [{"date": d["date"], "count": d["contributionCount"], "level": LEVELS[d["contributionLevel"]]}
         for d in w["contributionDays"]]
        for w in cc["contributionCalendar"]["weeks"]
    ]

    # Full history for streaks: the API caps each window at one year.
    history = {}
    for year in range(created.year, now.year + 1):
        start = max(created, datetime(year, 1, 1, tzinfo=timezone.utc))
        end = min(now, datetime(year, 12, 31, 23, 59, 59, tzinfo=timezone.utc))
        data = _query(token, YEAR, {"login": login, "from": _iso(start), "to": _iso(end)})
        for w in data["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]:
            for d in w["contributionDays"]:
                history[d["date"]] = d["contributionCount"]

    stars, repos, languages, cursor = 0, 0, {}, None
    while True:
        page = _query(token, REPOS, {"login": login, "cursor": cursor})["user"]["repositories"]
        for node in page["nodes"]:
            repos += 1
            stars += node["stargazerCount"]
            for edge in node["languages"]["edges"]:
                name = edge["node"]["name"]
                languages[name] = languages.get(name, 0) + edge["size"]
        if not page["pageInfo"]["hasNextPage"]:
            break
        cursor = page["pageInfo"]["endCursor"]

    return {
        "login": login,
        "created_at": created.date().isoformat(),
        "year": {
            "contributions": cc["contributionCalendar"]["totalContributions"],
            "commits": cc["totalCommitContributions"],
            "prs": cc["totalPullRequestContributions"],
            "reviews": cc["totalPullRequestReviewContributions"],
            "issues": cc["totalIssueContributions"],
            "private": cc["restrictedContributionsCount"],
        },
        "calendar": calendar,
        "history": history,
        "stars": stars,
        "repos": repos,
        "languages": languages,
    }
