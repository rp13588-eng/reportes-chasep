#!/usr/bin/env python3
"""Icebreakers CHASEP + MEJAB.
Fuentes: correo Hycite "IcebreakerCounts" (PDF semanal, conteos por distribuidor) y
PDF "Reclutamiento México" de Ivan Sasito en el grupo Premiers México (reclutamiento y
reclutamiento con venta por Premier). No se suman entre sí: el correo da los icebreakers
por distribuidor; el PDF de Ivan solo aporta "con venta".

Uso:
  ice.py add-report <IcebreakerCounts.pdf> <AAAA-MM-DD fecha de ejecución>
  ice.py set-ivan <AAAA-MM> <AAAA-MM-DD> <chasep_recl> <chasep_venta> <mejab_recl> <mejab_venta>
  ice.py build <distribuciones.xlsx> <salida data.json>
  ice.py summary <data.json>
"""
import sys, os, re, json, subprocess, datetime as dt, calendar
HERE = os.path.dirname(os.path.abspath(__file__))
STATE = os.path.join(HERE, 'state.json')
TARGET = {'13588': 'CHASEP', '29365': 'MEJAB'}
NUM = r'(-?[\d,]+)'; PCT = r'(-?[\d,\.]+%)'
ROW6 = re.compile(r'\s+'+NUM+r'\s+'+NUM+r'\s+'+PCT+r'\s+'+NUM+r'\s+'+NUM+r'\s+'+PCT+r'\s*$')
DET = re.compile(r'^\s+(\d{4,6})'+ROW6.pattern)
HDR = re.compile(r'^\s*(\d{4,6})-(\S.*)$')
NUMONLY = re.compile(r'^'+ROW6.pattern)
MESES = ['ene','feb','mar','abr','may','jun','jul','ago','sep','oct','nov','dic']

def toi(s): return int(s.replace(',', ''))

def load():
    if os.path.exists(STATE): return json.load(open(STATE))
    return {'cum': {}, 'partial': None, 'overrides': {}, 'reports': [], 'prem': {}, 'ivan': {}}

def save(s): json.dump(s, open(STATE, 'w'), ensure_ascii=False, indent=0, sort_keys=True)

def parse_pdf(path):
    txt = subprocess.run(['pdftotext', '-layout', path, '-'], capture_output=True, text=True).stdout
    prem, dist = {}, {}
    in_det = False; cur = None; pending = None
    for ln in txt.splitlines():
        if re.search(r'\bDetails:', ln): in_det = True; continue
        m = HDR.match(ln)
        if m and not DET.match(ln):
            pid = m.group(1); nm = ROW6.search(m.group(2))
            if in_det: cur = pid
            elif nm:
                if pid in TARGET: prem[pid] = [toi(nm.group(i)) for i in (1, 2, 4, 5)]
                pending = None
            else: pending = pid
            continue
        if not in_det and pending:
            nm = NUMONLY.match(ln)
            if nm:
                if pending in TARGET: prem[pending] = [toi(nm.group(i)) for i in (1, 2, 4, 5)]
                pending = None
            continue
        if in_det:
            d = DET.match(ln)
            if d and cur in TARGET:
                dist[d.group(1)] = ([toi(d.group(i)) for i in (2, 3, 5, 6)], cur)
    # validación: suma de distribuidores = total del Premier
    for pid in TARGET:
        rows = [v for v, p in dist.values() if p == pid]
        if pid in prem:
            s = [sum(r[i] for r in rows) for i in range(4)]
            if s != prem[pid]:
                raise SystemExit(f'ERROR validación {pid}: suma distribuidores {s} != total {prem[pid]}')
    if not dist: raise SystemExit('ERROR: no encontré detalle de CHASEP/MEJAB en el PDF')
    return prem, dist

def add_report(pdf, fecha):
    s = load()
    run = dt.date.fromisoformat(fecha)
    asof = run - dt.timedelta(days=1)          # el reporte cubre hasta el día anterior
    Y, M = asof.year, asof.month
    prem, dist = parse_pdf(pdf)
    def setcum(y, m, vals):
        s['cum'].setdefault(str(y), {})[str(m)] = vals
    if M > 1:
        setcum(Y, M-1, {i: v[3]-v[1] for i, (v, p) in dist.items()})
        setcum(Y-1, M-1, {i: v[2]-v[0] for i, (v, p) in dist.items()})
    last = calendar.monthrange(Y, M)[1] == asof.day
    if last:
        setcum(Y, M, {i: v[3] for i, (v, p) in dist.items()})
        setcum(Y-1, M, {i: v[2] for i, (v, p) in dist.items()})
    if M == 12:
        s['overrides'][f'{Y}-12'] = {'asof': asof.isoformat(), 'v': {i: v[1] for i, (v, p) in dist.items()}}
    if not s['partial'] or s['partial']['asof'] <= asof.isoformat():
        s['partial'] = {'ym': f'{Y}-{M:02d}', 'asof': asof.isoformat(), 'closed': last,
                        'mtd': {i: v[1] for i, (v, p) in dist.items()},
                        'prev_same': {i: v[0] for i, (v, p) in dist.items()},
                        'totals': {TARGET[k]: v for k, v in prem.items()}}
    for i, (v, p) in dist.items(): s['prem'][i] = TARGET[p]
    if fecha not in s['reports']: s['reports'].append(fecha); s['reports'].sort()
    save(s)
    tot = {TARGET[k]: v for k, v in prem.items()}
    print(json.dumps({'reporte': fecha, 'corte': asof.isoformat(), 'mes': f'{Y}-{M:02d}', 'totales [pMTD,MTD,pYTD,YTD]': tot}, ensure_ascii=False))

def set_ivan(ym, fecha, cr, cv, mr, mv):
    s = load()
    old = s['ivan'].get(ym)
    if old and old['fecha'] > fecha:
        print('Ya hay un PDF más reciente para', ym, old); return
    s['ivan'][ym] = {'fecha': fecha, 'CHASEP': [int(cr), int(cv)], 'MEJAB': [int(mr), int(mv)]}
    save(s); print('ok', ym, s['ivan'][ym])

def monthly(s, start=(2025, 1)):
    p = s['partial']; py, pm = map(int, p['ym'].split('-'))
    out = {}  # ym -> {id: n}
    y, m = start
    while (y, m) <= (py, pm):
        ym = f'{y}-{m:02d}'
        cur = s['cum'].get(str(y), {}).get(str(m))
        prev = {} if m == 1 else s['cum'].get(str(y), {}).get(str(m-1))
        if (y, m) == (py, pm) and not p.get('closed'):
            out[ym] = dict(p['mtd'])
        elif cur is not None and prev is not None:
            ids = set(cur) | set(prev)
            out[ym] = {i: cur.get(i, 0) - prev.get(i, 0) for i in ids}
        elif ym in s['overrides']:
            out[ym] = dict(s['overrides'][ym]['v'])
        else:
            out[ym] = None
        m += 1
        if m == 13: y, m = y+1, 1
    return out

def read_distrib(xlsx):
    import openpyxl
    wb = openpyxl.load_workbook(xlsx, data_only=True)
    db = {}
    names = {n.upper(): n for n in wb.sheetnames}
    for sh in ['CHASEP', 'MEJAB', 'BAJAS']:
        if sh not in names: continue
        ws = wb[names[sh]]
        for r in ws.iter_rows(min_row=2, values_only=True):
            if not r or r[0] is None: continue
            did = str(r[0]).strip().split('.')[0]
            if not did.isdigit(): continue
            g = lambda k: (str(r[k]).strip() if len(r) > k and r[k] is not None else '')
            rec = {'nombre': g(1), 'compania': g(2) or g(1), 'sub': g(3).upper(),
                   'premier': 'MEJAB' if sh == 'MEJAB' or g(4).upper() == 'MEJAB' else 'CHASEP',
                   'nivel': g(5).upper(), 'sponsor': g(6).split('.')[0],
                   'sucursal': g(7).upper() if sh != 'BAJAS' else '', 'baja': sh == 'BAJAS',
                   'fecha_baja': g(7) if sh == 'BAJAS' else ''}
            if sh == 'BAJAS' and did in db: continue
            db[did] = rec
    return db

def build(xlsx, out):
    s = load(); db = read_distrib(xlsx); mo = monthly(s)
    months = sorted(mo)
    ids = set()
    for v in mo.values():
        if v: ids |= {i for i, n in v.items() if n}
    dist = []
    for i in sorted(ids):
        info = db.get(i)
        rec = {'id': i, 'clas': bool(info)}
        if info: rec.update(info)
        else:
            rec.update({'nombre': f'ID {i} (sin clasificar)', 'compania': 'SIN CLASIFICAR', 'sub': 'SIN CLASIFICAR',
                        'premier': s['prem'].get(i, 'CHASEP'), 'nivel': '', 'sucursal': '', 'baja': False, 'sponsor': ''})
        rec['m'] = [(mo[k] or {}).get(i, 0) if mo[k] is not None else None for k in months]
        dist.append(rec)
    p = s['partial']
    data = {'generado': dt.datetime.now().strftime('%Y-%m-%d %H:%M'), 'corte': p['asof'], 'mes_actual': p['ym'],
            'mes_cerrado': p.get('closed', False), 'meses': months, 'dist': dist,
            'prev_same': {i: n for i, n in p['prev_same'].items() if n},
            'ivan': s['ivan'], 'dic_corte': {k: v['asof'] for k, v in s['overrides'].items()},
            'sin_dato': [k for k in months if mo[k] is None]}
    json.dump(data, open(out, 'w'), ensure_ascii=False, separators=(',', ':'))
    # resumen de control
    tot = {k: sum((mo[k] or {}).values()) for k in months}
    unk = [d for d in dist if not d['clas'] and any(d['m'][j] for j in range(len(months)) if months[j].startswith(p['ym'][:4]))]
    print(json.dumps({'corte': p['asof'], 'por_mes': tot, 'sin_clasificar_anio_actual': [(d['id'], d['premier'], sum(x or 0 for x in d['m'])) for d in unk]}, ensure_ascii=False))

def summary(path):
    d = json.load(open(path))
    ym = d['mes_actual']; y, m = map(int, ym.split('-')); j = d['meses'].index(ym)
    def tot(f, idx): return sum((x['m'][idx] or 0) for x in d['dist'] if f(x))
    lines = []
    corte = dt.date.fromisoformat(d['corte'])
    lines.append(f"🧊 *Icebreakers CHASEP + MEJAB*")
    lines.append(f"Corte al {corte.day} {MESES[corte.month-1]} {corte.year} · {MESES[m-1].capitalize()} {'cerrado' if d['mes_cerrado'] else 'a la fecha'}")
    for pr in ('CHASEP', 'MEJAB'):
        n = tot(lambda x: x['premier'] == pr, j)
        prev = sum(v for k, v in d['prev_same'].items() if any(x['id'] == k and x['premier'] == pr for x in d['dist']))
        iv = d['ivan'].get(ym)
        venta = f" · con venta {iv[pr][1]} de {iv[pr][0]} (PDF Ivan {iv['fecha'][8:10]}-{MESES[int(iv['fecha'][5:7])-1]})" if iv else ''
        lines.append(f"• {pr}: *{n}* (mismo periodo {y-1}: {prev}){venta}")
    ytd = sum(tot(lambda x: True, k) for k in range(len(d['meses'])) if d['meses'][k].startswith(str(y)))
    lines.append(f"• Año {y}: *{ytd}* icebreakers")
    unk = [x for x in d['dist'] if not x['clas'] and (x['m'][j] or 0) > 0]
    if unk: lines.append('⚠️ Sin clasificar este mes: ' + ', '.join(f"{x['id']} ({x['m'][j]})" for x in unk))
    print('\n'.join(lines))

if __name__ == '__main__':
    a = sys.argv[1:]
    if not a: print(__doc__); sys.exit(1)
    {'add-report': lambda: add_report(a[1], a[2]), 'set-ivan': lambda: set_ivan(*a[1:8]),
     'build': lambda: build(a[1], a[2]), 'summary': lambda: summary(a[1])}[a[0]]()
