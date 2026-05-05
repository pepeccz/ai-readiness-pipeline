# 02 — AI Act: las 4 categorías de riesgo y cómo clasificar a tu cliente

> **Objetivo del módulo**: que puedas mirar un caso PYME y decir, en menos de 15 minutos, en qué categoría de riesgo cae el sistema IA propuesto, qué obligaciones aplican, y si necesitás derivar a abogado.

El AI Act (Reglamento UE 2024/1689) es el primer marco jurídico horizontal del mundo sobre inteligencia artificial. **Convive con el RGPD, no lo sustituye**. Si hay datos personales, ambos aplican.

---

## 1. Timeline — qué fechas tenés que saber

| Fecha | Qué entra en vigor |
|-------|--------------------|
| **1 agosto 2024** | El AI Act entra en vigor |
| **2 febrero 2025** | Aplicación de **prohibiciones** (riesgo inaceptable) y obligaciones de **alfabetización en IA** (Art. 4) |
| **2 agosto 2025** | Obligaciones para **modelos de IA de propósito general (GPAI)** + sanciones + gobernanza |
| **2 agosto 2026** | Aplicación general (incluye **alto riesgo Anexo III**) |
| **2 agosto 2027** | Aplicación a sistemas alto riesgo del **Anexo I** (productos regulados: juguetes, dispositivos médicos, etc.) |

> **Lo que ya está vivo a fecha de hoy (mayo 2026)**: prohibiciones + alfabetización + GPAI. **Alto riesgo del Anexo III aplica desde agosto 2026** — quedan tres meses. Si tu cliente tiene un sistema candidato a alto riesgo, esto es **urgente**.

---

## 2. Las 4 categorías

### 2.1 Riesgo INACEPTABLE (Art. 5) — PROHIBIDO

No se puede hacer. Punto. Aunque el cliente lo pida y pague.

- **Manipulación subliminal** que cause daño
- **Explotación de vulnerabilidades** (edad, discapacidad, situación socioeconómica)
- **Social scoring** por autoridades públicas
- **Predicción de delitos** basada solo en perfilado de personalidad
- **Scraping masivo de imágenes faciales** para crear bases biométricas
- **Reconocimiento de emociones** en trabajo y educación (salvo médicas/seguridad)
- **Categorización biométrica** por raza, opiniones políticas, religión, orientación sexual
- **Identificación biométrica remota en tiempo real** en espacios públicos por fuerzas de seguridad (con excepciones tasadas)

> Ejemplo PYME: una academia de idiomas quiere un sistema que **detecte emociones de alumnos por webcam** para "ajustar la clase". **PROHIBIDO** desde febrero 2025. Tu rol: explicárselo y proponer alternativa (encuesta de satisfacción manual, por ejemplo).

### 2.2 ALTO RIESGO (Art. 6 + Anexo III)

**Permitido pero muy regulado.** Requiere paquete de compliance pesado antes del despliegue.

Sectores típicos donde aparece (Anexo III):
- **Biometría** (identificación, categorización, reconocimiento emocional fuera de prohibidos)
- **Infraestructuras críticas** (agua, gas, electricidad, tráfico)
- **Educación y formación profesional** (admisión, evaluación, detección de fraude en exámenes)
- **Empleo y RR.HH.** (cribado de CVs, decisiones de promoción/despido, monitorización de rendimiento)
- **Servicios esenciales públicos y privados** (scoring crediticio, scoring para seguros de vida/salud, gestión de emergencias)
- **Aplicación de la ley**
- **Migración, asilo y control fronterizo**
- **Administración de justicia y procesos democráticos**

Obligaciones del proveedor (Arts. 8–17):
1. Sistema de **gestión de riesgos** continuo
2. **Gobernanza de datos** (calidad, sesgos, representatividad)
3. **Documentación técnica** (Anexo IV)
4. **Registro de eventos (logging)** automático
5. **Transparencia e información** al usuario (deployer)
6. **Supervisión humana** efectiva
7. **Robustez, exactitud y ciberseguridad**
8. **Sistema de gestión de la calidad**
9. **Marcado CE** + declaración de conformidad
10. **Registro en base de datos UE** antes de comercializar

Obligaciones del **deployer** (Art. 26) — la PYME que lo usa:
- Usar el sistema según instrucciones
- Garantizar supervisión humana competente
- Monitorizar funcionamiento
- Conservar logs
- Informar a personas afectadas en empleo/decisiones
- **DPIA bajo RGPD** si hay datos personales

> Ejemplo PYME: empresa de 80 empleados quiere usar una herramienta IA tipo HireVue para cribar CVs. Eso es **alto riesgo Anexo III punto 4**. Como deployer, la PYME debe: garantizar supervisión humana, informar a candidatos, hacer DPIA, conservar logs, formar al equipo. Como consultor, tu trabajo es montar ese paquete.

### 2.3 RIESGO LIMITADO (Art. 50)

**Obligación principal: TRANSPARENCIA.**

- **Chatbots / sistemas conversacionales**: el usuario debe saber que habla con una IA
- **Generadores de contenido sintético** (texto, imagen, audio, video): marcado/watermarking que indique que es generado por IA (formato legible por máquina)
- **Deepfakes**: declaración explícita de que es contenido manipulado (excepciones para arte, sátira con matices)
- **Reconocimiento emocional / categorización biométrica permitidos**: informar a las personas

> Ejemplo PYME: e-commerce que pone un chatbot para soporte. Riesgo limitado. Acción mínima: aviso visible "Estás hablando con un asistente IA" + opción de pasar a humano. Si además el chatbot toma decisiones automatizadas con efecto jurídico (denegación de devolución, por ejemplo) → además Art. 22 RGPD.

### 2.4 RIESGO MÍNIMO

Sin obligaciones específicas del AI Act. Aplican RGPD si hay datos personales y código de conducta voluntario.

Ejemplos: filtros de spam, NPCs en videojuegos, optimización de rutas, sistemas de recomendación de productos básicos, autocorrector de texto.

---

## 3. Tabla — casos típicos PYME → categoría probable

| Caso PYME | Categoría probable | Notas |
|-----------|--------------------|-------|
| Chatbot atención cliente en e-commerce | Limitado | Transparencia + RGPD |
| Generador de descripciones de producto con LLM | Limitado / Mínimo | Watermarking si publica contenido sintético |
| Cribado automático de CVs | **ALTO RIESGO** | Anexo III.4 |
| Asistente IA que resume historiales clínicos | **ALTO RIESGO** | Anexo III + Art. 9 RGPD |
| Sistema de scoring para conceder microcréditos | **ALTO RIESGO** | Anexo III.5 |
| Reconocimiento facial para fichaje empleados | Alto riesgo o prohibido según uso | Categorización biométrica + RGPD Art. 9 |
| Detección de fraude en exámenes online | **ALTO RIESGO** | Anexo III.3 |
| Predicción de demanda en stock | Mínimo | Sin datos personales |
| Asistente IA interno para redactar emails | Mínimo / Limitado | RGPD si datos de clientes en prompts |
| Análisis de sentimiento de reviews | Limitado | Si se publica algo, transparencia |
| Detección de emociones en call center para evaluar agentes | **PROHIBIDO** | Art. 5 — emociones en trabajo |

---

## 4. Sanciones AI Act

Más duras que RGPD:

| Infracción | Sanción máxima |
|-----------|----------------|
| Prácticas prohibidas (Art. 5) | **35 M€ o 7% facturación global** (la mayor) |
| Incumplimientos de obligaciones (alto riesgo, transparencia, GPAI) | **15 M€ o 3% facturación global** |
| Información falsa o engañosa a autoridades | **7,5 M€ o 1% facturación global** |

Para PYMEs y startups, las sanciones se aplican con el importe **menor** entre los dos. Aún así, queman.

---

## 5. Algoritmo de decisión para clasificar en sesión con cliente

Preguntas en orden, con respuesta SÍ/NO:

```
1. ¿El sistema cae en alguna práctica del Art. 5 (prohibidas)?
   SÍ → STOP. No se puede hacer. Buscá alternativa.
   NO → seguí.

2. ¿Es un sistema biométrico, o se usa en alguno de los sectores
   del Anexo III (educación, empleo, servicios esenciales,
   infraestructuras críticas, ley/justicia, migración)?
   SÍ → ALTO RIESGO. Paquete de compliance completo. Derivá a abogado.
   NO → seguí.

3. ¿Es un chatbot, generador de contenido sintético, deepfake o
   reconocimiento emocional permitido?
   SÍ → RIESGO LIMITADO. Transparencia + (si datos) RGPD.
   NO → seguí.

4. Resto → RIESGO MÍNIMO. Solo RGPD si hay datos personales.
```

> **Truco operativo**: imprimí esto y llevalo a la primera reunión. Lo recorrés con el cliente en 10 minutos y ya tenés el 60% del scope claro.

---

## 6. ¿Cuándo derivás SIEMPRE a abogado?

- Caso ambiguo entre alto riesgo y limitado
- Sospecha de práctica prohibida
- Decisión automatizada con efecto jurídico (Art. 22 RGPD + alto riesgo)
- Transferencias internacionales fuera del EEE
- Cliente quiere comercializar el sistema IA (pasa de deployer a proveedor)
- Modelos GPAI con riesgo sistémico (>10^25 FLOPs entrenamiento)

---

## Referencias oficiales

- Texto AI Act (Reglamento UE 2024/1689): [EUR-Lex](https://eur-lex.europa.eu/eli/reg/2024/1689/oj)
- Portal con explorador interactivo: [artificialintelligenceact.eu](https://artificialintelligenceact.eu)
- Comisión Europea — AI Office: [digital-strategy.ec.europa.eu/en/policies/ai-office](https://digital-strategy.ec.europa.eu/en/policies/ai-office)
- AEPD — guía sobre IA y protección de datos: [aepd.es](https://www.aepd.es)

> **Cierre**: clasificar bien en la primera sesión te ahorra rehacer el proyecto a mitad. Y si dudás entre limitado y alto riesgo, asumí alto riesgo hasta que el abogado del cliente confirme lo contrario. Es más barato sobre-cumplir que recibir una resolución sancionadora.
