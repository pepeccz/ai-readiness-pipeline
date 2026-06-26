# Bloque 3 — Datos

**Objetivo**: mapear de dónde vienen los datos, evaluar calidad y volumen, identificar datos personales/sensibles, y verificar accesibilidad técnica. La calidad de datos es el **predictor #1 de éxito en IA**, y el cliente típicamente la sobreestima.

**Tiempo target**: 14 min.

---

## q3_1_sources — Orígenes de datos

**Concepto**: tener un Excel **no es** tener un dataset utilizable. Datos en la cabeza de personas tampoco. Una API directa accesible vale más que 10 documentos PDF.

**Por qué importa**: si el "dato" vive solo en la experiencia de personas, el primer entregable de IA no es modelar — es **extraer conocimiento implícito** a un repositorio estructurado.

**Ejemplos sectoriales**:
- Clínica: HCE (historia clínica electrónica), agenda, llamadas grabadas.
- SaaS: CRM + base producto + logs de uso.
- Retail: ERP de stock + histórico de ventas + planillas por sucursal.

**Pregunta abierta**: *"Pensá en los datos que el proceso usa para decidir. ¿De dónde salen?"*

**Decision tree → opciones** (multi):

| Lo que dice | Marcá |
|---|---|
| ERP / SAP / Odoo / SAGE | `erp` |
| CRM / Salesforce / HubSpot / Pipedrive | `crm` |
| Excel / Google Sheets | `hojas` |
| Email / WhatsApp / Slack | `email` |
| PDFs / Word / presentaciones | `docs` |
| Base de datos propia / aplicación interna | `bbdd_propia` |
| API de tercero | `apis` |
| "Lo sabemos por experiencia" / "está en la cabeza" | `conocimiento_cabezas` → **DEEP `extraccion_conocimiento`** |
| "No tenemos datos" | `no_datos` |

**Banderas rojas**:
- Solo `hojas` + proceso crítico → calidad probablemente baja, riesgo alto.
- `conocimiento_cabezas` único → IA imposible sin trabajo previo de explicitación.

---

## q3_2_quality — Calidad de datos

**Concepto**: la calidad de datos predice mejor el éxito que la sofisticación del modelo. La sobreestimación es **muy común** — el ejemplo concreto la reduce.

**Por qué importa**: arrancar un piloto con datos `regular` o `mala` = perder 3 meses descubriendo lo obvio.

**Ejemplos sectoriales**:
- Clínica: HCE bien estructurada → `excelente`. Notas libres mezcladas con códigos → `regular`.
- SaaS: eventos de producto con schema → `buena`. Logs sin parsear → `regular`.
- Retail: stock con SKU consistente → `buena`. Códigos distintos por sucursal → `mala`.

**Pregunta abierta**: *"En una escala mental: ¿los datos están completos, consistentes, actualizados? ¿O hay campos vacíos, duplicados, fechas raras?"*

**Decision tree → opciones**:

| Lo que dice | q3_2_level |
|---|---|
| "Excelentes, todo bien" | `excelente` (sospechá: pedí ejemplo) |
| "Buenos con algún detalle" | `buena` |
| "Tienen huecos, hay que limpiar" | `regular` → **DEEP `auditoria_calidad`** |
| "Es un desastre" | `mala` → **DEEP `auditoria_calidad`** |
| "No los miramos así" | `no_se` → **DEEP `auditoria_calidad`** |

`q3_2_example` (opcional): pedí siempre un ejemplo concreto de problema. Suele bajar la auto-evaluación una notch.

**Banderas rojas**:
- `excelente` sin ejemplo de cómo se mide calidad → bajar mentalmente a `buena`.
- `excelente` + sector regulado sin DPIA hecha (ver bloque 6) → contradicción.

---

## q3_3_volume — Volumen y antigüedad

**Concepto**: con <1.000 registros, **olvidate de ML clásico**. Considerá IA generativa (LLMs no necesitan tantos datos) o reglas. Retención <6 meses limita modelos de tendencia/estacionalidad.

**Por qué importa**: dimensionar viabilidad técnica antes de prometer nada.

**Ejemplos sectoriales**:
- Clínica: 50.000 consultas/año, 5 años retenidos → OK para ML.
- SaaS: 10.000 tickets/mes, 3 años → OK.
- Retail nuevo: 6 meses de operación → solo LLMs o reglas.

**Pregunta abierta**: *"¿Cuántos registros más o menos tenemos disponibles, y desde cuándo?"*

**Decision tree → opciones**:

| q3_3_volume_count | q3_3_retention |
|---|---|
| Menos de 100 → `menos_100` | <6m → `menos_6m` |
| 100–1k → `100_1k` | 6m–2a → `6m_2a` |
| 1k–10k → `1k_10k` | 2–5a → `2a_5a` |
| 10k–100k → `10k_100k` | >5a → `mas_5a` |
| >100k → `mas_100k` | "no sé" → `no_se` |

**Banderas rojas**: `mas_5a` retención + sector con datos personales + DPIA no hecha → riesgo RGPD por retención excesiva. Anotá para bloque 6.

---

## q3_4_personal_data — Datos personales / sensibles

**Concepto**: definición RGPD: **email empresarial = personal**. **IP = personal**. Esto suele estar mal entendido. Datos sensibles (salud, biométrica, ideología, menores) requieren **DPIA obligatoria** Art.35 RGPD.

**Por qué importa**: tratar datos personales sin base jurídica = multa hasta 4% facturación global. El cliente típicamente subestima qué cuenta como personal.

**Ejemplos sectoriales**:
- Clínica: salud + DNI = `sensible`.
- SaaS B2B: emails y nombres = `personal_identificable`.
- Retail con tarjeta de fidelidad: nombre + compras = `personal_identificable`.

**Pregunta abierta**: *"En esos datos, ¿hay nombres, emails, IPs, salud, datos financieros, o todo va anonimizado?"*

**Decision tree → opciones**:

| Lo que dice | q3_4_category |
|---|---|
| "Nombres, emails" | `personal_identificable` |
| "Salud / biométrica / menores / ideología" | `sensible` → **DEEP `dpia_obligatorio`** |
| "Contratos / finanzas internas" | `confidencial_empresarial` |
| "Todo anónimo / agregado" | `anonimos` (verificá: pedí ejemplo) |
| "No tengo claro qué cuenta" | `no_claro` → **DEEP `auditoria_tratamiento`** |

`q3_4_types` (multi, condicional): si hay `personal_identificable` o `sensible`, marcá los tipos: nombre/email, ubicación, salud, financieros, biométricos, menores, ideología, otros.

**Banderas rojas**:
- "Anónimo" pero hay email → no es anónimo. Reclasificar a `personal_identificable`.
- "No aplica RGPD porque es B2B" → mito. RGPD aplica si hay personas físicas (incluso emails personales en empresas). Educar.

---

## q3_5_accessibility — Acceso técnico

**Concepto**: **vendor lock-in de datos** es el bloqueante más caro. "Tener datos" ≠ "poder usarlos". Si tu CRM no exporta, no tenés datos — tenés rehenes.

**Por qué importa**: un proceso que depende de datos en un SaaS sin API es un proyecto bloqueado en arquitectura, no en IA.

**Ejemplos sectoriales**:
- Clínica con HCE moderna: `api_directo`.
- SaaS: típicamente `api_directo` en su propio stack.
- Retail con ERP legacy: `exportable` o peor.

**Pregunta abierta**: *"Si yo te pidiera mañana esos datos para procesarlos, ¿cómo me los pasarías?"*

**Decision tree → opciones**:

| Lo que dice | q3_5_accessibility |
|---|---|
| "API REST / webhook" | `api_directo` |
| "Te exporto un CSV" | `exportable` |
| "Solo mirando la pantalla / scrapeando" | `solo_interfaz` |
| "El proveedor no nos da acceso directo" | `bloqueado_proveedor` → **DEEP `migracion_negociacion`** |
| "No sé cómo está montado" | `no_se` |

**Banderas rojas**: `bloqueado_proveedor` + `q5_4_lockin=alto` (bloque 5) → IA bloqueada por arquitectura. Anotalo para cierre.

---

## Cierre de bloque 3

Síntesis: *"Datos vienen de X, calidad auto-evaluada Y, volumen Z, hay datos personales W, y técnicamente acceso V. Eso me da una primera lectura de readiness."*

**DEEP triggers a anotar**: `dpia_obligatorio`, `auditoria_tratamiento`, `auditoria_calidad`, `migracion_negociacion`, `extraccion_conocimiento`.
