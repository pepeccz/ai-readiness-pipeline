// ============================================================
// AI Readiness Assessment — AppScript v2.0 para Zanovix
// Sheet: Formulario In-Take — AI Readiness Assessment (respuestas)
// ID:    1cMZuWl2t3dH_7-6LIKMkXL9S8ueMMKPz69rK_AiZoZ8
//
// ARQUITECTURA DEL SISTEMA:
//   Este script NO llama a ninguna API LLM (sin OpenRouter, sin OpenAI).
//   Su función es: (1) calcular scoring matemático, (2) construir el JSON
//   del assessment, (3) enviar email AIR-ASSESSMENT: a pepe@zanovix.com.
//   Un cron de OpenClaw detecta ese email y lanza un subagente (Claude)
//   que genera los textos del informe y ejecuta pipeline.py localmente.
//
// SETUP (ejecutar una vez):
//   1. Abre el editor AppScript vinculado al sheet
//   2. Pega este código completo (reemplaza todo)
//   3. Ejecuta setupAiReadinessMvpSheets() → crea hojas auxiliares
//   4. Ejecuta installAssessmentEmailTrigger() → instala trigger
//   5. Autoriza los permisos OAuth cuando se soliciten
// ============================================================


// ============================================================
// === ARCHIVO: SetUp.gs ===
// ============================================================

/**
 * Setup principal: crea hojas auxiliares, instala fórmulas y trigger.
 * Ejecutar UNA VEZ manualmente desde el menú.
 */
function setupAiReadinessMvpSheets() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();

  var responseSheet = detectResponseSheet_(ss);
  if (!responseSheet) throw new Error('No se encontró hoja de respuestas del formulario.');

  var analysisSheet    = getOrCreateSheet_(ss, 'analysis');
  var catalogsSheet    = getOrCreateSheet_(ss, 'catalogs');
  var reportSheet      = getOrCreateSheet_(ss, 'report_output');

  setupAnalysisHeaders_(analysisSheet);
  setupReportOutputHeaders_(reportSheet);
  setupCatalogsSheet_(catalogsSheet);

  SpreadsheetApp.flush();

  SpreadsheetApp.getUi().alert(
    '✅ Setup completado.\n\n' +
    'Hoja detectada: "' + responseSheet.getName() + '"\n' +
    'Hojas creadas: analysis, catalogs, report_output\n\n' +
    'Siguiente paso: ejecuta installAssessmentEmailTrigger()'
  );
}

function detectResponseSheet_(ss) {
  var sheets = ss.getSheets();
  // Por form URL
  for (var i = 0; i < sheets.length; i++) {
    try { if (sheets[i].getFormUrl()) return sheets[i]; } catch(e) {}
  }
  // Por nombre
  var patterns = [/^respuestas/i, /^form responses/i, /^respuestas de formulario/i];
  for (var i = 0; i < sheets.length; i++) {
    for (var j = 0; j < patterns.length; j++) {
      if (patterns[j].test(sheets[i].getName())) return sheets[i];
    }
  }
  // Por primera columna
  for (var i = 0; i < sheets.length; i++) {
    var sh = sheets[i];
    if (sh.getLastColumn() < 1) continue;
    var h0 = String(sh.getRange(1,1).getValue()).trim().toLowerCase();
    if (h0 === 'marca temporal' || h0 === 'timestamp') return sh;
  }
  return null;
}

function getOrCreateSheet_(ss, name) {
  return ss.getSheetByName(name) || ss.insertSheet(name);
}

function setupAnalysisHeaders_(sheet) {
  sheet.clearContents();
  var headers = [
    'source_row','assessment_id','access_code','company_name',
    'respondent_name_role','sector','employee_range','revenue_range','operating_region',
    // scoring pts
    'pts_tools','pts_automation','pts_area_usage','pts_governance','pts_goal_clarity',
    'maturity_score','maturity_level',
    'pts_data_risk','pts_ai_personal_data','pts_dpa','pts_dpia',
    'pts_automated_decisions','pts_sector','pts_incident',
    'risk_score','risk_level',
    'deal_fit_score','deal_fit_level',
    'top_gaps','top_opportunities','recommended_next_step','internal_summary',
    // campos raw para LLM
    'tools_used','chatbot_desc','custom_ai_desc',
    'process_to_improve','proceso_personas','proceso_horas',
    'proceso_dato_input','sistemas_existentes','proceso_falla','proceso_resultado_esperado',
    'data_types','data_in_ai','dpa','eipd','auto_decisions',
    'ai_act','high_risk','incident','incident_desc',
    'politica_ia','formacion_ia',
    'concerns','goals_12m','main_pain','hours_lost','priority','budget','proceso_urgencia',
    'who_decides','previous_consultancy','previous_experience','additional_context',
    'llm_input_json','processed_at'
  ];
  sheet.getRange(1, 1, 1, headers.length).setValues([headers]).setFontWeight('bold');
  sheet.setFrozenRows(1);
}

function setupReportOutputHeaders_(sheet) {
  sheet.clearContents();
  var headers = [
    'assessment_id','company_name','access_code','sector','employee_range',
    'maturity_score','maturity_level','risk_score','risk_level',
    'deal_fit_score','deal_fit_level',
    'top_gaps','top_opportunities','recommended_next_step','internal_summary',
    'llm_input_json',
    'llm_executive_summary','llm_current_state','llm_risk_findings',
    'llm_opportunities','llm_roadmap_30_60_90','llm_final_recommendation',
    'llm_scoring_answers',
    'drive_url','deck_url','processed_at','review_status','last_updated'
  ];
  sheet.getRange(1, 1, 1, headers.length).setValues([headers]).setFontWeight('bold');
  sheet.setFrozenRows(1);
}

function setupCatalogsSheet_(sheet) {
  sheet.clearContents();
  sheet.getRange('A1').setValue('catalogs — pesos de scoring');
  var rows = [
    ['Criterio','Peso máximo','Tipo'],
    ['pts_tools',20,'madurez'],
    ['pts_automation',20,'madurez'],
    ['pts_area_usage',25,'madurez'],
    ['pts_governance',20,'madurez'],
    ['pts_goal_clarity',15,'madurez'],
    ['pts_data_risk',30,'riesgo'],
    ['pts_ai_personal_data',15,'riesgo'],
    ['pts_dpa',15,'riesgo'],
    ['pts_dpia',15,'riesgo'],
    ['pts_automated_decisions',15,'riesgo'],
    ['pts_sector',5,'riesgo'],
    ['pts_incident',5,'riesgo'],
  ];
  sheet.getRange(2, 1, rows.length, 3).setValues(rows);
}


// ============================================================
// === ARCHIVO: Code.gs ===
// ============================================================

/**
 * Trigger principal de formulario.
 * Se instala con installAssessmentEmailTrigger() como onFormSubmit.
 */
function onFormSubmit(e) {
  try {
    processLatestFormResponseToAnalysis_();
  } catch(err) {
    Logger.log('Error en onFormSubmit: ' + err.message);
  }
}

function processLatestFormResponseToAnalysis_() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var responseSheet = detectResponseSheet_(ss);
  var analysisSheet = ss.getSheetByName('analysis');
  if (!responseSheet) throw new Error('No se encontró hoja de respuestas.');
  if (!analysisSheet) throw new Error('No existe hoja analysis. Ejecuta setupAiReadinessMvpSheets() primero.');
  var lastRow = responseSheet.getLastRow();
  if (lastRow < 2) return;
  processRow_(ss, responseSheet, analysisSheet, lastRow);
}

function backfillAllResponsesToAnalysis() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var responseSheet = detectResponseSheet_(ss);
  var analysisSheet = ss.getSheetByName('analysis');
  if (!responseSheet || !analysisSheet) throw new Error('Ejecuta setupAiReadinessMvpSheets() primero.');
  var total = responseSheet.getLastRow();
  for (var i = 2; i <= total; i++) {
    try { processRow_(ss, responseSheet, analysisSheet, i); }
    catch(e) { Logger.log('Fila ' + i + ' error: ' + e.message); }
  }
}

/**
 * Procesa una fila de respuestas → calcula scoring → escribe en analysis → envía email.
 */
function processRow_(ss, responseSheet, analysisSheet, sourceRow) {
  var vals = responseSheet.getRange(sourceRow, 1, 1, Math.max(responseSheet.getLastColumn(), 50)).getValues()[0];

  // Helper: columna 1-indexed → índice 0-based
  var col = function(n) { return String(vals[n-1] || '').trim(); };

  // ── Campos básicos (nuevo formulario v2) ──
  var access_code    = col(2);   // B — Codigo de acceso
  var sector         = col(3);   // C
  var employees      = col(4);   // D
  var revenue        = col(5);   // E
  var region         = col(6);   // F
  var respondent     = col(7);   // G
  var tools          = col(8);   // H
  var auto_system    = col(9);   // I
  var chatbot        = col(10);  // J
  var chatbot_desc   = col(11);  // K
  var custom_ai      = col(12);  // L
  var custom_ai_desc = col(13);  // M

  // ── Áreas N-T (cols 14-20) ──
  var areas = [col(14),col(15),col(16),col(17),col(18),col(19),col(20)];

  var area_potential = col(21);  // U
  var process_improve = col(22); // V
  var proc_people    = col(23);  // W
  var proc_hours     = col(24);  // X
  var proc_input     = col(25);  // Y
  var systems        = col(26);  // Z
  var proc_fail      = col(27);  // AA
  var proc_goal      = col(28);  // AB
  var data_types     = col(29);  // AC
  var data_in_ai     = col(30);  // AD
  var eipd           = col(31);  // AE
  var auto_dec       = col(32);  // AF
  var incident       = col(33);  // AG
  var incident_desc  = col(34);  // AH
  var ai_act         = col(35);  // AI
  var high_risk      = col(36);  // AJ
  var concerns       = col(37);  // AK
  var goals_12m      = col(38);  // AL
  var main_pain      = col(39);  // AM
  var hours_lost     = col(40);  // AN
  var priority       = col(41);  // AO
  var who_decides    = col(42);  // AP
  var prev_cons      = col(43);  // AQ
  var prev_exp       = col(44);  // AR
  var extra_ctx      = col(45);  // AS
  var dpa            = col(46);  // AT
  var ai_policy      = col(47);  // AU
  var ai_training    = col(48);  // AV
  var budget         = col(49);  // AW
  var proc_urgency   = col(50);  // AX

  // ── Obtener company_name de Notion si es posible ──
  var company_name = getCompanyFromNotion_(access_code) || access_code || 'Empresa';

  // ── Assessment ID ──
  var assessment_id = 'AIR-' + Utilities.formatDate(new Date(), 'Europe/Madrid', 'yyyyMMdd')
    + '-' + access_code.replace(/[^A-Z0-9]/gi, '').toLowerCase().slice(-6);

  // ── SCORING ──
  var scored = computeScores_(
    tools, auto_system, chatbot, custom_ai, areas,
    process_improve, goals_12m,
    data_types, data_in_ai, dpa, eipd, auto_dec, sector, incident,
    ai_act, ai_policy, ai_training,
    priority, budget
  );

  // ── top_gaps / top_opportunities / internal_summary ──
  var top_gaps = buildTopGaps_(scored, data_types, dpa, eipd, auto_dec, ai_act);
  var top_opps = buildTopOpportunities_(process_improve, tools, chatbot, custom_ai, sectors);
  var next_step = scored.deal_fit_score >= 70 && priority.toLowerCase().includes('alta')
    ? 'Propuesta proyecto IA en 48h — encaje excelente'
    : scored.deal_fit_score >= 45
      ? 'Assessment OK, proponer discovery técnico esta semana'
      : 'Enviar informe estándar, no priorizar seguimiento inmediato';
  var internal_summary = 'Madurez: ' + scored.maturity_score + ' (' + scored.maturity_level + ') | '
    + 'Riesgo: ' + scored.risk_score + ' (' + scored.risk_level + ') | '
    + 'Deal fit: ' + scored.deal_fit_score + ' (' + scored.deal_fit_level + ')';

  // ── Construir rec para JSON ──
  var rec = {
    assessment_id:           assessment_id,
    access_code:             access_code,
    company_name:            company_name,
    respondent_name_role:    respondent,
    sector:                  sector,
    employee_range:          employees,
    revenue_range:           revenue,
    operating_region:        region,
    maturity_score:          scored.maturity_score,
    maturity_level:          scored.maturity_level,
    risk_score:              scored.risk_score,
    risk_level:              scored.risk_level,
    priority_score:          scored.priority_score,
    priority_level:          scored.priority_level,
    deal_fit_score:          scored.deal_fit_score,
    deal_fit_level:          scored.deal_fit_level,
    top_gaps:                top_gaps,
    top_opportunities:       top_opps,
    recommended_next_step:   next_step,
    internal_summary:        internal_summary,
    // scoring pts
    pts_tools:               scored.pts.pts_tools,
    pts_automation:          scored.pts.pts_automation,
    pts_area_usage:          scored.pts.pts_area_usage,
    pts_governance:          scored.pts.pts_governance,
    pts_goal_clarity:        scored.pts.pts_goal_clarity,
    pts_data_risk:           scored.pts.pts_data_risk,
    pts_ai_personal_data:    scored.pts.pts_ai_personal_data,
    pts_dpa:                 scored.pts.pts_dpa,
    pts_dpia:                scored.pts.pts_dpia,
    pts_automated_decisions: scored.pts.pts_automated_decisions,
    pts_sector:              scored.pts.pts_sector,
    pts_incident:            scored.pts.pts_incident,
    // campos cualitativos para LLM
    tools_used:              tools,
    chatbot_desc:            chatbot_desc,
    custom_ai_desc:          custom_ai_desc,
    process_to_improve:      process_improve,
    proceso_personas:        proc_people,
    proceso_horas:           proc_hours,
    proceso_dato_input:      proc_input,
    sistemas_existentes:     systems,
    proceso_falla:           proc_fail,
    proceso_resultado_esperado: proc_goal,
    proceso_urgencia:        proc_urgency,
    data_types:              data_types,
    data_in_ai:              data_in_ai,
    dpa:                     dpa,
    eipd:                    eipd,
    auto_decisions:          auto_dec,
    ai_act:                  ai_act,
    high_risk:               high_risk,
    incident:                incident,
    incident_desc:           incident_desc,
    politica_ia:             ai_policy,
    formacion_ia:            ai_training,
    concerns:                concerns,
    goals_12m:               goals_12m,
    main_pain:               main_pain,
    hours_lost:              hours_lost,
    priority:                priority,
    budget:                  budget,
    who_decides:             who_decides,
    previous_consultancy:    prev_cons,
    previous_experience:     prev_exp,
    additional_context:      extra_ctx
  };
  var llm_input_json = JSON.stringify(rec);

  // ── Escribir en analysis ──
  var aSheet = ss.getSheetByName('analysis');
  var aHeaders = aSheet.getRange(1, 1, 1, aSheet.getLastColumn()).getValues()[0];
  var aMap = {};
  aHeaders.forEach(function(h, i) { aMap[h] = i + 1; });

  var aRow = aSheet.getLastRow() + 1;
  var setA = function(field, val) {
    var idx = aMap[field];
    if (idx) aSheet.getRange(aRow, idx).setValue(val);
  };

  setA('source_row', sourceRow);
  setA('assessment_id', assessment_id);
  setA('access_code', access_code);
  setA('company_name', company_name);
  setA('respondent_name_role', respondent);
  setA('sector', sector);
  setA('employee_range', employees);
  setA('revenue_range', revenue);
  setA('operating_region', region);
  setA('pts_tools', scored.pts.pts_tools);
  setA('pts_automation', scored.pts.pts_automation);
  setA('pts_area_usage', scored.pts.pts_area_usage);
  setA('pts_governance', scored.pts.pts_governance);
  setA('pts_goal_clarity', scored.pts.pts_goal_clarity);
  setA('maturity_score', scored.maturity_score);
  setA('maturity_level', scored.maturity_level);
  setA('pts_data_risk', scored.pts.pts_data_risk);
  setA('pts_ai_personal_data', scored.pts.pts_ai_personal_data);
  setA('pts_dpa', scored.pts.pts_dpa);
  setA('pts_dpia', scored.pts.pts_dpia);
  setA('pts_automated_decisions', scored.pts.pts_automated_decisions);
  setA('pts_sector', scored.pts.pts_sector);
  setA('pts_incident', scored.pts.pts_incident);
  setA('risk_score', scored.risk_score);
  setA('risk_level', scored.risk_level);
  setA('priority_score', scored.priority_score);
  setA('priority_level', scored.priority_level);
  setA('deal_fit_score', scored.deal_fit_score);
  setA('deal_fit_level', scored.deal_fit_level);
  setA('top_gaps', top_gaps);
  setA('top_opportunities', top_opps);
  setA('recommended_next_step', next_step);
  setA('internal_summary', internal_summary);
  setA('tools_used', tools);
  setA('process_to_improve', process_improve);
  setA('proceso_personas', proc_people);
  setA('proceso_horas', proc_hours);
  setA('sistemas_existentes', systems);
  setA('proceso_falla', proc_fail);
  setA('goals_12m', goals_12m);
  setA('main_pain', main_pain);
  setA('priority', priority);
  setA('budget', budget);
  setA('dpa', dpa);
  setA('politica_ia', ai_policy);
  setA('formacion_ia', ai_training);
  setA('llm_input_json', llm_input_json);
  setA('processed_at', new Date().toISOString());

  // ── Escribir en report_output ──
  writeToReportOutput_(ss, rec, llm_input_json);

  Logger.log('✅ Procesado: ' + assessment_id + ' | ' + company_name);
}

function writeToReportOutput_(ss, rec, llm_input_json) {
  var sheet = ss.getSheetByName('report_output');
  if (!sheet) return;
  var headers = sheet.getRange(1, 1, 1, sheet.getLastColumn()).getValues()[0];
  var map = {};
  headers.forEach(function(h, i) { map[h] = i + 1; });

  var row = sheet.getLastRow() + 1;
  var set = function(field, val) {
    var idx = map[field];
    if (idx) sheet.getRange(row, idx).setValue(val);
  };

  set('assessment_id', rec.assessment_id);
  set('company_name', rec.company_name);
  set('access_code', rec.access_code);
  set('sector', rec.sector);
  set('employee_range', rec.employee_range);
  // pts_* individuales — necesarios para que pipeline.py construya tablas trazables
  // sin tener que recalcular ni divergir del score del AppScript
  set('pts_tools', rec.pts_tools);
  set('pts_automation', rec.pts_automation);
  set('pts_area_usage', rec.pts_area_usage);
  set('pts_governance', rec.pts_governance);
  set('pts_goal_clarity', rec.pts_goal_clarity);
  set('maturity_score', rec.maturity_score);
  set('maturity_level', rec.maturity_level);
  set('pts_data_risk', rec.pts_data_risk);
  set('pts_ai_personal_data', rec.pts_ai_personal_data);
  set('pts_dpa', rec.pts_dpa);
  set('pts_dpia', rec.pts_dpia);
  set('pts_automated_decisions', rec.pts_automated_decisions);
  set('pts_sector', rec.pts_sector);
  set('pts_incident', rec.pts_incident);
  set('risk_score', rec.risk_score);
  set('risk_level', rec.risk_level);
  set('priority_score', rec.priority_score);
  set('priority_level', rec.priority_level);
  set('deal_fit_score', rec.deal_fit_score);
  set('deal_fit_level', rec.deal_fit_level);
  set('top_gaps', rec.top_gaps);
  set('top_opportunities', rec.top_opportunities);
  set('recommended_next_step', rec.recommended_next_step);
  set('internal_summary', rec.internal_summary);
  set('llm_input_json', llm_input_json);
  set('review_status', 'pending');
  set('last_updated', new Date().toISOString());
}


// ============================================================
// === ARCHIVO: Engine.gs ===
// ============================================================

/**
 * Calcula todos los scores a partir de los valores del formulario.
 */
function computeScores_(tools, auto_system, chatbot, custom_ai, areas,
                         process_improve, goals_12m,
                         data_types, data_in_ai, dpa, eipd, auto_dec, sector, incident,
                         ai_act, ai_policy, ai_training,
                         priority, budget) {
  var tl = function(s) { return String(s||'').toLowerCase(); };

  // ── MADUREZ ──

  // pts_tools (0-20): contar herramientas (separadas por coma)
  var pts_tools = 0;
  var ttools = tl(tools);
  if (ttools.includes('no utilizamos') || ttools === '') {
    pts_tools = 0;
  } else {
    var count = (tools.match(/,/g) || []).length + 1;
    pts_tools = count >= 5 ? 20 : count >= 3 ? 12 : 6;
  }

  // pts_automation (0-20): tomar el máximo entre chatbot/custom/auto_system
  var pts_automation = 0;
  if (tl(custom_ai).includes('si')) pts_automation = 20;
  else if (tl(chatbot).includes('si')) pts_automation = 14;
  else if (tl(auto_system).includes('si') && !tl(auto_system).includes('no')) pts_automation = 8;

  // pts_area_usage (0-25): suma de 7 áreas escalada
  var areaRaw = 0;
  for (var i = 0; i < areas.length; i++) {
    var a = tl(areas[i]);
    if (a.includes('integrada')) areaRaw += 4;
    else if (a.includes('automatizado') || a.includes('chatbot')) areaRaw += 2;
    else if (a.includes('genericas') || a.includes('individual')) areaRaw += 1;
  }
  var pts_area_usage = Math.min(25, Math.round(areaRaw * 25 / 28));

  // pts_governance (0-20)
  var pts_governance = 0;
  if (tl(ai_act).includes('bastante')) pts_governance += 5;
  else if (tl(ai_act).includes('oido') || tl(ai_act).includes('oído')) pts_governance += 2;
  if (tl(ai_policy).includes('documentada')) pts_governance += 8;
  else if (tl(ai_policy).includes('informal')) pts_governance += 4;
  if (tl(ai_training).includes('formal')) pts_governance += 7;
  else if (tl(ai_training).includes('informal')) pts_governance += 4;
  pts_governance = Math.min(20, pts_governance);

  // pts_goal_clarity (0-15)
  var pts_goal_clarity = 0;
  var plen = String(process_improve || '').length;
  var glen = String(goals_12m || '').length;
  if (plen > 50) pts_goal_clarity += 10;
  else if (plen > 20) pts_goal_clarity += 6;
  if (glen > 30) pts_goal_clarity += 5;
  pts_goal_clarity = Math.min(15, pts_goal_clarity);

  var maturity_score = pts_tools + pts_automation + pts_area_usage + pts_governance + pts_goal_clarity;
  var maturity_level = maturity_score >= 85 ? 'Avanzada'
    : maturity_score >= 70 ? 'Operativa'
    : maturity_score >= 50 ? 'En adopción'
    : maturity_score >= 30 ? 'Inicial'
    : 'Muy inicial';

  // ── RIESGO ──

  // pts_data_risk (0-30)
  var pts_data_risk = 0;
  var dtl = tl(data_types);
  if (dtl.includes('menores') || dtl.includes('biometrico') || dtl.includes('biométrico')) pts_data_risk = 30;
  else if (dtl.includes('salud') || dtl.includes('financiero') || dtl.includes('bancario')) pts_data_risk = 25;
  else if (dtl.includes('empleado')) pts_data_risk = 15;
  else if (dtl.includes('cliente')) pts_data_risk = 10;

  // pts_ai_personal_data (0-15)
  var pts_ai_personal_data = tl(data_in_ai).startsWith('sí') || tl(data_in_ai).startsWith('si') ? 15 : 0;

  // pts_dpa (0-15)
  var pts_dpa = 0;
  var tdpa = tl(dpa);
  if (tdpa.includes('no se') || tdpa.includes('no sé') || (tdpa.startsWith('no') && !tdpa.includes('algunos'))) pts_dpa = 15;
  else if (tdpa.includes('algunos')) pts_dpa = 8;

  // pts_dpia (0-15)
  var pts_dpia = 0;
  var teipd = tl(eipd);
  if (teipd.includes('no se') || teipd.includes('no sé') || teipd.startsWith('no')) pts_dpia = 15;

  // pts_automated_decisions (0-15)
  var pts_automated_decisions = (tl(auto_dec).startsWith('sí') || tl(auto_dec).startsWith('si')) ? 15 : 0;

  // pts_sector (0-5)
  var pts_sector = 0;
  var sl = tl(sector);
  if (sl.includes('salud') || sl.includes('finanzas') || sl.includes('seguros')) pts_sector = 5;

  // pts_incident (0-5)
  var pts_incident = (tl(incident).startsWith('sí') || tl(incident).startsWith('si')) ? 5 : 0;

  var risk_score = pts_data_risk + pts_ai_personal_data + pts_dpa + pts_dpia
    + pts_automated_decisions + pts_sector + pts_incident;
  var risk_level = risk_score >= 75 ? 'Muy alto'
    : risk_score >= 50 ? 'Alto'
    : risk_score >= 25 ? 'Medio'
    : 'Bajo';

  // ── PRIORIDAD / URGENCIA (visible en el doc cliente) ──
  // Mide la urgencia operativa del cliente: cuánto les duele ahora y con qué prisa quieren actuar.
  // Escala 0-100. No incluye métricas comerciales internas.
  var priority_score = 0;
  // Prioridad declarada (hasta 35 pts)
  if (tl(priority).includes('alta')) priority_score += 35;
  else if (tl(priority).includes('media')) priority_score += 20;
  else if (tl(priority).includes('baja')) priority_score += 5;
  // Horas perdidas semanalmente (hasta 30 pts)
  var hl = tl(hours_lost);
  if (hl.includes('más de 20') || hl.includes('mas de 20')) priority_score += 30;
  else if (hl.includes('10') || hl.includes('15') || hl.includes('entre 10')) priority_score += 20;
  else if (hl.includes('5') || hl.includes('entre 5')) priority_score += 10;
  else if (hl.includes('menos')) priority_score += 5;
  // Urgencia temporal del proceso (hasta 20 pts)
  var proc_urg = tl(proc_urgency);
  if (proc_urg.includes('sí') || proc_urg.includes('si')) priority_score += 20;
  else if (proc_urg.includes('temporada') || proc_urg.includes('verano') || proc_urg.includes('navidad')) priority_score += 15;
  // Riesgo regulatorio activo eleva urgencia (hasta 15 pts)
  if (risk_score >= 75) priority_score += 15;
  else if (risk_score >= 50) priority_score += 10;
  else if (risk_score >= 25) priority_score += 5;

  priority_score = Math.min(100, priority_score);
  var priority_level = priority_score >= 80 ? 'Muy urgente'
    : priority_score >= 60 ? 'Urgente'
    : priority_score >= 40 ? 'Moderada'
    : 'Baja';

  // ── DEAL FIT (interno, no sale en doc cliente) ──
  var deal_fit = 0;
  if (tl(priority).includes('alta')) deal_fit += 30;
  else if (tl(priority).includes('media')) deal_fit += 15;
  var tb = tl(budget);
  if (tb.includes('10000') || tb.includes('más de') || tb.includes('mas de')) deal_fit += 30;
  else if (tb.includes('3000') || tb.includes('entre')) deal_fit += 20;
  else if (tb.includes('calcular')) deal_fit += 15;
  deal_fit += Math.min(20, Math.round(maturity_score / 5));
  deal_fit += Math.min(20, Math.round(risk_score / 5));
  deal_fit = Math.min(100, deal_fit);

  var deal_fit_level = deal_fit >= 70 ? 'Prioritario'
    : deal_fit >= 45 ? 'Interesante'
    : deal_fit >= 20 ? 'A evaluar'
    : 'Bajo potencial';

  return {
    maturity_score: maturity_score, maturity_level: maturity_level,
    risk_score: risk_score, risk_level: risk_level,
    priority_score: priority_score, priority_level: priority_level,
    deal_fit_score: deal_fit, deal_fit_level: deal_fit_level,
    pts: {
      pts_tools: pts_tools, pts_automation: pts_automation,
      pts_area_usage: pts_area_usage, pts_governance: pts_governance,
      pts_goal_clarity: pts_goal_clarity,
      pts_data_risk: pts_data_risk, pts_ai_personal_data: pts_ai_personal_data,
      pts_dpa: pts_dpa, pts_dpia: pts_dpia,
      pts_automated_decisions: pts_automated_decisions,
      pts_sector: pts_sector, pts_incident: pts_incident
    }
  };
}

function buildTopGaps_(scored, data_types, dpa, eipd, auto_dec, ai_act) {
  var gaps = [];
  var tl = function(s) { return String(s||'').toLowerCase(); };
  if (scored.pts.pts_dpa > 0) gaps.push('Sin DPA formalizado con proveedores (RGPD art.28)');
  if (scored.pts.pts_dpia > 0) gaps.push('Sin EIPD/DPIA realizada (RGPD arts.9+35)');
  if (scored.pts.pts_ai_personal_data > 0 && scored.pts.pts_dpa > 0)
    gaps.push('Datos personales en sistemas IA sin contratos de encargo');
  if (scored.pts.pts_governance < 10) gaps.push('Sin política interna de IA ni formación del equipo');
  if (!tl(ai_act).includes('bastante')) gaps.push('Desconocimiento del EU AI Act — riesgo de incumplimiento');
  if (scored.pts.pts_tools < 10) gaps.push('Adopción de herramientas IA muy baja — potencial sin explotar');
  return gaps.slice(0, 4).join(' | ');
}

function buildTopOpportunities_(process_improve, tools, chatbot, custom_ai) {
  var opps = [];
  var tl = function(s) { return String(s||'').toLowerCase(); };
  if (process_improve && process_improve.length > 10) opps.push('Automatización de: ' + process_improve.slice(0,60));
  if (!tl(chatbot).includes('si') && !tl(custom_ai).includes('si'))
    opps.push('Implementar asistente/chatbot para atención o consultas frecuentes');
  if (tl(tools).includes('chatgpt') && !tl(custom_ai).includes('si'))
    opps.push('Estructurar uso de ChatGPT en workflows reales con prompts definidos');
  opps.push('Compliance IA: DPA + política interna de uso (bajo coste, alto impacto)');
  return opps.slice(0, 3).join(' | ');
}

/**
 * Consulta la BD Assessments de Notion para obtener el company_name
 * a partir del código de acceso.
 * Si falla (sin internet, token expirado, etc.) devuelve null silenciosamente.
 */
function getCompanyFromNotion_(accessCode) {
  if (!accessCode) return null;
  try {
    var NOTION_KEY_PROP = 'NOTION_API_KEY';
    var notionKey = PropertiesService.getScriptProperties().getProperty(NOTION_KEY_PROP);
    if (!notionKey) return null;

    var ASS_DB = '33118d57-3b10-81d3-a7a0-c56f70f41853';
    var response = UrlFetchApp.fetch('https://api.notion.com/v1/databases/' + ASS_DB + '/query', {
      method: 'post',
      headers: {
        'Authorization': 'Bearer ' + notionKey,
        'Notion-Version': '2022-06-28',
        'Content-Type': 'application/json'
      },
      payload: JSON.stringify({ page_size: 100 }),
      muteHttpExceptions: true
    });

    if (response.getResponseCode() !== 200) return null;
    var pages = JSON.parse(response.getContentText()).results || [];

    for (var i = 0; i < pages.length; i++) {
      var props = pages[i].properties || {};
      var rt = (props['Codigo acceso'] || {}).rich_text || [];
      var stored = rt.length ? rt[0].plain_text : '';
      if (stored.toUpperCase() === accessCode.toUpperCase()) {
        // Buscar empresa via relación Cliente
        var rel = (props['Cliente'] || {}).relation || [];
        if (rel.length) {
          var clientePage = UrlFetchApp.fetch('https://api.notion.com/v1/pages/' + rel[0].id, {
            headers: {
              'Authorization': 'Bearer ' + notionKey,
              'Notion-Version': '2022-06-28'
            },
            muteHttpExceptions: true
          });
          if (clientePage.getResponseCode() === 200) {
            var cp = JSON.parse(clientePage.getContentText());
            var title = ((cp.properties || {})['Empresa'] || {}).title || [];
            if (title.length) return title[0].plain_text;
          }
        }
      }
    }
  } catch(e) {
    Logger.log('getCompanyFromNotion_ error: ' + e.message);
  }
  return null;
}

/** Configurar Notion API key (ejecutar una vez) */
function setNotionKey() {
  PropertiesService.getScriptProperties().setProperty('NOTION_API_KEY', 'PEGAR_AQUI_LA_KEY');
  SpreadsheetApp.getUi().alert('Notion API key guardada.');
}


// ============================================================
// === ARCHIVO: EmailTrigger.gs ===
// ============================================================

// ── Webhook config (usar Script Properties para no hardcodear IP) ───────────────
// Se configura via setWebhookConfig() o PropertiesService

function getWebhookConfig_() {
  var props = PropertiesService.getScriptProperties();
  var url = props.getProperty('WEBHOOK_URL');
  var token = props.getProperty('WEBHOOK_TOKEN');
  
  // Fallback — configurar via setWebhookConfig() o Script Properties
  if (!url) url = 'https://air.zanovix.com/assessment';
  if (!token) token = '';
  
  return { url: url, token: token };
}

function setWebhookConfig(url, token) {
  var props = PropertiesService.getScriptProperties();
  props.setProperty('WEBHOOK_URL', url);
  props.setProperty('WEBHOOK_TOKEN', token);
  SpreadsheetApp.getUi().alert('✅ Webhook configurado:\nURL: ' + url);
}

// ─────────────────────────────────────────────────────────────────────────────────

/**
 * Se ejecuta tras cada envío del formulario.
 * Lee la última fila de report_output y llama al webhook del servidor Zanovix.
 * El servidor lanza pipeline.py directamente (sin pasar por email).
 *
 * Fallback: si el webhook falla, envía email como antes (retrocompatibilidad).
 */
function onFormSubmitEmailAssessment(e) {
  try {
    // Esperar a que las fórmulas y processRow_ terminen
    Utilities.sleep(4000);

    var ss = SpreadsheetApp.getActiveSpreadsheet();
    var sheet = ss.getSheetByName('report_output');
    if (!sheet) return;

    var lastRow = findLastDataRow_(sheet, 1);
    if (lastRow < 2) return;

    var headers = sheet.getRange(1, 1, 1, sheet.getLastColumn()).getValues()[0];
    var values  = sheet.getRange(lastRow, 1, 1, sheet.getLastColumn()).getValues()[0];
    var rec = {};
    headers.forEach(function(h, i) { rec[h] = values[i]; });

    if (!rec['assessment_id'] || !rec['llm_input_json']) return;

    var company = rec['company_name'] || rec['access_code'] || 'Empresa';

    // Construir payload a partir del JSON del assessment
    var payload;
    try {
      payload = JSON.parse(rec['llm_input_json']);
    } catch(parseErr) {
      payload = { raw: rec['llm_input_json'] };
    }

    // ── Intentar webhook con retry exponencial ────────────────────────────────
    var webhookConfig = getWebhookConfig_();
    var webhookOk = false;
    var maxRetries = 3;
    var baseDelay = 2000; // 2 segundos

    for (var attempt = 1; attempt <= maxRetries; attempt++) {
      try {
        Logger.log('📤 Webhook intento ' + attempt + '/' + maxRetries + ' a ' + webhookConfig.url);
        
        var response = UrlFetchApp.fetch(webhookConfig.url, {
          method: 'post',
          contentType: 'application/json',
          headers: { 'Authorization': 'Bearer ' + webhookConfig.token },
          payload: JSON.stringify(payload),
          muteHttpExceptions: true,
          deadline: 15
        });
        
        var code = response.getResponseCode();
        
        if (code === 202) {
          webhookOk = true;
          Logger.log('✅ Webhook OK (202): pipeline lanzado para ' + company);
          break;
        } else if (code >= 500 && attempt < maxRetries) {
          // Error服务器, hacer retry
          var delay = baseDelay * Math.pow(2, attempt - 1);
          Logger.log('⚠️ Webhook error ' + code + ', retry en ' + delay + 'ms');
          Utilities.sleep(delay);
        } else {
          Logger.log('⚠️ Webhook respondió ' + code + ': ' + response.getContentText().substring(0, 200));
          if (code < 500) break; // Error cliente, no reintentar
        }
        
      } catch(webhookErr) {
        Logger.log('⚠️ Webhook intento ' + attempt + ' error: ' + webhookErr.message);
        if (attempt < maxRetries) {
          var delay = baseDelay * Math.pow(2, attempt - 1);
          Utilities.sleep(delay);
        }
      }
    }

    // ── Fallback: email si el webhook falló después de todos los intentos ───────
    if (!webhookOk) {
      Logger.log('↩️ Fallback a email para ' + company);
      var subject = 'AIR-ASSESSMENT: ' + rec['assessment_id'] + ' | ' + company;
      var body = 'Nuevo AI Readiness Assessment recibido (fallback email — webhook falló).\n\n'
        + 'Empresa: ' + company + '\n'
        + 'Codigo acceso: ' + (rec['access_code'] || '-') + '\n'
        + 'Assessment ID: ' + rec['assessment_id'] + '\n'
        + 'Madurez: ' + rec['maturity_score'] + '/100 (' + rec['maturity_level'] + ')\n'
        + 'Riesgo: ' + rec['risk_score'] + '/100 (' + rec['risk_level'] + ')\n'
        + '──── JSON DEL ASSESSMENT (no borrar) ────\n'
        + rec['llm_input_json'] + '\n'
        + '──── FIN JSON ────\n';
      GmailApp.sendEmail('pepe@zanovix.com', subject, body);
      Logger.log('✅ Email fallback enviado: ' + subject);
    }

  } catch(err) {
    Logger.log('Error en onFormSubmitEmailAssessment: ' + err.message);
  }
}

/**
 * Instala el trigger correcto. Ejecutar UNA VEZ manualmente.
 */
function installAssessmentEmailTrigger() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();

  // Eliminar duplicados
  ScriptApp.getProjectTriggers().forEach(function(t) {
    if (t.getHandlerFunction() === 'onFormSubmitEmailAssessment' ||
        t.getHandlerFunction() === 'onFormSubmit') {
      ScriptApp.deleteTrigger(t);
    }
  });

  // Trigger principal: procesar datos
  ScriptApp.newTrigger('onFormSubmit')
    .forSpreadsheet(ss)
    .onFormSubmit()
    .create();

  // Trigger de email: enviar notificación (con delay de 5s para que procese primero)
  ScriptApp.newTrigger('onFormSubmitEmailAssessment')
    .forSpreadsheet(ss)
    .onFormSubmit()
    .create();

  SpreadsheetApp.getUi().alert(
    '✅ Triggers instalados.\n\n'
    + 'Cada nuevo assessment:\n'
    + '  1. Se procesa automáticamente (scoring)\n'
    + '  2. Se envía email AIR-ASSESSMENT: a pepe@zanovix.com\n'
    + '  3. OpenClaw genera el informe y la presentación\n\n'
    + 'Cron OpenClaw ID: 54215d5d-cb92-493e-b3b7-2f0dfa3bdfc3'
  );
}

// Helper
function findLastDataRow_(sheet, col) {
  var data = sheet.getRange(1, col, sheet.getLastRow(), 1).getValues();
  for (var i = data.length - 1; i >= 0; i--) {
    if (data[i][0] !== '') return i + 1;
  }
  return 1;
}


// ============================================================
// === ARCHIVO: ReportGen.gs ===
// ============================================================

/**
 * Menú de la hoja para acciones manuales.
 */
function onOpen() {
  SpreadsheetApp.getUi()
    .createMenu('AI Readiness')
    .addItem('▶ Setup completo', 'setupAiReadinessMvpSheets')
    .addItem('⚡ Instalar triggers', 'installAssessmentEmailTrigger')
    .addSeparator()
    .addItem('🔄 Reprocesar último assessment', 'reprocessLatest')
    .addItem('📊 Backfill todas las respuestas', 'backfillAllResponsesToAnalysis')
    .addSeparator()
    .addItem('🔑 Configurar Notion API Key', 'setNotionKey')
    .addToUi();
}

/**
 * Reprocesa manualmente la última fila para testing.
 */
function reprocessLatest() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var responseSheet = detectResponseSheet_(ss);
  var analysisSheet = ss.getSheetByName('analysis');
  if (!responseSheet || !analysisSheet) {
    SpreadsheetApp.getUi().alert('Ejecuta Setup completo primero.');
    return;
  }
  var lastRow = responseSheet.getLastRow();
  if (lastRow < 2) {
    SpreadsheetApp.getUi().alert('No hay respuestas todavía.');
    return;
  }
  processRow_(ss, responseSheet, analysisSheet, lastRow);
  SpreadsheetApp.getUi().alert('✅ Fila ' + lastRow + ' procesada. Revisa analysis y report_output.');
}

/**
 * Test de envío de email para verificar que el sistema funciona.
 */
function testEmailTrigger() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  GmailApp.sendEmail('pepe@zanovix.com',
    'AIR-ASSESSMENT: TEST-' + Date.now() + ' | Test Company',
    'Este es un email de prueba del sistema AI Readiness.\n\n'
    + '──── JSON DEL ASSESSMENT (no borrar) ────\n'
    + JSON.stringify({assessment_id: 'TEST-001', company_name: 'Test Company', maturity_score: 33, risk_score: 50}) + '\n'
    + '──── FIN JSON ────'
  );
  SpreadsheetApp.getUi().alert('✅ Email de test enviado a pepe@zanovix.com');
}
