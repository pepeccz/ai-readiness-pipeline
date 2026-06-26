# PPTX Tooling — Comparativa

Qué herramienta usar para producir, mantener y presentar las slides. Criterios: integración con la app intake, edición no-técnica por consultor, export limpio a PDF para cliente, mantenibilidad.

## Comparativa rápida

| Herramienta | Edición | Integración | Export PDF | Versionado | Lock-in |
|---|---|---|---|---|---|
| **PowerPoint / Keynote** | Excelente (cualquiera) | Nula | Excelente | Pésimo (binario) | Medio |
| **Google Slides** | Excelente colaborativa | Vía link | Bueno | Histórico GDocs | Alto (vendor) |
| **Reveal.js** | Requiere dev | Total (web app) | Vía decktape | Git-native | Bajo |
| **Slidev** | Markdown-first | Alta (Vue, web) | Built-in | Git-native | Bajo |
| **Gamma** | Excelente AI-assisted | Limitada | Bueno | Limitado | Alto |
| **Pitch** | Excelente colaborativa | API | Bueno | Limitado | Alto |

## Análisis por opción

### PowerPoint / Keynote
- **Pros**: cualquier consultor sabe usarlo. Curva cero. Animaciones ricas (que no usaremos).
- **Contras**: binario, imposible de versionar. Cambios de cliente requieren coordinar archivos. No se integra con la app intake.
- **Ideal si**: consultores 100% no técnicos, sin equipo dev disponible para mantener slides.

### Google Slides
- **Pros**: colaborativo en tiempo real. Histórico decente. Comparte por link.
- **Contras**: lock-in Google. Diseño limitado. Difícil de mantener consistencia tipográfica entre decks.
- **Ideal si**: equipo distribuido sin pipeline técnico.

### Reveal.js
- **Pros**: HTML/JS puros. Embeddable en la app intake (mismo dominio, misma sesión). Versionado git. Tematizable globalmente.
- **Contras**: requiere dev para cambios estructurales. Consultor no-tech no edita cómodamente.
- **Ideal si**: querés que el deck **viva dentro de la app** (slides en `/admin/intake/<lead_id>/deck`).

### Slidev
- **Pros**: **markdown-first**. Cada slide es un bloque markdown separado por `---`. Fácil de versionar, escribir, traducir. Components Vue para custom. Export PDF nativo. Speaker notes nativas.
- **Contras**: aún requiere `npm run dev` para preview. Curva 30 min para no-tech.
- **Ideal si**: querés un balance entre potencia técnica (versionado, sync con YAML) y edición razonable.

### Gamma
- **Pros**: generación asistida por IA. Resultado visual de buena calidad sin diseñador.
- **Contras**: lock-in fuerte. Difícil mantener convención de naming `core.bN.qX.tipo`. Sin git.
- **Ideal si**: quick MVP, sin commitment a mantener.

### Pitch
- **Pros**: colaboración tipo Figma. Templates buenos. Comentarios.
- **Contras**: lock-in. Sin sync con schema YAML.

## Recomendación

**Slidev** como principal, **PowerPoint como fallback exportado** para clientes.

Rationale:

1. **Sync con YAML**: el bloqueo más caro a futuro es que cambien las preguntas y no se actualicen los slides. Slidev permite que un script lea `schemas/questionnaire-v2/core/*.yaml` y **genere stubs de slides**:
   ```
   schemas/.../block-1-strategic.yaml → slides/core/b1.md (con secciones por pregunta)
   ```
   Ver `sync-strategy.md` para el script.

2. **Versionado git**: cada cambio en el guion queda trazable, revisable en PR, reversible.

3. **Speaker notes inline**: en cada slide markdown, las notas están abajo con `<!-- ... -->`. Perfecto para incluir `QID`, `OPCIONES`, `RED FLAGS`.

4. **Export PDF para cliente**: `slidev export` produce PDF limpio sin animaciones, perfecto para enviar post-sesión.

5. **Custom components opcionales**: si más adelante querés un slide que muestre las opciones del YAML cargadas dinámicamente, podés hacer un `<QuestionOptions qid="q1_2_sponsor" />` que las lee del schema. El consultor usa el mismo deck, los datos siempre actualizados.

6. **Costo**: $0. Self-hosted o estático.

### Fallback PowerPoint

Para consultores que **no quieren ni ver markdown**: el equipo dev exporta el deck Slidev a PPTX (vía Slidev → PDF → PPTX, o build estático embebido). El consultor edita el PPTX en su sesión particular sin afectar el master. **Aceptamos divergencia** entre master Slidev y la copia personal del consultor.

## Decisión recomendada

| Equipo | Recomendación |
|---|---|
| Tenés 1+ dev con tiempo para mantener | **Slidev** (master) + PDF export para clientes |
| Solo consultores, cero dev | **PowerPoint** master compartido en Drive + checklist manual de sync con YAML |
| Mid-term | Empezar PowerPoint, migrar a Slidev cuando duela el sync |

## Bonus: integración con app intake

Si elegís Slidev, podés montar el build estático en `/admin/intake/<lead_id>/deck`. Beneficios:

- El consultor abre la sesión, click "Iniciar deck", se abre la presentación en mismo dominio.
- Speaker notes pueden tener un link "abrir form en pregunta X" → un click navega el form a la pregunta correspondiente.
- Telemetría: cuánto tiempo pasaron en cada slide → dato real para iterar el playbook.

Esto requiere ~1 sprint dev. No es para v1, pero está en el horizonte.
