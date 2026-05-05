# DEEP Branch: dpia_obligatorio

## Contexto que recibe el LLM
- Respuestas TRIAGE del cliente
- Respuestas bloques CORE relevantes
- Razón de activación: el tratamiento de datos personales requiere una DPIA según RGPD Art. 35

## Instrucciones
Generá 5-15 preguntas DE PROFUNDIZACIÓN sobre evaluación de impacto de protección de datos (DPIA): finalidad, riesgos, medidas que el cliente responderá async para alimentar el report sesión 2.

Las preguntas deben:
- Ser específicas, no genéricas
- Apuntar a información que NO se obtuvo en CORE
- Ser respondibles por el cliente sin ayuda especializada
- Estar agrupadas conceptualmente

## Output schema
JSON: { "questions": [{ "id": "string", "text": "string", "rationale": "string", "type": "textarea|single_choice|multi_choice", "options": null | [{"value": "string", "label": "string"}], "required": true|false }], "reasoning": "string" }
