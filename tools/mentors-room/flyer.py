#!/usr/bin/env python3
"""
The Mentor's Room · generador del flyer semanal del ponente (9:16).

Uso:
  python3 flyer.py datos.json salida_sin_extension

datos.json:
  {"name": "...", "role": "Élite", "country": "mx", "countryName": "México",
   "topic": "...", "date": "2026-11-17", "photo": "/ruta/foto.jpg"}

Genera <salida>.png (1080x1920, para WhatsApp/redes) y <salida>.pdf
(con el botón "Conéctate aquí" clicable hacia la sala de Zoom).
Requiere: rembg, pillow, playwright (chromium) y las fuentes de @fontsource.
"""
import json, sys, os, base64, io, pathlib, subprocess, unicodedata

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent.parent
IMG = REPO / "p" / "mentors-room" / "img"
ZOOM = "https://us06web.zoom.us/my/chasepenterprise?pwd=WFVQUEI3NVBJemRGZWJVYlg4MmUzZz09"
MESES = ["enero","febrero","marzo","abril","mayo","junio","julio","agosto","septiembre","octubre","noviembre","diciembre"]
ROLES = {"blue royal":"Blue Royal","blue":"Blue Royal","premier":"Premier","elite":"Élite","master":"Master","spin out":"Spin Out","spinout":"Spin Out"}


def fonts_dir():
    d = pathlib.Path(os.environ.get("TMR_FONTS", "/tmp/tmr-fonts"))
    if not (d / "pf700.woff2").exists():
        d.mkdir(parents=True, exist_ok=True)
        subprocess.run(["npm", "pack", "-s", "@fontsource/playfair-display@5", "@fontsource/montserrat@5"], cwd=d, check=True,
                       stdout=subprocess.DEVNULL)
        for t in d.glob("*.tgz"):
            subprocess.run(["tar", "xzf", t.name], cwd=d, check=True)
            (d / "package").rename(d / t.stem)
        pf = next(d.glob("fontsource-playfair-display-*")) / "files"
        mo = next(d.glob("fontsource-montserrat-*")) / "files"
        (d / "pf700.woff2").write_bytes((pf / "playfair-display-latin-700-normal.woff2").read_bytes())
        for w in (200, 300, 400, 500, 600, 700):
            (d / f"mo{w}.woff2").write_bytes((mo / f"montserrat-latin-{w}-normal.woff2").read_bytes())
    return d


def b64(p, mime):
    return f"data:{mime};base64," + base64.b64encode(pathlib.Path(p).read_bytes()).decode()


def cutout(photo):
    from rembg import remove, new_session
    from PIL import Image
    im = Image.open(photo).convert("RGB")
    out = remove(im, session=new_session("isnet-general-use"), post_process_mask=True)
    out = out.crop(out.getbbox())
    buf = io.BytesIO(); out.save(buf, "PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


def clean(s):
    s = " ".join(str(s or "").split())
    return s[:1].upper() + s[1:] if s else s


def title(s):
    return " ".join(w[:1].upper() + w[1:].lower() if len(w) > 2 else w for w in str(s or "").split())


def build(d, out):
    from PIL import Image
    F = fonts_dir()
    y, m, dd = map(int, d["date"].split("-"))
    role = ROLES.get(unicodedata.normalize("NFD", str(d.get("role", ""))).encode("ascii", "ignore").decode().strip().lower(), clean(d.get("role", "")))
    name = title(d["name"]); topic = clean(d.get("topic", ""))
    ff = "".join(f"@font-face{{font-family:Mo;font-weight:{w};src:url({b64(F / f'mo{w}.woff2','font/woff2')})}}" for w in (200, 300, 500, 600, 700))
    ff += f"@font-face{{font-family:Pf;font-weight:700;src:url({b64(F / 'pf700.woff2','font/woff2')})}}"
    flag = f"https://flagcdn.com/w160/{d['country']}.png" if d.get("country") else ""
    name_size = 104 if len(name) <= 16 else 88 if len(name) <= 22 else 72
    html = f"""<!doctype html><html><head><meta charset="utf-8"><style>{ff}
*{{margin:0;padding:0;box-sizing:border-box}}
body{{width:1080px;height:1920px;overflow:hidden;background:#020C15;font-family:Mo;color:#F5F1EA}}
.bg{{position:absolute;inset:0;background:linear-gradient(165deg,#0A2A47 0%,#05233C 22%,#020C15 58%,#020C15 100%)}}
.lounge{{position:absolute;left:0;top:560px;width:1080px;height:940px;background:url({b64(IMG/'lounge.jpg','image/jpeg')}) left center/cover;opacity:.55;filter:saturate(1.1);-webkit-mask:linear-gradient(180deg,transparent 0%,#000 25%,#000 60%,transparent 100%);mask:linear-gradient(180deg,transparent 0%,#000 25%,#000 60%,transparent 100%)}}
.panel{{position:absolute;width:900px;height:900px;transform:rotate(45deg);background:linear-gradient(135deg,rgba(10,42,71,.85),rgba(5,35,60,.25));border-left:2px solid rgba(224,172,112,.75);box-shadow:-6px 0 30px rgba(224,172,112,.35)}}
.p1{{right:-640px;top:-260px}}.p2{{left:-700px;bottom:-520px;transform:rotate(225deg)}}
.vig{{position:absolute;inset:0;background:radial-gradient(ellipse at 50% 50%,rgba(2,12,21,0) 40%,rgba(2,12,21,.7) 100%),linear-gradient(180deg,rgba(2,12,21,0) 0%,rgba(2,12,21,0) 55%,rgba(2,12,21,.92) 72%,#020C15 100%)}}
.gold{{background:linear-gradient(135deg,#F4D5AD 0%,#E0AC70 45%,#A7764A 100%);-webkit-background-clip:text;background-clip:text;color:transparent}}
.logo{{position:absolute;top:56px;left:50%;transform:translateX(-50%);width:700px}}
.logo img{{width:100%;display:block;-webkit-mask:radial-gradient(ellipse 58% 62% at 50% 46%,#000 62%,transparent 100%);mask:radial-gradient(ellipse 58% 62% at 50% 46%,#000 62%,transparent 100%)}}
.eyebrow{{position:absolute;top:452px;width:100%;text-align:center;font-weight:500;letter-spacing:.42em;font-size:26px;color:#E0AC70}}
.eyebrow:before,.eyebrow:after{{content:"";display:inline-block;width:120px;height:1px;vertical-align:middle;margin:0 26px;background:linear-gradient(90deg,transparent,#E0AC70,transparent)}}
.halo{{position:absolute;left:50%;top:580px;width:760px;height:760px;transform:translateX(-50%);border-radius:50%;background:radial-gradient(circle,rgba(224,172,112,.38) 0%,rgba(224,172,112,.10) 45%,rgba(224,172,112,0) 70%)}}
.ring{{position:absolute;left:50%;top:620px;width:600px;height:600px;transform:translateX(-50%);border-radius:50%;border:2px solid rgba(224,172,112,.55);box-shadow:0 0 60px rgba(224,172,112,.25) inset}}
.photo{{position:absolute;left:50%;bottom:690px;transform:translateX(-50%);height:690px;max-width:960px;filter:drop-shadow(0 0 2px rgba(244,213,173,.6)) drop-shadow(0 30px 60px rgba(0,0,0,.6))}}
.photo img{{height:100%;display:block;-webkit-mask:linear-gradient(180deg,#000 80%,transparent 100%);mask:linear-gradient(180deg,#000 80%,transparent 100%)}}
.name{{position:absolute;top:1190px;width:100%;text-align:center;font-family:Pf;font-weight:700;font-size:{name_size}px;line-height:1.05;letter-spacing:.01em;padding:0 60px}}
.role{{position:absolute;top:{1190+int(name_size*1.15)+18}px;width:100%;display:flex;justify-content:center;align-items:center;gap:22px;font-weight:600;font-size:30px;letter-spacing:.32em;text-transform:uppercase}}
.role img{{width:62px;height:62px;border-radius:50%;object-fit:cover;box-shadow:0 0 0 3px #E0AC70,0 0 20px rgba(224,172,112,.45)}}
.role span.sep{{width:8px;height:8px;border-radius:50%;background:#E0AC70}}
.topic{{position:absolute;top:1430px;width:100%;text-align:center;padding:0 90px}}
.topic small{{display:block;font-weight:300;letter-spacing:.42em;font-size:22px;color:#C9CDD2;margin-bottom:12px}}
.topic div{{font-weight:600;font-size:{48 if len(topic)<=34 else 40 if len(topic)<=60 else 34}px;line-height:1.2;text-transform:uppercase;letter-spacing:.06em}}
.bar{{position:absolute;top:1585px;left:70px;right:70px;display:grid;grid-template-columns:1fr 1px 1fr 1px 1fr;align-items:center;gap:26px}}
.bar i{{height:76px;background:linear-gradient(180deg,transparent,rgba(224,172,112,.6),transparent)}}
.it{{display:flex;align-items:center;gap:16px}}
.it svg{{width:58px;height:58px;flex:none}}
.it small{{display:block;font-weight:300;font-size:19px;letter-spacing:.24em;color:#C9CDD2}}
.it b{{display:block;font-weight:700;font-size:25px;letter-spacing:.02em;margin-top:2px}}
.cta{{position:absolute;top:1712px;left:50%;transform:translateX(-50%);padding:16px 46px;border-radius:999px;border:1.5px solid #E0AC70;color:#F4D5AD;font-weight:600;font-size:22px;letter-spacing:.3em;text-decoration:none;white-space:nowrap}}
.foot{{position:absolute;bottom:22px;width:100%;display:flex;justify-content:center;align-items:center;gap:20px}}
.foot small{{font-weight:300;letter-spacing:.38em;font-size:17px;color:#C9CDD2}}
.foot img{{height:74px;border-radius:8px}}
</style></head><body>
<div class="bg"></div><div class="lounge"></div><div class="panel p1"></div><div class="panel p2"></div><div class="vig"></div>
<div class="logo"><img src="{b64(IMG/'hero-portal.jpg','image/jpeg')}"></div>
<div class="eyebrow">MENTOR INVITADO</div>
<div class="halo"></div><div class="ring"></div>
<div class="photo"><img src="{cutout(d['photo'])}"></div>
<div class="name gold">{name}</div>
<div class="role">{f'<img src="{flag}">' if flag else ''}<span class="gold">{role}</span>{'<span class="sep"></span><span>'+d.get('countryName','')+'</span>' if d.get('countryName') else ''}</div>
<div class="topic"><small>TEMA</small><div>{topic}</div></div>
<div class="bar">
 <div class="it"><svg viewBox="0 0 48 48" fill="none" stroke="#E0AC70" stroke-width="2.4"><rect x="6" y="9" width="36" height="33" rx="4"/><path d="M6 19h36M15 5v8M33 5v8"/><path d="M13 26h4M22 26h4M31 26h4M13 33h4M22 33h4M31 33h4" stroke-linecap="round"/></svg><div><small>MARTES</small><b>{dd} DE {MESES[m-1].upper()}</b></div></div>
 <i></i>
 <div class="it"><svg viewBox="0 0 48 48" fill="none" stroke="#E0AC70" stroke-width="2.4"><circle cx="24" cy="24" r="18"/><path d="M24 13v12l7 5" stroke-linecap="round"/></svg><div><b>10:00 AM</b><small>HORA CDMX</small></div></div>
 <i></i>
 <div class="it"><svg viewBox="0 0 48 48"><circle cx="24" cy="24" r="21" fill="#F5F1EA"/><rect x="11" y="17" width="18" height="14" rx="3" fill="#05233C"/><path d="M30 21.5l7-4.5v14l-7-4.5z" fill="#05233C"/></svg><div><small>POR</small><b>ZOOM</b></div></div>
</div>
<a class="cta" href="{ZOOM}">CONÉCTATE AQUÍ</a>
<div class="foot"><small>PRESENTADO POR</small><img src="{b64(IMG/'chasep-2x.jpg','image/jpeg')}"></div>
</body></html>"""
    hp = pathlib.Path(out + ".html"); hp.write_text(html, encoding="utf-8")
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": 1080, "height": 1920})
        pg.goto(hp.as_uri()); pg.wait_for_timeout(1500)
        pg.screenshot(path=out + ".png")
        pg.pdf(path=out + ".pdf", width="1080px", height="1920px", print_background=True, page_ranges="1")
        b.close()
    hp.unlink()
    return out + ".png", out + ".pdf"


if __name__ == "__main__":
    data = json.load(open(sys.argv[1], encoding="utf-8"))
    print(build(data, sys.argv[2]))
