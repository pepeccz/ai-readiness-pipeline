# Bloque 4 — Talento & Cultura

**Objetivo**: dimensionar capacidad técnica interna, experiencia previa real con IA, plan de formación y disposición al cambio. Define qué **modelo de ejecución** es viable: SaaS-only, partner-managed, híbrido o in-house.

**Tiempo target**: 10 min.

---

## q4_1_team — Composición del equipo

**Concepto**: **developer ≠ ML engineer**. **Data analyst ≠ data scientist**. La mayoría de PYMEs cree que "tener un dev" alcanza para IA. No es cierto. Esta distinción define qué arquitectura puede sostener el equipo.

**Por qué importa**: prometer in-house con un IT generalista = prometer fracaso.

**Ejemplos sectoriales**:
- Clínica chica: típicamente `it_generalista` + `externalizado`.
- SaaS mid: `dev_software` + `data_analyst`.
- Retail mid: `it_generalista` + `data_analyst`.

**Pregunta abierta**: *"¿Quiénes manejan la parte técnica hoy? Listame perfiles, sin nombres."*

**Decision tree → opciones**:

| Lo que dice | Marcá (multi) |
|---|---|
| "No tenemos nadie técnico" | `ninguno` |
| "Hay una persona de IT / soporte" | `it_generalista` |
| "Tenemos developer/s" | `dev_software` |
| "Hay alguien que mira datos / dashboards" | `data_analyst` |
| "Tenemos data engineer / ML engineer" | `data_engineer_ml` |
| "Tenemos data scientist" | `data_scientist` |
| "Lo lleva una agencia / consultora" | `externalizado` |

`q4_1_count` (texto opcional): número total de personas técnicas, incluidos externos.

**Banderas rojas**:
- Marca `data_scientist` pero el respondente no sabe distinguir de analyst → bajar a `data_analyst`.
- Solo `externalizado` + apetito `agresivo` → riesgo: IA delegada sin governance interna.

---

## q4_2_experience — Experiencia real con IA

**Concepto**: hay 6 niveles. Usar ChatGPT en lo personal **no es** experiencia organizacional. Los niveles altos (fine-tuning, MLOps) son raros en PYME y suelen estar sobreestimados.

**Por qué importa**: calibra qué pueden absorber sin colapsar.

**Pregunta abierta**: *"¿Qué hicieron concretamente con IA hasta ahora? Contame el caso más avanzado."*

**Decision tree → opciones**:

| Lo que dice | q4_2_level |
|---|---|
| "Nada" | `ninguna` |
| "Yo uso ChatGPT" / "algunos del equipo" | `uso_individual` |
| "Hicimos prompts elaborados, hay biblioteca" | `prompts_elaborados` |
| "Llamamos a la API de OpenAI desde nuestro sistema" | `integracion_apis` |
| "Hicimos fine-tuning de un modelo" | `fine_tuning` |
| "Tenemos modelos en producción con monitoreo" | `mlops_produccion` |

`q4_2_areas` (multi, condicional si nivel ≠ ninguna): atención cliente, contenido, análisis, automatización, software, otro.

**Banderas rojas**:
- Salta nivel ("hacemos MLOps" pero no tiene data engineer en q4_1) → bajar.
- "Probamos ChatGPT en producción con datos de cliente" → marcá nivel + flag mental para bloque 7 (Shadow AI).

---

## q4_3_training — Plan de formación + disposición

**Concepto**: la formación **es parte del scope**, no un extra. Comprar un Ferrari sin enseñar a conducir = piloto que duerme.

**Por qué importa**: equipo motivado pero sin plan = entusiasmo que muere en 3 meses. Equipo capacitado pero reacio = sabotaje pasivo.

**Ejemplos sectoriales**:
- Clínica: típicamente `no_plan` + `mixto` (parte del staff es senior y reacio).
- SaaS: `planeado_sin_fecha` + `motivado`.
- Retail: `hablado_no_formal` + `mixto`.

**Pregunta abierta**: *"¿Hay plan de formación en IA para el equipo? Y por otro lado, ¿cómo lo está tomando la gente — entusiasmo, escepticismo, miedo?"*

**Decision tree → opciones**:

| q4_3_plan | Lo que dice |
|---|---|
| `presupuestado` | "Sí, ya hay budget y fechas" |
| `planeado_sin_fecha` | "Sí pero sin fecha" |
| `hablado_no_formal` | "Lo charlamos pero no hay nada formal" |
| `no_plan` | "No, no hay plan" → **DEEP `change_management`** |

| q4_3_disposition | Lo que dice |
|---|---|
| `motivado` | "Quieren aprender, están entusiasmados" |
| `mixto` | "Algunos sí, otros no" |
| `reacio` | "Hay resistencia / miedo a perder el laburo" → **DEEP `change_management`** |
| `no_hablado` | "Todavía no lo comunicamos" |

**Banderas rojas**: `motivado` declarado pero el respondente es CEO sin contacto con base → desconfiar, dejar `mixto`.

---

## q4_4_change_capacity — Capacidad de absorber cambio

**Concepto**: **change management es variable real de éxito**. Una empresa "en medio de otro cambio importante" → recomendación honesta es **postergar**, no agregar.

**Por qué importa**: forzar IA encima de otro cambio = fracaso garantizado. Mejor decirlo ahora que en mes 4.

**Pregunta abierta**: *"En los últimos 18 meses, ¿hicieron cambios grandes — software nuevo, reorganización, fusión, etc? ¿Cómo salieron?"*

**Decision tree → opciones**:

| q4_4_history | Lo que dice |
|---|---|
| `exitosos` | "Hicimos cambios, salieron bien" |
| `resistencia` | "Lo intentamos, hubo mucha resistencia" → **DEEP `change_management`** |
| `sin_cambios` | "Nada relevante recientemente" |
| `otro_cambio_activo` | "Estamos en medio de [ERP nuevo / reorga / fusión]" → **DEEP `evaluacion_timing`** |

`q4_4_example` (texto opcional): pedí ejemplo concreto, ayuda al LLM closing.

**Banderas rojas**:
- `otro_cambio_activo` + apetito `agresivo` → confluencia explosiva, recomendar postergar.
- `sin_cambios` + empresa >5 años → improbable, profundizar.

---

## Cierre de bloque 4

Síntesis: *"Equipo X, experiencia Y, plan/disposición Z, capacidad de cambio W. Eso me da una recomendación de modelo de ejecución (SaaS / partner / híbrido / in-house) que armamos al cierre."*

**DEEP triggers a anotar**: `change_management`, `evaluacion_timing`.
