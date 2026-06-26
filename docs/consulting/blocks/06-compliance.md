# Bloque 6 — Compliance IA

**Objetivo**: evaluar DPIA y base jurídica, identificar decisiones automatizadas con efecto sobre personas, estimar categoría AI Act, validar procedimiento ARCO y revisar incidentes de seguridad. Es el bloque de mayor valor diferencial — **la mitad de la consultoría está acá** y es donde más empresa subestima riesgo.

**Tiempo target**: 12 min. **NO acelerar.**

---

## q6_1_dpia — DPIA y base jurídica

**Concepto**: la **DPIA (Evaluación de Impacto de Protección de Datos)** es obligatoria por **Art.35 RGPD** cuando hay datos sensibles, decisiones automatizadas, o tratamiento masivo. La **base jurídica** es la justificación legal para tratar datos personales (consentimiento, contractual, interés legítimo). La mayoría de PYMEs lo desconoce.

**Por qué importa**: sin DPIA + sin base jurídica documentada, cualquier proyecto IA con datos personales es un riesgo legal directo.

**Ejemplos sectoriales**:
- Clínica: DPIA obligatoria casi siempre. Base jurídica: contractual + consentimiento.
- SaaS B2B: DPIA recomendada. Base: contractual + interés legítimo documentado.
- Retail con fidelización: DPIA según volumen. Base: consentimiento.

**Pregunta abierta (combinada)**: *"¿Hicieron una DPIA para los datos que tratan hoy? Y ¿saben con qué base jurídica los tratan?"*

**Decision tree → opciones**:

| q6_1_dpia_status | Lo que dice |
|---|---|
| `hecha_documentada` | "Sí, hecha y documentada formal" |
| `hecha_informal` | "La hicimos pero sin formalidad" |
| `no_hecha_sabe` | "Sabemos qué es, no la hicimos" |
| `no_hecha_no_sabe` | "No sabemos bien qué es" → **DEEP `dpia_inicial`** |
| `no_aplica` | "Datos totalmente anónimos" (verificá con bloque 3) |

| q6_1_base_juridica | Lo que dice |
|---|---|
| `consentimiento_doc` | "Tenemos consentimientos firmados" |
| `contractual_legitimado` | "Es contractual o interés legítimo, está documentado" |
| `asumido_no_doc` | "Asumimos que sí pero no está escrito" → **DEEP `dpia_inicial`** |
| `no_claro` | "No tengo claro" → **DEEP `dpia_inicial`** |
| `no_aplica` | "No aplica" |

**Banderas rojas**:
- `no_aplica` declarado + bloque 3 con `personal_identificable` → contradicción. **Forzar conversación**: el cliente cree que no aplica pero sí.
- `hecha_documentada` sin poder mostrar el documento → bajar a `hecha_informal`.

---

## q6_2_automated_decisions — Decisiones automatizadas

**Concepto**: **AI Act + RGPD Art.22**: cuando una IA toma decisiones con efecto significativo sobre personas, hay derecho a **intervención humana, explicación e impugnación**. Esto aplica incluso a sistemas basados en reglas.

**Por qué importa**: scoring crediticio, contratación, denegación de servicio, precios dinámicos personalizados — todo requiere arquitectura específica de control humano.

**Ejemplos sectoriales**:
- Clínica: triage automático → decisión sobre persona. Aplica.
- SaaS: clasificación de tickets → no hay decisión sobre persona. No aplica directamente.
- Retail: precios dinámicos personalizados → aplica.

**Pregunta abierta**: *"¿Tu proceso decide algo automáticamente que afecte a una persona — su acceso, su precio, su contratación, su salud, su crédito?"*

**Decision tree → opciones**:

| q6_2_status | Lo que dice |
|---|---|
| `ninguna` | "No, todo lo decide una persona" |
| `reglas_no_ia` | "Sí pero con reglas, no IA" |
| `planeamos_ia` | "Planeamos hacerlo con IA" |
| `ya_con_ia` | "Ya usamos IA para decidir" → **DEEP `regularizacion_art22`** |
| `no_claro` | "No tengo claro si entra" |

`q6_2_examples` (multi, condicional si planeamos_ia o ya_con_ia): scoring crediticio, contratación/RRHH, precios, denegación de servicio, otro.

**Banderas rojas**:
- `ya_con_ia` + DPIA `no_hecha_*` → riesgo legal activo, **prioridad #1**.
- `ninguna` declarado + sector finanzas/RRHH → improbable, profundizar.

---

## q6_3_ai_act_category — Categoría AI Act

**Concepto**: el **AI Act** clasifica los sistemas en 4 categorías. Multas hasta **35M€ o 7% de facturación global**. Las categorías:

- **Inaceptable**: prohibido (manipulación subliminal, vigilancia masiva).
- **Alto riesgo**: educación, empleo, sanidad, justicia, infra crítica, scoring biométrico → obligaciones extensas.
- **Limitado**: chatbots, generación de contenido → obligaciones de transparencia.
- **Mínimo**: filtros spam, recomendación → autoregulación.

**Por qué importa**: la categoría determina el peso entero del proyecto. Capacitar al cliente sobre SU caso específico es el momento de mayor valor docente.

**Ejemplos sectoriales**:
- Clínica usando IA para diagnóstico → `alto_riesgo`.
- SaaS con chatbot de soporte → `limitado`.
- Retail con recomendación de productos → `minimo`.

**Pregunta abierta**: *"Según lo que vimos del caso, ¿en qué categoría del AI Act creés que entra?"* — y enseñá las 4 antes.

**Decision tree → opciones**:

| q6_3_category | Cuándo |
|---|---|
| `inaceptable` | RARO. Si aparece, alerta total. |
| `alto_riesgo` | Educación, empleo, sanidad, justicia, infra crítica, scoring → **DEEP `obligaciones_ai_act`** |
| `limitado` | Chatbot, content gen, deepfake declarado |
| `minimo` | Recomendación, spam |
| `no_lo_se` | "No lo sé" → **DEEP `capacitacion_ai_act`** |

`q6_3_description` (texto opcional, máx 200): describí el caso de uso previsto.

**Banderas rojas**:
- Cliente subestima ("creo que es mínimo") en sector regulado → corregí en sesión, marca lo correcto.
- `no_lo_se` + sector regulado → automáticamente alta probabilidad de `alto_riesgo`.

---

## q6_4_arco — Derechos ARCO

**Concepto**: **ARCO + portabilidad + limitación + olvido**. La empresa tiene **1 mes** para responder a una solicitud de un afectado. Sin procedimiento, llegado el caso es caos + multa.

**Por qué importa**: integrar IA aumenta la superficie ARCO (más datos, más tratamientos). Sin procedimiento previo, IA agrava el problema.

**Pregunta abierta**: *"Si mañana un cliente te pide que borres todos sus datos, ¿qué hacés? ¿Hay procedimiento, o es ad-hoc?"*

**Decision tree → opciones**:

| q6_4_arco | Lo que dice |
|---|---|
| `procedimiento_doc` | "Hay procedimiento documentado y operativo" |
| `sabemos_no_formal` | "Sabemos cómo, sin formalizar" |
| `caso_a_caso` | "Caso a caso" |
| `no_pensado` | "No lo pensamos" → **DEEP `procedimiento_arco`** |
| `no_aplica` | "No tratamos datos personales" (re-verificar con bloque 3) |

**Banderas rojas**:
- `no_aplica` declarado pero bloque 3 dice `personal_identificable` → forzar revisión.
- `caso_a_caso` + sector regulado + tamaño >50 → riesgo de incumplimiento por escala.

---

## q6_5_incidents — Incidentes y brechas

**Concepto**: *"No tenemos forma de saber"* es **más sincero y más alarmante** que *"ninguno"*. Antes de IA-ficar, hay que saber qué pasa con los datos hoy.

**Por qué importa**: agregar IA encima de un sistema sin observabilidad de seguridad = multiplicar superficie sin visibilidad.

**Pregunta abierta**: *"En los últimos 24 meses, ¿hubo algún incidente de seguridad, brecha, accesos indebidos? Notificación a AEPD?"*

**Decision tree → opciones**:

| q6_5_status | Lo que dice |
|---|---|
| `ninguno_24m` | "Ninguno" (verificar con q6_5_no_forma_saber: ¿cómo lo sabrías?) |
| `menores_resueltos` | "Cosas chicas, internas" |
| `brecha_notificada` | "Sí, notificamos a AEPD" |
| `sospechamos` | "Creemos que sí, no investigamos" → **DEEP `monitorizacion_log`** |
| `no_forma_saber` | "No tenemos forma de saber" → **DEEP `monitorizacion_log`** |

`q6_5_description` (texto opcional, máx 200): descripción breve.

**Banderas rojas**:
- `ninguno_24m` sin sistema de logging → bajar a `no_forma_saber`. Pregunta de control: *"¿Cómo te enterarías si pasara hoy?"*. Si no tiene respuesta, no tiene observabilidad.

---

## Cierre de bloque 6

Síntesis (más larga acá, este bloque pesa): *"DPIA está en X, base jurídica Y. Decisiones automatizadas Z. AI Act categoría W. ARCO V. Incidentes U. Esto nos dice si compliance se trabaja **antes**, **en paralelo**, o **después** del piloto."*

**DEEP triggers a anotar**: `dpia_inicial`, `regularizacion_art22`, `obligaciones_ai_act`, `capacitacion_ai_act`, `procedimiento_arco`, `monitorizacion_log`.

> Este bloque es donde más se nota el valor del consultor. Si vas justo de tiempo, NO acelerar este bloque — recortá del bloque 5 o del cierre.
