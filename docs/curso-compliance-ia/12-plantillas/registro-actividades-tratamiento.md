# Plantilla — Registro de Actividades de Tratamiento (RAT)

> Art. 30 RGPD. Obligatorio para responsables y encargados (excepciones muy limitadas para <250 empleados que no traten sensibles ni a gran escala — en la práctica, casi todos lo necesitan). El RAT es el **mapa base** de todo el cumplimiento.

---

## Cabecera

| Campo | Valor |
|-------|-------|
| Razón social | |
| NIF | |
| Domicilio | |
| Contacto | |
| DPO (si aplica) | |
| Versión RAT | |
| Última actualización | YYYY-MM-DD |
| Responsable del registro | |

---

## Ficha por tratamiento

Una ficha por cada actividad. Replicar tantas veces como tratamientos haya.

### Tratamiento #[N] — [Nombre corto]

| Campo | Valor |
|-------|-------|
| **ID interno** | T-001 |
| **Nombre** | Ej: Gestión de clientes |
| **Finalidad(es)** | Ej: alta, facturación, soporte, comunicación contractual |
| **Base jurídica** (Art. 6) | Ej: ejecución de contrato |
| **Si datos especiales** (Art. 9), excepción aplicable | N/A o consentimiento explícito / asistencia sanitaria / etc. |
| **Categorías de interesados** | Clientes, leads, empleados, candidatos, proveedores, etc. |
| **Categorías de datos** | Identificativos, contacto, económicos, salud, biométricos, etc. |
| **Origen** | Directo del interesado / fuente pública / tercero (especificar) |
| **Destinatarios** | Encargados (lista) + cesiones legales |
| **Transferencias internacionales** | No / Sí: país + mecanismo (adecuación, SCCs, BCRs) |
| **Plazo de conservación** | Ej: relación contractual + 6 años obligación fiscal |
| **Criterio de supresión** | Ej: borrado automático tras vencimiento del plazo |
| **Medidas técnicas** | Cifrado, MFA, backups, logging, control de acceso |
| **Medidas organizativas** | Política de accesos, formación, NDA, procedimiento de brecha |
| **¿Requiere DPIA?** | Sí (referenciar) / No (justificar) |
| **¿Hay decisiones automatizadas?** | Sí (descripción + supervisión humana) / No |
| **¿Hay IA?** | Sí (modelo, proveedor, finalidad) / No |
| **Sistemas y aplicaciones** | CRM X, hosting Y, email marketing Z |
| **Encargados de tratamiento** | Lista con DPA firmado y fecha |

---

## Tratamientos típicos en una PYME (mínimo)

Replicar la ficha para cada uno que aplique:

1. **Gestión de clientes** (CRM, facturación, soporte)
2. **Gestión de leads y marketing** (formularios web, newsletter, campañas)
3. **Recursos humanos — empleados** (nóminas, contratos, prevención riesgos, evaluación)
4. **Recursos humanos — candidatos** (CV, procesos selección)
5. **Gestión de proveedores** (datos de contacto, facturación)
6. **Videovigilancia** (si aplica)
7. **Control de acceso** (físico o lógico)
8. **Web y cookies**
9. **Asistencia sanitaria** (si sector salud)
10. **Sistemas IA en producción** (cada uno como tratamiento separado)

---

## Resumen de encargados (anexo al RAT)

| Encargado | Servicio | Datos a los que accede | DPA firmado | Fecha | Ubicación servidores | Subencargados autorizados |
|-----------|----------|------------------------|-------------|-------|---------------------|---------------------------|
| Google Workspace | Email + Drive | Todos los corporativos | Sí | YYYY-MM-DD | UE / EEUU (DPF) | Sí, lista pública |
| HubSpot | CRM | Clientes, leads | Sí | | | |
| Stripe | Pagos | Datos pago, identificativos | Sí | | | |
| OpenAI API | IA generativa | Inputs prompt | Sí (DPA enterprise) | | EEUU (SCCs + DPF) | Sí |
| AWS / Hetzner | Hosting | Todos | Sí | | UE | Limitado |

---

## Mantenimiento del RAT

- Revisión **mínima anual**.
- Actualización **inmediata** ante:
  - Nuevo tratamiento
  - Nuevo encargado / nuevo subencargado
  - Cambio de finalidad o base jurídica
  - Nueva transferencia internacional
  - Cambio en categorías de datos o interesados
  - Brecha de seguridad
- Versión + fecha + responsable en cada cambio.
- Disponible para AEPD si lo requiere (Art. 30.4).

> [!NOTE] El RAT no se publica externamente. Es documento interno de cumplimiento, pero debe estar listo para entregar a la AEPD.
