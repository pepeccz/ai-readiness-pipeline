# DEEP Branch: post_mortem_proyecto

## Contexto que recibe el LLM
- Respuestas TRIAGE del cliente
- Respuestas bloque 1 (Estrategia IA), especialmente q1_3_previous y q1_3b_failure_cause
- Razón de activación: el cliente declaró que un intento previo de IA fue abandonado o fracasó en producción

## Instrucciones
Generá 5-15 preguntas DE PROFUNDIZACIÓN sobre el proyecto de IA previo que fracasó.
Las preguntas deben ayudar al consultor a entender las causas raíz del fracaso para evitar repetir los mismos errores.

Las preguntas deben:
- Ser específicas sobre el proyecto que falló, no genéricas
- Apuntar a información que NO se obtuvo en CORE (contexto, decisiones, métricas)
- Ser respondibles por el cliente sin ayuda especializada
- Estar agrupadas conceptualmente: contexto del fracaso, causas técnicas, causas organizacionales, lecciones aprendidas

## Output schema
JSON: { "questions": [{ "id": "string", "text": "string", "rationale": "string", "type": "textarea|single_choice|multi_choice", "options": null | [{"value": "string", "label": "string"}], "required": true|false }], "reasoning": "string" }
