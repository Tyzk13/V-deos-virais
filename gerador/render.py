"""Monta e renderiza o vídeo: cenas -> quadros + áudio -> MP4 9:16."""
import math
import os
import random
import re
import shutil
import subprocess
import tempfile
from concurrent.futures import ProcessPoolExecutor
from functools import lru_cache

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageOps

from . import audio as au
from .canvas import font
from .cenarios import fundo
from .personagens import sprite, FX, FY
from .props import sprite_prop, tamanho

W, H, FPS = 1080, 1920, 30
LEG_Y = 1330          # altura da legenda (centro)
AMARELO = (255, 222, 40)


# ======================================================================= API dos roteiros
def A(spec, x=540, y=1750, s=1.4, expr="neutro", pose="parado", fala=False, anim="respirar", para=None,
      flip=False, entra=0.0, troca=(), look=0, sai=None):
    """Ator. (x, y) = posição dos pés no cenário 1080x1920; s = escala."""
    return dict(tipo="ator", spec=spec, x=x, y=y, s=s, expr=expr, pose=pose, fala=fala, anim=anim, para=para,
                flip=flip, entra=entra, troca=tuple(troca), look=look, sai=sai)


def Pr(nome, x=540, y=1500, s=1.0, anim=None, para=None, entra=0.0, sai=None, flip=False, **args):
    """Objeto de cena. (x, y) = base-centro."""
    return dict(tipo="prop", nome=nome, x=x, y=y, s=s, anim=anim, para=para, entra=entra, sai=sai, flip=flip,
                args=tuple(sorted(args.items())))


def Cena(fala, fundo, elenco=(), cam=None, sfx=(), fx=(), destaque=(), voz=None, extra=0.35, desfoque=0,
         min_dur=1.4):
    return dict(fala=fala, fundo=fundo, elenco=list(elenco), cam=cam, sfx=list(sfx), fx=list(fx),
                destaque=[d.lower() for d in destaque], voz=voz, extra=extra, desfoque=desfoque, min_dur=min_dur)


# ======================================================================= utilidades
def ease(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def _pop(t):
    """Curva de entrada com overshoot (0..1 em 0.3s)."""
    if t >= 0.3:
        return 1.0
    u = t / 0.3
    return 1 + 0.25 * math.sin(u * math.pi) - (1 - u) ** 2 * 0.9


@lru_cache(maxsize=64)
def _fundo_borrado(nome, raio):
    img = fundo(nome)
    return img.filter(ImageFilter.GaussianBlur(raio)) if raio else img


@lru_cache(maxsize=1)
def _vinheta():
    y, x = np.mgrid[0:H, 0:W]
    d = np.sqrt(((x - W / 2) / (W * 0.75)) ** 2 + ((y - H / 2) / (H * 0.7)) ** 2)
    a = np.clip((d - 0.55) * 1.3, 0, 0.55) * 255
    m = Image.fromarray(a.astype(np.uint8), "L")
    black = Image.new("RGB", (W, H), (0, 0, 0))
    return black, m


@lru_cache(maxsize=600)
def _sprite_ator(spec, expr, blink, talk, pose, scale, look, flip):
    im = sprite(spec, expr, blink, talk, pose, scale, look)
    return ImageOps.mirror(im) if flip else im


def _cam(cena, t, dur):
    cam = cena["cam"] or ((540, 960, 1.0), (540, 960, 1.07))
    if len(cam) == 3 and not isinstance(cam[0], (tuple, list)):
        cam = (cam, cam)
    (x0, y0, z0), (x1, y1, z1) = cam
    e = ease(t / max(dur, 0.01))
    cx, cy, z = x0 + (x1 - x0) * e, y0 + (y1 - y0) * e, z0 + (z1 - z0) * e
    if "soco" in cena["fx"]:
        z *= 1 + 0.16 * math.exp(-t * 9)
    z = max(1.0, z)
    hw, hh = W / 2 / z, H / 2 / z
    cx = min(max(cx, hw), W - hw)
    cy = min(max(cy, hh), H - hh)
    ox = oy = 0
    if "tremor" in cena["fx"]:
        r = random.Random(int(t * FPS))
        amp = 14 * (1 if "tremor_forte" not in cena["fx"] else 2)
        ox, oy = r.uniform(-amp, amp), r.uniform(-amp, amp)
    return cx, cy, z, ox, oy


# ======================================================================= legendas
def _limpa(w):
    return re.sub(r"[^\wÀ-ÿ%]", "", w.lower())


def blocos_legenda(palavras, destaque, t0):
    """Agrupa palavras em blocos de 1-3 palavras (estilo legenda 'palavra por palavra')."""
    blocos = []
    atual = []
    for w, a, b, cens in palavras:
        if cens:
            if atual:
                blocos.append(atual)
                atual = []
            blocos.append([(w, a, b, True)])
            continue
        if atual and len(" ".join(x[0] for x in atual) + " " + w) > 16:
            blocos.append(atual)
            atual = []
        atual.append((w, a, b, False))
        txt = " ".join(x[0] for x in atual)
        if len(atual) >= 3 or len(txt) >= 12 or w[-1] in ".,!?:;…":
            blocos.append(atual)
            atual = []
    if atual:
        blocos.append(atual)
    out = []
    for bl in blocos:
        palav = []
        for w, a, b, cens in bl:
            hl = (not cens) and any(_limpa(d) and _limpa(d) in _limpa(w) for d in destaque) and len(_limpa(w)) > 1
            palav.append((w, hl, cens))
        out.append(dict(ini=t0 + bl[0][1], fim=t0 + bl[-1][2], palavras=tuple(palav)))
    for i in range(len(out) - 1):
        out[i]["fim"] = max(out[i]["fim"], out[i + 1]["ini"])
    return out


@lru_cache(maxsize=512)
def _img_legenda(palavras):
    f = font(92, black=True)
    stroke = 11
    esp = f.getlength(" ")
    itens = []
    for w, hl, cens in palavras:
        if cens:
            itens.append(("#$%&!", 330, "cens"))
        else:
            itens.append((w, f.getlength(w), "hl" if hl else "n"))
    total = sum(i[1] for i in itens) + esp * (len(itens) - 1)
    linhas = [itens]
    if total > 980 and len(itens) > 1:
        meio = len(itens) // 2
        linhas = [itens[:meio], itens[meio:]]
    lh = 110
    img = Image.new("RGBA", (1080, lh * len(linhas) + 60), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    for li, linha in enumerate(linhas):
        tw = sum(i[1] for i in linha) + esp * (len(linha) - 1)
        x = 540 - tw / 2
        y = 30 + li * lh + lh / 2
        for txt, wd, kind in linha:
            if kind == "cens":
                d.rounded_rectangle([x, y - 52, x + wd, y + 52], radius=14, fill=(8, 8, 8), outline=(255, 255, 255),
                                    width=6)
                d.text((x + wd / 2, y), "BIP", font=font(56, True), fill=(255, 60, 60), anchor="mm")
            else:
                d.text((x, y), txt, font=f, fill=AMARELO if kind == "hl" else (255, 255, 255), anchor="lm",
                       stroke_width=stroke, stroke_fill=(10, 10, 14))
            x += wd + esp
    return img


def _desenha_legenda(frame, bloco, T):
    img = _img_legenda(bloco["palavras"])
    dt = T - bloco["ini"]
    k = 1.0 + 0.22 * max(0.0, 1 - dt / 0.12)
    if k != 1.0:
        img = img.resize((int(img.width * k), int(img.height * k)), Image.BILINEAR)
    frame.paste(img, (int(540 - img.width / 2), int(LEG_Y - img.height / 2)), img)


# ======================================================================= quadro
def _pos(el, t, dur):
    x, y = el["x"], el["y"]
    if el["para"]:
        x2, y2 = el["para"][:2]
        t_ini = el["entra"]
        t_fim = el["para"][2] if len(el["para"]) > 2 else dur
        e = ease((t - t_ini) / max(0.01, t_fim - t_ini))
        x, y = x + (x2 - x) * e, y + (y2 - y) * e
    anim = el["anim"]
    ph = (hash((el.get("nome"), el["x"], el["y"])) % 100) / 100 * 6.28
    if anim == "respirar":
        y += math.sin(t * 3 + ph) * 5
    elif anim == "pulo":
        y -= abs(math.sin(t * 7 + ph)) * 70
    elif anim == "andar":
        y -= abs(math.sin(t * 10 + ph)) * 22
    elif anim == "flutuar":
        y += math.sin(t * 2.2 + ph) * 18
    elif anim == "tremer":
        r = random.Random(int(t * FPS) + int(ph * 100))
        x += r.uniform(-7, 7)
        y += r.uniform(-4, 4)
    return x, y


def render_quadro(cena, t, dur, env, legenda, T):
    cx, cy, z, ox, oy = _cam(cena, t, dur)
    bg = _fundo_borrado(cena["fundo"], cena["desfoque"])
    a = 1 / z
    frame = bg.transform((W, H), Image.AFFINE, (a, 0, cx - W / 2 * a - ox * a, 0, a, cy - H / 2 * a - oy * a),
                         Image.BILINEAR)
    for i, el in enumerate(cena["elenco"]):
        if t < el["entra"] or (el["sai"] is not None and t >= el["sai"]):
            continue
        x, y = _pos(el, t, dur)
        k = _pop(t - el["entra"]) if el["entra"] > 0 or el.get("anim") == "pop" else 1.0
        if el["anim"] == "pulsar":
            k *= 1 + 0.05 * math.sin(t * 8)
        sc = round(el["s"] * z * k / 0.02) * 0.02
        if sc <= 0.02:
            continue
        sx = (x - cx) * z + W / 2 + ox
        sy = (y - cy) * z + H / 2 + oy
        if el["tipo"] == "ator":
            expr, pose, look = el["expr"], el["pose"], el["look"]
            for tt, mud in el["troca"]:
                if t >= tt:
                    expr = mud.get("expr", expr)
                    pose = mud.get("pose", pose)
                    look = mud.get("look", look)
            blink = ((t + i * 1.3) % 3.4) < 0.12
            talk = bool(el["fala"]) and env > 0.12 and int(t * 11) % 3 != 2
            im = _sprite_ator(el["spec"], expr, blink, talk, pose, sc, look, el["flip"])
            ax, ay = FX * sc, FY * sc
        else:
            im = sprite_prop(el["nome"], el["args"], t, sc)
            if el["flip"]:
                im = ImageOps.mirror(im)
            pw, ph = tamanho(el["nome"])
            ax, ay = pw * sc / 2, ph * sc
        px, py = int(sx - ax), int(sy - ay)
        if px > W or py > H or px + im.width < 0 or py + im.height < 0:
            continue
        frame.paste(im, (px, py), im)

    fx = cena["fx"]
    if "escuro" in fx:
        frame = Image.blend(frame, Image.new("RGB", (W, H), (5, 5, 15)), 0.45)
    if "vermelho" in fx:
        frame = Image.blend(frame, Image.new("RGB", (W, H), (160, 0, 20)), 0.22 + 0.08 * math.sin(t * 6))
    if "cinza" in fx:
        g = frame.convert("L").convert("RGB")
        frame = Image.blend(frame, g, 0.8)
    if "glitch" in fx and (int(t * FPS) % 9 < 3 or t < 0.3):
        arr = np.asarray(frame).copy()
        r = random.Random(int(t * FPS))
        arr[:, :, 0] = np.roll(arr[:, :, 0], r.randint(8, 22), axis=1)
        arr[:, :, 2] = np.roll(arr[:, :, 2], -r.randint(8, 22), axis=1)
        for _ in range(6):
            y0 = r.randint(0, H - 80)
            h = r.randint(10, 70)
            arr[y0:y0 + h] = np.roll(arr[y0:y0 + h], r.randint(-60, 60), axis=1)
        frame = Image.fromarray(arr)
    black, mask = _vinheta()
    frame.paste(black, (0, 0), mask)
    if "flash" in fx and t < 0.3:
        frame = Image.blend(frame, Image.new("RGB", (W, H), (255, 255, 255)), (1 - t / 0.3) * 0.85)
    if legenda is not None:
        _desenha_legenda(frame, legenda, T)
    return frame


# ======================================================================= pipeline
def _ffmpeg_writer(path):
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
           "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "21", "-pix_fmt", "yuv420p",
           path]
    return subprocess.Popen(cmd, stdin=subprocess.PIPE)


def _worker(args):
    cenas, idxs, starts, durs, env, legendas, path = args
    p = _ffmpeg_writer(path)
    for i in idxs:
        cena = cenas[i]
        n = int(round(durs[i] * FPS))
        f0 = int(round(starts[i] * FPS))
        for f in range(n):
            t = f / FPS
            T = (f0 + f) / FPS
            gi = min(len(env) - 1, f0 + f)
            leg = None
            for b in legendas:
                if b["ini"] <= T < b["fim"]:
                    leg = b
                    break
            im = render_quadro(cena, t, durs[i], env[gi], leg, T)
            p.stdin.write(im.tobytes())
    p.stdin.close()
    p.wait()
    return path


def gerar(cenas, saida, humor="misterio", bpm=96, workers=4, capa_t=0.6, velocidade=0.9, narracao=False):
    """narracao=False: a voz sintética só serve de guia de ritmo (legenda, boca, duração das cenas);
    o MP4 sai só com trilha + efeitos, pronto para receber as vozes gravadas."""
    tmp = tempfile.mkdtemp(prefix="video_")
    print(f"[1/4] Narrando {len(cenas)} cenas...")
    vozes, starts, durs, legendas = [], [], [], []
    T = 0.0
    for c in cenas:
        x, palavras = au.narrar(c["fala"], c["voz"], velocidade)
        dur = max(c["min_dur"], len(x) / au.SR + c["extra"])
        dur = round(dur * FPS) / FPS
        starts.append(T)
        durs.append(dur)
        legendas += blocos_legenda(palavras, c["destaque"], T)
        pad = np.zeros(int(dur * au.SR) - len(x), np.float32) if int(dur * au.SR) > len(x) else np.zeros(0, np.float32)
        vozes.append(np.concatenate([x, pad])[: int(dur * au.SR)])
        T += dur
    voz = np.concatenate(vozes)
    total = len(voz) / au.SR
    print(f"      duração total: {total:.1f}s")

    print("[2/4] Trilha e efeitos...")
    musica = au.trilha(total, humor, bpm)
    efeitos = np.zeros_like(voz)
    for i, c in enumerate(cenas):
        for k, nome in enumerate(c["sfx"]):
            if isinstance(nome, tuple):
                nome, dt = nome
            else:
                dt = 0.0
            s = au.sfx(nome, seed=i * 10 + k)
            a = int((starts[i] + dt) * au.SR)
            b = min(len(efeitos), a + len(s))
            efeitos[a:b] += s[: b - a]
    au.salvar_wav(os.path.join(tmp, "voz.wav"), voz)
    au.salvar_wav(os.path.join(tmp, "musica.wav"), musica)
    au.salvar_wav(os.path.join(tmp, "sfx.wav"), np.clip(efeitos, -1, 1))

    # envelope da voz por quadro (para mexer a boca)
    hop = au.SR // FPS
    nfr = int(math.ceil(len(voz) / hop))
    env = np.array([np.sqrt(np.mean(voz[i * hop:(i + 1) * hop] ** 2)) if i * hop < len(voz) else 0 for i in range(nfr)])
    env = env / (env.max() + 1e-6)

    print(f"[3/4] Renderizando quadros com {workers} processos...")
    # divide cenas em blocos contíguos de duração parecida
    alvo = total / workers
    grupos, atual, acc = [], [], 0.0
    for i, d in enumerate(durs):
        atual.append(i)
        acc += d
        if acc >= alvo and len(grupos) < workers - 1:
            grupos.append(atual)
            atual, acc = [], 0.0
    if atual:
        grupos.append(atual)
    jobs = [(cenas, g, starts, durs, env, legendas, os.path.join(tmp, f"parte{j:02d}.mp4")) for j, g in enumerate(grupos)]
    with ProcessPoolExecutor(workers) as ex:
        partes = list(ex.map(_worker, jobs))
    lista = os.path.join(tmp, "lista.txt")
    with open(lista, "w") as f:
        for p in partes:
            f.write(f"file '{p}'\n")

    print("[4/4] Mixando áudio e montando o MP4...")
    os.makedirs(os.path.dirname(os.path.abspath(saida)), exist_ok=True)
    if not narracao:
        filtro = ("[2:a]volume=0.5[m];[3:a]volume=0.9[s];"
                  "[m][s]amix=inputs=2:normalize=0,loudnorm=I=-18:TP=-2:LRA=11,aformat=channel_layouts=stereo[a]")
    else:
        filtro = (
        "[1:a]highpass=f=90,equalizer=f=2800:t=q:w=1.2:g=4,equalizer=f=200:t=q:w=1:g=2,"
        "acompressor=threshold=-20dB:ratio=3:attack=5:release=80:makeup=2,asplit=2[v][vk];"
        "[2:a]volume=0.55[m];[m][vk]sidechaincompress=threshold=0.04:ratio=8:attack=15:release=350[md];"
        "[3:a]volume=0.9[s];"
        "[v][md][s]amix=inputs=3:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=11,aformat=channel_layouts=stereo[a]"
    )
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lista,
           "-i", os.path.join(tmp, "voz.wav"), "-i", os.path.join(tmp, "musica.wav"), "-i", os.path.join(tmp, "sfx.wav"),
           "-filter_complex", filtro,
           "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", "44100",
           "-movflags", "+faststart", "-shortest", saida]
    subprocess.run(cmd, check=True)
    capa = os.path.splitext(saida)[0] + "_capa.jpg"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", str(capa_t), "-i", saida, "-frames:v", "1", "-q:v", "2", capa],
                   check=True)
    srt = os.path.splitext(saida)[0] + ".srt"
    _salvar_srt(legendas, srt)
    _salvar_roteiro(cenas, starts, durs, os.path.splitext(saida)[0] + "_roteiro.txt")
    shutil.rmtree(tmp, ignore_errors=True)
    print(f"Pronto: {saida}")
    return saida


def _ts(t):
    h, r = divmod(t, 3600)
    m, s = divmod(r, 60)
    return f"{int(h):02d}:{int(m):02d}:{int(s):02d},{int((s % 1) * 1000):03d}"


def _salvar_srt(legendas, path):
    with open(path, "w", encoding="utf-8") as f:
        for i, b in enumerate(legendas, 1):
            txt = " ".join("[BIP]" if c else w for w, _, c in b["palavras"])
            f.write(f"{i}\n{_ts(b['ini'])} --> {_ts(b['fim'])}\n{txt}\n\n")


# ======================================================================= atalhos de câmera
def close(x, y, s, z0=1.3, z1=1.45, dy=170):
    """Câmera em close no rosto do ator com pés em (x, y) e escala s."""
    hy = y - 450 * s
    return ((x, hy + dy, z0), (x, hy + dy, z1))


def plano(z0=1.0, z1=1.08, x=540, y=960, x1=None, y1=None):
    return ((x, y, z0), (x1 if x1 is not None else x, y1 if y1 is not None else y, z1))


def previa(cenas, path, t_rel=0.7, dur=4.0, cols=5):
    """Folha de contato com um quadro de cada cena (sem áudio) para revisar o enquadramento."""
    thumbs = []
    for c in cenas:
        pal = [(w, 0, 1, False) for w in re.sub(r"\[\[.*?\]\]", "", c["fala"]).split()[:3]]
        leg = blocos_legenda(pal, c["destaque"], 0)[0] if pal else None
        im = render_quadro(c, dur * t_rel, dur, 0.5, leg, 0.05)
        thumbs.append(im.resize((270, 480)))
    rows = (len(thumbs) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * 270, rows * 480), (0, 0, 0))
    for i, im in enumerate(thumbs):
        sheet.paste(im, ((i % cols) * 270, (i // cols) * 480))
    sheet.save(path)


def _mmss(t):
    return f"{int(t // 60):02d}:{t % 60:04.1f}"


def transcricao(cenas, starts, durs):
    linhas = []
    for i, (c, a, d) in enumerate(zip(cenas, starts, durs), 1):
        txt = re.sub(r"\[\[(.*?)\]\]", r"[BIP: \1]", c["fala"])
        linhas.append(f"{i:02d}. [{_mmss(a)} - {_mmss(a + d)}] {txt}")
    return "\n".join(linhas)


def _salvar_roteiro(cenas, starts, durs, path):
    with open(path, "w", encoding="utf-8") as f:
        f.write(transcricao(cenas, starts, durs) + "\n")
