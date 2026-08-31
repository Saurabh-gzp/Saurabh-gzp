#!/usr/bin/env python3
"""Generate self-hosted GitHub stats SVGs for Saurabh-gzp's profile README.

No third-party services -> cards can never go down. Runs locally or in
GitHub Actions (stats.yml) with GITHUB_TOKEN. Outputs:
  stats/stats.svg       (repos / stars / forks / followers)
  stats/top-langs.svg   (top languages by bytes, weighted, max 6)
"""
import json
import os
import sys
import urllib.request

USER = "Saurabh-gzp"
TOKEN = os.environ.get("GITHUB_TOKEN") or (sys.argv[1] if len(sys.argv) > 1 else "")

LANG_COLORS = {
    "Python": "#3572A5", "JavaScript": "#F1E05A", "HTML": "#E34C26",
    "CSS": "#563D7C", "Kotlin": "#A97BFF", "Shell": "#89E051",
    "Java": "#B07219", "C": "#555555", "C++": "#F34B7D",
    "TypeScript": "#3178C6", "Go": "#00ADD8", "Rust": "#DEA584",
    "Ruby": "#701516", "PHP": "#4F5D95", "C#": "#178600",
    "Dart": "#00B4AB", "Swift": "#F05138", "Jupyter Notebook": "#DA5B0B",
}


def api(path):
    req = urllib.request.Request(
        "https://api.github.com" + path,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "saurabh-stats-generator",
            **({"Authorization": f"Bearer {TOKEN}"} if TOKEN else {}),
        },
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())


def esc(s):
    return (
        str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def hex_to_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


# ---------------------------------------------------------------- user data
user = api(f"/users/{USER}")
repos = api(f"/users/{USER}/repos?per_page=100&type=owner")

public_repos = user.get("public_repos", 0)
followers = user.get("followers", 0)
stars = sum(r.get("stargazers_count", 0) for r in repos)
forks = sum(r.get("forks_count", 0) for r in repos)

# ------------------------------------------------------------- top languages
lang_bytes = {}
for r in repos:
    if r.get("fork"):
        continue
    name = r.get("name", "")
    if not name or name.lower() == USER.lower():
        continue
    try:
        langs = api(f"/repos/{USER}/{name}/languages")
    except Exception:
        continue
    for lang, b in (langs or {}).items():
        lang_bytes[lang] = lang_bytes.get(lang, 0) + b

total_bytes = sum(lang_bytes.values()) or 1
top = sorted(lang_bytes.items(), key=lambda kv: kv[1], reverse=True)[:6]

# ------------------------------------------------------------- helpers
ACCENT = "#7C3AED"
ACCENT2 = "#22D3EE"
CARD = "#0D1117"
BORDER = "#30363D"
TEXT = "#F8FAFC"
MUTED = "#8B949E"

FONT = "Segoe UI, -apple-system, BlinkMacSystemFont, Helvetica, Arial, sans-serif"


def card_shell(w, h, title, title_icon):
    """Return svg open tag + header, caller appends body + close tag."""
    s = []
    s.append(
        f'<svg width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
        f'xmlns="http://www.w3.org/2000/svg" role="img" aria-label="{esc(title)}">'
    )
    s.append(f'<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="0">'
             f'<stop offset="0" stop-color="{ACCENT}"/>'
             f'<stop offset="1" stop-color="{ACCENT2}"/></linearGradient></defs>')
    s.append(f'<rect x="0.5" y="0.5" width="{w - 1}" height="{h - 1}" rx="10" '
             f'fill="{CARD}" stroke="{BORDER}"/>')
    s.append(f'<rect x="0" y="0" width="6" height="{h}" rx="3" fill="url(#g)"/>')
    # header
    s.append(f'<text x="26" y="38" font-family="{FONT}" font-size="15" '
             f'font-weight="600" fill="{TEXT}">{esc(title_icon)} {esc(title)}</text>')
    return s


def stat_card():
    w, h = 495, 195
    s = card_shell(w, h, "GitHub Stats", "⚡")
    stats = [
        ("Repositories", public_repos),
        ("Total Stars", stars),
        ("Forks", forks),
        ("Followers", followers),
    ]
    cell_w = (w - 40) / 2
    cell_h = 62
    for i, (label, value) in enumerate(stats):
        col, row = i % 2, i // 2
        x = 24 + col * (cell_w + 4)
        y = 66 + row * (cell_h + 6)
        s.append(f'<rect x="{x}" y="{y}" width="{cell_w}" height="{cell_h}" rx="8" '
                 f'fill="#161B22"/>')
        s.append(f'<text x="{x + 16}" y="{y + 30}" font-family="{FONT}" font-size="26" '
                 f'font-weight="700" fill="url(#g)">{value}</text>')
        s.append(f'<text x="{x + 16}" y="{y + 50}" font-family="{FONT}" font-size="12" '
                 f'fill="{MUTED}">{esc(label)}</text>')
    s.append("</svg>")
    return "".join(s)


def langs_card():
    w, h = 495, 240
    s = card_shell(w, h, "Top Languages", "💻")
    y = 68
    bar_x, bar_w = 24, w - 24 - 150 - 60
    for lang, b in top:
        pct = round(b / total_bytes * 100, 1)
        color = LANG_COLORS.get(lang, "#9AA4B2")
        r, g, bl = hex_to_rgb(color)
        s.append(f'<text x="24" y="{y}" font-family="{FONT}" font-size="13" '
                 f'fill="{TEXT}">{esc(lang)}</text>')
        s.append(f'<text x="{w - 60}" y="{y}" font-family="{FONT}" font-size="13" '
                 f'fill="{MUTED}" text-anchor="end">{pct}%</text>')
        # bar background + fill
        s.append(f'<rect x="{bar_x}" y="{y + 4}" width="{bar_w}" height="8" rx="4" '
                 f'fill="#161B22"/>')
        fill_w = max(8, bar_w * b / (top[0][1] or 1))
        s.append(f'<rect x="{bar_x}" y="{y + 4}" width="{fill_w}" height="8" rx="4" '
                 f'fill="rgba({r},{g},{bl},0.85)"/>')
        y += 28
    s.append("</svg>")
    return "".join(s)


os.makedirs("stats", exist_ok=True)
with open("stats/stats.svg", "w") as f:
    f.write(stat_card())
with open("stats/top-langs.svg", "w") as f:
    f.write(langs_card())

print("Wrote stats/stats.svg and stats/top-langs.svg")
print("repos:", public_repos, "| stars:", stars, "| forks:", forks, "| followers:", followers)
print("top languages:", [(l, round(b / total_bytes * 100, 1)) for l, b in top])
