#!/usr/bin/env python3
"""Семь слайдов для защиты проекта Walkback Envelope.

Формат 16:9, 1920x1080, тёмная тема под проектор. Только английский.
Каждый кадр приложения вставляется ОБРЕЗАННЫМ по значимой области —
целиком вставленный скриншот 1680x945 на слайде нечитаем.

Правило: ни одно число на слайдах не правится «для красоты». Все значения
взяты из прогонов приложения и из test-physics.mjs.
"""
from PIL import Image, ImageDraw, ImageFont
import os

W, H = 1920, 1080
BG      = (9, 11, 15)
PANEL   = (16, 19, 25)
LINE    = (38, 44, 54)
TX      = (232, 236, 242)
DIM     = (150, 158, 170)
DIM2    = (104, 112, 124)
GO      = (46, 230, 168)
CAUTION = (255, 194, 71)
ABORT   = (255, 77, 94)
ACCENT  = (255, 122, 69)

SHOTS = '/root/work/slides/shots'
OUT   = '/root/work/slides/out'
os.makedirs(OUT, exist_ok=True)

def font(sz, bold=False):
    paths = ([ '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
               '/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf' ]
             if bold else
             [ '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
               '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf' ])
    for p in paths:
        if os.path.exists(p):
            return ImageFont.truetype(p, sz)
    return ImageFont.load_default()

def mono(sz):
    for p in ['/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf',
              '/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf']:
        if os.path.exists(p):
            return ImageFont.truetype(p, sz)
    return font(sz)


# ─────────────────── Движок компоновки ───────────────────
# Все прямоугольники регистрируются; пересечение = ошибка сборки.
# Прежние слайды верстались «на глаз», и блок пояснения налезал
# на карточку схемы, а подписи уезжали за край.
class Layout:
    def __init__(s, d):
        s.d = d; s.boxes = []; s.containers = []
    def _reg(s, box, what):
        x0,y0,x1,y1 = box
        if x0 < 60 or y0 < 128 or x1 > W-60 or y1 > H-40:
            raise AssertionError(f'{what}: выходит за поля {box}')
        for cb, _ in s.containers:          # внутри панели — законно
            if cb[0] <= x0 and cb[1] <= y0 and x1 <= cb[2] and y1 <= cb[3]:
                return
        for b, w2 in s.boxes:
            if not (x1 <= b[0] or b[2] <= x0 or y1 <= b[1] or b[3] <= y0):
                raise AssertionError(f'НАЛОЖЕНИЕ: "{what}" на "{w2}"  {box} vs {b}')
        s.boxes.append((box, what))
    def text(s, xy, txt, f, fill, what='text', lead=None):
        """Многострочный текст с измерением. Возвращает нижнюю границу."""
        lines = txt.split('\n') if isinstance(txt, str) else list(txt)
        lead = lead or int(f.size * 1.45)
        wmax = 0
        for ln in lines:
            bb = s.d.textbbox((0,0), ln, font=f)
            wmax = max(wmax, bb[2]-bb[0])
        h = lead*(len(lines)-1) + int(f.size*1.25)
        s._reg((xy[0], xy[1], xy[0]+wmax, xy[1]+h), what)
        for i, ln in enumerate(lines):
            s.d.text((xy[0], xy[1]+i*lead), ln, font=f, fill=fill)
        return xy[1] + h
    def panel(s, box, what, fill=None, outline=None):
        # Панель — КОНТЕЙНЕР: регистрируем её границы, но текст внутри
        # не считается наложением (он для того туда и кладётся).
        s._reg(box, what)
        s.boxes.pop()                       # снимаем с учёта как препятствие
        s.containers.append((box, what))
        s.d.rectangle(box, fill=fill, outline=outline)
    def img(s, im_, img, xy, what, label=None, lf=None):
        box = (xy[0], xy[1], xy[0]+img.width, xy[1]+img.height)
        s._reg(box, what)
        im_.paste(img, xy)
        s.d.rectangle([box[0]-1, box[1]-1, box[2], box[3]], outline=LINE, width=1)
        if label:
            s.text((xy[0], box[3]+10), label, lf or mono(16), DIM2, what+' label')
        return box[3]

def base(n, kicker, title, sub=None):
    im = Image.new('RGB', (W, H), BG)
    d  = ImageDraw.Draw(im)
    d.line([(0, 118), (W, 118)], fill=LINE, width=1)
    d.text((72, 46), kicker, font=mono(19), fill=ACCENT)
    d.text((W - 96, 44), f'{n}/7', font=mono(21), fill=DIM2, anchor='ra')
    d.text((72, 150), title, font=font(54, True), fill=TX)
    if sub:
        d.text((72, 222), sub, font=font(25), fill=DIM)
    return im, d

def crop(path, box, size):
    """box = (left, top, right, bottom) в долях исходника"""
    im = Image.open(path).convert('RGB')
    w, h = im.size
    c = im.crop((int(box[0]*w), int(box[1]*h), int(box[2]*w), int(box[3]*h)))
    c.thumbnail(size, Image.LANCZOS)
    return c

def paste(im, d, img, xy, label=None):
    im.paste(img, xy)
    d.rectangle([xy[0]-1, xy[1]-1, xy[0]+img.width, xy[1]+img.height],
                outline=LINE, width=1)
    if label:
        d.text((xy[0], xy[1] + img.height + 11), label, font=mono(16), fill=DIM2)

def bullet(d, x, y, text, col=TX, sz=26, gap=42):
    for i, ln in enumerate(text):
        d.ellipse([x, y + i*gap + sz//2 - 3, x + 6, y + i*gap + sz//2 + 3], fill=ACCENT)
        d.text((x + 22, y + i*gap), ln, font=font(sz), fill=col)

# ───────────────────────────── 1. Титул ─────────────────────────────
im, d = base(1, 'TEAM ORDINATUM · NASA SPACE APPS CHALLENGE 2026 · URALSK',
             'Can the astronaut still walk home?',
             'A return-capability map for a Mars EVA, computed over real terrain')
# приложение целиком: карта и панель вердикта вместе
g = crop(f'{SHOTS}/s1_hero.png', (0.012, 0.085, 0.995, 0.90), (1240, 700))
paste(im, d, g, (72, 286), 'Jezero Crater · EVA elapsed 02:30 · live model, nothing staged')
x = 1360
d.text((x, 292), 'THE QUESTION', font=mono(17), fill=DIM2)
for i, ln in enumerate(['An astronaut 4 km out',
                        'has one decision:',
                        'turn back, or keep going.']):
    d.text((x, 326 + i*34), ln, font=font(24), fill=TX)
d.text((x, 452), 'WHAT THE TOOL ANSWERS', font=mono(17), fill=DIM2)
for i, ln in enumerate(['Can I still reach the',
                        'habitat from here —',
                        'and which consumable',
                        'runs out first?']):
    d.text((x, 486 + i*34), ln, font=font(24), fill=GO)
d.text((x, 650), 'A concept demonstrator,', font=font(21), fill=CAUTION)
d.text((x, 678), 'not flight software.', font=font(21), fill=CAUTION)
d.line([(x, 724), (W-96, 724)], fill=LINE)
d.text((x, 746), 'Challenge: route planning', font=font(19), fill=DIM)
d.text((x, 772), 'across the Martian surface', font=font(19), fill=DIM)
d.text((72, 1024), 'ordinatum.github.io/walkback-envelope', font=mono(26), fill=ACCENT)
im.save(f'{OUT}/slide1.png')

# ─────────────────── 2. Настоящий рельеф, принятая миссия ───────────────────
im, d = base(2, 'INPUTS', 'Real terrain, assumed mission',
             'Four actual Mars sites from the USGS MOLA + HRSC blended DEM, 200 m/px')
a = crop(f'{SHOTS}/s2_melas.png',   (0.015, 0.10, 0.52, 0.86), (700, 620))
b = crop(f'{SHOTS}/s2_elysium.png', (0.015, 0.10, 0.52, 0.86), (700, 620))
paste(im, d, a, (72, 300),  'MELAS CHASMA · relief 3261 m · 11 % of cells over 25°')
paste(im, d, b, (820, 300), 'ELYSIUM PLANITIA · relief 61 m · max slope 1.7°')
d.text((1580, 300), 'OBSERVED', font=mono(18), fill=GO)
for i, ln in enumerate(['Elevation — USGS/NASA/DLR',
                        'blended DEM, 200 m/px',
                        'Dose baseline — MSL RAD',
                        'Basemap — NASA Trek']):
    d.text((1580, 338 + i*32), ln, font=font(20), fill=TX)
d.text((1580, 490), 'ASSUMED', font=mono(18), fill=CAUTION)
for i, ln in enumerate(['Suit capacities',
                        'Weather scenarios',
                        'Shelter locations',
                        'Metabolic model']):
    d.text((1580, 528 + i*32), ln, font=font(20), fill=DIM)
d.text((72, 952),
       'Same settings, same clock, havens off. The envelope is pinned along the valley '
       'on Melas and near-circular on the plain —',
       font=font(23), fill=TX)
d.text((72, 990), 'the shape comes from the terrain, not from the drawing.',
       font=font(23), fill=GO)
im.save(f'{OUT}/slide2.png')

# ─────────────────── 3. Как бюджет становится картой ───────────────────
im, d = base(3, 'METHOD', 'How a consumable budget becomes a map',
             'One reverse Dijkstra from the habitat drives the verdict, the PNR and the envelope')
L = Layout(d)
# четыре карточки конвейера — во всю ширину, ниже подзаголовка
bx, by, bw, bh = 72, 300, 404, 158
steps = [('REAL TERRAIN',     ['84 x 84 grid, 298 m cells', 'slope per edge, 16 directions']),
         ('COST PER EDGE',    ['Pandolf adapted to 0.38 g', 'water / CO2 / battery / O2']),
         ('REVERSE DIJKSTRA', ['cost to walk home', 'from every cell']),
         ('COMPARE',          ['remaining minus return need', 'against the 25 % reserve'])]
for k, (h, body) in enumerate(steps):
    x = bx + k*(bw + 24)
    L.panel((x, by, x+bw, by+bh), f'card{k}', fill=PANEL, outline=LINE)
    d.text((x+20, by+20), h, font=mono(19), fill=ACCENT)
    for q, ln in enumerate(body):
        d.text((x+20, by+58 + q*30), ln, font=font(20), fill=TX)
    if k < 3:
        d.text((x+bw+4, by+bh//2-18), '>', font=font(28, True), fill=DIM2)
# левая колонка: каналы
L.text((72, 510), 'FOUR CHANNELS IN PHYSICAL UNITS', mono(19), DIM2, 'ch head')
for k, (nm, cap) in enumerate([('Cooling water','5.6 kg'), ('CO2 scrubber','640 g'),
                               ('Battery','1100 Wh'), ('Oxygen','560 g')]):
    L.text((72, 556 + k*50), nm, font(25), TX, f'chn{k}')
    L.text((400, 556 + k*50), cap, mono(25), GO, f'chv{k}')
L.text((72, 790),
       'The verdict names the limiting one.\nRadiation is a separate abort channel —\nfull tanks do not cancel a dose warning.',
       font(23), TX, 'ch note')
# правая колонка: оговорка про приближение — ПОД карточками, не поверх
L.panel((900, 510, W-72, 700), 'approx', fill=PANEL, outline=CAUTION)
L.text((924, 530), 'THE APPROXIMATION WE ACCEPT', mono(18), CAUTION, 'approx head')
L.text((924, 566),
       '298 m cells, 16 travel directions\n'
       'about 2.7 % directional distance error\n'
       'summed edge costs, not a geodesic solver',
       font(21), DIM, 'approx body')
L.text((900, 730), 'RESERVE POLICY', mono(18), DIM2, 'res head')
L.text((900, 766),
       '25 % of each channel\u2019s initial capacity.\n'
       'Breaching it is the abort condition —\n'
       'not running the tank dry.',
       font(21), TX, 'res body')
im.save(f'{OUT}/slide3.png')

# ─────────────────── 4. Реальное решение о возврате ───────────────────
im, d = base(4, 'DEMONSTRATION', 'One EVA, three decisions',
             'Jezero Crater, 1.7 km/h, nominal scenario — the envelope contracts as the suit empties')
seq = [('s4_early', '01:00 · GO',          'envelope wide, 1.7 km out',  GO),
       ('s4_pnr',   '04:00 · PNR PASSED',  'outbound deadline expired',  CAUTION),
       ('s4_home',  '05:58 · EVA COMPLETE','home, 1.8 kg water left',    GO)]
for i, (f, tag, cap, col) in enumerate(seq):
    g = crop(f'{SHOTS}/{f}.png', (0.015, 0.11, 0.53, 0.80), (560, 500))
    x = 72 + i*(560 + 34)
    paste(im, d, g, (x, 300))
    d.text((x, 816), tag, font=mono(24), fill=col)
    d.text((x, 850), cap, font=font(21), fill=DIM)
d.rectangle([72, 908, W-96, 1030], fill=PANEL, outline=CAUTION)
d.text((96, 926), 'WHAT "PNR PASSED" MEANS HERE', font=mono(18), fill=CAUTION)
d.text((96, 958),
       'It is a hypothetical outbound deadline — the last minute you could keep walking away. '
       'The executed plan turns back at the target,',
       font=font(21), fill=TX)
d.text((96, 992),
       'so the astronaut passes it and still walks home above reserve. It is not a certified '
       'point of no return on this plan.',
       font=font(21), fill=TX)
im.save(f'{OUT}/slide4.png')

# ─────────────────── 5. Радиация — независимый канал ───────────────────
im, d = base(5, 'INDEPENDENT ABORT CHANNEL', 'Full tanks do not cancel radiation',
             'Solar particle event: consumables are fine, the verdict is still an abort')
L = Layout(d)
# приложение целиком — видно и карту, и вердикт SHELTER UNREACHABLE
# Карта и ПАНЕЛЬ ВЕРДИКТА — двумя отдельными кадрами: втиснутый целиком
# интерфейс 1680 px в 1150 делает текст панели нечитаемым с проектора.
gm = crop(f'{SHOTS}/s5_spe.png', (0.015, 0.09, 0.56, 0.84), (620, 560))
L.img(im, gm, (72, 292), 'spe map', 'SOLAR FLARE (SPE) · EVA elapsed 03:05')
gv = crop(f'{SHOTS}/s5_spe.png', (0.7786, 0.0397, 0.9923, 0.5205), (470, 620))
L.img(im, gv, (740, 292), 'spe verdict', 'Verdict panel, unretouched')
x = 1270
L.text((x, 300), 'SOURCED', mono(18), GO, 'src head')
L.text((x, 334), '0.0267 mSv/h\nMSL RAD, Gale crater', font(21), TX, 'src body')
L.text((x, 418), 'ASSUMED BY US', mono(18), CAUTION, 'asm head')
L.text((x, 452), 'x80 flux multiplier\n45 min warning lead\n3 mSv abort threshold',
       font(21), DIM, 'asm body')
L.panel((x, 560, W-72, 790), 'thr', fill=PANEL, outline=CAUTION)
L.text((x+20, 580), 'THE 3 mSv THRESHOLD IS OURS', mono(17), CAUTION, 'thr head')
L.text((x+20, 616),
       'Not a NASA limit. NASA states\n'
       'blood-forming organ limits in\n'
       'mGy-Eq; equivalent and effective\n'
       'dose are not interchangeable.',
       font(19), TX, 'thr body')
L.text((72, 960),
       'Every channel is above its reserve — cooling water, the tightest one, still holds 3.65 of 5.6 kg.\n'
       'The abort comes from radiation alone: the proton flux arrives before shelter can be reached.',
       font(23), TX, 'foot', lead=36)
im.save(f'{OUT}/slide5.png')

# ─────────────────── 6. Что проверено и что нет ───────────────────
im, d = base(6, 'VERIFICATION', 'What we tested — and what we did not',
             'Twelve invariants over 288 configurations, plus the deviations we declare')
L = Layout(d)
L.text((72, 300), 'VERIFIED BY MACHINE', mono(19), GO, 'v head')
L.text((96, 340),
       'Consumables never increase, dose never decreases\n'
       'A deficit always implies a breached reserve\n'
       'PNR does not depend on the time slider\n'
       'Walkback time never beats distance / pace\n'
       'Return cost from the habitat is exactly zero\n'
       'Havens never shrink the envelope',
       font(22), TX, 'v body', lead=36)
L.text((72, 594), 'WHAT THAT HARNESS CAUGHT', mono(19), ACCENT, 'f head')
L.text((96, 634),
       'A render crash in every flare scenario\n'
       'A sweep silently testing one pace as three\n'
       'A PNR marker 783 m from its own computation',
       font(22), TX, 'f body', lead=36)
x = 1010
L.text((x, 300), 'DECLARED DEVIATIONS', mono(19), CAUTION, 'd head')
yy = 340
for h, body in [('Metabolism 225.7 W at 1.7 km/h',
                 'below our 300-500 W design target. If real\ncost is higher, the envelope is too wide\nand the PNR too late.'),
                ('Terrain shielding only about 3 %',
                 'at 200 m/px the canyon walls are smoothed;\na real canyon would shield far more.'),
                ('Safe Havens are hypothetical',
                 'not mapped infrastructure; caches are\nassumed values showing the mechanism.')]:
    yy = L.text((x, yy), h, font(23, True), TX, 'dev '+h[:12]) + 6
    yy = L.text((x, yy), body, font(19), DIM, 'devb '+h[:12], lead=28) + 26
L.panel((72, 884, W-72, 1016), 'nm', fill=PANEL, outline=LINE)
L.text((96, 902), 'NOT MODELLED AT ALL', mono(17), DIM2, 'nm head')
L.text((96, 934),
       'Metre-scale hazards (boulders, fissures) — needs HiRISE or CTX DTM  ·  teleoperation delay  ·  surface type under the boot\n'
       'Passing regression tests does not validate the physiology: the arithmetic is checked, the metabolic model is not flight-validated.',
       font(19), DIM, 'nm body', lead=30)
im.save(f'{OUT}/slide6.png')

# ─────────────────── 7. Доступ, источники, раскрытие ───────────────────
im, d = base(7, 'ACCESS AND ATTRIBUTION', 'Try it, and check our sources')
L = Layout(d)
L.text((72, 272), 'LIVE DEMO', mono(19), DIM2, 'demo head')
L.text((72, 308), 'ordinatum.github.io/walkback-envelope', mono(32), GO, 'demo url')
L.text((72, 360), 'No login, no install. One HTML file — works offline once loaded.',
       font(21), DIM, 'demo note')
L.text((72, 428), 'SOURCE', mono(19), DIM2, 'src head')
L.text((72, 464), 'github.com/ordinatum/walkback-envelope', mono(28), ACCENT, 'src url')
L.text((72, 512), 'MIT licence · the README documents every assumption and known limit',
       font(21), DIM, 'src note')
L.text((72, 586), 'DATA AND TOOLS', mono(19), DIM2, 'data head')
L.text((96, 624),
       'Terrain — USGS/NASA/DLR, Mars MGS MOLA + MEX HRSC Blended DEM, 200 m/px\n'
       'Context basemap — NASA Trek MOLA colour-shade tiles\n'
       'Dose baseline — MSL RAD, Gale crater surface measurements\n'
       'Metabolic scale reference — NASA Apollo lunar-EVA metabolic report\n'
       'Tools — GDAL, Python 3, Node.js, plain HTML and Canvas (no frameworks)',
       font(21), TX, 'data body', lead=34)
L.panel((1108, 272, W-72, 530), 'ai', fill=PANEL, outline=CAUTION)
L.text((1132, 292), 'AI ASSISTANCE — DISCLOSED', mono(18), CAUTION, 'ai head')
L.text((1132, 330),
       'Built with Claude and OpenAI Codex for\n'
       'code, physics derivation, independent\n'
       'review and documentation. Every defect\n'
       'fix was verified in-browser against the\n'
       'running application.\n\n'
       'NASA Space Apps requires this disclosure.',
       font(20), TX, 'ai body', lead=29)
L.panel((1108, 570, W-72, 830), 'what', fill=PANEL, outline=GO)
L.text((1132, 590), 'WHAT IS DEMONSTRATED', mono(18), GO, 'what head')
L.text((1132, 628),
       'Real Mars terrain drives a return-\n'
       'capability map that contracts as the\n'
       'suit empties, names the limiting\n'
       'consumable, and treats radiation as an\n'
       'independent abort channel.\n\n'
       'A concept demonstrator, not flight software.',
       font(20), TX, 'what body', lead=29)
L.text((72, 938), 'Team ordinatum', mono(22), TX, 'team name')
L.text((72, 976), 'Captain: Alexander Kornienko · alex226019@gmail.com', font(21), DIM, 'team')
im.save(f'{OUT}/slide7.png')

print('слайды собраны:')
for i in range(1, 8):
    p = f'{OUT}/slide{i}.png'
    print(f'  {p}  {os.path.getsize(p)//1024} KB')
