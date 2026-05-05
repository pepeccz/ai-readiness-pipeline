# 06 — Decisiones automatizadas (Art. 22 RGPD)

> **Idea fuerza**: el Art. 22 es el artículo que más se ignora y más va a doler con la IA generativa metiéndose en procesos de negocio. Si tu cliente PYME usa IA para **decidir** algo sobre una persona — contratarla, aprobarle un crédito, fijarle un precio, denegarle un servicio — tenés Art. 22 encima.

---

## 1. Qué dice exactamente el Art. 22

> *"Todo interesado tendrá derecho a no ser objeto de una decisión basada **únicamente en el tratamiento automatizado**, incluida la elaboración de perfiles, que produzca efectos jurídicos en él o le afecte significativamente de modo similar."*

Tres elementos a cumplirse simultáneamente para que aplique:

1. **Decisión basada únicamente en tratamiento automatizado** (sin intervención humana significativa)
2. **Efectos jurídicos** sobre la persona, **o**
3. **Efectos significativos** análogos a los jurídicos

Si falta uno, Art. 22 no se activa (pero seguís teniendo el resto del RGPD: información, base legítima, etc.).

---

## 2. ¿Qué es "efecto significativo"? — la pregunta del millón

La EDPB (Directrices WP251) y la AEPD lo han concretado. **Sí es significativo**:

| Caso | Por qué |
|------|---------|
| Scoring crediticio que deniega préstamo | Acceso a servicio financiero |
| Filtro automático de CVs que descarta candidato | Acceso al empleo |
| Denegación automática de seguro o cotización extrema | Acceso a servicio esencial |
| Precio dinámico personalizado muy desviado del medio | Discriminación económica |
| Asignación de turnos/horarios que afecta condiciones laborales | Impacto laboral |
| Cierre o suspensión automática de cuenta plataforma | Privación de servicio |
| Decisión sobre prestación pública | Efecto jurídico claro |

**No suele ser significativo**:
- Recomendaciones de productos ("también te puede gustar")
- Personalización de UI no determinante
- Segmentación marketing genérica que no excluye

> **Zona gris peligrosa**: precio dinámico estándar (Booking, Uber). Si la desviación es razonable y aplica a todos, no es Art. 22. Si es **personalizado en función de perfil individual** (el navegador detecta usuario premium y le sube 30%), entra en debate.

---

## 3. Excepciones — cuándo SÍ podés tomar decisiones automatizadas

El Art. 22.2 abre tres puertas:

| Excepción | Requisitos |
|-----------|-----------|
| **Necesario para celebrar/ejecutar contrato** | Que no haya alternativa menos intrusiva |
| **Autorizada por Derecho UE/Estado miembro** | Con medidas adecuadas |
| **Consentimiento explícito** | Libre, informado, granular, revocable |

En las tres, **siempre** debés ofrecer:
- Intervención humana
- Derecho a expresar punto de vista
- Derecho a impugnar la decisión

Y datos especiales (art. 9): regla más estricta — solo consentimiento explícito o interés público sustancial, **y** garantías reforzadas.

---

## 4. "Intervención humana significativa" vs "rubber-stamping"

Esta es **la** distinción crítica. La EDPB es tajante: el humano que aprueba sin revisar **no cuenta** como intervención humana. Sigue siendo decisión automatizada.

| Rubber-stamping (NO vale) | Intervención significativa (SÍ vale) |
|---------------------------|--------------------------------------|
| Humano ve "score 0.87 — denegar" y firma | Humano accede a los datos, evalúa criterios, puede contradecir el modelo |
| Sin formación ni autoridad para revertir | Formado, autorizado, con tiempo asignado |
| 500 decisiones/día por persona | Carga compatible con revisión real |
| No queda registro de la revisión | Registro de criterio aplicado |

> **Test del consultor**: si el humano solo puede hacer clic en "aprobar" o no entiende cómo funciona el modelo, **es decisión automatizada** aunque haya humano de adorno.

---

## 5. Cruce con AI Act — alto riesgo

Muchos sistemas Art. 22 son **alto riesgo** según el Anexo III del AI Act:

- Empleo (selección, evaluación, despido)
- Servicios esenciales (crédito, seguros, prestaciones públicas)
- Aplicación de la ley
- Educación (evaluación, admisión)

Cuando algo cae en ambos:
- **RGPD Art. 22**: derechos individuales (información, intervención, impugnación)
- **AI Act**: obligaciones del sistema (gestión de riesgos, datos calidad, supervisión humana art. 14, registro UE, marcado CE...)

Son acumulativos, no alternativos. Y la sanción por uno no excluye la del otro.

---

## 6. Garantías obligatorias — cómo se implementan

Cuando aplicás una excepción del Art. 22.2, montá estas garantías:

### a) Información reforzada (Arts. 13-14 + 22.3)
La política de privacidad debe decir explícitamente:
- Que existe decisión automatizada
- **Lógica aplicada** (no el código fuente, pero sí los criterios principales y peso aproximado)
- Consecuencias previstas
- Derechos disponibles

### b) Canal de intervención humana
Procedimiento documentado: cómo se solicita revisión, en qué plazo, por quién, con qué autoridad para revocar.

### c) Canal de impugnación
Distinto del anterior. La impugnación es contra la decisión final, con expresión de punto de vista del afectado.

### d) Registro de decisiones
Para cada decisión: inputs, output del modelo, revisor humano (si lo hubo), decisión final, motivación.

---

## 7. Caso PYME — empresa de selección que filtra CVs con IA

**Situación**: "TalentoPro", consultora de selección de 18 personas, integra una herramienta SaaS de cribado de CVs con IA. La herramienta puntúa CVs 0-100; los <60 se descartan automáticamente; los >60 pasan a entrevista.

### Análisis del consultor IA

**¿Aplica Art. 22?** Sí. Decisión automatizada (el descarte <60 es automático), efecto significativo (acceso al empleo).

**¿Aplica AI Act alto riesgo?** Sí, Anexo III punto 4 (empleo).

**Problemas que ves al entrar al cliente**:
1. No hay información al candidato de que se usa IA en el cribado
2. No hay revisor humano antes del descarte
3. El proveedor SaaS no entrega documentación de sesgos ni datos de entrenamiento
4. No hay procedimiento de impugnación
5. La política de privacidad no menciona la lógica aplicada

### Plan de remediación que propone el consultor

| Acción | Plazo |
|--------|-------|
| Revisar contrato con proveedor SaaS — exigir info AI Act (datasheet del modelo, métricas de sesgo, transparencia) | 2 semanas |
| **Cambiar diseño**: ningún candidato se descarta automáticamente. La IA puntúa, un reclutador formado revisa los <60 antes de descartar. Queda registro. | 1 mes |
| Política de privacidad y aviso en formulario de candidatura: "se utiliza IA en la fase inicial; tiene derecho a revisión humana e impugnación" | 2 semanas |
| Procedimiento de impugnación con plazo y responsable | 1 mes |
| EIPD (Evaluación Impacto Protección Datos) — obligatoria por perfilado masivo | 6 semanas |
| Registro de actividades actualizado | 1 semana |
| Formación a 3 reclutadores como "supervisores humanos" | 1 mes |

**Si el cliente se resiste**: explicale que la sanción RGPD por Art. 22 mal aplicado puede llegar a 20M€ o 4% facturación, y que la AEPD ya ha sancionado casos análogos. La sanción AI Act por sistema alto riesgo sin conformidad llega a 15M€ o 3% facturación. Acumulables.

> **Lección consultor**: el Art. 22 no se cumple "tachando casillas". Se cumple **rediseñando el proceso** para que el humano decida de verdad. Si no podés rediseñarlo, la decisión no debería ser automatizada.
