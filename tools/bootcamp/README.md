# I-TEAM BOOTCAMP · página de registro y avance

Página: https://rp13588-eng.github.io/reportes-chasep/p/iteam-bootcamp/ (oficina: agregar `?oficina`)

- Registro: el formulario de la página envía a un Google Form oculto
  (`1FAIpQLSeS7SaRbIC2PT04nn5A5RGmxzIUG9g0E3U1zwxLxCo8z_1nZQ`) ligado al Sheet
  "I-TEAM Bootcamp · Registro (respuestas)" `1oz5hr3ctnGFWP-41SJzy4Mp91mt4H_wgstUsYgnjOhc`.
  - Pestaña "Respuestas de formulario 1": datos completos (incluye WhatsApp). Columna I "Estatus": escribir CANCELADO para quitar un registro de la lista.
  - Pestaña "Publico": fórmula sin teléfonos, publicada en la web como CSV (la lee la página).
  - "Detalle boletos" = `Nombre|Tipo|Talla|WhatsApp` separados por `;`. Tipo = Participante / Acompañante.
- `participantes.json`: lista de participantes (regenerar con `build_participantes.py` en cada corte).
- `avance.json`: lo escribe el corte de los lunes. Esquema:
```json
{"corte":"AAAA-MM-DD","corte_texto":"16 nov 2026","dias_restantes":45,"ritmo_sub":5246,
 "subterritorios":[{"sub":"FORZA","meta":40000,"compras_nov":0,"compras_dic":null,"ventas":0,"calificados":0}],
 "top":{"dj":["id"],"dist":["id"],"sub":["FORZA"]},
 "participantes":[{"id":"72772","nombre":"…","sub":"FORZA","tipo":"DJ|Distribuidor","ventas":0,"compras":0,
   "recluta":false,"estatus":"verde|azul|amarillo|rojo","falta":"15,000 V · 5,500 C · recluta"}]}
```

Cuotas (corregidas 9-nov-2026): completo 24,000 V + 8,000 C + recluta · subsidiado 20,000 V + 6,500 C + recluta · pareja 36,000 V + 12,000 C + recluta. Ranking: ventas válidas = mín(ventas, compras × 3). `ritmo_sub` = ritmo esperado de ventas para 20k.
