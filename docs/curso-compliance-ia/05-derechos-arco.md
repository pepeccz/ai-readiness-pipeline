# 05 — Derechos del interesado (ARCO+)

> **Idea fuerza**: cuando una persona ejerce un derecho RGPD, el reloj empieza a correr. Tu cliente PYME tiene **un mes** para responder bien o quedar expuesto a una denuncia ante la AEPD. Tu trabajo como consultor es montar el procedimiento ANTES de que llegue la primera solicitud — no después.

El RGPD (arts. 15 a 22) reconoce siete derechos al interesado. La sigla histórica "ARCO" (Acceso, Rectificación, Cancelación, Oposición) se quedó corta. Hoy hablamos de **ARCO+** o, más correctamente, derechos del Capítulo III del RGPD.

---

## 1. Los siete derechos, uno a uno

### Acceso (Art. 15)
El interesado puede pedir **qué datos suyos tratás, para qué, con quién los compartís y cuánto tiempo los conservás**. Debés entregar copia gratuita (la primera; las siguientes podés cobrar coste razonable).

**Trampa típica PYME**: entregar un volcado crudo del CRM. NO. Hay que entregar información comprensible, no un CSV de 4000 columnas.

### Rectificación (Art. 16)
Corregir datos inexactos o completar incompletos. Suele ser el más fácil. Documentá igual.

### Supresión / "derecho al olvido" (Art. 17)
Borrar los datos cuando: ya no son necesarios, retira consentimiento, se opone con éxito, tratamiento ilícito, obligación legal de borrar.

**No es absoluto**: si tenés obligación legal de conservar (ej. facturas 4 años AEAT, 6 años Código de Comercio), no borrás — bloqueás.

### Oposición (Art. 21)
El interesado se opone al tratamiento. Si la base es interés legítimo o misión pública, debés parar salvo que demuestres motivos imperiosos. **Marketing directo: oposición absoluta, sin discusión.**

### Limitación (Art. 18)
"No borres, pero no uses". Cuando se discute exactitud o licitud. Marcás los datos como bloqueados.

### Portabilidad (Art. 20)
Entregar los datos en formato **estructurado, de uso común y lectura mecánica** (JSON, CSV, XML). Aplica solo cuando la base es consentimiento o contrato Y el tratamiento es automatizado.

### No ser objeto de decisión automatizada (Art. 22)
Lo vemos en detalle en el módulo 06.

---

## 2. Plazos — el reloj que mata

| Hito | Plazo |
|------|-------|
| Acuse de recibo | Buena práctica: 48-72h |
| Respuesta completa | **1 mes desde recepción** |
| Prórroga (complejidad o volumen) | +2 meses, **comunicando al interesado en el primer mes** y motivando |
| Si no actuás | El interesado puede reclamar ante la AEPD en 1 mes |

> **Callout consultor**: la prórroga NO es automática. Hay que notificarla expresamente y justificarla. "Estamos liados" no es justificación.

---

## 3. Procedimiento operativo PYME

Montá esto en cualquier cliente, da igual el tamaño:

### Canal de entrada
- Email dedicado: `privacidad@empresa.com` o `dpo@empresa.com`
- Formulario web en la política de privacidad
- Postal, presencial — aceptarlo si llega así

**Importante**: no podés exigir un canal único. Si llega por WhatsApp del comercial, vale igual. Lo que sí podés es **redirigir** al canal formal y documentarlo.

### Identificación del solicitante
La AEPD lo dice claro: **identificación razonable, no excesiva**. NO pidas DNI escaneado por defecto. Sí podés pedirlo si hay duda razonable de la identidad.

| Situación | Identificación adecuada |
|-----------|-------------------------|
| Cliente con cuenta activa | Email registrado + verificación login |
| Lead sin cuenta | Email + un dato de contraste |
| Duda real de suplantación | Entonces sí, DNI/equivalente |

### Respuesta y documentación
1. Registrar entrada (fecha, canal, solicitante, derecho ejercido)
2. Buscar datos en TODOS los sistemas (CRM, ERP, mailing, backups, hojas Excel del comercial)
3. Ejecutar la acción (entregar, rectificar, borrar...)
4. Responder por escrito con lo realizado
5. Archivar todo el expediente **mínimo 3 años** (prueba ante reclamación)

---

## 4. Plantillas base reutilizables

### Acuse de recibo
> Hemos recibido su solicitud de ejercicio del derecho de [acceso/supresión/...] el [fecha]. Conforme al art. [X] del RGPD, le responderemos en el plazo máximo de un mes. Si necesitamos prorrogar el plazo se lo comunicaremos antes de su vencimiento.

### Respuesta acceso
> En cumplimiento de su solicitud, le facilitamos la información de los datos personales que tratamos sobre usted: [tabla categorías]. Las finalidades son [...]. Los destinatarios son [...]. El plazo de conservación es [...]. Puede ejercer adicionalmente los derechos de [...].

### Respuesta supresión
> Hemos procedido a la supresión de sus datos personales en nuestros sistemas con fecha [X]. Le informamos que conservamos bloqueados los siguientes datos por obligación legal: [facturación, 4-6 años]. Estos datos solo se utilizarán para atender requerimientos de Hacienda o tribunales.

### Respuesta oposición a marketing
> Confirmamos la baja de sus datos en nuestras comunicaciones comerciales con efecto inmediato. Mantenemos su email en una lista de exclusión técnica para garantizar que no vuelva a recibir comunicaciones.

---

## 5. Errores típicos PYME

| Error | Consecuencia | Cómo evitarlo |
|-------|--------------|---------------|
| Ignorar la solicitud | Reclamación AEPD, sanción casi segura | Procedimiento documentado + responsable nombrado |
| Pedir DNI por defecto | Tratamiento excesivo, infracción autónoma | Identificación proporcional |
| Borrar también facturación | Incumplimiento mercantil/fiscal | Distinguir borrado vs bloqueo |
| No buscar en backups ni Excel del comercial | Supresión incompleta | Mapa de datos previo |
| Responder sin documentar | Sin prueba ante reclamación | Expediente por solicitud |

---

## 6. Caso real — supresión en e-commerce con CRM + ERP + Mailchimp

**Situación**: cliente "Laura" envía email pidiendo supresión total a una PYME e-commerce de cosmética. Sus datos están en:
- **Prestashop** (cuenta y pedidos)
- **HubSpot** (CRM, lead scoring, histórico interacciones)
- **Holded** (ERP, facturas emitidas)
- **Mailchimp** (suscripción newsletter)
- **Backup mensual** en NAS

### Qué hacés como consultor IA

**Día 0 — recepción**: acuse de recibo en 24h. Identificación con email de cuenta + login confirmado.

**Día 1-3 — análisis legal**:
- Cuenta y datos marketing → **suprimir**
- Histórico HubSpot → **suprimir** (no hay base legal residual)
- Facturas en Holded → **bloquear**, no borrar (Art. 30 Cº Comercio: 6 años; LGT: 4 años)
- Mailchimp → **suprimir** + añadir a lista de exclusión (hash del email) para no volver a importarla
- Backups → política: o se purgan en próximo ciclo o se documenta la imposibilidad técnica con plazo de rotación

**Día 4-10 — ejecución**:
1. Borrado en Prestashop, HubSpot, Mailchimp
2. Marcado de "datos bloqueados — solo conservación legal" en Holded
3. Lista exclusión técnica
4. Documentación de cada acción con captura/log

**Día 11-15 — respuesta**:
- Email a Laura confirmando supresión, listando qué se conserva bloqueado y por qué (con referencia legal), y recordando derechos.

**Día 30 — archivo**: expediente cerrado en carpeta "Solicitudes RGPD 2026/", referenciado en el Registro de Actividades.

> **Lección**: sin **mapa de datos** previo, este ejercicio es imposible en plazo. La fase de inventario del módulo 03 no es burocracia — es lo que te salva el mes.
