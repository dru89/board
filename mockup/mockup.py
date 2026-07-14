#!/usr/bin/env python3
"""Static mockup of the 800x480 e-ink dashboard.

Renders the layout with sample data (mirroring real HA entities) so spacing
and typography can be iterated on before writing the ESPHome lambda.

Outputs:
  out/mockup.png     - 1-bit, honest preview of what the panel will show
  out/mockup_aa.png  - antialiased grayscale, easier on the eyes while iterating
"""

from PIL import Image, ImageDraw, ImageFont

# ---------------------------------------------------------------- sample data
# Values pulled from live HA state on 2026-07-13 where possible.

DATA = {
    "time": "9:41",
    "ampm": "PM",
    "date": "Monday, July 13",
    "weather": {
        "condition": "Clear",          # clear-day | clear-night | cloudy | rain
        "icon": "sun",                 # sun | moon | cloud | rain
        "temp": 61,
        "feels": 60,
        "high": 78,
        "low": 49,
        "rain_pct": 0,
        "wind": 8,
    },
    # who: D=Drew, A=Ashley, F=Family, B=Birthday
    "days": [
        {
            "label": "TODAY",
            "events": [
                {"time": "6:00 PM", "title": "Soccer practice pickup", "who": "F"},
                {"time": "7:30 PM", "title": "Poker night at Mike's", "who": "D"},
            ],
        },
        {
            "label": "TOMORROW",
            "events": [
                {"time": "9:00 AM", "title": "Dentist", "who": "A"},
                {"time": "12:00 PM", "title": "Lunch w/ platform team", "who": "D"},
            ],
        },
        {
            "label": "WED JUL 15",
            "events": [
                {"time": "All day", "title": "School book fair", "who": "F"},
                {"time": "3:30 PM", "title": "Haircut appointment downtown", "who": "A"},
            ],
        },
    ],
    "trash": {"show": True, "recycling": True},
    # droppable: removed (in list order) when alert pills need room
    "status": [
        {"icon": "shield", "text": "Disarmed", "alert": False},
        {"icon": "lock", "text": "1 unlocked", "alert": True},
        {"icon": "garage", "text": "Closed", "alert": False},
        {"icon": "thermo", "text": "69° in", "alert": False, "droppable": 1},
        {"icon": "car", "text": "EV 87%", "alert": False, "droppable": 2},
    ],
    # worst offender first; rendered as one pill: "Garage lock 2%" (+N if more)
    "battery_alerts": [
        {"name": "Garage lock", "pct": 2},
        {"name": "Kitchen motion", "pct": None},   # binary low-battery warning
        {"name": "Upstairs glass break", "pct": None},
        {"name": "Family rm glass break", "pct": None},
    ],
}

# ---------------------------------------------------------------- rendering

W, H = 800, 480
S = 2  # supersample factor
BLACK, WHITE = 0, 255

FONT = "/usr/share/fonts/liberation/LiberationSans-Regular.ttf"
FONT_BOLD = "/usr/share/fonts/liberation/LiberationSans-Bold.ttf"

LEFT_W = 296          # left column width
STATUS_H = 56         # bottom status bar height
MARGIN = 20


def font(size, bold=False):
    return ImageFont.truetype(FONT_BOLD if bold else FONT, size * S)


def sx(*vals):
    out = tuple(v * S for v in vals)
    return out if len(out) > 1 else out[0]


class Canvas:
    def __init__(self):
        self.img = Image.new("L", (W * S, H * S), WHITE)
        self.d = ImageDraw.Draw(self.img)

    def text(self, xy, s, f, fill=BLACK, anchor="la"):
        self.d.text(sx(*xy), s, font=f, fill=fill, anchor=anchor)

    def text_w(self, s, f):
        return (self.d.textbbox((0, 0), s, font=f)[2]) / S

    def line(self, x0, y0, x1, y1, w=2, fill=BLACK):
        self.d.line(sx(x0, y0) + sx(x1, y1), fill=fill, width=w * S)

    def ellipse(self, x0, y0, x1, y1, fill=None, outline=None, w=2):
        self.d.ellipse(sx(x0, y0) + sx(x1, y1), fill=fill, outline=outline,
                       width=w * S)

    def rrect(self, x0, y0, x1, y1, r, fill=None, outline=None, w=2):
        self.d.rounded_rectangle(sx(x0, y0) + sx(x1, y1), radius=r * S,
                                 fill=fill, outline=outline, width=w * S)

    def poly(self, pts, fill=None, outline=None, w=2):
        pts = [sx(x, y) for x, y in pts]
        self.d.polygon(pts, fill=fill, outline=outline, width=w * S)

    def arc(self, x0, y0, x1, y1, a0, a1, w=2, fill=BLACK):
        self.d.arc(sx(x0, y0) + sx(x1, y1), a0, a1, fill=fill, width=w * S)


# ------------------------------------------------------------------- icons
# All icons draw inside a (x, y, size) box, chunky enough to survive 1-bit.

def icon_sun(c, x, y, s, fill=BLACK):
    cx, cy, r = x + s / 2, y + s / 2, s * 0.26
    c.ellipse(cx - r, cy - r, cx + r, cy + r, outline=fill, w=3)
    import math
    for i in range(8):
        a = math.radians(i * 45)
        r0, r1 = s * 0.36, s * 0.48
        c.line(cx + r0 * math.cos(a), cy + r0 * math.sin(a),
               cx + r1 * math.cos(a), cy + r1 * math.sin(a), w=3, fill=fill)


def icon_moon(c, x, y, s, fill=BLACK):
    cx, cy, r = x + s / 2, y + s / 2, s * 0.38
    c.ellipse(cx - r, cy - r, cx + r, cy + r, fill=fill)
    off = s * 0.22
    c.ellipse(cx - r + off, cy - r - off * 0.4, cx + r + off,
              cy + r - off * 0.4, fill=WHITE)


def icon_cloud(c, x, y, s, fill=BLACK):
    c.ellipse(x + s * 0.08, y + s * 0.38, x + s * 0.52, y + s * 0.78,
              outline=fill, w=3)
    c.ellipse(x + s * 0.30, y + s * 0.18, x + s * 0.80, y + s * 0.68,
              outline=fill, w=3)
    c.rrect(x + s * 0.18, y + s * 0.52, x + s * 0.86, y + s * 0.78, r=int(s * 0.12),
            fill=WHITE, outline=None)
    c.line(x + s * 0.20, y + s * 0.78, x + s * 0.84, y + s * 0.78, w=3, fill=fill)


def icon_trash(c, x, y, s, fill=BLACK):
    c.rrect(x + s * 0.18, y + s * 0.24, x + s * 0.82, y + s * 0.92,
            r=int(s * 0.06), outline=fill, w=3)
    c.line(x + s * 0.08, y + s * 0.24, x + s * 0.92, y + s * 0.24, w=3, fill=fill)
    c.line(x + s * 0.38, y + s * 0.10, x + s * 0.62, y + s * 0.10, w=3, fill=fill)
    c.line(x + s * 0.38, y + s * 0.10, x + s * 0.38, y + s * 0.24, w=3, fill=fill)
    c.line(x + s * 0.62, y + s * 0.10, x + s * 0.62, y + s * 0.24, w=3, fill=fill)
    for fx in (0.36, 0.50, 0.64):
        c.line(x + s * fx, y + s * 0.36, x + s * fx, y + s * 0.80, w=3, fill=fill)


def icon_recycle(c, x, y, s, fill=BLACK):
    # simplified: bold triangle with clipped corners + arrowheads
    import math
    cx, cy, r = x + s / 2, y + s * 0.56, s * 0.40
    pts = [(cx + r * math.cos(math.radians(a)), cy + r * math.sin(math.radians(a)))
           for a in (-90, 30, 150)]
    for i in range(3):
        p0, p1 = pts[i], pts[(i + 1) % 3]
        mx, my = (p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2
        c.line(p0[0], p0[1], mx, my, w=3, fill=fill)
        gx, gy = mx + (p1[0] - p0[0]) * 0.18, my + (p1[1] - p0[1]) * 0.18
        c.line(gx, gy, p1[0], p1[1], w=3, fill=fill)
        # arrowhead at the gap
        dx, dy = (p1[0] - p0[0]), (p1[1] - p0[1])
        ln = math.hypot(dx, dy)
        ux, uy = dx / ln, dy / ln
        px, py = -uy, ux
        ah = s * 0.10
        c.poly([(mx + ux * ah, my + uy * ah),
                (mx - ux * ah * 0.4 + px * ah, my - uy * ah * 0.4 + py * ah),
                (mx - ux * ah * 0.4 - px * ah, my - uy * ah * 0.4 - py * ah)],
               fill=fill)


def icon_shield(c, x, y, s, fill=BLACK):
    c.poly([(x + s * 0.5, y + s * 0.06), (x + s * 0.88, y + s * 0.22),
            (x + s * 0.88, y + s * 0.52), (x + s * 0.5, y + s * 0.94),
            (x + s * 0.12, y + s * 0.52), (x + s * 0.12, y + s * 0.22)],
           outline=fill, w=3)


def icon_lock(c, x, y, s, fill=BLACK):
    c.rrect(x + s * 0.16, y + s * 0.42, x + s * 0.84, y + s * 0.92,
            r=int(s * 0.08), outline=fill, w=3)
    c.arc(x + s * 0.26, y + s * 0.06, x + s * 0.74, y + s * 0.58, 180, 360, w=3,
          fill=fill)
    c.ellipse(x + s * 0.44, y + s * 0.58, x + s * 0.56, y + s * 0.70, fill=fill)


def icon_garage(c, x, y, s, fill=BLACK):
    c.poly([(x + s * 0.08, y + s * 0.42), (x + s * 0.5, y + s * 0.08),
            (x + s * 0.92, y + s * 0.42)], outline=fill, w=3)
    c.line(x + s * 0.14, y + s * 0.42, x + s * 0.14, y + s * 0.92, w=3, fill=fill)
    c.line(x + s * 0.86, y + s * 0.42, x + s * 0.86, y + s * 0.92, w=3, fill=fill)
    for fy in (0.55, 0.68, 0.81):
        c.line(x + s * 0.22, y + s * fy, x + s * 0.78, y + s * fy, w=3, fill=fill)


def icon_car(c, x, y, s, fill=BLACK):
    c.rrect(x + s * 0.04, y + s * 0.42, x + s * 0.96, y + s * 0.74,
            r=int(s * 0.10), outline=fill, w=3)
    c.line(x + s * 0.22, y + s * 0.42, x + s * 0.34, y + s * 0.20, w=3, fill=fill)
    c.line(x + s * 0.34, y + s * 0.20, x + s * 0.70, y + s * 0.20, w=3, fill=fill)
    c.line(x + s * 0.70, y + s * 0.20, x + s * 0.80, y + s * 0.42, w=3, fill=fill)
    c.ellipse(x + s * 0.16, y + s * 0.66, x + s * 0.36, y + s * 0.86, fill=WHITE,
              outline=fill, w=3)
    c.ellipse(x + s * 0.64, y + s * 0.66, x + s * 0.84, y + s * 0.86, fill=WHITE,
              outline=fill, w=3)


def icon_thermo(c, x, y, s, fill=BLACK):
    c.rrect(x + s * 0.40, y + s * 0.06, x + s * 0.60, y + s * 0.62,
            r=int(s * 0.10), outline=fill, w=3)
    c.ellipse(x + s * 0.30, y + s * 0.56, x + s * 0.70, y + s * 0.94,
              outline=fill, w=3)
    c.ellipse(x + s * 0.42, y + s * 0.68, x + s * 0.58, y + s * 0.84, fill=fill)


def icon_battlow(c, x, y, s, fill=BLACK):
    # horizontal battery, nearly empty
    c.rrect(x + s * 0.04, y + s * 0.28, x + s * 0.84, y + s * 0.72,
            r=int(s * 0.06), outline=fill, w=3)
    c.rrect(x + s * 0.84, y + s * 0.40, x + s * 0.94, y + s * 0.60,
            r=int(s * 0.03), fill=fill)
    c.rrect(x + s * 0.12, y + s * 0.38, x + s * 0.24, y + s * 0.62, r=1,
            fill=fill)


ICONS = {
    "sun": icon_sun, "moon": icon_moon, "cloud": icon_cloud,
    "battlow": icon_battlow,
    "trash": icon_trash, "recycle": icon_recycle, "shield": icon_shield,
    "lock": icon_lock, "garage": icon_garage, "car": icon_car,
    "thermo": icon_thermo,
}


# ------------------------------------------------------------------- layout

def draw_left_column(c):
    w = DATA["weather"]
    colc = LEFT_W / 2

    # clock
    f_clock = font(108, bold=True)
    f_ampm = font(28, bold=True)
    tw = c.text_w(DATA["time"], f_clock)
    aw = c.text_w(" " + DATA["ampm"], f_ampm)
    x0 = colc - (tw + aw) / 2
    c.text((x0, 18), DATA["time"], f_clock)
    c.text((x0 + tw, 96), " " + DATA["ampm"], f_ampm)

    # date
    c.text((colc, 148), DATA["date"], font(24), anchor="ma")

    c.line(MARGIN, 192, LEFT_W - MARGIN, 192, w=2)

    # weather: icon + big temp
    ICONS[w["icon"]](c, 28, 210, 78)
    c.text((124, 200), f"{w['temp']}°", font(58, bold=True))
    c.text((126, 264), f"{w['condition']} · feels {w['feels']}°",
           font(19))

    # forecast lines
    c.text((colc, 304), f"H {w['high']}°    L {w['low']}°",
           font(24, bold=True), anchor="ma")
    c.text((colc, 336),
           f"Rain {w['rain_pct']}%  ·  Wind {w['wind']} mph",
           font(19), anchor="ma")

    # trash / recycling badge
    t = DATA["trash"]
    if t["show"]:
        by0, by1 = 370, 412
        c.rrect(MARGIN, by0, LEFT_W - MARGIN, by1, r=8, fill=BLACK)
        label = "TRASH + RECYCLING" if t["recycling"] else "TRASH NIGHT"
        f_badge = font(17, bold=True)
        iw = 26
        icons = ["trash"] + (["recycle"] if t["recycling"] else [])
        total = len(icons) * (iw + 8) + c.text_w(label, f_badge)
        x = colc - total / 2
        for name in icons:
            ICONS[name](c, x, by0 + 8, iw, fill=WHITE)
            x += iw + 8
        c.text((x, (by0 + by1) / 2), label, f_badge, fill=WHITE, anchor="lm")


def draw_events(c):
    x0 = LEFT_W + 26
    x1 = W - MARGIN
    y = 16
    f_hdr = font(17, bold=True)
    f_title = font(22)
    f_time = font(17)
    f_badge = font(15, bold=True)

    for day in DATA["days"]:
        if y > H - STATUS_H - 60:
            break
        # section header
        c.text((x0, y), day["label"], f_hdr)
        hw = c.text_w(day["label"], f_hdr)
        c.line(x0 + hw + 12, y + 9, x1, y + 9, w=1)
        y += 30
        for ev in day["events"]:
            if y > H - STATUS_H - 44:
                break
            # person badge
            r = 13
            cy = y + 15
            c.ellipse(x0, cy - r, x0 + 2 * r, cy + r, fill=BLACK)
            c.text((x0 + r, cy), ev["who"], f_badge, fill=WHITE, anchor="mm")
            # time, right-aligned
            tw = c.text_w(ev["time"], f_time)
            c.text((x1 - tw, cy - 9), ev["time"], f_time)
            # title, truncated to fit
            title = ev["title"]
            max_w = (x1 - tw - 16) - (x0 + 2 * r + 12)
            while c.text_w(title, f_title) > max_w and len(title) > 1:
                title = title[:-2].rstrip() + "…"
            c.text((x0 + 2 * r + 12, cy - 12), title, f_title)
            y += 42
        y += 10


def draw_status_bar(c):
    y0 = H - STATUS_H
    c.line(0, y0, W, y0, w=2)
    items = list(DATA["status"])
    f_st = font(18)
    f_st_b = font(18, bold=True)
    iw = 26
    pad_x = 10

    # battery alert pill: worst offender by name, +N for the rest
    batts = DATA.get("battery_alerts", [])
    if batts:
        worst = batts[0]
        text = worst["name"]
        if worst["pct"] is not None:
            text += f" {worst['pct']}%"
        if len(batts) > 1:
            text += f"  +{len(batts) - 1}"
        items.append({"icon": "battlow", "text": text, "alert": True})

    def item_w(it):
        f = f_st_b if it["alert"] else f_st
        return iw + 8 + c.text_w(it["text"], f) + (2 * pad_x if it["alert"] else 0)

    # drop low-priority items until everything fits with sane gaps
    min_gap = 24
    while (sum(item_w(i) for i in items) + min_gap * (len(items) - 1)
           > W - 2 * MARGIN):
        drops = [i for i in items if i.get("droppable")]
        if not drops:
            break
        items.remove(min(drops, key=lambda i: i["droppable"]))

    widths = [item_w(it) for it in items]
    gap = (W - 2 * MARGIN - sum(widths)) / max(len(items) - 1, 1)
    x = MARGIN
    cy = y0 + STATUS_H / 2
    for it, wd in zip(items, widths):
        if it["alert"]:
            c.rrect(x, y0 + 10, x + wd, H - 10, r=8, fill=BLACK)
            ICONS[it["icon"]](c, x + pad_x, cy - iw / 2, iw, fill=WHITE)
            c.text((x + pad_x + iw + 8, cy), it["text"], f_st_b, fill=WHITE,
                   anchor="lm")
        else:
            ICONS[it["icon"]](c, x, cy - iw / 2, iw)
            c.text((x + iw + 8, cy), it["text"], f_st, anchor="lm")
        x += wd + gap


def main():
    import os
    c = Canvas()
    c.line(LEFT_W, 16, LEFT_W, H - STATUS_H - 12, w=2)
    draw_left_column(c)
    draw_events(c)
    draw_status_bar(c)

    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")
    os.makedirs(out, exist_ok=True)
    aa = c.img.resize((W, H), Image.LANCZOS)
    aa.save(os.path.join(out, "mockup_aa.png"))
    bw = aa.point(lambda p: 255 if p > 160 else 0).convert("1")
    bw.save(os.path.join(out, "mockup.png"))
    print("wrote", os.path.join(out, "mockup.png"))


if __name__ == "__main__":
    main()
