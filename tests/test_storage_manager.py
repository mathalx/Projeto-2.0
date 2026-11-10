import json
import os

import pytest

import src.export_manager as export_manager
import src.storage_manager as storage
from src.form_template import (
    first_unanswered_section,
    section_completion,
    visit_completion,
)


@pytest.fixture()
def isolated_storage(tmp_path, monkeypatch):
    """Redireciona o armazenamento para uma pasta temporária isolada."""
    data_dir = tmp_path / "data"
    photos_dir = data_dir / "photos"
    exports_dir = data_dir / "exports"

    monkeypatch.setattr(storage, "DATA_DIR", str(data_dir))
    monkeypatch.setattr(storage, "CLIENTS_FILE", str(data_dir / "clients.json"))
    monkeypatch.setattr(storage, "VISITS_FILE", str(data_dir / "visits.json"))
    monkeypatch.setattr(storage, "PHOTOS_DIR", str(photos_dir))
    monkeypatch.setattr(export_manager, "EXPORTS_DIR", str(exports_dir))
    return tmp_path


def test_init_storage_is_idempotent_and_preserves_data(isolated_storage):
    storage.init_storage()
    storage.init_storage()

    assert os.path.isdir(storage.DATA_DIR)
    assert os.path.isdir(storage.PHOTOS_DIR)
    assert os.path.exists(storage.CLIENTS_FILE)
    assert os.path.exists(storage.VISITS_FILE)

    storage.save_clients({"abc": {"id": "abc", "name": "Empresa"}})
    storage.save_visits({"v1": {"id": "v1", "status": "Rascunho"}})

    # Reexecutar a inicialização não pode apagar nem duplicar dados.
    storage.init_storage()
    storage.init_storage()

    assert storage.load_clients() == {"abc": {"id": "abc", "name": "Empresa"}}
    assert storage.load_visits() == {"v1": {"id": "v1", "status": "Rascunho"}}


def test_save_functions_only_write_json(isolated_storage):
    storage.init_storage()
    storage.save_clients({"x": {"id": "x"}})
    storage.save_visits({})

    with open(storage.CLIENTS_FILE, "r", encoding="utf-8") as file:
        assert json.load(file) == {"x": {"id": "x"}}
    with open(storage.VISITS_FILE, "r", encoding="utf-8") as file:
        assert json.load(file) == {}


def test_client_crud(isolated_storage):
    storage.init_storage()

    success, client_id, message = storage.add_client(
        "Empresa A", "00.000.000/0001-00", "Rua 1", "Fulano", "99999-9999", "a@a.com"
    )
    assert success and client_id
    assert storage.load_clients()[client_id]["name"] == "Empresa A"

    success, _ = storage.update_client(
        client_id, "Empresa B", "00.000.000/0001-00", "Rua 2", "Beltrano", "88888-8888", "b@b.com"
    )
    assert success
    assert storage.load_clients()[client_id]["name"] == "Empresa B"

    success, _ = storage.delete_client(client_id)
    assert success
    assert storage.load_clients() == {}


def test_visit_and_photos_flow(isolated_storage):
    storage.init_storage()
    _success, client_id, _ = storage.add_client(
        "Empresa", "1", "Rua", "Resp", "Tel", "mail@x.com"
    )
    success, visit_id, _ = storage.add_visit(client_id, "Técnico", "2026-01-01")
    assert success

    forms = {"epi": {"epi_fornecimento": "Sim"}}
    success, _ = storage.update_visit(visit_id, forms, "Obs", "Conclusão", "Em Andamento")
    assert success
    assert storage.load_visits()[visit_id]["status"] == "Em Andamento"

    success, _ = storage.add_photo_to_visit(visit_id, b"fake-image", "foto.jpg", "Legenda")
    assert success
    photo = storage.load_visits()[visit_id]["photos"][0]
    assert os.path.exists(photo["path"])

    success, _ = storage.replace_photo_in_visit(
        visit_id, photo["id"], b"new-image", "nova.png", "Nova legenda"
    )
    assert success
    replaced = storage.load_visits()[visit_id]["photos"][0]
    assert replaced["description"] == "Nova legenda"
    assert os.path.exists(replaced["path"])
    assert not os.path.exists(photo["path"])

    success, _ = storage.remove_photo_from_visit(visit_id, replaced["id"])
    assert success
    assert storage.load_visits()[visit_id]["photos"] == []
    assert not os.path.exists(replaced["path"])


def test_form_helpers():
    forms = {
        "epi": {
            "epi_fornecimento": "Sim",
            "epi_uso": "Não",
            "epi_conservacao": "Parcial",
            "epi_ca": "Sim",
            "epi_obs": "ok",
        }
    }
    assert section_completion("epi", forms["epi"]) == (4, 4)
    assert section_completion("epi", {}) == (0, 4)

    answered, total = visit_completion(forms)
    assert answered == 4
    assert total == 19
    assert first_unanswered_section(forms) == 1


def test_exports_generate_files(isolated_storage):
    storage.init_storage()
    _success, client_id, _ = storage.add_client(
        "Empresa", "1", "Rua", "Resp", "Tel", "mail@x.com"
    )
    _success, visit_id, _ = storage.add_visit(client_id, "Técnico", "2026-01-01")
    storage.update_visit(visit_id, {}, "Obs", "Conclusão", "Finalizada")

    pdf_path = export_manager.generate_pdf_report(visit_id)
    assert pdf_path and os.path.exists(pdf_path)

    clients_xlsx = export_manager.export_clients_to_excel()
    assert clients_xlsx and os.path.exists(clients_xlsx)

    visits_xlsx = export_manager.export_visits_to_excel()
    assert visits_xlsx and os.path.exists(visits_xlsx)
