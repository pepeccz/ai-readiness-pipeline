# 10. Rol del consultor IA vs. abogado: dónde termina tu trabajo

> **TL;DR**: Sos consultor técnico-organizativo, no asesor jurídico. Esa frontera no es un detalle burocrático: es la diferencia entre cobrar bien y enfrentar una denuncia por intrusismo profesional (Art. 403 CP). Bien posicionada, esa limitación se convierte en tu mejor argumento comercial.

---

## 1. Qué SÍ podés hacer (sin colegiación de abogado)

Todo lo que es **diagnóstico, diseño técnico-organizativo y acompañamiento operativo** está dentro de tu rol. Nada de esto requiere ser abogado:

| Actividad | Alcance del consultor |
|-----------|----------------------|
| Redactar **borradores** de DPIA (Evaluación de Impacto) | Sí, usando plantilla AEPD adaptada |
| Capacitación interna a equipos PYME en RGPD/AI Act | Sí, formación práctica no vinculante |
| Identificar riesgos de tratamiento y proponer medidas | Sí, es tu core |
| Proponer medidas técnicas y organizativas (Art. 32 RGPD) | Sí, cifrado, control de acceso, logging, retención |
| Acompañar implementación (configurar herramientas, flujos) | Sí |
| Recoger y organizar evidencia de cumplimiento | Sí, registros, capturas, logs, actas |
| Redactar **borradores** de política de privacidad / aviso legal **bajo plantilla** | Sí, siempre que el cliente o su abogado validen |
| Gestionar procedimientos ARCO operativos (recibir, tramitar, responder) | Sí, el flujo operativo es tuyo |
| Mapear bases jurídicas con el cliente | Sí, ayudás a documentar la decisión, **no la tomás vos** |
| Auditoría técnica de proveedores IA (DPAs, ubicación servidores, subencargados) | Sí |
| Clasificar sistemas IA según AI Act (riesgo inaceptable / alto / limitado / mínimo) | Sí, como diagnóstico técnico |

**Regla mental**: si la tarea termina en un **documento, configuración o procedimiento**, es tuya. Si termina en un **dictamen jurídico, una firma profesional o representación**, no.

---

## 2. Qué NO podés hacer

Esto es lo que se considera ejercicio de la abogacía y requiere colegiación:

- **Dictamen jurídico vinculante**: "te confirmo que cumplís el RGPD" firmado por vos, sin abogado. No.
- **Firmar como asesor legal**: poner tu sello/firma en documento que el cliente presentará como defensa legal.
- **Representación ante AEPD**: contestar requerimientos formales en nombre del cliente como si fueras su letrado.
- **Defensa en procedimiento sancionador**: alegaciones, recursos, negociación de sanciones.
- **Litigio**: cualquier cosa que vaya a tribunales.
- **Asesoramiento legal en contratos comerciales** (B2B con cláusulas RGPD complejas, transferencias internacionales con SCCs negociadas).

> [!WARNING] **Intrusismo profesional — Art. 403 Código Penal**
> Ejercer actos propios de profesión que requiere titulación oficial sin tenerla puede ser delito. Pena: multa o prisión. Además: responsabilidad civil por mal asesoramiento + queja ante el Colegio de Abogados. No es teórico, hay sentencias.

---

## 3. Cláusulas contractuales OBLIGATORIAS en tu propuesta

Tu contrato de servicios DEBE incluir, mínimo:

```
1. NATURALEZA DEL SERVICIO
   El presente servicio constituye consultoría técnico-organizativa
   en materia de protección de datos e inteligencia artificial.
   NO constituye asesoramiento jurídico ni dictamen legal.
   La validación jurídica final de los documentos, políticas y
   decisiones corresponde al CLIENTE, a su Delegado de Protección
   de Datos (DPO) o a su asesor jurídico colegiado.

2. RESPONSABILIDAD DEL TRATAMIENTO
   El CLIENTE mantiene en todo momento la condición de Responsable
   del Tratamiento conforme al Art. 4.7 RGPD. Esta responsabilidad
   no se transfiere ni se comparte con el CONSULTOR.

3. LIMITACIÓN DE RESPONSABILIDAD
   La responsabilidad del CONSULTOR se limita al [importe del
   contrato / X veces los honorarios] y no cubre sanciones
   administrativas impuestas al CLIENTE por la AEPD u otros
   organismos.

4. DESLINDE DE VALIDACIÓN FINAL
   Los entregables (DPIA, RAT, políticas, cláusulas) son borradores
   técnicos que requieren validación del CLIENTE antes de su
   publicación o uso oficial.
```

Sin estas cláusulas, estás abierto a que un cliente sancionado por la AEPD intente trasladarte la culpa.

---

## 4. Modelo de responsabilidad: el responsable sigue siendo el cliente

Esto es **fundamental** y muchos consultores lo explican mal:

- **Responsable del tratamiento** (Art. 4.7 RGPD) = el cliente. Es quien decide los fines y medios. Esto NO se delega.
- **Encargado del tratamiento** (Art. 4.8) = quien trata datos por cuenta del responsable (ej: tu hosting, tu CRM SaaS).
- **Tú como consultor** = ni una cosa ni la otra. Sos un proveedor de servicios profesionales que **no trata datos personales del cliente final** (salvo que accedas a ellos durante el proyecto, ahí sí firmás un encargo).

> [!NOTE] Cuando entrás a auditar y vés datos reales (CRM, base clientes), **firmá un acuerdo de encargado del tratamiento (DPA)** específico para esa fase. Mientras solo asesores sin tocar datos, no hace falta.

---

## 5. Cuándo derivar a abogado especializado (sí o sí)

| Escenario | Por qué derivar |
|-----------|-----------------|
| **Sectores muy regulados**: salud, banca/finanzas, infraestructuras críticas, defensa | Normativa sectorial específica (LOPDGDD secreto sanitario, PSD2, NIS2). Excede consultoría general. |
| **AI Act categoría "alto riesgo"** (Anexo III) | Conformidad CE, marcado, registro UE, evaluación por organismo notificado. Necesita validación legal robusta. |
| **Sospecha de brecha grave** o notificación a AEPD en 72h | Implicaciones sancionadoras inmediatas. Aquí tu rol es operativo (contención técnica), pero la comunicación oficial la lleva el abogado. |
| **Sanción AEPD activa** o procedimiento abierto | Defensa = abogado. Vos podés aportar evidencia técnica como perito. |
| **Litigio pendiente** (laboral, civil, mercantil con componente de datos) | Siempre abogado. |
| **Decisión automatizada con efecto jurídico significativo** (Art. 22 RGPD): scoring crediticio, selección de personal automatizada, etc. | Riesgo alto + AI Act. Validación jurídica imprescindible. |
| **Transferencias internacionales complejas** con SCCs negociadas, BCRs, evaluaciones de impacto de transferencia (TIA) | Requiere análisis jurídico de jurisdicciones. |

---

## 6. Cómo posicionarte comercialmente: convertir el límite en valor

Mal posicionado: *"yo no soy abogado, eh, ojo"* → suena a debilidad.

Bien posicionado:

> **"Soy consultor técnico-organizativo en IA y cumplimiento. Diseño, implemento y documento. Para la validación jurídica final coordino con nuestro partner legal especializado en protección de datos. Así tu PYME tiene a la vez profundidad técnica e IA, y respaldo jurídico, sin pagar dos veces por lo mismo."**

Esto:
- Te diferencia del abogado generalista que de IA no sabe.
- Te diferencia del consultor IT que de RGPD no sabe.
- Le da al cliente la sensación (correcta) de equipo completo.

---

## 7. Modelo de partnership con abogado

Tres modelos, elegí uno:

1. **Derivación pura**: pasás el cliente al abogado para temas legales, cobrás comisión por derivación (típico 10-20%).
2. **Revenue share por proyecto**: el abogado factura al cliente por validación legal, te pasa un porcentaje. O al revés.
3. **Paquete conjunto**: facturás vos el total, subcontratás al abogado como tu proveedor para la parte legal. Más control pero asumís más riesgo de cobro.

> [!TIP] Buscá abogado **especializado en protección de datos y derecho digital**, no generalista. Que conozca AEPD, EDPB, AI Act. Idealmente con perfil técnico (entiende cifrado, logs, IA). Hay pocos, valen oro.

---

## 8. Frase entrenada para sesión con cliente

Memorizala. Usala cuando el cliente te pida algo que cruza la línea:

> **"Yo te ayudo a estructurar y redactar. Tu DPO o asesor jurídico valida y firma. Así tenés profundidad técnica de mi parte y respaldo legal de la suya."**

Variaciones:

- *"Esto te lo dejo redactado para que tu abogado lo revise antes de publicarlo."*
- *"Operativamente lo resolvemos así. La interpretación legal del artículo X que la confirme tu DPO."*
- *"Si esto va a defensa ante la AEPD, es tu abogado quien lleva la voz. Yo aporto la evidencia técnica."*

---

## 9. Checklist mental antes de aceptar cualquier encargo

- [ ] ¿Lo que me piden termina en dictamen, firma legal o representación? → Derivar.
- [ ] ¿Lo que me piden termina en documento técnico, configuración, formación o procedimiento? → Tomar.
- [ ] ¿El cliente está en sector altamente regulado o tiene sanción activa? → Coordinar con abogado desde el inicio.
- [ ] ¿Tengo cláusulas de deslinde en mi contrato? → Imprescindible.
- [ ] ¿Voy a tocar datos personales reales? → Firmar DPA específico.

---

**Siguiente paso operativo**: revisar el archivo `11-checklists-operativas.md` con las checklists que usás en cliente.
