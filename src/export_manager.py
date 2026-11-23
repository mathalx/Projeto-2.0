import json
import os
import pandas as pd
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage, KeepTogether, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from src.storage_manager import (
    DATA_DIR,
    get_visit_equipment,
    get_visit_measurements,
    load_clients,
    load_visits,
)

EXPORTS_DIR = os.path.join(DATA_DIR, "exports")


def init_exports_dir():
    os.makedirs(EXPORTS_DIR, exist_ok=True)


def generate_pdf_report(visit_id: str) -> str:
    init_exports_dir()
    visits = load_visits()
    clients = load_clients()
    
    if visit_id not in visits:
        return None
        
    visit = visits[visit_id]
    client_id = visit.get("client_id")
    client = clients.get(client_id, {})
    
    pdf_filename = f"Relatorio_Visita_{visit_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    pdf_path = os.path.join(EXPORTS_DIR, pdf_filename)
    
    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )
    
    styles = getSampleStyleSheet()
    
    # Custom styles
    primary_color = colors.HexColor("#16834A")
    dark_green = colors.HexColor("#216B45")
    graphite = colors.HexColor("#59636A")
    black = colors.HexColor("#000000")
    light_bg = colors.HexColor("#E8F2EA")
    
    title_style = ParagraphStyle(
        'ACNTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=20,
        textColor=primary_color,
        spaceAfter=4
    )
    
    subtitle_style = ParagraphStyle(
        'ACNSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=12,
        textColor=graphite,
        spaceAfter=15
    )
    
    section_style = ParagraphStyle(
        'ACNSection',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=13,
        textColor=dark_green,
        spaceBefore=10,
        spaceAfter=6
    )
    
    normal_style = ParagraphStyle(
        'ACNNormal',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        textColor=black,
        leading=14
    )
    
    bold_style = ParagraphStyle(
        'ACNBold',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        textColor=black,
        leading=14
    )
    
    story = []
    
    # Header Branding
    header_text = "<font color='#16834A'><b>ACN</b></font><font color='#59636A'><b>norte</b></font> — Relatório de Visita Técnica de Segurança"
    story.append(Paragraph(header_text, title_style))
    story.append(Paragraph(f"Emitido em: {datetime.now().strftime('%d/%m/%Y às %H:%M')}", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=2, color=primary_color, spaceAfter=15))
    
    # Client and visit information.
    start_date = str(visit.get("date_start") or visit.get("date") or "N/A")
    end_date = str(visit.get("date_end") or "").strip()
    date_label = start_date
    if end_date and end_date != start_date:
        date_label = f"{start_date} a {end_date}"

    status_display = str(visit.get('status') or '').strip()
    if not status_display or status_display.upper() == 'N/A':
        status_display = 'Não visitado'
    client_data = [
        [Paragraph("<b>Empresa Cliente:</b>", bold_style), Paragraph(client.get('name', 'N/A'), normal_style)],
        [Paragraph("<b>CNPJ:</b>", bold_style), Paragraph(client.get('cnpj', 'N/A'), normal_style)],
        [Paragraph("<b>Endereço:</b>", bold_style), Paragraph(client.get('address', 'N/A'), normal_style)],
        [Paragraph("<b>Responsável na Empresa:</b>", bold_style), Paragraph(client.get('responsible', 'N/A'), normal_style)],
        [Paragraph("<b>Contato:</b>", bold_style), Paragraph(f"Tel: {client.get('phone', 'N/A')} | E-mail: {client.get('email', 'N/A')}", normal_style)],
        [Paragraph("<b>Data da Visita:</b>", bold_style), Paragraph(date_label, normal_style)],
        [Paragraph("<b>Técnico Responsável:</b>", bold_style), Paragraph(visit.get('technician', 'N/A'), normal_style)],
        [Paragraph("<b>Situação:</b>", bold_style), Paragraph(status_display, normal_style)]
    ]
    
    t_client = Table(client_data, colWidths=[150, 390])
    t_client.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F4F6F4")),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#D0D7DE")),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E5E9EC")),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    
    story.append(t_client)
    story.append(Spacer(1, 15))

    # Identificação da visita (DATA / NOME DO FUNCIONÁRIO / HORÁRIO)
    visit_time = str(visit.get("horario") or "").strip()
    worker = visit.get("worker") if isinstance(visit.get("worker"), dict) else {}
    worker_name = (
        str(worker.get("name") or "").strip()
        or str(visit.get("worker_name") or "").strip()
        or "Não informado"
    )
    ident_parts = [date_label]
    ident_parts.append(worker_name if worker_name != "Não informado" else "Funcionário não identificado")
    if visit_time:
        ident_parts.append(visit_time)
    story.append(Paragraph("Identificação da Visita", section_style))
    story.append(Paragraph(" / ".join(ident_parts), normal_style))
    story.append(Spacer(1, 10))

    # Funcionário avaliado (nome e fotografia)
    story.append(Paragraph("Funcionário Avaliado", section_style))
    worker_photo = (
        worker.get("photo_path")
        or worker.get("funcionario_foto_url")
        or visit.get("worker_photo")
        or ""
    )
    worker_text = [Paragraph(f"<b>Nome:</b> {worker_name}", normal_style)]
    if worker_photo and os.path.exists(str(worker_photo)):
        try:
            worker_img = RLImage(str(worker_photo), width=120, height=120, kind="proportional", mask="auto")
            t_worker = Table(
                [[worker_text, [worker_img]]],
                colWidths=[390, 150],
            )
            t_worker.setStyle(TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (1, 0), (1, 0), "CENTER"),
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F4F6F4")),
                ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#D0D7DE")),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ]))
            story.append(t_worker)
        except Exception:
            story.append(Paragraph(f"<b>Nome:</b> {worker_name}", normal_style))
            story.append(Paragraph("Fotografia do funcionário indisponível.", normal_style))
    else:
        story.append(Paragraph(f"<b>Nome:</b> {worker_name}", normal_style))
        story.append(Paragraph("Fotografia do funcionário: não registrada.", normal_style))
    story.append(Spacer(1, 15))

    # Caderno de Avaliação de Agentes Químicos (quando houver dados)
    caderno = visit.get("caderno_avaliacao") if isinstance(visit.get("caderno_avaliacao"), dict) else {}
    if caderno:
        has_caderno_data = any(str(v or "").strip() for v in caderno.values())
    else:
        has_caderno_data = False
    if has_caderno_data:
        story.append(Paragraph("Caderno de Avaliação de Agentes Químicos", section_style))

        def _cval(key, fallback="—"):
            val = str(caderno.get(key) or "").strip()
            return val if val else fallback

        empresa_c = _cval("empresa_avaliada", client.get('name', '—'))
        unidade_c = _cval("unidade")
        estado_c = _cval("estado")
        bloco_a = [
            [Paragraph("<b>Empresa Avaliada</b>", bold_style), Paragraph(empresa_c, normal_style)],
            [Paragraph("<b>Unidade</b>", bold_style), Paragraph(unidade_c, normal_style)],
            [Paragraph("<b>Estado</b>", bold_style), Paragraph(estado_c, normal_style)],
        ]
        t_a = Table(bloco_a, colWidths=[200, 340])
        t_a.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,-1), colors.white),
            ("BOX", (0,0), (-1,-1), 0.5, colors.HexColor("#D0D7DE")),
            ("INNERGRID", (0,0), (-1,-1), 0.5, colors.HexColor("#E5E9EC")),
            ("TOPPADDING", (0,0), (-1,-1), 4), ("BOTTOMPADDING", (0,0), (-1,-1), 4),
            ("LEFTPADDING", (0,0), (-1,-1), 6), ("RIGHTPADDING", (0,0), (-1,-1), 6),
            ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ]))
        story.append(t_a)
        story.append(Spacer(1, 8))

        bloco_b = [
            [Paragraph("<b>Agente Químico</b>", bold_style), Paragraph(_cval("agente_quimico"), normal_style)],
            [Paragraph("<b>Data de Amostragem</b>", bold_style), Paragraph(_cval("data_amostragem"), normal_style)],
            [Paragraph("<b>Identificação da Amostra</b>", bold_style), Paragraph(_cval("identificacao_amostra"), normal_style)],
            [Paragraph("<b>Hora Inicial</b>", bold_style), Paragraph(_cval("hora_inicial"), normal_style)],
            [Paragraph("<b>Hora Final</b>", bold_style), Paragraph(_cval("hora_final"), normal_style)],
            [Paragraph("<b>Vazão (L/Min)</b>", bold_style), Paragraph(_cval("vazao_l_min"), normal_style)],
            [Paragraph("<b>Temperatura (amostragem)</b>", bold_style), Paragraph(_cval("temperatura_amostragem"), normal_style)],
        ]
        t_b = Table(bloco_b, colWidths=[200, 340])
        t_b.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,-1), colors.white),
            ("BOX", (0,0), (-1,-1), 0.5, colors.HexColor("#D0D7DE")),
            ("INNERGRID", (0,0), (-1,-1), 0.5, colors.HexColor("#E5E9EC")),
            ("TOPPADDING", (0,0), (-1,-1), 4), ("BOTTOMPADDING", (0,0), (-1,-1), 4),
            ("LEFTPADDING", (0,0), (-1,-1), 6), ("RIGHTPADDING", (0,0), (-1,-1), 6),
            ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ]))
        story.append(t_b)
        story.append(Spacer(1, 8))

        bloco_c = [
            [Paragraph("<b>Setor</b>", bold_style), Paragraph(_cval("setor"), normal_style)],
            [Paragraph("<b>Funcionário</b>", bold_style), Paragraph(_cval("funcionario", worker_name), normal_style)],
            [Paragraph("<b>Função</b>", bold_style), Paragraph(_cval("funcao"), normal_style)],
            [Paragraph("<b>Matrícula</b>", bold_style), Paragraph(_cval("matricula"), normal_style)],
        ]
        t_c = Table(bloco_c, colWidths=[200, 340])
        t_c.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,-1), colors.white),
            ("BOX", (0,0), (-1,-1), 0.5, colors.HexColor("#D0D7DE")),
            ("INNERGRID", (0,0), (-1,-1), 0.5, colors.HexColor("#E5E9EC")),
            ("TOPPADDING", (0,0), (-1,-1), 4), ("BOTTOMPADDING", (0,0), (-1,-1), 4),
            ("LEFTPADDING", (0,0), (-1,-1), 6), ("RIGHTPADDING", (0,0), (-1,-1), 6),
            ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ]))
        story.append(t_c)
        story.append(Spacer(1, 8))

        story.append(Paragraph("<b>Atividades desenvolvidas</b>", bold_style))
        story.append(Paragraph(str(caderno.get("atividades_desenvolvidas") or "—").replace("\n", "<br/>"), normal_style))
        story.append(Spacer(1, 6))
        story.append(Paragraph("<b>EPI</b>", bold_style))
        story.append(Paragraph(str(caderno.get("epi") or "—").replace("\n", "<br/>"), normal_style))
        story.append(Spacer(1, 6))
        story.append(Paragraph("<b>EPC</b>", bold_style))
        story.append(Paragraph(str(caderno.get("epc") or "—").replace("\n", "<br/>"), normal_style))
        story.append(Spacer(1, 6))
        story.append(Paragraph("<b>Observações (Caderno)</b>", bold_style))
        story.append(Paragraph(str(caderno.get("obs") or "—").replace("\n", "<br/>"), normal_style))
        story.append(Spacer(1, 8))

        bloco_g = [
            [Paragraph("<b>Funcionário / Responsável</b>", bold_style), Paragraph(_cval("responsavel_funcionario", worker_name), normal_style)],
            [Paragraph("<b>Nome (Responsável)</b>", bold_style), Paragraph(_cval("nome_responsavel"), normal_style)],
            [Paragraph("<b>Avaliador</b>", bold_style), Paragraph(_cval("avaliador", visit.get('technician', '—')), normal_style)],
            [Paragraph("<b>Nome do Avaliador</b>", bold_style), Paragraph(_cval("nome_avaliador", visit.get('technician', '—')), normal_style)],
        ]
        t_g = Table(bloco_g, colWidths=[200, 340])
        t_g.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,-1), colors.white),
            ("BOX", (0,0), (-1,-1), 0.5, colors.HexColor("#D0D7DE")),
            ("INNERGRID", (0,0), (-1,-1), 0.5, colors.HexColor("#E5E9EC")),
            ("TOPPADDING", (0,0), (-1,-1), 4), ("BOTTOMPADDING", (0,0), (-1,-1), 4),
            ("LEFTPADDING", (0,0), (-1,-1), 6), ("RIGHTPADDING", (0,0), (-1,-1), 6),
            ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ]))
        story.append(t_g)
        story.append(Spacer(1, 15))

    # Temperatura, origem e horário da consulta (quando utilizada)
    weather = visit.get("weather") if isinstance(visit.get("weather"), dict) else {}
    if weather and (weather.get("temperature_c") is not None or weather.get("internal_temperature_c") is not None or weather.get("source") or weather.get("captured_at")):
        story.append(Paragraph("Temperatura e Clima", section_style))
        weather_rows = []
        def _fmt_temp(v):
            try:
                return f"{float(v):.1f} °C"
            except Exception:
                return "—"
        def _fmt_hum(v):
            try:
                return f"{float(v):.0f}%"
            except Exception:
                return "—"
        weather_rows.append([Paragraph("<b>Temperatura externa (clima)</b>", bold_style), Paragraph(_fmt_temp(weather.get("temperature_c")), normal_style)])
        if weather.get("internal_temperature_c") is not None:
            weather_rows.append([Paragraph("<b>Temperatura interna medida</b>", bold_style), Paragraph(_fmt_temp(weather.get("internal_temperature_c")), normal_style)])
        weather_rows.append([Paragraph("<b>Umidade</b>", bold_style), Paragraph(_fmt_hum(weather.get("humidity_pct")), normal_style)])
        weather_rows.append([Paragraph("<b>Origem</b>", bold_style), Paragraph(str(weather.get("source") or "—"), normal_style)])
        weather_rows.append([Paragraph("<b>Horário da consulta</b>", bold_style), Paragraph(str(weather.get("captured_at") or "—"), normal_style)])
        if weather.get("city"):
            weather_rows.append([Paragraph("<b>Local</b>", bold_style), Paragraph(str(weather.get("city")), normal_style)])
        elif weather.get("latitude") is not None and weather.get("longitude") is not None:
            weather_rows.append([Paragraph("<b>Local</b>", bold_style), Paragraph(f"{weather.get('latitude')}, {weather.get('longitude')}", normal_style)])
        if weather.get("description"):
            weather_rows.append([Paragraph("<b>Condição</b>", bold_style), Paragraph(str(weather.get("description")), normal_style)])
        t_weather = Table(weather_rows, colWidths=[200, 340])
        t_weather.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,-1), colors.white),
            ("BOX", (0,0), (-1,-1), 0.5, colors.HexColor("#D0D7DE")),
            ("INNERGRID", (0,0), (-1,-1), 0.5, colors.HexColor("#E5E9EC")),
            ("TOPPADDING", (0,0), (-1,-1), 4),
            ("BOTTOMPADDING", (0,0), (-1,-1), 4),
            ("LEFTPADDING", (0,0), (-1,-1), 6),
            ("RIGHTPADDING", (0,0), (-1,-1), 6),
            ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ]))
        story.append(t_weather)
        story.append(Spacer(1, 15))

    # Forms data section
    story.append(Paragraph("Resumo dos Formulários Técnicos Preenchidos", section_style))
    forms_data = visit.get("forms", {})
    
    if forms_data:
        from src.form_template import TECHNICAL_FORM_SECTIONS
        for cat_key, cat_answers in forms_data.items():
            cat_info = TECHNICAL_FORM_SECTIONS.get(cat_key, {})
            cat_title = cat_info.get("title", cat_key)
            story.append(Paragraph(f"<b>{cat_title}</b>", bold_style))
            story.append(Spacer(1, 4))
            
            table_rows = []
            for field in cat_info.get("fields", []):
                f_id = field["id"]
                f_label = field["label"]
                f_val = cat_answers.get(f_id) or "Não preenchido"
                table_rows.append([Paragraph(f_label, normal_style), Paragraph(str(f_val), bold_style)])
                
            if table_rows:
                t_form = Table(table_rows, colWidths=[370, 170])
                t_form.setStyle(TableStyle([
                    ('BACKGROUND', (0,0), (-1,-1), colors.white),
                    ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#D0D7DE")),
                    ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E5E9EC")),
                    ('TOPPADDING', (0,0), (-1,-1), 4),
                    ('BOTTOMPADDING', (0,0), (-1,-1), 4),
                    ('LEFTPADDING', (0,0), (-1,-1), 6),
                    ('RIGHTPADDING', (0,0), (-1,-1), 6),
                    ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                ]))
                story.append(t_form)
                story.append(Spacer(1, 8))
    else:
        story.append(Paragraph("Nenhum formulário preenchido para esta visita.", normal_style))
        
    story.append(Spacer(1, 10))

    # Equipment used in noise dosimetry.
    story.append(
        Paragraph(
            "Equipamentos Utilizados — Dosimetria de Ruído",
            section_style,
        )
    )
    equipment_items = get_visit_equipment(visit)
    measurements = {
        str(m.get("equipment_code")): m for m in get_visit_measurements(visit)
    }
    if equipment_items:
        equipment_rows = [
            [
                Paragraph("<b>Categoria</b>", bold_style),
                Paragraph("<b>Marca</b>", bold_style),
                Paragraph("<b>Identificação do registro</b>", bold_style),
                Paragraph("<b>Medição vinculada</b>", bold_style),
            ]
        ]
        for index, item in enumerate(equipment_items, start=1):
            code = str(item.get("codigo") or "")
            measurement = measurements.get(code, {})
            registro = (
                measurement.get("identificacao_registro")
                or item.get("identificacao_registro")
                or str(item.get("identificacao") or "—")
            )
            measurement_id = measurement.get("id") or item.get("measurement_id") or f"Medição {index}"
            equipment_rows.append(
                [
                    Paragraph(str(item.get("categoria") or "—"), normal_style),
                    Paragraph(str(item.get("marca") or "—"), normal_style),
                    Paragraph(str(registro), bold_style),
                    Paragraph(str(measurement_id), normal_style),
                ]
            )
        t_equipment = Table(equipment_rows, colWidths=[130, 110, 190, 110])
        t_equipment.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), colors.white),
                    ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#D0D7DE")),
                    ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E5E9EC")),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ]
            )
        )
        story.append(t_equipment)
    else:
        story.append(
            Paragraph(
                "Nenhum equipamento registrado para esta visita.",
                normal_style,
            )
        )
    story.append(Spacer(1, 10))

    # Observations & Conclusions
    story.append(Paragraph("Observações Técnicas", section_style))
    obs_text = visit.get("observations") or "Nenhuma observação registrada."
    story.append(Paragraph(obs_text.replace("\n", "<br/>"), normal_style))
    story.append(Spacer(1, 10))
    
    story.append(Paragraph("Conclusões e Recomendações", section_style))
    conc_text = visit.get("conclusions") or "Nenhuma conclusão registrada."
    story.append(Paragraph(conc_text.replace("\n", "<br/>"), normal_style))
    story.append(Spacer(1, 15))
    
    # Photos Section
    photos = visit.get("photos", [])
    if photos:
        story.append(Paragraph(f"Fotografias Anexadas ({len(photos)})", section_style))
        photo_rows = []
        for p in photos:
            p_path = p.get("path")
            p_desc = p.get("description", "Sem descrição")
            p_date = p.get("uploaded_at", "")
            
            registro = str(p.get("identificacao_registro") or "").strip()
            horario = str(p.get("horario") or "").strip()
            obs = str(p.get("observations") or "").strip()
            registro_html = ""
            if registro:
                registro_html = f"<br/><b>Equipamento:</b> {registro}"
            elif horario:
                registro_html = f"<br/><b>Horário:</b> {horario}"
            if horario and registro and horario not in registro:
                registro_html = f"<br/><b>Horário:</b> {horario}" + registro_html
            obs_html = ""
            if obs:
                obs_html = f"<br/><b>Observações:</b> {obs}"
            p_elements = [Paragraph(f"<b>Descrição:</b> {p_desc}{registro_html}{obs_html}<br/><font size=8 color='#59636A'>Enviado em: {p_date}</font>", normal_style)]
            if p_path and os.path.exists(p_path):
                try:
                    img = RLImage(p_path, width=180, height=135)
                    p_elements.insert(0, img)
                except Exception:
                    p_elements.insert(0, Paragraph("[Imagem não encontrada]", normal_style))
            else:
                p_elements.insert(0, Paragraph("[Arquivo de imagem indisponível]", normal_style))
                
            photo_rows.append(p_elements)
            
        # Group in pairs or single table cells
        for i in range(0, len(photo_rows), 2):
            row_items = photo_rows[i:i+2]
            while len(row_items) < 2:
                row_items.append(Paragraph("", normal_style))
            t_photo = Table([[row_items[0], row_items[1]]], colWidths=[265, 265])
            t_photo.setStyle(TableStyle([
                ('VALIGN', (0,0), (-1,-1), 'TOP'),
                ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F8F9FA")),
                ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#D0D7DE")),
                ('TOPPADDING', (0,0), (-1,-1), 6),
                ('BOTTOMPADDING', (0,0), (-1,-1), 6),
                ('LEFTPADDING', (0,0), (-1,-1), 6),
                ('RIGHTPADDING', (0,0), (-1,-1), 6),
            ]))
            story.append(KeepTogether([t_photo, Spacer(1, 10)]))

    # Signatures Section
    story.append(Spacer(1, 8))
    story.append(Paragraph("Assinaturas", section_style))
    story.append(
        Paragraph(
            "Registros eletrônicos de assinatura. Este documento não possui "
            "validade jurídica automática.",
            normal_style,
        )
    )
    story.append(Spacer(1, 8))

    signatures = visit.get("signatures")
    if not isinstance(signatures, dict):
        signatures = {}

    signature_cells = []
    for role, label in (
        ("technical", "Responsável Técnico"),
        ("evaluator", "Avaliador"),
    ):
        signature = signatures.get(role)
        if not isinstance(signature, dict):
            signature = {}
        name = str(signature.get("name") or "").strip() or "Não informado"
        signed_at = signature.get("signed_at") or ""
        signature_path = signature.get("path")

        cell = [Paragraph(f"<b>{label}</b>", bold_style), Spacer(1, 4)]
        if signature_path and os.path.exists(signature_path):
            try:
                cell.append(
                    RLImage(
                        signature_path,
                        width=220,
                        height=80,
                        kind="proportional",
                        mask="auto",
                    )
                )
            except Exception:
                cell.append(Paragraph("[Assinatura indisponível]", normal_style))
        else:
            cell.append(Paragraph("Não assinado", normal_style))

        cell.append(Spacer(1, 4))
        cell.append(Paragraph(f"Nome: {name}", normal_style))
        if signed_at:
            cell.append(Paragraph(f"Registrada em: {signed_at}", normal_style))
        signature_cells.append(cell)

    t_signatures = Table(
        [[signature_cells[0], signature_cells[1]]],
        colWidths=[265, 265],
    )
    t_signatures.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F8F9FA")),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#D0D7DE")),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E5E9EC")),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.append(KeepTogether([t_signatures]))

    doc.build(story)
    return pdf_path

def export_clients_to_excel() -> str:
    init_exports_dir()
    clients = load_clients()
    if not clients:
        return None
        
    data = []
    for c_id, c in clients.items():
        data.append({
            "ID": c_id,
            "Nome da Empresa": c.get("name"),
            "CNPJ": c.get("cnpj"),
            "Endereço": c.get("address"),
            "Responsável": c.get("responsible"),
            "Telefone": c.get("phone"),
            "E-mail": c.get("email"),
            "Data de Cadastro": c.get("created_at")
        })
        
    df = pd.DataFrame(data)
    filename = f"Clientes_ACNnorte_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    filepath = os.path.join(EXPORTS_DIR, filename)
    df.to_excel(filepath, index=False)
    return filepath

def export_visits_to_excel() -> str:
    init_exports_dir()
    visits = load_visits()
    if not visits:
        return None
        
    data = []
    for v_id, v in visits.items():
        photos_count = len(v.get("photos", []))
        photos_desc = "; ".join([p.get("description", "") for p in v.get("photos", [])])
        signatures = v.get("signatures") if isinstance(v.get("signatures"), dict) else {}
        technical = signatures.get("technical") if isinstance(signatures.get("technical"), dict) else {}
        evaluator = signatures.get("evaluator") if isinstance(signatures.get("evaluator"), dict) else {}
        equipment_items = get_visit_equipment(v)
        measurements = {
            str(m.get("equipment_code")): m for m in get_visit_measurements(v)
        }
        equipment_records = []
        for item in equipment_items:
            code = str(item.get("codigo") or "")
            measurement = measurements.get(code, {})
            registro = (
                measurement.get("identificacao_registro")
                or item.get("identificacao_registro")
                or f"{item.get('marca', '')} {item.get('identificacao', '')}".strip()
            )
            equipment_records.append(str(registro).strip())
        equipment_text = "; ".join([r for r in equipment_records if r])
        measurement_text = "; ".join(
            [
                str(
                    measurements.get(str(item.get("codigo") or ""), {}).get("id")
                    or item.get("measurement_id")
                    or ""
                )
                for item in equipment_items
                if (measurements.get(str(item.get("codigo") or ""), {}).get("id") or item.get("measurement_id"))
            ]
        )
        photos_registros = "; ".join(
            [str(p.get("identificacao_registro") or "") for p in v.get("photos", []) if p.get("identificacao_registro")]
        )
        weather = v.get("weather") if isinstance(v.get("weather"), dict) else {}
        forms_data = v.get("forms") if isinstance(v.get("forms"), dict) else {}
        try:
            forms_structured = json.dumps(forms_data, ensure_ascii=False)
        except Exception:
            forms_structured = str(forms_data)
        caderno = v.get("caderno_avaliacao") if isinstance(v.get("caderno_avaliacao"), dict) else {}
        status_excel = str(v.get("status") or "").strip()
        if not status_excel or status_excel.upper() == "N/A":
            status_excel = "Não visitado"
        data.append({
            "ID Visita": v_id,
            "ID Cliente": v.get("client_id"),
            "Cliente": v.get("client_name"),
            "Data da Visita": v.get("date"),
            "Data Início": v.get("date_start") or v.get("date"),
            "Data Término": v.get("date_end") or "",
            "Horário": v.get("horario", ""),
            "Técnico Responsável": v.get("technician"),
            "Funcionário": (v.get("worker") or {}).get("name") if isinstance(v.get("worker"), dict) else v.get("worker_name", ""),
            "Situação": status_excel,
            "Qtd Equipamentos (Dosimetria)": len(equipment_items),
            "Equipamentos (Dosimetria de Ruído)": equipment_text,
            "Medições Vinculadas": measurement_text,
            "Identificações em Fotografias": photos_registros,
            "Qtd Fotografias": photos_count,
            "Descrição Fotografias": photos_desc,
            "Assinatura Responsável Técnico": technical.get("name", ""),
            "Assinatura Avaliador": evaluator.get("name", ""),
            "Observações": v.get("observations"),
            "Conclusões": v.get("conclusions"),
            "Temperatura Externa (°C)": weather.get("temperature_c"),
            "Temperatura Interna (°C)": weather.get("internal_temperature_c"),
            "Umidade (%)": weather.get("humidity_pct"),
            "Origem Temperatura": weather.get("source", ""),
            "Horário Consulta Temperatura": weather.get("captured_at", ""),
            "Formulário (estruturado)": forms_structured,
            "Caderno - Empresa Avaliada": caderno.get("empresa_avaliada", ""),
            "Caderno - Unidade": caderno.get("unidade", ""),
            "Caderno - Estado": caderno.get("estado", ""),
            "Caderno - Agente Químico": caderno.get("agente_quimico", ""),
            "Caderno - Data de Amostragem": caderno.get("data_amostragem", ""),
            "Caderno - Identificação da Amostra": caderno.get("identificacao_amostra", ""),
            "Caderno - Hora Inicial": caderno.get("hora_inicial", ""),
            "Caderno - Hora Final": caderno.get("hora_final", ""),
            "Caderno - Vazão (L/Min)": caderno.get("vazao_l_min", ""),
            "Caderno - Temperatura (amostragem)": caderno.get("temperatura_amostragem", ""),
            "Caderno - Setor": caderno.get("setor", ""),
            "Caderno - Funcionário": caderno.get("funcionario", ""),
            "Caderno - Função": caderno.get("funcao", ""),
            "Caderno - Matrícula": caderno.get("matricula", ""),
            "Caderno - Atividades Desenvolvidas": caderno.get("atividades_desenvolvidas", ""),
            "Caderno - EPI": caderno.get("epi", ""),
            "Caderno - EPC": caderno.get("epc", ""),
            "Caderno - Obs.": caderno.get("obs", ""),
            "Caderno - Funcionário/Responsável": caderno.get("responsavel_funcionario", ""),
            "Caderno - Nome Responsável": caderno.get("nome_responsavel", ""),
            "Caderno - Avaliador": caderno.get("avaliador", ""),
            "Caderno - Nome do Avaliador": caderno.get("nome_avaliador", ""),
            "Última Atualização": v.get("updated_at"),
        })
        
    df = pd.DataFrame(data)
    filename = f"Visitas_Tecnicas_ACNnorte_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    filepath = os.path.join(EXPORTS_DIR, filename)
    df.to_excel(filepath, index=False)
    return filepath
