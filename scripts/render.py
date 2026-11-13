#!/usr/bin/env python3
"""Renders the animated profile SVGs (dark + light). Pulls live stats from the GitHub API."""
import json, os, sys, urllib.request
from collections import Counter
from datetime import datetime, timezone
from html import escape
from pathlib import Path

USER = os.getenv("GH_USER") or os.getenv("GITHUB_REPOSITORY_OWNER") or "octocat"
TOKEN = os.getenv("GITHUB_TOKEN")
OUT = Path(__file__).resolve().parent.parent / "assets"

THEMES = {
    "dark":  dict(bg="#0d1117", panel="#161b22", border="#30363d", text="#c9d1d9", muted="#8b949e",
                  blue="#58a6ff", green="#3fb950", purple="#d2a8ff", yellow="#d29922", red="#ff7b72"),
    "light": dict(bg="#ffffff", panel="#f6f8fa", border="#d0d7de", text="#1f2328", muted="#656d76",
                  blue="#0969da", green="#1a7f37", purple="#8250df", yellow="#9a6700", red="#cf222e"),
}
FONT = "'JetBrains Mono','Fira Code',Consolas,Menlo,monospace"

# ---------------------------------------------------------------- data
def gh(path):
    req = urllib.request.Request(f"https://api.github.com{path}", headers={"Accept": "application/vnd.github+json"})
    if TOKEN:
        req.add_header("Authorization", f"Bearer {TOKEN}")
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.load(r)

def ago(iso):
    s = (datetime.now(timezone.utc) - datetime.fromisoformat(iso.replace("Z", "+00:00"))).total_seconds()
    for unit, n in (("d", 86400), ("h", 3600), ("m", 60)):
        if s >= n:
            return f"{int(s // n)}{unit} ago"
    return "just now"

def stats():
    try:
        repos = [r for r in gh(f"/users/{USER}/repos?per_page=100&type=owner") if not r["fork"]]
        langs = Counter()
        for r in repos[:40]:
            langs.update(gh(f"/repos/{USER}/{r['name']}/languages"))
        total = sum(langs.values()) or 1
        top = " · ".join(f"{k} {v * 100 // total}%" for k, v in langs.most_common(3))
        last = max(repos, key=lambda r: r["pushed_at"]) if repos else None
        return dict(
            repos=f"{len(repos)} public · {sum(r['stargazers_count'] for r in repos)} ★",
            langs=top or "C# · Python · SQL",
            push=f"{last['name']} · {ago(last['pushed_at'])}" if last else "—",
        )
    except Exception as e:
        print(f"[warn] GitHub API unavailable ({e}); using fallback", file=sys.stderr)
        return dict(repos="—", langs="C# · Python · SQL", push="—")

# ---------------------------------------------------------------- terminal
def terminal(t, s):
    rows = [
        ("info", "Location ......", "Istanbul, TR"),
        ("info", "Role ..........", ".NET Backend Engineer"),
        ("info", "Domains .......", "IoT · Fleet Telematics · E-Invoicing"),
        ("info", "Repos .........", s["repos"]),
        ("info", "Languages .....", s["langs"]),
        ("info", "Last push .....", s["push"]),
        ("warn", "Coffee ........", "degraded"),
    ]
    y0, step, delay = 114, 28, 1.9
    lines = []
    for i, (lvl, key, val) in enumerate(rows):
        c = t["yellow"] if lvl == "warn" else t["blue"]
        vc = t["yellow"] if lvl == "warn" else t["text"]
        lines.append(
            f'<text x="28" y="{y0 + i * step}" class="l" style="animation-delay:{delay + i * .35:.2f}s" xml:space="preserve">'
            f'<tspan fill="{c}">{lvl}</tspan><tspan fill="{t["muted"]}">: {key}</tspan> '
            f'<tspan fill="{vc}">{escape(val)}</tspan></text>')
    ready_y = y0 + len(rows) * step + 10
    h = ready_y + 46
    rd = delay + len(rows) * .35 + .3
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="820" height="{h}" viewBox="0 0 820 {h}">
<style>
text{{font-family:{FONT};font-size:15px;fill:{t["text"]}}}
.l{{opacity:0;animation:in .4s ease-out forwards}}
@keyframes in{{from{{opacity:0;transform:translateX(-6px)}}to{{opacity:1;transform:none}}}}
.cur{{animation:blink 1s step-end infinite}}
@keyframes blink{{50%{{opacity:0}}}}
</style>
<defs><clipPath id="type"><rect x="0" y="60" height="30" width="0">
<animate attributeName="width" from="0" to="820" begin=".3s" dur="1.4s" fill="freeze"/></rect></clipPath></defs>
<rect x=".5" y=".5" width="819" height="{h - 1}" rx="12" fill="{t["bg"]}" stroke="{t["border"]}"/>
<circle cx="24" cy="22" r="6" fill="#ff5f57"/><circle cx="44" cy="22" r="6" fill="#febc2e"/><circle cx="64" cy="22" r="6" fill="#28c840"/>
<text x="410" y="27" text-anchor="middle" fill="{t["muted"]}" style="font-size:12px;fill:{t["muted"]}">samil@istanbul: ~</text>
<line x1="0" y1="44" x2="820" y2="44" stroke="{t["border"]}"/>
<text x="28" y="80" clip-path="url(#type)" xml:space="preserve"><tspan fill="{t["green"]}">❯</tspan> dotnet run --project <tspan fill="{t["purple"]}">Samil.Profile</tspan></text>
{chr(10).join(lines)}
<g class="l" style="animation-delay:{rd:.2f}s">
<text x="28" y="{ready_y}" xml:space="preserve"><tspan fill="{t["green"]}">❯</tspan> ready</text>
<rect x="98" y="{ready_y - 13}" width="9" height="17" fill="{t["text"]}" class="cur"/></g>
<text x="792" y="{h - 14}" text-anchor="end" style="font-size:11px;fill:{t["muted"]}">synced {stamp}</text>
</svg>'''

# ---------------------------------------------------------------- pipeline
def pipeline(t):
    W, H, MID = 900, 320, 160
    def node(x, y, w, h, title, sub=None, color=None):
        s = f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" fill="{t["panel"]}" stroke="{color or t["border"]}"/>'
        cx = x + w / 2
        if sub:
            s += f'<text x="{cx}" y="{y + h / 2 - 3}" text-anchor="middle" class="t">{title}</text>'
            s += f'<text x="{cx}" y="{y + h / 2 + 13}" text-anchor="middle" class="s">{sub}</text>'
        else:
            s += f'<text x="{cx}" y="{y + h / 2 + 5}" text-anchor="middle" class="t">{title}</text>'
        return s

    parts, wires, packets = [], [], []
    def flow(d, color, dur, begins):
        wires.append(f'<path d="{d}" fill="none" stroke="{t["border"]}" stroke-width="1.5"/>')
        for b in begins:
            packets.append(f'<circle r="3.5" fill="{color}" opacity="0"><animateMotion dur="{dur}s" begin="{b}s" repeatCount="indefinite" path="{d}"/>'
                           f'<animate attributeName="opacity" values="0;1;1;0" keyTimes="0;.1;.9;1" dur="{dur}s" begin="{b}s" repeatCount="indefinite"/></circle>')

    # devices
    for i, (name, sub) in enumerate([("GPS Tracker", "telemetry"), ("CAN / OBD", "vehicle bus"), ("Sensors", "temp · door · fuel")]):
        y = 44 + i * 88
        cy = y + 28
        parts.append(node(30, y, 160, 56, name, sub))
        parts.append(f'<circle cx="46" cy="{y + 14}" r="4" fill="{t["green"]}"><animate attributeName="opacity" values="1;.25;1" dur="{1.6 + i * .3}s" repeatCount="indefinite"/></circle>')
        flow(f"M190,{cy} C225,{cy} 225,{MID} 260,{MID}", t["green"], 1.4, [i * .45, i * .45 + .7])

    parts.append(node(260, MID - 26, 120, 52, "Ingestion", "TCP gateway"))
    flow(f"M380,{MID} L440,{MID}", t["blue"], .8, [0, .4])

    # kafka with partition lanes
    parts.append(f'<rect x="440" y="{MID - 60}" width="130" height="120" rx="8" fill="{t["panel"]}" stroke="{t["purple"]}"/>')
    parts.append(f'<text x="505" y="{MID - 36}" text-anchor="middle" class="t">Kafka</text>')
    for i, dur in enumerate((2.2, 1.7, 2.6)):
        ly = MID - 14 + i * 20
        parts.append(f'<rect x="456" y="{ly}" width="98" height="10" rx="2" fill="none" stroke="{t["border"]}"/>')
        for k in range(3):
            b = f"{k * dur / 3:.2f}"
            parts.append(f'<rect x="458" y="{ly + 2}" width="10" height="6" rx="1" fill="{t["purple"]}" opacity="0">'
                         f'<animate attributeName="x" from="458" to="542" dur="{dur}s" begin="{b}s" repeatCount="indefinite"/>'
                         f'<animate attributeName="opacity" values="0;1;1;0" keyTimes="0;.15;.85;1" dur="{dur}s" begin="{b}s" repeatCount="indefinite"/></rect>')
    parts.append(f'<text x="505" y="{MID + 52}" text-anchor="middle" class="s">p0 · p1 · p2</text>')
    flow(f"M570,{MID} L630,{MID}", t["purple"], .8, [.2, .6])

    parts.append(node(630, MID - 30, 130, 60, ".NET Workers", "MassTransit", t["blue"]))

    sinks = [("PostgreSQL", t["blue"]), ("Redis", t["red"]), ("Alarms", t["yellow"]), ("E-Invoice", t["green"])]
    for i, (name, c) in enumerate(sinks):
        y = 36 + i * 70
        cy = y + 18
        parts.append(node(790, y, 100, 36, name))
        flow(f"M760,{MID} C775,{MID} 775,{cy} 790,{cy}", c, 1.1, [i * .3, i * .3 + .55])

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
<style>
.t{{font-family:{FONT};font-size:13px;fill:{t["text"]};font-weight:600}}
.s{{font-family:{FONT};font-size:10.5px;fill:{t["muted"]}}}
</style>
<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="12" fill="{t["bg"]}" stroke="{t["border"]}"/>
{"".join(wires)}
{"".join(parts)}
{"".join(packets)}
</svg>'''

# ---------------------------------------------------------------- main
if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    s = stats()
    for name, t in THEMES.items():
        (OUT / f"terminal-{name}.svg").write_text(terminal(t, s), encoding="utf-8")
        (OUT / f"pipeline-{name}.svg").write_text(pipeline(t), encoding="utf-8")
    print(f"rendered for @{USER}: {s}")
