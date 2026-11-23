#!/usr/bin/env python3
"""Prepara lo que la tarea programada escribe en el Google Sheet "Histórico Radiografía CHASEP"
(1Ktd5ux1TyOiEmkCKDTWH90A8tkvhMVqK_X2Ib87m6I0) y el texto del aviso de WhatsApp.
Uso: python3 tools/radiografia/sheet_rows.py <corte AAAAMM> <PNL 13588|29365>
Escribe tools/radiografia/out/sheet_<corte>_<pnl>.json con:
  estructura   -> filas completas (sin encabezado) para reescribir Estructura!A2
  alertas      -> filas completas (sin encabezado) para reescribir Alertas!A2
  historico    -> filas del corte para AGREGAR al final de 'Histórico cortes'
  mensual      -> filas del último mes del corte para AGREGAR al final de 'Mensual'
  equipos      -> [red, subterritorio] que deben existir en Equipos (col A:B)
  mensaje      -> líneas del aviso de WhatsApp (escribir cada una con shift+Enter entre ellas)
"""
import csv, json, os, sys
B = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(B, 'out')
corte, pnl = sys.argv[1], sys.argv[2]
rd = lambda n: list(csv.reader(open(os.path.join(OUT, n), encoding='utf-8')))[1:]
def num(v):
    try: return float(v)
    except Exception: return v
est = [[num(x) if i >= 10 else x for i, x in enumerate(r)] for r in rd('estructura.csv')]
for r in est: r[0] = str(r[0])
hist = [[num(x) if i >= 8 else x for i, x in enumerate(r)] for r in rd('historico_cortes.csv') if r[0] == corte and r[1] == pnl]
men_all = rd('mensual.csv')
mes = max(r[0] for r in men_all)
ids = {r[3] for r in hist}
men = [[num(x) if i >= 5 else x for i, x in enumerate(r)] for r in men_all if r[1] in ids and r[0] == mes]
res = json.load(open(os.path.join(OUT, 'resumen.json'), encoding='utf-8'))
eqs = rd('equipos.csv')
MES = ['ene', 'feb', 'mar', 'abr', 'may', 'jun', 'jul', 'ago', 'sep', 'oct', 'nov', 'dic']
def ml(c): return f"{MES[int(c[4:6])-1]} {c[2:4]}"
def k(v): return f"${v/1e6:.2f}M" if abs(v) >= 1e6 else f"${v/1e3:.1f}k"
def p(v): return f"{'▲' if v >= 0 else '▼'}{abs(v)*100:.1f}%"
lines = []
if pnl == '13588':
    a, b = res['territorio_ytd']
    lines.append(f"🤖 📊 *Radiografía CHASEP · corte {ml(corte)}*")
    lines.append(f"Compras territorio YTD: {k(b)} USD ({p((b-a)/a)} vs año anterior)")
    eq = [(e[1], float(e[6])) for e in eqs if e[0] == 'CHASEP' and e[6] not in ('', None) and not e[1].startswith(('PNL', 'SIN'))]
    eq.sort(key=lambda x: -x[1])
    up = [f"{s.title().replace('Hl ', 'HL ').replace('Hlc', 'HLC')} {v*100:+.0f}%" for s, v in eq if v > 0][:3]
    dn = [f"{s.title().replace('Hl ', 'HL ').replace('Hlc', 'HLC')} {v*100:+.0f}%" for s, v in eq[::-1] if v < 0][:3]
    if up: lines.append('Crecen: ' + ', '.join(up))
    if dn: lines.append('Caen: ' + ', '.join(dn))
else:
    lines.append(f"🤖 📊 *Radiografía MEJAB (Abdul) · corte {ml(corte)}*")
    eq = [(e[1], float(e[6])) for e in eqs if e[0] == 'MEJAB' and e[6] not in ('', None) and not e[1].startswith(('PNL', 'SIN'))]
    lines.append('Equipos YTD: ' + ', '.join(f"{s.title()} {v*100:+.0f}%" for s, v in sorted(eq, key=lambda x: -x[1])))
at = res['alertas_por_tipo']
lines.append(f"⚠️ {res['alertas']} alertas" + (f" ({at.get('Morosidad total', 0)} con morosidad total arriba de 39%)" if at.get('Morosidad total') else ''))
if res['sin_clasificar']:
    lines.append('🔎 Sin clasificar en tu archivo de distribuciones: ' + ', '.join(f"{n.title()} ({i})" for i, n in res['sin_clasificar']))
lines.append('')
lines.append('👉 https://rp13588-eng.github.io/reportes-chasep/p/radiografia/')
lines.append('Histórico en Sheets: https://docs.google.com/spreadsheets/d/1Ktd5ux1TyOiEmkCKDTWH90A8tkvhMVqK_X2Ib87m6I0/edit')
outp = os.path.join(OUT, f'sheet_{corte}_{pnl}.json')
json.dump(dict(corte=corte, pnl=pnl, estructura=est, alertas=rd('alertas.csv'), historico=hist, mensual=men,
               equipos=[[e[0], e[1]] for e in eqs], mensaje=lines), open(outp, 'w', encoding='utf-8'), ensure_ascii=False)
print(outp, f"estructura={len(est)} alertas={len(rd('alertas.csv'))} historico={len(hist)} mensual={len(men)} (mes {mes})")
print('\n'.join(lines))
