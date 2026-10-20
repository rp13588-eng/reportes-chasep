# Runbook — Dashboard "Crecimiento HyCite México"

Dashboard publicado (artifact): https://claude.ai/artifact/AiRJhzx5jKN2RtF1Z5QbjX
Archivos en el Project (carpeta claude/hycite/): data.json, build.py, template.html, extractor.js, logo_s.png

## Fuente
- Remitente: ReportingServices@hycite.com → rp13588@gmail.com
- Asunto: "HyCite: Mexico Purchase Growth by Territory Director - <fecha> 1:25 AM"
- Llega los días 1, 10 y 20 (~1:25 am CDMX). Adjunto: MexicoSalesComparison.pdf (attid 0.1.0)
- Día 1 = mes anterior CERRADO. Días 10/20 = mes en curso parcial (2025 MTD es el mes completo del año anterior).

## Actualización (cada reporte)
1. Gmail search: `from:ReportingServices@hycite.com subject:"Purchase Growth" newer_than:2d` → tomar thread id (hex) y el msg-f decimal del viewUrl.
2. Claude in Chrome (Mac mini, sesión rp13588 en Gmail): abrir pestaña nueva en
   `https://mail.google.com/mail/u/0/#inbox`, leer `GLOBALS[9]` (ik) con javascript_tool.
3. Navegar a `https://mail.google.com/mail/u/0/?ui=2&ik=<ik>&attid=0.1.0&permmsgid=msg-f:<msgDecimal>&th=<threadHex>&view=att&disp=inline`
   (redirige a mail-attachment.googleusercontent.com y muestra el PDF).
4. En esa pestaña, ejecutar extractor.js con javascript_tool (en llamada aparte del navigate). Devuelve líneas.
   Si alguna línea sale truncada, pedir el arreglo por rebanadas (slice).
5. Guardar las líneas en reporte.txt en el workspace, luego:
   `python3 build.py apply reporte.txt && python3 build.py check && python3 build.py render`
6. Publicar `crecimiento-hycite.html` con Artifact action publish + url del artifact (leerlo antes con action read).
7. Subir data.json actualizado al Project (project_write claude/hycite/data.json).
8. Enviar por WhatsApp el link y el resumen al grupo indicado.

## Reglas de cálculo
- Crecimiento sobre meses cerrados; el mes en curso se compara con su cierre proyectado
  (compras al corte ÷ % que la selección llevaba al mismo día en los 3 meses cerrados previos).
- Mes cerrado: se ajusta para cuadrar con el YTD oficial (absorbe compras posteadas tarde).
- "OTROS" = total nacional oficial − suma de directores.
- Año nuevo (reporte del 1 de enero): trae el año completo anterior; se debe iniciar data.json del año nuevo (build.py se detiene y avisa).
