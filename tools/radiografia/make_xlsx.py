#!/usr/bin/env python3
"""Arma Historico_Radiografia.xlsx (carga inicial del Google Sheet) desde tools/radiografia/out/*.csv."""
import csv, os, sys
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'out')
NUMCOLS = lambda h: h not in ('Corte', 'PNL', 'Fecha reporte', 'ID', 'Distribuidor', 'Nombre', 'Red', 'Subterritorio', 'DJ', 'Es DJ',
                               'Compañía', 'Nivel', 'Sponsor', 'Sucursal', 'Clasificación', 'Alerta', 'Detalle', 'Mes')
def load(n):
    r = list(csv.reader(open(os.path.join(OUT, n), encoding='utf-8')))
    h = r[0]
    rows = [[(float(v) if v not in ('', None) and NUMCOLS(h[i]) else v) for i, v in enumerate(x)] for x in r[1:]]
    return h, rows
wb = Workbook(); hdr = Font(bold=True, color='FFFFFF', name='Arial'); fill = PatternFill('solid', fgColor='0A2A5E')
def sheet(title, h, rows, fmts={}):
    ws = wb.create_sheet(title); ws.append(h)
    for r in rows: ws.append(r)
    for c in ws[1]: c.font = hdr; c.fill = fill; c.alignment = Alignment(wrap_text=True, vertical='center')
    ws.freeze_panes = 'A2'
    for i, name in enumerate(h, 1):
        col = ws.cell(1, i).column_letter
        ws.column_dimensions[col].width = 34 if name in ('Distribuidor', 'Nombre', 'Compañía', 'Detalle') else 14
        f = fmts.get(name)
        if f:
            for c in ws[col][1:]: c.number_format = f
    return ws
P = '0.0%;(0.0%);"-"'; U = '$#,##0;($#,##0);"-"'; N = '#,##0;(#,##0);"-"'
eh, er = load('estructura.csv')
ws = sheet('Estructura', eh, er, {'Reserva': P, 'Morosidad 31+': '0.00%', 'Morosidad total': P, 'Recompra': P,
           'Compras compañía YTD ant': U, 'Compras compañía YTD act': U, 'Órdenes YTD': N, 'Reclutamiento YTD': N})
n = len(er) + 1
# Equipos con fórmulas sobre Estructura
subs = sorted({(r[2], r[3]) for r in er})
q = wb.create_sheet('Equipos', 0)
q.append(['Red', 'Subterritorio', 'Integrantes', 'DJs', 'Compras compañía YTD año anterior (USD)', 'Compras compañía YTD (USD)', 'Variación',
          'Órdenes YTD', 'Reclutamiento YTD', 'Morosidad total promedio', 'Alertas'])
for i, (red, sub) in enumerate(subs, 2):
    c = f'Estructura!$C:$C,$A{i},Estructura!$D:$D,$B{i}'
    q.append([red, sub, f'=COUNTIFS({c},Estructura!$J:$J,"<>bajas")', f'=COUNTIFS({c},Estructura!$I:$I,"SÍ",Estructura!$J:$J,"<>bajas")',
              f'=SUMIFS(Estructura!$P:$P,{c},Estructura!$J:$J,"<>bajas")', f'=SUMIFS(Estructura!$Q:$Q,{c},Estructura!$J:$J,"<>bajas")',
              f'=IF(E{i}=0,0,F{i}/E{i}-1)', f'=SUMIFS(Estructura!$R:$R,{c},Estructura!$J:$J,"<>bajas")',
              f'=SUMIFS(Estructura!$S:$S,{c},Estructura!$J:$J,"<>bajas")',
              f'=IFERROR(AVERAGEIFS(Estructura!$N:$N,{c},Estructura!$J:$J,"<>bajas"),0)',
              f'=COUNTIFS(Alertas!$C:$C,$A{i},Alertas!$D:$D,$B{i})'])
for cel in q[1]: cel.font = hdr; cel.fill = fill; cel.alignment = Alignment(wrap_text=True, vertical='center')
q.freeze_panes = 'C2'
for col, w, f in [('A', 10, None), ('B', 18, None), ('C', 12, N), ('D', 8, N), ('E', 18, U), ('F', 18, U), ('G', 11, P), ('H', 12, N), ('I', 14, N), ('J', 14, P), ('K', 9, N)]:
    q.column_dimensions[col].width = w
    if f:
        for cel in q[col][1:]: cel.number_format = f
ah, ar = load('alertas.csv'); sheet('Alertas', ah, ar)
hh, hr = load('historico_cortes.csv')
sheet('Histórico cortes', hh, hr, {k: (P if k in ('Reserva', 'Morosidad total', 'Recompra') else '0.00%' if k == 'Morosidad 31+' else U if 'Compras' in k else N)
                                     for k in hh if NUMCOLS(k)})
mh, mr = load('mensual.csv')
sheet('Mensual', mh, mr, {k: (U if 'USD' in k or 'MXN' in k else N) for k in mh if NUMCOLS(k)})
del wb['Sheet']
dst = sys.argv[1] if len(sys.argv) > 1 else os.path.join(OUT, 'Historico_Radiografia.xlsx')
wb.save(dst); print(dst, os.path.getsize(dst))
