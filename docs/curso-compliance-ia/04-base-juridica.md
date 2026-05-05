# 04 — Base jurídica del tratamiento: cómo elegirla y documentarla

> **Objetivo del módulo**: que dejes de mirar el RGPD como una caja negra y entiendas las 6 bases del Art. 6 con criterio operativo. Que sepas elegir bien, documentar correctamente, y detectar cuándo el cliente está usando una base equivocada (que es lo más común en PYME).

Sin base jurídica, **no hay tratamiento legal**. Es la pregunta que la AEPD hace primero cuando inspecciona. Y es donde más fallos comete la PYME.

---

## 1. Las 6 bases jurídicas del Art. 6.1 RGPD

### a) Consentimiento (Art. 6.1.a)

**Cuándo aplica**: cuando ninguna otra base encaja y el titular acepta libremente.

**Requisitos** (Art. 7):
- **Libre**: sin condicionar el servicio
- **Específico**: para cada finalidad
- **Informado**: el titular sabe exactamente qué pasa con sus datos
- **Inequívoco**: acción afirmativa clara (NO casillas premarcadas, NO silencio)
- **Demostrable**: tenés que poder probar que lo dio
- **Revocable** en cualquier momento, igual de fácil que darlo

**Riesgos**: si el titular lo retira, **se acabó la base**. Tenés que parar el tratamiento (salvo otra base que aplique).

**Ejemplo PYME**: newsletter de la tienda online. Checkbox no marcado por defecto, texto claro "Quiero recibir ofertas y novedades por email". Botón unsubscribe en cada envío. Registro del consentimiento (fecha, IP, texto mostrado).

> **Anti-patrón típico**: "consentimiento" forzado para acceder al servicio. Si no se puede usar el servicio sin aceptar, **NO es libre, no es válido**.

### b) Ejecución de un contrato (Art. 6.1.b)

**Cuándo aplica**: el tratamiento es **necesario** para cumplir un contrato del que el titular es parte (o medidas precontractuales a petición suya).

**Clave**: necesario, no "útil". Si podés cumplir el contrato sin ese dato, no es base contractual.

**Ejemplo PYME**: una academia online necesita el email del alumno para mandarle las clases. Base contractual. NO necesita la fecha de nacimiento — eso requeriría otra base.

**Riesgos**: estirar la base a tratamientos accesorios (marketing, perfilado) que no son "necesarios" para el contrato.

### c) Obligación legal (Art. 6.1.c)

**Cuándo aplica**: una ley impone el tratamiento.

**Requisito**: la ley tiene que ser clara y precisa, y el tratamiento estrictamente necesario.

**Ejemplos PYME**:
- Conservar facturas 6 años (Código de Comercio)
- Comunicar bases de cotización a la Seguridad Social
- Reportes a Hacienda
- Prevención de blanqueo (Ley 10/2010)

**Riesgo**: invocar "obligación legal" cuando es solo "buena práctica" o "criterio interno".

### d) Intereses vitales (Art. 6.1.d)

**Cuándo aplica**: proteger intereses vitales del titular u otra persona física (vida, integridad).

**Uso real**: muy raro fuera de sanidad/emergencias. **Casi nunca aplicable en PYME estándar**.

**Ejemplo**: hospital trata datos de un paciente inconsciente para salvarle la vida.

### e) Interés público o ejercicio de poderes públicos (Art. 6.1.e)

**Cuándo aplica**: misión de interés público o ejercicio de potestades públicas conferidas por ley.

**Uso real**: administración pública, organismos delegados. **No aplica a PYME privada típica**, salvo que tenga un encargo público (notarios, registradores, ITV...).

### f) Interés legítimo (Art. 6.1.f)

**Cuándo aplica**: el tratamiento es necesario para satisfacer **intereses legítimos** del responsable o de un tercero, siempre que **no prevalezcan los derechos del titular**.

**Requisito clave: ponderación (test en 3 pasos)**:
1. **Legitimidad del interés**: ¿es real, lícito y concreto? (marketing directo a clientes existentes, prevención de fraude, seguridad de red...)
2. **Necesidad**: ¿no hay forma menos invasiva de conseguirlo?
3. **Equilibrio**: ¿qué expectativa razonable tiene el titular? ¿Qué impacto en sus derechos?

**Hay que documentar la ponderación por escrito**. Sin documento, no hay base.

**Ejemplos PYME**:
- Email marketing a clientes que ya compraron productos similares (Considerando 47 + LSSI Art. 21.2)
- Videovigilancia en local con cartel y zonas razonables
- Logs de seguridad informática
- Análisis de fraude en pagos

**Riesgos**:
- Usar interés legítimo con menores → casi nunca pasa la ponderación
- Categorías especiales → **NO aplica** Art. 6.1.f
- No documentar la ponderación

> **Anti-patrón típico**: "lo justifico con interés legítimo" como comodín. La AEPD pide la ponderación documentada. Sin eso, sanción.

---

## 2. Categorías especiales (Art. 9): bases REFORZADAS

Para datos sensibles necesitás **además** una base del Art. 9. Las más usadas en PYME:

- **Consentimiento explícito** (no basta el del Art. 6, debe ser explícito)
- **Cumplimiento de obligaciones laborales y de seguridad social** (Art. 9.2.b — ej. mutuas, prevención de riesgos)
- **Intereses vitales** (Art. 9.2.c)
- **Datos manifiestamente públicos** (Art. 9.2.e — el titular los publicó)
- **Reclamaciones** (Art. 9.2.f)
- **Salud, medicina preventiva, gestión sanitaria** (Art. 9.2.h)

> **Regla de oro**: si tu proyecto IA toca datos del Art. 9, parálo y consultá con abogado antes de seguir. La base jurídica del 9 es donde más PYMES se equivocan y donde más caro sale.

---

## 3. Árbol de decisión para elegir base

```
¿Hay una ley que te obligue a tratar el dato?
├── SÍ → Obligación legal (c)
└── NO →
    ¿Es estrictamente necesario para un contrato con el titular?
    ├── SÍ → Ejecución contractual (b)
    └── NO →
        ¿Hay riesgo vital inminente?
        ├── SÍ → Intereses vitales (d)
        └── NO →
            ¿Sos administración pública con potestad legal?
            ├── SÍ → Interés público (e)
            └── NO →
                ¿Podés justificar interés legítimo con ponderación favorable
                y NO son datos sensibles ni de menores en contexto delicado?
                ├── SÍ → Interés legítimo (f) — DOCUMENTÁ LA PONDERACIÓN
                └── NO →
                    Consentimiento (a) — informado, libre, revocable
```

> Para datos del Art. 9 (sensibles): hacé este árbol Y ADEMÁS encontrá base del 9.2.

---

## 4. Documentación obligatoria — Registro de Actividades de Tratamiento (RAT, Art. 30)

El RAT es el documento que la AEPD pide primero. Para cada tratamiento:

| Campo | Contenido |
|-------|-----------|
| Nombre del tratamiento | "Gestión de clientes", "Selección de personal"... |
| Responsable / DPO | Datos de contacto |
| Finalidad | Descripción concreta |
| **Base jurídica** | Art. 6 + Art. 9 si aplica |
| Categorías de interesados | Clientes, empleados, candidatos... |
| Categorías de datos | Identificativos, contacto, económicos... |
| Destinatarios | Encargados, sub-encargados, autoridades |
| Transferencias internacionales | Países y garantías |
| Plazos de conservación | Concretos, no "indefinido" |
| Medidas técnicas y organizativas | Resumen |

> **PYME < 250 empleados**: el Art. 30.5 las exime del RAT **salvo** que el tratamiento sea ocasional, no entrañe riesgo, o no incluya categorías especiales. **En la práctica casi siempre aplica RAT**, porque casi todo tratamiento estable lo dispara. Asumí que tu cliente lo necesita.

---

## 5. Errores típicos en PYME (que vas a encontrar)

| Error | Por qué está mal | Cómo corregirlo |
|-------|------------------|-----------------|
| Consentimiento para todo | No cumple el requisito de "libre" si es la única vía al servicio | Identificar la base correcta por finalidad |
| "Interés legítimo" sin ponderación | No es base válida sin documento | Redactar test de ponderación |
| Misma base para todas las finalidades | Cada finalidad necesita su base | Separar por finalidades en RAT |
| Casillas premarcadas en formularios | No es consentimiento válido (Sentencia Planet49 TJUE) | Casillas vacías + acción afirmativa |
| Newsletter sin opt-in claro | Vulnera RGPD + LSSI | Doble opt-in, registro, unsubscribe visible |
| Cookies analíticas sin consentimiento | Vulnera RGPD + ePrivacy | Banner conforme + bloqueo previo |
| "Lo necesitamos para mejorar el servicio" como finalidad | Demasiado vago | Especificar: estadísticas agregadas / personalización |
| Conservación "indefinida" | Vulnera principio de limitación | Plazos concretos basados en obligaciones legales |

---

## 6. Cómo el consultor ayuda a documentar bases jurídicas

Tu flujo operativo con el cliente:

1. **Inventario de tratamientos**: workshop de 2 horas. Salís con lista de finalidades y datos por área (RR.HH., comercial, marketing, soporte...)
2. **Asignación de base por finalidad**: usás el árbol de decisión. Marcás dudas para el abogado
3. **Redacción del RAT**: plantilla AEPD adaptada
4. **Test de ponderación** para cada interés legítimo: documento de 1-2 páginas por caso
5. **Revisión de avisos de privacidad y formularios**: que la base declarada coincida con la real
6. **Validación jurídica**: el abogado o DPO revisa antes de cierre
7. **Plan de mantenimiento**: revisión anual del RAT, alertas ante cambios de finalidad

> **Punto de derivación a abogado**: cualquier ponderación de interés legítimo con riesgo medio/alto, cualquier base del Art. 9, cualquier decisión automatizada Art. 22, transferencias internacionales fuera del EEE.

---

## 7. Plantilla mínima de ponderación de interés legítimo

```
Tratamiento: [nombre]
Responsable: [empresa]
Fecha / versión: [fecha] / v1.0

1. Interés legítimo perseguido
   - Descripción concreta:
   - ¿Es lícito, real, presente?:

2. Necesidad
   - Finalidad alcanzable con menor injerencia?:
   - Datos mínimos necesarios?:

3. Ponderación con derechos del titular
   - Expectativa razonable del titular:
   - Naturaleza de los datos:
   - Impacto potencial:
   - Garantías y salvaguardas (opt-out, transparencia, minimización):

4. Conclusión
   - Prevalece el interés del responsable: SÍ / NO
   - Medidas adicionales requeridas:

Firma responsable / DPO / fecha
```

---

## Referencias oficiales

- Art. 6 y 9 RGPD: [EUR-Lex](https://eur-lex.europa.eu/eli/reg/2016/679/oj)
- AEPD — Guía sobre interés legítimo: [aepd.es/guias](https://www.aepd.es/guias)
- AEPD — Plantilla RAT y guía: [aepd.es](https://www.aepd.es)
- EDPB — Directrices sobre consentimiento (5/2020): [edpb.europa.eu](https://edpb.europa.eu)
- Sentencia Planet49 (TJUE C-673/17) sobre cookies y consentimiento

> **Cierre**: la base jurídica es la pregunta más sencilla y la que más PYMES suspenden. Si dejás cada tratamiento con base correcta, ponderaciones documentadas y RAT al día, le ahorrás a tu cliente el 70% del riesgo de sanción. Y a vos, te posiciona como consultor que entiende el negocio Y el marco legal — que es el perfil que la PYME paga bien.
