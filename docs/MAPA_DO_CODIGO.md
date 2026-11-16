# Mapa do código

Gerado por `scripts/mapa_do_codigo.py` — rode de novo depois de criar, mover ou mudar arquivos.
Para ler uma função: Read com `offset` = linha e `limit` ≈ 40–80. Não leia arquivos inteiros sem necessidade.

## Pastas pesadas (binários: imagens, modelos, áudio, vídeo) — não abrir

| Pasta | Arquivos | Tamanho |
|---|---|---|
| `videos/` | 6 | 124.7 MB |
| `narracoes/` | 3 | 5.5 MB |

## Arquivos de texto/código

| Arquivo | Linhas | Tamanho |
|---|---|---|
| `gerador/__init__.py` | 1 | 0 KB |
| `gerador/alinhamento.py` | 300 | 11 KB |
| `gerador/audio.py` | 271 | 10 KB |
| `gerador/canvas.py` | 165 | 6 KB |
| `gerador/cenarios.py` | 1347 | 64 KB |
| `gerador/personagens.py` | 649 | 29 KB |
| `gerador/props.py` | 409 | 15 KB |
| `gerador/render.py` | 567 | 23 KB |
| `gerar.py` | 56 | 2 KB |
| `roteiros/__init__.py` | 1 | 0 KB |
| `roteiros/ia_dominou.py` | 135 | 9 KB |
| `roteiros/ilha_canibais.py` | 138 | 8 KB |
| `roteiros/naruto_presidente.py` | 146 | 9 KB |

Outros textos: `CLAUDE.md`, `README.md`, `videos/ia_dominou.srt`, `videos/ia_dominou_legenda_post.txt`, `videos/ia_dominou_roteiro.txt`, `videos/ilha_canibais.srt`, `videos/ilha_canibais_legenda_post.txt`, `videos/ilha_canibais_roteiro.txt`, `videos/naruto_presidente.srt`, `videos/naruto_presidente_legenda_post.txt`, `videos/naruto_presidente_roteiro.txt`

## Funções, classes e exports (linha)

### `gerador/alinhamento.py`
`carregar` 15 · `trechos_de_fala` 22 · `alinhar` 50 · `_distribuir` 85 · `palavras_nos_trechos` 96 · `real` 142 · `detectar_bips` 152 · `frases` 185 · `prever_inicios` 204 · `feats` 216 · `alinhar_frases` 241 · `prior` 251 · `mesma_cena` 263

### `gerador/audio.py`
`_get_voice` 17 · `_resample` 25 · `_limpa_tts` 34 · `tts` 39 · `trim` 54 · `bip` 63 · `narrar` 72 · `_freq` 115 · `_env` 119 · `trilha` 125 · `sfx` 196 · `salvar_wav` 253 · `duracao_guia` 265

### `gerador/canvas.py`
`font` 13 · `mix` 21 · `darker` 25 · `lighter` 29 · `Canvas` 33 · `__init__` 36 · `_p` 43 · `_w` 47 · `ellipse` 51 · `circle` 56 · `rect` 59 · `poly` 68 · `line` 78 · `arc` 86 · `chord` 95 · `pieslice` 100 · `text` 105 · `vgradient` 110 · `layer` 118 · `merge` 122 · `glow` 139 · `shade` 145 · `final` 152 · `star` 158

### `gerador/cenarios.py`
`ceu` 18 · `sol` 22 · `nuvem` 29 · `montanhas` 40 · `arvore` 50 · `arbusto` 65 · `coqueiro` 76 · `_bezier` 103 · `_leaf_pts` 108 · `folha_grande` 127 · `mar` 144 · `raios_luz` 154 · `f` 155 · `predio` 166 · `skyline` 254 · `skyline_distante` 264 · `poste` 276 · `calcada` 290 · `asfalto` 304 · `bueiro` 319 · `hidrante` 325 · `lixeira` 331 · `carro_bg` 338 · `X` 339 · `sala` 359 · `piso_madeira` 379 · `piso_ladrilho` 400 · `janela` 418 · `luz_janela` 455 · `quadro` 460 · `planta` 474 · `estante` 481 · `luminaria` 505 · `tapete` 515 · `raios_bg` 521 · `bandeira_br` 539 · `oca` 547 · `tocha` 572 · `cerca` 582 · `_bandeira` 590 · `_paulista` 603 · `_feira` 632 · `_tv_estudio` 672 · `_brasilia` 695 · `_gabinete` 736 · `_escola` 751 · `_plenario` 776 · `_cofre` 803 · `_cidade_feliz` 839 · `_estadio` 873 · `_raios_lj` 915 · `_raios_azul` 919 · `_raios_vermelho` 923 · `_raios_verde` 927 · `_escuro` 931 · `_aviao` 940 · `_mar_tempestade` 977 · `_praia` 1000 · `brilho` 1008 · `_selva` 1040 · `_aldeia` 1091 · `_aldeia_noite` 1126 · `_conves` 1130 · `_quarto` 1173 · `_quarto_noite` 1209 · `_cidade_ia` 1213 · `_rua` 1236 · `_rua_cinza` 1240 · `_porao` 1252 · `_servidores` 1290 · `fundo` 1332

### `gerador/personagens.py`
`P` 18 · `_spiky` 29 · `_cap_hair` 48 · `_curly` 62 · `_long_back` 70 · `_hair_detail` 74 · `sombra` 79 · `brilho` 85 · `_head` 93 · `sombra` 100 · `_ground_shadow` 107 · `_body_shade` 111 · `sombra` 112 · `_eyes` 121 · `_mouth` 174 · `_face_extras` 214 · `blush` 229 · `_arm` 245 · `_arms` 252 · `_torso` 287 · `_legs` 347 · `_acc_back` 371 · `_acc_head` 400 · `_acc_body` 456 · `_robot` 473 · `sprite` 527 · `figurante` 618 · `politico` 628 · `nativo` 635

### `gerador/props.py`
`_texto_censurado` 10 · `_celular` 32 · `prop` 49 · `deco` 50 · `p_celular` 57 · `p_tv` 62 · `p_placa` 77 · `p_caldeirao` 89 · `p_fogueira` 107 · `p_tigela` 120 · `p_pastel` 136 · `p_miojo` 144 · `p_navio` 154 · `p_dinheiro` 167 · `p_portal` 177 · `p_bandeira` 192 · `p_laptop` 206 · `p_loading` 219 · `p_olho` 231 · `p_carro` 241 · `p_semaforo` 254 · `p_lampada` 264 · `p_relogio` 276 · `p_balao` 288 · `p_briga` 303 · `p_estrelas` 322 · `p_simbolo` 333 · `p_texto` 339 · `p_bolacha` 348 · `p_pegadas` 359 · `p_urna` 369 · `p_drone` 380 · `_render` 393 · `sprite_prop` 400 · `tamanho` 406

### `gerador/render.py`
`A` 27 · `Pr` 34 · `Cena` 40 · `ease` 47 · `_pop` 52 · `_fundo_borrado` 61 · `_vinheta` 67 · `_sprite_ator` 77 · `_cam` 82 · `_limpa` 104 · `blocos_legenda` 108 · `_img_legenda` 142 · `_desenha_legenda` 176 · `_pos` 186 · `render_quadro` 211 · `_ffmpeg_writer` 283 · `_worker` 290 · `_palavras_no_grupo` 313 · `_tempos_da_gravacao` 350 · `gerar` 409 · `_ts` 513 · `_salvar_srt` 519 · `close` 527 · `plano` 533 · `previa` 537 · `_mmss` 552 · `transcricao` 556 · `_salvar_roteiro` 564

### `gerar.py`
`main` 26

