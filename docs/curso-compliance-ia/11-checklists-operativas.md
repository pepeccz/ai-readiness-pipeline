# 11. Checklists operativas

> Checklists imprimibles para usar en sesión con cliente. Cada bloque es independiente: arrancás por el que aplique al caso.

---

## A. ¿La PYME necesita DPIA? (Art. 35 RGPD + Lista AEPD)

Respondé sí/no. **Con una sola "sí" en bloque 1, DPIA obligatoria.**

### Bloque 1 — Disparadores automáticos
- [ ] ¿Hay **decisiones automatizadas con efecto jurídico significativo** sobre personas? (scoring, selección, denegación)
- [ ] ¿Se tratan **datos sensibles a gran escala**? (salud, biométricos, ideología, orientación sexual, datos penales)
- [ ] ¿Hay **observación sistemática de zona pública**? (videovigilancia masiva, tracking)
- [ ] ¿Se tratan datos de **menores** con fines comerciales o de perfilado?
- [ ] ¿Hay **cruce o combinación de datasets** de distintas fuentes?
- [ ] ¿Se usan **tecnologías innovadoras** sin precedente claro? (IA generativa con datos personales, biometría, IoT masivo)
- [ ] ¿Hay **transferencias internacionales** fuera del EEE sin decisión de adecuación?
- [ ] ¿El tratamiento puede **impedir el ejercicio de derechos** o el acceso a servicios?

### Bloque 2 — Disparadores por combinación
Dos o más "sí" → DPIA recomendada (y normalmente obligatoria por criterio AEPD):
- [ ] Tratamiento a **gran escala**
- [ ] **Perfilado** o evaluación de aspectos personales
- [ ] **Datos de categoría especial** aunque no sea a gran escala
- [ ] **Geolocalización** continua
- [ ] **Comunicaciones electrónicas** (contenido o metadatos)

> [!NOTE] Si el cliente usa una IA generativa pública (ChatGPT, Gemini) con datos de clientes, casi seguro entra por "tecnología innovadora". DPIA.

---

## B. Categoría AI Act del sistema

Algoritmo paso a paso. Parar en la primera respuesta afirmativa.

### Paso 1 — ¿Es PROHIBIDO? (Art. 5)
- [ ] ¿Hace **scoring social** estilo crédito ciudadano?
- [ ] ¿**Manipula subliminalmente** el comportamiento causando daño?
- [ ] ¿**Explota vulnerabilidades** de menores, discapacidad, situación económica?
- [ ] ¿**Reconocimiento facial en tiempo real en espacios públicos** por fuerzas de seguridad sin excepción?
- [ ] ¿**Inferencia de emociones** en trabajo o educación?
- [ ] ¿**Categorización biométrica** por raza, religión, orientación?
- [ ] ¿**Scraping masivo de caras** para construir bases biométricas?

→ Si UNA es sí: **PROHIBIDO**. Parar el proyecto.

### Paso 2 — ¿Es ALTO RIESGO? (Anexo III)
- [ ] Biometría / identificación remota
- [ ] Infraestructuras críticas (agua, energía, transporte)
- [ ] Educación: admisión, evaluación, detección fraude exámenes
- [ ] Empleo: selección, evaluación, asignación de tareas, monitorización
- [ ] Acceso a servicios esenciales: crédito, scoring, prestaciones, emergencias
- [ ] Fuerzas del orden, migración, justicia
- [ ] Procesos democráticos

→ Si una es sí: **ALTO RIESGO**. Conformidad CE + registro UE + DPO + supervisión humana significativa + documentación técnica. **Derivar a abogado.**

### Paso 3 — ¿RIESGO LIMITADO?
- [ ] ¿Es chatbot que interactúa con personas?
- [ ] ¿Genera contenido sintético (deepfakes, imágenes, texto)?
- [ ] ¿Detecta emociones (fuera de escenarios prohibidos)?
- [ ] ¿Categoriza biométricamente (fuera de escenarios prohibidos)?

→ **Obligación de transparencia**: avisar al usuario que interactúa con IA / contenido es sintético.

### Paso 4 — Resto: RIESGO MÍNIMO
Buenas prácticas voluntarias. Recomendar políticas internas de uso.

---

## C. Documentación mínima ANTES de arrancar IA

Antes de meter ningún sistema IA, el cliente tiene que tener esto. Si no, primero ordenamos esto:

- [ ] **Registro de Actividades de Tratamiento (RAT)** actualizado — Art. 30 RGPD
- [ ] **Bases jurídicas** documentadas para cada tratamiento — Art. 6
- [ ] **Procedimiento ARCO** operativo (acceso, rectificación, supresión, oposición, portabilidad, limitación) con plazo y responsable
- [ ] **Contratos de encargado (DPA)** firmados con todos los proveedores que tocan datos (hosting, CRM, email marketing, IA)
- [ ] **Aviso legal y política de privacidad** publicados, actualizados, fechados
- [ ] **Cláusula informativa** en formularios de captura — Art. 13
- [ ] **Política de cookies** con consentimiento granular si aplica
- [ ] **Procedimiento de respuesta a brechas** (quién, qué, en cuánto tiempo, a quién notifica) — 72h AEPD
- [ ] **Inventario de tratamientos y sistemas** (no solo el RAT formal: el mapa real)
- [ ] **Política de retención y borrado** documentada por tipo de dato
- [ ] **Formación básica RGPD** del personal (al menos la última ronda con registro de asistencia)

> [!WARNING] Si falta el RAT, no arranques con IA. Es como construir un piso sin saber qué hay en los cimientos.

---

## D. Por sector regulado

### Salud
- [ ] **Secreto sanitario** (Ley 41/2002 autonomía paciente)
- [ ] Datos de salud = categoría especial Art. 9 RGPD
- [ ] Base jurídica: **consentimiento explícito** o asistencia sanitaria con profesional sujeto a secreto
- [ ] Historia clínica electrónica con trazabilidad de accesos
- [ ] Cifrado en reposo y tránsito
- [ ] DPO **obligatorio** en centros sanitarios
- [ ] Derivar a abogado especializado en derecho sanitario para validar

### Legal (despachos, asesorías)
- [ ] **Secreto profesional del abogado** (LOPJ + Estatuto General de la Abogacía)
- [ ] Base jurídica: ejecución de contrato + obligación legal
- [ ] No subir documentación de cliente a IA pública sin DPA + análisis específico
- [ ] **Deber de confidencialidad** prevalece sobre conveniencia operativa

### Finanzas / Banca
- [ ] **Secreto bancario** + normativa Banco de España
- [ ] **PSD2** para servicios de pago
- [ ] **Prevención blanqueo (PBC/FT)** — Ley 10/2010
- [ ] AI Act: scoring crediticio = ALTO RIESGO
- [ ] Derivar a abogado especializado financiero

### Educación
- [ ] LOPDGDD Art. 92 (centros educativos)
- [ ] Datos de menores: consentimiento parental < 14 años
- [ ] Imágenes y vídeos: consentimiento específico
- [ ] AI Act: evaluación automatizada de alumnos = ALTO RIESGO

---

## E. Pre-piloto IA (gate antes de pasar a producción)

Checklist firmable cliente + consultor antes de activar piloto:

- [ ] **DPIA** completada y firmada por responsable
- [ ] **Base jurídica** del tratamiento documentada
- [ ] **Información a interesados** actualizada (avisa que se usa IA)
- [ ] **Supervisión humana** definida: quién revisa, cuándo, con qué criterio
- [ ] **Registro / logging** del sistema activo (entradas, salidas, decisiones, usuario)
- [ ] **Transparencia**: el usuario final sabe que interactúa con IA si aplica (AI Act)
- [ ] **Plan de respuesta a incidente**: alucinación grave, sesgo detectado, brecha
- [ ] **DPA** firmado con proveedor IA (OpenAI, Anthropic, Google, etc.)
- [ ] **Ubicación de datos** verificada (UE / EEUU / otros) y mecanismo de transferencia
- [ ] **Política de uso** comunicada al equipo (qué se puede y qué no se puede meter en el prompt)
- [ ] **Métricas** definidas: precisión, sesgo, tasa de intervención humana
- [ ] **Cláusula de salida**: cómo se apaga el sistema si falla, quién decide
- [ ] **Formación** del equipo que va a operar la IA
- [ ] **Revisión a 30/60/90 días** agendada en calendario

> [!TIP] Si el cliente quiere saltarse alguno, firma escrita con asunción de riesgo. No te juegues tu responsabilidad por su prisa.
