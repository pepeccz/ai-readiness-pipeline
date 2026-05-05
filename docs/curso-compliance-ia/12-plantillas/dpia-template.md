# Plantilla DPIA — Evaluación de Impacto en Protección de Datos

> Adaptada de la guía AEPD "Gestión del Riesgo y Evaluación de Impacto en Tratamientos de Datos Personales". Borrador técnico — requiere validación de DPO o asesor jurídico antes de su uso oficial.

---

## 0. Identificación

| Campo | Valor |
|-------|-------|
| Nombre del tratamiento | |
| Versión DPIA | 1.0 |
| Fecha | YYYY-MM-DD |
| Responsable del tratamiento | |
| DPO (si aplica) | |
| Consultor que redacta | |
| Validación jurídica (firma) | Pendiente / Validado por [nombre + colegiado] |

---

## 1. Descripción sistemática del tratamiento

- **Finalidad(es)** del tratamiento:
- **Base jurídica** (Art. 6 RGPD): consentimiento / contrato / obligación legal / interés vital / interés público / interés legítimo
- **Categorías de interesados**:
- **Categorías de datos**: identificativos / contacto / económicos / salud / biométricos / ideología / etc.
- **Origen de los datos**: directamente del interesado / fuentes públicas / terceros
- **Destinatarios y cesiones**:
- **Encargados de tratamiento** (proveedores con acceso): incluir lista con DPA firmado
- **Transferencias internacionales**: sí/no, países, mecanismo (decisión adecuación / SCCs / BCRs)
- **Plazo de conservación** y criterio de borrado:
- **Sistemas y aplicaciones** que intervienen:
- **Si hay IA**: modelo, proveedor, ubicación, datos de entrenamiento, supervisión humana

---

## 2. Necesidad y proporcionalidad

- ¿El tratamiento es **necesario** para el fin? Justificar.
- ¿Hay **alternativas menos invasivas**? Documentar por qué se descartan.
- **Minimización**: ¿se tratan solo los datos imprescindibles?
- **Limitación de la finalidad**: ¿los datos se usan solo para lo declarado?
- **Información a interesados**: cláusula informativa publicada (referenciar)
- **Derechos ARCO**: procedimiento operativo (referenciar)
- **Consentimiento** (si aplica): cómo se recoge, cómo se prueba, cómo se revoca

---

## 3. Identificación de riesgos

Para cada riesgo: probabilidad (1-3) × impacto (1-3) = nivel.

| # | Riesgo | Origen | Probabilidad | Impacto | Nivel |
|---|--------|--------|--------------|---------|-------|
| R1 | Acceso no autorizado a base de datos | Externo / interno | | | |
| R2 | Pérdida de datos por fallo del proveedor IA | Encargado | | | |
| R3 | Reidentificación de datos pseudonimizados | Tratamiento | | | |
| R4 | Sesgo discriminatorio del modelo IA | Algoritmo | | | |
| R5 | Filtración por prompt injection | IA | | | |
| R6 | Uso secundario por proveedor IA para entrenar | Encargado | | | |
| R7 | Transferencia internacional sin garantías | Flujo | | | |
| R8 | Conservación más allá del plazo | Operación | | | |

---

## 4. Medidas para mitigar riesgos

Por cada riesgo medio/alto, definir medidas:

| Riesgo | Medida técnica | Medida organizativa | Responsable | Plazo |
|--------|----------------|---------------------|-------------|-------|
| R1 | Cifrado AES-256 reposo + TLS tránsito + MFA | Política de accesos, revisión trimestral | | |
| R2 | Backup independiente + plan de salida | Cláusula contractual de portabilidad | | |
| R5 | Filtros de entrada/salida + sandbox | Política de uso del prompt + formación | | |
| R6 | DPA con cláusula "no entrenamiento" + endpoint enterprise | Auditoría anual al proveedor | | |

Medidas mínimas siempre presentes:
- Cifrado en reposo y tránsito
- Control de acceso por roles + MFA
- Logging y monitorización
- Backups y plan de recuperación
- Política de retención
- Formación del personal
- Procedimiento de gestión de brechas (notificación AEPD 72h)

---

## 5. Riesgo residual y decisión

- **Riesgo residual** tras medidas: bajo / medio / alto
- **Decisión**: tratamiento aprobado / aprobado con condiciones / requiere consulta previa AEPD (Art. 36) / no aprobado
- **Consulta previa AEPD**: obligatoria si el riesgo residual sigue siendo ALTO

---

## 6. Revisión

- **Próxima revisión**: YYYY-MM-DD (mínimo anual o ante cambio sustancial)
- **Disparadores de revisión anticipada**: nuevo proveedor, nueva finalidad, nueva categoría de datos, brecha, cambio normativo

---

## 7. Firmas

| Rol | Nombre | Firma | Fecha |
|-----|--------|-------|-------|
| Responsable del tratamiento | | | |
| DPO | | | |
| Consultor (autor borrador) | | | |
| Asesor jurídico (validación) | | | |
