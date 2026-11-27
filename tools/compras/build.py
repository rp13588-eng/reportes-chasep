#!/usr/bin/env python3
"""Reporte Compras CHASEP: Excel de Vanessa (TerritoryPurchases del portal Hycite) -> data/compras/<periodo_id>.json
y data/compras/index.json para el dashboard https://rp13588-eng.github.io/reportes-chasep/

Uso (dos formas):
  python3 -I tools/compras/build.py <carpeta_o_archivo> <distrib.xlsx> <id>          (la usa la tarea programada)
  python3 -I tools/compras/build.py <carpeta_o_archivo> <id> "<periodo>" "<periodo comparativo>"
  <carpeta>: toma el .xls/.xlsx cuyo nombre diga "compra"/"purchase" (si no, el primero). Si no das los textos
  del periodo, se leen del encabezado del Excel ("MES HASTA LA FECHA - <MES AAAA>" o "AAAA-MM-DD - AAAA-MM-DD").
  Opcional: --fecha AAAA-MM-DD (fecha de generado; por omisión hoy).

Formato esperado (el mismo del Excel "Export > EXCEL" del portal y de los reportes de Vanessa):
  hoja "TODOS" si existe (USD; se ignoran "MX" y "Vendedor"); columna D = "ID-NOMBRE";
  columna J = compras propias periodo actual; columna K = propias año anterior; fila "TOTALS" al final.
Clasificación: hoja "DISTRUBUCIONES CHASEP & MEJAB" (tools/compras/estructura.py).
Valida que la suma de filas cuadre con TOTALS (tolerancia 1 USD). Si el formato no se reconoce, sale con error
y NO escribe nada (la tarea debe avisar a Alejandro).
"""
import json, os, re, sys, datetime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import estructura  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def num(v):
    try:
        if v is None or (isinstance(v, float) and v != v):
            return 0.0
        if isinstance(v, str):
            v = v.replace(",", "").replace("$", "").strip() or 0
        return round(float(v), 2)
    except Exception:
        return None


def leer(path):
    import pandas as pd
    xl = pd.ExcelFile(path)
    hoja = next((h for h in xl.sheet_names if h.strip().upper() == "TODOS"), xl.sheet_names[0])
    df = xl.parse(hoja, header=None)
    filas, total = [], None
    for _, r in df.iterrows():
        vals = list(r.values) + [None] * 12
        d = str(vals[3]) if vals[3] is not None else ""
        m = re.match(r"^\s*(\d{3,7})\s*-\s*(.+?)\s*$", d)
        if m:
            a, b = num(vals[9]), num(vals[10])
            if a is None or b is None:
                sys.exit(f"ERROR: montos no numéricos en la fila de {m.group(1)}: J={vals[9]!r} K={vals[10]!r}")
            filas.append((m.group(1), m.group(2).upper(), a, b))
        elif any(isinstance(x, str) and x.strip().upper().startswith("TOTALS") for x in vals[:6]):
            total = (num(vals[9]), num(vals[10]))
    if not filas:
        sys.exit(f"ERROR: no encontré filas 'ID-NOMBRE' en la columna D de la hoja '{hoja}'. Formato no reconocido.")
    return hoja, filas, total


MESES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]
MESES_L = ["ENERO", "FEBRERO", "MARZO", "ABRIL", "MAYO", "JUNIO", "JULIO", "AGOSTO", "SEPTIEMBRE", "OCTUBRE", "NOVIEMBRE", "DICIEMBRE"]


def elegir(path):
    if os.path.isdir(path):
        xs = sorted(f for f in os.listdir(path) if f.lower().endswith((".xls", ".xlsx")))
        if not xs:
            sys.exit(f"ERROR: no hay archivos .xls/.xlsx en {path}")
        pref = [f for f in xs if re.search(r"compra|purchase", f, re.I)]
        return os.path.join(path, (pref or xs)[0])
    return path


def periodo_de_excel(path):
    import pandas as pd
    xl = pd.ExcelFile(path)
    hoja = next((h for h in xl.sheet_names if h.strip().upper() == "TODOS"), xl.sheet_names[0])
    df = xl.parse(hoja, header=None, nrows=11)
    texto = " | ".join(str(v) for v in df.values.flatten() if v is not None and str(v) != "nan")
    m = re.search(r"(\d{4})-(\d{2})-(\d{2})\s*-\s*(\d{4})-(\d{2})-(\d{2})", texto)
    if m:
        y1, m1, d1, y2, m2, d2 = map(int, m.groups())
        a = f"{d1} {MESES[m1-1]} – {d2} {MESES[m2-1]} {y2}"
        b = f"{d1} {MESES[m1-1]} – {d2} {MESES[m2-1]} {y2-1}"
        return a, b
    m = re.search(r"HASTA LA FECHA\s*-\s*([A-ZÁÉÍÓÚ]+)\s+(\d{4})", texto.upper())
    if m and m.group(1) in MESES_L:
        k = MESES_L.index(m.group(1)); y = int(m.group(2))
        return f"{MESES[k]} {y} a la fecha", f"{MESES[k]} {y-1} mismo tramo"
    return None, None


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    fecha = datetime.date.today().isoformat()
    if "--fecha" in sys.argv:
        fecha = sys.argv[sys.argv.index("--fecha") + 1]
        args = [a for a in args if a != fecha]
    if len(args) >= 3 and args[1].lower().endswith(".xlsx") and len(args) == 3:
        path, pid, per, per_cmp = args[0], args[2], None, None   # forma de la tarea: <carpeta> <distrib.xlsx> <id>
    elif len(args) >= 4:
        path, pid, per, per_cmp = args[:4]
    elif len(args) == 2:
        path, pid, per, per_cmp = args[0], args[1], None, None
    else:
        sys.exit(__doc__)
    path = elegir(path)
    if not per:
        per, per_cmp = periodo_de_excel(path)
        per = per or pid
        per_cmp = per_cmp or "mismo periodo año anterior"
    hoja, filas, total = leer(path)
    sa, sb = round(sum(f[2] for f in filas), 2), round(sum(f[3] for f in filas), 2)
    avisos = []
    if total:
        if abs(sa - (total[0] or 0)) > 1 or abs(sb - (total[1] or 0)) > 1:
            sys.exit(f"ERROR: la suma de distribuidores no cuadra con TOTALS: actual {sa} vs {total[0]}, anterior {sb} vs {total[1]}")
    else:
        avisos.append("El Excel no trae fila TOTALS: no se pudo validar la suma.")

    e = estructura.construir()
    dist_e, comps = e["distribuidores"], e["companias"]
    activos_raw, _ = estructura.cargar()
    salida, sin = [], []
    for i, nm, a, b in filas:
        x = dist_e.get(i)
        if x:
            c = x["c"]
            co = (activos_raw.get(c, {}).get("COMPAÑÍA") or comps.get(c, {}).get("nombre") or c).upper()
            st, pr, bj, ld = x["s"] or "SIN CLASIFICAR", x["pr"] or "CHASEP", x["est"] != "activo", (c == i and x["est"] == "activo")
        else:
            st, co, pr, bj, ld = "SIN CLASIFICAR", "SIN CLASIFICAR", "CHASEP", False, False
            if a > 0:
                sin.append(f"{i} {nm}")
        salida.append({"id": i, "nm": nm, "st": st, "co": co, "pr": pr, "ld": ld, "bj": bj,
                       "a": a, "b": b, "nv": (b == 0 and not bj)})
    salida.sort(key=lambda d: -d["a"])
    nota = "Clasificación por la hoja DISTRUBUCIONES CHASEP & MEJAB al " + fecha + "."
    if sin:
        nota += " Sin clasificar (compraron y no están en la hoja): " + ", ".join(sin[:15]) + "."
    data = {"periodo": per, "periodo_comparativo": per_cmp, "periodo_id": pid, "generado": fecha,
            "nota": nota, "dist": salida}
    os.makedirs(os.path.join(ROOT, "data", "compras"), exist_ok=True)
    out = os.path.join(ROOT, "data", "compras", pid + ".json")
    json.dump(data, open(out, "w"), ensure_ascii=False, indent=1)
    idx_p = os.path.join(ROOT, "data", "compras", "index.json")
    idx = json.load(open(idx_p)) if os.path.exists(idx_p) else {"periodos": []}
    idx["periodos"] = [p for p in idx["periodos"] if p.get("id") != pid]
    idx["periodos"].insert(0, {"id": pid, "label": f"{per} (vs {per_cmp})", "archivo": f"data/compras/{pid}.json",
                               "generado": fecha, "tipo": "compras"})
    json.dump(idx, open(idx_p, "w"), ensure_ascii=False, indent=2)
    tot_a = sum(d["a"] for d in salida); tot_b = sum(d["b"] for d in salida)
    var = (tot_a / tot_b - 1) * 100 if tot_b else 0
    print(json.dumps({"ok": True, "hoja": hoja, "distribuidores": len(salida), "total_actual": round(tot_a, 2),
                      "total_anterior": round(tot_b, 2), "variacion_pct": round(var, 1), "sin_clasificar": sin,
                      "avisos": avisos + e["avisos"][:5], "archivo": os.path.relpath(out, ROOT)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
