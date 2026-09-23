"""Draws the last 31 days of contributions as a line graph (graph.svg)."""
import json, os, subprocess, urllib.request

USER = "xoorki"
DAYS = 31
QUERY = """query($login: String!) { user(login: $login) { contributionsCollection {
  contributionCalendar { weeks { contributionDays { date contributionCount } } } } } }"""


def fetch():
    token = os.environ.get("GITHUB_TOKEN") or subprocess.run(
        [os.path.expanduser("~/bin/gh"), "auth", "token"], capture_output=True, text=True
    ).stdout.strip()
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"login": USER}}).encode(),
        headers={"Authorization": f"bearer {token}"},
    )
    weeks = json.load(urllib.request.urlopen(req))["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]
    return [d for w in weeks for d in w["contributionDays"]][-DAYS:]


def draw(days):
    w, h, left, right, top, bottom = 1000, 300, 50, 20, 50, 50
    pw, ph = w - left - right, h - top - bottom
    peak = max(max(d["contributionCount"] for d in days), 4)
    pts = [
        (left + i * pw / (len(days) - 1), top + ph - d["contributionCount"] / peak * ph)
        for i, d in enumerate(days)
    ]
    line = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    area = f"{left},{top + ph} {line} {left + pw},{top + ph}"
    grid = "".join(
        f'<line x1="{left}" x2="{left + pw}" y1="{top + ph - f * ph:.1f}" y2="{top + ph - f * ph:.1f}" stroke="#21262d"/>'
        f'<text x="{left - 10}" y="{top + ph - f * ph + 4:.1f}" text-anchor="end">{round(f * peak)}</text>'
        for f in (0, 0.25, 0.5, 0.75, 1)
    )
    dots = "".join(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3.5" fill="#0d1117" stroke="#58a6ff" stroke-width="2"/>' for x, y in pts)
    labels = "".join(
        f'<text x="{x:.1f}" y="{top + ph + 20}" text-anchor="middle">{int(d["date"][8:])}</text>'
        for (x, _), d in zip(pts, days)
    )
    total = sum(d["contributionCount"] for d in days)
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">
  <defs><linearGradient id="fill" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#58a6ff" stop-opacity="0.35"/><stop offset="1" stop-color="#58a6ff" stop-opacity="0"/>
  </linearGradient></defs>
  <rect width="{w}" height="{h}" rx="14" fill="#0d1117"/>
  <g font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="11" fill="#8b949e">
    <text x="{w / 2}" y="30" text-anchor="middle" font-size="15" fill="#58a6ff">{USER}'s contribution graph</text>
    <text x="{w - right}" y="30" text-anchor="end">{total} in the last {DAYS} days</text>
    {grid}{labels}
  </g>
  <polygon points="{area}" fill="url(#fill)"/>
  <polyline points="{line}" fill="none" stroke="#58a6ff" stroke-width="2.5" stroke-linejoin="round"/>
  {dots}
</svg>
"""


if __name__ == "__main__":
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "graph.svg")
    with open(out, "w") as f:
        f.write(draw(fetch()))
