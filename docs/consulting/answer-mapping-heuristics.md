# Answer Mapping Heuristics

Reglas transversales para traducir lo que dice el cliente a las opciones del YAML. Esto es lo que separa una sesión profesional de un cuestionario torpe.

## Principio general

**El cliente nunca ve las opciones.** Vos escuchás, mapeás mentalmente, y confirmás con la frase: *"Entonces lo que escucho es <opción reformulada en lenguaje natural>. ¿Confirmás?"*. Si confirma, marcás. Si corrige, ajustás.

## Por tipo de campo

### `single_choice`

1. Hacé la pregunta abierta.
2. Escuchá 30–90 seg.
3. Identificá la opción más cercana.
4. Resumí: *"Entonces sería <opción reformulada>. ¿Es así?"*
5. Si dice sí → marcá.
6. Si vacila → leé en voz alta 2–3 opciones cercanas: *"¿Más cercano a A o a B?"*. Nunca leas las 6 opciones, eso es interrogatorio.

### `multi_choice`

1. Mientras el cliente habla, marcá mentalmente las que aplican.
2. Al final preguntá explícitamente las que sospechás pero no confirmó: *"Mencionaste X y Z. ¿También Y?"*
3. Confirmá la lista final: *"Entonces marco X, Y, Z. ¿Falta alguna?"*
4. Si hay `max_selections` (ej: máx 2 en `triage.q.ai_goals`), forzá priorización: *"Si tuvieras que elegir las 2 más importantes…"*

### `composite`

1. Tratá cada `sub_field` como pregunta menor pero **conversacional**, no como subformulario.
2. Una pregunta abierta puede llenar varios sub-fields a la vez. Ej: *"Contame el proceso, cuántas veces ocurre y qué volumen"* → cubre `q2_1_name`, `q2_1_frequency`, `q2_1_volume` de un saque.
3. Solo volvés a preguntar los sub-fields que quedaron vacíos.

### `text` / `textarea`

1. Transcribí literal, sin "limpiar" lo que dice.
2. Respetá `max_length`. Si pasás, recortá pero anotá lo extra en bloc físico.
3. Citas literales sirven al LLM closing analysis.

### `consent`

1. **NO lo pidas durante el flow didáctico.**
2. Al cierre del bloque que corresponda (TRIAGE para los del triage), pedido formal.
3. Lectura corta + click. Si el cliente quiere leer la política completa, mandala link.

## Cuándo dejar campo en blanco vs forzar respuesta

| Situación | Acción |
|---|---|
| Campo `required: true` y cliente no sabe | Marcá `no_se`/`no_claro` si la opción existe. Si no existe esa opción, escogé la más cercana + nota en bloc. |
| Campo `required: false` y cliente vacila | Dejá vacío. La carencia es señal. |
| Cliente da respuesta evasiva intencional | Marcá `no_claro` o equivalente. NO inventes. |
| Cliente da respuesta detallada que no encaja | Reformulá hacia la opción más cercana + transcribí literal en `*_example` o nota. |

**Regla de oro**: el form contaminado con respuestas inventadas es **peor** que un form con campos vacíos. El LLM closing detecta inconsistencias; los campos vacíos son neutros.

## Cuándo activar DEEP follow-up

Los `deep_branches` están en cada `option`. Cuando el cliente elige una opción con deep_branch:

1. **NO hagas el deep en sesión 1.** Marcá la opción y seguí.
2. Anotá el branch_id en el bloc (ej: `dpia_inicial`, `change_management`).
3. Al cierre, mencioná: *"En la sesión 2 vamos a profundizar en X temas: [lista de branches]"*.
4. La sesión 2 (deep) usa esos branches como agenda.

**Excepción**: si el cliente espontáneamente profundiza en un branch durante sesión 1 y aporta info útil, transcribilo en bloc físico — el LLM lo reusa.

## Manejo del cliente verboso

| Síntoma | Frase de corte |
|---|---|
| Habla 3+ min sin acercarse a opción | *"Para no quedarme sin tiempo, lo que escucho es X. ¿Confirmás?"* |
| Se va a tema futuro | *"Buenísimo, lo anoto para el cierre / sesión 2."* |
| Repite lo mismo con otras palabras | *"Confirmo X, avanzamos."* |
| Quiere debatir el concepto | *"Te entiendo. En tu caso, ¿la respuesta es A o B?"* — devuelvo a opción. |

## Manejo del cliente vago / inseguro

| Síntoma | Acción |
|---|---|
| "No sé bien" | *"¿Más cercano a A o a B?"* (binarizar). Si sigue sin saber → `no_se`. |
| Mira a otra persona | Esperá, normalmente otra persona del equipo aporta. |
| Cambia respuesta a mitad | Anotá ambas, confirmá la final: *"¿Quedamos en X?"*. |

## Confirmación tipo

Frase canónica de cierre por pregunta:

> *"Perfecto. Entonces marco <opción en lenguaje natural>. Avanzamos."*

Si la respuesta tiene matices, agregá nota:

> *"Marco <opción> con nota de que <matiz>. Avanzamos."*

## Qué NO hacer (anti-patrones)

- Leer las 6 opciones del YAML al cliente como un menú.
- Forzar respuesta cuando el cliente claramente no sabe.
- "Limpiar" la respuesta del cliente para que encaje en una opción que no es.
- Saltar la confirmación porque "ya entendí".
- Preguntar `consent_*` en medio del flow didáctico.
