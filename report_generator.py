"""
AI Readiness Assessment - Report Generator v2
Genera el informe completo (12-15 páginas) con branding Zanovix.
Versión cliente: sin encaje comercial, con rigor metodológico.
"""

import sys, json, os, re
from datetime import datetime
from docx import Document
from docx.shared import Pt, RGBColor, Inches, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

# ─── Brand ─────────────────────────────────────────────────────────────────────
TEAL        = RGBColor(0x2B, 0xA8, 0x9E)
DARK        = RGBColor(0x1A, 0x1A, 0x1A)
GREY        = RGBColor(0x6B, 0x72, 0x80)
LIGHT_GREY  = RGBColor(0xE5, 0xE7, 0xEB)
WHITE       = RGBColor(0xFF, 0xFF, 0xFF)
RED         = RGBColor(0xDC, 0x26, 0x26)
AMBER       = RGBColor(0xD9, 0x77, 0x06)
GREEN       = RGBColor(0x16, 0xA3, 0x4A)
BLUE_DARK   = RGBColor(0x1F, 0x4E, 0x79)

HEX = {
    'dark': '1A1A1A', 'teal': '2BA89E', 'white': 'FFFFFF',
    'light': 'F3FAFA', 'alt': 'EBF5F4', 'header_grey': 'F9FAFB',
    'red_light': 'FEF2F2', 'amber_light': 'FFFBEB', 'green_light': 'F0FDF4',
}

LOGO_PATH = os.path.join(os.path.dirname(__file__), 'assets', 'zanovix_logo.png')

# ─── Helpers ───────────────────────────────────────────────────────────────────
def set_cell_bg(cell, hex_color):
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:fill'), hex_color.lstrip('#'))
    shd.set(qn('w:val'), 'clear')
    tcPr.append(shd)

def safe(v, default='—'):
    return str(v).strip() if v is not None and str(v).strip() else default

def today():
    return datetime.now().strftime('%d/%m/%Y')

def pipe_split(text):
    return [s.strip() for s in str(text or '').split('|') if s.strip()]

def add_run(para, text, bold=False, italic=False, size=11, color=None, underline=False):
    run = para.add_run(str(text or ''))
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.italic = italic
    run.font.underline = underline
    if color:
        run.font.color.rgb = color
    return run

def add_para(doc, text='', bold=False, italic=False, size=11, color=None,
             space_before=0, space_after=6, align=None):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(space_before)
    p.paragraph_format.space_after = Pt(space_after)
    p.paragraph_format.line_spacing = Pt(16)
    if align:
        p.alignment = align
    if text:
        add_run(p, text, bold=bold, italic=italic, size=size, color=color)
    return p

def add_heading(doc, text, color=TEAL, size=14, space_before=18, space_after=8,
                underline=False, border=False):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(space_before)
    p.paragraph_format.space_after = Pt(space_after)
    if border:
        pPr = p._p.get_or_add_pPr()
        pBdr = OxmlElement('w:pBdr')
        bottom = OxmlElement('w:bottom')
        bottom.set(qn('w:val'), 'single')
        bottom.set(qn('w:sz'), '4')
        bottom.set(qn('w:space'), '4')
        bottom.set(qn('w:color'), '2BA89E')
        pBdr.append(bottom)
        pPr.append(pBdr)
    add_run(p, text, bold=True, size=size, color=color, underline=underline)
    return p

def add_bullet(doc, text, color=DARK, size=11):
    p = doc.add_paragraph(style='List Bullet')
    p.paragraph_format.space_after = Pt(3)
    add_run(p, text, size=size, color=color)
    return p

def add_divider(doc):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(6)
    p.paragraph_format.space_after = Pt(6)
    pPr = p._p.get_or_add_pPr()
    pBdr = OxmlElement('w:pBdr')
    bottom = OxmlElement('w:bottom')
    bottom.set(qn('w:val'), 'single')
    bottom.set(qn('w:sz'), '6')
    bottom.set(qn('w:space'), '1')
    bottom.set(qn('w:color'), '2BA89E')
    pBdr.append(bottom)
    pPr.append(pBdr)
    return p

def style_table_header_row(row, bg_hex=None, text_color=WHITE):
    bg = bg_hex or HEX['dark']
    for cell in row.cells:
        set_cell_bg(cell, bg)
        cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
        for para in cell.paragraphs:
            for run in para.runs:
                run.font.bold = True
                run.font.color.rgb = text_color
                run.font.size = Pt(10)

def style_table_data_row(row, bg_hex=None):
    bg = bg_hex or HEX['white']
    for cell in row.cells:
        set_cell_bg(cell, bg)
        cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
        for para in cell.paragraphs:
            for run in para.runs:
                run.font.size = Pt(10)

def set_col_widths(table, widths_cm):
    for row in table.rows:
        for i, cell in enumerate(row.cells):
            if i < len(widths_cm):
                cell.width = Cm(widths_cm[i])

# ─── Score metadata ─────────────────────────────────────────────────────────────
def get_score_breakdown(rec):
    """
    Genera la tabla de scoring visible con criterios y respuestas.
    Usa llm_maturity_breakdown / llm_risk_breakdown si están disponibles (generados por scoring_engine).
    Fallback a campos sueltos pts_* si no.
    """
    mat_bd = rec.get('llm_maturity_breakdown')
    risk_bd = rec.get('llm_risk_breakdown')

    if mat_bd and isinstance(mat_bd, list) and len(mat_bd) > 1:
        # Excluir la fila de total (última)
        maturity_items = [(row[0], row[1], row[2], row[3]) for row in mat_bd[:-1]]
    else:
        # Fallback: construir respuestas descriptivas desde los campos raw del rec
        def _desc_tools():
            t = safe(rec.get('tools_used', ''))
            if not t or t == '—': return 'Sin herramientas de IA declaradas'
            return t[:120]

        def _desc_auto():
            chatbot = safe(rec.get('chatbot_desc', rec.get('chatbot', '')))
            custom  = safe(rec.get('custom_ai_desc', rec.get('custom_ai', '')))
            auto_sys = safe(rec.get('auto_system', ''))
            parts = [p for p in [chatbot, custom, auto_sys] if p and p != '—' and p.lower() not in ('no', 'no,')]
            return (' + '.join(parts))[:120] if parts else 'Sin automatización activa'

        def _desc_area():
            areas = [rec.get(f'area_{a}', '') for a in ['atencion','marketing','ventas','rrhh','operaciones','finanzas','producto']]
            actives = [a for a in areas if a and 'sin uso' not in str(a).lower() and str(a).strip() != '']
            if not actives: return 'Sin adopción de IA en áreas de negocio'
            return f'{len(actives)} áreas con algún uso de IA'

        def _desc_gov():
            policy = safe(rec.get('politica_ia', ''))
            training = safe(rec.get('formacion_ia', ''))
            ai_act = safe(rec.get('ai_act', ''))
            return f'Política: {policy} · Formación: {training} · AI Act: {ai_act}'[:120]

        def _desc_goal():
            process = safe(rec.get('process_to_improve', ''))
            goals = safe(rec.get('goals_12m', ''))
            return (process or goals or '—')[:120]

        maturity_items = [
            ('Herramientas de IA activas',      _desc_tools(),  safe(rec.get('pts_tools', 0)),         '20'),
            ('Automatización de procesos',       _desc_auto(),   safe(rec.get('pts_automation', 0)),    '20'),
            ('Uso de IA por áreas de negocio',   _desc_area(),   safe(rec.get('pts_area_usage', 0)),    '25'),
            ('Gobierno, política y formación',   _desc_gov(),    safe(rec.get('pts_governance', 0)),    '20'),
            ('Claridad de objetivos y ROI',      _desc_goal(),   safe(rec.get('pts_goal_clarity', 0)),  '15'),
        ]

    if risk_bd and isinstance(risk_bd, list) and len(risk_bd) > 1:
        risk_items = [(row[0], row[1], row[2], row[3]) for row in risk_bd[:-1]]
    else:
        def _desc_data():
            return safe(rec.get('data_types', '—'))[:120]
        def _desc_ai_data():
            return 'Sí — datos personales en sistemas IA' if str(rec.get('data_in_ai','')).lower().startswith('s') else 'No declarado'
        def _desc_dpa():
            return safe(rec.get('dpa', '—'))[:80]
        def _desc_eipd():
            return safe(rec.get('eipd', '—'))[:80]
        def _desc_dec():
            return safe(rec.get('auto_decisions', '—'))[:80]
        def _desc_incident():
            return safe(rec.get('incident', '—'))[:60]

        risk_items = [
            ('Tipo de datos personales tratados',       _desc_data(),     safe(rec.get('pts_data_risk', 0)),            '30'),
            ('Datos personales en flujos de IA',        _desc_ai_data(),  safe(rec.get('pts_ai_personal_data', 0)),     '15'),
            ('DPA con proveedores tecnológicos',        _desc_dpa(),      safe(rec.get('pts_dpa', 0)),                  '15'),
            ('EIPD / DPIA realizada',                   _desc_eipd(),     safe(rec.get('pts_dpia', 0)),                 '15'),
            ('Decisiones automatizadas sobre personas', _desc_dec(),      safe(rec.get('pts_automated_decisions', 0)), '15'),
            ('Sector regulado',                         safe(rec.get('sector', '—')), safe(rec.get('pts_sector', 0)),  '5'),
            ('Incidente previo con IA',                 _desc_incident(), safe(rec.get('pts_incident', 0)),            '5'),
        ]

    return maturity_items, risk_items


# ─── Main generator ─────────────────────────────────────────────────────────────
def generate_report(rec: dict, output_path: str = None) -> str:
    doc = Document()

    # Page setup
    for section in doc.sections:
        section.top_margin    = Cm(2.2)
        section.bottom_margin = Cm(2.2)
        section.left_margin   = Cm(2.8)
        section.right_margin  = Cm(2.8)

    company   = safe(rec.get('company_name'), 'Empresa')
    aid       = safe(rec.get('assessment_id'), '—')
    respondent= safe(rec.get('respondent_name_role'), 'No especificado')
    sector    = safe(rec.get('sector'), 'No especificado')
    employees = safe(rec.get('employee_range'), 'No especificado')
    revenue   = safe(rec.get('revenue_range'), 'No especificado')
    region    = safe(rec.get('operating_region'), 'No especificado')

    # ── 1. PORTADA ─────────────────────────────────────────────────────────────
    if os.path.exists(LOGO_PATH):
        logo_p = doc.add_paragraph()
        logo_p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        logo_p.paragraph_format.space_after = Pt(48)
        logo_p.add_run().add_picture(LOGO_PATH, width=Inches(1.8))

    badge = add_para(doc, 'AI READINESS ASSESSMENT', bold=True, size=11,
                     color=TEAL, space_after=8)

    title = add_para(doc, company, bold=True, size=30, color=DARK, space_after=12)

    respondent = safe(rec.get('respondent_name_role'), '')
    if respondent:
        add_para(doc, f'Contacto: {respondent}', size=12, color=GREY, space_after=4)

    meta = add_para(doc, f'Assessment ID: {aid}     ·     Fecha: {today()}',
                    size=10, color=GREY, space_after=32)

    add_divider(doc)

    tag = add_para(doc,
        'Diagnóstico estructurado de madurez en IA, exposición regulatoria '
        'y potencial de automatización con impacto real en el negocio.',
        italic=True, size=12, color=DARK, space_before=20, space_after=8)

    add_para(doc, 'Elaborado por Zanovix · zanovix.com',
             size=10, color=GREY, space_after=4)

    add_para(doc, 'Documento confidencial — uso exclusivo de ' + company,
             italic=True, size=9, color=GREY)

    doc.add_page_break()

    # ── 2. ÍNDICE ──────────────────────────────────────────────────────────────
    add_heading(doc, 'Contenido del informe', border=True)
    toc = [
        'Base del diagnóstico',
        'Resumen ejecutivo',
        'Inventario de sistemas',
        'Scoring detallado',
        'Hallazgos: riesgos regulatorios',
        'Oportunidades: matriz de priorización',
        'Estimación económica',
        'Roadmap de actuación (30/60/90 días)',
        'Recomendación final',
    ]
    # Secciones condicionales de recomendaciones
    if rec.get('llm_tool_recommendations') and isinstance(rec.get('llm_tool_recommendations'), list) and len(rec['llm_tool_recommendations']) > 0:
        toc.append('Stack tecnológico recomendado')
    if rec.get('llm_dpa_guidance') and isinstance(rec.get('llm_dpa_guidance'), list) and len(rec['llm_dpa_guidance']) > 0:
        toc.append('Guía DPA por herramienta')
    if rec.get('llm_ai_policy_draft') and isinstance(rec.get('llm_ai_policy_draft'), dict) and len(rec['llm_ai_policy_draft']) > 0:
        toc.append('Borrador de política de IA interna')
    if rec.get('llm_followup_questions') and isinstance(rec.get('llm_followup_questions'), list) and len(rec['llm_followup_questions']) > 0:
        toc.append('Preguntas de profundización (Fase 2)')
    toc.extend([
        'Dependencias y límites del análisis',
        'Siguiente paso propuesto',
    ])
    for i, item in enumerate(toc, 1):
        add_para(doc, f'{i}. {item}', size=11, color=DARK, space_after=3)
    doc.add_page_break()

    # ── 3. BASE DEL DIAGNÓSTICO ────────────────────────────────────────────────
    add_heading(doc, '1. Base del diagnóstico', border=True)

    data_base_all = [
        ('Empresa analizada',   company),
        ('Respondente',         respondent),
        ('Fecha del análisis',  today()),
        ('Sector',              sector),
        ('Tamaño del equipo',   employees),
        ('Facturación aprox.',  revenue),
        ('Ámbito geográfico',   region),
    ]
    # Filtrar filas con valor real (no "No especificado" ni vacío)
    data_base = [(l, v) for l, v in data_base_all if v and v != '—' and v.lower() != 'no especificado']
    table = doc.add_table(rows=len(data_base), cols=2)
    table.style = 'Table Grid'
    for i, (label, value) in enumerate(data_base):
        row = table.rows[i]
        cell_l, cell_r = row.cells[0], row.cells[1]
        set_cell_bg(cell_l, HEX['header_grey'])
        cell_l.paragraphs[0].clear()
        add_run(cell_l.paragraphs[0], label, bold=True, size=10, color=DARK)
        cell_r.paragraphs[0].clear()
        add_run(cell_r.paragraphs[0], value, size=10, color=DARK)
    set_col_widths(table, [5.5, 10.5])

    add_para(doc, '', space_after=8)

    add_heading(doc, 'Alcance y metodología', size=12, color=DARK,
                space_before=12, space_after=4)
    add_para(doc,
        'Este análisis se basa en las respuestas a un cuestionario estructurado '
        'de 42 preguntas sobre herramientas, procesos, datos, gobierno y objetivos '
        'de la empresa. Los resultados reflejan la información declarada por el '
        'respondente y no sustituyen una auditoría técnica ni asesoramiento '
        'jurídico formal.',
        size=11, color=DARK, space_after=8)

    add_heading(doc, 'Limitaciones del análisis', size=12, color=DARK,
                space_before=8, space_after=4)
    for lim in [
        'La información no ha sido verificada de forma independiente.',
        'Los scores reflejan indicadores declarados, no una auditoría real del tratamiento de datos.',
        'Las estimaciones económicas son rangos orientativos basados en supuestos explícitos.',
        'Las observaciones regulatorias son orientaciones, no dictámenes jurídicos.',
        'Los puntos marcados como "indicios" requieren análisis adicional para confirmar.',
    ]:
        add_bullet(doc, lim, size=10, color=GREY)

    doc.add_page_break()

    # ── 4. RESUMEN EJECUTIVO ───────────────────────────────────────────────────
    add_heading(doc, '2. Resumen ejecutivo', border=True)

    # Score cards in a table
    score_table = doc.add_table(rows=1, cols=4)
    score_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    score_labels = [
        ('Madurez',    rec.get('maturity_score'), rec.get('maturity_level'),   HEX['teal']),
        ('Riesgo',     rec.get('risk_score'),     rec.get('risk_level'),       '991B1B'),
        ('Prioridad',  rec.get('priority_score'), rec.get('priority_level'),   '1D4ED8'),
    ]
    headers = ['Madurez en IA', 'Riesgo regulatorio', 'Prioridad / urgencia']
    for i, (label, score, level, color_hex) in enumerate(score_labels):
        cell = score_table.rows[0].cells[i]
        set_cell_bg(cell, HEX['light'])
        cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
        p1 = cell.paragraphs[0]
        p1.alignment = WD_ALIGN_PARAGRAPH.CENTER
        add_run(p1, headers[i], bold=True, size=9, color=DARK)
        p2 = cell.add_paragraph()
        p2.alignment = WD_ALIGN_PARAGRAPH.CENTER
        rgb = RGBColor(int(color_hex[0:2],16), int(color_hex[2:4],16), int(color_hex[4:6],16))
        add_run(p2, safe(score, '—'), bold=True, size=22, color=rgb)
        p3 = cell.add_paragraph()
        p3.alignment = WD_ALIGN_PARAGRAPH.CENTER
        add_run(p3, safe(level, '—'), size=10, color=GREY)
    # 4th cell: next step
    cell4 = score_table.rows[0].cells[3]
    set_cell_bg(cell4, HEX['alt'])
    cell4.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
    p4a = cell4.paragraphs[0]
    p4a.alignment = WD_ALIGN_PARAGRAPH.CENTER
    add_run(p4a, 'Siguiente paso', bold=True, size=9, color=DARK)
    p4b = cell4.add_paragraph()
    p4b.alignment = WD_ALIGN_PARAGRAPH.CENTER
    # Campo "Siguiente paso" en la tabla resumen — celda pequeña, máx ~80 chars visibles
    # Fuente preferida: recommended_next_step (ya es corto y ejecutivo, viene del AppScript)
    # Fallback: primera oración de llm_final_recommendation
    next_display = rec.get('llm_next_step_short') or ''
    if not next_display:
        raw_next = safe(rec.get('recommended_next_step', ''))
        crm_texts = ['lead frío', 'nurture', 'assessment express', 'proponer pronto',
                     'proponer en', 'deal fit', 'encaje']
        if raw_next and not any(t in raw_next.lower() for t in crm_texts):
            next_display = raw_next
    if not next_display:
        # Fallback: primera oración de llm_final_recommendation, máx 90 chars
        llm_rec = safe(rec.get('llm_final_recommendation', ''))
        if llm_rec:
            # Quitar el prefijo "▶  " si existe
            llm_rec = llm_rec.lstrip('▶ ').strip()
            # Cortar en coma o punto, lo que llegue antes de 90 chars
            for sep in [',', '.', ';']:
                idx = llm_rec.find(sep)
                if 0 < idx <= 88:
                    next_display = llm_rec[:idx].strip()
                    break
            if not next_display:
                next_display = llm_rec[:88].strip()
    if not next_display:
        next_display = 'Discovery técnico + propuesta de implementación'
    add_run(p4b, next_display, bold=True, size=10, color=TEAL)
    set_col_widths(score_table, [4, 4, 4, 4])

    add_para(doc, '', space_after=12)
    add_para(doc, safe(rec.get('llm_executive_summary'), 'Sin resumen disponible.'),
             size=11, color=DARK, space_after=8)

    doc.add_page_break()

    # ── 5. INVENTARIO DE SISTEMAS ──────────────────────────────────────────────
    add_heading(doc, '3. Inventario de sistemas declarados', border=True)
    add_para(doc,
        'Herramientas y sistemas con componentes de IA o automatización identificados '
        'a partir de la información declarada por el respondente.',
        size=10, color=GREY, italic=True, space_after=8)

    inv_data = rec.get('llm_inventory_table')
    if inv_data and isinstance(inv_data, list) and len(inv_data) > 0:
        cols = ['Herramienta / sistema', 'Uso declarado', 'Canal', 'Datos que toca', '¿Avisa de IA?']
        inv_table = doc.add_table(rows=1 + len(inv_data), cols=5)
        inv_table.style = 'Table Grid'
        for i, label in enumerate(cols):
            cell = inv_table.rows[0].cells[i]
            set_cell_bg(cell, HEX['dark'])
            cell.paragraphs[0].clear()
            add_run(cell.paragraphs[0], label, bold=True, size=9, color=WHITE)
        for ri, row_data in enumerate(inv_data):
            row = inv_table.rows[ri + 1]
            bg = HEX['light'] if ri % 2 == 0 else HEX['white']
            for ci, val in enumerate(row_data[:5]):
                cell = row.cells[ci]
                set_cell_bg(cell, bg)
                cell.paragraphs[0].clear()
                add_run(cell.paragraphs[0], str(val), size=9, color=DARK)
        set_col_widths(inv_table, [4, 3.5, 2, 3, 2.5])
    else:
        tools = safe(rec.get('llm_tools_list'), 'No especificadas')
        add_para(doc, f'Herramientas declaradas: {tools}', size=11, color=DARK)

    doc.add_page_break()

    # ── 6. SCORING DETALLADO ───────────────────────────────────────────────────
    add_heading(doc, '4. Scoring detallado', border=True)
    add_para(doc,
        'Cada dimensión se evalúa en base a las respuestas declaradas. '
        'Se indica la respuesta que motivó la puntuación para que el resultado sea trazable.',
        size=10, color=GREY, italic=True, space_after=10)

    # Madurez table
    add_heading(doc, 'Madurez en IA — ' + safe(rec.get('maturity_score'), '—') + '/100 (' + safe(rec.get('maturity_level'), '—') + ')',
                size=12, color=TEAL, space_before=8, space_after=6)

    mat_items, risk_items = get_score_breakdown(rec)

    # Use LLM-provided breakdown if available
    mat_breakdown = rec.get('llm_maturity_breakdown', [])
    if not mat_breakdown:
        mat_breakdown = mat_items

    mat_table = doc.add_table(rows=1 + len(mat_breakdown), cols=4)
    mat_table.style = 'Table Grid'
    for i, h in enumerate(['Criterio', 'Respuesta declarada', 'Puntuación', 'Máximo']):
        cell = mat_table.rows[0].cells[i]
        set_cell_bg(cell, HEX['teal'])
        cell.paragraphs[0].clear()
        add_run(cell.paragraphs[0], h, bold=True, size=9, color=WHITE)
    for ri, item in enumerate(mat_breakdown):
        row = mat_table.rows[ri + 1]
        bg = HEX['light'] if ri % 2 == 0 else HEX['white']
        is_total = ri == len(mat_breakdown) - 1
        for ci, val in enumerate(item[:4]):
            cell = row.cells[ci]
            set_cell_bg(cell, HEX['alt'] if is_total else bg)
            cell.paragraphs[0].clear()
            add_run(cell.paragraphs[0], str(val), bold=is_total, size=9,
                    color=TEAL if (ci in [2,3] and is_total) else DARK)
    set_col_widths(mat_table, [5, 7, 2.5, 1.5])

    add_para(doc, '', space_after=12)

    # Riesgo table
    add_heading(doc, 'Riesgo regulatorio — ' + safe(rec.get('risk_score'), '—') + '/100 (' + safe(rec.get('risk_level'), '—') + ')',
                size=12, color=RGBColor(0x99, 0x1B, 0x1B), space_before=8, space_after=6)

    risk_breakdown = rec.get('llm_risk_breakdown', [])
    if not risk_breakdown:
        risk_breakdown = risk_items

    risk_table = doc.add_table(rows=1 + len(risk_breakdown), cols=4)
    risk_table.style = 'Table Grid'
    for i, h in enumerate(['Criterio', 'Respuesta declarada', 'Puntuación', 'Máximo']):
        cell = risk_table.rows[0].cells[i]
        set_cell_bg(cell, '991B1B')
        cell.paragraphs[0].clear()
        add_run(cell.paragraphs[0], h, bold=True, size=9, color=WHITE)
    for ri, item in enumerate(risk_breakdown):
        row = risk_table.rows[ri + 1]
        bg = HEX['light'] if ri % 2 == 0 else HEX['white']
        is_total = ri == len(risk_breakdown) - 1
        for ci, val in enumerate(item[:4]):
            cell = row.cells[ci]
            set_cell_bg(cell, HEX['red_light'] if is_total else bg)
            cell.paragraphs[0].clear()
            add_run(cell.paragraphs[0], str(val), bold=is_total, size=9, color=DARK)
    set_col_widths(risk_table, [5, 7, 2.5, 1.5])

    doc.add_page_break()

    # ── 7. HALLAZGOS REGULATORIOS ──────────────────────────────────────────────
    add_heading(doc, '5. Hallazgos: riesgos regulatorios', border=True)
    add_para(doc,
        'Se distingue entre hallazgos confirmados (evidencia directa en las respuestas), '
        'indicios (alta probabilidad pero requieren análisis adicional) y '
        'recomendaciones (buenas prácticas a revisar).',
        size=10, color=GREY, italic=True, space_after=10)

    risk_findings = rec.get('llm_risk_findings_structured')
    if risk_findings and isinstance(risk_findings, list):
        for finding in risk_findings:
            level   = finding.get('level', 'RECOMENDABLE')
            title   = finding.get('title', '')
            body    = finding.get('body', '')
            marco   = finding.get('marco', '')
            impacto = finding.get('impacto', '')

            if level == 'CONFIRMADO':
                emoji, bg, color = '🔴', HEX['red_light'], RGBColor(0x99, 0x1B, 0x1B)
            elif level == 'INDICIO':
                emoji, bg, color = '🟡', HEX['amber_light'], AMBER
            else:
                emoji, bg, color = '🟠', HEX['light'], TEAL

            finding_table = doc.add_table(rows=1, cols=1)
            finding_table.style = 'Table Grid'
            cell = finding_table.rows[0].cells[0]
            set_cell_bg(cell, bg)

            p_title = cell.paragraphs[0]
            add_run(p_title, f'{emoji} {level} — ', bold=True, size=11, color=color)
            add_run(p_title, title, bold=True, size=11, color=DARK)

            if body:
                p_body = cell.add_paragraph()
                add_run(p_body, body, size=10, color=DARK)

            if marco:
                p_marco = cell.add_paragraph()
                add_run(p_marco, 'Marco legal: ', bold=True, size=9, color=GREY)
                add_run(p_marco, marco, size=9, color=GREY)

            if impacto:
                p_imp = cell.add_paragraph()
                add_run(p_imp, 'Impacto potencial: ', bold=True, size=9, color=GREY)
                add_run(p_imp, impacto, size=9, color=GREY)

            add_para(doc, '', space_after=6)
    else:
        # Fallback: plain text
        add_para(doc, safe(rec.get('llm_risk_findings'), 'Sin hallazgos disponibles.'),
                 size=11, color=DARK)
        for gap in pipe_split(rec.get('top_gaps', '')):
            add_bullet(doc, gap, color=DARK)

    doc.add_page_break()

    # ── 8. MATRIZ DE OPORTUNIDADES ─────────────────────────────────────────────
    add_heading(doc, '6. Oportunidades: matriz de priorización', border=True)
    add_para(doc, safe(rec.get('llm_opportunities'), ''),
             size=11, color=DARK, space_after=10)

    opp_matrix = rec.get('llm_opportunity_matrix')
    if opp_matrix and isinstance(opp_matrix, list):
        headers_opp = ['Iniciativa', 'Impacto', 'Complejidad', 'Riesgo si no actúas', 'Prioridad']
        opp_table = doc.add_table(rows=1 + len(opp_matrix), cols=5)
        opp_table.style = 'Table Grid'
        for i, h in enumerate(headers_opp):
            cell = opp_table.rows[0].cells[i]
            set_cell_bg(cell, HEX['dark'])
            cell.paragraphs[0].clear()
            add_run(cell.paragraphs[0], h, bold=True, size=9, color=WHITE)
        for ri, row_data in enumerate(opp_matrix):
            row = opp_table.rows[ri + 1]
            bg = HEX['light'] if ri % 2 == 0 else HEX['white']
            for ci, val in enumerate(row_data[:5]):
                cell = row.cells[ci]
                set_cell_bg(cell, bg)
                cell.paragraphs[0].clear()
                bold = (ci == 4)  # Prioridad col bold
                color = TEAL if ci == 4 else DARK
                add_run(cell.paragraphs[0], str(val), bold=bold, size=9, color=color)
        set_col_widths(opp_table, [5.5, 2, 2.5, 3.5, 2.5])
    else:
        for opp in pipe_split(rec.get('top_opportunities', '')):
            add_bullet(doc, opp, color=TEAL)

    doc.add_page_break()

    # ── 9. ESTIMACIÓN ECONÓMICA ────────────────────────────────────────────────
    add_heading(doc, '7. Estimación económica', border=True)
    add_para(doc,
        'Las siguientes estimaciones se basan en la información declarada y en supuestos '
        'estándar para empresas del sector y tamaño indicados. Deben validarse operativamente '
        'antes de usarse como base de decisión de inversión.',
        size=10, color=GREY, italic=True, space_after=10)

    econ = rec.get('llm_economic_estimate')
    if econ and isinstance(econ, dict):
        # Normalizar claves técnicas a etiquetas legibles para el cliente
        KEY_LABELS = {
            'concepto': 'Proceso analizado',
            'calculo': 'Cálculo del coste actual',
            'calculo_detalle': 'Detalle del cálculo',
            'detalle': 'Detalle',
            'ahorro_estimado': 'Ahorro anual estimado',
            'ahorro_proyectado': 'Ahorro proyectado',
            'ahorro_anual_euros': 'Ahorro anual estimado',
            'ahorro_total_anual': 'Ahorro total anual',
            'ingresos_adicionales': 'Ingresos adicionales estimados',
            'inversion_estimada': 'Inversión estimada implementación',
            'inversion_implementacion': 'Inversión estimada implementación',
            'componentes_inversion': 'Desglose de la inversión',
            'roi_meses': 'Plazo de retorno estimado',
            'roi_12_meses': 'Retorno a 12 meses',
            'payback_estimado': 'Plazo de retorno estimado',
            'resultado': 'Resultado',
        }
        econ_display = {KEY_LABELS.get(k, k): v for k, v in econ.items()}

        econ_table = doc.add_table(rows=len(econ_display), cols=2)
        econ_table.style = 'Table Grid'
        for i, (label, value) in enumerate(econ_display.items()):
            row = econ_table.rows[i]
            bg = HEX['light'] if i % 2 == 0 else HEX['white']
            set_cell_bg(row.cells[0], HEX['header_grey'])
            set_cell_bg(row.cells[1], bg)
            row.cells[0].paragraphs[0].clear()
            add_run(row.cells[0].paragraphs[0], label, bold=True, size=10, color=DARK)
            row.cells[1].paragraphs[0].clear()
            # Renderizar listas como líneas separadas, no como repr de Python
            if isinstance(value, list):
                display_value = '\n'.join(str(v) for v in value)
            else:
                display_value = str(value)
            add_run(row.cells[1].paragraphs[0], display_value, size=10, color=DARK)
        set_col_widths(econ_table, [7, 9])
    else:
        econ_text = safe(rec.get('llm_economic_summary'), '')
        if econ_text:
            add_para(doc, econ_text, size=11, color=DARK)

    doc.add_page_break()

    # ── 10. ROADMAP ────────────────────────────────────────────────────────────
    add_heading(doc, '8. Roadmap de actuación (30 / 60 / 90 días)', border=True)

    roadmap_structured = rec.get('llm_roadmap_structured')
    # Validar que tiene las 3 fases — si no, caer al texto plano
    if roadmap_structured and isinstance(roadmap_structured, list) and len(roadmap_structured) >= 3:
        for phase in roadmap_structured:
            label    = phase.get('label', '')
            objetivo = phase.get('objetivo', '')
            acciones = phase.get('acciones', [])
            resp     = phase.get('responsable', '')

            p_label = add_para(doc, '', space_before=12, space_after=4)
            add_run(p_label, label + ' ', bold=True, size=12, color=TEAL)
            if objetivo:
                add_run(p_label, '— ' + objetivo, size=11, color=DARK)

            for accion in acciones:
                add_bullet(doc, accion, size=10)

            if resp:
                add_para(doc, f'Responsable sugerido: {resp}', size=9, color=GREY,
                         italic=True, space_after=4)
    else:
        roadmap_text = safe(rec.get('llm_roadmap_30_60_90'), 'Sin roadmap disponible.')
        phases = re.split(r'(\d+\s*días?:)', roadmap_text, flags=re.IGNORECASE)
        if len(phases) > 1:
            for i in range(1, len(phases), 2):
                p = add_para(doc, '', space_before=10, space_after=4)
                add_run(p, phases[i].strip() + ' ', bold=True, size=12, color=TEAL)
                content = phases[i+1].strip() if i+1 < len(phases) else ''
                add_run(p, content, size=11, color=DARK)
        else:
            add_para(doc, roadmap_text, size=11, color=DARK)

    doc.add_page_break()

    # ── 11. RECOMENDACIÓN FINAL ────────────────────────────────────────────────
    add_heading(doc, '9. Recomendación final', border=True)

    rec_table = doc.add_table(rows=1, cols=1)
    rec_table.style = 'Table Grid'
    cell_rec = rec_table.rows[0].cells[0]
    set_cell_bg(cell_rec, HEX['alt'])
    p_rec = cell_rec.paragraphs[0]
    add_run(p_rec, '▶  ', bold=True, size=13, color=TEAL)
    add_run(p_rec,
            safe(rec.get('llm_final_recommendation'),
                 safe(rec.get('recommended_next_step'), '—')),
            bold=True, size=12, color=DARK)
    add_para(doc, '', space_after=12)

    final_narrative = rec.get('llm_final_narrative')
    if final_narrative:
        add_para(doc, final_narrative, size=11, color=DARK, space_after=8)

    # ── SECCIONES DE RECOMENDACIONES (condicionales) ─────────────────────────

    # ── STACK TECNOLÓGICO RECOMENDADO ──────────────────────────────────────
    tool_recs = rec.get('llm_tool_recommendations')
    if tool_recs and isinstance(tool_recs, list) and len(tool_recs) > 0:
        doc.add_page_break()
        add_heading(doc, 'Stack tecnológico recomendado', border=True)
        add_para(doc,
                 f'Herramientas recomendadas según el perfil de {safe(rec.get("company_name", "la empresa"))}',
                 italic=True, size=10, color=GREY, space_after=8)

        cols = ['Herramienta', 'Área', 'Problema que resuelve', 'Confianza', 'Coste estimado', 'Prioridad']
        t = doc.add_table(rows=1, cols=len(cols))
        t.style = 'Table Grid'
        t.alignment = WD_TABLE_ALIGNMENT.CENTER
        for i, h in enumerate(cols):
            t.rows[0].cells[i].text = h
        style_table_header_row(t.rows[0])

        priority_labels = {1: '1 — Inmediata', 2: '2 — Corto plazo', 3: '3 — Medio plazo'}
        confidence_labels = {'high': 'Alta ✓', 'medium': 'Media'}

        for idx, tr in enumerate(tool_recs):
            row = t.add_row()
            row.cells[0].text = safe(tr.get('tool'))
            row.cells[1].text = safe(tr.get('area'))
            row.cells[2].text = safe(tr.get('problem_solved'))
            row.cells[3].text = confidence_labels.get(tr.get('confidence', ''), safe(tr.get('confidence')))
            row.cells[4].text = safe(tr.get('estimated_cost'))
            prio = tr.get('priority', 3)
            row.cells[5].text = priority_labels.get(prio, str(prio))
            bg = HEX['white'] if idx % 2 == 0 else HEX['alt']
            style_table_data_row(row, bg)

        set_col_widths(t, [3.0, 2.5, 5.0, 2.0, 2.5, 2.5])
        add_divider(doc)

    # ── GUÍA DPA POR HERRAMIENTA ──────────────────────────────────────────
    dpa_guidance = rec.get('llm_dpa_guidance')
    if dpa_guidance and isinstance(dpa_guidance, list) and len(dpa_guidance) > 0:
        add_heading(doc, 'Guía DPA por herramienta', border=True)

        risk_colors = {'high': RED, 'medium': AMBER, 'low': GREEN}

        for entry in dpa_guidance:
            add_para(doc, safe(entry.get('tool')), bold=True, size=12, color=DARK, space_before=8)
            add_bullet(doc, f'Proveedor: {safe(entry.get("provider"))}')
            data_types = entry.get('data_types_processed', [])
            if isinstance(data_types, list):
                add_bullet(doc, f'Datos procesados: {", ".join(data_types)}')
            else:
                add_bullet(doc, f'Datos procesados: {safe(data_types)}')

            risk = entry.get('risk_level', 'medium')
            risk_p = doc.add_paragraph(style='List Bullet')
            risk_p.paragraph_format.space_after = Pt(3)
            add_run(risk_p, 'Nivel de riesgo: ', size=11, color=DARK)
            add_run(risk_p, risk.upper(), bold=True, size=11, color=risk_colors.get(risk, AMBER))

            add_bullet(doc, f'Acción requerida: {safe(entry.get("action_required"))}')

            clauses = entry.get('key_clauses_needed', [])
            if clauses and isinstance(clauses, list):
                add_para(doc, 'Cláusulas clave necesarias:', bold=True, size=10, color=DARK, space_before=4)
                for clause in clauses:
                    add_bullet(doc, clause, size=10, color=GREY)

        add_divider(doc)

    # ── BORRADOR DE POLÍTICA DE IA INTERNA ────────────────────────────────
    policy_draft = rec.get('llm_ai_policy_draft')
    if policy_draft and isinstance(policy_draft, dict) and len(policy_draft) > 0:
        doc.add_page_break()
        add_heading(doc, 'Borrador de política de IA interna', border=True)
        add_para(doc,
                 'Este borrador es orientativo y debe ser revisado por un profesional legal antes de su adopción formal.',
                 italic=True, size=10, color=GREY, space_after=8)

        # Map keys to Spanish section titles
        section_titles = {
            'scope': 'Ámbito de aplicación',
            'permitted_uses': 'Usos permitidos',
            'prohibited_uses': 'Usos prohibidos',
            'data_handling': 'Tratamiento de datos',
            'human_oversight': 'Supervisión humana',
            'incident_protocol': 'Protocolo de incidentes',
            'training_requirements': 'Formación requerida',
            'review_cadence': 'Cadencia de revisión',
        }

        for key, title in section_titles.items():
            value = policy_draft.get(key)
            if not value:
                continue
            add_para(doc, title, bold=True, size=11, color=TEAL, space_before=8, space_after=4)
            if isinstance(value, list):
                for item in value:
                    add_bullet(doc, item, size=10, color=DARK)
            else:
                add_para(doc, str(value), size=10, color=DARK, space_after=6)

        add_divider(doc)

    # ── PREGUNTAS DE PROFUNDIZACIÓN (FASE 2) ──────────────────────────────
    followup_qs = rec.get('llm_followup_questions')
    if followup_qs and isinstance(followup_qs, list) and len(followup_qs) > 0:
        add_heading(doc, 'Preguntas de profundización (Fase 2)', border=True)
        add_para(doc,
                 'Las siguientes preguntas permiten profundizar en áreas donde el formulario '
                 'no aportó suficiente contexto para hacer recomendaciones concretas.',
                 italic=True, size=10, color=GREY, space_after=8)

        for q in followup_qs:
            area = safe(q.get('area', '')).upper()
            p_area = doc.add_paragraph()
            p_area.paragraph_format.space_before = Pt(8)
            p_area.paragraph_format.space_after = Pt(2)
            add_run(p_area, f'[{area}]', bold=True, size=11, color=TEAL)

            add_para(doc, safe(q.get('question')), size=11, color=DARK, space_after=2)

            why = q.get('why_needed')
            if why:
                add_para(doc, f'Por qué: {why}', italic=True, size=10, color=GREY, space_after=2)

            unlocks = q.get('what_it_unlocks')
            if unlocks:
                add_para(doc, f'Qué habilita: {unlocks}', italic=True, size=10, color=GREY, space_after=6)

        add_divider(doc)

    doc.add_page_break()

    # ── 12. DEPENDENCIAS Y LÍMITES ─────────────────────────────────────────────
    add_heading(doc, '10. Dependencias y límites del análisis', border=True)

    dependencies = rec.get('llm_dependencies')
    if dependencies and isinstance(dependencies, list):
        for dep in dependencies:
            add_bullet(doc, dep, size=10, color=DARK)
    else:
        default_deps = [
            'La automatización de procesos depende de las integraciones disponibles con los sistemas actuales.',
            'Las estimaciones económicas requieren validación operativa con datos reales del negocio.',
            'Este informe no constituye asesoramiento jurídico formal ni sustituye una auditoría de cumplimiento.',
            'Los hallazgos regulatorios marcados como "indicios" requieren análisis adicional para confirmar.',
            'La viabilidad técnica de cada iniciativa debe verificarse en una fase de discovery.',
        ]
        for dep in default_deps:
            add_bullet(doc, dep, size=10, color=DARK)

    add_para(doc, '', space_after=12)

    # ── 13. SIGUIENTE PASO ─────────────────────────────────────────────────────
    add_heading(doc, '11. Siguiente paso propuesto', border=True)

    next_step_text = rec.get('llm_next_step_proposal')
    if next_step_text:
        add_para(doc, next_step_text, size=11, color=DARK, space_after=8)
    else:
        add_para(doc,
            'El siguiente paso recomendado es una sesión de discovery de 60 minutos '
            'para validar los hallazgos, definir el alcance exacto del primer proyecto '
            'y elaborar una propuesta de implementación con scope, plazo y coste detallados.',
            size=11, color=DARK, space_after=8)

    add_para(doc, 'Para coordinar esta sesión:', bold=True, size=11, color=DARK, space_after=4)
    add_para(doc, 'pepe@zanovix.com  ·  zanovix.com', size=11, color=TEAL, space_after=4)

    # ── FOOTER ────────────────────────────────────────────────────────────────
    add_divider(doc)
    footer_p = add_para(doc,
        f'Documento confidencial  ·  Zanovix  ·  zanovix.com  ·  '
        f'Elaborado el {today()}  ·  '
        f'Este informe no sustituye asesoramiento jurídico formal.',
        size=9, italic=True, color=GREY, align=WD_ALIGN_PARAGRAPH.CENTER)

    # Save
    if not output_path:
        slug = re.sub(r'[^\w]', '_', company)[:30]
        # Use /app/output in Docker, /tmp locally
        reports_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'output')
        if not os.path.isdir(reports_dir):
            os.makedirs(reports_dir, exist_ok=True)
        output_path = f'{reports_dir}/AIReadiness_{slug}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.docx'

    doc.save(output_path)
    return output_path


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Uso: python3 report_generator.py \'{"assessment_id":...}\'')
        sys.exit(1)
    rec = json.loads(sys.argv[1])
    path = generate_report(rec)
    print(path)
