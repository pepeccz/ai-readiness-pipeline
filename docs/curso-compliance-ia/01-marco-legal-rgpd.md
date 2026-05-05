# 01 — Marco legal RGPD para consultor IA en PYME

> **Objetivo del módulo**: que entiendas el RGPD lo suficiente como para diagnosticar tratamientos de datos en una PYME, hablar el mismo idioma que el DPO o el abogado del cliente, y saber cuándo el problema te excede y hay que derivar.

No sos abogado. Tu trabajo no es interpretar jurisprudencia, es **detectar riesgos, traducirlos a la PYME y proponer soluciones técnicas/operativas**. Para eso, este módulo.

---

## 1. ¿Qué es un dato personal? (Art. 4.1 RGPD)

Definición literal: *"toda información sobre una persona física identificada o identificable"*. La clave es **identificable**: no hace falta que aparezca el nombre, basta con que combinando datos puedas llegar a la persona.

Ejemplos que solés encontrar en una PYME:

| Dato | ¿Personal? | Por qué |
|------|-----------|---------|
| `juan.perez@empresa.com` | Sí | Identifica directamente |
| `info@empresa.com` | Depende | Si solo lo lee una persona concreta, sí |
| Dirección IP (192.168.x.x) | Sí | EDPB y TJUE confirmado (caso Breyer) |
| Cookie con ID de sesión | Sí | Permite rastrear comportamiento |
| Foto de empleado en intranet | Sí | Identifica visualmente |
| Voz en grabación de call center | Sí | Biométrico potencial |
| Matrícula de vehículo | Sí | Vinculable al titular |
| Teléfono móvil de contacto | Sí | Casi siempre asociado a persona |

> **Trampa típica**: el cliente te dice "pero esto está anonimizado". Verificá. **Seudonimización ≠ anonimización**. Si existe una tabla que mapea el ID al nombre, sigue siendo dato personal (Considerando 26 RGPD).

---

## 2. Categorías especiales — datos sensibles (Art. 9)

Tratamiento **prohibido por defecto**, salvo excepciones tasadas (consentimiento explícito, obligación laboral, interés vital, etc.).

- Origen racial o étnico
- Opiniones políticas
- Convicciones religiosas o filosóficas
- Afiliación sindical
- Datos genéticos
- Datos biométricos para identificar unívocamente
- Datos de salud
- Vida sexual u orientación sexual

**Implicación para vos como consultor IA**: si el cliente quiere usar IA con CV (puede haber datos de salud o sindicales), reconocimiento facial para fichaje (biométrico), o un chatbot de salud, **se enciende la alarma**. Probable DPIA obligatoria + base jurídica reforzada + consulta a abogado.

> Ejemplo PYME: clínica dental de 12 empleados quiere un asistente IA que resuma historiales. Eso es Art. 9 puro. No empieces sin DPIA y sin que el cliente tenga claro que el proveedor del LLM no puede entrenar con esos datos (DPA + cláusulas específicas).

---

## 3. Principios del RGPD (Art. 5) con ejemplo PYME por cada uno

| Principio | Qué significa | Ejemplo PYME |
|-----------|---------------|--------------|
| **Licitud, lealtad, transparencia** | Necesitás base jurídica + informar al titular | Inmobiliaria que captura leads en web debe tener aviso de privacidad visible y base jurídica clara (consentimiento o interés legítimo) |
| **Limitación de la finalidad** | Recogés para X, no podés usarlo para Y sin nueva base | Gestoría que tiene emails de clientes para facturas no puede usarlos para enviar newsletter sin consentimiento adicional |
| **Minimización** | Solo los datos necesarios | Tienda online que pide DNI para enviar zapatillas: NO. Pide solo nombre y dirección |
| **Exactitud** | Datos correctos y actualizados | CRM con teléfonos de hace 5 años sin proceso de actualización: incumplimiento |
| **Limitación del plazo de conservación** | No los guardes "por si acaso" eternamente | Despacho de arquitectura que conserva CVs de candidatos rechazados 8 años: sobra. Política habitual: 1-2 años máx |
| **Integridad y confidencialidad** | Cifrado, control de accesos, backups | Asesoría que comparte hojas Excel con datos por WhatsApp sin cifrar: incumplimiento técnico |
| **Responsabilidad proactiva (accountability)** | Tenés que poder demostrar que cumplís | Si la AEPD te pregunta, hace falta RAT, DPIAs, contratos de encargo, formación documentada |

> El principio de **accountability** es el que más subestima la PYME. No basta con cumplir, hay que **documentarlo**. Tu trabajo como consultor incluye dejar trazabilidad.

---

## 4. Roles en un proyecto IA típico

| Rol | Quién es | En proyecto IA típico |
|-----|----------|----------------------|
| **Responsable del tratamiento** | Quien decide el "para qué" y el "cómo" | La PYME cliente |
| **Encargado del tratamiento** | Quien trata datos por cuenta del responsable | Tu agencia/tú si procesás datos del cliente; el proveedor del LLM (OpenAI, Anthropic) si lo usás vía API |
| **Sub-encargado** | El encargado del encargado | Si tu herramienta usa AWS por debajo, AWS es sub-encargado |
| **DPO (Delegado de Protección de Datos)** | Figura obligatoria en algunos casos (Art. 37) | Puede ser interno o externo de la PYME. Tu interlocutor ideal |
| **Corresponsables** | Dos entidades deciden conjuntamente fines y medios | Raro en PYME, típico en joint ventures de marketing |

> **Cadena típica que vas a montar**:  
> Cliente PYME (responsable) → Tu consultora (encargada) → OpenAI/Anthropic (sub-encargada) → AWS/GCP (sub-sub-encargada).  
>  
> Cada eslabón necesita **contrato de encargo de tratamiento (DPA, Art. 28)**. Sin DPA firmado, no hay tratamiento legal.

¿Cuándo es **obligatorio** tener DPO? (Art. 37):
- Autoridades públicas
- Tratamientos a gran escala que requieran observación sistemática
- Tratamientos a gran escala de categorías especiales

La PYME media no está obligada, pero muchas lo nombran voluntariamente. Si no tiene DPO, tu rol como consultor pesa más — y la presión sobre derivar a abogado en casos grises también.

---

## 5. Sanciones AEPD

Dos tramos (Art. 83 RGPD):

- **Hasta 10 M€ o 2% facturación global anual** (la mayor): incumplimientos formales (registro de actividades, contratos de encargo, designación DPO)
- **Hasta 20 M€ o 4% facturación global anual** (la mayor): incumplimientos sustantivos (principios, bases jurídicas, derechos de los titulares, transferencias internacionales)

> **Realidad PYME**: las sanciones AEPD a PYMEs suelen estar entre 1.000€ y 60.000€. No es ruina, pero sí golpe serio. Y la **reputación** pesa más: las resoluciones se publican.

Ejemplos reales (consultables en [aepd.es](https://www.aepd.es) → Resoluciones):
- Sanciones por brechas no notificadas en 72h
- Sanciones por uso de cookies sin consentimiento
- Sanciones por videovigilancia mal señalizada

---

## 6. Mini-checklist para arrancar con un cliente nuevo

Antes de proponer **cualquier solución IA**, recopilá esto:

- [ ] ¿Tienen aviso de privacidad y política de cookies actualizados?
- [ ] ¿Tienen RAT (Registro de Actividades de Tratamiento, Art. 30)?
- [ ] ¿Hay DPO designado? Datos de contacto
- [ ] ¿Tienen DPIAs previas? ¿De qué tratamientos?
- [ ] ¿Qué proveedores cloud/SaaS usan? ¿DPA firmados con cada uno?
- [ ] ¿Hay transferencias internacionales (USA, India, etc.)? ¿Con qué garantías (SCC, decisión de adecuación)?
- [ ] ¿Han tenido brechas de seguridad? ¿Procedimiento de notificación 72h documentado?
- [ ] ¿Quién es el interlocutor jurídico? (asesor externo, abogado interno)
- [ ] ¿Qué datos personales toca el proyecto IA propuesto? ¿Hay categorías especiales?
- [ ] ¿Existe decisión automatizada con efecto jurídico (Art. 22)?

> **Regla del consultor pragmático**: si tres respuestas son "no sé" o "no tenemos", **antes de IA hace falta higiene básica de RGPD**. Vendelo como fase 0 del proyecto.

---

## Referencias oficiales

- Texto consolidado RGPD (Reglamento UE 2016/679): [EUR-Lex](https://eur-lex.europa.eu/eli/reg/2016/679/oj)
- AEPD — guías y plantillas: [aepd.es](https://www.aepd.es)
- EDPB — directrices interpretativas: [edpb.europa.eu](https://edpb.europa.eu)
- LOPDGDD (España, ley nacional complementaria): BOE-A-2018-16673

> **Cierre**: el RGPD no es un obstáculo, es el **lenguaje común** que vas a hablar con el cliente, su abogado y los proveedores. Dominalo a nivel operativo y vas a ahorrarte el 80% de los problemas en los proyectos IA.
