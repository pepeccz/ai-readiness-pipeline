# 09 — Incidentes y brechas de seguridad

> **Idea fuerza**: 72 horas. Ese es el plazo para notificar a la AEPD desde que tu cliente **conoce** la brecha. No desde que la entiende, no desde que la resuelve — desde que la conoce. El que más se equivoca aquí no es el que sufre la brecha, es el que no la notifica.

---

## 1. Qué es una brecha de seguridad de datos personales

El RGPD (Art. 4.12) la define como:

> *"Toda violación de la seguridad que ocasione la destrucción, pérdida o alteración accidental o ilícita de datos personales transmitidos, conservados o tratados de otra forma, o la comunicación o acceso no autorizados a dichos datos."*

Tres tipos clásicos (las "3 C" del WP29 / EDPB):

| Tipo | Qué afecta | Ejemplo |
|------|-----------|---------|
| **Confidencialidad** | Acceso/divulgación no autorizada | Email enviado a destinatario erróneo, exfiltración por ataque |
| **Integridad** | Alteración no autorizada | Manipulación de registros, fallo que cambia datos |
| **Disponibilidad** | Pérdida o inaccesibilidad | Ransomware, borrado accidental sin backup |

**Importante**: NO toda incidencia de seguridad es brecha. Solo si afecta **datos personales**. Un DDoS que tira la web pero no toca datos personales no es brecha (sí es incidente y conviene tratarlo).

---

## 2. El plazo de 72 horas (Art. 33)

**Cuando notificar a la AEPD**:
- Sin dilación indebida
- A más tardar **72 horas desde que el responsable tenga conocimiento**
- Si pasás de 72h → motivar el retraso

**Salvo que** sea improbable que la brecha entrañe riesgo para los derechos y libertades de las personas. Esta excepción hay que **documentarla y motivarla**, no es libre.

> **Trampa común**: "tengo 72h para investigar". NO. Tenés 72h para notificar lo que sepas, aunque sea poco. Podés ampliar la notificación después (Art. 33.4 lo permite expresamente).

---

## 3. Notificación al interesado (Art. 34)

Cuando además hay **alto riesgo** para los derechos del afectado, debés comunicárselo **a él directamente**, sin dilación.

| Indicador de alto riesgo | Por qué |
|--------------------------|---------|
| Datos especiales (salud, ideología, biometría) | Impacto severo |
| Datos financieros / suficientes para fraude | Riesgo económico inmediato |
| Credenciales (usuario+contraseña) | Reutilización en otros servicios |
| Volumen masivo | Impacto agregado |
| Categorías vulnerables (menores) | Tutela reforzada |

**Excepciones a notificar al interesado**:
- Datos cifrados con clave no comprometida
- Medidas posteriores que neutralizan el riesgo
- Esfuerzo desproporcionado (entonces, comunicación pública equivalente)

---

## 4. Procedimiento operativo — los 5 pasos

### Paso 1 — Detección
Quién detecta, cómo, a quién avisa. Canal interno claro (email seguridad@, teléfono guardia, ticket).

### Paso 2 — Contención
Aislar sistema, cambiar credenciales, desconectar red, congelar logs. Antes de investigar, contener.

### Paso 3 — Evaluación
Comité de respuesta evalúa:
- ¿Qué datos? ¿De cuántas personas?
- ¿Qué tipo de brecha (3 C)?
- ¿Hay riesgo? ¿Es alto?
- ¿Hay obligación de notificar AEPD? ¿A interesados?

### Paso 4 — Notificación
- A AEPD via Sede Electrónica (formulario "Comunicación de quiebras de seguridad")
- A interesados si aplica
- A encargados/responsables conjuntos según contrato
- A cliente si tu cliente actúa como encargado

### Paso 5 — Registro y mejora
**Toda** brecha se registra (incluso las no notificables). Análisis post-incidente, lecciones, mejora de medidas.

---

## 5. Plantilla — notificación a la AEPD

Campos obligatorios del formulario AEPD:

```
1. DATOS DEL RESPONSABLE
   - Razón social, NIF, dirección
   - DPO (si lo hay) y contacto

2. DESCRIPCIÓN DE LA BRECHA
   - Fecha y hora de ocurrencia (estimada)
   - Fecha y hora de detección
   - Origen: interno, externo, accidental, deliberado
   - Tipo: confidencialidad, integridad, disponibilidad

3. NATURALEZA DE LOS DATOS AFECTADOS
   - Categorías (identificativos, financieros, salud, etc.)
   - Volumen aproximado de afectados
   - Categorías de afectados (clientes, empleados, menores...)

4. CONSECUENCIAS PROBABLES
   - Riesgos identificados
   - Por qué se considera de alto / no alto riesgo

5. MEDIDAS ADOPTADAS
   - Contención inmediata
   - Mitigación
   - Comunicación a interesados (si aplica)

6. CONTACTO PARA AMPLIACIÓN
```

> Si no tenés todos los datos en 72h, presentá lo que tengas y marcá "comunicación parcial — se ampliará".

---

## 6. Errores típicos PYME

| Error | Por qué es peor que la brecha en sí |
|-------|------------------------------------|
| **No notificar por miedo a la sanción** | La sanción por no notificar puede ser superior a la de la brecha; la AEPD lo considera agravante |
| **Notificar tarde sin motivar** | Convierte un incidente menor en infracción autónoma |
| **No avisar a interesados cuando hay alto riesgo** | Infracción separada del Art. 34 |
| **No documentar las brechas "menores"** | Si después aparece una mayor, no podés probar diligencia |
| **No tener plan** | En medio del ataque se improvisa mal y se borran logs |
| **Encargado que no avisa al responsable** | El responsable no puede cumplir 72h si el encargado calla |
| **Comunicar a interesados de forma alarmista o vaga** | Infracción del deber de información clara |

---

## 7. Plan de respuesta para PYME sin equipo de seguridad

La realidad: la mayoría de PYMEs no tienen CISO ni SOC. El plan tiene que ser **realista y ejecutable por gente no técnica con apoyo externo**.

### Componentes mínimos

**Roles**
- **Coordinador de incidentes**: gerente o responsable cumplimiento. Toma decisiones.
- **Soporte técnico**: proveedor IT habitual (con cláusula contractual de respuesta 24h)
- **Asesor legal/RGPD**: tu cliente — vos como consultor — o externo
- **Comunicación**: gerencia para clientes y prensa si aplica

**Documento de plan (8-12 páginas, no más)**
1. Definición de incidente y de brecha
2. Canal de detección y reporte interno
3. Roles y teléfonos (actualizados trimestralmente)
4. Árbol de decisión: ¿hay brecha? ¿hay riesgo? ¿hay alto riesgo?
5. Procedimiento contención por tipo (ransomware, phishing, pérdida dispositivo, error humano)
6. Plantillas de notificación (AEPD + interesados)
7. Registro de brechas
8. Revisión post-incidente

**Simulacro anual**: media mañana, caso ficticio, cronómetro. Revela los huecos antes de que sean reales.

---

## 8. Caso PYME — ransomware en servidor con datos de clientes

**Situación**: lunes 9:00. "ConstruObras SL" (45 empleados, distribuidora de materiales). El responsable IT te llama: el servidor de archivos está cifrado, pantalla con rescate en BTC. CRM y ERP en SaaS están bien. En el servidor afectado hay: presupuestos, contratos escaneados (con DNI), nóminas, fichero clientes en Excel.

### Qué hace el consultor IA, hora a hora

**09:00 — H+0**
- Confirmar contención: servidor desconectado de red. Equipos de oficina aislados por segmentación.
- Reunión de crisis convocada: gerente, IT, vos.
- Cronómetro de 72h arranca **ahora**: tienes hasta el jueves 09:00 para notificar.

**09:30 — Evaluación inicial**
- ¿Qué datos? Identificativos + DNI + nóminas (datos económicos + categorías especiales si hay datos de salud en bajas).
- ¿Volumen? ~1200 clientes + 45 empleados.
- ¿Exfiltración o solo cifrado? IT debe revisar logs antes de pagar/restaurar.
- ¿Backups? Sí, off-site, viernes anterior. Pérdida potencial: viernes-lunes.

**11:00 — Decisiones**
- NO se paga rescate (criterio FBI/INCIBE/política empresa).
- Restauración desde backup: jueves estimado.
- Comunicación a AEPD: **alto riesgo confirmado** (DNI + datos económicos + posible exfiltración).
- Comunicación a interesados: sí, en cuanto se confirme alcance.

**Lunes tarde — Notificación inicial AEPD**
Presentás formulario con lo que sabés. Marcado "comunicación parcial". Conservás logs, escaneo forense en marcha por proveedor especializado contratado de urgencia.

**Martes — Análisis forense**
- ¿Hubo exfiltración? IDS muestra tráfico anómalo el viernes 23:00. Probable sí.
- Vector: phishing a empleado de administración + escalado privilegios por contraseña débil.

**Miércoles — Comunicación a interesados**
Email + carta certificada (clientes con DNI/datos sensibles):
> Le informamos que el [fecha] hemos sufrido un incidente de seguridad que ha podido afectar a sus datos personales. Los datos potencialmente afectados son: nombre, DNI, datos de contacto y, en su caso, datos económicos relativos a sus operaciones con nosotros. Hemos adoptado las siguientes medidas: [...]. Le recomendamos: [vigilar movimientos, no atender comunicaciones sospechosas, contactar a su banco si nota anomalías]. Para más información: [contacto]. Hemos notificado el incidente a la AEPD.

**Jueves — Ampliación AEPD**
Subís documentación adicional al expediente: alcance final, medidas correctivas, plan de mejora.

**Semana siguiente — Post-incidente**
- MFA obligatorio en todos los accesos
- Backups con regla 3-2-1 + un offline
- Formación phishing a todo el personal
- Rotación de credenciales completa
- Revisión y actualización del plan de respuesta
- Registro de la brecha en el inventario interno

> **Lección**: el cliente no te paga por evitar la brecha — eso no siempre es posible. Te paga por que cuando ocurra, el daño legal y reputacional sea **el mínimo posible**. 72 horas y un plan ensayado marcan la diferencia entre una multa simbólica y una sanción ejemplar.
