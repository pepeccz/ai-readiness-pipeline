# 15. FAQs del cliente PYME — respuestas entrenadas

> Preguntas reales que vas a oír en sesión. Respuestas concisas, accionables, sin hedging. Cuando la respuesta correcta es "deriva al abogado", se dice claro.

---

### 1. "¿Tengo que hacer DPIA si solo tengo un CRM con clientes?"

**No**, en general no. Un CRM clásico (datos identificativos, contacto, historial comercial) sin perfilado avanzado, sin sensibles, sin IA decisoria, **no dispara DPIA**. Lo que **sí necesitás**: RAT, base jurídica documentada, DPA con el proveedor del CRM, política de retención, procedimiento ARCO.

Si al CRM le metés módulo de **scoring con IA** o **perfilado avanzado**, ahí sí: DPIA.

---

### 2. "¿Si los datos están en EE.UU. en Google Workspace estoy mal?"

**No, si Google está adherido al Data Privacy Framework (DPF)** — y lo está. Desde julio 2023 el DPF UE-EEUU restablece la presunción de adecuación para empresas certificadas. Google, Microsoft, AWS están dentro.

**Lo que tenés que tener**:
- DPA firmado con Google (lo tienen estándar).
- Constatado que Google figura en la lista oficial DPF.
- Documentado en el RAT.

**Atención**: si mañana cae el DPF (como cayó Privacy Shield en 2020), volvemos a SCCs + análisis de impacto de transferencia. Es un riesgo a vigilar, no un drama hoy.

---

### 3. "¿Puedo usar ChatGPT con datos de mis clientes?"

**Con la versión gratuita o ChatGPT personal: NO.** Los inputs pueden usarse para entrenar, no hay DPA, no hay control.

**Con ChatGPT Enterprise / Team o API con DPA**: SÍ, con condiciones:
- DPA firmado con OpenAI.
- Configuración de "no entrenamiento" activada.
- DPIA si hay datos sensibles o decisión automatizada.
- Política interna de uso (qué se puede meter, qué no).
- Formación del equipo.
- Cláusula informativa actualizada si afecta a interesados.

**Regla práctica**: con cuenta personal, nunca. Con cuenta empresarial bien configurada, sí, dentro de un marco.

---

### 4. "¿Tengo que poner aviso de cookies?"

**Sí**, si usás cookies no esenciales (analítica, marketing, terceros). Requisitos:
- Banner que **bloquee** las cookies no esenciales hasta consentimiento.
- Opciones **granulares** (no "aceptar todo" como única salida).
- "Rechazar" tan visible como "Aceptar".
- Política de cookies con lista detallada.
- Posibilidad de **retirar** consentimiento fácilmente.

Cookies estrictamente necesarias (sesión, carrito): no requieren consentimiento, pero sí información.

> [!WARNING] La AEPD ha sancionado mucho por banners mal hechos. Es de los puntos que primero miran.

---

### 5. "¿Si vendo datos a otra empresa que los reutiliza qué obligaciones tengo?"

Eso ya **no es venta de datos en abstracto**, es una **cesión** que requiere:
- Base jurídica clara (normalmente consentimiento informado y específico).
- Información previa al interesado del destinatario y la finalidad.
- Si la otra empresa decide fines y medios, es **otro responsable**, no tu encargado.

Vender datos como producto es delicado. **Aquí derivá a abogado** porque las implicaciones contractuales y de bases jurídicas son específicas.

---

### 6. "¿Cuánto cuesta una sanción AEPD real?"

**Depende del nivel**:
- Infracciones leves: hasta **40.000 €**.
- Infracciones graves: hasta **300.000 €**.
- Infracciones muy graves: hasta **20 M€ o 4% facturación global**, lo mayor.

En PYMEs típicas las sanciones reales suelen ir de **2.000 € a 80.000 €**. Lo que más se sanciona: cookies mal puestas, falta de información en formularios, no atender derechos ARCO en plazo, brechas no notificadas.

> Consultá la sección **Resoluciones** de la AEPD: están publicadas, podés ver cuánto y por qué se ha sancionado a empresas similares a la del cliente.

---

### 7. "¿Necesito DPO si soy PYME de 20 empleados?"

**No automáticamente.** DPO obligatorio (Art. 37 RGPD) si:
- Sos autoridad pública.
- Tu actividad principal requiere observación sistemática a gran escala.
- Tratás datos sensibles o de condenas a gran escala.

Una PYME de 20 empleados con tratamiento normal **no necesita DPO**. Sí conviene tener un **referente interno** de protección de datos y, si se complica, **DPO externo a tiempo parcial** (cuesta poco y cubre).

Excepciones donde sí: clínicas, despachos con muchos casos sensibles, empresas de seguridad con videovigilancia masiva, etc.

---

### 8. "¿Debo formar a mi equipo en RGPD?"

**Sí, sin excepción.** No es opcional: forma parte de las medidas organizativas (Art. 32). En una inspección AEPD lo van a preguntar.

Mínimo:
- **Formación inicial** al alta de cada empleado.
- **Refresco anual** (1-2 horas).
- **Formación específica** para roles que tocan datos sensibles o IA.
- **Registro de asistencia** firmado o con log digital.

Sin esto, cualquier brecha causada por error humano se agrava como falta de medidas.

---

### 9. "¿Y si un empleado usa ChatGPT por su cuenta con datos de clientes?"

Eso es **shadow AI** y es uno de los riesgos más reales hoy. Tu cliente tiene que:

1. **Política de uso de IA** publicada y firmada por todos.
2. **Lista clara** de qué herramientas IA están autorizadas y cuáles no.
3. **Alternativa autorizada**: si prohibís ChatGPT, dales Copilot Enterprise o ChatGPT Team, porque si no, lo usarán igual.
4. **Monitorización razonable** (DLP, control de salida de información).
5. **Formación** específica.
6. Si pasa: **investigar como brecha potencial**, evaluar notificación a AEPD.

> Es delito disciplinario laboral si está bien comunicado en política. Sin política, no podés sancionar.

---

### 10. "¿Cómo demuestro que cumplo si me audita la AEPD?"

Con **evidencia documental ordenada**. Carpeta única con:
- RAT actualizado y fechado.
- DPIAs realizadas.
- DPAs con todos los proveedores.
- Política de privacidad y avisos legales versionados.
- Registros de formación.
- Procedimientos ARCO con histórico de solicitudes y respuestas.
- Registro de incidentes y brechas (notificadas o evaluadas).
- Política de cookies + capturas del banner.
- Plan de medidas de seguridad (Art. 32).

Lema: **"Si no está documentado, no existe."** El principio de **responsabilidad proactiva** (Art. 5.2) exige que **demuestres** que cumplís.

---

### 11. "¿AI Act me afecta si solo uso un chatbot de un proveedor?"

**Sí, pero como usuario (deployer)**, no como proveedor. Tus obligaciones:
- **Transparencia**: avisar al usuario que interactúa con IA.
- **Uso conforme** a las instrucciones del proveedor.
- **Supervisión humana** si el chatbot tiene impacto significativo.
- **Documentación** del sistema en el RAT.

Si el chatbot toma decisiones automatizadas con efecto (ej: deniega devolución, da scoring), las obligaciones suben.

---

### 12. "¿Qué pasa si mi proveedor IA tiene una brecha?"

El proveedor (encargado) **te tiene que notificar sin dilación indebida** (Art. 33.2). A partir de ahí:
1. Evaluar el riesgo para los interesados.
2. Si hay riesgo: **notificar a la AEPD en 72h** desde que tuviste conocimiento.
3. Si el riesgo es alto: **notificar a los interesados afectados**.
4. Documentar todo en el registro interno de brechas.

**Tu responsabilidad** sigue siendo tuya como responsable, aunque la brecha sea del encargado. Por eso el DPA es crítico: define obligaciones, plazos y responsabilidades.

---

### 13. "¿Puedo entrenar IA con datos de mis clientes?"

**Depende mucho del caso**. Tres preguntas:

1. **Base jurídica**: ¿tenés base para usar esos datos para esa finalidad nueva (entrenar IA es finalidad nueva, distinta de la original)? Probablemente necesites consentimiento específico.
2. **Minimización**: ¿podés entrenar con datos **anonimizados** o sintéticos? Si sí, es la opción correcta.
3. **DPIA**: casi seguro requerida.

**Por defecto**: no entrenes con datos personales reales sin pasar por consentimiento + DPIA. Si el cliente insiste y no hay claridad, **derivar a abogado**.

---

### 14. "¿Y si los datos son anónimos puedo hacer lo que quiera?"

**Sí, RGPD no aplica a datos verdaderamente anónimos.** El problema es que la **anonimización real es muy difícil**: si combinando con otras fuentes podés reidentificar, no es anónimo, es pseudónimo, y RGPD aplica.

Test: ¿alguien con esfuerzo razonable podría reidentificar? Si sí → datos personales. Si claramente no → anonimizado.

> En PYMEs, asumí que casi nada es realmente anónimo. Trabajá con pseudonimización + medidas técnicas, y considerá los datos como personales para todo.

---

### 15. "¿Cuánto tarda implementar todo esto?"

Para una PYME tipo (20-50 empleados, tratamientos estándar, sin sector regulado):

| Fase | Tiempo |
|------|--------|
| Diagnóstico inicial | 1-2 semanas |
| RAT + bases jurídicas | 2-3 semanas |
| DPAs con proveedores | 2-4 semanas (depende del proveedor) |
| Políticas + cláusulas | 1-2 semanas |
| Procedimientos (ARCO, brechas) | 1-2 semanas |
| Formación | 1 sesión inicial + refresco |
| **Total realista** | **2-3 meses** |

Si hay IA en producción, sumá DPIA y conformidad AI Act: **1-2 meses extra**.

---

### 16. "¿Tengo que decir a mis clientes que uso IA?"

**Sí, en varios casos**:
- Si interactuás con IA (chatbot): obligación de transparencia AI Act.
- Si hay decisión automatizada con efecto significativo: información Art. 13/22 RGPD.
- Si la IA usa datos personales con fines distintos a los originales: información de finalidad.

Cómo: añadir párrafo a la política de privacidad + aviso en el punto de interacción ("estás hablando con un asistente IA").

---

### 17. "¿Las grabaciones de las videollamadas con clientes las puedo guardar?"

**Sí, con condiciones**:
- **Información previa** al inicio de la llamada (consentimiento o base jurídica clara).
- **Finalidad específica** (no "por si acaso"): formación, calidad, prueba contractual.
- **Plazo de conservación** definido.
- **Acceso restringido** y trazado.
- En el RAT como tratamiento separado.

Si la grabación incluye datos sensibles (reuniones médicas, legales): consentimiento explícito + medidas reforzadas.

---

### 18. "¿Y si solo uso IA para escribir emails de marketing, también es AI Act?"

**AI Act sí aplica**, pero como **riesgo mínimo**: solo buenas prácticas. Lo que sí aplica fuerte es **RGPD**:
- Base jurídica del marketing (consentimiento o interés legítimo a clientes existentes).
- Si la IA personaliza con perfilado: información Art. 13.
- Si hay decisión automatizada (ej: a quién enviar / no enviar): Art. 22.

**No es alto riesgo, pero no es "campo libre".** Política interna + transparencia.
