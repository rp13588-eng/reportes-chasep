"""Genera p/iteam-bootcamp/participantes.json.
Uso: python3 -I build_participantes.py CHASEP.json BAJAS.json SALIDA.json FECHA
CHASEP.json / BAJAS.json = lista de filas (sin encabezado) tal como las regresa Google Sheets get_values
de las pestañas CHASEP (A:H) y BAJAS (A:H) del Sheet "DISTRUBUCIONES CHASEP & MEJAB"."""
import json, re, sys
from collections import Counter
chasep = json.load(open(sys.argv[1], encoding='utf-8'))
bajas = {str(r[0]).strip() for r in json.load(open(sys.argv[2], encoding='utf-8')) if r and str(r[0]).strip()}
SUBS = {'FORZA', 'DAMARO', 'HENKEM', 'ARLISSA'}
SMALL = {'de', 'la', 'del', 'y', 'las', 'los'}
def nice(s):
    s = re.sub(r'\s+', ' ', s).strip()
    return ' '.join(w.capitalize() if w.lower() not in SMALL else w.lower() for w in s.split(' '))
res = []
for r in chasep:
    r = [str(x).strip() for x in r] + [''] * 8
    i, nom, comp, sub, prem, niv, spon = r[:7]
    if not i or sub not in SUBS or i in bajas:
        continue
    m = re.search(r'\(([^)]+)\)', nom)  # paréntesis = código a nombre de familiar; lo trabaja quien está entre paréntesis
    res.append({'id': i, 'nombre': nice(m.group(1)) if m else nice(nom), 'titular': nice(nom) if m else None,
                'sub': sub, 'nivel': niv, 'tipo': 'DJ' if niv == 'DJ' else 'Distribuidor',
                'sponsor': spon, 'pareja': ' & ' in nom, 'anfitrion': i == '13588'})
json.dump({'actualizado': sys.argv[4], 'participantes': res}, open(sys.argv[3], 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(len(res), dict(Counter((p['sub'], p['tipo']) for p in res if not p['anfitrion'])))
