"""Cenários (fundos 1080x1920) desenhados proceduralmente e guardados em cache."""
import math
import os
import random
from PIL import Image, ImageFilter
from .canvas import Canvas, OUT, mix, darker, lighter

W, H = 1080, 1920
CACHE = os.path.join(os.path.dirname(__file__), "..", ".cache", "fundos")


# ---------------------------------------------------------------- blocos básicos
def ceu(c, top, bot, y1=H):
    c.vgradient(0, 0, W, y1, top, bot)


def nuvem(c, x, y, s=1.0, cor=(255, 255, 255)):
    for dx, dy, r in ((-60, 10, 50), (0, -20, 70), (70, 5, 55), (120, 20, 40), (-110, 25, 35)):
        c.circle(x + dx * s, y + dy * s, r * s, fill=cor, w=0)
    c.rect(x - 140 * s, y + 10 * s, x + 160 * s, y + 60 * s, fill=cor, w=0, r=25 * s)


def predio(c, x, y_base, w, h, cor, janelas=True, acesas=0.0, rnd=None):
    rnd = rnd or random.Random(int(x * 7 + h))
    c.rect(x, y_base - h, x + w, y_base, fill=cor, w=5)
    if janelas:
        jc = lighter(cor, 0.45)
        for yy in range(int(y_base - h + 30), int(y_base - 40), 60):
            for xx in range(int(x + 20), int(x + w - 30), 46):
                on = rnd.random() < acesas
                c.rect(xx, yy, xx + 26, yy + 34, fill=(255, 225, 120) if on else jc, w=0)


def piso_madeira(c, y0, cor=(170, 120, 75)):
    c.rect(0, y0, W, H, fill=cor, w=0)
    for i in range(-10, 22):
        x = W / 2 + i * 120
        c.line([(W / 2 + (x - W / 2) * 0.15, y0), (x * 1.0 + (x - W / 2) * 1.6, H)], fill=darker(cor, 0.85), w=4,
               round_caps=False)
    for j, y in enumerate([y0 + 40, y0 + 110, y0 + 220, y0 + 390]):
        if y < H:
            c.line([(0, y), (W, y)], fill=darker(cor, 0.88), w=3, round_caps=False)


def parede(c, y1, cor, rodape=None):
    c.rect(0, 0, W, y1, fill=cor, w=0)
    if rodape:
        c.rect(0, y1 - 70, W, y1, fill=rodape, w=0)
        c.line([(0, y1 - 70), (W, y1 - 70)], w=5)


def janela(c, x, y, w, h, ceu_top=(120, 190, 250), ceu_bot=(200, 230, 255), noite=False):
    c.rect(x - 14, y - 14, x + w + 14, y + h + 14, fill=(240, 240, 240), w=5)
    c.vgradient(x, y, x + w, y + h, ceu_top if not noite else (15, 20, 50), ceu_bot if not noite else (40, 40, 90))
    if not noite:
        nuvem(c, x + w * 0.3, y + h * 0.3, 0.45)
    else:
        c.circle(x + w * 0.7, y + h * 0.25, 30, fill=(250, 245, 210), w=0)
    c.line([(x + w / 2, y), (x + w / 2, y + h)], fill=(240, 240, 240), w=12, round_caps=False)
    c.line([(x, y + h / 2), (x + w, y + h / 2)], fill=(240, 240, 240), w=12, round_caps=False)
    c.rect(x, y, x + w, y + h, fill=None, w=5)


def coqueiro(c, x, y, s=1.0, flip=1):
    tronco = (150, 100, 55)
    pts = []
    for i in range(12):
        t = i / 11
        pts.append((x + flip * 60 * s * math.sin(t * 1.6), y - 520 * s * t))
    c.line(pts, fill=OUT, w=58 * s)
    c.line(pts, fill=tronco, w=42 * s)
    for i in range(1, 11):
        px, py = pts[i]
        c.line([(px - 18 * s, py), (px + 18 * s, py + 6 * s)], fill=darker(tronco, 0.75), w=5 * s)
    tx, ty = pts[-1]
    for a in (200, 235, 275, 310, 345, 160, 20):
        r = math.radians(a)
        ex, ey = tx + 230 * s * math.cos(r), ty + 120 * s * math.sin(r) + 60 * s
        mx, my = tx + 120 * s * math.cos(r), ty + 90 * s * math.sin(r) - 30 * s
        folha = [(tx, ty), (mx - 20 * s, my - 25 * s), (ex, ey), (mx + 20 * s, my + 25 * s)]
        c.poly(folha, fill=(60, 170, 80), w=6 * s)
        c.line([(tx, ty), (mx, my), (ex, ey)], fill=(40, 120, 60), w=4 * s)
    for dx in (-25, 20):
        c.circle(tx + dx * s, ty + 30 * s, 22 * s, fill=(110, 80, 40), w=5 * s)


def oca(c, x, y, s=1.0):
    palha = (205, 165, 90)
    c.rect(x - 150 * s, y - 170 * s, x + 150 * s, y, fill=(170, 120, 70), w=6)
    c.rect(x - 45 * s, y - 120 * s, x + 45 * s, y, fill=(50, 35, 25), w=6, r=30 * s)
    c.poly([(x - 210 * s, y - 150 * s), (x, y - 400 * s), (x + 210 * s, y - 150 * s)], fill=palha, w=6)
    for i in range(1, 6):
        c.line([(x, y - 400 * s), (x - 210 * s + i * 70 * s, y - 150 * s)], fill=darker(palha, 0.8), w=4)


def folhagem(c, rnd, y0, y1, n=40, cores=((40, 130, 60), (50, 150, 70), (30, 110, 50))):
    for _ in range(n):
        x = rnd.uniform(-50, W + 50)
        y = rnd.uniform(y0, y1)
        r = rnd.uniform(60, 140)
        c.circle(x, y, r, fill=rnd.choice(cores), w=5)


def raios_bg(c, cor1, cor2, cx=W / 2, cy=H * 0.42, n=24):
    c.rect(0, 0, W, H, fill=cor1, w=0)
    R = 2600
    for i in range(n):
        if i % 2:
            continue
        a0 = math.radians(i * 360 / n)
        a1 = math.radians((i + 1) * 360 / n)
        c.poly([(cx, cy), (cx + R * math.cos(a0), cy + R * math.sin(a0)), (cx + R * math.cos(a1), cy + R * math.sin(a1))],
               fill=cor2, w=0)


def bandeira_br(c, x, y, w, h):
    c.rect(x, y, x + w, y + h, fill=(0, 150, 60), w=6)
    c.poly([(x + w * 0.08, y + h / 2), (x + w / 2, y + h * 0.1), (x + w * 0.92, y + h / 2), (x + w / 2, y + h * 0.9)],
           fill=(255, 210, 0), w=0)
    c.circle(x + w / 2, y + h / 2, h * 0.24, fill=(20, 50, 140), w=0)
    c.arc(x + w / 2, y + h / 2 + h * 0.25, h * 0.36, h * 0.3, 240, 300, fill=(255, 255, 255), w=h * 0.04)


# ---------------------------------------------------------------- cenários
def _bandeira(c):
    raios_bg(c, (0, 140, 60), (20, 165, 75))
    c.poly([(W / 2, 360), (W - 30, 900), (W / 2, 1440), (30, 900)], fill=(255, 210, 0), w=10)
    c.circle(W / 2, 900, 300, fill=(20, 50, 140), w=10)
    c.arc(W / 2, 1210, 470, 380, 236, 304, fill=(255, 255, 255), w=36)
    rnd = random.Random(3)
    for _ in range(26):
        c.circle(W / 2 + rnd.uniform(-240, 240), 900 + rnd.uniform(-60, 240), rnd.uniform(4, 9), fill=(255, 255, 255), w=0)


def _paulista(c, noite=False):
    ceu(c, (110, 180, 245) if not noite else (15, 20, 45), (200, 230, 255) if not noite else (60, 50, 100), 1300)
    if not noite:
        nuvem(c, 260, 260, 1.0)
        nuvem(c, 820, 420, 0.8)
    rnd = random.Random(11)
    x = -40
    while x < W:
        w = rnd.randint(160, 260)
        h = rnd.randint(500, 1050)
        cor = rnd.choice([(150, 160, 180), (120, 135, 160), (170, 160, 150), (100, 115, 140)])
        predio(c, x, 1300, w, h, cor if not noite else darker(cor, 0.5), acesas=0.6 if noite else 0.0, rnd=rnd)
        x += w - 10
    c.rect(0, 1300, W, 1380, fill=(190, 190, 190), w=5)
    c.rect(0, 1380, W, H, fill=(70, 72, 80), w=0)
    for i in range(6):
        c.rect(60 + i * 190, 1620, 160 + i * 190, 1650, fill=(250, 250, 250), w=0)


def _feira(c):
    ceu(c, (120, 190, 250), (210, 235, 255), 1250)
    nuvem(c, 800, 250, 0.9)
    predio(c, 0, 1250, 380, 700, (230, 200, 160))
    predio(c, 700, 1250, 400, 820, (200, 170, 150))
    c.rect(0, 1250, W, H, fill=(160, 160, 165), w=0)
    # barraca
    c.rect(90, 980, 990, 1060, fill=(240, 240, 240), w=6)
    for i in range(9):
        c.rect(90 + i * 100, 980, 190 + i * 100, 1060, fill=(230, 60, 50) if i % 2 == 0 else (250, 250, 250), w=4)
    for i in range(9):
        c.chord(140 + i * 100, 1060, 50, 34, 0, 180, fill=(230, 60, 50) if i % 2 == 0 else (250, 250, 250), w=4)
    c.line([(120, 1060), (120, 1500)], w=18)
    c.line([(960, 1060), (960, 1500)], w=18)
    c.rect(330, 860, 750, 960, fill=(250, 210, 40), w=7, r=16)
    c.text(540, 912, "PASTEL", 70, fill=(200, 40, 40), black=True)
    c.rect(60, 1400, 1020, 1520, fill=(150, 100, 60), w=7, r=10)


def _tv_estudio(c):
    c.rect(0, 0, W, H, fill=(25, 35, 70), w=0)
    for i in range(12):
        c.line([(i * 100 - 300, 0), (i * 100 + 300, 1300)], fill=(35, 50, 95), w=30, round_caps=False)
    c.rect(0, 1300, W, H, fill=(45, 55, 95), w=0)
    c.rect(-20, 1300, W + 20, 1420, fill=(60, 120, 220), w=6)
    c.rect(-20, 1420, W + 20, 1440, fill=(250, 200, 40), w=0)


def _brasilia(c):
    ceu(c, (100, 175, 245), (215, 238, 255), 1260)
    nuvem(c, 230, 230, 0.9)
    nuvem(c, 880, 380, 0.7)
    # torres
    for x in (440, 560):
        c.rect(x, 520, x + 85, 1110, fill=(215, 220, 225), w=6)
        for y in range(545, 1100, 26):
            c.line([(x + 8, y), (x + 77, y)], fill=(150, 175, 200), w=6, round_caps=False)
    c.rect(500, 760, 600, 800, fill=(215, 220, 225), w=6)
    # base
    c.rect(80, 1100, 1000, 1170, fill=(230, 232, 235), w=6)
    # cúpulas
    c.chord(260, 1105, 140, 90, 180, 360, fill=(240, 240, 240), w=6)
    c.chord(820, 1190, 190, 120, 0, 180, fill=(240, 240, 240), w=6)
    c.rect(0, 1170, W, H, fill=(110, 180, 80), w=0)
    c.poly([(380, 1170), (700, 1170), (1080, H), (0, H)], fill=(200, 200, 200), w=0)
    c.line([(380, 1170), (0, H)], w=5)
    c.line([(700, 1170), (1080, H)], w=5)


def _gabinete(c):
    parede(c, 1300, (225, 210, 180), (150, 110, 70))
    janela(c, 120, 250, 420, 560)
    c.line([(830, 260), (830, 1300)], fill=(120, 90, 50), w=14)
    bandeira_br(c, 840, 270, 220, 150)
    c.rect(600, 340, 790, 560, fill=(150, 110, 70), w=6)
    c.rect(625, 365, 765, 535, fill=(240, 235, 220), w=4)
    c.text(695, 450, "BR", 60, fill=(0, 140, 60), black=True)
    c.rect(0, 1300, W, H, fill=(120, 30, 40), w=0)
    c.rect(90, 1300, 990, 1380, fill=(100, 25, 35), w=0)


def _escola(c):
    parede(c, 1280, (205, 195, 235), (150, 110, 80))
    c.rect(150, 300, 930, 760, fill=(50, 90, 70), w=8)
    c.text(540, 420, "CARDÁPIO", 64, fill=(250, 250, 250))
    c.text(540, 540, "RAMEN GRÁTIS", 72, fill=(250, 220, 90), black=True)
    c.text(540, 650, "todo dia :)", 48, fill=(250, 250, 250))
    piso_madeira(c, 1280)


def _plenario(c):
    c.rect(0, 0, W, H, fill=(40, 70, 60), w=0)
    for i in range(7):
        y = 520 + i * 120
        c.chord(W / 2, y + 900, 900 + i * 40, 900, 180, 360, fill=(30, 110, 70) if i % 2 else (25, 95, 60), w=5)
    c.rect(0, 1250, W, H, fill=(25, 85, 55), w=0)
    c.rect(300, 200, 780, 380, fill=(120, 80, 50), w=7, r=10)
    bandeira_br(c, 460, 230, 160, 110)


def _cofre(c):
    c.rect(0, 0, W, H, fill=(60, 65, 75), w=0)
    for y in range(0, 1300, 130):
        c.line([(0, y), (W, y)], fill=(80, 85, 95), w=6, round_caps=False)
    c.circle(W / 2, 600, 380, fill=(150, 155, 165), w=10)
    c.circle(W / 2, 600, 300, fill=(120, 125, 135), w=8)
    for a in range(0, 360, 45):
        r = math.radians(a)
        c.line([(W / 2, 600), (W / 2 + 220 * math.cos(r), 600 + 220 * math.sin(r))], w=18)
    c.circle(W / 2, 600, 70, fill=(200, 170, 60), w=8)
    c.rect(0, 1300, W, H, fill=(90, 90, 100), w=0)
    rnd = random.Random(5)
    for i in range(60):
        x = rnd.uniform(-20, W)
        y = rnd.uniform(1280, 1500)
        c.rect(x, y, x + 130, y + 60, fill=(80, 170, 90), w=5, r=6)
        c.circle(x + 65, y + 30, 16, fill=(60, 140, 70), w=3)


def _cidade_feliz(c):
    ceu(c, (255, 190, 120), (255, 235, 180), 1300)
    c.circle(W / 2, 700, 230, fill=(255, 240, 150), w=0)
    rnd = random.Random(21)
    x = -30
    while x < W:
        w = rnd.randint(170, 240)
        h = rnd.randint(380, 700)
        cor = rnd.choice([(250, 160, 120), (120, 190, 220), (250, 210, 110), (160, 210, 140), (230, 140, 170)])
        predio(c, x, 1300, w, h, cor, rnd=rnd)
        c.rect(x + 20, 1300 - 120, x + w - 30, 1300 - 70, fill=(230, 60, 50), w=4, r=6)
        c.text(x + w / 2 - 5, 1300 - 95, "RAMEN", 30, fill=(255, 255, 255), black=True)
        x += w - 8
    c.rect(0, 1300, W, H, fill=(210, 200, 185), w=0)
    for i in range(12):
        c.line([(i * 100, 1300), (i * 140 - 250, H)], fill=(190, 180, 165), w=4)


def _estadio(c):
    c.rect(0, 0, W, H, fill=(15, 20, 45), w=0)
    for x in (120, 960):
        c.line([(x, 120), (x, 600)], fill=(80, 80, 90), w=16)
        c.rect(x - 90, 60, x + 90, 160, fill=(250, 250, 220), w=6, r=10)
    rnd = random.Random(8)
    for row in range(14):
        y = 560 + row * 48
        for i in range(30):
            x = i * 38 + (row % 2) * 18
            col = rnd.choice([(250, 210, 40), (0, 150, 60), (250, 250, 250), (220, 40, 50), (40, 60, 160)])
            c.circle(x, y, 17, fill=col, w=3)
    c.rect(0, 1240, W, H, fill=(40, 150, 60), w=0)
    for i in range(0, 10, 2):
        c.rect(0, 1240 + i * 70, W, 1310 + i * 70, fill=(50, 165, 70), w=0)
    c.line([(0, 1240), (W, 1240)], fill=(255, 255, 255), w=8)


def _raios_lj(c):
    raios_bg(c, (250, 140, 40), (255, 175, 70))


def _raios_azul(c):
    raios_bg(c, (40, 90, 200), (60, 120, 230))


def _raios_vermelho(c):
    raios_bg(c, (170, 30, 40), (200, 45, 55))


def _raios_verde(c):
    raios_bg(c, (30, 150, 80), (50, 175, 100))


def _escuro(c):
    c.rect(0, 0, W, H, fill=(18, 16, 28), w=0)
    c.circle(W / 2, 760, 600, fill=(30, 28, 45), w=0)


# ---- ilha
def _aviao(c):
    c.rect(0, 0, W, H, fill=(225, 225, 230), w=0)
    c.chord(W / 2, 200, 700, 300, 0, 180, fill=(200, 200, 210), w=6)
    for x in (120, 760):
        c.rect(x, 420, x + 200, 700, fill=(200, 200, 205), w=6, r=90)
        c.vgradient(x + 25, 445, x + 175, 675, (110, 180, 250), (210, 235, 255))
        c.rect(x + 25, 445, x + 175, 675, fill=None, w=5, r=70)
        nuvem(c, x + 100, 580, 0.35)
    c.rect(0, 1200, W, H, fill=(70, 80, 110), w=0)
    for i, x in enumerate((20, 330, 640, 950)):
        c.rect(x - 60, 900, x + 150, 1350, fill=(40, 70, 140), w=7, r=40)
        c.rect(x - 50, 860, x + 140, 960, fill=(240, 240, 245), w=6, r=20)


def _mar_tempestade(c):
    ceu(c, (35, 40, 60), (80, 85, 110), 1100)
    for x, y, s in ((200, 200, 1.4), (700, 300, 1.6), (450, 520, 1.2), (950, 600, 1.0)):
        nuvem(c, x, y, s, (60, 65, 85))
    c.poly([(640, 300), (560, 620), (640, 610), (560, 900), (720, 560), (640, 570), (720, 300)], fill=(255, 240, 120), w=6)
    c.rect(0, 1100, W, H, fill=(20, 60, 100), w=0)
    for row in range(10):
        y = 1120 + row * 85
        for i in range(-1, 10):
            x = i * 130 + (row % 2) * 65
            c.chord(x, y, 70, 45, 180, 360, fill=(40, 100, 150) if row % 2 else (30, 80, 130), w=5)


def _praia(c, navio=False):
    ceu(c, (90, 175, 245), (220, 240, 255), 1050)
    c.circle(840, 260, 110, fill=(255, 230, 110), w=0)
    nuvem(c, 250, 280, 0.9)
    c.rect(0, 1000, W, 1250, fill=(40, 150, 210), w=0)
    for i in range(8):
        c.line([(i * 150 + 20, 1060 + (i % 3) * 50), (i * 150 + 90, 1060 + (i % 3) * 50)], fill=(170, 225, 250), w=6)
    c.chord(W / 2, 1260, 1000, 120, 180, 360, fill=(250, 250, 250), w=0)
    c.rect(0, 1250, W, H, fill=(245, 215, 150), w=0)
    c.chord(W / 2, 1255, 900, 60, 180, 360, fill=(245, 215, 150), w=0)
    rnd = random.Random(2)
    for _ in range(40):
        c.circle(rnd.uniform(0, W), rnd.uniform(1300, H), 4, fill=(220, 185, 120), w=0)
    coqueiro(c, 60, 1420, 1.25, 1)
    coqueiro(c, 1030, 1380, 1.0, -1)


def _praia_navio(c):
    _praia(c)


def _selva(c):
    c.rect(0, 0, W, H, fill=(25, 70, 40), w=0)
    rnd = random.Random(7)
    for x in (60, 330, 760, 1000):
        c.rect(x, 0, x + 90, 1500, fill=(90, 60, 40), w=6)
    folhagem(c, rnd, -100, 500, 30, ((30, 100, 50), (40, 120, 55), (25, 85, 45)))
    c.rect(0, 1300, W, H, fill=(80, 120, 50), w=0)
    folhagem(c, rnd, 1250, 1400, 22, ((50, 140, 60), (40, 125, 55), (60, 155, 70)))
    for _ in range(14):
        x = rnd.uniform(0, W)
        c.line([(x, 0), (x + rnd.uniform(-30, 30), rnd.uniform(400, 900))], fill=(50, 110, 50), w=8)


def _aldeia(c, noite=False):
    if noite:
        ceu(c, (10, 15, 40), (70, 40, 70), 1150)
        rnd = random.Random(4)
        for _ in range(60):
            c.circle(rnd.uniform(0, W), rnd.uniform(0, 900), rnd.uniform(2, 5), fill=(255, 255, 230), w=0)
        c.circle(820, 260, 90, fill=(250, 245, 210), w=0)
    else:
        ceu(c, (255, 160, 90), (255, 215, 150), 1150)
        c.circle(540, 900, 260, fill=(255, 235, 150), w=0)
    rnd = random.Random(9)
    folhagem(c, rnd, 950, 1150, 18, ((30, 90, 50), (25, 75, 45)) if not noite else ((15, 40, 30), (20, 50, 35)))
    oca(c, 170, 1250, 0.95)
    oca(c, 900, 1230, 0.85)
    c.rect(0, 1240, W, H, fill=(185, 140, 90) if not noite else (90, 65, 55), w=0)
    for x in (40, 1040):
        c.line([(x, 1250), (x, 1000)], fill=(110, 70, 40), w=20)


def _aldeia_noite(c):
    _aldeia(c, True)


def _conves(c):
    ceu(c, (90, 175, 245), (220, 240, 255), 1000)
    c.rect(0, 900, W, 1150, fill=(40, 140, 200), w=0)
    c.rect(0, 1150, W, H, fill=(160, 110, 60), w=0)
    for i in range(12):
        c.line([(0, 1150 + i * 70), (W, 1150 + i * 70)], fill=(130, 85, 45), w=5)
    c.rect(0, 1080, W, 1150, fill=(140, 90, 50), w=6)
    c.line([(880, 1100), (880, 0)], fill=(120, 80, 40), w=36)
    c.poly([(890, 120), (890, 800), (1080, 760), (1080, 160)], fill=(250, 250, 245), w=6)


# ---- IA
def _quarto(c, noite=False):
    parede(c, 1300, (170, 190, 220) if not noite else (35, 40, 70), (120, 90, 70) if not noite else (50, 40, 50))
    janela(c, 600, 260, 340, 420, noite=noite)
    c.rect(90, 330, 430, 560, fill=(250, 250, 250) if not noite else (70, 70, 90), w=6)
    c.text(260, 445, "ESTUDAR", 46, fill=(60, 60, 80), black=True)
    piso_madeira(c, 1300, (160, 115, 80) if not noite else (60, 45, 45))
    c.rect(60, 1180, 1020, 1240, fill=(150, 100, 60) if not noite else (60, 45, 40), w=7, r=10)
    c.line([(140, 1240), (140, 1600)], w=24)
    c.line([(940, 1240), (940, 1600)], w=24)


def _quarto_noite(c):
    _quarto(c, True)


def _cidade_ia(c):
    ceu(c, (30, 10, 20), (130, 30, 40), 1300)
    rnd = random.Random(31)
    x = -30
    while x < W:
        w = rnd.randint(150, 240)
        h = rnd.randint(500, 1000)
        predio(c, x, 1300, w, h, (40, 35, 55), acesas=0.25, rnd=rnd)
        x += w - 6
    c.rect(0, 1300, W, H, fill=(35, 30, 40), w=0)
    for i in range(6):
        c.rect(60 + i * 190, 1620, 160 + i * 190, 1650, fill=(200, 60, 60), w=0)


def _rua(c):
    _paulista(c)


def _rua_cinza(c):
    ceu(c, (150, 155, 160), (190, 192, 195), 1300)
    rnd = random.Random(11)
    x = -40
    while x < W:
        w = rnd.randint(160, 260)
        h = rnd.randint(500, 1050)
        g = rnd.randint(110, 160)
        predio(c, x, 1300, w, h, (g, g, g + 5), rnd=rnd)
        x += w - 10
    c.rect(0, 1300, W, H, fill=(95, 95, 100), w=0)


def _porao(c):
    c.rect(0, 0, W, H, fill=(55, 45, 45), w=0)
    for row in range(0, 1300, 70):
        off = 0 if (row // 70) % 2 else 60
        for x in range(-60, W, 120):
            c.rect(x + off, row, x + off + 116, row + 66, fill=(95, 60, 50), w=4)
    c.circle(W / 2, 600, 520, fill=None, w=0)
    c.rect(0, 1300, W, H, fill=(70, 65, 65), w=0)
    c.line([(W / 2, 0), (W / 2, 260)], w=6)
    c.circle(W / 2, 300, 45, fill=(255, 230, 140), w=6)
    c.rect(170, 1150, 910, 1230, fill=(120, 80, 50), w=7, r=8)
    c.line([(220, 1230), (220, 1500)], w=22)
    c.line([(860, 1230), (860, 1500)], w=22)


def _servidores(c):
    c.rect(0, 0, W, H, fill=(15, 20, 35), w=0)
    rnd = random.Random(13)
    for i, x in enumerate((20, 290, 560, 830)):
        c.rect(x, 200, x + 230, 1350, fill=(40, 45, 65), w=7, r=10)
        for y in range(240, 1320, 70):
            c.rect(x + 20, y, x + 210, y + 50, fill=(25, 30, 45), w=4, r=4)
            for j in range(4):
                col = rnd.choice([(80, 230, 255), (80, 255, 140), (255, 70, 70)])
                c.circle(x + 40 + j * 22, y + 25, 6, fill=col, w=0)
    c.rect(0, 1350, W, H, fill=(25, 30, 45), w=0)
    for i in range(12):
        c.line([(i * 100, 1350), (i * 150 - 280, H)], fill=(35, 40, 60), w=4)


BACKGROUNDS = {
    "bandeira": _bandeira, "paulista": _paulista, "paulista_noite": lambda c: _paulista(c, True), "feira": _feira,
    "tv": _tv_estudio, "brasilia": _brasilia, "gabinete": _gabinete, "escola": _escola, "plenario": _plenario,
    "cofre": _cofre, "cidade_feliz": _cidade_feliz, "estadio": _estadio, "raios_laranja": _raios_lj,
    "raios_azul": _raios_azul, "raios_vermelho": _raios_vermelho, "raios_verde": _raios_verde, "escuro": _escuro,
    "aviao": _aviao, "mar": _mar_tempestade, "praia": _praia, "selva": _selva, "aldeia": _aldeia,
    "aldeia_noite": _aldeia_noite, "conves": _conves, "quarto": _quarto, "quarto_noite": _quarto_noite,
    "cidade_ia": _cidade_ia, "rua": _rua, "rua_cinza": _rua_cinza, "porao": _porao, "servidores": _servidores,
}

_mem = {}


def fundo(nome):
    """Retorna o fundo (RGB 1080x1920). Usa cache em disco e memória."""
    if nome in _mem:
        return _mem[nome]
    os.makedirs(CACHE, exist_ok=True)
    path = os.path.join(CACHE, f"{nome}.png")
    if os.path.exists(path):
        img = Image.open(path).convert("RGB")
    else:
        c = Canvas(W, H, bg=(0, 0, 0))
        BACKGROUNDS[nome](c)
        img = c.final().convert("RGB")
        img.save(path)
    _mem[nome] = img
    return img
