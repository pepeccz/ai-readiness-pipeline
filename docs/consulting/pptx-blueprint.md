# PPTX Blueprint

Estructura repetible para producir las slides de la sesión. Cada bloque YAML → un deck. Cada pregunta → 3–5 slides.

## Plantilla por pregunta

| Tipo slide | Contenido | Tiempo en pantalla |
|---|---|---|
| **concept** | Definición + 1 visual. *"Sponsor = quien aprueba presupuesto y resuelve bloqueos."* | 30–45 s |
| **why** | Por qué le importa a SU negocio (genérico, customizado en vivo verbalmente). *"Sin sponsor, los proyectos se mueren a los 3 meses."* | 30 s |
| **example** | 3 mini-casos sectoriales (clínica / SaaS / retail) — el consultor elige el más cercano. | 30 s |
| **question** | La pregunta abierta, sin opciones visibles. *"En tu caso, ¿quién aprobaría esta iniciativa?"* | escucha 1–3 min |
| **options** *(opcional)* | Solo para preguntas con `single_choice` complejas — visual de las opciones para guiar mapeo. | 20 s si se usa |

## Plantilla por bloque

```
[Slide portada bloque]    → "Bloque N — Título"  + objetivo en 1 línea + agenda mini
[N preguntas × 3–5 slides cada una]
[Slide cierre/transición] → 1 frase de síntesis + "Pasamos al bloque siguiente"
```

## Diseño visual

### Jerarquía tipográfica

- **Título slide**: 36–44pt, peso 600.
- **Subtítulo / concepto clave**: 22–28pt, peso 400.
- **Cuerpo**: 16–20pt, peso 300.
- **Nota inferior (question.id)**: 10pt, color secundario.

Una idea por slide. Si necesitás 2 ideas, son 2 slides.

### Paleta sobria

Recomendación (3 colores + neutros):

- Primario: azul oscuro (`#1E2A44`) — títulos, marca.
- Acento: ámbar (`#E8A33D`) — destacados, números.
- Alerta: rojo apagado (`#B23A48`) — banderas rojas, riesgos.
- Neutros: blanco roto + 2 grises.

NO uses gradientes ni sombras. NO bullets densos.

### Íconos consistentes

Una sola familia de íconos (Lucide, Phosphor, Heroicons — elegí UNA). Tamaño fijo (32 o 48px). Trazo, no relleno.

### Animaciones

- **Permitido**: reveal progresivo (un punto por click) en slide concept solamente.
- **Prohibido**: zoom, fade decorativo, transiciones 3D, efectos de entrada por palabra.

## Convención de naming

Slides ↔ question.id mapeo 1:1 vía nombre de slide.

```
core.b{block_number}.{question_id}.{slide_type}
```

Ejemplos:

| Slide | YAML question |
|---|---|
| `core.b1.q1_2_sponsor.concept` | `block-1-strategic.yaml → q1_2_sponsor` |
| `core.b1.q1_2_sponsor.why` | idem |
| `core.b1.q1_2_sponsor.example` | idem |
| `core.b1.q1_2_sponsor.question` | idem |
| `core.b6.q6_3_ai_act_category.concept` | `block-6-compliance.yaml → q6_3_ai_act_category` |

Para TRIAGE (no se presenta, pero si querés hacerlo):

```
triage.{question_id}.{slide_type}
```

Para slides de bloque (portada / cierre):

```
core.b{N}.cover
core.b{N}.closing
```

### Por qué importa esta convención

- Permite generar stub de slides desde YAML (ver `sync-strategy.md`).
- En modo presenter, el consultor sabe exactamente qué campo del form tocar.
- Renombrar question.id en YAML → renombrar slide → catch automático.

## Notas del speaker

Cada slide debe tener en notas:

```
QID: <question.id>
TYPE: <single_choice|multi_choice|composite|...>
OPCIONES (no leer):
  - opt_a → "...etiqueta..."
  - opt_b → "..."
DEEP TRIGGERS: <branch_id si activa>
RED FLAGS: <qué cuidar>
```

Esto permite que un consultor nuevo presente sin perderse.

## Export

- Formato master: editable (PPTX o equivalente — ver `pptx-tooling.md`).
- Export para cliente: PDF post-sesión, watermark sutil.
- NO compartir el master editable con el cliente.
