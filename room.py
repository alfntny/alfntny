#!/usr/bin/env python3
"""Animated pixel-art room for a GitHub profile README.
Live data: weather + time of day (window), contributions (wall heatmap),
languages (bookshelf + fairy lights), streak (plant), today's commits (monitor).
No dependencies. Env: GH_TOKEN, GH_USER, CITY, LAT, LON, TZ_OFFSET, OUT
"""
import datetime as dt
import json
import os
import random
import urllib.request

USER = os.getenv("GH_USER", "alfntny")
TOKEN = os.getenv("GH_TOKEN", "")
CITY = os.getenv("CITY", "Ernakulam")
LAT, LON = os.getenv("LAT", "9.98"), os.getenv("LON", "76.28")
TZ = dt.timezone(dt.timedelta(minutes=int(os.getenv("TZ_OFFSET", "330"))))
OUT = os.getenv("OUT", "room.svg")
W, H = 400, 225


# ---------------------------------------------------------------- data
def get(url, data=None, headers=None):
    req = urllib.request.Request(url, data=data, headers=headers or {})
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read())


def weather():
    try:
        c = get(f"https://api.open-meteo.com/v1/forecast?latitude={LAT}&longitude={LON}"
                "&current=temperature_2m,weather_code,is_day&timezone=auto")["current"]
        return round(c["temperature_2m"]), int(c["weather_code"])
    except Exception as e:
        print("weather fallback:", e)
        return 28, 61


def kind(code):
    if code in (95, 96, 99): return "storm"
    if code in (71, 73, 75, 77, 85, 86): return "snow"
    if code in (51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 80, 81, 82): return "rain"
    if code in (45, 48): return "fog"
    if code in (2, 3): return "cloud"
    return "clear"


LABEL = {"storm": "thunderstorm", "snow": "snow", "rain": "rain", "fog": "fog",
         "cloud": "cloudy", "clear": "clear sky"}

Q = """query($u:String!,$f:DateTime!,$t:DateTime!){user(login:$u){
contributionsCollection(from:$f,to:$t){contributionCalendar{totalContributions
 weeks{contributionDays{contributionCount date}}}}
repositories(first:100,ownerAffiliations:OWNER,isFork:false){nodes{
 languages(first:10,orderBy:{field:SIZE,direction:DESC}){edges{size node{name color}}}}}}}"""


def github():
    try:
        now = dt.datetime.now(TZ).replace(microsecond=0)
        start = (now - dt.timedelta(days=364)).replace(hour=0, minute=0, second=0)
        body = json.dumps({"query": Q, "variables": {
            "u": USER, "f": start.isoformat(), "t": now.isoformat()}}).encode()
        u = get("https://api.github.com/graphql", body,
                {"Authorization": f"bearer {TOKEN}", "Content-Type": "application/json"})["data"]["user"]
        cal = u["contributionsCollection"]["contributionCalendar"]
        days = [(d["date"], d["contributionCount"]) for w in cal["weeks"] for d in w["contributionDays"]]
        langs = {}
        for repo in u["repositories"]["nodes"]:
            for e in repo["languages"]["edges"]:
                n = e["node"]
                s, col = langs.get(n["name"], (0, n["color"] or "#888"))
                langs[n["name"]] = (s + e["size"], col)
        return cal["totalContributions"], days, langs
    except Exception as e:
        print("github fallback:", e)
        rnd = random.Random(1)
        today = dt.datetime.now(TZ).date()
        days = [((today - dt.timedelta(days=i)).isoformat(), rnd.choice([0, 0, 1, 2, 3, 5, 8, 12]))
                for i in range(364, -1, -1)]
        days[-1] = (days[-1][0], 4)
        langs = {"Python": (60, "#3572A5"), "Java": (20, "#b07219"), "JavaScript": (10, "#f1e05a"),
                 "HTML": (5, "#e34c26"), "CSS": (3, "#563d7c"), "Shell": (2, "#89e051")}
        return sum(c for _, c in days), days, langs


def streak(days):
    s, seq = 0, list(reversed(days))
    if seq and seq[0][1] == 0:
        seq = seq[1:]  # today not over yet
    for _, c in seq:
        if c == 0:
            break
        s += 1
    return s


# ---------------------------------------------------------------- drawing
def rect(x, y, w, h, f, a=""):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{f}" {a}/>'


def sprite(rows, x, y, pal, s=2):
    out = []
    for j, row in enumerate(rows):
        i = 0
        while i < len(row):
            ch = row[i]
            if ch == ".":
                i += 1
                continue
            k = i
            while k < len(row) and row[k] == ch:
                k += 1
            out.append(rect(x + i * s, y + j * s, (k - i) * s, s, pal[ch]))
            i = k
    return "".join(out)


def text(x, y, t, size=6, fill="#e6edf3", anchor="start", a=""):
    return (f'<text x="{x}" y="{y}" font-family="\'Courier New\',monospace" font-size="{size}" '
            f'font-weight="bold" fill="{fill}" text-anchor="{anchor}" {a}>{t}</text>')


CHAR = [
    "....HHHHHH....",
    "...HHHHHHHH...",
    "...SSSSHHHHH..",
    "..SSESSSHHHH..",
    "..SSSSSSSHHH..",
    "...SSSSSSSH...",
    "....SSSSS.....",
    ".....SSS......",
    "....TTTTTT....",
    "...TTTTTTTT...",
    "...TTTTTTTT...",
    "...TTTTTTTT...",
    "...TTTTTTTT...",
    "...TTTTTTTT...",
    "...TTTTTTTT...",
    "...TTTTTTTT...",
    "...TTTTTTTT...",
    "...DDDDDDDD...",
    "PPPPPPPPPPP...",
    "PPPPPPPPPPP...",
    "..PPP.........",
    "..PPP.........",
    "..PPP.........",
    "..PPP.........",
    "..PPP.........",
    "..PPP.........",
    "..PPP.........",
    "..PPP.........",
    "BBBBB.........",
    "BBBBB.........",
]
ARM = ["......AA", "..AAAAA.", "SSAA...."]
CHAIR = [
    "...........KK",
    "...........KK",
    "...........KK",
    "...........KK",
    "...........KK",
    "...........KK",
    "...........KK",
    "...........KK",
    "...........KK",
    "...........KK",
    "...........KK",
    "...........KK",
    "..KKKKKKKKKKK",
    "..KKKKKKKKKKK",
    ".......k.....",
    ".......k.....",
    ".......k.....",
    ".......k.....",
    ".......k.....",
    ".......k.....",
    "....kkkkkkk..",
    "....k.....k..",
]
CAT = [
    "..O.O.........",
    "..OOO.........",
    ".OOOOOOOOOOO..",
    ".OEOOoOOoOOOO.",
    "..OOOOOOOOOOO.",
    "...O.O....O.O.",
]


def build():
    now = dt.datetime.now(TZ)
    hour = now.hour + now.minute / 60
    temp, code = weather()
    wk = kind(code)
    total, days, langs = github()
    today = days[-1][1] if days else 0
    st = streak(days)
    top = sorted(langs.items(), key=lambda kv: -kv[1][0])[:6]
    lsum = sum(v[0] for _, v in top) or 1
    lang_cols = [v[1] for _, v in top] or ["#58a6ff"]
    night = hour < 6 or hour >= 19
    dusk = 17 <= hour < 19
    dawn = 6 <= hour < 7.5
    asleep = night and today == 0
    rnd = random.Random(now.strftime("%Y%m%d%H"))

    o = []
    # --- room shell
    wall = "#3b3561"
    o.append(rect(0, 0, W, 178, wall))
    for x in range(0, W, 16):  # wallpaper stripes
        o.append(rect(x, 0, 8, 178, "#403a68"))
    o.append(rect(0, 170, W, 8, "#2a2548"))  # skirting
    o.append(rect(0, 178, W, 22, "#6b4428"))
    for y in (183, 190, 196):
        o.append(rect(0, y, W, 1, "#5a3820"))
    for x in range(10, W, 46):
        o.append(rect(x, 178, 1, 22, "#5a3820"))
    o.append(rect(178, 186, 120, 8, "#7a2e48"))  # rug
    o.append(rect(182, 188, 112, 4, "#9a3c5c"))

    # --- window frame
    o.append(rect(22, 20, 116, 84, "#2a2140"))
    o.append(rect(18, 102, 124, 6, "#5c4a7a"))  # sill

    # --- cat on floor
    eyes = "#2a2140" if night else "#9be564"
    o.append(sprite(CAT, 40, 166, {"O": "#e0913a", "o": "#b86a22", "E": eyes}))
    o.append(f'<g class="tail">{rect(64, 166, 4, 2, "#e0913a")}{rect(66, 162, 2, 4, "#e0913a")}</g>')
    if night:
        o.append(f'<g class="z">{text(44, 160, "z", 6, "#c9d1ff")}</g>')

    # --- shelf + books (languages)
    o.append(rect(288, 56, 96, 4, "#7a4e2e"))
    o.append(rect(288, 96, 96, 4, "#7a4e2e"))
    for bx in (292, 376):
        o.append(rect(bx, 60, 4, 6, "#5a3820"))
        o.append(rect(bx, 100, 4, 6, "#5a3820"))
    shelf_y, bx = 56, 292
    for name, (size, col) in top:
        bw = max(5, round(size / lsum * 140))
        while bw > 0:
            room_left = 380 - bx
            if room_left < 5:
                if shelf_y == 96:
                    bw = 0
                    break
                shelf_y, bx = 96, 292
                continue
            w = min(bw, room_left, 7 + (bx % 5))
            bh = 16 + ((bx * 7 + sum(map(ord, name))) % 12)
            o.append(rect(bx, shelf_y - bh, w, bh, col))
            o.append(rect(bx, shelf_y - bh + 3, w, 2, "#00000040"))
            o.append(rect(bx, shelf_y - 5, w, 1, "#ffffff40"))
            bx += w + 1
            bw -= w
    # trophy on bottom shelf
    if total >= 100:
        o.append(sprite(["YYYYY", "YYYYY", ".YYY.", "..Y..", ".YYY."], 366, 86, {"Y": "#ffd34e"}))

    # --- plant (streak)
    stem = 6 + 4 * min(st, 12)
    o.append(f'<g class="sway">')
    o.append(rect(337, 164 - stem, 2, stem, "#3f8f3a"))
    for i in range(0, stem - 4, 6):
        side = -6 if (i // 6) % 2 else 2
        o.append(rect(337 + side, 164 - i - 6, 6, 3, "#5cc24f"))
    if st >= 7:
        o.append(rect(334, 158 - stem, 8, 6, "#ff6fa8"))
        o.append(rect(336, 160 - stem, 4, 2, "#ffe066"))
    o.append("</g>")
    o.append(rect(330, 164, 16, 14, "#c0623a"))
    o.append(rect(328, 164, 20, 3, "#d8784e"))
    o.append(text(338, 174, str(st), 6, "#fff3d6", "middle"))

    # --- chair, character, desk
    o.append(sprite(CHAIR, 222, 154, {"K": "#2d2d3a", "k": "#1d1d26"}))
    pal = {"H": "#2b1b12", "S": "#e8b48a", "E": "#e8b48a" if asleep else "#1b1b1b",
           "T": "#2f81f7", "D": "#1f3b6e", "P": "#30363d", "B": "#111"}
    o.append(sprite(CHAR, 222, 118, pal))
    arm = sprite(ARM, 214, 134, {"A": "#2f81f7", "S": "#e8b48a"})
    o.append(f'<g class="{"" if asleep else "type"}">{arm}</g>')
    if asleep:
        for i, d in enumerate((0, 1, 2)):
            o.append(f'<g class="z" style="animation-delay:{d}s">{text(244 + i * 4, 114, "Z", 7, "#c9d1ff")}</g>')

    o.append(rect(94, 138, 146, 5, "#8a5a36"))  # desk top
    o.append(rect(94, 143, 146, 2, "#6b4428"))
    o.append(rect(98, 145, 5, 33, "#6b4428"))
    o.append(rect(231, 145, 5, 33, "#6b4428"))
    o.append(rect(196, 135, 26, 3, "#d0d7de"))  # keyboard
    o.append(rect(198, 135, 22, 1, "#8c959f"))

    # monitor
    o.append(rect(134, 92, 76, 42, "#1c1f26"))
    o.append(rect(164, 134, 14, 4, "#1c1f26"))
    # mug
    o.append(rect(122, 128, 8, 10, "#e6edf3"))
    o.append(rect(130, 130, 3, 5, "#e6edf3"))
    o.append(rect(122, 128, 8, 2, "#6b3b1f"))
    # lamp body
    o.append(rect(98, 134, 12, 4, "#30363d"))
    o.append(rect(103, 106, 2, 28, "#30363d"))
    o.append(rect(103, 104, 16, 2, "#30363d"))
    o.append(rect(114, 100, 12, 6, "#f0b429" if night else "#8b6b1f"))

    # --- night overlay
    if night:
        o.append(rect(0, 0, W, 200, "#070b24", 'opacity=".55"'))
    elif dusk or dawn:
        o.append(rect(0, 0, W, 200, "#3a1a3a", 'opacity=".2"'))

    # --- fairy lights (language colours)
    o.append('<path d="M0 6 Q50 16 100 6 T200 6 T300 6 T400 6" stroke="#222" fill="none" stroke-width="1"/>')
    for i in range(20):
        x = 10 + i * 20
        y = 9 if i % 2 else 11
        c = lang_cols[i % len(lang_cols)]
        o.append(rect(x, y, 3, 4, c, f'class="fl" style="animation-delay:{(i % 5) * 0.3:.1f}s"'))

    # --- window sky
    if night:
        sky = ["#0b1033", "#101646", "#151d58", "#1b2468"]
    elif dusk:
        sky = ["#4b3b8f", "#a04f8a", "#ff7a59", "#ffb36b"]
    elif dawn:
        sky = ["#6fa8ff", "#a8c8ff", "#ffc7a1", "#ffd9a8"]
    else:
        sky = ["#4fb3ff", "#6ec6ff", "#8fd5ff", "#b4e4ff"]
    if wk in ("rain", "storm", "fog") and not night:
        sky = ["#5d6b7d", "#6c7a8c", "#7b899b", "#8a98aa"]
    o.append('<defs><clipPath id="win"><rect x="26" y="24" width="108" height="76"/></clipPath>'
             '<radialGradient id="glow"><stop offset="0" stop-color="#ffd27a" stop-opacity=".55"/>'
             '<stop offset="1" stop-color="#ffd27a" stop-opacity="0"/></radialGradient></defs>')
    o.append('<g clip-path="url(#win)">')
    for i, c in enumerate(sky):
        o.append(rect(26, 24 + i * 19, 108, 19, c))
    if night:
        for _ in range(14):
            o.append(rect(rnd.randint(28, 130), rnd.randint(26, 70), 1, 1, "#fff",
                          f'class="fl" style="animation-delay:{rnd.random()*2:.2f}s"'))
        o.append(sprite(["..MMM.", ".MMM..", "MMM...", "MMM...", ".MMM..", "..MMM."], 104, 30, {"M": "#f4f1c9"}))
    elif wk in ("clear", "cloud"):
        o.append(rect(108, 32, 14, 14, "#ffe066"))
        o.append(rect(106, 34, 18, 10, "#ffe066"))
        o.append(rect(110, 30, 10, 18, "#ffd23f"))
    # city skyline
    for i in range(9):
        bh = 10 + (i * 37) % 22
        x = 26 + i * 12
        o.append(rect(x, 100 - bh, 11, bh, "#1a1530" if night else "#4a4f6a"))
        if night:
            for wy in range(100 - bh + 3, 98, 5):
                if rnd.random() < .5:
                    o.append(rect(x + 3, wy, 2, 2, "#ffd27a"))
    ncloud = {"clear": 1, "cloud": 4, "rain": 4, "storm": 5, "fog": 2, "snow": 3}[wk]
    ccol = "#d8dee9" if wk in ("clear", "cloud", "snow") else "#9aa4b2"
    if night:
        ccol = "#3a4170"
    for i in range(ncloud):
        cy = 30 + (i * 13) % 30
        o.append(f'<g class="cloud" style="animation-delay:-{i * 7}s;animation-duration:{26 + i * 4}s">'
                 f'{rect(0, cy, 22, 6, ccol)}{rect(4, cy - 4, 12, 4, ccol)}</g>')
    if wk in ("rain", "storm"):
        for _ in range(40):
            x = rnd.randint(30, 150)
            o.append(rect(x, rnd.randint(24, 100), 1, 4, "#a9d4ff",
                          f'class="drop" style="animation-delay:-{rnd.random():.2f}s"'))
    if wk == "snow":
        for _ in range(30):
            o.append(rect(rnd.randint(26, 140), rnd.randint(24, 100), 2, 2, "#fff",
                          f'class="snow" style="animation-delay:-{rnd.random()*4:.2f}s"'))
    if wk == "fog":
        for i in range(3):
            o.append(f'<g class="cloud" style="animation-delay:-{i*9}s;animation-duration:20s">'
                     f'{rect(-20, 50 + i * 14, 120, 5, "#e5e9f0", "opacity=.5")}</g>')
    if wk == "storm":
        o.append(rect(26, 24, 108, 76, "#fff", 'class="flash"'))
    o.append("</g>")
    o.append(rect(78, 24, 4, 76, "#2a2140"))  # mullions
    o.append(rect(26, 60, 108, 4, "#2a2140"))
    if wk in ("rain", "storm"):  # drops on glass
        for _ in range(6):
            o.append(rect(rnd.randint(30, 128), rnd.randint(28, 94), 2, 3, "#cfe8ff", 'opacity=".7"'))

    # --- contribution poster
    o.append(rect(156, 12, 118, 66, "#e9e1cf"))
    o.append(rect(158, 14, 114, 62, "#0d1117"))
    o.append(text(162, 22, f"{total} contributions / yr", 6, "#7ee787"))
    recent = days[-119:]
    lvl = lambda c: "#161b22" if c == 0 else "#0e4429" if c <= 2 else "#006d32" if c <= 5 else "#26a641" if c <= 9 else "#39d353"
    # align so the last column ends on today
    pad = (7 - len(recent) % 7) % 7
    cells = [None] * pad + recent
    for i, cell in enumerate(cells):
        if cell is None:
            continue
        wx, wy = i // 7, i % 7
        a = 'class="today"' if i == len(cells) - 1 else ""
        o.append(rect(162 + wx * 6, 26 + wy * 6, 5, 5, lvl(cell[1]), a))
    o.append(rect(212, 6, 6, 8, "#c0392b"))  # pin

    # --- monitor screen (glows)
    o.append(rect(138, 96, 68, 34, "#0d1117"))
    for i in range(5):
        lw = 14 + (i * 23 + today * 7) % 40
        c = lang_cols[i % len(lang_cols)]
        o.append(rect(148, 100 + i * 6, lw, 3, c, f'class="ln" style="animation-delay:{i*0.8:.1f}s"'))
        o.append(rect(141, 100 + i * 6, 4, 3, "#484f58"))
    o.append(rect(148, 100 + 5 * 6 - 1, 3, 4, "#e6edf3", 'class="blink"'))
    if night:
        o.append(f'<ellipse cx="172" cy="113" rx="44" ry="30" fill="url(#glow)" opacity=".5"/>')
    # sticky note
    o.append(rect(194, 88, 18, 14, "#ffe066"))
    o.append(text(203, 98, f"+{today}", 7, "#3b2a00", "middle"))

    # --- steam + lamp light
    for i in range(3):
        o.append(rect(124 + i * 2, 120 - i * 2, 1, 4, "#ffffff",
                      f'class="steam" style="animation-delay:{i*0.6:.1f}s"'))
    if night:
        o.append('<polygon points="114,106 126,106 150,138 90,138" fill="#ffd27a" opacity=".22"/>')
        o.append('<ellipse cx="120" cy="120" rx="40" ry="30" fill="url(#glow)"/>')

    # --- status bar
    o.append(rect(0, 200, W, 25, "#0d1117"))
    o.append(rect(0, 200, W, 1, "#30363d"))
    lang_txt = top[0][0] if top else "-"
    status = (f"{CITY} {temp}°C {LABEL[wk]}  ·  {st}-day streak  ·  "
              f"+{today} today  ·  mostly {lang_txt}")
    o.append(text(8, 215, status, 7, "#e6edf3"))
    o.append(text(W - 8, 215, now.strftime("%H:%M"), 7, "#7ee787", "end"))

    css = """
.type{animation:type .3s steps(1) infinite}
@keyframes type{50%{transform:translateY(-1px)}}
.ln{transform-box:fill-box;transform-origin:left;animation:ln 4s steps(8) infinite both}
@keyframes ln{0%{transform:scaleX(0)}45%,100%{transform:scaleX(1)}}
.blink,.today{animation:blink 1s steps(1) infinite}
@keyframes blink{50%{opacity:0}}
.fl{animation:tw 1.6s steps(1) infinite}
@keyframes tw{50%{opacity:.25}}
.cloud{animation:drift 30s linear infinite}
@keyframes drift{from{transform:translateX(-30px)}to{transform:translateX(140px)}}
.drop{animation:rain .6s linear infinite}
@keyframes rain{from{transform:translate(0,-80px)}to{transform:translate(-14px,80px)}}
.snow{animation:snow 4s linear infinite}
@keyframes snow{from{transform:translate(0,-80px)}to{transform:translate(6px,80px)}}
.flash{opacity:0;animation:flash 6s steps(1) infinite}
@keyframes flash{0%{opacity:0}90%{opacity:.85}92%{opacity:0}95%{opacity:.6}97%{opacity:0}}
.steam{animation:steam 1.8s steps(6) infinite}
@keyframes steam{0%{transform:translateY(0);opacity:.8}100%{transform:translateY(-12px);opacity:0}}
.tail{transform-box:fill-box;transform-origin:0 100%;animation:tail 1.2s steps(2) infinite alternate}
@keyframes tail{to{transform:rotate(-30deg)}}
.z{animation:z 3s linear infinite}
@keyframes z{0%{transform:translate(0,0);opacity:0}20%{opacity:1}100%{transform:translate(10px,-18px);opacity:0}}
.sway{transform-box:fill-box;transform-origin:50% 100%;animation:sway 3s ease-in-out infinite alternate}
@keyframes sway{from{transform:rotate(-3deg)}to{transform:rotate(3deg)}}
"""
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W*2}" height="{H*2}" '
           f'shape-rendering="crispEdges"><style>{css}</style>{"".join(o)}</svg>')
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"wrote {OUT}: {wk}, {temp}C, streak {st}, today {today}, night={night}")


if __name__ == "__main__":
    build()
