"""
DIMA VISION — generator de ilustrații pentru poveste (v2).
Lumina și vigneta se compun în numpy, ca haloul să fie moale.
"""

import math, random, os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageChops

W, H = 1500, 844
S = 2
OUT = '/mnt/user-data/outputs/dima-vision/assets/story'
CW, CH = W * S, H * S

random.seed(7)


# ------------------------------------------------------------------ bază
def new(size=None, color=(0, 0, 0, 0)):
    return Image.new('RGBA', size or (CW, CH), color)


def vgrad(stops):
    col = np.zeros((CH, 3), np.float32)
    stops = sorted(stops)
    ts = np.array([s[0] for s in stops], np.float32)
    cs = np.array([s[1] for s in stops], np.float32)
    y = np.linspace(0, 1, CH, dtype=np.float32)
    for k in range(3):
        col[:, k] = np.interp(y, ts, cs[:, k])
    arr = np.repeat(col[:, None, :], CW, axis=1)
    return Image.fromarray(arr.astype(np.uint8), 'RGB').convert('RGBA')


def glow(img, x, y, r, color, strength=1.0, falloff=2.0):
    """Halou radial moale, adăugat pe o subregiune."""
    x, y, r = float(x), float(y), float(r)
    x0, y0 = int(max(0, x - r * 1.7)), int(max(0, y - r * 1.7))
    x1, y1 = int(min(CW, x + r * 1.7)), int(min(CH, y + r * 1.7))
    if x1 <= x0 or y1 <= y0:
        return img
    box = img.crop((x0, y0, x1, y1)).convert('RGB')
    a = np.asarray(box, np.float32)
    yy, xx = np.mgrid[y0:y1, x0:x1].astype(np.float32)
    d = np.sqrt((xx - x) ** 2 + (yy - y) ** 2) / r
    f = np.exp(-(d ** falloff) * 2.4) * strength
    a += f[..., None] * np.array(color, np.float32)
    img.paste(Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), 'RGB'), (x0, y0))
    return img


def soft(im, r):
    return im.filter(ImageFilter.GaussianBlur(r))


def poly(img, pts, color, alpha=255, blur=0):
    lay = new(img.size)
    ImageDraw.Draw(lay).polygon([(float(a), float(b)) for a, b in pts], fill=tuple(color) + (alpha,))
    img.alpha_composite(soft(lay, blur) if blur else lay)
    return img


def rect(img, box, color, alpha=255, blur=0):
    return poly(img, [(box[0], box[1]), (box[2], box[1]), (box[2], box[3]), (box[0], box[3])], color, alpha, blur)


def ell(img, box, color=None, alpha=255, blur=0, outline=None, wdt=1):
    lay = new(img.size)
    d = ImageDraw.Draw(lay)
    b = [float(v) for v in box]
    if color:
        d.ellipse(b, fill=tuple(color) + (alpha,))
    if outline:
        d.ellipse(b, outline=tuple(outline) + (alpha,), width=int(max(1, wdt)))
    img.alpha_composite(soft(lay, blur) if blur else lay)
    return img


def line(img, pts, color, w=2, alpha=255, blur=0):
    lay = new(img.size)
    ImageDraw.Draw(lay).line([(float(a), float(b)) for a, b in pts],
                             fill=tuple(color) + (alpha,), width=int(max(1, w)), joint='curve')
    img.alpha_composite(soft(lay, blur) if blur else lay)
    return img


def ridge(y_base, amp, seed, n=8, tilt=0.0):
    rnd = random.Random(seed)
    ctrl = [rnd.uniform(-1, 1) for _ in range(n + 2)]
    pts = []
    for i in range(0, CW + 1, 6):
        t = i / CW
        f = 0.0
        for k in range(n + 2):
            u = t * n - k + 1
            if -1.5 < u < 1.5:
                f += ctrl[k] * math.exp(-u * u * 1.8)
        pts.append((i, y_base + f * amp + tilt * (t - 0.5) * amp * 2))
    return pts


def hill(img, pts, color, blur=0, alpha=255):
    return poly(img, list(pts) + [(CW, CH), (0, CH)], color, alpha, blur)


def band(img, y, h, color, alpha=40, blur=60):
    return rect(img, [0, y, CW, y + h], color, alpha, blur)


def rays(img, x, y, color, count=9, length=1200, spread=1.2, alpha=22, blur=70):
    lay = new(img.size)
    d = ImageDraw.Draw(lay)
    for i in range(count):
        a = -math.pi / 2 + (i / max(count - 1, 1) - 0.5) * spread + random.uniform(-.04, .04)
        w = random.uniform(12, 40) * S
        x2 = x + math.cos(a) * length * S
        y2 = y + math.sin(a) * length * S
        d.polygon([(x, y), (x2 - w, y2), (x2 + w, y2)], fill=tuple(color) + (int(alpha * random.uniform(.6, 1.2)),))
    img.alpha_composite(soft(lay, blur))
    return img


def motes(img, n, box, color, rmax=4, alpha=150, seed=1):
    rnd = random.Random(seed)
    lay = new(img.size)
    d = ImageDraw.Draw(lay)
    x0, y0, x1, y1 = box
    for _ in range(n):
        x = rnd.uniform(x0, x1); y = rnd.uniform(y0, y1)
        r = rnd.uniform(0.7, rmax) * S
        d.ellipse([x - r, y - r, x + r, y + r], fill=tuple(color) + (int(alpha * rnd.uniform(.2, 1)),))
    img.alpha_composite(soft(lay, 1.4 * S))
    return img


def finish(img, name, vig=0.55, gr=7, lift=0.94, sat=1.0):
    a = np.asarray(img.convert('RGB'), np.float32) / 255.0
    yy, xx = np.mgrid[0:CH, 0:CW].astype(np.float32)
    dx = (xx - CW / 2) / (CW / 2); dy = (yy - CH / 2) / (CH / 2)
    d = np.sqrt(dx * dx * 0.92 + dy * dy)
    v = 1.0 - np.clip((d - 0.55) / 0.85, 0, 1) ** 1.7 * vig
    a *= v[..., None]
    a = np.clip(a, 0, 1) ** lift
    if sat != 1.0:
        g = a.mean(axis=2, keepdims=True)
        a = np.clip(g + (a - g) * sat, 0, 1)
    im = Image.fromarray((a * 255).astype(np.uint8), 'RGB').resize((W, H), Image.LANCZOS)
    n = np.random.default_rng(3).normal(0, gr, (H, W, 1)).astype(np.float32)
    im = Image.fromarray(np.clip(np.asarray(im, np.float32) + n, 0, 255).astype(np.uint8), 'RGB')
    im.save(f'{OUT}/{name}.jpg', quality=80, optimize=True, progressive=True)
    return im


# ------------------------------------------------------------------ siluete
def house(img, x, ground, w, h, color, lit=None, roof=0.6):
    hw = w / 2
    poly(img, [(x - hw, ground), (x - hw, ground - h), (x, ground - h - h * roof),
               (x + hw, ground - h), (x + hw, ground)], color)
    if lit:
        ww, wh = w * 0.17, h * 0.3
        rect(img, [x - ww / 2, ground - h * 0.66, x + ww / 2, ground - h * 0.66 + wh], lit, 225)


def church(img, x, ground, s, color, lit):
    poly(img, [(x - 52 * s, ground), (x - 52 * s, ground - 66 * s), (x - 12 * s, ground - 92 * s),
               (x + 30 * s, ground - 66 * s), (x + 30 * s, ground)], color)
    poly(img, [(x - 52 * s, ground), (x - 52 * s, ground - 160 * s), (x - 22 * s, ground - 160 * s),
               (x - 22 * s, ground)], color)
    poly(img, [(x - 58 * s, ground - 158 * s), (x - 37 * s, ground - 250 * s), (x - 16 * s, ground - 158 * s)], color)
    rect(img, [x - 39 * s, ground - 282 * s, x - 35 * s, ground - 248 * s], color)
    rect(img, [x - 48 * s, ground - 272 * s, x - 26 * s, ground - 268 * s], color)
    rect(img, [x - 43 * s, ground - 128 * s, x - 31 * s, ground - 104 * s], lit, 210)
    rect(img, [x - 4 * s, ground - 50 * s, x + 12 * s, ground - 24 * s], lit, 190)


def horse(img, x, ground, s, color):
    """Cal din profil, spre stânga. Proporții: gât ~45%% și cap ~30%% din lungimea corpului."""
    def P(pts):
        poly(img, [(x + a * s, ground + b * s) for a, b in pts], color)

    P([(-130, -132), (-108, -158), (-96, -168), (-78, -152), (-56, -134), (-42, -120),
       (-16, -118), (20, -116), (56, -118), (80, -114), (88, -96), (78, -64), (30, -58),
       (-14, -60), (-40, -70), (-50, -88), (-58, -104), (-70, -124), (-86, -140),
       (-104, -140), (-122, -126)])
    P([(-98, -170), (-105, -187), (-88, -172)])
    P([(-88, -170), (-83, -185), (-77, -172)])
    P([(80, -114), (94, -106), (98, -56), (86, -26), (78, -60), (74, -100)])
    P([(-96, -168), (-80, -156), (-46, -124), (-56, -118), (-84, -148)])

    P([(-40, -92), (-20, -92), (-16, -56), (-12, 0), (-26, 0), (-30, -54)])
    P([(-24, -90), (-6, -88), (-2, -54), (2, 0), (-12, 0), (-16, -52)])
    P([(40, -104), (66, -108), (72, -66), (62, -44), (70, 0), (56, 0), (50, -46), (38, -72)])
    P([(56, -102), (76, -106), (82, -64), (74, -44), (82, 0), (68, 0), (62, -46)])


def cart(img, x, ground, s, color, cargo=None):
    """Căruță cu două roți; oiștea pleacă spre stânga, la înălțimea platformei."""
    bed = ground - 92 * s
    poly(img, [(x - 84 * s, bed), (x + 88 * s, bed - 5 * s),
               (x + 88 * s, bed + 14 * s), (x - 84 * s, bed + 19 * s)], color)
    poly(img, [(x - 84 * s, bed + 19 * s), (x + 88 * s, bed + 14 * s),
               (x + 84 * s, bed + 30 * s), (x - 80 * s, bed + 35 * s)], color)
    for i in range(8):
        px = x - 76 * s + i * 21 * s
        rect(img, [px, bed - 48 * s, px + 5 * s, bed], color)
    poly(img, [(x - 80 * s, bed - 54 * s), (x + 84 * s, bed - 59 * s),
               (x + 84 * s, bed - 47 * s), (x - 80 * s, bed - 42 * s)], color)
    poly(img, [(x - 80 * s, bed + 2 * s), (x - 260 * s, bed + 34 * s),
               (x - 260 * s, bed + 44 * s), (x - 80 * s, bed + 13 * s)], color)

    for cx, r in ((x + 54 * s, 62 * s), (x - 44 * s, 44 * s)):
        cy = ground - r
        ell(img, [cx - r, cy - r, cx + r, cy + r], None, outline=color, wdt=int(max(1, 7 * s)))
        ell(img, [cx - r * .84, cy - r * .84, cx + r * .84, cy + r * .84], None, outline=color, wdt=int(max(1, 3.4 * s)))
        for i in range(12):
            a = i * math.pi / 6
            line(img, [(cx + math.cos(a) * 9 * s, cy + math.sin(a) * 9 * s),
                       (cx + math.cos(a) * r * .86, cy + math.sin(a) * r * .86)], color, max(1, 3.4 * s))
        ell(img, [cx - 10 * s, cy - 10 * s, cx + 10 * s, cy + 10 * s], color)

    if cargo:
        poly(img, [(x - 62 * s, bed - 50 * s), (x + 54 * s, bed - 55 * s),
                   (x + 56 * s, bed - 2 * s), (x - 60 * s, bed + 3 * s)], cargo, alpha=70)
        line(img, [(x - 62 * s, bed - 50 * s), (x + 54 * s, bed - 55 * s)], cargo, 4 * s, 210)
        line(img, [(x - 62 * s, bed - 50 * s), (x - 60 * s, bed + 3 * s)], cargo, 3 * s, 150)


def seated(img, x, ground, s, color):
    """Vizitiu, așezat pe capră, aplecat spre stânga."""
    ell(img, [x - 16 * s, ground - 128 * s, x + 16 * s, ground - 96 * s], color)
    poly(img, [(x - 22 * s, ground - 100 * s), (x + 18 * s, ground - 104 * s),
               (x + 26 * s, ground - 34 * s), (x - 20 * s, ground - 30 * s)], color)
    poly(img, [(x - 20 * s, ground - 38 * s), (x + 22 * s, ground - 38 * s),
               (x - 46 * s, ground - 10 * s), (x - 52 * s, ground - 26 * s)], color)
    poly(img, [(x - 16 * s, ground - 92 * s), (x - 2 * s, ground - 96 * s),
               (x - 58 * s, ground - 54 * s), (x - 68 * s, ground - 64 * s)], color)
    poly(img, [(x - 24 * s, ground - 126 * s), (x + 20 * s, ground - 122 * s),
               (x + 18 * s, ground - 116 * s), (x - 24 * s, ground - 120 * s)], color)
    poly(img, [(x - 15 * s, ground - 138 * s), (x + 13 * s, ground - 136 * s),
               (x + 14 * s, ground - 124 * s), (x - 16 * s, ground - 126 * s)], color)


def figure(img, x, ground, s, color, lean=0.0, reach=1.0):
    hx = x - lean * 30 * s
    ell(img, [hx - 17 * s, ground - 186 * s, hx + 17 * s, ground - 152 * s], color)
    poly(img, [(hx - 12 * s, ground - 158 * s), (hx + 10 * s, ground - 156 * s),
               (x + 12 * s, ground - 148 * s), (x - 16 * s, ground - 148 * s)], color)
    poly(img, [(x - 30 * s, ground - 150 * s), (hx + 16 * s, ground - 154 * s),
               (x + 30 * s, ground - 66 * s), (x - 30 * s, ground - 66 * s)], color)
    poly(img, [(x - 26 * s, ground - 68 * s), (x + 28 * s, ground - 68 * s),
               (x + 22 * s, ground), (x + 8 * s, ground), (x + 5 * s, ground - 44 * s),
               (x - 8 * s, ground), (x - 26 * s, ground)], color)
    poly(img, [(x - 20 * s, ground - 142 * s), (x - 4 * s, ground - 146 * s),
               (x - 56 * s * reach, ground - 86 * s), (x - 70 * s * reach, ground - 96 * s)], color)
    poly(img, [(x + 4 * s, ground - 142 * s), (x + 18 * s, ground - 140 * s),
               (x - 30 * s * reach, ground - 78 * s), (x - 44 * s * reach, ground - 90 * s)], color, alpha=210)


def sheet_of_glass(img, pts, tint, edge, alpha=42, edge_a=190, w=3):
    poly(img, pts, tint, alpha)

    for i in range(len(pts)):
        a = pts[i]; b = pts[(i + 1) % len(pts)]
        line(img, [a, b], edge, w * S, edge_a if i in (0, 3) else int(edge_a * .55))


# ------------------------------------------------------------------ scene
def sc01_sat():
    img = vgrad([(0.00, (30, 22, 15)), (0.30, (74, 48, 26)), (0.55, (148, 98, 46)),
                 (0.66, (214, 152, 78)), (0.72, (238, 186, 108)), (0.78, (150, 104, 56)), (1.0, (34, 24, 15))])
    sx, sy = CW * .66, CH * .655
    img = glow(img, sx, sy, 520 * S, (140, 96, 40), .85, 1.7)
    img = glow(img, sx, sy, 150 * S, (200, 160, 92), 1.0, 2.4)
    ell(img, [sx - 62 * S, sy - 62 * S, sx + 62 * S, sy + 62 * S], (255, 236, 196), 235, blur=10 * S)
    img = rays(img, sx, sy, (255, 214, 150), 12, 800, 1.9, 12, 90)

    img = hill(img, ridge(CH * .585, 34 * S, 3, 6, .25), (118, 84, 50), blur=6 * S)
    band(img, CH * .575, 70 * S, (236, 192, 132), 52, 50 * S)
    img = hill(img, ridge(CH * .645, 30 * S, 11, 7, -.2), (78, 55, 33), blur=3 * S)
    band(img, CH * .645, 66 * S, (226, 178, 118), 44, 42 * S)
    img = hill(img, ridge(CH * .705, 24 * S, 19, 8, .15), (48, 34, 20))

    ground = CH * .775
    dark = (22, 15, 9)
    church(img, CW * .485, ground, 0.62 * S, dark, (255, 206, 138))
    for hx, hw, hh, lit in [(.27, 74, 50, 1), (.335, 60, 42, 0), (.385, 54, 38, 1), (.205, 56, 38, 0),
                            (.575, 66, 46, 1), (.635, 56, 40, 0), (.70, 78, 52, 1), (.775, 58, 40, 0),
                            (.845, 50, 34, 1)]:
        house(img, CW * hx, ground + 4 * S, hw * S, hh * S, dark, (255, 202, 132) if lit else None)
    for hx in (.30, .45, .62, .74):
        tx = CW * hx
        poly(img, [(tx - 5 * S, ground), (tx - 3 * S, ground - 96 * S), (tx + 3 * S, ground - 96 * S), (tx + 5 * S, ground)], dark)
        ell(img, [tx - 16 * S, ground - 128 * S, tx + 16 * S, ground - 76 * S], dark)

    img = hill(img, ridge(CH * .80, 16 * S, 27, 7), (26, 18, 11))
    band(img, CH * .78, 60 * S, (230, 180, 120), 30, 46 * S)
    img = hill(img, ridge(CH * .875, 20 * S, 31, 5, .3), (14, 10, 6))

    tx = CW * .115
    poly(img, [(tx - 13 * S, CH), (tx - 7 * S, CH * .60), (tx + 7 * S, CH * .60), (tx + 13 * S, CH)], (10, 7, 4))
    for a, r, rr in [(-1.9, 120, 78), (-1.2, 150, 92), (-.5, 120, 70), (-2.6, 110, 64), (-1.55, 60, 96)]:
        cx2 = tx + math.cos(a) * r * S
        cy2 = CH * .60 + math.sin(a) * r * S * .8
        ell(img, [cx2 - rr * S, cy2 - rr * .72 * S, cx2 + rr * S, cy2 + rr * .72 * S], (10, 7, 4))
    for i in range(4):
        line(img, [(tx, CH * .60 + 20 * S), (tx + math.cos(-2.4 + i * .55) * 130 * S,
                                             CH * .60 + math.sin(-2.4 + i * .55) * 110 * S)], (10, 7, 4), 7 * S)

    for _ in range(9):
        bx = random.uniform(.34, .90) * CW; by = random.uniform(.12, .30) * CH
        sz = random.uniform(6, 13) * S
        line(img, [(bx - sz, by), (bx - sz * .3, by - sz * .5), (bx + sz * .3, by - sz * .45), (bx + sz, by + sz * .1)],
             (34, 23, 14), 2.6 * S, 190)

    img = motes(img, 150, (0, CH * .35, CW, CH), (255, 216, 154), 2.6, 85, 5)
    return finish(img, '01-sat', .5, 7, .92)


def sc02_atelier_vechi():
    img = vgrad([(0, (26, 19, 12)), (.5, (46, 33, 20)), (1, (18, 13, 8))])
    wx0, wy0, wx1, wy1 = CW * .55, CH * .07, CW * .97, CH * .60
    rect(img, [wx0, wy0, wx1, wy1], (236, 196, 132))
    img = glow(img, (wx0 + wx1) / 2, (wy0 + wy1) / 2, 420 * S, (120, 88, 44), .9, 1.6)
    for i in range(1, 3):
        rect(img, [wx0 + (wx1 - wx0) * i / 3 - 6 * S, wy0, wx0 + (wx1 - wx0) * i / 3 + 6 * S, wy1], (30, 21, 13))
    rect(img, [wx0, (wy0 + wy1) * .52 - 6 * S, wx1, (wy0 + wy1) * .52 + 6 * S], (30, 21, 13))
    rect(img, [wx0 - 14 * S, wy0 - 14 * S, wx1, wy0], (34, 24, 15))
    rect(img, [wx0 - 14 * S, wy0, wx0, wy1 + 14 * S], (34, 24, 15))
    rect(img, [wx0 - 14 * S, wy1, wx1, wy1 + 14 * S], (34, 24, 15))
    img = rays(img, int((wx0 + wx1) / 2), int(wy1), (255, 216, 152), 9, 700, 1.4, 20, 80)

    ground = CH * .74
    rect(img, [0, ground + 26 * S, CW, CH], (20, 14, 9))
    rect(img, [CW * .02, ground, CW * .98, ground + 26 * S], (86, 60, 32))
    line(img, [(CW * .02, ground), (CW * .98, ground)], (188, 140, 78), 4 * S, 170)
    for lx in (CW * .12, CW * .82):
        rect(img, [lx, ground + 26 * S, lx + 30 * S, CH * .97], (52, 36, 20))

    gp = [(CW * .09, ground - 16 * S), (CW * .74, ground - 58 * S),
          (CW * .80, ground - 8 * S), (CW * .15, ground + 12 * S)]
    sheet_of_glass(img, gp, (196, 214, 200), (255, 246, 214), 46, 210, 3)
    line(img, [(CW * .14, ground - 24 * S), (CW * .70, ground - 56 * S)], (255, 250, 224), 2.6 * S, 130)
    line(img, [(CW * .12, ground - 6 * S), (CW * .76, ground - 44 * S)], (255, 244, 210), 2 * S, 80)

    line(img, [(CW * .16, ground - 42 * S), (CW * .62, ground - 70 * S)], (120, 86, 46), 14 * S)
    line(img, [(CW * .16, ground - 48 * S), (CW * .62, ground - 76 * S)], (170, 126, 70), 4 * S, 200)

    tool_c = (60, 42, 23)
    rail = CH * .155
    line(img, [(CW * .02, rail), (CW * .40, rail)], tool_c, 5 * S, 220)
    # ciocan
    hx0 = CW * .05
    rect(img, [hx0 - 5 * S, rail, hx0 + 5 * S, rail + 120 * S], tool_c)
    poly(img, [(hx0 - 30 * S, rail + 116 * S), (hx0 + 26 * S, rail + 112 * S),
               (hx0 + 26 * S, rail + 142 * S), (hx0 - 30 * S, rail + 146 * S)], tool_c)
    # ferăstrău
    sx0 = CW * .115
    rect(img, [sx0 - 16 * S, rail, sx0 + 16 * S, rail + 46 * S], tool_c)
    poly(img, [(sx0 - 14 * S, rail + 46 * S), (sx0 + 14 * S, rail + 46 * S),
               (sx0 + 46 * S, rail + 188 * S), (sx0 + 30 * S, rail + 190 * S)], tool_c)
    # echer
    ex0 = CW * .185
    rect(img, [ex0 - 6 * S, rail, ex0 + 6 * S, rail + 168 * S], tool_c)
    rect(img, [ex0 - 6 * S, rail + 156 * S, ex0 + 96 * S, rail + 168 * S], tool_c)
    # clește
    px0 = CW * .265
    poly(img, [(px0 - 6 * S, rail), (px0 + 6 * S, rail), (px0 + 30 * S, rail + 150 * S),
               (px0 + 18 * S, rail + 152 * S)], tool_c)
    poly(img, [(px0 - 6 * S, rail), (px0 + 6 * S, rail), (px0 - 16 * S, rail + 150 * S),
               (px0 - 28 * S, rail + 148 * S)], tool_c)
    # riglă lungă
    rect(img, [CW * .33, rail, CW * .345, rail + 250 * S], tool_c)
    rect(img, [CW * .365, rail, CW * .375, rail + 210 * S], tool_c)

    poly(img, [(CW * .40, ground - 150 * S), (CW * .445, ground - 158 * S),
               (CW * .475, ground - 66 * S), (CW * .43, ground - 58 * S)], (40, 28, 16))
    img = glow(img, CW * .45, ground - 56 * S, 90 * S, (150, 108, 52), .8, 2.2)

    img = motes(img, 300, (CW * .25, CH * .06, CW, ground), (255, 222, 166), 4.4, 165, 9)
    return finish(img, '02-atelier-vechi', .55, 7, .93)


def sc03_caruta():
    """Calul și căruța, în lumina de dimineață."""
    img = vgrad([(0, (32, 22, 14)), (.32, (86, 56, 28)), (.56, (168, 114, 54)),
                 (.66, (232, 172, 96)), (.73, (196, 138, 72)), (1, (40, 27, 16))])
    sx, sy = CW * .105, CH * .60
    img = glow(img, sx, sy, 600 * S, (144, 96, 42), .95, 1.7)
    ell(img, [sx - 80 * S, sy - 80 * S, sx + 80 * S, sy + 80 * S], (255, 234, 190), 225, blur=16 * S)
    img = rays(img, sx, sy, (255, 212, 148), 11, 1000, 2.1, 13, 95)

    img = hill(img, ridge(CH * .575, 32 * S, 41, 6, .2), (110, 76, 44), blur=6 * S)
    band(img, CH * .575, 80 * S, (238, 194, 134), 54, 55 * S)
    img = hill(img, ridge(CH * .655, 24 * S, 47, 7, -.15), (64, 44, 26), blur=2 * S)
    band(img, CH * .655, 60 * S, (226, 178, 118), 34, 40 * S)

    ground = CH * .845
    img = hill(img, ridge(CH * .735, 14 * S, 53, 9), (34, 23, 14))
    dark = (14, 10, 6)
    sc = 1.78 * S
    hx, cx0 = CW * .235, CW * .545

    cart(img, cx0, ground, sc * 1.06, dark, (255, 232, 182))
    horse(img, hx, ground, sc, dark)
    bed = ground - 92 * sc * 1.06
    seated(img, cx0 - 34 * sc, bed + 6 * S, 1.05 * S, dark)

    rect(img, [0, ground - 4 * S, CW, ground + 12 * S], (48, 33, 18), 200, blur=6 * S)
    for oy, aa in ((16, 120), (34, 80), (58, 50)):
        line(img, [(0, ground + oy * S), (CW, ground + oy * S - 10 * S)], (120, 86, 46), 3 * S, aa, blur=3 * S)
    for i in range(26):
        gx = random.uniform(0, CW); gy = ground + random.uniform(6, 60) * S
        for k in range(3):
            line(img, [(gx, gy), (gx + random.uniform(-9, 9) * S, gy - random.uniform(10, 22) * S)],
                 (58, 40, 22), 2 * S, 200)
    img = motes(img, 200, (CW * .2, CH * .60, CW, CH * .96), (255, 214, 156), 2.8, 95, 11)
    rect(img, [0, CH * .90, CW, CH], (12, 8, 5), 190, blur=40 * S)
    return finish(img, '03-caruta', .5, 7, .92)


def sc04_drum():
    img = vgrad([(0, (30, 21, 13)), (.34, (82, 54, 27)), (.56, (160, 110, 54)),
                 (.645, (226, 168, 96)), (.70, (168, 118, 62)), (1, (26, 18, 11))])
    sx, sy = CW * .52, CH * .625
    img = glow(img, sx, sy, 480 * S, (132, 90, 40), .85, 1.7)
    ell(img, [sx - 56 * S, sy - 56 * S, sx + 56 * S, sy + 56 * S], (255, 232, 186), 210, blur=12 * S)

    img = hill(img, ridge(CH * .585, 40 * S, 61, 6, -.3), (114, 80, 46), blur=8 * S)
    band(img, CH * .585, 76 * S, (238, 194, 134), 56, 52 * S)
    img = hill(img, ridge(CH * .655, 26 * S, 67, 7, .2), (66, 46, 26), blur=3 * S)

    horizon = CH * .665
    poly(img, [(CW * .452, horizon), (CW * .548, horizon), (CW * 1.30, CH), (CW * -.30, CH)], (128, 92, 50))
    poly(img, [(CW * .466, horizon), (CW * .534, horizon), (CW * 1.02, CH), (CW * -.02, CH)], (158, 118, 66), 150)
    for sgn in (-1, 1):
        poly(img, [(CW * (.5 + sgn * .012), horizon + 3 * S), (CW * (.5 + sgn * .020), horizon + 3 * S),
                   (CW * (.5 + sgn * .30), CH), (CW * (.5 + sgn * .40), CH)], (96, 66, 34), 190)
    band(img, horizon - 10 * S, 40 * S, (240, 198, 140), 60, 30 * S)

    for i in range(15):
        t = (i / 14) ** 2.2
        y = horizon + (CH - horizon) * t
        hgt = 10 * S + 150 * S * t
        for sgn in (-1, 1):
            x = CW * .5 + sgn * (CW * .055 + CW * .78 * t)
            rect(img, [x - (2 + 8 * t) * S, y - hgt, x + (2 + 8 * t) * S, y], (26, 18, 11))
            if i < 14:
                t2 = ((i + 1) / 14) ** 2.2
                y2 = horizon + (CH - horizon) * t2
                x2 = CW * .5 + sgn * (CW * .055 + CW * .78 * t2)
                line(img, [(x, y - hgt * .6), (x2, y2 - (10 * S + 150 * S * t2) * .6)], (26, 18, 11), (1.6 + 6 * t) * S, 210)

    horse(img, CW * .4735, horizon + 26 * S, .085 * S, (24, 16, 10))
    cart(img, CW * .513, horizon + 26 * S, .085 * S, (24, 16, 10), None)
    img = glow(img, CW * .495, horizon + 14 * S, 90 * S, (120, 82, 36), .5, 2.0)

    img = motes(img, 150, (0, CH * .5, CW, CH), (255, 212, 148), 2.8, 85, 13)
    return finish(img, '04-drum', .5, 7, .93)


def sc05_ani():
    """Foile de sticlă, stivuite; fiecare an, încă o foaie."""
    img = vgrad([(0, (26, 19, 12)), (.55, (42, 30, 19)), (1, (16, 11, 7))])
    rect(img, [CW * .02, CH * .06, CW * .215, CH * .58], (240, 202, 142))
    img = glow(img, CW * .115, CH * .32, 470 * S, (130, 94, 46), .95, 1.6)
    rect(img, [CW * .112, CH * .06, CW * .124, CH * .58], (30, 21, 13))
    rect(img, [CW * .02, CH * .30, CW * .215, CH * .315], (30, 21, 13))
    img = rays(img, int(CW * .125), int(CH * .40), (255, 214, 152), 9, 1100, 1.0, 20, 90)

    ground = CH * .875
    rect(img, [0, ground, CW, CH], (24, 17, 11))
    rect(img, [0, ground - 12 * S, CW, ground + 16 * S], (80, 56, 30))
    line(img, [(0, ground - 12 * S), (CW, ground - 12 * S)], (150, 110, 60), 3 * S, 150)
    for rx in (CW * .285, CW * .97):
        rect(img, [rx - 10 * S, CH * .15, rx + 10 * S, ground], (56, 39, 22))
    rect(img, [CW * .275, CH * .175, CW * .98, CH * .193], (56, 39, 22))

    # foile se suprapun: se vede doar câte o fâșie din fiecare
    n = 15
    for i in range(n):
        t = i / (n - 1)
        x = CW * (.30 + t * .58)
        wdt = CW * .20
        lean = (46 - 40 * t) * S
        top = CH * (.245 + .014 * math.sin(i * 1.9))
        poly(img, [(x + lean, top), (x + lean + wdt, top + 6 * S),
                   (x + wdt, ground - 12 * S), (x, ground - 12 * S)],
             (172, 196, 184), int(22 + 16 * (1 - t)))
        line(img, [(x + lean, top), (x + lean + wdt, top + 6 * S)], (255, 250, 226), 3.6 * S, int(200 - 90 * t))
        line(img, [(x + lean, top), (x, ground - 12 * S)], (255, 248, 220), 3 * S, int(225 - 105 * t))

    img = glow(img, CW * .36, CH * .55, 340 * S, (132, 100, 52), .55, 2.0)
    line(img, [(CW * .30 + 46 * S, CH * .245), (CW * .30, ground - 12 * S)], (255, 252, 232), 6 * S, 245, blur=2 * S)
    rect(img, [CW * .28, CH * .2, CW * .40, ground], (255, 226, 170), 26, blur=50 * S)

    img = motes(img, 340, (CW * .03, CH * .06, CW * .97, ground), (255, 224, 170), 4.6, 175, 17)
    return finish(img, '05-ani', .55, 7, .93)


def sc06_generatii():
    """Doi oameni la aceeași masă de lucru."""
    img = vgrad([(0, (28, 20, 13)), (.5, (46, 33, 21)), (1, (16, 12, 8))])
    rect(img, [CW * .30, CH * .04, CW * .72, CH * .40], (240, 202, 142))
    img = glow(img, CW * .51, CH * .22, 500 * S, (130, 94, 46), 1.0, 1.6)
    for i in range(1, 3):
        x = CW * (.30 + .42 * i / 3)
        rect(img, [x - 7 * S, CH * .04, x + 7 * S, CH * .40], (30, 21, 13))
    rect(img, [CW * .30, CH * .21, CW * .72, CH * .225], (30, 21, 13))
    rect(img, [CW * .285, CH * .025, CW * .735, CH * .04], (38, 27, 17))
    img = rays(img, int(CW * .51), int(CH * .40), (255, 214, 152), 10, 800, 1.5, 17, 80)

    ground = CH * .865
    rect(img, [0, ground + 22 * S, CW, CH], (18, 13, 8))
    rect(img, [CW * .02, ground, CW * .98, ground + 22 * S], (92, 65, 35))
    line(img, [(CW * .02, ground), (CW * .98, ground)], (192, 142, 78), 4 * S, 170)
    for lx in (CW * .09, CW * .86):
        rect(img, [lx, ground + 22 * S, lx + 34 * S, CH], (54, 38, 21))

    dark = (13, 9, 6)
    figure(img, CW * .38, CH * 1.06, 2.05 * S, dark, lean=.30, reach=.95)
    figure(img, CW * .69, CH * 1.04, 1.90 * S, dark, lean=.12, reach=.60)

    rect(img, [0, ground + 22 * S, CW, CH], (18, 13, 8))
    rect(img, [CW * .02, ground, CW * .98, ground + 22 * S], (92, 65, 35))
    line(img, [(CW * .02, ground), (CW * .98, ground)], (192, 142, 78), 4 * S, 170)
    sheet_of_glass(img, [(CW * .16, ground - 14 * S), (CW * .86, ground - 14 * S),
                         (CW * .82, ground + 2 * S), (CW * .20, ground + 2 * S)],
                   (200, 218, 204), (255, 250, 224), 62, 220, 4)

    img = motes(img, 260, (CW * .04, CH * .04, CW * .96, ground), (255, 222, 168), 4.6, 165, 19)
    return finish(img, '06-generatii', .55, 7, .93)


def sc07_maiestrie():
    """Prim-plan: muchia sticlei și tăietura trasă cu mâna."""
    img = vgrad([(0, (24, 17, 11)), (.42, (48, 34, 20)), (1, (14, 10, 6))])
    img = glow(img, CW * .22, CH * .14, 560 * S, (120, 86, 40), .85, 1.8)

    base = CH * .60
    dyy = -150 * S

    def onl(t, off=0):
        return (-CW * .08 + t * CW * 1.16, base + t * dyy + off)

    # corpul sticlei
    poly(img, [onl(0, -170 * S), onl(1, -170 * S), onl(1, 250 * S), onl(0, 250 * S)], (150, 176, 166), 26)
    # muchia de sus, cu bizou
    line(img, [onl(0, -170 * S), onl(1, -170 * S)], (255, 252, 232), 6 * S, 245)
    line(img, [onl(0, -158 * S), onl(1, -158 * S)], (255, 240, 200), 3 * S, 150)
    line(img, [onl(0, -170 * S), onl(1, -170 * S)], (255, 226, 178), 30 * S, 60, blur=16 * S)
    for off, a, w in ((-96, 80, 3), (-40, 52, 2.4), (60, 40, 2.2), (150, 30, 2)):
        line(img, [onl(0, off * S), onl(1, off * S)], (255, 250, 226), w * S, a)
    line(img, [onl(0, 250 * S), onl(1, 250 * S)], (222, 224, 198), 3 * S, 110)

    # linia tăiată
    line(img, [onl(0, 20 * S), onl(1, 20 * S)], (255, 252, 236), 3.6 * S, 235)
    line(img, [onl(0, 20 * S), onl(1, 20 * S)], (255, 230, 184), 22 * S, 62, blur=12 * S)

    # unealta: mâner de lemn, manșon de alamă, vârf de diamant
    tip = onl(.52, 20 * S)
    ang = math.radians(-72)
    dx, dy = math.cos(ang), math.sin(ang)
    def at(d, o=0):
        return (tip[0] + dx * d * S - dy * o * S, tip[1] + dy * d * S + dx * o * S)
    poly(img, [at(66, -26), at(66, 26), at(320, 38), at(320, -38)], (46, 32, 19))       # mâner
    poly(img, [at(320, -38), at(320, 38), at(384, 30), at(384, -30)], (62, 43, 25))
    poly(img, [at(38, -19), at(38, 19), at(66, 26), at(66, -26)], (150, 112, 52))        # alamă
    poly(img, [at(8, -10), at(8, 10), at(38, 19), at(38, -19)], (112, 84, 40))
    poly(img, [at(0, 0), at(13, -9), at(13, 9)], (244, 240, 220))                        # vârf
    for d in (120, 180, 240):
        line(img, [at(d, -26), at(d, 26)], (26, 18, 10), 3.4 * S, 150)
    img = glow(img, tip[0], tip[1], 130 * S, (180, 132, 62), 1.0, 2.1)
    ell(img, [tip[0] - 8 * S, tip[1] - 8 * S, tip[0] + 8 * S, tip[1] + 8 * S], (255, 250, 226), 250)

    # praf de sticlă pe linia tăiată
    for _ in range(90):
        t = random.random()
        x, y = onl(t, 20 * S)
        x += random.uniform(-6, 6) * S
        y += random.uniform(-9, 9) * S
        r = random.uniform(1, 3.6) * S
        ell(img, [x - r, y - r, x + r, y + r], (255, 246, 216), int(random.uniform(90, 240)))

    img = motes(img, 200, (0, 0, CW, CH), (255, 224, 168), 3.6, 130, 23)
    return finish(img, '07-maiestrie', .5, 7, .93)


def sc08_unelte():
    g = CH * .72
    left = vgrad([(0, (28, 20, 13)), (.5, (58, 40, 23)), (1, (18, 13, 8))])
    left = glow(left, CW * .16, CH * .20, 430 * S, (122, 86, 40), .85, 1.7)
    rect(left, [0, g + 22 * S, CW, CH], (20, 14, 9))
    rect(left, [0, g, CW, g + 22 * S], (78, 55, 30))
    poly(left, [(-CW * .05, g - 14 * S), (CW * .60, g - 52 * S), (CW * .60, g - 4 * S), (-CW * .05, g + 12 * S)],
         (192, 210, 196), 48)
    line(left, [(-CW * .05, g - 14 * S), (CW * .60, g - 52 * S)], (255, 248, 218), 4 * S, 210)
    cx, cy = CW * .26, g - 66 * S
    poly(left, [(cx - 22 * S, cy), (cx + 18 * S, cy - 12 * S), (cx + 116 * S, cy - 226 * S), (cx + 72 * S, cy - 212 * S)],
         (32, 22, 13))
    poly(left, [(cx - 14 * S, cy + 2 * S), (cx + 12 * S, cy - 8 * S), (cx - 3 * S, cy + 30 * S)], (60, 42, 24))
    left = glow(left, cx, cy + 24 * S, 100 * S, (168, 120, 56), .9, 2.2)
    left = motes(left, 140, (0, CH * .1, CW * .7, CH * .9), (255, 220, 162), 4, 150, 29)

    right = vgrad([(0, (12, 17, 21)), (.5, (26, 38, 47)), (1, (9, 13, 17))])
    right = glow(right, CW * .80, CH * .18, 460 * S, (66, 104, 132), .8, 1.7)
    rect(right, [0, g + 22 * S, CW, CH], (12, 16, 20))
    rect(right, [0, g, CW, g + 22 * S], (44, 58, 70))
    poly(right, [(CW * .36, g - 52 * S), (CW * 1.05, g - 14 * S), (CW * 1.05, g + 12 * S), (CW * .36, g - 4 * S)],
         (168, 202, 222), 48)
    line(right, [(CW * .36, g - 52 * S), (CW * 1.05, g - 14 * S)], (232, 248, 255), 4 * S, 215)
    mx = CW * .74
    rect(right, [mx - 110 * S, CH * .08, mx + 110 * S, CH * .32], (34, 46, 56))
    rect(right, [mx - 110 * S, CH * .08, mx + 110 * S, CH * .125], (62, 84, 100))
    rect(right, [mx - 34 * S, CH * .32, mx + 34 * S, CH * .46], (48, 64, 78))
    poly(right, [(mx - 13 * S, CH * .46), (mx + 13 * S, CH * .46), (mx + 4 * S, g - 62 * S), (mx - 4 * S, g - 62 * S)],
         (86, 112, 132))
    right = glow(right, mx, g - 54 * S, 150 * S, (120, 168, 206), 1.0, 2.0)
    for i in range(34):
        a = random.uniform(.2, math.pi - .2); r = random.uniform(16, 120) * S
        line(right, [(mx, g - 54 * S), (mx - math.cos(a) * r, g - 54 * S - math.sin(a) * r * .5)],
             (214, 240, 255), 1.6 * S, 150)

    img = new(color=(0, 0, 0, 255))
    img.alpha_composite(left)
    mask = Image.new('L', (CW, CH), 0)
    ImageDraw.Draw(mask).polygon([(CW * .545, 0), (CW * 2, 0), (CW * 2, CH), (CW * .455, CH)], fill=255)
    img.paste(right, (0, 0), mask)

    edge = new()
    d = ImageDraw.Draw(edge)
    for wd, al in ((14, 34), (6, 90), (2.4, 190), (1, 255)):
        d.polygon([(CW * .545 - wd * S, 0), (CW * .545 + wd * S, 0),
                   (CW * .455 + wd * S, CH), (CW * .455 - wd * S, CH)], fill=(255, 255, 255, al))
    img.alpha_composite(soft(edge, 2.4 * S))
    return finish(img, '08-unelte', .5, 7, .93)


def sc09_cnc():
    img = vgrad([(0, (12, 17, 21)), (.42, (26, 38, 48)), (1, (10, 14, 18))])
    for i in range(4):
        lx = CW * (.17 + i * .22)
        img = glow(img, lx, CH * .085, 260 * S, (58, 92, 118), .85, 1.8)
        rect(img, [lx - 88 * S, CH * .055, lx + 88 * S, CH * .082], (214, 238, 252), 240)

    ground = CH * .735
    rect(img, [0, ground + 30 * S, CW, CH], (13, 18, 23))
    rect(img, [0, ground + 30 * S, CW, ground + 48 * S], (42, 58, 70))
    rect(img, [CW * .02, ground - 18 * S, CW * .98, ground + 34 * S], (26, 36, 45))
    for i in range(15):
        rx = CW * (.05 + i * .064)
        ell(img, [rx - 30 * S, ground - 24 * S, rx + 30 * S, ground + 26 * S], (34, 48, 60))
        ell(img, [rx - 30 * S, ground - 24 * S, rx + 30 * S, ground + 26 * S], None, outline=(96, 128, 150), wdt=int(3 * S))
        line(img, [(rx - 20 * S, ground - 14 * S), (rx + 2 * S, ground - 20 * S)], (170, 208, 232), 3 * S, 170)

    poly(img, [(CW * .03, ground - 40 * S), (CW * .97, ground - 40 * S),
               (CW * .97, ground - 28 * S), (CW * .03, ground - 28 * S)], (166, 206, 228), 90)
    line(img, [(CW * .03, ground - 40 * S), (CW * .97, ground - 40 * S)], (232, 248, 255), 4 * S, 230)
    line(img, [(CW * .03, ground - 28 * S), (CW * .97, ground - 28 * S)], (160, 196, 220), 2.4 * S, 140)

    rect(img, [CW * .05, CH * .20, CW * .95, CH * .29], (30, 42, 52))
    rect(img, [CW * .05, CH * .20, CW * .95, CH * .215], (74, 100, 118))
    rect(img, [CW * .05, CH * .29, CW * .10, ground - 40 * S], (24, 34, 42))
    rect(img, [CW * .90, CH * .29, CW * .95, ground - 40 * S], (24, 34, 42))
    for i in range(9):
        x = CW * (.12 + i * .092)
        line(img, [(x, CH * .29), (x, CH * .33)], (60, 82, 98), 4 * S, 200)

    mx = CW * .44
    rect(img, [mx - 74 * S, CH * .285, mx + 74 * S, CH * .43], (40, 54, 66))
    rect(img, [mx - 74 * S, CH * .285, mx + 74 * S, CH * .305], (78, 104, 124))
    rect(img, [mx - 26 * S, CH * .43, mx + 26 * S, CH * .55], (52, 70, 84))
    poly(img, [(mx - 10 * S, CH * .55), (mx + 10 * S, CH * .55), (mx + 3 * S, ground - 46 * S), (mx - 3 * S, ground - 46 * S)],
         (96, 124, 146))
    img = glow(img, mx, ground - 42 * S, 170 * S, (130, 178, 214), 1.05, 2.0)
    for i in range(40):
        a = random.uniform(.12, math.pi - .12); r = random.uniform(18, 140) * S
        line(img, [(mx, ground - 42 * S), (mx - math.cos(a) * r, ground - 42 * S - math.sin(a) * r * .5)],
             (218, 242, 255), 1.6 * S, 145)
    line(img, [(CW * .05, ground - 34 * S), (mx, ground - 34 * S)], (236, 250, 255), 2.6 * S, 190)

    img = motes(img, 130, (0, CH * .1, CW, ground), (186, 222, 246), 3, 90, 31)
    return finish(img, '09-cnc', .5, 6, .93)


def sc10_proiect():
    img = vgrad([(0, (12, 16, 20)), (.5, (24, 33, 41)), (1, (10, 14, 18))])
    desk = CH * .80
    rect(img, [0, desk, CW, CH], (22, 29, 36))
    rect(img, [0, desk, CW, desk + 10 * S], (62, 82, 98))

    sx0, sx1, sy0, sy1 = CW * .255, CW * .745, CH * .155, CH * .625
    rect(img, [sx0 - 12 * S, sy0 - 12 * S, sx1 + 12 * S, sy1 + 12 * S], (44, 58, 70))
    rect(img, [sx0, sy0, sx1, sy1], (16, 26, 35))
    img = glow(img, (sx0 + sx1) / 2, (sy0 + sy1) / 2, 400 * S, (44, 78, 104), .95, 1.7)
    poly(img, [(sx0 - 34 * S, sy1 + 12 * S), (sx1 + 34 * S, sy1 + 12 * S),
               (sx1 + 108 * S, desk), (sx0 - 108 * S, desk)], (38, 50, 62))
    rect(img, [sx0 - 44 * S, desk - 10 * S, sx1 + 44 * S, desk], (74, 96, 114))
    poly(img, [(sx0 - 20 * S, sy1 + 14 * S), (sx1 + 20 * S, sy1 + 14 * S),
               (sx1 + 70 * S, desk - 12 * S), (sx0 - 70 * S, desk - 12 * S)], (52, 68, 82))

    ox, oy = CW * .375, CH * .27
    ww, hh, dd = CW * .215, CH * .245, CW * .085
    C = (168, 214, 242)
    A = (ox, oy + hh); B = (ox + ww, oy + hh); Cc = (ox + ww, oy); D = (ox, oy)
    A2 = (ox + dd, oy + hh - dd * .5); B2 = (ox + ww + dd, oy + hh - dd * .5)
    C2 = (ox + ww + dd, oy - dd * .5); D2 = (ox + dd, oy - dd * .5)
    poly(img, [A, B, Cc, D], (120, 180, 214), 34)
    poly(img, [B, B2, C2, Cc], (120, 180, 214), 22)
    poly(img, [D, D2, C2, Cc], (120, 180, 214), 16)
    for a, b in [(A, B), (B, Cc), (Cc, D), (D, A), (A2, B2), (B2, C2), (C2, D2), (D2, A2),
                 (A, A2), (B, B2), (Cc, C2), (D, D2)]:
        line(img, [a, b], C, 2.6 * S, 225)
    line(img, [((A[0] + B[0]) / 2, A[1]), ((D[0] + Cc[0]) / 2, D[1])], (214, 238, 252), 2 * S, 150)
    line(img, [(ox, oy + hh + 26 * S), (ox + ww, oy + hh + 26 * S)], (120, 160, 186), 1.8 * S, 190)
    line(img, [(ox - 26 * S, oy), (ox - 26 * S, oy + hh)], (120, 160, 186), 1.8 * S, 190)
    for gx in range(8):
        x = sx0 + 20 * S + gx * (sx1 - sx0 - 40 * S) / 7
        line(img, [(x, sy0 + 18 * S), (x, sy1 - 18 * S)], (70, 108, 134), 1.2 * S, 70)

    rect(img, [CW * .055, desk - 40 * S, CW * .195, desk], (34, 46, 56))
    line(img, [(CW * .055, desk - 40 * S), (CW * .195, desk - 40 * S)], (140, 182, 210), 2.6 * S, 200)
    for i in range(4):
        line(img, [(CW * .80, desk - (12 + i * 9) * S), (CW * .94, desk - (12 + i * 9) * S)], (54, 72, 86), 5 * S)
    ell(img, [CW * .855, desk - 96 * S, CW * .90, desk - 44 * S], (44, 60, 74))
    img = glow(img, CW * .12, desk - 30 * S, 150 * S, (50, 80, 104), .5, 2.2)

    img = motes(img, 90, (0, CH * .1, CW, desk), (170, 210, 238), 2.6, 80, 37)
    return finish(img, '10-proiect', .5, 6, .93)


def sc11_oglinda():
    img = vgrad([(0, (20, 26, 32)), (.45, (34, 44, 54)), (1, (14, 19, 24))])
    for i in range(7):
        x = CW * (i / 6)
        line(img, [(x, 0), (x, CH * .82)], (54, 70, 84), 2 * S, 110)
    for j in range(5):
        y = CH * (j / 4) * .82
        line(img, [(0, y), (CW, y)], (54, 70, 84), 2 * S, 80)

    cx, cy = CW * .5, CH * .40
    rx, ry = CW * .150, CH * .295
    img = glow(img, cx, cy, 520 * S, (52, 84, 110), .9, 1.8)
    ell(img, [cx - rx * 1.14, cy - ry * 1.11, cx + rx * 1.14, cy + ry * 1.11], (198, 230, 250), 210, blur=22 * S)
    ell(img, [cx - rx, cy - ry, cx + rx, cy + ry], (26, 36, 45))
    ell(img, [cx - rx, cy - ry, cx + rx, cy + ry], None, outline=(150, 190, 216), wdt=int(3 * S))

    ref = new()
    ImageDraw.Draw(ref).polygon([(cx - rx * .95, cy + ry * .2), (cx - rx * .2, cy - ry * .95),
                                 (cx + rx * .15, cy - ry * .95), (cx - rx * .7, cy + ry * .6)],
                                fill=(190, 224, 246, 17))
    m = Image.new('L', (CW, CH), 0)
    ImageDraw.Draw(m).ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=255)
    ref.putalpha(ImageChops.multiply(ref.split()[3], m))
    img.alpha_composite(soft(ref, 10 * S))

    top = CH * .82
    rect(img, [CW * .10, top, CW * .90, top + 20 * S], (62, 82, 98))
    rect(img, [CW * .10, top + 20 * S, CW * .90, CH], (20, 27, 34))
    line(img, [(CW * .10, top), (CW * .90, top)], (150, 190, 214), 3 * S, 190)
    ell(img, [cx - 150 * S, top - 30 * S, cx + 150 * S, top + 12 * S], (74, 96, 114))
    ell(img, [cx - 128 * S, top - 24 * S, cx + 128 * S, top + 4 * S], (26, 34, 42))
    rect(img, [cx - 7 * S, top - 116 * S, cx + 7 * S, top - 24 * S], (170, 206, 230))
    rect(img, [cx - 7 * S, top - 122 * S, cx + 64 * S, top - 108 * S], (170, 206, 230))
    rect(img, [cx + 56 * S, top - 108 * S, cx + 64 * S, top - 92 * S], (170, 206, 230))
    img = glow(img, cx, top - 20 * S, 230 * S, (48, 78, 100), .6, 2.0)

    for sx in (CW * .085, CW * .915):
        rect(img, [sx - 6 * S, CH * .16, sx + 6 * S, CH * .64], (216, 240, 254), 240)
        img = glow(img, sx, CH * .40, 220 * S, (56, 92, 118), .85, 1.9)

    px = CW * .19
    rect(img, [px - 26 * S, top - 54 * S, px + 26 * S, top - 4 * S], (48, 64, 78))
    for i in range(7):
        a = -math.pi / 2 + (i / 6 - .5) * 1.9
        line(img, [(px, top - 54 * S), (px + math.cos(a) * 70 * S, top - 54 * S + math.sin(a) * 90 * S)],
             (54, 84, 76), 5 * S, 220)

    return finish(img, '11-oglinda', .45, 6, .93)


FNS = [sc01_sat, sc02_atelier_vechi, sc03_caruta, sc04_drum, sc05_ani, sc06_generatii,
       sc07_maiestrie, sc08_unelte, sc09_cnc, sc10_proiect, sc11_oglinda]

if __name__ == '__main__':
    import sys
    os.makedirs(OUT, exist_ok=True)
    only = sys.argv[1:] 
    ims = []
    for f in FNS:
        if only and not any(o in f.__name__ for o in only):
            continue
        random.seed(7)
        ims.append(f())
        print('ok', f.__name__)
    cols, tw, th = 3, 520, 292
    rows = (len(ims) + cols - 1) // cols
    sheet = Image.new('RGB', (tw * cols, th * rows), (0, 0, 0))
    for i, im in enumerate(ims):
        sheet.paste(im.resize((tw, th), Image.LANCZOS), ((i % cols) * tw, (i // cols) * th))
    sheet.save('/tmp/story_sheet.png')
    print('planșă /tmp/story_sheet.png')
