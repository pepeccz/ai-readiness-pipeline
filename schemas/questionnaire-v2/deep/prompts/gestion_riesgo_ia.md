# DEEP Branch: gestion_riesgo_ia

## Contexto que recibe el LLM
- Respuestas TRIAGE del cliente
- Respuestas bloques CORE relevantes
- Razón de activación: no existe un proceso de gestión de riesgos para el sistema de IA

## Instrucciones
Generá 5-15 preguntas DE PROFUNDIZACIÓN sobre gestión de riesgos IA: identificación, evaluación, mitigación e incidentes que el cliente responderá async para alimentar el report sesión 2.

Las preguntas deben:
- Ser específicas, no genéricas
- Apuntar a información que NO se obtuvo en CORE
- Ser respondibles por el cliente sin ayuda especializada
- Estar agrupadas conceptualmente

## Output schema
JSON: { "questions": [{ "id": "string", "text": "string", "rationale": "string", "type": "textarea|single_choice|multi_choice", "options": null | [{"value": "string", "label": "string"}], "required": true|false }], "reasoning": "string" }
