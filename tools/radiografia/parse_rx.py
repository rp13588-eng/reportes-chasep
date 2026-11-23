#!/usr/bin/env python3
"""Parser de la Radiografía mensual de Hycite (PNL 13588 / 29365).

Uso: python3 parse_rx.py <archivo.xlsx> <corte AAAAMM> <fuente> <salida_dir>
Escribe/actualiza en salida_dir:
  <corte>_<fuente>_snapshot.csv -> 1 fila por (corte, fuente, dist): datos del distribuidor + indicadores ACTUAL + YTD
  <corte>_<fuente>_mensual.csv  -> 1 fila por (corte, fuente, dist, kpi, mes AAAA-MM): valor
Re-procesar un corte sobrescribe sus 2 archivos (idempotente).
"""
import csv, datetime as dt, os, re, sys
import openpyxl

KPIS = {
    'RESERVA': 'reserva', 'MOROSIDAD 31+': 'mor31', 'MOROSIDAD TOTAL': 'mortot',
    'RECOMPRA': 'recompra', 'COMPRAS DE TERRITORIO USD': 'compras_territorio',
    'COMPRAS COMPAÑÍA USD': 'compras_compania', 'COMPRAS NO. DIRECTO USD': 'compras_no_directo',
    'RECLUTAMIENTO': 'reclutamiento', 'ORDENES': 'ordenes', 'TICKET PROMEDIO MXN': 'ticket_mxn',
    'AGREGADOS': 'agregados',
}
INFO = ['PNL', 'PREMIER', 'DIST', 'DISTRIBUCIÓN', 'DISTRIBUIDOR', 'DJ', 'NIVEL', 'FCR',
        'FECHA DJ', 'FECHA DIST', 'TIEMPO DJ', 'ESTADO (Oficina)', 'CIUDAD (Oficina)']
INFO_KEYS = ['pnl', 'premier', 'dist', 'distribucion', 'distribuidor', 'dj', 'nivel_num', 'fcr',
             'fecha_dj', 'fecha_dist', 'tiempo_dj', 'estado', 'ciudad']
SNAP_COLS = ['corte', 'fuente', 'fecha_reporte'] + INFO_KEYS + \
    ['reserva', 'mor31', 'mortot', 'recompra'] + \
    [f'{k}_ytd_{s}' for k in ['compras_territorio', 'compras_compania', 'compras_no_directo',
                              'reclutamiento', 'ordenes', 'ticket_mxn'] for s in ('ant', 'act')]
MENS_COLS = ['corte', 'fuente', 'dist', 'kpi', 'mes', 'valor']


def norm(v):
    if isinstance(v, dt.datetime):
        return v.date().isoformat()
    if v is None:
        return ''
    if isinstance(v, str):
        return v.strip()
    return v


def parse(path, corte, fuente):
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    ws = wb.worksheets[0]
    rows = list(ws.iter_rows(values_only=True))
    r1, r2 = list(rows[0]), list(rows[1])
    fecha_rep = next((norm(v) for v in r1 if isinstance(v, dt.datetime)), '')
    # columnas de info
    hdr = {str(v).strip(): i for i, v in enumerate(r2) if isinstance(v, str)}
    info_idx = [hdr.get(h) for h in INFO]
    # bloques KPI
    starts = sorted((i, KPIS[str(v).strip()]) for i, v in enumerate(r1)
                    if isinstance(v, str) and str(v).strip() in KPIS)
    blocks = []
    for n, (i, k) in enumerate(starts):
        end = starts[n + 1][0] if n + 1 < len(starts) else len(r2)
        blocks.append((k, i, end))
    snaps, mens = [], []
    for r in rows[2:]:
        r = list(r) + [None] * (len(r2) - len(r))
        d = r[info_idx[2]] if info_idx[2] is not None else None
        if not isinstance(d, (int, float)) or d <= 0:
            continue
        s = {'corte': corte, 'fuente': fuente, 'fecha_reporte': fecha_rep}
        for k, i in zip(INFO_KEYS, info_idx):
            s[k] = norm(r[i]) if i is not None else ''
        s['dist'] = int(d)
        s['pnl'] = int(s['pnl']) if isinstance(s['pnl'], (int, float)) else s['pnl']
        for k, a, b in blocks:
            for c in range(a, b):
                lab, val = r2[c], r[c]
                if isinstance(lab, str) and ('ACTUAL' in lab.upper() or 'MENOR' in lab.upper()):
                    s[k] = val if val not in (None, '') else ''
                elif isinstance(lab, str) and re.match(r'^\d{4} YTD$', lab.strip()):
                    yr = int(lab[:4])
                    s.setdefault('_ytd', {}).setdefault(k, {})[yr] = val
                elif isinstance(lab, (dt.datetime, dt.date)):
                    if val not in (None, '') and isinstance(val, (int, float)):
                        mens.append({'corte': corte, 'fuente': fuente, 'dist': s['dist'], 'kpi': k,
                                     'mes': f'{lab.year}-{lab.month:02d}', 'valor': val})
        ytd = s.pop('_ytd', {})
        for k, yrs in ytd.items():
            if len(yrs) >= 2:
                ys = sorted(yrs)
                s[f'{k}_ytd_ant'], s[f'{k}_ytd_act'] = yrs[ys[-2]], yrs[ys[-1]]
        snaps.append(s)
    return snaps, mens


def upsert(path, cols, new, corte, fuente):
    old = []
    if os.path.exists(path):
        with open(path, newline='', encoding='utf-8') as f:
            old = [r for r in csv.DictReader(f) if not (r['corte'] == corte and r['fuente'] == fuente)]
    with open(path, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction='ignore')
        w.writeheader()
        for r in old + new:
            w.writerow(r)


if __name__ == '__main__':
    src, corte, fuente, out = sys.argv[1:5]
    os.makedirs(out, exist_ok=True)
    snaps, mens = parse(src, corte, fuente)
    for name, cols, rows in (('snapshot', SNAP_COLS, snaps), ('mensual', MENS_COLS, mens)):
        with open(os.path.join(out, f'{corte}_{fuente}_{name}.csv'), 'w', newline='', encoding='utf-8') as f:
            w = csv.DictWriter(f, fieldnames=cols, extrasaction='ignore'); w.writeheader(); w.writerows(rows)
    print(f'{corte} {fuente}: {len(snaps)} distribuidores, {len(mens)} valores mensuales')
