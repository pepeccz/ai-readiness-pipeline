# DEEP Branch: modelo_delivery_saas

## Contexto que recibe el LLM
- Respuestas TRIAGE del cliente
- Respuestas bloques CORE relevantes
- Razón de activación: la arquitectura óptima puede ser SaaS managed en vez de desarrollo propio

## Instrucciones
Generá 5-15 preguntas DE PROFUNDIZACIÓN sobre modelo de entrega SaaS vs partner-managed y criterios de selección de vendor que el cliente responderá async para alimentar el report sesión 2.

Las preguntas deben:
- Ser específicas, no genéricas
- Apuntar a información que NO se obtuvo en CORE
- Ser respondibles por el cliente sin ayuda especializada
- Estar agrupadas conceptualmente

## Output schema
JSON: { "questions": [{ "id": "string", "text": "string", "rationale": "string", "type": "textarea|single_choice|multi_choice", "options": null | [{"value": "string", "label": "string"}], "required": true|false }], "reasoning": "string" }
