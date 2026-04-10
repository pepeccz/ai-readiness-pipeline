"""
Scoring Engine — AI Readiness Assessment
Construye las tablas de scoring trazables a partir de los pts_* reales del JSON.
Los números vienen del sheet (calculados por fórmulas). El LLM solo aporta texto descriptivo.
"""

# ─── Criterios fijos de Madurez ─────────────────────────────────────────────
# Peso total: 100. Fuente: catalogs!WEIGHTS del sheet.
MATURITY_CRITERIA = [
    {
        'key':   'pts_tools',
        'label': 'Herramientas de IA activas',
        'max':   20,
        'desc':  {
            '20': 'Uso habitual de 5+ herramientas de IA',
            '12': 'Uso habitual de 3-4 herramientas de IA',
            '6':  'Uso de 1-2 herramientas de IA',
            '0':  'Sin herramientas de IA en uso',
        }
    },
    {
        'key':   'pts_automation',
        'label': 'Automatización de procesos',
        'max':   20,
        'desc':  {
            '20': 'Sistema de IA a medida desarrollado',
            '14': 'Chatbot o sistema conversacional activo',
            '8':  'Automatizaciones básicas en uso',
            '0':  'Sin automatizaciones',
        }
    },
    {
        'key':   'pts_area_usage',
        'label': 'Uso de IA por áreas de negocio',
        'max':   25,
        'desc':  'Basado en el nivel de adopción declarado en cada área (atención, ventas, RRHH, operaciones, finanzas, producto)'
    },
    {
        'key':   'pts_governance',
        'label': 'Gobierno, política y formación de IA',
        'max':   20,
        'desc':  {
            '5':  'Conocimiento del AI Act + política documentada + formación formal',
            '3':  'Conocimiento parcial del AI Act o política informal',
            '2':  'Sin política pero con conocimiento básico',
            '0':  'Sin política interna ni conocimiento del AI Act',
        }
    },
    {
        'key':   'pts_goal_clarity',
        'label': 'Claridad de objetivos y ROI esperado',
        'max':   15,
        'desc':  'Basado en la especificidad del proceso a mejorar y los resultados esperados declarados'
    },
]

# ─── Criterios fijos de Riesgo ───────────────────────────────────────────────
# Peso total: 100. Fuente: catalogs!WEIGHTS del sheet.
RISK_CRITERIA = [
    {
        'key':   'pts_data_risk',
        'label': 'Tipo de datos personales tratados',
        'max':   30,
        'desc':  {
            '30': 'Datos de menores o biométricos',
            '25': 'Datos de salud o financieros',
            '15': 'Datos de empleados',
            '10': 'Datos básicos de clientes',
            '0':  'Sin datos personales',
        }
    },
    {
        'key':   'pts_ai_personal_data',
        'label': 'Datos personales en flujos de IA',
        'max':   15,
        'desc':  {
            '15': 'Sí, datos personales pasan por sistemas de IA',
            '0':  'No o no lo saben',
        }
    },
    {
        'key':   'pts_dpa',
        'label': 'DPA con proveedores tecnológicos',
        'max':   15,
        'desc':  {
            '0':  'Sí, con todos los proveedores',
            '15': 'No o no sabe qué es un DPA',
            '8':  'Sí, con algunos proveedores',
        }
    },
    {
        'key':   'pts_dpia',
        'label': 'EIPD / DPIA realizada',
        'max':   15,
        'desc':  {
            # Nota: estos son textos de nivel de riesgo, no de respuesta del cliente.
            # El texto real de la respuesta del cliente lo provee llm_scoring_answers.
            # pts=0 → sin riesgo → empresa SÍ realizó EIPD o no aplica
            # pts=15 → riesgo alto → empresa no la realizó / no sabe qué es
            '0':  'EIPD realizada o no aplicable en este contexto',
            '15': 'No han realizado EIPD ni conocen el concepto',
        }
    },
    {
        'key':   'pts_automated_decisions',
        'label': 'Decisiones automatizadas sobre personas',
        'max':   15,
        'desc':  {
            '15': 'Sí, hay decisiones automatizadas con efectos sobre personas',
            '0':  'No',
        }
    },
    {
        'key':   'pts_sector',
        'label': 'Sector regulado',
        'max':   5,
        'desc':  {
            '5':  'Sector regulado (Salud o Finanzas/Seguros) — obligaciones adicionales',
            '0':  'Sector no regulado de forma específica — el riesgo por datos de salud '
                  'queda recogido en el criterio de tipo de datos (pts_data_risk)',
        }
    },
    {
        'key':   'pts_incident',
        'label': 'Incidente previo con IA o automatizaciones',
        'max':   5,
        'desc':  {
            '5':  'Sí, ha habido incidentes',
            '0':  'No',
        }
    },
]

# ─── Niveles ─────────────────────────────────────────────────────────────────
MATURITY_LEVELS = [
    (85, 100, 'Avanzada'),
    (70, 84,  'Operativa'),
    (50, 69,  'En adopción'),
    (30, 49,  'Inicial'),
    (0,  29,  'Muy inicial'),
]

RISK_LEVELS = [
    (75, 100, 'Muy alto'),
    (50, 74,  'Alto'),
    (25, 49,  'Medio'),
    (0,  24,  'Bajo'),
]


def _safe_int(val, default=0):
    try:
        return int(float(str(val).replace(',', '.')))
    except (ValueError, TypeError):
        return default


def _get_desc(criterion, pts_value):
    """Devuelve la descripción del criterio para el score dado."""
    desc = criterion.get('desc', '')
    if isinstance(desc, dict):
        # Buscar la descripción que corresponde al valor
        val_str = str(pts_value)
        if val_str in desc:
            return desc[val_str]
        # Buscar por valor más cercano
        int_val = _safe_int(pts_value)
        best = None
        best_diff = 9999
        for k, v in desc.items():
            diff = abs(_safe_int(k) - int_val)
            if diff < best_diff:
                best_diff = diff
                best = v
        return best or desc.get(list(desc.keys())[0], '')
    return str(desc)


def build_maturity_breakdown(rec: dict, llm_answers: dict = None) -> list:
    """
    Construye la tabla de desglose de madurez.
    llm_answers: dict opcional con {pts_key: "texto descripción respuesta declarada"}
    Devuelve lista de listas [criterio, respuesta, puntuación, máximo]

    NOTA: el total de la tabla siempre refleja maturity_score del sheet (fuente canónica),
    no la suma de pts_* individuales. Esto evita inconsistencias cuando el fallback
    de cálculo difiere del AppScript.
    """
    rows = []
    pts_total = 0

    for c in MATURITY_CRITERIA:
        key = c['key']
        pts = _safe_int(rec.get(key, 0))
        pts_total += pts

        # Texto de respuesta: LLM si disponible, sino descripción del criterio
        if llm_answers and key in llm_answers:
            answer_text = llm_answers[key]
        else:
            answer_text = _get_desc(c, pts)

        rows.append([c['label'], answer_text, str(pts), str(c['max'])])

    # Usar el score canónico del sheet como total si está disponible y difiere
    canonical_score = _safe_int(rec.get('maturity_score', 0))
    display_total   = canonical_score if canonical_score > 0 else pts_total

    rows.append(['Madurez total', '', str(display_total), '100'])
    return rows


def build_risk_breakdown(rec: dict, llm_answers: dict = None) -> list:
    """
    Construye la tabla de desglose de riesgo regulatorio.
    El total refleja risk_score del sheet (fuente canónica).
    """
    rows = []
    pts_total = 0

    for c in RISK_CRITERIA:
        key = c['key']
        pts = _safe_int(rec.get(key, 0))
        pts_total += pts

        if llm_answers and key in llm_answers:
            answer_text = llm_answers[key]
        else:
            answer_text = _get_desc(c, pts)

        rows.append([c['label'], answer_text, str(pts), str(c['max'])])

    # Usar el score canónico del sheet como total si está disponible y difiere
    canonical_score = _safe_int(rec.get('risk_score', 0))
    display_total   = canonical_score if canonical_score > 0 else pts_total

    rows.append(['Riesgo total', '', str(display_total), '100'])
    return rows


def get_maturity_level(score: int) -> str:
    for lo, hi, label in MATURITY_LEVELS:
        if lo <= score <= hi:
            return label
    return 'Muy inicial'


def get_risk_level(score: int) -> str:
    for lo, hi, label in RISK_LEVELS:
        if lo <= score <= hi:
            return label
    return 'Bajo'


def _compute_pts_from_answers(rec: dict) -> dict:
    """
    Calcula pts_* individuales desde las respuestas del formulario si no vienen del sheet.
    Replica EXACTAMENTE la lógica de Engine.gs (AppScript) para garantizar consistencia.

    IMPORTANTE: si el AppScript ya calculó y guardó los pts_* en el sheet (vía analysis),
    esta función NO debe ejecutarse — usar fetch_pts_from_sheet() primero.
    """
    tl = lambda s: str(s or '').lower()
    computed = {}

    # pts_tools (0-20): contar ítems separados por coma (igual que AppScript)
    tools = rec.get('tools_used', '')
    if not tools or tl(tools).startswith('no util') or tl(tools) == '':
        computed['pts_tools'] = 0
    else:
        # AppScript: count = (tools.match(/,/g) || []).length + 1
        count = tools.count(',') + 1
        computed['pts_tools'] = 20 if count >= 5 else (12 if count >= 3 else 6)

    # pts_automation (0-20): máximo entre custom_ai, chatbot, auto_system (igual que AppScript)
    chatbot   = tl(rec.get('chatbot_desc', rec.get('chatbot', '')))
    custom    = tl(rec.get('custom_ai_desc', rec.get('custom_ai', '')))
    auto      = tl(rec.get('auto_system', ''))
    if custom.startswith('si') or custom.startswith('sí'):
        computed['pts_automation'] = 20
    elif chatbot.startswith('si') or chatbot.startswith('sí'):
        computed['pts_automation'] = 14
    elif (auto.startswith('si') or auto.startswith('sí')) and 'no' not in auto:
        computed['pts_automation'] = 8
    else:
        # chatbot_desc relleno (ej: "WhatsApp; Callbell; no informamos...") = chatbot activo
        if chatbot and chatbot not in ('no', 'no tenemos', ''):
            computed['pts_automation'] = 14
        else:
            computed['pts_automation'] = 0

    # pts_area_usage (0-25): suma de 7 áreas escalada a 25 (igual que AppScript)
    # AppScript: areaRaw escalada sobre max 28 (7 áreas × 4 pts cada una)
    # Áreas: atención_cliente, marketing, ventas_crm, rrhh, operaciones, finanzas, producto
    area_fields = [
        rec.get('area_atencion', rec.get('[Atencion al cliente]', '')),
        rec.get('area_marketing', rec.get('[Marketing y comunicacion]', '')),
        rec.get('area_ventas', rec.get('[Ventas y CRM]', '')),
        rec.get('area_rrhh', rec.get('[RRHH y seleccion]', '')),
        rec.get('area_operaciones', rec.get('[Operaciones y logistica]', '')),
        rec.get('area_finanzas', rec.get('[Finanzas y administracion]', '')),
        rec.get('area_producto', rec.get('[Producto o servicio principal]', '')),
    ]
    area_raw = 0
    for a in area_fields:
        al = tl(a)
        if 'integrada' in al:           area_raw += 4
        elif 'automatizado' in al or 'chatbot' in al: area_raw += 2
        elif 'generica' in al or 'individual' in al:  area_raw += 1
    computed['pts_area_usage'] = min(25, round(area_raw * 25 / 28))

    # pts_governance (0-20): igual que AppScript
    gov = 0
    ai_act = tl(rec.get('ai_act', ''))
    if 'bastante' in ai_act:                   gov += 5
    elif 'oido' in ai_act or 'oído' in ai_act: gov += 2
    policy = tl(rec.get('politica_ia', ''))
    if 'documentada' in policy:   gov += 8
    elif 'informal' in policy:    gov += 4
    training = tl(rec.get('formacion_ia', ''))
    if 'formal' in training:      gov += 7
    elif 'informal' in training:  gov += 4
    computed['pts_governance'] = min(20, gov)

    # pts_goal_clarity (0-15): igual que AppScript
    plen = len(str(rec.get('process_to_improve', '') or ''))
    glen = len(str(rec.get('goals_12m', '') or ''))
    gc = 0
    if plen > 50:   gc += 10
    elif plen > 20: gc += 6
    if glen > 30:   gc += 5
    computed['pts_goal_clarity'] = min(15, gc)

    # pts_data_risk (0-30): igual que AppScript
    dtl = tl(rec.get('data_types', ''))
    if 'menores' in dtl or 'biometri' in dtl:              computed['pts_data_risk'] = 30
    elif 'salud' in dtl or 'financier' in dtl or 'bancar' in dtl: computed['pts_data_risk'] = 25
    elif 'empleado' in dtl:                                 computed['pts_data_risk'] = 15
    elif 'cliente' in dtl:                                  computed['pts_data_risk'] = 10
    else:                                                   computed['pts_data_risk'] = 0

    # pts_ai_personal_data (0-15): igual que AppScript
    dai = tl(rec.get('data_in_ai', ''))
    computed['pts_ai_personal_data'] = 15 if (dai.startswith('sí') or dai.startswith('si')) else 0

    # pts_dpa (0-15): igual que AppScript
    dpa = tl(rec.get('dpa', ''))
    if 'no se' in dpa or 'no sé' in dpa or (dpa.startswith('no') and 'algunos' not in dpa):
        computed['pts_dpa'] = 15
    elif 'algunos' in dpa:
        computed['pts_dpa'] = 8
    else:
        computed['pts_dpa'] = 0

    # pts_dpia (0-15): igual que AppScript
    eipd = tl(rec.get('eipd', ''))
    computed['pts_dpia'] = 15 if ('no se' in eipd or 'no sé' in eipd or eipd.startswith('no')) else 0

    # pts_automated_decisions (0-15): igual que AppScript
    ad = tl(rec.get('auto_decisions', ''))
    computed['pts_automated_decisions'] = 15 if (ad.startswith('sí') or ad.startswith('si')) else 0

    # pts_sector (0-5): igual que AppScript — retail/óptica NO puntúa, solo salud/finanzas/seguros
    sl = tl(rec.get('sector', ''))
    computed['pts_sector'] = 5 if ('salud' in sl or 'finanz' in sl or 'seguro' in sl) else 0

    # pts_incident (0-5): igual que AppScript
    inc = tl(rec.get('incident', ''))
    computed['pts_incident'] = 5 if (inc.startswith('sí') or inc.startswith('si')) else 0

    return computed


def compute_priority(rec: dict) -> tuple[int, str]:
    """
    Calcula priority_score (0-100) y priority_level.
    Mide la urgencia operativa del cliente — visible en el informe.
    Lógica idéntica al AppScript Engine.gs.
    """
    tl = lambda s: str(s or '').lower()
    score = 0

    # Prioridad declarada (hasta 35 pts)
    priority = tl(rec.get('priority', ''))
    if 'alta' in priority:       score += 35
    elif 'media' in priority:    score += 20
    elif 'baja' in priority:     score += 5

    # Horas perdidas (hasta 30 pts)
    hl = tl(rec.get('hours_lost', ''))
    if 'más de 20' in hl or 'mas de 20' in hl: score += 30
    elif '10' in hl or '15' in hl:             score += 20
    elif '5' in hl:                            score += 10
    elif 'menos' in hl:                        score += 5

    # Urgencia temporal del proceso (hasta 20 pts)
    proc_urg = tl(rec.get('proceso_urgencia', ''))
    if proc_urg.startswith('sí') or proc_urg.startswith('si'): score += 20
    elif any(x in proc_urg for x in ['temporada', 'verano', 'navidad', 'urgente']): score += 15

    # Riesgo regulatorio activo (hasta 15 pts)
    risk = _safe_int(rec.get('risk_score', 0))
    if risk >= 75:    score += 15
    elif risk >= 50:  score += 10
    elif risk >= 25:  score += 5

    score = min(100, score)
    level = ('Muy urgente' if score >= 80
             else 'Urgente' if score >= 60
             else 'Moderada' if score >= 40
             else 'Baja')
    return score, level


def fetch_pts_from_sheet(assessment_id: str, sheet_id: str) -> dict | None:
    """
    Lee los pts_* ya calculados por el AppScript desde la pestaña 'analysis' del sheet.
    Devuelve un dict {pts_key: int} o None si no se encuentran.

    Esto garantiza que el pipeline usa exactamente los mismos pts que el AppScript calculó,
    evitando divergencias entre el score del resumen ejecutivo y la tabla de desglose.
    """
    pts_keys = [
        'pts_tools', 'pts_automation', 'pts_area_usage', 'pts_governance', 'pts_goal_clarity',
        'pts_data_risk', 'pts_ai_personal_data', 'pts_dpa', 'pts_dpia',
        'pts_automated_decisions', 'pts_sector', 'pts_incident',
    ]

    try:
        import google_client

        # Leer headers de analysis
        headers_rows = google_client.sheets_read(sheet_id, 'analysis!1:1')
        headers = headers_rows[0] if headers_rows else []
        if not headers:
            return None

        col_map = {h: i for i, h in enumerate(headers)}
        id_col  = col_map.get('assessment_id')
        if id_col is None:
            return None

        # Leer todas las filas de datos
        rows = google_client.sheets_read(sheet_id, 'analysis!A2:ZZ500')

        for row in rows:
            if len(row) > id_col and row[id_col] == assessment_id:
                pts = {}
                for k in pts_keys:
                    ci = col_map.get(k)
                    if ci is not None and ci < len(row):
                        pts[k] = _safe_int(row[ci], 0)
                    else:
                        pts[k] = 0
                # Solo devolver si hay al menos algún pts > 0 (no son todos cero por error)
                if any(v > 0 for v in pts.values()):
                    return pts
        return None

    except Exception as e:
        print(f'   [scoring] fetch_pts_from_sheet error: {e}')
        return None


def enrich_with_scoring(rec: dict, llm_answers: dict = None,
                        sheet_id: str = None) -> dict:
    """
    Añade al record los campos de scoring trazables.
    Prioridad de fuente de pts_*:
      1. pts_* ya presentes en rec (pasados explícitamente)
      2. pts_* leídos desde analysis sheet (fuente canónica del AppScript)
      3. pts_* calculados desde las respuestas como fallback (lógica fiel al AppScript)

    Nunca sobreescribe maturity_score ni risk_score si ya vienen del sheet.
    """
    pts_keys = ['pts_tools', 'pts_automation', 'pts_area_usage', 'pts_governance',
                'pts_goal_clarity', 'pts_data_risk', 'pts_ai_personal_data',
                'pts_dpa', 'pts_dpia', 'pts_automated_decisions', 'pts_sector', 'pts_incident']

    pts_sum = sum(_safe_int(rec.get(k, 0)) for k in pts_keys)

    if pts_sum == 0:
        # Intentar leer desde analysis sheet (fuente canónica)
        sheet_pts = None
        assessment_id = rec.get('assessment_id', '')
        if assessment_id and sheet_id:
            print('   [scoring] Buscando pts_* en analysis sheet...')
            sheet_pts = fetch_pts_from_sheet(assessment_id, sheet_id)

        if sheet_pts:
            print(f'   [scoring] pts_* obtenidos del sheet (fuente canónica)')
            for k, v in sheet_pts.items():
                rec[k] = v
        else:
            # Fallback: calcular desde respuestas del formulario
            print('   [scoring] pts_* no en sheet — calculando desde respuestas (fallback)')
            computed = _compute_pts_from_answers(rec)
            for k, v in computed.items():
                rec[k] = v

    # Verificar coherencia: si maturity_score ya viene del sheet, el total de pts debe coincidir
    # Si no, loguear advertencia pero NO sobreescribir el score (el sheet es la fuente de verdad)
    existing_maturity = _safe_int(rec.get('maturity_score', 0))
    mat_pts_total = sum(_safe_int(rec.get(k, 0)) for k in
                        ['pts_tools', 'pts_automation', 'pts_area_usage', 'pts_governance', 'pts_goal_clarity'])
    if existing_maturity > 0 and mat_pts_total > 0 and abs(existing_maturity - mat_pts_total) > 2:
        print(f'   [scoring] ⚠ AVISO: maturity_score del sheet ({existing_maturity}) '
              f'≠ suma de pts_* ({mat_pts_total}). Usando score del sheet.')

    existing_risk = _safe_int(rec.get('risk_score', 0))
    risk_pts_total = sum(_safe_int(rec.get(k, 0)) for k in
                         ['pts_data_risk', 'pts_ai_personal_data', 'pts_dpa', 'pts_dpia',
                          'pts_automated_decisions', 'pts_sector', 'pts_incident'])
    if existing_risk > 0 and risk_pts_total > 0 and abs(existing_risk - risk_pts_total) > 2:
        print(f'   [scoring] ⚠ AVISO: risk_score del sheet ({existing_risk}) '
              f'≠ suma de pts_* ({risk_pts_total}). Usando score del sheet.')

    # Calcular priority_score si no viene del sheet
    if not rec.get('priority_score'):
        p_score, p_level = compute_priority(rec)
        rec['priority_score'] = p_score
        rec['priority_level'] = p_level

    # Construir breakdowns con los pts correctos
    mat_breakdown  = build_maturity_breakdown(rec, llm_answers)
    risk_breakdown = build_risk_breakdown(rec, llm_answers)

    rec['llm_maturity_breakdown'] = mat_breakdown
    rec['llm_risk_breakdown']     = risk_breakdown

    return rec


if __name__ == '__main__':
    import json, sys
    rec = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    result = enrich_with_scoring(rec)
    print(json.dumps({
        'maturity_breakdown': result['llm_maturity_breakdown'],
        'risk_breakdown':     result['llm_risk_breakdown'],
    }, ensure_ascii=False, indent=2))


def fix_employee_range(value) -> str:
    """Convierte fecha serial de Sheets a texto si es necesario."""
    if value is None:
        return '—'
    s = str(value).strip()
    # Si es un número > 40000, probablemente es un serial de fecha — ignorar
    try:
        n = float(s)
        if n > 10000:
            return '—'  # valor corrupto
        return s
    except (ValueError, TypeError):
        return s if s else '—'
