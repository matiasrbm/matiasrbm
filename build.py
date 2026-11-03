"""
Generates dark_mode.svg and light_mode.svg (neofetch-style GitHub profile).
Runs daily via GitHub Actions so the uptime (age) counter and the GitHub stats
update by themselves. Only the Python standard library is needed.

Local test:  python build.py
"""
import json
import os
import re
import urllib.request
from calendar import monthrange
from datetime import date, datetime
from html import escape
from zoneinfo import ZoneInfo

# ----------------------------- YOUR DATA -----------------------------------
USER = os.environ.get("USER_NAME", "matiasrbm")
BIRTHDAY = date(2005, 5, 13)
TZ = ZoneInfo("America/Sao_Paulo")

TITLE = "rafael@matias"

# (key, value)  ->  "key" may contain dots, e.g. "Skills.Linux"
# ("-", "Section name") creates a section header.  ("", "") creates a small gap.
ROWS = [
    ("OS", "Fedora, Windows 11, iOS"),
    ("Uptime", "{age}"),                      # filled automatically
    ("Host", "RNP - Rede Nacional de Ensino e Pesquisa"),
    ("Kernel", "Network Analyst"),
    ("Education", "Computer Science, UniCEUB"),
    ("", ""),
    ("Languages.Programming", "PHP, Python, C++, Bash"),
    ("Languages.Real", "Portuguese, English"),
    ("-", "Cybersecurity"),
    ("Focus", "Blue Team, SOC, Incident Response"),
    ("Skills.Networking", "TCP/IP, Routing & Switching, DNS"),
    ("Skills.Linux", "System Administration, Bash Scripting"),
    ("Skills.Security", "Network Security, Log Analysis"),
    ("-", "Certifications"),
    ("Certs.Networking", "CCNA (planned)"),
    ("Certs.Linux", "LPIC-1 (planned)"),
    ("Certs.Security", "Security+, PenTest+, CySA+ (planned)"),
    ("-", "Contact"),
    ("Email.Personal", "matias1rbm@gmail.com"),
    ("Email.Work", "rafael.matias@terceiro.rnp.br"),
    ("LinkedIn", "matiasrbm"),
    ("Discord", "matiasrbm"),
    ("TryHackMe", "matiasrbm"),
    ("-", "GitHub Stats"),
    ("Repos", "{repos}"),
    ("Stars", "{stars}"),
    ("Followers", "{followers}"),
]
# ---------------------------------------------------------------------------

FEDORA = r"""${c1}             .',;::::;,'.
         .';:cccccccccccc:;,.
      .;cccccccccccccccccccccc;.
    .:cccccccccccccccccccccccccc:.
  .;ccccccccccccc;${c2}.:dddl:.${c1};ccccccc;.
 .:ccccccccccccc;${c2}OWMKOOXMWd${c1};ccccccc:.
.:ccccccccccccc;${c2}KMMc${c1};cc;${c2}xMMc${c1};ccccccc:.
,cccccccccccccc;${c2}MMM.${c1};cc;${c2};WW:${c1};cccccccc,
:cccccccccccccc;${c2}MMM.${c1};cccccccccccccccc:
:ccccccc;${c2}oxOOOo${c1};${c2}MMM0OOk.${c1};cccccccccccc:
cccccc;${c2}0MMKxdd:${c1};${c2}MMMkddc.${c1};cccccccccccc;
ccccc;${c2}XM0'${c1};cccc;${c2}MMM.${c1};cccccccccccccccc'
ccccc;${c2}MMo${c1};ccccc;${c2}MMW.${c1};ccccccccccccccc;
ccccc;${c2}0MNc.${c1}ccc${c2}.xMMd${c1};ccccccccccccccc;
cccccc;${c2}dNMWXXXWM0:${c1};cccccccccccccc:,
cccccccc;${c2}.:odl:.${c1};cccccccccccccc:,.
:cccccccccccccccccccccccccccc:'.
.:cccccccccccccccccccccc:;,..
  '::cccccccccccccc::;,."""

THEMES = {
    "dark_mode.svg": dict(bg="#161b22", text="#c9d1d9", key="#ffa657",
                          value="#a5d6ff", cc="#616e7f", c1="#51a2da", c2="#c9d1d9"),
    "light_mode.svg": dict(bg="#f6f8fa", text="#24292f", key="#953800",
                           value="#0a3069", cc="#c2cfde", c1="#3c6eb4", c2="#24292f"),
}

W = 62          # width of the data column, in characters
FS, LH = 15, 20
X_ART, X_DATA = 15, 400


def age(born: date, today: date) -> str:
    y, m, d = today.year - born.year, today.month - born.month, today.day - born.day
    if d < 0:
        m -= 1
        py, pm = (today.year, today.month - 1) if today.month > 1 else (today.year - 1, 12)
        d += monthrange(py, pm)[1]
    if m < 0:
        y -= 1
        m += 12
    pl = lambda n, w: f"{n} {w}{'' if n == 1 else 's'}"
    cake = " 🎂" if (m == 0 and d == 0) else ""
    return f"{pl(y, 'year')}, {pl(m, 'month')}, {pl(d, 'day')}{cake}"


def gh(path):
    req = urllib.request.Request(f"https://api.github.com{path}")
    req.add_header("User-Agent", "profile-readme-builder")
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.load(r)


def stats():
    try:
        u = gh(f"/users/{USER}")
        stars, page = 0, 1
        while True:
            repos = gh(f"/users/{USER}/repos?per_page=100&page={page}")
            stars += sum(r["stargazers_count"] for r in repos)
            if len(repos) < 100:
                break
            page += 1
        return dict(repos=u["public_repos"], stars=stars, followers=u["followers"])
    except Exception as e:  # offline / rate limit: do not break the build
        print("stats unavailable:", e)
        return dict(repos="n/a", stars="n/a", followers="n/a")


def key_markup(key):
    parts = key.split(".")
    return '<tspan class="key">' + '</tspan>.<tspan class="key">'.join(escape(p) for p in parts) + "</tspan>"


def art_markup(art, y0):
    out = []
    for i, line in enumerate(art.splitlines()):
        segs = re.split(r"(\$\{c[12]\})", line)
        cls, buf = "c1", []
        for s in segs:
            if s in ("${c1}", "${c2}"):
                cls = s[2:4]
            elif s:
                buf.append(f'<tspan class="{cls}">{escape(s)}</tspan>')
        out.append(f'<tspan x="{X_ART}" y="{y0 + i * LH}">{"".join(buf)}</tspan>')
    return "\n".join(out)


def build():
    today = datetime.now(TZ).date()
    values = dict(age=age(BIRTHDAY, today), **stats())

    lines, y = [], 30
    lines.append(f'<tspan x="{X_DATA}" y="{y}">{escape(TITLE)}</tspan> '
                 f'<tspan class="cc">{"-" * (W - len(TITLE) - 1)}</tspan>')
    for key, val in ROWS:
        if key == "":
            y += LH // 2
            continue
        y += LH + (LH // 2 if key == "-" else 0)
        if key == "-":
            head = f"- {val} "
            lines.append(f'<tspan x="{X_DATA}" y="{y}">- {escape(val)}</tspan> '
                         f'<tspan class="cc">{"-" * (W - len(head))}</tspan>')
            continue
        val = str(val).format(**values)
        dots = "." * max(2, W - 5 - len(key) - len(val))
        lines.append(f'<tspan x="{X_DATA}" y="{y}" class="cc">. </tspan>{key_markup(key)}:'
                     f'<tspan class="cc"> {dots} </tspan><tspan class="value">{escape(val)}</tspan>')

    height = y + 30
    width = X_DATA + int(W * 9.0) + 20
    art_h = len(FEDORA.splitlines()) * LH
    art_y0 = max(30, (height - art_h) // 2 + 14)

    for name, c in THEMES.items():
        svg = f"""<?xml version='1.0' encoding='UTF-8'?>
<svg xmlns="http://www.w3.org/2000/svg" xml:space="preserve" font-family="ConsolasFallback,Consolas,monospace" width="{width}px" height="{height}px" font-size="{FS}px">
<style>
@font-face {{
src: local('Consolas'), local('Consolas Bold');
font-family: 'ConsolasFallback';
font-display: swap;
-webkit-size-adjust: 109%;
size-adjust: 109%;
}}
.key {{fill: {c['key']};}}
.value {{fill: {c['value']};}}
.cc {{fill: {c['cc']};}}
.c1 {{fill: {c['c1']};}}
.c2 {{fill: {c['c2']};}}
text, tspan {{white-space: pre;}}
</style>
<rect width="{width}px" height="{height}px" fill="{c['bg']}" rx="15"/>
<text x="{X_ART}" y="{art_y0}" fill="{c['text']}">
{art_markup(FEDORA, art_y0)}
</text>
<text x="{X_DATA}" y="30" fill="{c['text']}">
{chr(10).join(lines)}
</text>
</svg>
"""
        with open(name, "w", encoding="utf-8") as f:
            f.write(svg)
    print("OK:", values["age"], "|", width, "x", height)


if __name__ == "__main__":
    build()
