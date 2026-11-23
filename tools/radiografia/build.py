#!/usr/bin/env python3
"""Arma el modelo de la Radiografía + estructura de equipos y genera:
  - p/radiografia/index.html  (dashboard con datos embebidos)
  - tools/radiografia/out/*.csv (tablas para el Google Sheet "Histórico Radiografía")
  - tools/radiografia/out/resumen.json (para el aviso por WhatsApp)
Uso (desde la raíz del repo): python3 tools/radiografia/build.py
Requiere tools/radiografia/estructura.xlsx (export de DISTRUBUCIONES CHASEP & MEJAB).
"""
import csv, glob, json, os, re, unicodedata, datetime as dt
from collections import defaultdict
import openpyxl

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BASE = os.path.join(ROOT, 'tools', 'radiografia')
DATA, OUT = os.path.join(BASE, 'data'), os.path.join(BASE, 'out')
TPL = os.path.join(BASE, 'template.html')
DEST = os.path.join(ROOT, 'p', 'radiografia', 'index.html')
SERIES = ['compras_territorio', 'compras_compania', 'ordenes', 'reclutamiento', 'ticket_mxn']
YTDK = ['compras_compania', 'compras_territorio', 'ordenes', 'reclutamiento', 'ticket_mxn']
META = {'mor31': 0.10, 'mortot': 0.39, 'recompra': 0.02}  # metas del encabezado del reporte Hycite


def nid(x):
    try:
        return str(int(float(str(x).strip())))
    except Exception:
        return None


def nname(s):
    s = unicodedata.normalize('NFKD', str(s or '')).encode('ascii', 'ignore').decode().upper()
    return set(t for t in re.split(r'[^A-Z]+', s) if len(t) > 2)


def fnum(v):
    try:
        return float(v)
    except Exception:
        return None


def load_estructura():
    wb = openpyxl.load_workbook(os.path.join(BASE, 'estructura.xlsx'), data_only=True)
    st, bajas = {}, {}
    for sh in ('CHASEP', 'MEJAB'):
        for r in wb[sh].iter_rows(min_row=2, values_only=True):
            i = nid(r[0])
            if i:
                st[i] = dict(nombre=str(r[1] or '').strip(), comp=str(r[2] or '').strip(), sub=str(r[3] or '').strip().upper(),
                             red=sh, nivel=str(r[5] or '').strip().upper(), sponsor=nid(r[6]) or '', suc=str(r[7] or '').strip().upper())
    for r in wb['BAJAS'].iter_rows(min_row=2, values_only=True):
        i = nid(r[0])
        if i:
            red = 'MEJAB' if str(r[4] or '').strip().upper() == 'MEJAB' else 'CHASEP'
            bajas[i] = dict(nombre=str(r[1] or '').strip(), comp=str(r[2] or '').strip(), sub=str(r[3] or '').strip().upper(),
                            red=red, nivel=str(r[5] or '').strip().upper(), sponsor=nid(r[6]) or '', fecha_baja=str(r[7] or ''))
    return st, bajas


def load_rx():
    snaps, mens = [], []
    for f in sorted(glob.glob(os.path.join(DATA, '*_snapshot.csv'))):
        snaps += list(csv.DictReader(open(f, encoding='utf-8')))
    for f in sorted(glob.glob(os.path.join(DATA, '*_mensual.csv'))):
        mens += list(csv.DictReader(open(f, encoding='utf-8')))
    return snaps, mens


def main():
    st, bajas = load_estructura()
    snaps, mens = load_rx()
    cortes = sorted({s['corte'] for s in snaps})
    last = {f: max(s['corte'] for s in snaps if s['fuente'] == f) for f in {s['fuente'] for s in snaps}}
    fecha_rep = {(s['corte'], s['fuente']): s['fecha_reporte'] for s in snaps}
    # mensual: gana el corte más reciente
    best = {}
    for m in mens:
        k = (m['dist'], m['kpi'], m['mes'])
        if k not in best or m['corte'] > best[k][0]:
            best[k] = (m['corte'], float(m['valor']))
    meses = sorted({k[2] for k in best})
    meses = [x for x in meses if x >= '2025-01']
    # histórico de indicadores por corte
    hist = defaultdict(dict)
    for s in snaps:
        for k in ('reserva', 'mor31', 'mortot', 'recompra'):
            v = fnum(s[k])
            if v is not None:
                hist[(s['dist'], k)][s['corte']] = round(v, 4)
    # clasificación
    by_name = [(i, nname(v['nombre']) | nname(v['comp'])) for i, v in st.items()]

    def clasif(i, nombre, fuente='13588'):
        if i in st:
            return dict(st[i], clasif='archivo', baja=False)
        if i in bajas:
            return dict(bajas[i], suc='', clasif='bajas', baja=True)
        toks = nname(nombre)
        cand = max(by_name, key=lambda t: len(t[1] & toks)) if by_name else None
        if cand and len(cand[1] & toks) >= 3:
            v = st[cand[0]]
            return dict(v, nombre=nombre, clasif=f'inferido (nombre ≈ {cand[0]})', baja=False)
        return dict(nombre=nombre, comp='', sub='SIN CLASIFICAR', red='MEJAB' if fuente == '29365' else 'CHASEP', nivel='', sponsor='', suc='', clasif='sin clasificar', baja=False)

    dists = []
    for f, c in last.items():
        for s in (x for x in snaps if x['fuente'] == f and x['corte'] == c):
            i = s['dist']
            info = clasif(i, s['distribuidor'], f)
            d = dict(id=i, nombre=info['nombre'] or s['distribuidor'], nombre_rx=s['distribuidor'], razon=s['distribucion'],
                     red=info['red'], sub=info['sub'] or 'SIN CLASIFICAR', comp=info['comp'], nivel=info['nivel'],
                     sponsor=info['sponsor'], suc=info.get('suc', ''), clasif=info['clasif'], baja=info['baja'],
                     fuente=f, corte=c, es_dj=s['dj'].upper() == 'YES', fcr=s['fcr'], fecha_dist=s['fecha_dist'],
                     ciudad=s['ciudad'])
            for k in ('reserva', 'mor31', 'mortot', 'recompra'):
                d[k] = fnum(s[k])
            d['ytd'] = {k: [fnum(s.get(f'{k}_ytd_ant')), fnum(s.get(f'{k}_ytd_act'))] for k in YTDK}
            d['m'] = {k: [round(best[(i, k, m)][1], 2) if (i, k, m) in best else None for m in meses] for k in SERIES}
            d['h'] = {k: hist.get((i, k), {}) for k in ('reserva', 'mortot', 'mor31', 'recompra')}
            dists.append(d)
    if '13588' in {d['id'] for d in dists}:
        for d in dists:
            if d['id'] == '13588':
                d['sub'], d['red'] = 'PNL CHASEP', 'CHASEP'
    if '29365' in {d['id'] for d in dists}:
        for d in dists:
            if d['id'] == '29365':
                d['sub'], d['red'] = 'PNL MEJAB', 'MEJAB'
    # personas del archivo que aún no aparecen en la radiografía (DJs nuevos)
    rx_ids = {d['id'] for d in dists}
    pendientes = [dict(id=i, **v) for i, v in st.items() if i not in rx_ids]

    # alertas
    alerts = []
    ult = len(meses)

    def lastn(arr, n):
        vals = [v for v in arr[:ult]]
        while vals and vals[-1] is None:
            vals.pop()
        return vals[-n:]
    for d in dists:
        if d['baja']:
            continue
        A = []
        if d['mortot'] is not None and d['mortot'] >= META['mortot']:
            A.append(('Morosidad total', f"{d['mortot']*100:.1f}% (meta <39%)", 3))
        if d['mor31'] is not None and d['mor31'] >= META['mor31']:
            A.append(('Morosidad 31+', f"{d['mor31']*100:.1f}% (meta <10%)", 3))
        if d['recompra'] is not None and d['recompra'] >= META['recompra']:
            A.append(('Recompra', f"{d['recompra']*100:.1f}% (meta <2%)", 2))
        a, b = d['ytd']['compras_compania']
        if a and b is not None and a >= 1000 and (b - a) / a <= -0.20:
            A.append(('Caída compras YTD', f"{(b-a)/a*100:.0f}% vs año anterior", 2))
        if not d['es_dj'] and d['id'] not in ('13588', '29365'):
            r3 = lastn(d['m']['reclutamiento'], 3)
            if len(r3) == 3 and sum(v or 0 for v in r3) == 0:
                A.append(('Sin reclutamiento', '0 en los últimos 3 meses', 1))
        o2 = lastn(d['m']['ordenes'], 2)
        if len(o2) == 2 and sum(v or 0 for v in o2) == 0:
            A.append(('Sin órdenes', '0 en los últimos 2 meses', 1))
        for t, det, sev in A:
            alerts.append(dict(id=d['id'], nombre=d['nombre'], red=d['red'], sub=d['sub'], tipo=t, detalle=det, sev=sev))

    # equipos (subterritorio): suma de compras de compañía de sus miembros
    eq = defaultdict(lambda: dict(n=0, dj=0, ytd_ant=0.0, ytd_act=0.0, ord=0.0, rec=0.0, mort=[], alertas=0, m=[0.0]*len(meses)))
    for d in dists:
        if d['baja']:
            continue
        e = eq[(d['red'], d['sub'])]
        e['n'] += 1; e['dj'] += d['es_dj']
        a, b = d['ytd']['compras_compania']
        e['ytd_ant'] += a or 0; e['ytd_act'] += b or 0
        e['ord'] += d['ytd']['ordenes'][1] or 0; e['rec'] += d['ytd']['reclutamiento'][1] or 0
        if d['mortot'] is not None:
            e['mort'].append(d['mortot'])
        for j, v in enumerate(d['m']['compras_compania']):
            e['m'][j] += v or 0
    for a in alerts:
        if (a['red'], a['sub']) in eq:
            eq[(a['red'], a['sub'])]['alertas'] += 1
    equipos = []
    for (red, sub), e in eq.items():
        equipos.append(dict(red=red, sub=sub, n=e['n'], dj=e['dj'], ytd_ant=round(e['ytd_ant'], 2), ytd_act=round(e['ytd_act'], 2),
                            var=(e['ytd_act'] - e['ytd_ant']) / e['ytd_ant'] if e['ytd_ant'] else None,
                            ordenes=e['ord'], reclutamiento=e['rec'],
                            mortot=sum(e['mort']) / len(e['mort']) if e['mort'] else None, alertas=e['alertas'],
                            m=[round(v, 2) for v in e['m']]))
    equipos.sort(key=lambda x: -x['ytd_act'])

    pnl = next((d for d in dists if d['id'] == '13588'), None)
    lc = last.get('13588') or max(last.values())
    model = dict(generado=dt.datetime.now(dt.timezone(dt.timedelta(hours=-6))).strftime('%Y-%m-%d %H:%M'),
                 corte=lc, fecha_reporte=fecha_rep.get((lc, '13588'), ''), cortes=cortes, ultimos=last,
                 meses=meses, dists=dists, equipos=equipos, alertas=alerts, pendientes=pendientes, meta=META,
                 territorio=dict(m=pnl['m']['compras_territorio'] if pnl else [],
                                 ytd=pnl['ytd']['compras_territorio'] if pnl else [None, None],
                                 ordenes=pnl['ytd']['ordenes'] if pnl else [None, None],
                                 recl=pnl['ytd']['reclutamiento'] if pnl else [None, None]))
    # HTML
    html = open(TPL, encoding='utf-8').read().replace('/*__DATA__*/null', json.dumps(model, ensure_ascii=False, separators=(',', ':')))
    os.makedirs(os.path.dirname(DEST), exist_ok=True)
    open(DEST, 'w', encoding='utf-8').write(html)

    # CSV para Google Sheet
    os.makedirs(OUT, exist_ok=True)
    def wcsv(name, header, rows):
        with open(os.path.join(OUT, name), 'w', newline='', encoding='utf-8') as f:
            w = csv.writer(f); w.writerow(header); w.writerows(rows)
    wcsv('equipos.csv', ['Red', 'Subterritorio', 'Integrantes', 'DJs', 'Compras compañía YTD año ant (USD)', 'Compras compañía YTD año act (USD)',
                         'Var %', 'Órdenes YTD', 'Reclutamiento YTD', 'Morosidad total prom', 'Alertas'],
         [[e['red'], e['sub'], e['n'], e['dj'], e['ytd_ant'], e['ytd_act'], round(e['var'], 4) if e['var'] is not None else '',
           e['ordenes'], e['reclutamiento'], round(e['mortot'], 4) if e['mortot'] is not None else '', e['alertas']] for e in equipos])
    wcsv('estructura.csv', ['ID', 'Nombre', 'Red', 'Subterritorio', 'Compañía', 'Nivel', 'Sponsor', 'Sucursal', 'Es DJ', 'Clasificación',
                            'Corte', 'Reserva', 'Morosidad 31+', 'Morosidad total', 'Recompra',
                            'Compras compañía YTD ant', 'Compras compañía YTD act', 'Órdenes YTD', 'Reclutamiento YTD'],
         [[d['id'], d['nombre'], d['red'], d['sub'], d['comp'], d['nivel'], d['sponsor'], d['suc'], 'SÍ' if d['es_dj'] else 'NO', d['clasif'],
           d['corte'], d['reserva'], d['mor31'], d['mortot'], d['recompra'], d['ytd']['compras_compania'][0], d['ytd']['compras_compania'][1],
           d['ytd']['ordenes'][1], d['ytd']['reclutamiento'][1]] for d in sorted(dists, key=lambda x: (x['red'], x['sub'], x['comp'], x['nombre']))])
    wcsv('alertas.csv', ['ID', 'Nombre', 'Red', 'Subterritorio', 'Alerta', 'Detalle'],
         [[a['id'], a['nombre'], a['red'], a['sub'], a['tipo'], a['detalle']] for a in sorted(alerts, key=lambda a: (-a['sev'], a['sub']))])
    idx = {d['id']: d for d in dists}
    hrows = []
    for s in snaps:
        info = idx.get(s['dist']) or clasif(s['dist'], s['distribuidor'], s['fuente'])
        hrows.append([s['corte'], s['fuente'], s['fecha_reporte'], s['dist'], s['distribuidor'], info.get('red', ''), info.get('sub', ''),
                      s['dj'], s['reserva'], s['mor31'], s['mortot'], s['recompra'],
                      s['compras_compania_ytd_ant'], s['compras_compania_ytd_act'], s['compras_territorio_ytd_ant'], s['compras_territorio_ytd_act'],
                      s['ordenes_ytd_ant'], s['ordenes_ytd_act'], s['reclutamiento_ytd_ant'], s['reclutamiento_ytd_act']])
    hrows.sort(key=lambda r: (r[0], r[1], r[5], r[6]), reverse=False)
    wcsv('historico_cortes.csv', ['Corte', 'PNL', 'Fecha reporte', 'ID', 'Distribuidor', 'Red', 'Subterritorio', 'DJ', 'Reserva', 'Morosidad 31+',
                                  'Morosidad total', 'Recompra', 'Compras compañía YTD ant', 'Compras compañía YTD act',
                                  'Compras territorio YTD ant', 'Compras territorio YTD act', 'Órdenes YTD ant', 'Órdenes YTD act',
                                  'Reclutamiento YTD ant', 'Reclutamiento YTD act'], hrows)
    mrows = []
    for d in dists:
        for j, m in enumerate(meses):
            vals = [d['m'][k][j] for k in SERIES]
            if any(v not in (None, 0) for v in vals):
                mrows.append([m, d['id'], d['nombre'], d['red'], d['sub']] + ['' if v is None else v for v in vals])
    wcsv('mensual.csv', ['Mes', 'ID', 'Nombre', 'Red', 'Subterritorio', 'Compras territorio USD', 'Compras compañía USD', 'Órdenes',
                         'Reclutamiento', 'Ticket promedio MXN'], sorted(mrows))
    res = dict(corte=lc, fecha_reporte=model['fecha_reporte'], distribuidores=len([d for d in dists if not d['baja']]),
               territorio_ytd=model['territorio']['ytd'],
               ordenes_ytd=[sum(d['ytd']['ordenes'][j] or 0 for d in dists if not d['baja'] and d['fuente'] == '13588') for j in (0, 1)],
               recl_ytd=[sum(d['ytd']['reclutamiento'][j] or 0 for d in dists if not d['baja'] and d['fuente'] == '13588') for j in (0, 1)],
               ultimo_mes=meses[-1] if meses else '', ultimo_mes_territorio=(pnl['m']['compras_territorio'][-1] if pnl else None),
               alertas=len(alerts), alertas_por_tipo={t: sum(1 for a in alerts if a['tipo'] == t) for t in sorted({a['tipo'] for a in alerts})},
               top=[(e['sub'], e['var']) for e in sorted([e for e in equipos if e['var'] is not None and e['red'] == 'CHASEP' and not e['sub'].startswith('PNL')], key=lambda e: -e['var'])],
               sin_clasificar=[(d['id'], d['nombre']) for d in dists if d['clasif'] == 'sin clasificar'],
               inferidos=[(d['id'], d['nombre'], d['clasif']) for d in dists if d['clasif'].startswith('inferido')],
               bajas_en_rx=[(d['id'], d['nombre']) for d in dists if d['baja']],
               pendientes=len(pendientes))
    json.dump(res, open(os.path.join(OUT, 'resumen.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(json.dumps(res, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
