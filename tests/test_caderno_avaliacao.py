"""Testes do Caderno de Avaliação de Agentes Químicos e reorganização do fluxo de visitas."""

import src.export_manager as export_manager
import src.storage_manager as storage
from src.views.visits_view import _display_status, visit_identification_label


def _patch_storage(monkeypatch, tmp_path):
    data_dir = tmp_path / "data"
    monkeypatch.setattr(storage, "DATA_DIR", str(data_dir))
    monkeypatch.setattr(storage, "CLIENTS_FILE", str(data_dir / "clients.json"))
    monkeypatch.setattr(storage, "VISITS_FILE", str(data_dir / "visits.json"))
    monkeypatch.setattr(storage, "PHOTOS_DIR", str(data_dir / "photos"))
    monkeypatch.setattr(export_manager, "EXPORTS_DIR", str(data_dir / "exports"))
    storage.init_storage()


def _create_client_visit(monkeypatch, tmp_path):
    _patch_storage(monkeypatch, tmp_path)
    ok, client_id, _ = storage.add_client(
        "Empresa Química",
        "12.345.678/0001-90",
        "Rua A, 100",
        "Resp",
        "11999999999",
        "contato@empresa.com",
    )
    assert ok
    ok, visit_id, _ = storage.add_visit(
        client_id,
        "Ana Avaliadora",
        "2026-11-20",
        status="Em Andamento",
        worker_name="João da Silva",
        date_start="2026-11-20",
        date_end="2026-11-20",
        horario="14:30",
    )
    assert ok
    return client_id, visit_id


def test_caderno_created_with_defaults_and_linked_to_visit(monkeypatch, tmp_path):
    _client_id, visit_id = _create_client_visit(monkeypatch, tmp_path)
    visit = storage.load_visits()[visit_id]
    caderno = storage.get_caderno_avaliacao(visit)
    assert isinstance(caderno, dict)
    assert visit.get("horario") == "14:30"
    # campos principais presentes
    for field in [
        "empresa_avaliada",
        "unidade",
        "estado",
        "agente_quimico",
        "data_amostragem",
        "identificacao_amostra",
        "hora_inicial",
        "hora_final",
        "vazao_l_min",
        "temperatura_amostragem",
        "setor",
        "funcionario",
        "funcao",
        "matricula",
        "atividades_desenvolvidas",
        "epi",
        "epc",
        "obs",
        "responsavel_funcionario",
        "nome_responsavel",
        "avaliador",
        "nome_avaliador",
    ]:
        assert field in caderno


def test_caderno_save_update_and_recovery(monkeypatch, tmp_path):
    _client_id, visit_id = _create_client_visit(monkeypatch, tmp_path)
    payload = {
        "empresa_avaliada": "Empresa Química",
        "unidade": "Unidade Norte",
        "estado": "PA",
        "agente_quimico": "Benzeno",
        "data_amostragem": "2026-11-20",
        "identificacao_amostra": "AM-001",
        "hora_inicial": "08:00",
        "hora_final": "12:00",
        "vazao_l_min": "2.0",
        "temperatura_amostragem": "25.5",
        "setor": "Produção",
        "funcionario": "João da Silva",
        "funcao": "Operador",
        "matricula": "MAT-123",
        "atividades_desenvolvidas": "Operação de mistura",
        "epi": "Luva, respirador",
        "epc": "Exaustão local",
        "obs": "Sem intercorrências",
        "responsavel_funcionario": "João da Silva",
        "nome_responsavel": "João S.",
        "avaliador": "Ana Avaliadora",
        "nome_avaliador": "Ana A.",
    }
    ok, _ = storage.update_visit(
        visit_id,
        {},
        "",
        "",
        "Em Andamento",
        caderno_avaliacao=payload,
        horario="15:00",
    )
    assert ok
    visit = storage.load_visits()[visit_id]
    assert visit["horario"] == "15:00"
    caderno = storage.get_caderno_avaliacao(visit)
    for k, v in payload.items():
        assert caderno.get(k) == v

    # atualização parcial não deve apagar campos existentes
    ok, _ = storage.update_visit(
        visit_id,
        {},
        "",
        "",
        "Em Andamento",
        caderno_avaliacao={"obs": "Atualizado", "matricula": "MAT-999"},
    )
    assert ok
    visit = storage.load_visits()[visit_id]
    caderno = storage.get_caderno_avaliacao(visit)
    assert caderno["obs"] == "Atualizado"
    assert caderno["matricula"] == "MAT-999"
    assert caderno["agente_quimico"] == "Benzeno"
    assert caderno["unidade"] == "Unidade Norte"


def test_old_visit_compatibility_and_no_duplication(monkeypatch, tmp_path):
    _patch_storage(monkeypatch, tmp_path)
    ok, client_id, _ = storage.add_client("Empresa", "1", "R", "Resp", "1", "e@e.com")
    assert ok
    # visita antiga sem caderno/horario
    visits = storage.load_visits()
    visits["old1"] = {
        "id": "old1",
        "client_id": client_id,
        "client_name": "Empresa",
        "date": "2025-01-01",
        "technician": "Tec",
        "status": "Rascunho",
        "forms": {},
        "photos": [],
    }
    storage.save_visits(visits)

    loaded = storage.load_visits()["old1"]
    caderno = storage.get_caderno_avaliacao(loaded)
    assert isinstance(caderno, dict)
    assert caderno["agente_quimico"] == ""
    assert "empresa_avaliada" in caderno

    # atualizar visita antiga deve adicionar caderno sem sobrescrever dados existentes
    ok, _ = storage.update_visit(
        "old1",
        {"epi": {}},
        "obs antiga",
        "conc",
        "Em Andamento",
        caderno_avaliacao={"agente_quimico": "Solvente"},
    )
    assert ok
    updated = storage.load_visits()["old1"]
    assert updated["observations"] == "obs antiga"
    assert updated["date"] == "2025-01-01"
    assert storage.get_caderno_avaliacao(updated)["agente_quimico"] == "Solvente"

    # segunda atualização não deve duplicar estruturas
    storage.update_visit("old1", updated.get("forms", {}), "obs antiga", "conc", "Em Andamento", caderno_avaliacao={"obs": "x"})
    again = storage.load_visits()["old1"]
    assert isinstance(again.get("caderno_avaliacao"), dict)
    assert storage.get_caderno_avaliacao(again)["agente_quimico"] == "Solvente"


def test_visit_identification_label_and_nao_visitado_display():
    visit = {
        "date_start": "2026-11-20",
        "worker_name": "João da Silva",
        "horario": "14:30",
        "status": "Em Andamento",
    }
    label = visit_identification_label(visit)
    assert label == "20/11/2026 / João da Silva / 14:30"

    missing = {"date_start": "", "worker_name": "", "horario": "", "status": ""}
    label2 = visit_identification_label(missing)
    assert "Funcionário não identificado" in label2
    assert "Horário não informado" in label2

    assert _display_status("N/A") == "Não visitado"
    assert _display_status("") == "Não visitado"
    assert _display_status(None) == "Não visitado"
    assert _display_status("Rascunho") == "Rascunho"
    assert _display_status("Em Andamento") == "Em Andamento"


def test_export_pdf_and_excel_include_caderno(monkeypatch, tmp_path):
    client_id, visit_id = _create_client_visit(monkeypatch, tmp_path)
    storage.update_visit(
        visit_id,
        {},
        "Obs geral",
        "Conclusão",
        "Finalizada",
        caderno_avaliacao={
            "empresa_avaliada": "Empresa Química",
            "unidade": "Planta 1",
            "estado": "PA",
            "agente_quimico": "Tolueno",
            "data_amostragem": "2026-11-20",
            "identificacao_amostra": "AM-77",
            "hora_inicial": "09:00",
            "hora_final": "11:00",
            "vazao_l_min": "1.5",
            "temperatura_amostragem": "24",
            "setor": "Lab",
            "funcionario": "João da Silva",
            "funcao": "Técnico",
            "matricula": "M1",
            "atividades_desenvolvidas": "Análise",
            "epi": "Máscara",
            "epc": "Cabine",
            "obs": "OK",
            "responsavel_funcionario": "João",
            "nome_responsavel": "João da Silva",
            "avaliador": "Ana",
            "nome_avaliador": "Ana Avaliadora",
        },
    )
    # exportações não devem quebrar; PDF deve ser gerado
    pdf_path = export_manager.generate_pdf_report(visit_id)
    assert pdf_path

    xlsx_path = export_manager.export_visits_to_excel()
    assert xlsx_path
    import pandas as pd

    df = pd.read_excel(xlsx_path)
    assert "Caderno - Agente Químico" in df.columns
    row = df[df["ID Visita"] == visit_id].iloc[0]
    assert row["Horário"] == "14:30"
    assert row["Caderno - Agente Químico"] == "Tolueno"
    assert row["Caderno - Matrícula"] == "M1"


def test_reuse_existing_company_and_worker_data_without_duplication(monkeypatch, tmp_path):
    client_id, visit_id = _create_client_visit(monkeypatch, tmp_path)
    visits = storage.load_visits()
    visit = visits[visit_id]
    # empresa vem do cliente selecionado; funcionário vem da visita
    assert visit["client_id"] == client_id
    assert visit["client_name"] == "Empresa Química"
    assert visit["worker_name"] == "João da Silva"
    assert visit["horario"] == "14:30"

    # salvar caderno reutilizando dados não cria novo cliente/visita
    clients_before = storage.load_clients()
    visits_before = storage.load_visits()
    storage.update_visit(visit_id, {}, "", "", "Em Andamento", caderno_avaliacao={"funcionario": "João da Silva", "matricula": "ABC"})
    assert len(storage.load_clients()) == len(clients_before)
    assert len(storage.load_visits()) == len(visits_before)
    assert storage.load_visits()[visit_id]["worker_name"] == "João da Silva"
    assert storage.get_caderno_avaliacao(storage.load_visits()[visit_id])["matricula"] == "ABC"
