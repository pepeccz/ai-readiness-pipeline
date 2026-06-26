# Bloque 2 — Proceso Crítico

**Objetivo**: identificar el proceso concreto a IA-ficar, dimensionar volumen y variabilidad, mapear baseline de métricas, evaluar coste de fallo y dependencias. Es el bloque más largo y el más diagnóstico — acá se decide si IA es viable, o si la respuesta correcta es automatización simple, reglas, o nada.

**Tiempo target**: 20 min.

---

## q2_1_process — Definir el proceso

**Concepto**: un proceso es una **secuencia repetible de pasos con un input y un output**. "Atender consulta de cliente → respuesta en plataforma" es proceso. "Marketing" no es proceso, es función.

**Por qué importa**: la frecuencia y el volumen determinan si IA es candidato viable. Un proceso esporádico de bajo volumen rara vez justifica IA — es más barato hacerlo a mano o con reglas.

**Ejemplos sectoriales**:
- Clínica: *"Triage telefónico de consulta no urgente"* — continuo, ~80/día.
- SaaS: *"Clasificación de tickets entrantes"* — diario, ~200/día.
- Retail: *"Reposición de stock por tienda"* — semanal, 50 tiendas.

**Pregunta abierta**: *"Pensá en el proceso que más te duele hoy. Describímelo en 3 frases: input, pasos, output."*

**Decision tree → opciones**:

| sub_field | Mapeo |
|---|---|
| `q2_1_name` | Transcribir literal, máx 150 char. |
| `q2_1_frequency` | "Todo el tiempo" → `continuo`. "Cada día" → `diario`. "Cada semana" → `semanal`. "Una vez al mes" → `mensual`. "Cuando aparece" → `esporadico`. |
| `q2_1_volume` | Insistir suavemente: *"¿Más o menos cuántas veces al día/semana?"*. Si no sabe, dejar vacío + nota. |

**Banderas rojas**:
- Describe una función ("ventas") → reformular: *"¿Qué tarea concreta dentro de ventas?"*.
- "Esporádico" + querer IA generativa con LLMs → quizás OK por cero overhead. Esporádico + ML clásico → no viable.

---

## q2_2_variability — Variabilidad del proceso

**Concepto**: un proceso **estable** (entradas similares siempre) se resuelve con **reglas**. Un proceso **errático** (muy impredecible) puede necesitar **IA**. Intermedio → híbrido. Esta distinción es clave anti-hype: mucha gente pide IA para cosas que reglas resuelven mejor.

**Por qué importa**: si decimos "IA" sin chequear variabilidad, le vendemos al cliente un Ferrari para ir a la esquina.

**Ejemplos sectoriales**:
- Clínica: triage telefónico → `variable` (síntomas distintos cada vez).
- SaaS: validación de input de formulario → `estable` (reglas alcanzan).
- Retail: demanda en black friday → `estacional`.

**Pregunta abierta**: *"Cuando llega un caso a este proceso, ¿se parece al anterior, o cada uno es distinto?"*

**Decision tree → opciones**:

| Lo que dice | Opción |
|---|---|
| "Casi siempre lo mismo" | `estable` |
| "Picos predecibles (verano, fin de mes…)" | `estacional` |
| "Cambia bastante" | `variable` |
| "Es un caos / impredecible" | `erratico` → **DEEP `alternativas_no_ia`** |

**Banderas rojas**: `estable` + cliente quiere IA generativa → preguntar *"¿Por qué no reglas?"*. La respuesta revela si entendió la herramienta.

---

## q2_3_metrics — Métricas actuales

**Concepto**: **sin baseline no hay ROI defendible**. Si el cliente no mide hoy, el primer entregable es definir la métrica.

**Por qué importa**: presentar 6 meses después que "mejoramos" sin baseline = humo. Es la causa #1 de pilotos que no se renuevan.

**Ejemplos sectoriales**:
- Clínica: tiempo medio de triage = 8 min, abandono = 12%.
- SaaS: SLA de primera respuesta = 2h, tasa de resolución first-touch = 35%.
- Retail: roturas de stock = 8% SKUs/semana.

**Pregunta abierta**: *"Hoy, ¿cómo medís si este proceso va bien o mal?"*

**Decision tree → opciones**:

| sub_field | Mapeo |
|---|---|
| `q2_3_current_metric` | Transcribir literal, incluyendo unidad. Si no sabe, dejar vacío. |
| `q2_3_documented` | "Sí, tenemos dashboard" → `documentado`. "Algunos números sueltos" → `parcial`. "No medimos" → `no_mide` → **DEEP `definicion_baseline`**. |
| `q2_3_target` | "Queremos llegar a X" — opcional, transcribir. |

**Banderas rojas**: claim de mejora sin baseline → marcá `no_mide` aunque diga "tenemos números". Profundizá: *"¿Me lo podrías mostrar después?"*. Si no puede, es `no_mide`.

---

## q2_4_failure_cost — Coste de fallo

**Concepto**: el **coste de que el proceso falle** define la **arquitectura de control humano** necesaria. AI Act Art.22 aplica cuando el fallo tiene efecto significativo sobre personas.

**Por qué importa**: nivel `crítico` cambia la arquitectura entera — no es lo mismo IA-ficar marketing emails que IA-ficar denegación de servicio sanitario.

**Ejemplos sectoriales**:
- Clínica: triage mal → riesgo paciente = `critico`.
- SaaS: clasificación de ticket mal → cliente molesto = `medio`.
- Retail: forecast de stock mal → roturas / sobrestock = `alto`.

**Pregunta abierta**: *"Si este proceso se equivoca hoy, ¿qué pasa? ¿Cuánto duele?"*

**Decision tree → opciones**:

| Lo que dice | q2_4_level |
|---|---|
| "Nada, lo arreglamos" | `bajo` |
| "Pierde tiempo / cliente molesto" | `medio` |
| "Plata seria / mala prensa" | `alto` |
| "Riesgo legal / persona afectada / seguridad" | `critico` → **DEEP `ai_act_supervision`** |

**Banderas rojas**:
- Sector salud/legal/finanzas + responde `bajo` → desconocimiento del riesgo. **CRÍTICO**: explicá AI Act, NO marqués bajo. Marcá `critico` con nota de divergencia.
- "Nunca falló" → reformular: *"Si fallara, ¿qué pasaría?"*.

---

## q2_5_dependencies — Dependencias

**Concepto**: **bus factor** = riesgo organizacional. Si el proceso depende de 1–2 personas, antes de IA-ficar hay que documentar y automatizar.

**Por qué importa**: IA-ficar un proceso que vive en la cabeza de alguien sin extraer ese conocimiento = automatizar lo que ya nadie entiende.

**Ejemplos sectoriales**:
- Clínica: triage telefónico depende de 2 enfermeras con 10 años de oficio.
- SaaS: clasificación de ticket distribuida en equipo de soporte.
- Retail: forecast lo hace solo el COO con un Excel propio.

**Pregunta abierta**: *"Si la persona que mejor hace este proceso se va de vacaciones 2 semanas, ¿qué pasa?"*

**Decision tree → opciones**:

| sub_field | Mapeo |
|---|---|
| `q2_5_key_person` | "Sin esa persona se rompe" → `una_dos_personas`. "Otros pueden cubrir con esfuerzo" → `parcial`. "Cualquiera lo hace" → `distribuido`. |
| `q2_5_external` (multi) | Marcar las que mencione: proveedor, cliente, sistema externo, regulación, ninguna. |

**Banderas rojas**: `una_dos_personas` + cliente quiere IA "para ya" → frenar: *"Antes de IA, extraer ese conocimiento."*

---

## Heurísticas opcionales — q2_h1..q2_h4

Estas son señales de **proceso saturado**. No son obligatorias y se pueden saltar si vas justo de tiempo. Útil cuando el cliente vacila en otras preguntas.

| ID | Pregunta | Lectura |
|---|---|---|
| `q2_h1_overtime` | ¿Se trabaja fuera de horario? | `si` → saturación crónica |
| `q2_h2_single_person` | ¿Lo hace una sola persona? | `si` → bus factor confirmado |
| `q2_h3_saturation` | ¿Volumen supera capacidad? | `si_frecuente` → proceso quebrado |
| `q2_h4_repeated_complaints` | ¿Quejas repetidas? | `si_sistematico` → calidad rota |

Pregunta única recomendada (combina las 4): *"¿Hay momentos donde el equipo se queda fuera de hora, una sola persona aguanta el peso, o se acumulan quejas repetidas en este proceso?"*

---

## Cierre de bloque 2

Síntesis: *"Entonces el proceso es X, ocurre Y veces, hoy lo medimos Z, fallarlo cuesta W, y depende de A. Esto nos da una primera lectura de si IA es la respuesta o si hay paso previo."*

**DEEP triggers a anotar**: `ai_act_supervision`, `alternativas_no_ia`, `definicion_baseline`.
