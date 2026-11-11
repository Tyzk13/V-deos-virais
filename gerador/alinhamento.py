"""Alinha uma narração gravada (ex.: ElevenLabs) com as cenas do roteiro.

Sem reconhecimento de fala: detecta os trechos de fala separados por pausas e escolhe, por programação
dinâmica, quais pausas são as fronteiras entre cenas, comparando a duração de cada grupo de trechos
com a duração esperada da cena (medida com a voz-guia sintética, que fala o mesmo texto).
"""
import math
import subprocess

import numpy as np

SR = 44100


def carregar(path):
    """Decodifica qualquer áudio para float32 mono 44.1 kHz."""
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-f", "f32le", "-ac", "1", "-ar", str(SR), "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).copy()


def trechos_de_fala(x, limiar_db=-38, min_silencio=0.3, min_fala=0.12):
    """Lista de (inicio, fim) em segundos dos trechos com fala."""
    hop = int(0.01 * SR)
    n = len(x) // hop
    rms = np.sqrt(np.mean(x[: n * hop].reshape(n, hop) ** 2, axis=1) + 1e-12)
    db = 20 * np.log10(rms / (rms.max() + 1e-9))
    fala = db > limiar_db
    segs = []
    i = 0
    while i < n:
        if fala[i]:
            j = i
            while j < n and fala[j]:
                j += 1
            segs.append([i * 0.01, j * 0.01])
            i = j
        else:
            i += 1
    # junta trechos separados por pausas curtas
    out = []
    for s in segs:
        if out and s[0] - out[-1][1] < min_silencio:
            out[-1][1] = s[1]
        else:
            out.append(s)
    return [tuple(s) for s in out if s[1] - s[0] >= min_fala]


def alinhar(trechos, duracoes_guia):
    """Agrupa os trechos em len(duracoes_guia) cenas consecutivas.

    Retorna lista de (primeiro_trecho, ultimo_trecho_exclusivo) por cena.
    """
    N, S = len(trechos), len(duracoes_guia)
    if N < S:
        raise ValueError(f"A narração tem só {N} trechos de fala para {S} cenas. "
                         "Confira se o áudio é do roteiro certo ou se há pausas entre as frases.")
    fala_total = sum(b - a for a, b in trechos)
    escala = (trechos[-1][1] - trechos[0][0]) / max(1e-6, sum(duracoes_guia))
    INF = float("inf")
    custo = [[INF] * (N + 1) for _ in range(S + 1)]
    volta = [[0] * (N + 1) for _ in range(S + 1)]
    custo[0][0] = 0.0
    for s in range(1, S + 1):
        alvo = duracoes_guia[s - 1] * escala
        for j in range(s, N - (S - s) + 1):
            for i in range(s - 1, j):
                if custo[s - 1][i] == INF:
                    continue
                dur = trechos[j - 1][1] - trechos[i][0]
                c = custo[s - 1][i] + math.log(max(dur, 0.05) / max(alvo, 0.05)) ** 2
                if c < custo[s][j]:
                    custo[s][j] = c
                    volta[s][j] = i
    grupos = []
    j = N
    for s in range(S, 0, -1):
        i = volta[s][j]
        grupos.append((i, j))
        j = i
    return grupos[::-1]


def _distribuir(palavras, a, b):
    pesos = [len(w) + 2 for w in palavras]
    tot = sum(pesos)
    out, acc = [], 0
    for w, p in zip(palavras, pesos):
        ini = a + (b - a) * acc / tot
        acc += p
        out.append((w, ini, a + (b - a) * acc / tot))
    return out


def palavras_nos_trechos(texto_palavras, trechos):
    """Distribui as palavras de uma cena pelos trechos de fala dela.

    Quebra o texto em frases na pontuação e encaixa cada grupo de frases num trecho de fala
    (programação dinâmica pela duração). Se não der, distribui proporcionalmente ignorando as pausas.
    Retorna [(palavra, ini, fim)].
    """
    frases, atual = [], []
    for w in texto_palavras:
        atual.append(w)
        if w[-1] in ".,!?:;…":
            frases.append(atual)
            atual = []
    if atual:
        frases.append(atual)
    N, F = len(trechos), len(frases)
    if N == 1:
        return _distribuir(texto_palavras, *trechos[0])
    if F >= N:
        chars = [sum(len(w) + 1 for w in f) for f in frases]
        taxa = sum(b - a for a, b in trechos) / sum(chars)
        INF = float("inf")
        custo = [[INF] * (F + 1) for _ in range(N + 1)]
        volta = [[0] * (F + 1) for _ in range(N + 1)]
        custo[0][0] = 0
        for t in range(1, N + 1):
            d = trechos[t - 1][1] - trechos[t - 1][0]
            for j in range(t, F - (N - t) + 1):
                for i in range(t - 1, j):
                    if custo[t - 1][i] == INF:
                        continue
                    c = custo[t - 1][i] + math.log(d / (taxa * sum(chars[i:j]))) ** 2
                    if c < custo[t][j]:
                        custo[t][j], volta[t][j] = c, i
        cortes, j = [], F
        for t in range(N, 0, -1):
            i = volta[t][j]
            cortes.append((i, j))
            j = i
        out = []
        for (i, j), (a, b) in zip(cortes[::-1], trechos):
            out += _distribuir([w for f in frases[i:j] for w in f], a, b)
        return out
    # menos frases que trechos: distribui no "tempo de fala" (sem as pausas)
    fala = sum(b - a for a, b in trechos)

    def real(tf):
        acc = 0.0
        for a, b in trechos:
            if tf <= acc + (b - a) + 1e-9:
                return a + (tf - acc)
            acc += b - a
        return trechos[-1][1]
    return [(w, real(a), real(b)) for w, a, b in _distribuir(texto_palavras, 0.0, fala)]


def detectar_bips(x, freq=1000, min_dur=0.12):
    """Acha bips (tom puro perto de `freq` Hz) já presentes na gravação. Retorna [(ini, fim)]."""
    win = int(0.02 * SR)
    n = len(x) // win
    f = np.fft.rfftfreq(win * 2, 1 / SR)
    banda = (f > freq * 0.9) & (f < freq * 1.1)
    marc = np.zeros(n, bool)
    rms_max = np.sqrt(np.mean(x ** 2)) * 4 + 1e-9
    for i in range(n):
        seg = x[i * win:(i + 1) * win]
        sp = np.abs(np.fft.rfft(seg * np.hanning(win), win * 2)) ** 2
        tot = sp.sum() + 1e-12
        energia = np.sqrt(np.mean(seg ** 2))
        marc[i] = sp[banda].sum() / tot > 0.6 and energia > rms_max * 0.05
    out = []
    i = 0
    while i < n:
        if marc[i]:
            j = i
            while j < n and (marc[j] or (j + 1 < n and marc[j + 1])):
                j += 1
            if (j - i) * 0.02 >= min_dur:
                out.append((i * 0.02, j * 0.02))
            i = j
        else:
            i += 1
    return out
