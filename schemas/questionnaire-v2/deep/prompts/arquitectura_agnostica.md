# DEEP Branch: arquitectura_agnostica

## Contexto que recibe el LLM
- Respuestas TRIAGE del cliente
- Respuestas bloques CORE relevantes
- Razón de activación: se detectó riesgo de vendor lock-in en la arquitectura de IA propuesta

## Instrucciones
Generá 5-15 preguntas DE PROFUNDIZACIÓN sobre arquitectura agnóstica de modelos, estrategia multi-vendor y portabilidad que el cliente responderá async para alimentar el report sesión 2.

Las preguntas deben:
- Ser específicas, no genéricas
- Apuntar a información que NO se obtuvo en CORE
- Ser respondibles por el cliente sin ayuda especializada
- Estar agrupadas conceptualmente

## Output schema
JSON: { "questions": [{ "id": "string", "text": "string", "rationale": "string", "type": "textarea|single_choice|multi_choice", "options": null | [{"value": "string", "label": "string"}], "required": true|false }], "reasoning": "string" }
