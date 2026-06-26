# Bloque 00 — TRIAGE (recap pre-sesión)

El TRIAGE ya fue respondido por el cliente vía formulario público. **NO se presenta en la sesión** — pero el consultor debe revisarlo antes de empezar para llegar con hipótesis.

## Qué revisar (5 min antes de la sesión)

Abrí el lead en `/admin/leads/<id>` y leé:

| Campo | Qué te dice |
|---|---|
| `triage.q.identity` | Nombre, empresa, email, teléfono. Verificá pronunciación. |
| `triage.q.sector` | Sector → te dice qué ejemplo sectorial usar en cada slide. |
| `triage.q.company_size` | Tamaño → calibra escala de pilotos posibles. |
| `triage.q.ai_maturity` | Madurez actual (sin_ia / exploración / pilotos / producción sin gobierno / producción gobernada). Es el ANCLA del nivel didáctico. |
| `triage.q.urgency` | Urgencia (crítica / alta / media / baja). |
| `triage.q.ai_goals` | Objetivos seleccionados (máx 2). Te dice qué bloque enfatizar. |
| `triage.q.respondent_role` | Rol → CEO escucha distinto que CTO. |
| `triage.q.commitment` | Cuánto puede comprometer post-sesión. |

## Score y bucket

| Bucket | Score | Lectura |
|---|---|---|
| `auto_accept` | 85–136 | Lead caliente, sesión corta posible. Ir directo al deep. |
| `review` | 55–84 | Lead común. Sesión completa. |
| `cold_warm` | 45–54 | Necesita más formación. Más tiempo en bloque 1 y 6. |
| `cold_cool` | 30–44 | Sesión 100% educativa, vender es prematuro. |
| `reject_soft` | 0–29 | Idealmente no llega a sesión. Si llega, formación pura. |

## Hipótesis previa (mental, no la digas)

Combinando triage podés llegar con una hipótesis de 1 línea:

- *"Clínica de 50 personas en exploración con urgencia alta y objetivo cumplimiento → la conversación se va a centrar en bloques 3 (datos sensibles), 6 (DPIA + AI Act alto riesgo)."*
- *"SaaS de 200 personas en producción sin gobierno → el problema es Shadow AI y el bloque 7 va a estar caliente."*

Anotá la hipótesis en el bloc. Al cierre la confirmás o ajustás.

## Override flags a vigilar

Del schema:

- `regulated_urgent_force_accept`: salud/legal/finanzas + urgencia alta/crítica + score≥55 → fuerza auto_accept. **El cliente no sabe esto, no lo digas.** Solo te calibra a vos.
- `external_advocate`: si el rol es `consultor_externo` con `commitment=agendar`, hay flag de "consultor representando cliente final". **Preguntá al inicio**: *"¿La sesión es para vos como consultor, o para el cliente final que representás?"*

## Banderas rojas en el TRIAGE

| Combinación | Riesgo |
|---|---|
| `urgencia=critica` + `ai_maturity=sin_ia` | Expectativa rota. El cliente cree que IA = magia rápida. Bloque 1 lento. |
| `compromiso=evaluacion_interna` + `rol=consultor_externo` | Sesión informativa, no decisora. Calibrá tiempo invertido. |
| `objetivos=cumplimiento_regulatorio` + `sector=otro` | Probable confusión sobre AI Act. Bloque 6 muy didáctico. |
| Email genérico (gmail/hotmail) en `identity.email` | Empresa probablemente <10 personas o lead "exploratorio". |

## Consents

Ya están en el TRIAGE (`consent_privacy` obligatorio, `consent_marketing` opcional). **NO los re-pidas en sesión** — están en BBDD. Sí podés mencionar al cierre: *"Recordá que tenés derecho a borrar todo esto cuando quieras."*
