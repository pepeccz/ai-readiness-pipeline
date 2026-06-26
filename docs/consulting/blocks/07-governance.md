# Bloque 7 — Governance & Ética

**Objetivo**: identificar cómo se aprueban iniciativas IA, evaluar política GenAI (anti Shadow AI), validar transparencia hacia clientes y revisar plan de gestión de errores. Define los **artefactos de governance mínimos** que faltan para empezar.

**Tiempo target**: 10 min.

---

## q7_1_approval — Aprobación de iniciativas IA

**Concepto**: la **aprobación = filtro de riesgo + asignación de responsabilidad**. **Shadow AI es el riesgo #1 en PYMEs** — gente del equipo usando ChatGPT con datos de cliente sin que nadie lo sepa. Sin proceso de aprobación, no hay forma de detectarlo.

**Por qué importa**: integrar IA sin governance = legitimar el caos actual con sello oficial.

**Pregunta abierta**: *"Hoy, si alguien del equipo quiere usar una herramienta de IA nueva, ¿qué hace? ¿Pide permiso a quién? ¿O lo hace y ya?"*

**Decision tree → opciones**:

| q7_1_process | Lo que dice |
|---|---|
| `comite_formal` | "Hay comité con criterios" |
| `persona_criterios` | "Lo aprueba [rol] con criterios claros" |
| `persona_sin_criterios` | "Lo aprueba [rol], sin criterios formales" |
| `caso_a_caso` | "Caso a caso, depende" |
| `nadie` | "Cada uno hace lo que quiere" → **DEEP `governance_minimo`** |

`q7_1_responsible` (texto opcional, condicional si hay persona o comité): rol del responsable, no nombre.

**Banderas rojas**: `nadie` + uso individual de ChatGPT confirmado en bloque 4 → Shadow AI activo.

---

## q7_2_genai_policy — Política GenAI

**Concepto**: **Shadow AI ya ocurre**. La política la **regulariza**. Plantilla mínima: herramientas autorizadas, datos prohibidos, validación humana obligatoria, documentación de uso.

**Por qué importa**: sin política, una multa por dato subido a ChatGPT viene del empleado X, pero el responsable legal es la empresa.

**Pregunta abierta**: *"¿Tienen política escrita y comunicada de qué pueden y no pueden hacer los empleados con IA generativa?"*

**Decision tree → opciones**:

| q7_2_policy_status | Lo que dice |
|---|---|
| `firmada` | "Sí, firmada y comunicada" |
| `redactada_no_comunicada` | "Está escrita, no comunicada" |
| `verbal` | "Acuerdo verbal" |
| `no_prohibimos_no_oficial` | "No prohibimos pero no es oficial" → **DEEP `politica_genai`** |
| `cada_uno` | "Cada uno hace lo que quiere" → **DEEP `politica_genai`** |

`q7_2_risks_identified` (multi, condicional si verbal/no_prohibimos/cada_uno): datos de cliente subidos a ChatGPT, código sin revisar, docs confidenciales en IA pública, decisiones sin validación, sin visibilidad.

**Banderas rojas**: `firmada` declarada pero no puede mostrar el documento → bajar a `redactada_no_comunicada`.

---

## q7_3_transparency — Transparencia hacia clientes

**Concepto**: **AI Act Art.50 + RGPD Art.13–14** obligan a informar cuando hay IA en interacción con clientes. NO declarar = incumplimiento, sin grises.

**Por qué importa**: chatbots no declarados, IA en email replies sin nota → multa potencial + daño reputacional.

**Pregunta abierta**: *"Cuando un cliente interactúa con IA en tu servicio, ¿se lo decís explícitamente, o lo asumís?"*

**Decision tree → opciones**:

| q7_3_transparency | Lo que dice |
|---|---|
| `siempre` | "Siempre lo declaramos" |
| `casos_sensibles` | "Solo en casos sensibles" |
| `asumimos_no_declaramos` | "Asumimos que el cliente sabe" → **DEEP `transparencia_ai_act`** |
| `no_informamos` | "No informamos activamente" → **DEEP `transparencia_ai_act`** |
| `no_aplica` | "No tenemos IA cara al cliente" |

**Banderas rojas**: `no_aplica` + bloque 4 dice `integracion_apis` o nivel mayor en producto → contradicción, hay IA cliente-facing sin declarar.

---

## q7_4_error_plan — Plan de gestión de errores IA

**Concepto**: el AI Act exige **plan de gestión de riesgos** en alto riesgo. Componentes mínimos: **detección, reversión, comunicación, aprendizaje post-mortem**.

**Por qué importa**: cuando la IA se equivoca (que se va a equivocar), la diferencia entre incidente menor y crisis es tener plan documentado.

**Pregunta abierta**: *"Cuando la IA se equivoque — porque va a pasar — ¿cómo lo detectan, cómo revierten, a quién avisan, cómo aprenden del error?"*

**Decision tree → opciones**:

| q7_4_plan_status | Lo que dice |
|---|---|
| `documentado` | "Documentado con los 4 componentes" |
| `sabemos_no_doc` | "Sabemos qué haríamos, no está escrito" |
| `lo_decidiriamos` | "Lo decidiríamos en el momento" → **DEEP `gestion_riesgo_ia`** |
| `no_pensado` | "No lo pensamos" → **DEEP `gestion_riesgo_ia`** |
| `no_aplica` | "No tenemos IA en producción" (verificar contra bloques 4, 6) |

`q7_4_example` (texto opcional, máx 150): pedí el peor error posible imaginable. Útil para dimensionar.

**Banderas rojas**:
- `no_aplica` + bloque 6 q6_2_status=`ya_con_ia` → contradicción directa, **forzar conversación**.
- `documentado` sin documento que mostrar → bajar.

---

## Cierre de bloque 7

Síntesis: *"Aprobación X, política GenAI Y, transparencia Z, plan de errores W. Eso me dice el riesgo de Shadow AI (low/medium/high/critical), el cumplimiento de transparencia y los **artefactos de governance que vamos a entregar primero**."*

**DEEP triggers a anotar**: `governance_minimo`, `politica_genai`, `transparencia_ai_act`, `gestion_riesgo_ia`.
