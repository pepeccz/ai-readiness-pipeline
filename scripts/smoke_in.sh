#!/usr/bin/env bash
# smoke_in.sh — Backend smoke tests for the admin-frontend-independence change.
#
# NOTE: Backend smoke is in scripts/smoke_in.sh (this file).
#       Frontend smoke requires manual browser testing — see docs/OPERATIONS.md.
#
# Prerequisites:
#   export ASSESSMENT_ID="<uuid-of-a-draft-or-pending-review-assessment>"
#   export SESSION_COOKIE="<value-of-admin_sid-cookie>"
#   export BASE_URL="http://localhost:8100"  # optional, defaults below
#
# Usage:
#   chmod +x scripts/smoke_in.sh
#   ASSESSMENT_ID=... SESSION_COOKIE=... ./scripts/smoke_in.sh
#
# Each test prints PASS / FAIL and the relevant JSON excerpt.

set -euo pipefail

BASE_URL="${BASE_URL:-http://localhost:8100}"
API="${BASE_URL}/api/admin/assessments"

if [[ -z "${ASSESSMENT_ID:-}" ]]; then
  echo "ERROR: ASSESSMENT_ID is not set." >&2
  exit 1
fi

if [[ -z "${SESSION_COOKIE:-}" ]]; then
  echo "ERROR: SESSION_COOKIE is not set." >&2
  exit 1
fi

COOKIE_HEADER="Cookie: admin_sid=${SESSION_COOKIE}"
ID="${ASSESSMENT_ID}"

pass() { echo "  PASS: $1"; }
fail() { echo "  FAIL: $1"; }

check_code() {
  local label="$1" expected="$2" actual="$3"
  if [[ "${actual}" == "${expected}" ]]; then
    pass "${label} — code=${actual}"
  else
    fail "${label} — expected code=${expected}, got code=${actual}"
  fi
}

echo ""
echo "====================================================================="
echo " Smoke tests: Batch 2 IN-Backend (form_data_patch + ?mode=replace)"
echo " Assessment: ${ID}"
echo "====================================================================="

# ── T1: form_data_patch deep-merge (HAPPY PATH) ───────────────────────────
echo ""
echo "T1 — form_data_patch deep-merge"
RESPONSE=$(curl -s -X PATCH "${API}/${ID}" \
  -H "${COOKIE_HEADER}" \
  -H "Content-Type: application/json" \
  -d '{"form_data_patch": {"software_used": ["Notion","Slack"]}}')

HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X PATCH "${API}/${ID}" \
  -H "${COOKIE_HEADER}" \
  -H "Content-Type: application/json" \
  -d '{"form_data_patch": {"software_used": ["Notion","Slack"]}}')

if [[ "${HTTP_CODE}" == "200" ]]; then
  pass "T1 — 200 OK"
  echo "  form_data.software_used = $(echo "${RESPONSE}" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('form_data',{}).get('software_used','MISSING'))" 2>/dev/null || echo "(parse error)")"
  echo "  field_sources[form_data.software_used] = $(echo "${RESPONSE}" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('field_sources',{}).get('form_data.software_used','MISSING'))" 2>/dev/null || echo "(parse error)")"
else
  fail "T1 — expected 200, got ${HTTP_CODE}"
  echo "  Response: $(echo "${RESPONSE}" | head -c 300)"
fi

# ── T2: Sibling preservation (after T1, patch a different key) ────────────
echo ""
echo "T2 — Sibling preservation (add has_chatbot, software_used must survive)"
RESPONSE2=$(curl -s -X PATCH "${API}/${ID}" \
  -H "${COOKIE_HEADER}" \
  -H "Content-Type: application/json" \
  -d '{"form_data_patch": {"has_chatbot": true}}')

HTTP_CODE2=$(curl -s -o /dev/null -w "%{http_code}" -X PATCH "${API}/${ID}" \
  -H "${COOKIE_HEADER}" \
  -H "Content-Type: application/json" \
  -d '{"form_data_patch": {"has_chatbot": true}}')

# Re-fetch the assessment to check sibling persistence.
REFETCH=$(curl -s "${API}/${ID}" -H "${COOKIE_HEADER}")
SW=$(echo "${REFETCH}" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('form_data',{}).get('software_used','MISSING'))" 2>/dev/null || echo "(parse error)")
CB=$(echo "${REFETCH}" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('form_data',{}).get('has_chatbot','MISSING'))" 2>/dev/null || echo "(parse error)")

if [[ "${SW}" == *"Notion"* ]] && [[ "${SW}" == *"Slack"* ]]; then
  pass "T2 — software_used sibling preserved: ${SW}"
else
  fail "T2 — software_used was wiped or changed: ${SW}"
fi
echo "  form_data.has_chatbot = ${CB}"

# ── T3: form_data without ?mode=replace → 422 replace_mode_required ───────
echo ""
echo "T3 — form_data without ?mode=replace → 422 replace_mode_required"
RESPONSE3=$(curl -s -X PATCH "${API}/${ID}" \
  -H "${COOKIE_HEADER}" \
  -H "Content-Type: application/json" \
  -d '{"form_data": {"software_used": ["Excel"]}}')

HTTP_CODE3=$(curl -s -o /dev/null -w "%{http_code}" -X PATCH "${API}/${ID}" \
  -H "${COOKIE_HEADER}" \
  -H "Content-Type: application/json" \
  -d '{"form_data": {"software_used": ["Excel"]}}')

RESP_CODE3=$(echo "${RESPONSE3}" | python3 -c "import sys,json; print(json.load(sys.stdin).get('code','MISSING'))" 2>/dev/null || echo "(parse error)")

if [[ "${HTTP_CODE3}" == "422" ]]; then
  check_code "T3 — 422 + code" "replace_mode_required" "${RESP_CODE3}"
else
  fail "T3 — expected 422, got ${HTTP_CODE3}"
fi

# ── T4: form_data + ?mode=replace → 200, wholesale replace ────────────────
echo ""
echo "T4 — form_data + ?mode=replace → 200, wholesale replace"
RESPONSE4=$(curl -s -X PATCH "${API}/${ID}?mode=replace" \
  -H "${COOKIE_HEADER}" \
  -H "Content-Type: application/json" \
  -d '{"form_data": {"software_used": ["SAP"]}}')

HTTP_CODE4=$(curl -s -o /dev/null -w "%{http_code}" -X PATCH "${API}/${ID}?mode=replace" \
  -H "${COOKIE_HEADER}" \
  -H "Content-Type: application/json" \
  -d '{"form_data": {"software_used": ["SAP"]}}')

if [[ "${HTTP_CODE4}" == "200" ]]; then
  FD_KEYS=$(echo "${RESPONSE4}" | python3 -c "import sys,json; d=json.load(sys.stdin); print(list(d.get('form_data',{}).keys()))" 2>/dev/null || echo "(parse error)")
  pass "T4 — 200 OK, form_data keys after replace: ${FD_KEYS}"
  # Verify has_chatbot (set in T2) is GONE after replace
  CB_AFTER=$(echo "${RESPONSE4}" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('form_data',{}).get('has_chatbot','ABSENT'))" 2>/dev/null || echo "(parse error)")
  if [[ "${CB_AFTER}" == "ABSENT" ]]; then
    pass "T4 — has_chatbot correctly removed by wholesale replace"
  else
    fail "T4 — has_chatbot should be absent after replace, got: ${CB_AFTER}"
  fi
  # Verify field_sources only contains form_data.software_used (not form_data.has_chatbot)
  FS=$(echo "${RESPONSE4}" | python3 -c "import sys,json; d=json.load(sys.stdin); fs=d.get('field_sources',{}); print({k:v for k,v in fs.items() if k.startswith('form_data.')})" 2>/dev/null || echo "(parse error)")
  echo "  field_sources form_data.* after replace: ${FS}"
else
  fail "T4 — expected 200, got ${HTTP_CODE4}"
  echo "  Response: $(echo "${RESPONSE4}" | head -c 300)"
fi

# ── T5: BOTH form_data AND form_data_patch → 422 form_data_conflict ───────
echo ""
echo "T5 — BOTH form_data + form_data_patch → 422 form_data_conflict"
RESPONSE5=$(curl -s -X PATCH "${API}/${ID}" \
  -H "${COOKIE_HEADER}" \
  -H "Content-Type: application/json" \
  -d '{"form_data": {}, "form_data_patch": {"has_chatbot": false}}')

HTTP_CODE5=$(curl -s -o /dev/null -w "%{http_code}" -X PATCH "${API}/${ID}" \
  -H "${COOKIE_HEADER}" \
  -H "Content-Type: application/json" \
  -d '{"form_data": {}, "form_data_patch": {"has_chatbot": false}}')

RESP_CODE5=$(echo "${RESPONSE5}" | python3 -c "import sys,json; print(json.load(sys.stdin).get('code','MISSING'))" 2>/dev/null || echo "(parse error)")

if [[ "${HTTP_CODE5}" == "422" ]]; then
  check_code "T5 — 422 + code" "form_data_conflict" "${RESP_CODE5}"
else
  fail "T5 — expected 422, got ${HTTP_CODE5}"
fi

# ── T6: form_data_patch with unknown key → 422 unknown_form_data_key ──────
echo ""
echo "T6 — form_data_patch with unknown key → 422 unknown_form_data_key"
RESPONSE6=$(curl -s -X PATCH "${API}/${ID}" \
  -H "${COOKIE_HEADER}" \
  -H "Content-Type: application/json" \
  -d '{"form_data_patch": {"current_tools": "SAP"}}')

HTTP_CODE6=$(curl -s -o /dev/null -w "%{http_code}" -X PATCH "${API}/${ID}" \
  -H "${COOKIE_HEADER}" \
  -H "Content-Type: application/json" \
  -d '{"form_data_patch": {"current_tools": "SAP"}}')

RESP_CODE6=$(echo "${RESPONSE6}" | python3 -c "import sys,json; print(json.load(sys.stdin).get('code','MISSING'))" 2>/dev/null || echo "(parse error)")
RESP_DETAIL6=$(echo "${RESPONSE6}" | python3 -c "import sys,json; print(json.load(sys.stdin).get('detail','MISSING'))" 2>/dev/null || echo "(parse error)")

if [[ "${HTTP_CODE6}" == "422" ]]; then
  check_code "T6 — 422 + code" "unknown_form_data_key" "${RESP_CODE6}"
  echo "  detail: ${RESP_DETAIL6}"
else
  fail "T6 — expected 422, got ${HTTP_CODE6}"
fi

# ── T7: R5 sync — investment_budget / urgency update flat columns ──────────
echo ""
echo "T7 — R5 sync: form_data_patch investment_budget + urgency → flat columns"
RESPONSE7=$(curl -s -X PATCH "${API}/${ID}" \
  -H "${COOKIE_HEADER}" \
  -H "Content-Type: application/json" \
  -d '{"form_data_patch": {"investment_budget": "50k-150k", "urgency": "inmediata"}}')

HTTP_CODE7=$(curl -s -o /dev/null -w "%{http_code}" -X PATCH "${API}/${ID}" \
  -H "${COOKIE_HEADER}" \
  -H "Content-Type: application/json" \
  -d '{"form_data_patch": {"investment_budget": "50k-150k", "urgency": "inmediata"}}')

if [[ "${HTTP_CODE7}" == "200" ]]; then
  BUDGET=$(echo "${RESPONSE7}" | python3 -c "import sys,json; print(json.load(sys.stdin).get('budget','MISSING'))" 2>/dev/null || echo "(parse error)")
  PRIORITY=$(echo "${RESPONSE7}" | python3 -c "import sys,json; print(json.load(sys.stdin).get('priority_text','MISSING'))" 2>/dev/null || echo "(parse error)")
  FD_BUDGET=$(echo "${RESPONSE7}" | python3 -c "import sys,json; print(json.load(sys.stdin).get('form_data',{}).get('investment_budget','MISSING'))" 2>/dev/null || echo "(parse error)")
  FD_URGENCY=$(echo "${RESPONSE7}" | python3 -c "import sys,json; print(json.load(sys.stdin).get('form_data',{}).get('urgency','MISSING'))" 2>/dev/null || echo "(parse error)")

  if [[ "${BUDGET}" == "50k-150k" ]]; then
    pass "T7 — flat budget synced: ${BUDGET}"
  else
    fail "T7 — flat budget not synced, got: ${BUDGET}"
  fi

  if [[ "${PRIORITY}" == "inmediata" ]]; then
    pass "T7 — flat priority_text synced: ${PRIORITY}"
  else
    fail "T7 — flat priority_text not synced, got: ${PRIORITY}"
  fi

  echo "  form_data.investment_budget = ${FD_BUDGET}"
  echo "  form_data.urgency           = ${FD_URGENCY}"
else
  fail "T7 — expected 200, got ${HTTP_CODE7}"
  echo "  Response: $(echo "${RESPONSE7}" | head -c 300)"
fi

echo ""
echo "====================================================================="
echo " Smoke tests complete."
echo "====================================================================="
echo ""

# ── COMPLETENESS GATE NOTE ─────────────────────────────────────────────────
#
# The completeness gate is FRONTEND-ONLY (no backend endpoint).
# To validate it, use the manual browser checklist in docs/OPERATIONS.md
# (§ Frontend smoke after admin-frontend-independence change), steps 6-8.
#
# Reference: the gate is implemented in:
#   frontend/src/admin/hooks/useAssessmentCompleteness.ts   (logic)
#   frontend/src/admin/components/AssessmentEditor/SparseConfirmDialog.tsx (UI)
#   frontend/src/admin/components/AssessmentEditor/EnrichmentPanel.tsx (wiring)
#   frontend/src/admin/components/AssessmentEditor/ApproveAndSendDialog.tsx (approve path)
#
# A sparse assessment (form_data empty or with very few keys filled) will
# trigger the SparseConfirmDialog before LLM re-run, PDF generation, and
# approval. No backend curl command can exercise this gate directly.
# ──────────────────────────────────────────────────────────────────────────
