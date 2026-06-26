# Bloque 1 — Estrategia IA

**Objetivo**: separar objetivo de iniciativa, validar respaldo organizacional, sacar lecciones de intentos previos y calibrar expectativas de riesgo/horizonte. Es el bloque que decide si el resto de la sesión tiene sentido — sin sponsor y sin objetivo claro, todo lo demás es académico.

**Tiempo target**: 15 min.

---

## q1_1_objective — Resultado esperado, métrica, plazo

**Concepto** (didáctico): "Implementar un chatbot" es una **iniciativa**. "Reducir el tiempo de respuesta al cliente un 40% en 6 meses" es un **objetivo**. La iniciativa es el cómo, el objetivo es el qué medible. Sin objetivo medible, no hay forma de saber si la IA sirvió.

**Por qué importa**: si no podés articular el objetivo en términos de negocio, el primer entregable no es IA — es definir el objetivo. Eso ya es valor consultor.

**Ejemplos sectoriales**:
- Clínica: *"Reducir 30% el tiempo de triage telefónico de pacientes en 6 meses, medido por duración media de llamada."*
- SaaS: *"Aumentar 20% la activación trial→paid en 12 meses, medido por funnel."*
- Retail: *"Bajar 25% las roturas de stock en 6 meses, medido contra históricos."*

**Pregunta abierta**: *"Si dentro de 6 meses miramos hacia atrás y la IA fue un éxito, ¿qué número cambió y cuánto?"*

**Decision tree → opciones**:

| sub_field | Mapeo |
|---|---|
| `q1_1_outcome` (textarea) | Transcribí literal lo que dice. Máx 200 char. |
| `q1_1_metric` (text) | Si dice "más ventas" → preguntá *"¿en %, en €, en cantidad?"* y registrá la unidad. |
| `q1_1_timeframe` | "Pronto" / "este año" → `12m`. "Antes de fin de año" (si es Q1-Q2) → `6m` o `12m`. "Lo antes posible" → `3m` y nota mental: expectativa rota. "Largo plazo" → `24m_plus`. |

**Banderas rojas**:
- No puede articular outcome → marcá `outcome` con la frase del cliente cruda + comentario interno.
- Confunde herramienta con objetivo ("queremos ChatGPT") → reformulá: *"¿Para qué resultado de negocio?"*
- Plazo `3m` con objetivo de transformación → expectativa rota, anotalo.

---

## q1_2_sponsor — Sponsor ejecutivo

**Concepto**: Sponsor ≠ usuario. Sponsor es quien tiene **autoridad para aprobar presupuesto, resolver bloqueos y comunicar prioridad al equipo**. Un director técnico que pide IA pero no controla el budget no es sponsor.

**Por qué importa**: la IA fracasa más por falta de respaldo organizacional que por limitaciones técnicas. Sin sponsor = proyecto zombi.

**Ejemplos sectoriales**:
- Clínica: dueño/a o director/a médico/a.
- SaaS: CEO o VP Product.
- Retail: dueño/a o COO.

**Pregunta abierta**: *"¿Quién en la empresa va a defender este proyecto cuando aparezcan los problemas, y tiene poder para destrabarlos?"*

**Decision tree → opciones**:

| Lo que dice el cliente | Opción |
|---|---|
| "Yo, soy el CEO/dueño" | `ceo_total` |
| "Yo soy CEO pero tengo que validar con socios/directorio" | `ceo_valida` |
| "El CTO" / "la directora de operaciones" / cualquier C-level no-CEO | `director_cto` |
| "Lo decidimos en comité" / "el board" | `comite` |
| Vacila / "buena pregunta" / "todavía no lo definimos" | `sin_sponsor` → **DEEP `governance_previo_ia`** |

**Banderas rojas**:
- "Mi jefe lo está mirando" sin nombre concreto → `sin_sponsor`.
- Sponsor es el mismo respondente pero rol=`responsable_it` y empresa >100 → señal de que IT está empujando sin business-side. Anotá.

---

## q1_3_previous — Intentos previos

**Concepto**: la historia con IA/automatización predice mejor que el optimismo del presente. Un fracaso bien procesado es más valioso que un éxito sin lecciones.

**Por qué importa**: si fracasaron antes, hay deuda emocional + organizacional. Si nunca intentaron, hay que enseñar a evaluar éxito.

**Ejemplos sectoriales**:
- Clínica: *"Probamos un asistente para agenda y lo desactivamos."*
- SaaS: *"Tenemos un piloto de copilot interno funcionando."*
- Retail: *"Quisimos hacer demand forecasting y se canceló."*

**Pregunta abierta**: *"¿Han intentado antes implementar IA o automatización? Contame qué pasó."*

**Decision tree → opciones**:

| Lo que dice | Opción |
|---|---|
| "Nunca, esta es la primera" | `first_time` |
| "Sí, funciona en producción" | `exitoso_produccion` |
| "Tenemos un piloto activo" | `piloto_activo` |
| "Empezamos pero lo dejamos" | `abandoned` → **DEEP `post_mortem_proyecto`** |
| "Salió a prod y se rompió / lo apagamos" | `failed_production` → **DEEP `post_mortem_proyecto`** |

**Banderas rojas**:
- "Sí, exitoso" pero no puede dar métrica → probar empuje suave. Si sigue sin métrica, dudar.
- "Fracasó" + no quiere hablar del tema → respetar y marcar para sesión 2.

---

## q1_3b_failure_cause — Causa del fracaso (condicional)

Solo aparece si q1_3_previous ∈ {abandoned, failed_production}.

**Concepto**: los patrones de fracaso más comunes son **organizacionales** (sponsor, resistencia, change mgmt), no técnicos. Sin embargo, los entrevistados tienden a culpar al "vendor" o a "los datos".

**Pregunta abierta**: *"¿Qué se rompió primero — la tecnología, la organización, el budget, o las prioridades cambiaron?"*

**Decision tree → opciones** (multi, máx 2):

| Lo que dice | Marcá |
|---|---|
| "Los datos no estaban / el modelo no funcionaba" | `tecnico` |
| "Salió mucho más caro" | `economico` |
| "El equipo no lo adoptó / se resistieron" | `organizacional` |
| "El proveedor no entregó / desapareció" | `vendor` |
| "Apareció una norma / nos dijeron que no podíamos" | `regulatorio` |
| "Cambió la prioridad / vino otra cosa" | `estrategico` |
| "La verdad no sé" | `no_claro` |

**Banderas rojas**: solo marca `tecnico` y nada más. Probar: *"¿Y por qué nadie lo arregló?"* — suele aparecer la causa real.

---

## q1_4_appetite — Apetito de riesgo + horizonte ROI

**Concepto**: ROI realista de IA = pilotos en 3–6 meses, transformación en 12–24 meses. Apetito y horizonte tienen que alinear, o las expectativas están rotas desde el día 1.

**Por qué importa**: si el cliente quiere "transformación amplia" en "3 meses", el primer entregable de la consultoría es **calibrar expectativas**, no construir.

**Ejemplos sectoriales**:
- Clínica: conservador típicamente — *"Probemos un piloto en triage."*
- SaaS: moderado/agresivo — *"Varios experimentos en paralelo."*
- Retail: depende del tamaño — moderado en mid-market.

**Pregunta abierta**: *"¿Empezarías con un piloto pequeño, varios en paralelo, o vas con todo? ¿Y en cuánto tiempo esperás ver retorno?"*

**Decision tree → opciones**:

| q1_4_risk | q1_4_horizon |
|---|---|
| "Empezamos chico" → `conservador` | "Pronto" → `3m` |
| "Varios pilotos" → `moderado` | "Medio año" → `6m` |
| "Vamos con todo" → `agresivo` | "Un año" → `12m` |
| | "No tenemos prisa" → `24m_plus` |

**Banderas rojas**:
- `agresivo` + `3m` → expectativa imposible. Anotá literal y al cierre lo trabajás.
- `conservador` + `24m_plus` → desalineación inversa: querés energía, falta urgencia.

---

## Cierre de bloque 1

Síntesis verbal de 30 seg: *"Tenemos un objetivo de X medible en Y, sponsor es Z, vienen de [primera vez / éxito / fracaso], y el apetito es W. Pasamos a hablar del proceso concreto."*

**DEEP triggers activos a anotar**: `post_mortem_proyecto` (si q1_3 = abandoned/failed_production), `governance_previo_ia` (si q1_2 = sin_sponsor).
