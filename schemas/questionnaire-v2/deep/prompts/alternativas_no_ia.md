# DEEP Branch: alternativas_no_ia

## Contexto que recibe el LLM
- Respuestas TRIAGE del cliente
- Respuestas bloques CORE relevantes
- Razón de activación: el proceso analizado podría abordarse sin IA de forma más eficiente

## Instrucciones
Generá 5-15 preguntas DE PROFUNDIZACIÓN sobre alternativas no-IA al problema planteado (automatización RPA, rediseño de proceso, etc.) que el cliente responderá async para alimentar el report sesión 2.

Las preguntas deben:
- Ser específicas, no genéricas
- Apuntar a información que NO se obtuvo en CORE
- Ser respondibles por el cliente sin ayuda especializada
- Estar agrupadas conceptualmente

## Output schema
JSON: { "questions": [{ "id": "string", "text": "string", "rationale": "string", "type": "textarea|single_choice|multi_choice", "options": null | [{"value": "string", "label": "string"}], "required": true|false }], "reasoning": "string" }
