# Sync Strategy — Slides ↔ Schema YAML

Cómo mantener el deck (PPTX/Slidev) alineado con el schema YAML cuando cambien las preguntas. La fuente de verdad es siempre el YAML.

## Convención de IDs (recordatorio)

Naming de slide:

```
core.b{N}.{question_id}.{slide_type}
```

Ejemplos:

- `core.b1.q1_2_sponsor.concept`
- `core.b6.q6_3_ai_act_category.example`
- `core.b1.cover` / `core.b1.closing` (slides estructurales del bloque)

Esta convención permite que un script automatizado detecte:

- preguntas en YAML que **no tienen slide** → slides faltantes.
- slides que **no tienen pregunta YAML** → slides huérfanos (probablemente removidos del schema).

## Checklist post-cambio YAML

Cada vez que se edita `schemas/questionnaire-v2/core/*.yaml`, ejecutar:

1. **Diff de question.id**: ¿se agregó / removió / renombró alguna `id`?
2. **Diff de options**: ¿cambiaron las opciones de un `single_choice` o `multi_choice`?
3. **Diff de hints didácticos**: ¿cambió `hint_didactic` o `hint_commercial`?
4. **Diff de deep_branches**: ¿se agregó/removió un `deep_branch` en una opción?

Por cada cambio:

| Cambio en YAML | Acción en deck | Acción en docs |
|---|---|---|
| Pregunta nueva | Crear slides concept/why/example/question | Agregar entry en `blocks/0X-*.md` |
| Pregunta removida | Eliminar slides | Eliminar entry |
| Pregunta renombrada | Renombrar slides para mantener convention | Actualizar entry |
| Opción nueva | Actualizar slide `options` (si existe) + decision tree del block doc | Actualizar tabla decision tree |
| Hint didáctico cambió | Actualizar slide `concept` y `why` | Actualizar concepto/por qué importa |
| Deep branch nuevo | Actualizar tabla DEEP triggers del block doc | idem |

## Idea: script generador de stubs

Un script Python que lea los YAML y genere markdown de Slidev como **stub** (esqueleto). El consultor luego puebla la parte humana.

### Output esperado

`docs/consulting/decks/core/b1.md` (formato Slidev):

```markdown
---
theme: ./theme
title: Bloque 1 — Estrategia IA
---

<!-- core.b1.cover -->

# Bloque 1 — Estrategia IA

Objetivo: ...
Tiempo: 15 min

---

<!-- core.b1.q1_1_objective.concept -->

# Resultado esperado

[CONCEPTO — completar a partir de hint_didactic]

<!--
QID: q1_1_objective
TYPE: composite
HINT_DIDACTIC: Distinguí objetivo de iniciativa: 'implementar un chatbot' es una iniciativa…
-->

---

<!-- core.b1.q1_1_objective.why -->

# Por qué importa

[A completar]

<!--
HINT_COMMERCIAL: Si el cliente no puede articular un objetivo medible…
-->

---

<!-- core.b1.q1_1_objective.example -->

# Ejemplo

- Clínica: …
- SaaS: …
- Retail: …

---

<!-- core.b1.q1_1_objective.question -->

# ¿Cuál es el resultado concreto?

(Pregunta abierta — escuchá 1–2 min)

<!--
SUB_FIELDS:
  - q1_1_outcome (textarea)
  - q1_1_metric (text)
  - q1_1_timeframe (single_choice: 3m, 6m, 12m, 24m_plus)
-->
```

### Pseudocódigo del generador

```python
# scripts/generate_deck_stubs.py
import yaml
from pathlib import Path

CORE_DIR = Path("schemas/questionnaire-v2/core")
OUT_DIR = Path("docs/consulting/decks/core")

for yaml_file in sorted(CORE_DIR.glob("block-*.yaml")):
    block = yaml.safe_load(yaml_file.read_text())
    block_num = block["order"]
    out = []
    out.append(f"---\ntitle: {block['title']}\n---\n\n")
    out.append(f"<!-- core.b{block_num}.cover -->\n\n# {block['title']}\n\n")
    out.append(f"Tiempo: {block['estimated_minutes']} min\n\n---\n\n")

    for q in block["questions"]:
        for slide_type in ("concept", "why", "example", "question"):
            out.append(f"<!-- core.b{block_num}.{q['id']}.{slide_type} -->\n\n")
            out.append(f"# {slide_type.upper()} — {q['label']}\n\n")
            if slide_type == "concept" and q.get("hint_didactic"):
                out.append(f"> {q['hint_didactic']}\n\n")
            if slide_type == "why" and q.get("hint_commercial"):
                out.append(f"> {q['hint_commercial']}\n\n")
            out.append(_speaker_notes(q))
            out.append("\n---\n\n")

    out.append(f"<!-- core.b{block_num}.closing -->\n\n# Cierre\n\n")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / f"b{block_num}.md").write_text("".join(out))


def _speaker_notes(q):
    notes = [f"QID: {q['id']}", f"TYPE: {q['type']}"]
    if "options" in q:
        notes.append("OPTIONS:")
        for opt in q["options"]:
            line = f"  - {opt['value']}: {opt['label']}"
            if opt.get("deep_branches"):
                line += f"  (DEEP: {','.join(opt['deep_branches'])})"
            notes.append(line)
    return "<!--\n" + "\n".join(notes) + "\n-->\n"
```

**Uso**:

```bash
python scripts/generate_deck_stubs.py     # genera stubs (NO sobrescribe slides ya editados — usar flag --force)
```

### Flag `--check` (CI)

Versión que solo compara y reporta:

```
python scripts/generate_deck_stubs.py --check
> 3 preguntas en YAML sin slide:
>   - core.b3.q3_5_accessibility.concept
>   - core.b3.q3_5_accessibility.why
>   - core.b3.q3_5_accessibility.question
> 1 slide huérfano:
>   - core.b1.q1_5_old_question.concept (no existe en YAML)
```

Esto se puede correr en CI/PR check.

## Escenarios típicos

### Caso A: agregar una pregunta nueva al schema

1. Editar `block-X.yaml`, agregar `q.X_N`.
2. Correr `generate_deck_stubs.py --check` → reporta los 4 slides faltantes.
3. Correr `generate_deck_stubs.py` → genera stubs.
4. Editar el contenido humano de los stubs.
5. Actualizar `docs/consulting/blocks/0X-*.md` agregando la pregunta con su decision tree.

### Caso B: cambiar opciones de un single_choice

1. Editar opciones en YAML.
2. Actualizar slide `core.bX.qY.options` (si existe).
3. Actualizar tabla "Decision tree → opciones" en `docs/consulting/blocks/0X-*.md`.
4. Re-revisar banderas rojas.

### Caso C: deep branch nuevo

1. Editar option en YAML, agregar a `deep_branches`.
2. Actualizar `docs/consulting/blocks/0X-*.md` → tabla DEEP triggers.
3. Crear o actualizar la pregunta correspondiente en `schemas/questionnaire-v2/deep/...` (el branch necesita su prompt LLM).

## Ownership

- **Schema YAML**: product / consultor lead.
- **Slides master**: equipo dev (si Slidev) o consultor lead (si PPTX).
- **Block docs (`blocks/0X-*.md`)**: consultor lead.
- **Sync checks**: CI o consultor lead en cada cambio.

Sin owner claro, el playbook se desactualiza en 2 sprints.
