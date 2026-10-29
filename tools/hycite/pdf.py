"""PDF 'Compras HyCite México por año' (carta horizontal, 2 páginas) a partir de data.json.

Uso:  python3 pdf.py [--data data.json] [--out <archivo.pdf>]
Por defecto escribe ../../p/crecimiento-hycite/pdf/Compras_HyCite_CHASEP_13588_MEJAB_29365_<cutDate>.pdf
y una copia fija ../../p/crecimiento-hycite/pdf/ultimo.pdf. Imprime JSON con cifras clave y la ruta.
Cifras: COMPRAS en USD (no ventas, no pesos).
"""
import argparse, json, os, shutil, tempfile
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from reportlab.lib.pagesizes import letter, landscape
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor, white
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
ap = argparse.ArgumentParser()
ap.add_argument("--data", default=os.path.join(HERE, "data.json"))
ap.add_argument("--out", default=None)
args = ap.parse_args()
ALL = json.load(open(args.data)); D = ALL["years"]; Y = int(ALL["current"]); d = D[str(Y)]

# ---------- fuentes (Poppins si existe; si no, DejaVu) ----------
GF = "/usr/share/fonts/truetype/google-fonts/"; DV = "/usr/share/fonts/truetype/dejavu/"
if os.path.exists(GF + "Poppins-Regular.ttf"):
    F = {"P": GF + "Poppins-Regular.ttf", "PM": GF + "Poppins-Regular.ttf", "PS": GF + "Poppins-Medium.ttf", "PB": GF + "Poppins-Bold.ttf"}; FAM = "Poppins"
else:
    F = {"P": DV + "DejaVuSans.ttf", "PM": DV + "DejaVuSans.ttf", "PS": DV + "DejaVuSans-Bold.ttf", "PB": DV + "DejaVuSans-Bold.ttf"}; FAM = "DejaVu Sans"
for n, f in F.items(): pdfmetrics.registerFont(TTFont(n, f))
for f in set(F.values()): font_manager.fontManager.addfont(f)
plt.rcParams["font.family"] = FAM

NAVY = "#121033"; BLUE = "#1B3F8B"; GREEN = "#0F7B6C"; INK = "#131235"; MUTED = "#5F6480"
LINE = "#DDE2EE"; BG = "#EEF1F7"; GOOD = "#0F7B4F"; BAD = "#B42318"; GOLD = "#B07A2A"
MES = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
MESL = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]

def M(v, dec=2): return f"{v/1e6:,.{dec}f} M USD"
def Ms(v, dec=2): return f"{v/1e6:,.{dec}f} M"
def P(v): return "—" if v is None else f"{v*100:+.1f}%"
def money(v): return f"US${v:,.0f}"
def sgn(v): return ("+" if v >= 0 else "−") + f"{abs(v)/1e6:,.2f} M"

# ---------- periodo actual ----------
cur = d["cur"]; cutDay = d["cutDay"]; OPEN = cutDay != 1
nclosed = cur if OPEN else cur + 1           # meses cerrados del año en curso
cd = d["cutDate"]; cdd, cmm = int(cd[8:10]), int(cd[5:7])
CUTLBL = f"{cdd}-{MES[cmm-1].lower()}"         # 20-oct
CUTLBL_Y = f"{CUTLBL}-{Y}"
rng = (f"{MES[0]}–{MES[nclosed-1]}" if nclosed > 1 else MES[0]) if nclosed else ""
FULLYEAR = (not OPEN) and cur == 11
nat = d["nat"]
ytd, ytd_prev = nat["y"][1], nat["y"][0]
cs = sum(nat["m26"][:nclosed]); cs_prev = sum(nat["m25"][:nclosed])
g_cl = (cs / cs_prev - 1) if nclosed and cs_prev else None
prev = D.get(str(Y - 1)); fy_prev = prev["nat"]["y"][1] if prev else ytd_prev
prev_months = prev["nat"]["m26"] if prev else nat["m25"]

part_proj = None; avgp = None; pct_months = []
if OPEN:
    key = f"d{cutDay}"; arr = nat.get(key) or []
    for i in range(cur - 1, -1, -1):
        if i < len(arr) and arr[i] and nat["m26"][i]:
            pct_months.append(i)
        if len(pct_months) == 3: break
    if pct_months:
        avgp = sum(arr[i] / nat["m26"][i] for i in pct_months) / len(pct_months)
        part_proj = nat["m26"][cur] / avgp
proj = None
if FULLYEAR:
    proj = ytd
elif g_cl is not None and (part_proj is not None or not OPEN):
    rest = sum(prev_months[cur + 1:]) * (1 + g_cl)
    proj = cs + (part_proj or 0) + rest

# ---------- historia anual ----------
yrs_all = sorted(int(y) for y in D)
F0 = yrs_all[0]
ann = [(F0 - 1, D[str(F0)]["nat"]["y"][0], None, None)]
for y in yrs_all:
    if y == Y: continue
    n = D[str(y)]["nat"]; ann.append((y, n["y"][1], n["y"][0], n["y"][1] / n["y"][0] - 1))
closed_years = [a for a in ann]
best = max(closed_years, key=lambda a: a[1])

monthly = {F0 - 1: D[str(F0)]["nat"]["m25"]}
for y in yrs_all:
    mv = D[str(y)]["nat"]["m26"]
    monthly[y] = mv if y != Y else (mv[: cur + 1] + [None] * (11 - cur))
totals = {F0 - 1: D[str(F0)]["nat"]["y"][0]}
for y in yrs_all: totals[y] = D[str(y)]["nat"]["y"][1]

# ---------- CHASEP / MEJAB ----------
def rank(y, tid):
    T = sorted([t for t in D[str(y)]["T"] if t["id"] != "OTROS"], key=lambda t: -t["y"][1])
    for i, t in enumerate(T, 1):
        if t["id"] == tid: return i, len(T)
    return None, len(T)
cm = []
for y in yrs_all:
    by = {t["id"]: t for t in D[str(y)]["T"]}
    tc, tm = by.get("13588"), by.get("29365")
    if not tc: continue
    c_ = tc["y"][1]; m_ = tm["y"][1] if tm else None
    tot = c_ + (m_ or 0); base = tc["y"][0] + (tm["y"][0] if tm else 0)
    if y == Y and nclosed:
        sb = sum(tc["b"][:nclosed]) + (sum(tm["b"][:nclosed]) if tm else 0)
        sa = sum(tc["a"][:nclosed]) + (sum(tm["a"][:nclosed]) if tm else 0)
        g = sb / sa - 1 if sa else None
        gc = sum(tc["b"][:nclosed]) / sum(tc["a"][:nclosed]) - 1 if sum(tc["a"][:nclosed]) else None
        gm = (sum(tm["b"][:nclosed]) / sum(tm["a"][:nclosed]) - 1) if tm and sum(tm["a"][:nclosed]) else None
    else:
        g = tot / base - 1 if base else None; gc = gm = None
    rc, nT = rank(y, "13588"); rm = rank(y, "29365")[0] if tm else None
    cm.append(dict(y=y, c=c_, m=m_, tot=tot, g=g, gc=gc, gm=gm, share=tot / D[str(y)]["nat"]["y"][1], rc=rc, rm=rm, nT=nT))
cm = cm[-8:]

restat = []
for y in yrs_all[:-1]:
    nx = D[str(y + 1)]
    if not (nx["cutDay"] == 1 and nx["cur"] == 11): continue   # solo contra cierres anuales completos
    a = D[str(y)]["nat"]["y"][1]; b = nx["nat"]["y"][0]
    if abs(b - a) >= 1000: restat.append((y, b - a))

# ---------- salida ----------
OUTDIR = os.path.join(ROOT, "p", "crecimiento-hycite", "pdf")
OUT = args.out or os.path.join(OUTDIR, f"Compras_HyCite_CHASEP_13588_MEJAB_29365_{cd}.pdf")
os.makedirs(os.path.dirname(os.path.abspath(OUT)), exist_ok=True)
TMP = tempfile.mkdtemp()

# gráfica anual
W, H = landscape(letter)
ky = H - 140; PW = 430; PH = ky - 48 - 36
fig, ax = plt.subplots(figsize=((PW - 16) / 72, (PH - 46) / 72), dpi=220)
labels = [str(a[0]) for a in ann] + [f"{Y}\nal {CUTLBL}" if not FULLYEAR else str(Y)]
vals = [a[1] / 1e6 for a in ann] + [ytd / 1e6]
n = len(vals); colsb = ["#9AA7C7"] * (n - 1) + [BLUE]
pk = max(range(n - 1), key=lambda i: vals[i]); colsb[pk] = NAVY
bars = ax.bar(range(n), vals, color=colsb, width=0.62, zorder=3)
top = max(vals + [(proj or 0) / 1e6])
if proj and not FULLYEAR and proj > ytd:
    ax.bar([n - 1], [(proj - ytd) / 1e6], bottom=[ytd / 1e6], color="none", edgecolor=BLUE, hatch="////", linewidth=0.8, width=0.62, zorder=3)
    ax.text(n - 1, proj / 1e6 + top * 0.015, f"proy. {proj/1e6:,.1f}", ha="center", fontsize=6.5, color=BLUE)
for k, (b, v) in enumerate(zip(bars, vals)):
    last = k == n - 1 and not FULLYEAR and proj
    ax.text(b.get_x() + b.get_width() / 2, v - top * 0.028 if last else v + top * 0.015, f"{v:,.1f}", ha="center",
            va="top" if last else "bottom", fontsize=7.5, color="white" if last else INK, fontweight="bold")
ax.set_ylim(0, top * 1.17); ax.set_ylabel("Millones de USD", fontsize=7, color=MUTED)
ax.tick_params(labelsize=7.5, colors=MUTED, length=0); ax.grid(axis="y", color=LINE, lw=0.6, zorder=0)
for s in ["top", "right", "left"]: ax.spines[s].set_visible(False)
ax.spines["bottom"].set_color(LINE); ax.set_xticks(range(n)); ax.set_xticklabels(labels)
plt.tight_layout(pad=0.4); CH = os.path.join(TMP, "chart.png"); fig.savefig(CH, transparent=True); plt.close(fig)

c = canvas.Canvas(OUT, pagesize=(W, H))
c.setTitle("Compras HyCite México por año"); c.setAuthor("CHASEP 13588")
logo = ImageReader(os.path.join(HERE, "logo_chasep.png"))

def header(sub):
    c.setFillColor(HexColor(NAVY)); c.rect(0, H - 74, W, 74, fill=1, stroke=0)
    c.setFillColor(white); c.roundRect(28, H - 64, 50, 52, 8, fill=1, stroke=0)
    c.drawImage(logo, 32, H - 61, 42, 44, mask="auto", preserveAspectRatio=True)
    c.setFont("PB", 20); c.drawString(92, H - 38, "Compras HyCite México por año")
    c.setFont("P", 9.5); c.setFillColor(HexColor("#C9CEE3")); c.drawString(92, H - 55, sub)
    c.setFont("PM", 8.5); c.drawRightString(W - 28, H - 38, "Fuente: HyCite Mexico Purchase Growth by Territory Director")
    c.drawRightString(W - 28, H - 52, f"{'Corte' if OPEN else 'Cierre'}: {CUTLBL_Y} · compras en USD")

def footer(p):
    c.setFont("P", 7); c.setFillColor(HexColor(MUTED))
    c.drawString(28, 16, "CHASEP 13588 · MEJAB 29365 · Elaborado a partir de los reportes corporativos ReportingServices@hycite.com")
    c.drawRightString(W - 28, 16, f"Página {p} de 2")

def kpi(x, y, w, h, label, value, sub, color=INK, fill="#FFFFFF", sub_color=MUTED):
    c.setFillColor(HexColor(fill)); c.setStrokeColor(HexColor(LINE)); c.roundRect(x, y, w, h, 8, fill=1, stroke=1)
    c.setFillColor(HexColor(MUTED if fill == "#FFFFFF" else "#C9CEE3")); c.setFont("PS", 7); c.drawString(x + 10, y + h - 15, label.upper())
    c.setFillColor(HexColor(color)); c.setFont("PB", 17); c.drawString(x + 10, y + h - 36, value)
    c.setFillColor(HexColor(sub_color)); c.setFont("P", 7.5); c.drawString(x + 10, y + 9, sub)

# ===== Página 1 =====
c.setFillColor(HexColor(BG)); c.rect(0, 0, W, H, fill=1, stroke=0)
header(f"Total nacional de compras a HyCite {F0-1} – {Y} · México · USD")
kw = (W - 56 - 30) / 4
sub1 = (f"{rng} {Ms(cs)}" if nclosed else "") + (f" · {MES[cur]} parcial {Ms(nat['m26'][cur])}" if OPEN else "")
kpi(28, ky, kw, 56, f"Compras {Y} al {CUTLBL}", M(ytd), sub1.strip(" ·"), fill=NAVY, color="#FFFFFF", sub_color="#C9CEE3")
if g_cl is not None:
    kpi(28 + (kw + 10), ky, kw, 56, f"{rng} {Y} vs {Y-1}", P(g_cl), f"{Ms(cs)} vs {Ms(cs_prev)} USD (meses cerrados)", color=GOOD if g_cl >= 0 else BAD)
else:
    kpi(28 + (kw + 10), ky, kw, 56, f"{Y} vs {Y-1}", "—", "Aún no hay meses cerrados")
if FULLYEAR:
    kpi(28 + 2 * (kw + 10), ky, kw, 56, f"Cierre {Y}", M(ytd, 1), f"{P(ytd/ytd_prev-1)} vs {Y-1} ({Ms(ytd_prev,1)})", color=BLUE)
elif proj:
    kpi(28 + 2 * (kw + 10), ky, kw, 56, f"Proyección cierre {Y}", M(proj, 1), f"{P(proj/fy_prev-1)} vs {Y-1} ({Ms(fy_prev,1)}) · estimado", color=BLUE)
else:
    kpi(28 + 2 * (kw + 10), ky, kw, 56, f"Proyección cierre {Y}", "—", "Sin datos suficientes", color=BLUE)
kpi(28 + 3 * (kw + 10), ky, kw, 56, "Mejor año del periodo", f"{best[0]} · {M(best[1],1)}", f"{Y-1} quedó {P(fy_prev/best[1]-1)} vs el pico", color=INK)

px, py, pw, ph = 28, 36, PW, ky - 48
c.setFillColor(white); c.setStrokeColor(HexColor(LINE)); c.roundRect(px, py, pw, ph, 10, fill=1, stroke=1)
c.setFillColor(HexColor(INK)); c.setFont("PS", 11); c.drawString(px + 14, py + ph - 20, "Compras anuales (millones de USD)")
c.setFont("P", 7.5); c.setFillColor(HexColor(MUTED))
c.drawString(px + 14, py + ph - 33, "Barra oscura = año pico" + ("" if FULLYEAR else f" · {Y} sólido = real al {CUTLBL}, rayado = proyección al cierre"))
c.drawImage(CH, px + 8, py + 8, pw - 16, ph - 46, mask="auto", preserveAspectRatio=True)

tx, tw = px + pw + 12, W - 28 - (px + pw + 12)
c.setFillColor(white); c.roundRect(tx, py, tw, ph, 10, fill=1, stroke=1)
c.setFillColor(HexColor(INK)); c.setFont("PS", 11); c.drawString(tx + 14, py + ph - 20, "Detalle por año")
yy = py + ph - 44
c.setFillColor(HexColor(BLUE)); c.rect(tx + 8, yy - 6, tw - 16, 18, fill=1, stroke=0)
c.setFillColor(white); c.setFont("PS", 7.5)
c.drawString(tx + 14, yy, "AÑO"); c.drawRightString(tx + 132, yy, "COMPRAS USD"); c.drawRightString(tx + 196, yy, "CREC."); c.drawRightString(tx + tw - 14, yy, "VAR. USD")
rows = [(str(y), money(v), g, sgn(v - b) if b else "—") for y, v, b, g in ann[-10:]]
if FULLYEAR: rows.append((f"{Y}", money(ytd), ytd / ytd_prev - 1, sgn(ytd - ytd_prev)))
else: rows.append((f"{Y}*", money(ytd), g_cl, sgn(cs - cs_prev) if nclosed else "—"))
yy -= 21
for i, (a, v, gv, dd) in enumerate(rows):
    if i % 2 == 0: c.setFillColor(HexColor("#F5F7FB")); c.rect(tx + 8, yy - 6, tw - 16, 19, fill=1, stroke=0)
    c.setFillColor(HexColor(INK)); c.setFont("PS" if a.startswith(str(Y)) else "PM", 8.5); c.drawString(tx + 14, yy, a)
    c.setFont("P", 8.5); c.drawRightString(tx + 132, yy, v)
    if gv is not None:
        c.setFillColor(HexColor("#E1F3EA" if gv >= 0 else "#FCEAE8")); c.roundRect(tx + 150, yy - 4, 50, 14, 6, fill=1, stroke=0)
        c.setFillColor(HexColor(GOOD if gv >= 0 else BAD)); c.setFont("PS", 7.5); c.drawRightString(tx + 196, yy, P(gv))
    else:
        c.setFillColor(HexColor(MUTED)); c.drawRightString(tx + 196, yy, "—")
    c.setFillColor(HexColor(MUTED)); c.setFont("P", 7.5); c.drawRightString(tx + tw - 14, yy, dd)
    yy -= 19
notes = ["Crecimiento = el que marca el reporte de cierre de cada año", "(contra el año anterior reexpresado por HyCite)."]
if not FULLYEAR:
    notes.append(f"* {Y} al {CUTLBL}." + (f" Crec. y Var. USD comparan {rng} cerrados." if nclosed else ""))
if OPEN:
    rep = ytd / ytd_prev - 1 if ytd_prev else None
    notes += [f"Ojo: el reporte compara {Y} al {CUTLBL} contra {Y-1} con", f"{MESL[cur]} completo; por eso marca {P(rep)} (no comparable)."]
if OPEN and avgp:
    notes += [f"Proyección: {MES[cur]} al día {cutDay} ÷ {avgp*100:.1f}% (avance típico al",
              f"día {cutDay} en {MES[min(pct_months)]}–{MES[max(pct_months)]}) + resto de {Y-1} × (1 {g_cl*100:+.2f}%)." if g_cl is not None else ""]
elif not OPEN and not FULLYEAR and g_cl is not None:
    notes += [f"Proyección: meses cerrados + resto de {Y-1} × (1 {g_cl*100:+.2f}%)."]
c.setFont("P", 6.6); c.setFillColor(HexColor(MUTED))
ny = py + 14 + 9 * (len(notes) - 1)
for t in notes: c.drawString(tx + 14, ny, t); ny -= 9
footer(1); c.showPage()

# ===== Página 2 =====
c.setFillColor(HexColor(BG)); c.rect(0, 0, W, H, fill=1, stroke=0)
header("Detalle mensual nacional y territorio CHASEP 13588 + MEJAB 29365")
px, pw = 28, W - 56
myears = sorted(monthly)[-8:]
ph = 80 + 22 * len(myears); py = H - 86 - ph
c.setFillColor(white); c.setStrokeColor(HexColor(LINE)); c.roundRect(px, py, pw, ph, 10, fill=1, stroke=1)
c.setFillColor(HexColor(INK)); c.setFont("PS", 11); c.drawString(px + 14, py + ph - 20, "Compras nacionales por mes (miles de USD)")
c.setFont("P", 7.5); c.setFillColor(HexColor(MUTED))
c.drawString(px + 14, py + ph - 33, "Verde = mejor mes del año · Rojo = peor mes" + (f" · {MES[cur]} {Y} parcial al día {cutDay}" if OPEN else ""))
x0 = px + 14; cw = (pw - 28 - 46 - 70) / 12
yy = py + ph - 56
c.setFillColor(HexColor(BLUE)); c.rect(px + 8, yy - 6, pw - 16, 18, fill=1, stroke=0)
c.setFillColor(white); c.setFont("PS", 7.5); c.drawString(x0, yy, "AÑO")
for i, m in enumerate(MES): c.drawRightString(x0 + 46 + cw * (i + 1) - 4, yy, m.upper())
c.drawRightString(px + pw - 14, yy, "TOTAL")
yy -= 22
for k, y in enumerate(myears):
    mv = monthly[y]; closed = [v for v in mv[: (nclosed if y == Y else 12)] if v is not None]
    hi, lo = (max(closed), min(closed)) if len(closed) > 1 else (None, None)
    if k % 2 == 0: c.setFillColor(HexColor("#F5F7FB")); c.rect(px + 8, yy - 7, pw - 16, 22, fill=1, stroke=0)
    c.setFillColor(HexColor(INK)); c.setFont("PS", 8.5); c.drawString(x0, yy, str(y))
    for i, v in enumerate(mv):
        xr = x0 + 46 + cw * (i + 1) - 4
        if v is None: c.setFillColor(HexColor(MUTED)); c.setFont("P", 8); c.drawRightString(xr, yy, "—"); continue
        partial = (y == Y and OPEN and i == cur)
        if not partial and v == hi: c.setFillColor(HexColor("#E1F3EA")); c.rect(xr - cw + 8, yy - 5, cw - 4, 16, fill=1, stroke=0)
        if not partial and v == lo: c.setFillColor(HexColor("#FCEAE8")); c.rect(xr - cw + 8, yy - 5, cw - 4, 16, fill=1, stroke=0)
        c.setFillColor(HexColor(GOLD if partial else INK)); c.setFont("PS" if partial else "P", 8)
        c.drawRightString(xr, yy, f"{v/1e3:,.0f}" + ("*" if partial else ""))
    c.setFillColor(HexColor(INK)); c.setFont("PS", 8.5); c.drawRightString(px + pw - 14, yy, f"{totals[y]/1e3:,.0f}")
    yy -= 22
c.setFont("P", 6.6); c.setFillColor(HexColor(MUTED))
c.drawString(px + 14, py + 10, f"{F0-1} tomado del comparativo del reporte de cierre {F0}. Totales = cifra oficial del reporte de cada año (cuadra al dólar con la suma mensual).")

py2 = 36; ph2 = py - 12 - py2
c.setFillColor(white); c.roundRect(px, py2, pw, ph2, 10, fill=1, stroke=1)
c.setFillColor(HexColor(INK)); c.setFont("PS", 11); c.drawString(px + 14, py2 + ph2 - 20, "Territorio CHASEP + MEJAB por año")
c.setFont("P", 7.5); c.setFillColor(HexColor(MUTED))
c.drawString(px + 232, py2 + ph2 - 20, "Cuando el reporte no trae a 29365 por separado, MEJAB va incluido dentro de 13588")
hx = [px + 14, px + 70, px + 210, px + 330, px + 450, px + 540, px + 640, px + pw - 14]
yy = py2 + ph2 - 42
c.setFillColor(HexColor(BLUE)); c.rect(px + 8, yy - 6, pw - 16, 18, fill=1, stroke=0)
c.setFillColor(white); c.setFont("PS", 7.5)
for x, t, r in [(hx[0], "AÑO", 0), (hx[1], "PREMIER", 0), (hx[2], "COMPRAS 13588", 1), (hx[3], "COMPRAS 29365", 1), (hx[4], "TOTAL", 1), (hx[5], "CREC.", 1), (hx[6], "% NACIONAL", 1), (hx[7], "POSICIÓN NACIONAL", 1)]:
    (c.drawRightString if r else c.drawString)(x, yy, t)
yy -= 19
def badge(x, y, txt, col):
    c.setFillColor(HexColor(col)); c.roundRect(x, y - 3, 30, 12, 3, fill=1, stroke=0)
    c.setFillColor(white); c.setFont("PB", 6.5); c.drawCentredString(x + 15, y, txt)
for i, r in enumerate(cm):
    isY = r["y"] == Y and not FULLYEAR
    if isY: c.setFillColor(HexColor("#E7EFFD")); c.rect(px + 8, yy - 6, pw - 16, 17, fill=1, stroke=0)
    elif i % 2 == 0: c.setFillColor(HexColor("#F5F7FB")); c.rect(px + 8, yy - 6, pw - 16, 17, fill=1, stroke=0)
    c.setFillColor(HexColor(INK)); c.setFont("PS" if isY else "PM", 8.5); c.drawString(hx[0], yy, f"{r['y']}" + ("*" if isY else ""))
    badge(hx[1], yy, "13588", BLUE)
    if r["m"] is not None: badge(hx[1] + 33, yy, "29365", GREEN)
    c.setFillColor(HexColor(INK)); c.setFont("P", 8.5); c.drawRightString(hx[2], yy, money(r["c"]))
    if r["m"] is None: c.setFillColor(HexColor(MUTED)); c.drawRightString(hx[3], yy, "incluido")
    else: c.drawRightString(hx[3], yy, money(r["m"]))
    c.setFillColor(HexColor(INK)); c.setFont("PS", 8.5); c.drawRightString(hx[4], yy, money(r["tot"]))
    if r["g"] is not None: c.setFillColor(HexColor(GOOD if r["g"] >= 0 else BAD)); c.drawRightString(hx[5], yy, P(r["g"]))
    c.setFillColor(HexColor(INK)); c.setFont("P", 8.5); c.drawRightString(hx[6], yy, f"{r['share']*100:.1f}%")
    pos = f"{r['rc']}°" + (f" / {r['rm']}°" if r["rm"] else "") + f" de {r['nT']}"
    c.drawRightString(hx[7], yy, pos)
    yy -= 17
c.setFont("P", 6.6); c.setFillColor(HexColor(MUTED))
last = cm[-1]
if last["y"] == Y and not FULLYEAR and nclosed:
    extra = f" (13588 {P(last['gc'])}" + (f" · 29365 {P(last['gm'])}" if last["gm"] is not None else "") + ")"
    c.drawString(px + 14, py2 + 10, f"* {Y} al {CUTLBL}; crecimiento {rng} cerrados vs {Y-1} reexpresado{extra}. Posición = lugar por compras entre directores del reporte (sin 'Otros').")
else:
    c.drawString(px + 14, py2 + 10, "Posición = lugar por compras entre directores del reporte (sin 'Otros').")
if restat:
    txt = " · ".join(f"{y} {'+' if v >= 0 else '−'}{abs(v)/1e3:,.1f} mil" for y, v in restat)
    c.drawString(px + 14, py2 + 20, f"Reexpresiones de HyCite (cierre propio vs base del año siguiente): {txt}. Se respeta el cierre oficial de cada año.")
footer(2); c.save()

if args.out is None: shutil.copyfile(OUT, os.path.join(OUTDIR, "ultimo.pdf"))
shutil.rmtree(TMP, ignore_errors=True)
print(json.dumps(dict(pdf=OUT, file=os.path.basename(OUT), cutDate=cd, open=OPEN, ytd=round(ytd, 2), closed=rng, g_closed=None if g_cl is None else round(g_cl * 100, 2),
                      proj=None if proj is None else round(proj, 2), chasep_mejab=[(r["y"], round(r["tot"]), None if r["g"] is None else round(r["g"] * 100, 2)) for r in cm]), ensure_ascii=False))
