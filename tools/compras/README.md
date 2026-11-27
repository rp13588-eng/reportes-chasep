# Compras CHASEP · constructor

`build.py` convierte el Excel de compras que manda Vanessa (formato "TerritoryPurchases" del portal Hycite) en
`data/compras/<id>.json` y agrega el corte al inicio de `data/compras/index.json` (el dashboard de la raíz los lee).

```
python3 -I tools/compras/build.py /home/claude/compras/<id>/ /home/claude/distrib.xlsx <id>
```
- Lee la hoja "TODOS" (USD) si existe: columna D = "ID-NOMBRE", J = compras propias del periodo, K = año anterior, fila TOTALS.
- Valida que la suma de distribuidores cuadre con TOTALS (±1 USD); si no, sale con ERROR y no escribe nada.
- Clasifica con la hoja "DISTRUBUCIONES CHASEP & MEJAB" (export CSV público, `estructura.py`, mismas reglas que hycite-reportes):
  st = subterritorio, co = compañía (sube hasta quien se cuenta a sí mismo), pr = premier, ld = líder de su compañía,
  bj = baja (pestaña BAJAS), nv = nuevo (sin compras el año anterior). Quien no está en la hoja = "SIN CLASIFICAR".
- Imprime un JSON con totales, variación y los IDs sin clasificar (para el aviso).
- Si el formato del Excel cambia ("no encontré filas ID-NOMBRE"), la tarea avisa a Alejandro y no publica.
