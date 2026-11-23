# Radiografía Hycite → histórico + estructura de equipos

Fuente: correo mensual "ALEJANDRO SEPULVEDA RADIOGRAFIA AAAAMM" (pgaribi@hycite.com → rp13588@gmail.com, adjunto .xlsx)
y, cuando lo reenvía, "ABDUL MEJIA RADIOGRAFIA AAAAMM" (abdulmej14@gmail.com, PNL 29365 / MEJAB).
Estructura: Google Sheet "DISTRUBUCIONES CHASEP & MEJAB" (1Z0X2oGDuehvK660O_l5Y9CwYYbbWQmEIY-fi3GOQE6I), hojas CHASEP, MEJAB, BAJAS.

## Procesar un corte nuevo (desde la raíz del repo)
1. Guardar el adjunto en `tools/radiografia/xlsx/<AAAAMM>_<13588|29365>.xlsx`.
2. `python3 tools/radiografia/parse_rx.py tools/radiografia/xlsx/<AAAAMM>_<PNL>.xlsx <AAAAMM> <PNL> tools/radiografia/data`
3. Exportar la estructura vigente a `tools/radiografia/estructura.xlsx` (Drive export xlsx).
4. `python3 tools/radiografia/build.py` → regenera `p/radiografia/index.html`, `tools/radiografia/out/*.csv` y `out/resumen.json`.
5. Commit + push → https://rp13588-eng.github.io/reportes-chasep/p/radiografia/

`processed.json` lleva los mensajes de Gmail ya procesados (id → corte, PNL).
Compras por equipo = suma de "COMPRAS COMPAÑÍA USD" de sus integrantes (los DJ suman en la compañía de su distribuidor).
Metas de alertas = encabezado del reporte Hycite: morosidad 31+ <10%, morosidad total <39%, recompra <2%.
