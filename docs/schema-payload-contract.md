# Schema and Payload Contract

This document defines the canonical structure and conventions for block schemas (YAML) and the JSON payloads they produce. These rules ensure consistency across intake forms, backend validation, and data exports.

## Table of Contents

1. [Payload Key Namespace](#payload-key-namespace)
2. [Reserved Suffix: `_other_text`](#reserved-suffix-_other_text)
3. [Composite Payload Shape](#composite-payload-shape)
4. [Draft vs. Submitted Lifecycle](#draft-vs-submitted-lifecycle)
5. [Pydantic Extra Keys on Submit](#pydantic-extra-keys-on-submit)

---

## Payload Key Namespace

### Rules

1. **Top-level keys MUST match question IDs** defined in the block YAML schema, except for reserved sibling keys (see next section).
2. **Question IDs are case-sensitive** and normalized to lowercase with underscores (e.g., `q1_2_sponsor`, `q3_4_category`).
3. **Sibling companion keys** (e.g., for free-text "Otro" input) are stored as root-level entries in the same flat structure, NOT nested inside composite payloads.
4. **Sub-field IDs** within composite questions are also stored flat at the root level in the payload (not nested), unless explicitly grouped by the consumer (see Composite Payload Shape).

### Example: Single-level payload

```json
{
  "q1_2_sponsor": "ceo_total",
  "q1_3_previous": "exitoso_produccion",
  "q3_1_sources": ["erp", "crm"]
}
```

---

## Reserved Suffix: `_other_text`

### Rules

1. **No question ID in any block YAML schema MAY end with `_other_text`**.
   - This suffix is reserved as a companion key for free-text input paired with "Otro" (Other) radio/checkbox selections.
   - Using it on a question ID would cause collision and payload corruption.
   - A schema-load assertion in `frontend/src/intake/hooks/useSchemaForm.ts` (dev-mode only) detects violations and logs an error.
   - A pytest test `tests/integration/test_schema_contract.py` validates this contract at startup.

2. **Declaring "Otro" in YAML schemas** — Two patterns are supported:

   **Pattern A: Legacy — Value-based detection**
   ```yaml
   questions:
     - id: q3_1_sources
       type: multi_choice
       options:
         - value: "otro"
           label: "Otro"
   ```
   The renderer detects `value: "otro"` (or `otros`, `other`) and automatically provisions a free-text input.

   **Pattern B: Forward-compatible — Explicit flag**
   ```yaml
   questions:
     - id: q4_3_preference
       type: single_choice
       options:
         - value: "custom"
           label: "Mi opción personalizada"
           is_other: true
   ```
   The `is_other: true` flag explicitly signals that this option triggers free-text input. This is the canonical approach and should be used for new schemas.

3. **Storing "Otro" free-text** — When a user selects an "Otro" option and types free-text input, the text is stored under the key `${question_id}_other_text` at the root level of the payload.

### Example: Single-choice with "Otro"

**Schema:**
```yaml
- id: q1_sponsor
  type: single_choice
  options:
    - value: "ceo"
      label: "CEO"
    - value: "director"
      label: "Director"
    - value: "otro"
      label: "Otro (especificar)"
```

**Payload when user selects "Otro" and types "Junta directiva":**
```json
{
  "q1_sponsor": "otro",
  "q1_sponsor_other_text": "Junta directiva"
}
```

### Example: Multi-choice with "Otro"

**Schema:**
```yaml
- id: q3_sources
  type: multi_choice
  options:
    - value: "erp"
      label: "ERP"
    - value: "otros"
      label: "Otros"
```

**Payload when user selects ["erp", "otros"] and types "Base de datos personalizada":**
```json
{
  "q3_sources": ["erp", "otros"],
  "q3_sources_other_text": "Base de datos personalizada"
}
```

---

## Composite Payload Shape

### Definition

A **composite question** is a multi-field group with a single label and multiple sub-fields (e.g., a question asking "How old are you?" with separate sub-fields for "Years" and "Months").

### Payload Storage

Composite sub-field values are stored **flat at the root level** alongside other question values. They do NOT nest inside a composite object.

**Schema:**
```yaml
- id: q3_2_quality
  type: composite
  required: true
  label: "Data quality assessment"
  sub_fields:
    - id: q3_2_level
      type: single_choice
      required: true
      options:
        - value: "excellent"
          label: "Excellent"
        - value: "poor"
          label: "Poor"
    - id: q3_2_example
      type: text
      required: false
      label: "Example of quality issue"
```

**Payload (flat structure):**
```json
{
  "q3_2_level": "excellent",
  "q3_2_example": "Sometimes missing email addresses"
}
```

### Composite Counter Semantic (REQ-1)

The progress counter (answered questions / total questions) uses these rules:

- **Simple question**: Answered if value is non-empty (not `undefined`, `null`, `""`, or `[]`).
- **Composite with NO required sub-fields**: Answered if ANY visible sub-field has a non-empty value ("any" semantic).
- **Composite WITH required sub-fields**: Answered if ALL required visible sub-fields have non-empty values ("all-required" semantic).

**Example:**
- Composite with 3 sub-fields (none required) + user fills 1 → counts as 1 answered question.
- Composite with 2 required sub-fields + user fills 1 → counts as 0 answered questions (until both required fields are filled).

---

## Draft vs. Submitted Lifecycle

### State Definitions

1. **Draft** — A partial or complete set of answers saved to the backend but NOT yet finalized.
   - Stored in `BlockDraft` table (backend).
   - Created/updated via `PUT /api/intake/{lead_id}/blocks/{block_id}/draft`.
   - Lightweight validation (key whitelist only; full per-question rules are skipped).
   - Auto-deleted on successful block submission.
   - Allows cross-device resumption (user can switch devices and resume editing where they left off).

2. **Submitted** — A finalized answer set that has passed strict validation and is recorded in `BlockAnswer`.
   - Created via `POST /api/intake/{lead_id}/blocks/{block_id}/submit`.
   - Full Pydantic validation (all question rules, required fields, etc.).
   - Immutable (once submitted, this exact payload is the authoritative answer).
   - Takes precedence over draft on restoration (submitted is displayed as read-only with an "Edit" affordance).

### Resolution Order on Block Render

When a block form loads, the frontend restoration logic follows this priority:

1. **If submitted answer exists** → display submitted payload in read-only mode.
   - An "Edit" button allows the user to copy the submitted payload into a fresh draft and unlock the form.
2. **Else if draft exists** → display draft payload in editable mode.
3. **Else** → empty form.

### Autosave Behavior

- **Frontend** periodically saves form changes as drafts (debounced 1.5s after last edit).
- **Backend** is the source of truth; localStorage is a fallback-only offline cache.
- **Flush on unmount** or when tab is hidden (`visibilitychange: hidden`).
- **Failed sends** are retried on next form change.

### Lifecycle Example

```
User opens block 1
  ├─ No submitted answer, no draft
  └─ Empty form, ready for input

User fills in 2 fields (autosave fires 1.5s later)
  ├─ Draft created in BlockDraft table
  └─ GET /payload returns source='draft' with 2 fields

User fills in remaining fields, submits the block
  ├─ POST /submit validates fully, creates BlockAnswer
  ├─ BlockDraft is deleted (same transaction)
  └─ GET /payload returns source='submitted' with all fields

User reopens the block
  ├─ GET /payload returns source='submitted' (read-only)
  ├─ User clicks "Edit"
  └─ Draft created from submitted payload; form unlocked
```

---

## Pydantic Extra Keys on Submit

### Rule

Submit endpoint Pydantic models MUST accept `_other_text` sibling keys **without validation error**, even if those keys are not explicitly declared as fields.

### Implementation

**Option A: Explicit `extra='allow'` (recommended)**

```python
class BlockSubmitRequest(BaseModel):
    payload: dict

    model_config = ConfigDict(extra='allow')
```

This allows any undeclared keys at the model top level to pass validation without error. The `_other_text` keys arrive in `model_extra` (available but typically unused).

**Option B: Explicit allow-list per block**

If a block's schema is known at validation time, the model can explicitly declare the expected `_other_text` companion keys:

```python
class Block3SubmitRequest(BaseModel):
    q3_1_sources: list[str]
    q3_1_sources_other_text: str | None = None
    q3_2_level: str
    q3_2_example: str | None = None
    # ... other fields

    model_config = ConfigDict(extra='forbid')
```

However, this requires YAML schema changes to be reflected in the Pydantic schema, increasing maintenance burden. **Option A is preferred for MVP**.

### Rationale

- **Backward compatibility**: Existing code that does not use "Otro" continues to work (no validation failure).
- **Forward compatibility**: New questions can add `is_other: true` without backend schema update (the `_other_text` key is quietly accepted).
- **Consumer flexibility**: Downstream analytics, exports, and integrations can inspect the payload and extract `_other_text` keys if they need them; others can ignore them.

---

## Summary: Key Rules Checklist

- [ ] No question ID ends in `_other_text` (assert at schema load time and pytest startup).
- [ ] "Otro" options are declared with `value: 'otro' | 'otros' | 'other'` OR `is_other: true`.
- [ ] Free-text "Otro" input is stored as `${question_id}_other_text` at root level.
- [ ] Composite sub-fields are stored flat at root level (not nested).
- [ ] Composite progress counter uses hybrid semantic (any vs. all-required).
- [ ] Draft is lightweight; submit is strict.
- [ ] Submitted takes precedence over draft on restoration.
- [ ] Pydantic submit models accept `_other_text` extras without error.
- [ ] BlockDraft is auto-deleted on successful submit (same transaction).
