TECHNICAL_FORM_SECTIONS = {
    "epi": {
        "title": "1. Equipamentos de Proteção Individual (EPI) - NR-06",
        "fields": [
            {"id": "epi_fornecimento", "label": "A empresa fornece EPIs adequados a todos os colaboradores?", "type": "select", "required": True, "options": ["Sim", "Não", "Parcial", "N/A"]},
            {"id": "epi_uso", "label": "Os colaboradores fazem o uso correto e obrigatório dos EPIs?", "type": "select", "required": True, "options": ["Sim", "Não", "Parcial", "N/A"]},
            {"id": "epi_conservacao", "label": "Os EPIs encontram-se em bom estado de conservação e higienização?", "type": "select", "required": True, "options": ["Sim", "Não", "Parcial", "N/A"]},
            {"id": "epi_ca", "label": "Os EPIs possuem Certificado de Aprovação (CA) válido?", "type": "select", "required": True, "options": ["Sim", "Não", "N/A"]},
            {"id": "epi_obs", "label": "Observações sobre EPIs", "type": "text", "required": False}
        ]
    },
    "condicoes": {
        "title": "2. Condições Gerais e Instalações - NR-24 / NR-08",
        "fields": [
            {"id": "cond_sanitarios", "label": "Instalações sanitárias limpas, funcionais e em número adequado?", "type": "select", "required": True, "options": ["Sim", "Não", "Parcial", "N/A"]},
            {"id": "cond_iluminacao", "label": "Iluminação adequada nos postos de trabalho?", "type": "select", "required": True, "options": ["Sim", "Não", "Parcial", "N/A"]},
            {"id": "cond_ventilacao", "label": "Ambiente de trabalho ventilado e com temperatura adequada?", "type": "select", "required": True, "options": ["Sim", "Não", "Parcial", "N/A"]},
            {"id": "cond_ordem", "label": "Organização, limpeza e arrumação geral (Housekeeping) mantida?", "type": "select", "required": True, "options": ["Sim", "Não", "Parcial", "N/A"]},
            {"id": "cond_obs", "label": "Observações sobre Condições Gerais", "type": "text", "required": False}
        ]
    },
    "incendio": {
        "title": "3. Segurança contra Incêndio e Pânico - IT / NR-23",
        "fields": [
            {"id": "inc_extintores", "label": "Extintores dentro do prazo de validade e com carga em dia?", "type": "select", "required": True, "options": ["Sim", "Não", "Parcial", "N/A"]},
            {"id": "inc_desobstrucao", "label": "Extintores e hidrantes desobstruídos e com acesso livre?", "type": "select", "required": True, "options": ["Sim", "Não", "Parcial", "N/A"]},
            {"id": "inc_sinalizacao", "label": "Sinalização de emergência e rotas de fuga visíveis e iluminadas?", "type": "select", "required": True, "options": ["Sim", "Não", "Parcial", "N/A"]},
            {"id": "inc_saidas", "label": "Saídas de emergência livres de trancas ou obstáculos?", "type": "select", "required": True, "options": ["Sim", "Não", "N/A"]},
            {"id": "inc_obs", "label": "Observações sobre Incêndio e Pânico", "type": "text", "required": False}
        ]
    },
    "maquinas": {
        "title": "4. Segurança em Máquinas e Equipamentos - NR-12",
        "fields": [
            {"id": "maq_protecoes", "label": "Máquinas possuem proteções fixas ou móveis intertravadas?", "type": "select", "required": True, "options": ["Sim", "Não", "Parcial", "N/A"]},
            {"id": "maq_botoeiras", "label": "Dispositivos de parada de emergência (botão de emergência) operacionais?", "type": "select", "required": True, "options": ["Sim", "Não", "Parcial", "N/A"]},
            {"id": "maq_eletrica", "label": "Instalações elétricas aparentes protegidas contra choques e curtos?", "type": "select", "required": True, "options": ["Sim", "Não", "Parcial", "N/A"]},
            {"id": "maq_obs", "label": "Observações sobre Máquinas e Equipamentos", "type": "text", "required": False}
        ]
    },
    "documentacao": {
        "title": "5. Documentação e Programas de Segurança - PGR / PCMSO / CIPA",
        "fields": [
            {"id": "doc_pgr", "label": "Programa de Gerenciamento de Riscos (PGR) elaborado e atualizado?", "type": "select", "required": True, "options": ["Sim", "Não", "Em Andamento", "N/A"]},
            {"id": "doc_pcmso", "label": "PCMSO e ASOs dos funcionários em dia?", "type": "select", "required": True, "options": ["Sim", "Não", "Em Andamento", "N/A"]},
            {"id": "doc_cipa", "label": "CIPA ou Designado constituído e atuante (quando aplicável)?", "type": "select", "required": True, "options": ["Sim", "Não", "N/A"]},
            {"id": "doc_treinamento", "label": "Integração e treinamentos de segurança registrados?", "type": "select", "required": True, "options": ["Sim", "Não", "Parcial", "N/A"]},
            {"id": "doc_obs", "label": "Observações sobre Documentação", "type": "text", "required": False}
        ]
    }
}


# Rótulo exibido quando um campo obrigatório ainda não foi respondido.
UNANSWERED_LABEL = "— Selecione —"


def field_is_required(field: dict) -> bool:
    """Campos de seleção são obrigatórios; textos livres são opcionais."""
    return bool(field.get("required", field.get("type") == "select"))


def is_answered(value) -> bool:
    return str(value or "").strip() not in ("", UNANSWERED_LABEL)


def section_completion(cat_key: str, answers: dict) -> tuple:
    """Retorna (respondidos, total) considerando apenas campos obrigatórios."""
    fields = TECHNICAL_FORM_SECTIONS.get(cat_key, {}).get("fields", [])
    required = [f for f in fields if field_is_required(f)]
    answered = sum(1 for f in required if is_answered((answers or {}).get(f["id"])))
    return answered, len(required)


def visit_completion(forms: dict) -> tuple:
    """Progresso geral do formulário de uma visita."""
    forms = forms or {}
    answered = 0
    total = 0
    for cat_key in TECHNICAL_FORM_SECTIONS:
        cat_answered, cat_total = section_completion(cat_key, forms.get(cat_key, {}))
        answered += cat_answered
        total += cat_total
    return answered, total


def first_unanswered_section(forms: dict) -> int:
    """Índice da primeira seção com campos obrigatórios pendentes."""
    forms = forms or {}
    for index, cat_key in enumerate(TECHNICAL_FORM_SECTIONS):
        answered, total = section_completion(cat_key, forms.get(cat_key, {}))
        if answered < total:
            return index
    return len(TECHNICAL_FORM_SECTIONS)
