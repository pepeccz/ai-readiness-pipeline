# Bloque 5 — Infraestructura & Stack

**Objetivo**: caracterizar dónde corre la tecnología hoy, identificar vendors críticos, dimensionar velocidad de deploy y nivel de vendor lock-in. Define el **arquetipo de despliegue** posible y los constraints reales del piloto.

**Tiempo target**: 10 min.

---

## q5_1_infra — Modelo de infraestructura

**Concepto**: cloud vs on-prem es decisión de **compliance + control + coste**, no solo técnica. 100% on-prem condiciona radicalmente las opciones de IA (modelos cerrados, self-hosted).

**Por qué importa**: ofrecer "IA en la nube" a una empresa con dato sensible sin migración previa = problema legal.

**Ejemplos sectoriales**:
- Clínica privada: típicamente `hibrido` o `mayoria_on_prem`.
- SaaS: `100_cloud`.
- Industria/manufactura: `100_on_prem` o `mayoria_on_prem`.

**Pregunta abierta**: *"Hoy, los servidores y software importantes, ¿corren en cloud, en oficina/datacenter propio, o mezcla?"*

**Decision tree → opciones**:

| Lo que dice | q5_1_model |
|---|---|
| "Todo en AWS / Azure / GCP" | `100_cloud` |
| "Casi todo cloud, algo on-prem" | `mayoria_cloud` |
| "Mitad y mitad" | `hibrido` |
| "Casi todo on-prem" | `mayoria_on_prem` |
| "100% on-prem / datacenter propio" | `100_on_prem` → **DEEP `ia_self_hosted`** |
| "No sé" | `no_se` |

`q5_1_clouds` (multi, condicional si ≠ 100_on_prem): AWS, GCP, Azure, Oracle, IBM, OVH/Hetzner, otro.

**Banderas rojas**:
- `100_on_prem` + objetivo IA generativa cliente-facing → conflicto, tendrá que abrir cloud o usar self-hosted con coste alto.

---

## q5_2_vendors — Vendors críticos

**Concepto**: identificar **dependencias críticas**. Concentración en un vendor = riesgo acumulado silencioso. Un solo vendor cubriendo ERP+CRM+IA = lock-in compuesto.

**Por qué importa**: la elección de vendor IA hereda las dependencias actuales. Si todo es Microsoft, Copilot es la fricción mínima; pero también es la trampa máxima si querés salir.

**Pregunta abierta**: *"Listame los 3 proveedores tecnológicos más críticos. Qué pasa si uno se cae mañana."*

**Decision tree → opciones** (composite con sub-vendor 1):

| sub_field | Mapeo |
|---|---|
| `q5_2_v1_name` | Nombre literal (ej: "Salesforce", "Holded", "SAP"). |
| `q5_2_v1_category` | erp / crm / comm / cloud / ia / bi / otro. Mapear según función primaria. |
| `q5_2_v1_criticality` | "Si se cae, paramos" → `critico`. "Impacto pero seguimos" → `importante`. "Lo cambiamos en semanas" → `reemplazable`. |

> **Nota práctica**: el schema solo tiene `q5_2_vendor_1` formalmente. Si el cliente menciona varios, anotálos en bloc físico para el LLM closing — el form solo guarda el más crítico.

**Banderas rojas**: `critico` + sin contrato SLA documentado → riesgo silencioso.

---

## q5_3_deploy — Capacidad de deploy

**Concepto**: el **tiempo de cambio = constraint del piloto**. Diseñar a cadencia real, no a la deseada. Una empresa con deploy trimestral no puede sostener un piloto IA con iteración semanal.

**Por qué importa**: pilotos exitosos requieren ciclos cortos (semanas, no trimestres). Si tu cliente deploya cada 6 meses, hay que diseñar el piloto fuera del stack core o forzar cambio cultural antes.

**Ejemplos sectoriales**:
- SaaS moderno: `continuo` (CI/CD).
- Clínica: `trimestral` o `esporadico` (cambios delicados).
- Retail mid: `mensual` o `trimestral`.

**Pregunta abierta**: *"Cuando aparece una herramienta nueva que quieren probar, ¿cuánto tarda en estar funcionando con datos reales?"*

**Decision tree → opciones**:

| q5_3_frequency | Lo que dice |
|---|---|
| `continuo` | "Despliegues todos los días" |
| `mensual` | "Una vez al mes" |
| `trimestral` | "Cada trimestre" |
| `esporadico` | "Cuando hace falta" |
| `nunca` | "No tenemos proceso definido" |

| q5_3_time_new_tool | Lo que dice |
|---|---|
| `dias` | "Pocos días" |
| `semanas` | "Un par de semanas" |
| `meses` | "Algunos meses" |
| `trimestres` | "Trimestres / mucho" → **DEEP `modelo_delivery_saas`** |

**Banderas rojas**: `nunca` + apetito `agresivo` → desalineación. Antes de IA, proceso de deploy.

---

## q5_4_lockin — Vendor lock-in percibido

**Concepto**: lock-in se acumula silencioso. Una IA mal elegida ahora = lock-in más caro durante 5 años. La pregunta no es "¿es bueno este vendor?" sino "¿cuánto duele salir?".

**Por qué importa**: clientes con `alto` lock-in que no fueron evaluado están en deuda técnica oculta.

**Pregunta abierta**: *"Si mañana decidís cambiar de [vendor crítico mencionado en q5_2], ¿cuánto te llevaría? ¿Semanas, meses, un proyecto entero?"*

**Decision tree → opciones**:

| q5_4_level | Lo que dice |
|---|---|
| `bajo` | "Lo cambiamos en semanas" |
| `medio` | "Posible pero costoso" |
| `alto` | "Sería un proyecto mayor" → **DEEP `arquitectura_agnostica`** |
| `no_evaluado` | "No lo pensamos" |

`q5_4_example` (texto opcional): pedí el caso del mayor lock-in actual. Útil para el LLM.

**Banderas rojas**:
- `bajo` declarado pero usa SAP / Salesforce hace 10 años → bajar a `medio` o `alto` con confirmación.
- `no_evaluado` + sector regulado → riesgo: en una crisis legal, no podés salir rápido del vendor.

---

## Cierre de bloque 5

Síntesis: *"Infra X, vendor crítico Y, deploy Z, lock-in W. Eso define el arquetipo: cloud-native, híbrido manejable, on-prem constrained, o sin gestionar. Y nos dice si el piloto es compatible con tu cadencia."*

**DEEP triggers a anotar**: `ia_self_hosted`, `modelo_delivery_saas`, `arquitectura_agnostica`.
