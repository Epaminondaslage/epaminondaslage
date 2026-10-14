#!/usr/bin/env python3
"""Gera SVGs (claro/escuro) do grafico real de contribuicoes via GraphQL."""
import json, os, sys, urllib.request
from datetime import date

USER = os.environ["GH_USER"]
TOKEN = os.environ["GH_TOKEN"]
OUT = sys.argv[1] if len(sys.argv) > 1 else "dist"

QUERY = """query($u:String!){user(login:$u){contributionsCollection{contributionCalendar{
totalContributions weeks{contributionDays{contributionCount date weekday}}}}}}"""

req = urllib.request.Request(
    "https://api.github.com/graphql",
    data=json.dumps({"query": QUERY, "variables": {"u": USER}}).encode(),
    headers={"Authorization": f"bearer {TOKEN}", "Content-Type": "application/json"},
)
with urllib.request.urlopen(req) as r:
    payload = json.load(r)
cal = payload["data"]["user"]["contributionsCollection"]["contributionCalendar"]
weeks = cal["weeks"]
total = cal["totalContributions"]
peak = max((d["contributionCount"] for w in weeks for d in w["contributionDays"]), default=0)

THEMES = {
    "dark": {"bg": "#0d1117", "fg": "#8b949e", "lv": ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"]},
    "light": {"bg": "#ffffff", "fg": "#57606a", "lv": ["#ebedf0", "#9be9a8", "#40c463", "#30a14e", "#216e39"]},
}
MESES = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]
CELL, GAP, LEFT, TOP = 11, 3, 30, 28
STEP = CELL + GAP


def level(n):
    if n == 0 or peak == 0:
        return 0
    r = n / peak
    return 4 if r > 0.75 else 3 if r > 0.5 else 2 if r > 0.25 else 1


def render(t):
    w = LEFT + len(weeks) * STEP + 10
    h = TOP + 7 * STEP + 28
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" font-family="Segoe UI,Helvetica,Arial,sans-serif" font-size="10">',
         f'<rect width="{w}" height="{h}" rx="6" fill="{t["bg"]}"/>']
    last_month = None
    for i, wk in enumerate(weeks):
        first = wk["contributionDays"][0]["date"]
        m = int(first[5:7]) - 1
        if m != last_month and wk["contributionDays"][0]["date"][8:10] <= "21":
            s.append(f'<text x="{LEFT + i * STEP}" y="16" fill="{t["fg"]}">{MESES[m]}</text>')
            last_month = m
        for d in wk["contributionDays"]:
            c = d["contributionCount"]
            s.append(f'<rect x="{LEFT + i * STEP}" y="{TOP + d["weekday"] * STEP}" width="{CELL}" height="{CELL}" rx="2" fill="{t["lv"][level(c)]}"><title>{d["date"]}: {c}</title></rect>')
    for idx, name in ((1, "seg"), (3, "qua"), (5, "sex")):
        s.append(f'<text x="2" y="{TOP + idx * STEP + 9}" fill="{t["fg"]}">{name}</text>')
    s.append(f'<text x="{LEFT}" y="{h - 8}" fill="{t["fg"]}">{total} contribuições nos últimos 12 meses</text>')
    s.append("</svg>")
    return "\n".join(s)


os.makedirs(OUT, exist_ok=True)
for name, t in THEMES.items():
    suffix = "-dark" if name == "dark" else ""
    with open(os.path.join(OUT, f"contributions-graph{suffix}.svg"), "w", encoding="utf-8") as f:
        f.write(render(t))
print(f"ok: {total} contribuicoes, {len(weeks)} semanas")
