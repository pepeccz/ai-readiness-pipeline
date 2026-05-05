# 03 — DPIA: cuándo es obligatoria y cómo redactarla operativamente

> **Objetivo del módulo**: que sepas detectar cuándo un proyecto IA dispara DPIA obligatoria, redactar un borrador defendible, y entender qué firma el cliente y qué validás vos vs. lo que valida el DPO o el abogado.

DPIA = **Data Protection Impact Assessment** (en español: **EIPD — Evaluación de Impacto en la Protección de Datos**). Es una de las herramientas más importantes del RGPD y es **donde más valor agregado podés aportar como consultor IA**: la PYME no sabe hacerla, el abogado sabe la teoría pero no el detalle técnico de la IA, y vos estás justo en el medio.

---

## 1. ¿Qué es una DPIA?

Análisis previo y sistemático de los **riesgos para los derechos y libertades** de las personas físicas que un tratamiento de datos puede generar, junto con las **medidas para mitigarlos**.

**Clave conceptual**: la DPIA NO evalúa riesgos para la empresa. Evalúa riesgos **para el titular del dato** (el ciudadano, el empleado, el cliente). Esto cambia totalmente la perspectiva.

---

## 2. ¿Cuándo es OBLIGATORIA? (Art. 35 RGPD)

Cuando el tratamiento "entrañe un alto riesgo para los derechos y libertades", **especialmente** en estos casos:

1. **Evaluación sistemática y exhaustiva** de aspectos personales basada en tratamiento automatizado, incluida elaboración de perfiles, con efectos jurídicos o significativos
2. **Tratamiento a gran escala de categorías especiales** (Art. 9) o datos relativos a condenas (Art. 10)
3. **Observación sistemática a gran escala de zona de acceso público** (videovigilancia masiva)

### Lista oficial AEPD — actividades que SIEMPRE requieren DPIA

La AEPD publicó una lista de **operaciones que requieren DPIA obligatoriamente**. Resumen operativo:

- Tratamientos con **perfilado o evaluación** que produzcan efectos jurídicos
- Tratamientos con **decisiones automatizadas** con efecto jurídico
- **Observación sistemática** (incluye monitorización de empleados, videovigilancia avanzada)
- Tratamiento de **datos sensibles o de naturaleza altamente personal**
- Tratamiento de datos a **gran escala**
- **Combinación o cruce** de conjuntos de datos
- Datos relativos a **personas vulnerables** (menores, pacientes, empleados)
- **Uso innovador o aplicación de soluciones tecnológicas o organizativas nuevas** (acá entra **casi cualquier proyecto IA generativa actual**)
- Tratamientos que **impidan ejercer derechos** o acceder a servicios

> **Regla del consultor IA**: si introducís un LLM en un flujo que toca datos personales, **asumí DPIA por defecto** por el criterio de "uso innovador". Si el DPO del cliente dice que no hace falta, que lo justifique por escrito.

---

## 3. Estructura mínima de una DPIA (Art. 35.7)

Cuatro bloques obligatorios:

1. **Descripción sistemática** del tratamiento y sus finalidades
2. **Evaluación de la necesidad y proporcionalidad** respecto a la finalidad
3. **Evaluación de los riesgos** para los derechos y libertades del interesado
4. **Medidas previstas para afrontar los riesgos**, incluidas garantías y mecanismos de seguridad

---

## 4. PASO A PASO operativo (lo que hace el consultor)

### Paso 1 — Cuestionario inicial al cliente

Necesitás esta info antes de redactar nada. Mandala como formulario:

- Descripción del proyecto IA en lenguaje natural (1 párrafo)
- Categorías de datos tratados (lista exhaustiva)
- Categorías de interesados afectados (clientes, empleados, candidatos, menores...)
- Volumen aproximado (¿cuántas personas? ¿cuántos registros?)
- Finalidad concreta (no "mejorar el negocio", sino "automatizar respuestas a tickets de soporte")
- Base jurídica candidata (ver módulo 04)
- Plazo de conservación
- Destinatarios y proveedores (incluido el LLM)
- Transferencias internacionales (si OpenAI/Anthropic vía API → USA)
- Tecnologías y arquitectura técnica

### Paso 2 — Identificar tratamientos individuales

Un proyecto IA suele esconder **varios tratamientos**. Ejemplo: chatbot de atención cliente
- Tratamiento 1: recogida del mensaje del usuario
- Tratamiento 2: envío del prompt al LLM
- Tratamiento 3: almacenamiento de logs para mejora del servicio
- Tratamiento 4: derivación a agente humano

Cada uno puede tener distinta base jurídica y distinto riesgo. Listalos por separado.

### Paso 3 — Evaluar riesgo (probabilidad x impacto)

Usá una matriz simple. Para cada riesgo identificado:

| Probabilidad | 1 (baja) | 2 (media) | 3 (alta) |
|--------------|----------|-----------|----------|
| Impacto 1 (bajo) | Bajo | Bajo | Medio |
| Impacto 2 (medio) | Bajo | Medio | Alto |
| Impacto 3 (alto) | Medio | Alto | **Crítico** |

Riesgos típicos en proyecto IA:
- Acceso no autorizado a logs con datos personales
- **Reidentificación** desde respuestas del modelo
- **Memorización del modelo** (fuga de datos del prompt en respuestas a otros usuarios)
- **Sesgo discriminatorio** en decisiones automatizadas
- **Transferencia internacional** sin garantías a USA
- **Falta de supervisión humana** efectiva
- **Inexactitud / alucinación** con consecuencia para el titular

### Paso 4 — Proponer medidas de mitigación

Para cada riesgo Alto o Crítico, medida concreta. Catálogo típico:

| Riesgo | Medida |
|--------|--------|
| Memorización del LLM | Contrato con proveedor que prohíba entrenamiento con prompts (DPA + addendum); usar API con flag de no-training |
| Transferencia USA | Cláusulas Contractuales Tipo (SCC) + análisis de impacto de transferencias (TIA) |
| Sesgo | Auditoría del dataset; revisión humana obligatoria sobre el output |
| Reidentificación | Pseudonimización antes del prompt; eliminación de PII en logs |
| Falta supervisión | Supervisión humana documentada; opción de revisión por persona |
| Alucinación | Disclaimer al usuario; flujo de escalado a humano; humano-en-el-bucle para decisiones |

### Paso 5 — Documentar

Plantilla AEPD oficial: [Gestiona_EIPD](https://www.aepd.es/guias/herramienta-evalua-riesgo-rgpd.pdf) y la herramienta **Gestiona EIPD** descargable desde aepd.es.

Estructura recomendada del documento final:
1. Identificación (responsable, DPO, encargado, fecha, versión)
2. Descripción del tratamiento
3. Necesidad y proporcionalidad
4. Consulta a interesados (si procede)
5. Identificación de riesgos
6. Evaluación de riesgos
7. Medidas
8. Plan de seguimiento y revisión
9. Aprobación

### Paso 6 — Validación jurídica

**Vos redactás el borrador. NO firmás la DPIA.** La DPIA la **firma el responsable del tratamiento** (la PYME, su CEO o quien tenga poder). El **DPO da el dictamen** (Art. 35.2). Si no hay DPO, recomendá fuerte consulta a abogado externo antes de la firma.

> Si el riesgo residual sigue siendo alto tras las medidas, **consulta previa obligatoria a la AEPD** (Art. 36). Esto es señal de alerta máxima — derivá a abogado sí o sí.

---

## 5. Roles claros — qué hacés vos y qué no

| Acción | Consultor IA | DPO / Abogado | Cliente (responsable) |
|--------|--------------|---------------|----------------------|
| Cuestionario y recopilación | ✅ | | apoya |
| Identificar tratamientos técnicos | ✅ | revisa | |
| Evaluar riesgos técnicos | ✅ | revisa | |
| Evaluar riesgos jurídicos | apoya | ✅ | |
| Proponer medidas técnicas | ✅ | revisa | |
| Proponer medidas organizativas | apoya | ✅ | decide |
| Redactar el documento | ✅ | revisa | |
| **Dictamen formal** | | ✅ | |
| **Firma final** | | | ✅ |
| Consulta previa AEPD si aplica | apoya | ✅ | firma |

---

## 6. Caso real — PYME de 30 empleados que implementa chatbot de atención cliente

**Contexto**: e-commerce de productos para mascotas. Quieren chatbot 24/7 con LLM (vía API de proveedor USA). Tratará consultas de clientes (nombre, email, número de pedido, a veces dirección, ocasionalmente datos de salud de la mascota — no del humano).

**¿DPIA obligatoria?** Sí — uso innovador + tratamiento a gran escala de datos de clientes.

**Tratamientos identificados**:
1. Captura del mensaje del cliente → datos de contacto + contenido libre
2. Envío del prompt a API LLM → transferencia internacional
3. Almacenamiento de la conversación 12 meses → logs con PII
4. Análisis agregado para mejorar respuestas → posible perfilado

**Riesgos top**:
- **Alto**: transferencia a USA sin garantías reforzadas
- **Alto**: PII libre en prompts (cliente puede pegar DNI, datos de tarjeta)
- **Medio**: alucinación en información de pedidos (cliente recibe info incorrecta)
- **Medio**: memorización del modelo

**Medidas propuestas**:
- Proveedor con SCC + TIA documentado
- **Filtro de PII pre-prompt**: regex + clasificador para anonimizar antes de enviar al LLM
- **Aviso visible**: "Hablás con un asistente IA. No compartas datos sensibles. Para cuestiones complejas escribí soporte@..."
- Logs con cifrado, retención 6 meses (no 12), acceso restringido por rol
- Supervisión humana sobre conversaciones flagged
- Cláusula de no-entrenamiento en DPA con proveedor LLM

**Bases jurídicas**:
- Tratamiento 1 y 2: ejecución contractual (Art. 6.1.b)
- Tratamiento 3: interés legítimo con ponderación (Art. 6.1.f)
- Tratamiento 4: interés legítimo + opt-out

**Resultado esperado**: riesgo residual medio. No hace falta consulta previa AEPD. Firma el responsable, dictamen del DPO externo.

---

## Referencias oficiales

- AEPD — Listas DPIA y herramienta Gestiona EIPD: [aepd.es/guias](https://www.aepd.es/guias)
- EDPB — Directrices sobre DPIA (WP248): [edpb.europa.eu](https://edpb.europa.eu)
- Art. 35 RGPD: [EUR-Lex](https://eur-lex.europa.eu/eli/reg/2016/679/oj)

> **Cierre**: redactar DPIAs es donde más se nota un consultor IA bueno vs. uno mediocre. El malo copia plantillas. El bueno entiende los tratamientos técnicos, traduce los riesgos al lenguaje del titular, y propone medidas que el cliente puede implementar sin parar el proyecto. Apuntá a ser el segundo.
