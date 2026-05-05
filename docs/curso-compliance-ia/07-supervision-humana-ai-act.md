# 07 — Supervisión humana en el AI Act (Art. 14)

> **Idea fuerza**: el AI Act no se conforma con "que haya un humano". Exige supervisión **efectiva**: una persona formada, con tiempo, con autoridad, con procedimiento, capaz de **detener el sistema** si algo sale mal. Y todo eso documentado.

---

## 1. Qué dice el Art. 14 del AI Act

Para sistemas de **alto riesgo** (Anexo III: empleo, crédito, educación, infraestructuras críticas, aplicación de la ley, biometría, etc.), el proveedor debe diseñar el sistema de modo que personas físicas puedan supervisarlo eficazmente durante todo su ciclo de uso.

La supervisión humana debe permitir, como mínimo:

| Capacidad exigida | Qué significa en la práctica |
|-------------------|------------------------------|
| **Comprender capacidades y limitaciones** del sistema | El supervisor entiende qué hace bien y dónde falla |
| Mantenerse consciente del **automation bias** | Reconoce la tendencia a creer al modelo aunque se equivoque |
| **Interpretar correctamente el output** | Sabe leer probabilidades, scores, intervalos de confianza |
| **Decidir no usar** el resultado | Tiene autoridad para descartarlo |
| **Intervenir** en el funcionamiento o **detenerlo** | Botón de parada real, no decorativo |

Para biometría remota en tiempo real, la regla se refuerza: dos personas, formación específica.

---

## 2. Niveles de supervisión — los tres "human in/on/out"

Esta taxonomía no está en el texto legal, pero es el marco operativo que vas a usar con clientes.

| Nivel | Qué significa | Cuándo aplica |
|-------|---------------|---------------|
| **Human in the loop (HITL)** | Humano valida cada decisión antes de que se ejecute | Alto riesgo con impacto inmediato e irreversible: contratación, denegación crédito, diagnóstico médico |
| **Human on the loop (HOTL)** | Sistema decide solo, humano supervisa flujo y puede intervenir | Riesgo medio o decisiones reversibles: moderación contenido, detección fraude con bloqueo temporal |
| **Human out of the loop (HOOTL)** | Sin supervisión humana directa, solo monitoreo agregado | Riesgo limitado/mínimo: recomendadores, traductores, autocompletado |

Para alto riesgo AI Act, **HITL o HOTL fuerte** son las opciones. HOOTL no cumple Art. 14.

> **Confusión típica del cliente**: "tenemos un humano que mira las alertas semanales". Eso no es supervisión, es reporting. Supervisión = capacidad de intervenir en tiempo útil.

---

## 3. Diseño organizacional — montando supervisión en una PYME

### ¿Quién supervisa?
- **Perfil**: persona del dominio (no del IT). Si el sistema filtra CVs, supervisor de RRHH. Si scoring de crédito, analista financiero.
- **Formación obligatoria**: capacidades y limitaciones del modelo, métricas de sesgo, casos de fallo conocidos, procedimiento de escalado. Mínimo formación inicial + reciclaje anual.
- **Autoridad explícita**: por escrito, puede revertir decisiones del sistema sin pedir permiso.
- **Tiempo asignado**: porcentaje claro de la jornada. Si tiene 200 decisiones/día y 5 minutos por decisión, no le da el tiempo. No es supervisión.

### Reportes y métricas
| Frecuencia | Qué se revisa |
|------------|---------------|
| Diaria/operativa | Alertas, decisiones pendientes, anomalías inmediatas |
| Semanal | Tasa de override, falsos positivos/negativos, drift |
| Mensual | KPIs de calidad, sesgos por grupo demográfico |
| Trimestral | Revisión por dirección, decisiones de mejora o pausa |

### Procedimiento de escalado
Documentado, con tres niveles típicos:

1. **Anomalía menor** → supervisor registra, ajusta, sigue
2. **Anomalía repetida o significativa** → escala a responsable de cumplimiento + proveedor IA
3. **Fallo grave o riesgo inmediato** → **detención del sistema**, notificación interna y, si aplica, autoridad competente

---

## 4. Documentar la supervisión — parte del expediente técnico AI Act

El Anexo IV del AI Act exige documentación técnica para sistemas alto riesgo. La supervisión humana es una sección obligatoria. Debe contener:

- **Diseño**: cómo está construida la supervisión en el sistema (UI, alertas, botón de parada, logs)
- **Asignación**: quién supervisa, su rol, su formación
- **Procedimiento**: cómo se interviene paso a paso
- **Métricas**: qué se mide, con qué umbrales
- **Plan de escalado**: niveles y responsables
- **Registros**: cómo se evidencia que la supervisión ocurrió

> **Tip consultor**: trabajá con un único documento "Procedimiento de Supervisión Humana del Sistema X" que sirva tanto para AI Act como para AEPD si hay Art. 22 de por medio. Mismo procedimiento, doble cumplimiento.

---

## 5. Errores típicos en PYMEs

| Error | Por qué falla |
|-------|---------------|
| **Nombrar supervisor sin formación** | No comprende limitaciones → automation bias garantizado |
| **1 persona supervisa 10 sistemas distintos** | Imposible mantener competencia real |
| **Supervisor sin autoridad** ("solo puedo recomendar") | No es supervisión, es opinión |
| **Sin procedimiento ante anomalía** | Cuando pasa, nadie sabe qué hacer |
| **Botón de parada decorativo** | El sistema no tiene mecanismo real de detención, o requiere autorización IT que tarda 3 días |
| **Métricas sin umbrales** | Dashboards bonitos sin acción asociada |
| **Confundir auditoría con supervisión** | Auditar pasa cada 6 meses; supervisión es continua |
| **Supervisor que es el mismo que vendió la herramienta** | Conflicto de interés evidente |

---

## 6. Caso PYME — clínica con IA de triaje

**Situación**: "VetCare", red de 4 clínicas veterinarias, integra una herramienta IA que sugiere prioridad de atención al recibir una llamada de urgencia (verde/ámbar/rojo). El staff atiende en orden de prioridad.

### ¿Es alto riesgo?
Probable: salud (aunque animal, las directrices van orientadas a humanos; aquí lo trataríamos por riesgo limitado pero buenas prácticas alto riesgo, porque hay impacto en bienestar y responsabilidad civil).

### Diseño de supervisión que propondría el consultor

**Nivel**: Human in the loop. La IA **sugiere** prioridad, una auxiliar veterinaria **confirma** antes de aplicarla.

**Formación supervisores**: 8h iniciales sobre el modelo (qué señales pesa, dónde falla — animales pequeños, razas atípicas, descripciones ambiguas), 2h trimestrales.

**Autoridad**: la auxiliar puede subir o bajar prioridad sin pedir permiso. Queda registrada.

**Procedimiento de anomalía**: si en 1h hay 3 overrides, alerta al responsable clínico. Si la IA marca rojo y la auxiliar baja a verde más de X veces en una semana → revisión del modelo con el proveedor.

**Métricas semanales**: tasa de override, tiempo medio de atención por color, casos con desenlace adverso.

**Botón de parada**: si el modelo falla (>30% override) o hay incidente grave, se desactiva la sugerencia y se opera con triaje manual hasta resolver.

**Documentación**: ficha del sistema + procedimiento supervisión + log decisiones, todo accesible y revisado por dirección cada trimestre.

> **Lección**: la supervisión humana **no es un disclaimer**. Es un sistema operativo con personas, tiempos, autoridades y métricas. Si tu cliente no puede pagar eso, no debería usar IA en ese proceso.
