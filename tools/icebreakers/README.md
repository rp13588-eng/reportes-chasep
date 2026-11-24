# Icebreakers CHASEP + MEJAB

Página: https://rp13588-eng.github.io/reportes-chasep/p/icebreakers/

- `ice.py add-report <IcebreakerCounts.pdf> <AAAA-MM-DD>`: lee el PDF semanal de Hycite (correo de ReportingServices, lunes 5:15 am) y actualiza `state.json`. La fecha es la de ejecución del reporte (cubre hasta el día anterior).
- `ice.py set-ivan <AAAA-MM> <AAAA-MM-DD> <chasep_recl> <chasep_venta> <mejab_recl> <mejab_venta>`: datos del PDF "Reclutamiento México" de Ivan Sasito (grupo Premiers México). Se guarda el PDF más reciente de cada mes.
- `ice.py build <distribuciones.xlsx> p/icebreakers/data.json`: cruza con la hoja de Drive "DISTRUBUCIONES CHASEP & MEJAB" (pestañas CHASEP, MEJAB, BAJAS).
- `ice.py summary p/icebreakers/data.json`: texto corto del corte.

Reglas: los meses salen por diferencia de acumulados (no se suman semanas); el correo da los icebreakers, el PDF de Ivan solo "con venta" por Premier (no se suman); diciembre llega hasta el último reporte del año; IDs que no están en la hoja = "SIN CLASIFICAR".
