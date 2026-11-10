import base64
import io
import os
import pandas as pd
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage, KeepTogether, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from src.storage_manager import load_clients, load_visits, DATA_DIR

EXPORTS_DIR = os.path.join(DATA_DIR, "exports")


def init_exports_dir():
    os.makedirs(EXPORTS_DIR, exist_ok=True)


def _decode_data_url(value: str | None) -> bytes | None:
    """Converte uma assinatura Base64/data URL em bytes PNG."""
    if not value:
        return None
    text = str(value).strip()
    if "," in text and text.lower().startswith("data:"):
        text = text.split(",", 1)[1]
    try:
        return base64.b64decode(text)
    except (ValueError, TypeError):
        return None


def _signature_flowable(value: str | None, normal_style):
    raw = _decode_data_url(value)
    if not raw:
        return Paragraph("Assinatura não registrada", normal_style)
    try:
        return RLImage(io.BytesIO(raw), width=190, height=62, kind="proportional")
    except Exception:
        return Paragraph("Assinatura registrada (imagem indisponível)", normal_style)


def _format_calibration(item: dict) -> str:
    value = str(item.get("data_ultima_calibracao") or "").strip()
    if not value:
        return "Não informada"
    try:
        return datetime.strptime(value[:10], "%Y-%m-%d").strftime("%d/%m/%Y")
    except ValueError:
        return value

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
    
    # Client, climate and visit information.
    company_name = (
        client.get("name")
        or visit.get("empresa_nome")
        or visit.get("client_name")
        or "N/A"
    )
    start_date = visit.get("data_avaliacao") or visit.get("date") or "N/A"
    end_date = visit.get("data_avaliacao_fim") or start_date
    period = f"{start_date} a {end_date}" if end_date and end_date != start_date else start_date

    temperature = visit.get("temperatura_capturada")
    humidity = visit.get("umidade_capturada")
    temperature_text = (
        f"{float(temperature):.1f} °C" if temperature not in (None, "") else "Não capturada"
    )
    humidity_text = (
        f"{float(humidity):.0f}%" if humidity not in (None, "") else "Não capturada"
    )

    client_data = [
        [Paragraph("<b>Empresa Cliente:</b>", bold_style), Paragraph(company_name, normal_style)],
        [Paragraph("<b>CNPJ:</b>", bold_style), Paragraph(client.get('cnpj', 'N/A'), normal_style)],
        [Paragraph("<b>Endereço:</b>", bold_style), Paragraph(client.get('address', 'N/A'), normal_style)],
        [Paragraph("<b>Responsável na Empresa:</b>", bold_style), Paragraph(client.get('responsible', 'N/A'), normal_style)],
        [Paragraph("<b>Contato:</b>", bold_style), Paragraph(f"Tel: {client.get('phone', 'N/A')} | E-mail: {client.get('email', 'N/A')}", normal_style)],
        [Paragraph("<b>Período de Avaliação:</b>", bold_style), Paragraph(period, normal_style)],
        [Paragraph("<b>Temperatura / Umidade:</b>", bold_style), Paragraph(f"{temperature_text} / {humidity_text}", normal_style)],
        [Paragraph("<b>Técnico Responsável:</b>", bold_style), Paragraph(visit.get('technician', 'N/A'), normal_style)],
        [Paragraph("<b>Situação:</b>", bold_style), Paragraph(visit.get('status', 'N/A'), normal_style)]
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

    # Worker photo beside the name (CHANGE 09 / CHANGE 12).
    worker = visit.get("worker") or {}
    worker_name = worker.get("funcionario_nome") or "Não informado"
    worker_role = worker.get("funcao") or "—"
    worker_sector = worker.get("setor") or "—"
    worker_photo_path = worker.get("funcionario_foto_url")
    if worker_photo_path and os.path.exists(worker_photo_path):
        try:
            worker_photo = RLImage(worker_photo_path, width=92, height=92)
        except Exception:
            worker_photo = Paragraph("Foto indisponível", normal_style)
    else:
        worker_photo = Paragraph("Foto não anexada", normal_style)

    worker_info = Paragraph(
        f"<b>Funcionário avaliado:</b> {worker_name}<br/>"
        f"<b>Função:</b> {worker_role}<br/>"
        f"<b>Setor:</b> {worker_sector}",
        normal_style,
    )
    t_worker = Table([[worker_photo, worker_info]], colWidths=[112, 428])
    t_worker.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#E8F2EA")),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#A5CFAF")),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(Paragraph("Identificação do Funcionário Avaliado", section_style))
    story.append(t_worker)
    story.append(Spacer(1, 15))

    # Equipment detail table (CHANGE 10 / CHANGE 12).
    story.append(Paragraph("Equipamentos Utilizados", section_style))
    devices = visit.get("devices") or []
    if devices:
        equipment_rows = [[
            Paragraph("<b>Código</b>", bold_style),
            Paragraph("<b>Tipo</b>", bold_style),
            Paragraph("<b>Marca/Modelo</b>", bold_style),
            Paragraph("<b>Nº Série/Equipamento</b>", bold_style),
            Paragraph("<b>Certificado</b>", bold_style),
            Paragraph("<b>Calibração</b>", bold_style),
        ]]
        for item in devices:
            equipment_rows.append([
                Paragraph(str(item.get("codigo") or "—"), normal_style),
                Paragraph(str(item.get("tipo") or item.get("categoria") or "—"), normal_style),
                Paragraph(
                    f"{item.get('marca') or '—'} {item.get('modelo') or ''}".strip(),
                    normal_style,
                ),
                Paragraph(
                    str(item.get("num_serie") or item.get("num_equipamento") or "—"),
                    normal_style,
                ),
                Paragraph(str(item.get("certificado") or "—"), normal_style),
                Paragraph(_format_calibration(item), normal_style),
            ])
        t_equipment = Table(
            equipment_rows,
            colWidths=[78, 92, 95, 105, 72, 98],
            repeatRows=1,
        )
        t_equipment.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#E8F2EA")),
            ('BOX', (0, 0), (-1, -1), 0.75, colors.HexColor("#16834A")),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#D0D7DE")),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ]))
        story.append(t_equipment)
    else:
        story.append(Paragraph("Nenhum equipamento registrado.", normal_style))
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
            
            p_elements = [Paragraph(f"<b>Descrição:</b> {p_desc}<br/><font size=8 color='#59636A'>Enviado em: {p_date}</font>", normal_style)]
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

    # Digital signatures at the footer (CHANGE 12).
    signatures = visit.get("signatures") or {}
    story.append(Spacer(1, 18))
    story.append(Paragraph("Assinaturas Digitais", section_style))
    signature_table = Table(
        [
            [
                Paragraph("<b>Responsável Técnico</b>", bold_style),
                Paragraph("<b>Avaliador</b>", bold_style),
            ],
            [
                _signature_flowable(
                    signatures.get("ass_responsavel_tecnico"), normal_style
                ),
                _signature_flowable(signatures.get("ass_avaliador"), normal_style),
            ],
            [
                Paragraph("Assinatura digital", normal_style),
                Paragraph("Assinatura digital", normal_style),
            ],
        ],
        colWidths=[270, 270],
    )
    signature_table.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 0.75, colors.HexColor("#59636A")),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#D0D7DE")),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(KeepTogether([signature_table]))

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
        worker = v.get("worker") or {}
        devices = v.get("devices") or []
        device_codes = "; ".join(str(item.get("codigo") or "") for item in devices)
        signatures = v.get("signatures") or {}
        data.append({
            "ID Visita": v_id,
            "ID Cliente": v.get("client_id"),
            "Cliente": v.get("empresa_nome") or v.get("client_name"),
            "Data da Avaliação": v.get("data_avaliacao") or v.get("date"),
            "Data Final da Avaliação": v.get("data_avaliacao_fim"),
            "Temperatura (°C)": v.get("temperatura_capturada"),
            "Umidade (%)": v.get("umidade_capturada"),
            "Funcionário Avaliado": worker.get("funcionario_nome"),
            "Função": worker.get("funcao"),
            "Setor": worker.get("setor"),
            "Foto do Funcionário": worker.get("funcionario_foto_url"),
            "Equipamentos": device_codes,
            "Qtd Equipamentos": len(devices),
            "Técnico Responsável": v.get("technician"),
            "Situação": v.get("status"),
            "Qtd Fotografias": photos_count,
            "Descrição Fotografias": photos_desc,
            "Assinatura Responsável Técnico": bool(signatures.get("ass_responsavel_tecnico")),
            "Assinatura Avaliador": bool(signatures.get("ass_avaliador")),
            "Observações": v.get("observations"),
            "Conclusões": v.get("conclusions"),
            "Última Atualização": v.get("updated_at")
        })
        
    df = pd.DataFrame(data)
    filename = f"Visitas_Tecnicas_ACNnorte_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    filepath = os.path.join(EXPORTS_DIR, filename)
    df.to_excel(filepath, index=False)
    return filepath
