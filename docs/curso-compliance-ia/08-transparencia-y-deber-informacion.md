# 08 — Transparencia y deber de información

> **Idea fuerza**: si tu cliente no puede explicar — en una pantalla, sin abogado al lado — qué hace con los datos y cuándo interviene una IA, está incumpliendo. La transparencia es el cimiento de todo el RGPD y ahora también del AI Act.

---

## 1. Transparencia RGPD (Arts. 13 y 14)

Cuando recogés datos personales, debés informar al interesado **en el mismo momento** (Art. 13: datos del propio interesado) o **dentro de un mes** (Art. 14: datos obtenidos de terceros).

### Información obligatoria mínima

| Bloque | Qué incluir |
|--------|-------------|
| **Identidad del responsable** | Razón social, NIF, contacto, DPO si lo hay |
| **Finalidades** | Concretas, no genéricas ("mejorar tu experiencia" NO vale) |
| **Base legal** | Consentimiento, contrato, obligación legal, interés legítimo... |
| **Destinatarios** | Categorías y nombres de encargados/cesionarios principales |
| **Transferencias internacionales** | A qué país, con qué garantías (CCT, decisión adecuación) |
| **Plazo conservación** | Concreto o criterios para determinarlo |
| **Derechos del interesado** | Cómo y dónde ejercerlos |
| **Reclamación AEPD** | Mencionarla expresamente |
| **Origen de los datos** (Art. 14) | Si no se obtuvieron del interesado |
| **Decisiones automatizadas** | Existencia, lógica, consecuencias (cuando aplique Art. 22) |

### Capas — el truco que funciona

La AEPD recomienda el **modelo en capas**:
- **1ª capa** (corta, junto al formulario): responsable, finalidad, derechos, link a la 2ª
- **2ª capa** (política completa): todo lo demás

Esto evita el muro de texto que nadie lee y cumple el principio de transparencia "en forma concisa, transparente, inteligible y de fácil acceso".

---

## 2. Transparencia AI Act (Art. 50) — la nueva capa

El Art. 50 del AI Act introduce obligaciones de transparencia para **todos** los sistemas IA, no solo alto riesgo. Aplica desde **2 de agosto de 2026**.

| Caso | Obligación |
|------|-----------|
| **Sistema interactúa con persona física** (chatbot, asistente) | Informar de forma clara que se está interactuando con una IA, salvo que sea evidente |
| **Generación de contenido sintético** (texto, imagen, audio, vídeo) | El proveedor debe marcar el contenido como generado/manipulado por IA, en formato legible por máquina |
| **Deepfakes** (manipulación que parece real de personas, lugares, eventos) | El **desplegador** (quien lo usa) debe etiquetar visiblemente como artificial |
| **Texto de interés público** generado por IA | Informar que se ha generado o manipulado artificialmente |
| **Reconocimiento emocional o categorización biométrica** | Informar a las personas afectadas |

> **Importante**: transparencia AI Act se **suma** a la del RGPD. No la sustituye.

---

## 3. Plantilla — cláusula informativa para formulario web (1ª capa)

```
Tus datos serán tratados por [Empresa SL, NIF X, dirección, email] con la
finalidad de [gestionar tu solicitud / enviarte presupuesto / suscribirte
a newsletter]. La base legal es [tu consentimiento / la ejecución de
contrato / nuestro interés legítimo].

No cedemos tus datos a terceros [salvo proveedor de email Mailchimp,
EE.UU., con CCT].

Conservamos tus datos durante [X] o hasta que solicites supresión.

Puedes ejercer tus derechos de acceso, rectificación, supresión, oposición,
limitación y portabilidad escribiendo a privacidad@empresa.com.
También puedes reclamar ante la AEPD (www.aepd.es).

Más info: [link política de privacidad completa]

[ ] He leído y acepto la política de privacidad
[ ] Acepto recibir comunicaciones comerciales (opcional)
```

**Reglas que NO podés saltar**:
- Casillas sin premarcar
- Aceptación granular (privacidad ≠ marketing)
- Link real a la 2ª capa, no a "/legal" inexistente

---

## 4. Estructura mínima de la política de privacidad (2ª capa)

```
1. ¿Quién es el responsable del tratamiento?
2. ¿Qué datos recogemos y cómo?
3. ¿Para qué los usamos? (finalidades + bases legales, una por una)
4. ¿Cuánto tiempo los conservamos?
5. ¿Con quién los compartimos? (encargados, cesionarios, transferencias)
6. ¿Qué derechos tienes y cómo ejercerlos?
7. ¿Tomamos decisiones automatizadas? (Art. 22 si aplica + AI Act si aplica)
8. Cookies (link a política específica)
9. Cambios en esta política
10. Contacto y reclamación AEPD
```

> **Tip consultor**: trabajá con tres plantillas reutilizables (e-commerce, servicios B2B, healthcare) y adaptá. No las pidas a un abogado por 1500€ cuando la AEPD publica plantillas y guías oficiales.

---

## 5. Plantilla — aviso "estás hablando con un chatbot IA"

### Versión mínima (al iniciar conversación)
> Hola. Soy un asistente virtual basado en inteligencia artificial. Puedo resolver dudas sobre [productos/pedidos/citas]. Si necesitás hablar con una persona, escribí "agente humano" en cualquier momento. Más información sobre el tratamiento de tus datos: [link].

### Elementos imprescindibles
1. **Identificación clara como IA** (no "soy Lucía, tu asistente" si Lucía no existe)
2. **Alcance**: qué puede y qué no
3. **Vía de escalado humano**
4. **Link a info de privacidad**
5. Si genera contenido (resúmenes, propuestas) que se va a usar externamente, marcado de "generado por IA"

---

## 6. Caso PYME — clínica veterinaria con IA recomendadora

**Situación**: "VetSur" instala un sistema IA que, a partir de síntomas introducidos por el veterinario, sugiere posibles diagnósticos y opciones de tratamiento. La clínica quiere mostrar al dueño de la mascota un informe con esas sugerencias.

### ¿Hay datos personales?
Sí: los del dueño (cliente). Los datos de la mascota no son personales en sí, pero los del propietario (nombre, contacto, historial de visitas, pagos) sí lo son. La trazabilidad del informe se vincula al titular.

### ¿Qué tiene que decir VetSur?

**A nivel RGPD (al captar al cliente)**:
- Quién trata los datos
- Para qué (incluido: "elaboramos un informe asistido por IA con sugerencias diagnósticas para uso del veterinario")
- Base legal: ejecución de contrato (servicio veterinario) + interés legítimo (mejora del servicio)
- Plazos, derechos, reclamación

**A nivel AI Act (cuando entrega el informe)**:
- Marcar visiblemente: *"Este informe contiene sugerencias generadas por un sistema de inteligencia artificial. La decisión clínica final la toma el veterinario colegiado."*
- Si se usan imágenes generadas o reconstrucciones, marcado adicional.

**Buenas prácticas adicionales**:
- Explicar en la conversación que la IA es **apoyo al diagnóstico**, no diagnóstico
- Permitir al cliente pedir un informe sin componente IA
- Documentar quién (veterinario) revisó cada informe — esto es supervisión humana del módulo 07

### Texto literal que el consultor entrega a VetSur

Pie del informe:
> Este informe ha sido elaborado con el apoyo de un sistema de inteligencia artificial (modelo: [nombre]). Las sugerencias diagnósticas y terapéuticas han sido revisadas y validadas por [Dr/a. X, colegiado/a nº Y], que asume la responsabilidad clínica de las recomendaciones. La IA es una herramienta de apoyo y no sustituye el juicio profesional veterinario.

Aviso en formulario de admisión:
> En su atención podemos utilizar herramientas de inteligencia artificial como apoyo al diagnóstico. La decisión clínica final corresponde siempre al veterinario. Puede solicitar atención sin componente IA en cualquier momento.

---

## 7. Errores típicos PYME

| Error | Cómo se corrige |
|-------|-----------------|
| Política de privacidad copiada de otra empresa | Adaptar a finalidades y bases reales |
| "Mejorar tu experiencia" como finalidad única | Desglosar finalidades reales |
| Casilla premarcada de "acepto" | Quitarla — invalida el consentimiento |
| Chatbot que se hace pasar por humano | Aviso explícito al inicio |
| Imagen generada con IA en redes sin marcar | Etiquetado visible |
| No mencionar a la AEPD en la política | Añadir derecho de reclamación |
| Contrato encargado de tratamiento que no aparece en la política | Listar encargados principales |

> **Lección**: transparencia es **lo más barato de cumplir y lo más visible de incumplir**. Una denuncia de AEPD muchas veces empieza porque el reclamante leyó la política y no la entendió.
