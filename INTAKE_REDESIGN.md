# Rediseño del Formulario In-Take — Zanovix AI Readiness
**Versión:** 2.0  
**Fecha:** Marzo 2026  
**Criterio:** Mantener lo que funciona, añadir profundidad donde el LLM pierde información

---

## CAMBIOS RESPECTO A V1

### Mantener sin cambios
- Bloque 1: Datos empresa (P1-7) ✅
- Bloque 2: Inventario herramientas (P8-13) ✅
- Bloque 3: Uso por áreas P14-20 → **mejorar opciones** (ver abajo)
- Bloque 5: Compliance / datos personales (P23-33) ✅
- Bloque 6: Contexto comercial (P38-43) ✅

### Cambios en Bloque 3 — Uso por áreas (P14-20)
**Problema:** Las opciones actuales ("No usamos IA", "Usamos herramientas básicas", "Uso avanzado") 
no capturan *qué* se hace. El LLM no puede generar insight útil con eso.

**Mejora:** Cambiar las opciones de cada área a:
- No usamos IA en esta área
- Usamos herramientas genéricas (ChatGPT, Copilot, etc.) de forma individual
- Tenemos algún proceso automatizado (chatbot, flujo, integración)
- Tenemos sistemas de IA integrados en nuestro flujo operativo

Añadir en cada área: campo de texto corto "¿Qué herramienta o proceso concreto?" (opcional)

---

## MÓDULO NUEVO — Profundidad del proceso prioritario
**Insertar entre P22 y P23**  
**Lógica:** Solo se muestra cuando P22 tiene respuesta (siempre que haya un proceso concreto)  
**Objetivo:** Dar al LLM datos suficientes para calcular ROI real y proponer solución concreta

---

### P22b — Personas involucradas en ese proceso hoy
*¿Cuántas personas de tu equipo intervienen habitualmente en ese proceso?*
- Solo yo
- 2-3 personas
- 4-6 personas
- Más de 6 personas

**Por qué:** Multiplica directamente en el cálculo de ROI. Sin esto, el LLM asume.

---

### P22c — Tiempo invertido por persona
*¿Cuánto tiempo dedica aproximadamente cada persona a ese proceso por semana?*
- Menos de 2h
- 2-5h
- 5-10h
- Más de 10h
- No lo hemos medido, pero es mucho

**Por qué:** Con P22b y P22c el LLM calcula horas/semana reales, no lo inventa.

---

### P22d — Estado del dato
*Los documentos o datos que maneja ese proceso, ¿cómo llegan normalmente?*
Selección múltiple:
- Por email (adjuntos)
- Por WhatsApp (mensajes, fotos)
- A través de un formulario web
- En papel / físico que luego digitalizamos
- Desde un sistema (ERP, CRM, software de gestión...)
- En Excel o ficheros descargados manualmente
- De forma verbal / telefónica

**Por qué:** Define completamente la viabilidad técnica. Un proceso con papel tiene semanas de diferencia en implementación vs uno que llega por email.

---

### P22e — Sistemas ya existentes
*¿Usáis alguno de estos sistemas en vuestra empresa? (aunque no sean de IA)*
Selección múltiple:
- Software de gestión / ERP (SAP, Holded, A3, Sage, Odoo...)
- CRM (Salesforce, HubSpot, Pipedrive, Zoho...)
- Software de contabilidad o facturación
- Herramienta de gestión de citas o reservas
- Plataforma de ecommerce (Shopify, WooCommerce...)
- Google Workspace / Microsoft 365
- Ninguno de los anteriores / Solo hojas de cálculo
- Otro: ___

**Por qué:** Es la pregunta más ignorada en assessments de IA y la más crítica para el alcance técnico. Integrar con Holded es trivial. Integrar con SAP puede triplicar el coste.

---

### P22f — Qué falla exactamente
*¿Qué es lo que más tiempo consume o más errores genera en ese proceso hoy?*
Selección múltiple:
- Clasificar o enrutar información manualmente
- Buscar información en distintos sistemas o archivos
- Responder las mismas preguntas o peticiones repetidamente
- Pasar datos de un sistema a otro a mano
- Revisar y corregir errores antes de procesar
- Esperas o cuellos de botella porque depende de otra persona
- Generar documentos, informes o comunicaciones de forma manual
- Otro: ___

**Por qué:** El LLM necesita saber el punto de dolor específico para proponer la solución correcta. "Ahorrar tiempo" no es suficiente.

---

### P22g — Resultado esperado (cuantificado)
*Si ese proceso funcionara perfectamente con IA, ¿qué resultado concreto esperarías?*
Selección múltiple (puede marcar varios):
- Respuesta al cliente en menos de 5 minutos (24/7)
- Reducir el tiempo de procesamiento de X a Y (ej: de 30 min a 2 min)
- Eliminar errores manuales en la entrada de datos
- Poder gestionar el mismo volumen con menos personas
- Liberar al equipo para tareas de mayor valor
- Reducir coste operativo (€ concreto si lo saben)
- Mejorar la experiencia del cliente

**Por qué:** Ancla las expectativas del cliente desde el inicio. El informe puede contrastar lo esperado con lo viable, y la propuesta puede usar exactamente el lenguaje del cliente.

---

### P22h — Urgencia del proceso
*¿Hay algún momento del año en que ese proceso se vuelve crítico o desbordante?*
- No, es constante todo el año
- Sí, en temporada alta (cuándo: ___)
- Sí, en períodos de cierre fiscal / contable
- Sí, justo ahora mismo
- Otro: ___

**Por qué:** Ancla el timing de la propuesta. Si la temporada alta es en julio y estamos en marzo, el cliente necesita algo funcional en 8 semanas — cambia radicalmente la priorización del roadmap.

---

## CAMBIOS EN BLOQUE 6 — Contexto comercial

### P37 — Horas perdidas (mejorar)
**Actual:** "¿Cuánto tiempo estimas que se pierde semanalmente en tareas manuales o repetitivas?"  
**Problema:** Respuesta muy genérica, no vinculada al proceso prioritario  
**Mejora:** Cambiar a "¿Cuántas horas semanales se pierden específicamente en el proceso que describes arriba?"  
(La pregunta general ya queda cubierta por P22b + P22c)

### P39 — Presupuesto (añadir rango más preciso)
**Actual:** Opciones genéricas  
**Mejora:** Añadir opción "No tenemos presupuesto definido pero estamos dispuestos a calcularlo"  
(Elimina falsos negativos — muchas PYMEs no tienen presupuesto "previsto" pero sí voluntad)

---

## IMPACTO EN EL SCORING Y EL LLM

Con estas 7 preguntas nuevas, el LLM puede:

1. **Calcular ROI con datos reales:**  
   P22b (personas) × P22c (horas) × coste/hora × % automatizable = rango económico concreto  
   En lugar de "estimamos que podría ahorrar X" → "con los datos declarados, el ahorro sería de X-Y€/año"

2. **Proponer solución técnica específica:**  
   P22d (estado del dato) + P22e (sistemas existentes) → factibilidad técnica real  
   "Podemos integrar con vuestro Holded existente" vs "requiere digitalización previa"

3. **Eliminar la discovery call del roadmap:**  
   Con P22f (qué falla) + P22g (resultado esperado) el informe puede cerrar con propuesta ejecutable  
   En lugar de "siguiente paso: discovery call" → "Propuesta: [solución concreta], [precio], [plazo]"

4. **Personalizar el timing del roadmap:**  
   P22h (urgencia) → el roadmap refleja la realidad del negocio  
   "Implementar antes del 1 de julio" en lugar de "Fase 1: semanas 1-4" genérico

---

## ORDEN FINAL DEL FORMULARIO v2.0

**Bloque 1 — La empresa** (P1-7) — sin cambios  
**Bloque 2 — Herramientas de IA actuales** (P8-13) — sin cambios  
**Bloque 3 — Adopción por áreas** (P14-20) — opciones mejoradas  
**Bloque 4 — Proceso prioritario** (P21-22) — sin cambios  
**Bloque 4b — Profundidad del proceso** (P22b-22h) — **NUEVO**  
**Bloque 5 — Compliance y datos** (P23-33) — sin cambios  
**Bloque 6 — Contexto y objetivos** (P34-43) — ajustes menores  

**Total preguntas:** 43 → ~50 (pero las 7 nuevas son de selección múltiple, no texto libre — menos fricción)

---

## NOTA DE IMPLEMENTACIÓN

Para Google Forms:
- P22b-22h se añaden después de P22 
- No hay lógica condicional real en Google Forms → estas preguntas van siempre, con instrucción "Responde sobre el proceso que mencionaste arriba"
- Si migráis a Tally en el futuro, estas preguntas se convierten en condicionales reales (solo aparecen si P22 tiene respuesta)

Para el pipeline:
- El scoring_engine no necesita cambios (estas preguntas no afectan al score matemático)
- El llm_enricher necesita actualizar el prompt para incluir los nuevos campos
- Las nuevas variables en el JSON: proceso_personas, proceso_horas, proceso_dato_estado, sistemas_existentes, proceso_falla, proceso_resultado_esperado, proceso_urgencia
