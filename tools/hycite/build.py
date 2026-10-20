#!/usr/bin/env python3
"""Dashboard 'Crecimiento HyCite México' — data store + builder.

Uso:
  python3 build.py apply <reporte.txt>   # integra un reporte parseado (salida de extractor.js) a data.json
  python3 build.py render                # genera crecimiento-hycite.html desde template.html + data.json + logo_s.png
  python3 build.py check                 # imprime controles de cuadre

data.json = {current, years:{AAAA: datos del año}}. Cada año:
  year, cur (índice de mes 0-11 del último reporte), cutDay (1, 10 o 20), cutDate (AAAA-MM-DD)
  T: [{id, n, a[12] (año anterior, mensual), b[12] (año actual, mensual), y[2] (YTD oficial del último reporte), d10[12], d20[12]}]
  nat: {m25[12], m26[12], y[2], y24[12][2] (año anterior completo vs dos años atrás, del reporte del 1 ene), d10[12], d20[12]}
Regla: cutDay==1 → el mes 'cur' está CERRADO. cutDay 10/20 → 'cur' en curso (b parcial, a completo).
"""
import json, sys, base64, re, os
HERE = os.path.dirname(os.path.abspath(__file__))
P = lambda f: os.path.join(HERE, f)
MONTHS = ['JANUARY','FEBRUARY','MARCH','APRIL','MAY','JUNE','JULY','AUGUST','SEPTEMBER','OCTOBER','NOVEMBER','DECEMBER']

def load_all(): return json.load(open(P('data.json')))
def save_all(A): open(P('data.json'), 'w').write(json.dumps(A, separators=(',', ':'), ensure_ascii=False))
def load():
    A = load_all(); d = A['years'][str(A['current'])]; d['year'] = A['current']; return d
def save(d):
    A = load_all(); y = d['year']; A['years'][str(y)] = {k: v for k, v in d.items() if k != 'year'}; A['current'] = max(A['current'], y); save_all(A)

def parse_report(text):
    """Formato de extractor.js: líneas H:, F:, D:, T:MES|m25|m26|%|y25|y26|%, id|m25|m26|y25|y26|R|NOMBRE"""
    rep = {'tot': [], 'rows': {}}
    for ln in text.splitlines():
        ln = ln.strip()
        if ln.startswith('H:'): rep['head'] = ln[2:].split('|')
        elif ln.startswith('F:'):
            m = re.search(r'(\d{1,2})/(\d{1,2})/(\d{4})', ln)
            if m: rep['date'] = f"{m.group(3)}-{int(m.group(1)):02d}-{int(m.group(2)):02d}"; rep['day'] = int(m.group(2))
        elif ln.startswith('D:'): rep['month'] = MONTHS.index(ln[2:].split()[0])
        elif ln.startswith('T:'):
            p = ln[2:].split('|'); rep['tot'].append((MONTHS.index(p[0].strip()), float(p[1]), float(p[2]), float(p[4]), float(p[5])))
        elif re.match(r'^\d+\|', ln):
            p = ln.split('|'); rep['rows'][p[0]] = dict(m25=float(p[1]), m26=float(p[2]), y25=float(p[3]), y26=float(p[4]), name=p[6] if len(p) > 6 else None)
    return rep

def apply(path):
    d = load(); rep = parse_report(open(path).read())
    m, day = rep['month'], rep['day']
    yr = int(rep['head'][2].split()[0]) if 'head' in rep else d['year']
    if yr == d['year'] + 1:  # primer reporte de un año nuevo (día 10 de enero): se abre el año
        lst = [t for t in d['T'] if t['id'] != 'OTROS']
        d = dict(year=yr, cur=0, cutDay=10, cutDate='', T=[dict(id=t['id'], n=t['n'], a=[0]*12, b=[0]*12, y=[0, 0], d10=[None]*12, d20=[None]*12) for t in lst] +
                 [dict(id='OTROS', n='Otros (sin director asignado en el reporte)', a=[0]*12, b=[0]*12, y=[0, 0], d10=[None]*12, d20=[None]*12)],
                 nat=dict(m25=[0]*12, m26=[0]*12, y=[0, 0], y24=[], d10=[None]*12, d20=[None]*12))
    elif yr != d['year']:
        sys.exit(f"Reporte del año {yr} y el año en curso es {d['year']}: revisar manualmente.")
    closed = (day == 1)  # reporte del día 1 = mes 'm' cerrado
    T = {t['id']: t for t in d['T'] if t['id'] != 'OTROS'}
    for i, r in rep['rows'].items():
        if i not in T:
            T[i] = dict(id=i, n=r['name'] or i, a=[0]*12, b=[0]*12, y=[0, 0], d10=[None]*12, d20=[None]*12)
            d['T'].insert(-1, T[i])
        t = T[i]
        if r['name']: t['n'] = r['name']
        t['y'] = [r['y25'], r['y26']]
        if closed:
            # mes cerrado: se ajusta para cuadrar con el YTD oficial (absorbe compras posteadas tarde)
            t['a'][m] = round(r['y25'] - sum(t['a'][:m])); t['b'][m] = round(r['y26'] - sum(t['b'][:m]))
        else:
            t['a'][m] = round(r['m25']); t['b'][m] = round(r['m26'])
            (t['d10'] if day <= 10 else t['d20'])[m] = round(r['m26'])
    for (mi, n25, n26, y25, y26) in rep['tot']:
        d['nat']['m25'][mi] = n25; d['nat']['m26'][mi] = n26
    last = max(rep['tot'], key=lambda x: x[0])
    d['nat']['y'] = [last[3], last[4]]
    if not closed: d['nat']['d10' if day <= 10 else 'd20'][m] = last[2]
    # OTROS = oficial - suma de directores
    lst = [t for t in d['T'] if t['id'] != 'OTROS']; o = next(t for t in d['T'] if t['id'] == 'OTROS')
    for k in range(12):
        o['a'][k] = round(d['nat']['m25'][k] - sum(t['a'][k] for t in lst)); o['b'][k] = round(d['nat']['m26'][k] - sum(t['b'][k] for t in lst))
        for dk in ('d10', 'd20'):
            nv = d['nat'][dk][k]
            has = any(t[dk][k] is not None for t in lst)
            o[dk][k] = None if (nv is None or not has) else round(nv - sum((t[dk][k] or 0) for t in lst))
    o['y'] = [round(d['nat']['y'][0] - sum(t['y'][0] for t in lst), 2), round(d['nat']['y'][1] - sum(t['y'][1] for t in lst), 2)]
    d['cur'], d['cutDay'], d['cutDate'] = m, day, rep['date']
    save(d); print(f"OK: {rep['date']} · mes {MONTHS[m]} · {'cerrado' if closed else 'día '+str(day)} · {len(rep['rows'])} directores")

def render():
    A = load_all(); t = open(P('template.html')).read()
    b64 = base64.b64encode(open(P('logo_s.png'), 'rb').read()).decode() if os.path.exists(P('logo_s.png')) else open(P('logo_s.b64')).read().strip()
    logo = 'data:image/png;base64,' + b64
    open(P('crecimiento-hycite.html'), 'w').write(t.replace('__LOGO__', logo).replace('__DATA__', json.dumps(A, separators=(',', ':'), ensure_ascii=False)))
    print('render OK', P('crecimiento-hycite.html'))

def check():
    d = load(); lst = d['T']; cur = d['cur']
    for k in range(cur + 1):
        assert abs(sum(t['a'][k] for t in lst) - d['nat']['m25'][k]) < 2, k
        assert abs(sum(t['b'][k] for t in lst) - d['nat']['m26'][k]) < 2, k
    print('mensual = nacional OK hasta', MONTHS[cur])
    bad = [(t['id'], round(t['y'][1] - sum(t['b'][:cur + 1]))) for t in lst if abs(t['y'][1] - sum(t['b'][:cur + 1])) > 2]
    print('YTD 2026 oficial vs suma mensual (dif > $2):', bad or 'ninguna')

if __name__ == '__main__':
    {'apply': lambda: apply(sys.argv[2]), 'render': render, 'check': check}[sys.argv[1]]()
