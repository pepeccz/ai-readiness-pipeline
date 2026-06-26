# Session 1 — Macro Playbook

Sesión de 90–120 min que combina **formación + diagnóstico**. El cliente termina con conceptos nuevos y vos con el form intake completo.

## Pre-sesión (T-24h a T-1h)

### Materiales

- PPTX armado según `pptx-blueprint.md`, exportable a PDF para enviar después.
- Tab del admin (`/admin/intake/<lead_id>`) con el formulario abierto y guardado como draft.
- Doc TRIAGE del lead leído (`blocks/00-triage.md` lo cubre).
- Block notes (físico o digital) para citas literales del cliente — sirven para el LLM closing analysis.

### Qué saber del cliente antes de empezar

Del TRIAGE ya tenés:

- Identidad, sector, tamaño, madurez IA, urgencia, objetivos, rol y compromiso.
- Score y bucket (auto_accept / review / cold).
- Deep branches sugeridas (compliance, saas, industrial, enterprise).

Esto te da hipótesis previa. **No la verbalices al cliente** hasta el cierre — primero escuchá.

### Encuadre mental del consultor

- Sos **formador primero**, vendedor después.
- El form NO se completa "preguntando opciones del YAML". Se completa **traduciendo lo que el cliente dice** a la opción más cercana.
- Si el cliente no sabe algo, eso ES un dato. Marcá `no_se` / `no_claro` y seguí. La carencia es señal.

## Apertura — 5 min

| Momento | Qué hacés |
|---|---|
| 0:00 | Saludo + rapport corto (1 min). |
| 0:01 | Encuadre: "Vamos a hacer un diagnóstico de IA-readiness. No es un test, es una conversación. Yo te voy a explicar conceptos, vos me contás cómo se aplican a tu empresa, y al final tenés un mapa." |
| 0:03 | Agenda visible: 7 bloques, ~15 min cada uno, cierre con síntesis. |
| 0:04 | Permiso explícito: "¿Podemos grabar / tomar notas?" — registrá consentimiento. |

## Bloques CORE — 90–110 min

Tiempos estimados (del `estimated_minutes` del YAML):

| Bloque | Min | Foco |
|---|---|---|
| 1. Estrategia | 15 | Objetivo, sponsor, intentos previos, apetito de riesgo |
| 2. Proceso crítico | 20 | El proceso que querés mejorar — el corazón del diagnóstico |
| 3. Datos | 14 | Qué datos hay, calidad, accesibilidad, RGPD |
| 4. Talento | 10 | Equipo técnico, experiencia IA, formación, change capacity |
| 5. Infraestructura | 10 | Cloud/on-prem, vendors, deploy, lock-in |
| 6. Compliance | 12 | DPIA, decisiones automatizadas, AI Act, ARCO, incidentes |
| 7. Governance | 10 | Aprobación, política GenAI, transparencia, plan de errores |

**Total target: 91 min**. Dejá 10 min de buffer para preguntas y cierre.

### Patrón por pregunta (el corazón del método)

```
1. Slide CONCEPTO    (30–45 seg)  → qué es, didáctico
2. Slide POR QUÉ     (30 seg)     → por qué le importa a SU negocio
3. Slide EJEMPLO     (30 seg)     → caso sectorial, idealmente análogo
4. PREGUNTA ABIERTA  (1–2 min escucha activa)
5. CONFIRMACIÓN      (15 seg)     → "entonces sería <opción Y>, ¿sí?"
6. COMPLETÁS form mientras decís "perfecto, anoto eso".
```

Ratio target: ~3 min por pregunta. Si una pregunta lleva más de 5 min, parala con: *"Bueno, lo dejamos en `no_claro` y lo profundizamos en la sesión 2."*

### Rol consultor: 70/30

- **70% formador**: explicás, das ejemplos, contás casos. El cliente aprende.
- **30% interrogador**: preguntás, escuchás, mapeás, confirmás.

Si te encontrás >50% preguntando, frenaste de explicar. Volvé a slide concepto.

### Reglas de ritmo

| Síntoma | Acción |
|---|---|
| Cliente verboso (>3 min en una pregunta) | Resumir y confirmar: *"Para no quedarme sin tiempo, lo que escucho es X. ¿Confirmás?"* |
| Cliente vago / no sabe | Marcar `no_se`/`no_claro` y SEGUIR. La carencia es dato. |
| Cliente desvía a tema futuro | *"Buenísimo, lo anoto para el cierre."* y volvés. |
| Te quedaste sin tiempo en bloque | Saltá heurísticas opcionales (q2_h1..h4), no las core. |
| Cliente rebate un concepto | Validá, mostrá el caso real, no discutas. *"Te entiendo, en la práctica vimos que…"* |

### Cómo cortar al cliente verboso (sin ofender)

- *"Perfecto, eso es justo lo que necesitaba. Anoto X. Avanzamos a…"*
- *"Para respetar tu tiempo, lo dejo como X y si querés en sesión 2 profundizamos."*
- *"Eso ya entra en el bloque 6, lo retomamos ahí."*

## Modo dual: PPTX + Form

Setup recomendado:

- **Pantalla 1 (compartida con cliente)**: PPTX en presentation mode.
- **Pantalla 2 (privada, tuya)**: tab admin con el form.
- **Bloc de notas físico**: citas literales (las usa el LLM en closing analysis).

Navegación:

- Cada slide tiene en la nota inferior el `question.id` correspondiente. Cuando avanzás slide, sabés qué campo tocar.
- Convención de naming (ver `pptx-blueprint.md`): `core.b{N}.{question_id}.{tipo_slide}`.
- El form admin está pre-cargado con TRIAGE. Solo completás CORE.

Si perdés el control (cliente entró en loop, slide se rompió), volvé al PPTX en modo overview, mostrá agenda, y seguí.

## Cierre — 10 min

| Momento | Qué hacés |
|---|---|
| 0:00 | "Te muestro un primer mapa de lo que escuché." |
| 0:02 | **Síntesis verbal de 3–5 puntos** — tomados de los closing_analysis (synthesis) que el LLM ya generó por bloque, si querés esperar 30 seg, se ven en el panel admin. |
| 0:05 | **Hipótesis preliminar**: "Mi hipótesis es que el primer entregable debería ser X. ¿Resuena?" |
| 0:07 | **Próximos pasos**: sesión 2 (deep follow-ups), propuesta formal, fecha tentativa. |
| 0:09 | Agradecimiento, envío PDF de slides + recap escrito en 24h. |

## Antipatrones (NO hacer)

- Leer las opciones del YAML al cliente como un menú.
- Saltar slides concepto porque "se hace largo" — perdés el valor formativo.
- Forzar respuesta cuando el cliente no sabe — eso CONTAMINA el diagnóstico.
- Vender en el medio de un bloque — vendé en el cierre, no antes.
- Acelerar el bloque 6 (Compliance) — ahí está la mitad del valor diferencial.
