# DEEP Branch: capacitacion_ai_act

## Contexto que recibe el LLM
- Respuestas TRIAGE del cliente
- Respuestas bloques CORE relevantes
- Razón de activación: el equipo no está capacitado en las categorías de riesgo del AI Act

## Instrucciones
Generá 5-15 preguntas DE PROFUNDIZACIÓN sobre plan de capacitación en AI Act: categorías, obligaciones, roles responsables que el cliente responderá async para alimentar el report sesión 2.

Las preguntas deben:
- Ser específicas, no genéricas
- Apuntar a información que NO se obtuvo en CORE
- Ser respondibles por el cliente sin ayuda especializada
- Estar agrupadas conceptualmente

## Output schema
JSON: { "questions": [{ "id": "string", "text": "string", "rationale": "string", "type": "textarea|single_choice|multi_choice", "options": null | [{"value": "string", "label": "string"}], "required": true|false }], "reasoning": "string" }
