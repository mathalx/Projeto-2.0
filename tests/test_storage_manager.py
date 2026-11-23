import json
import os

import pandas as pd
import pytest

import src.export_manager as export_manager
import src.storage_manager as storage
from src.form_template import (
    first_unanswered_section,
    section_completion,
    visit_completion,
)

# PNG 1x1 válido para simular a assinatura exportada pelo canvas.
SIGNATURE_DATA_URL = (
    "data:image/png;base64,"
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk"
    "+A8AAQUBAScY42YAAAAASUVORK5CYII="
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
    storage.save_visit_signature(
        visit_id,
        "technical",
        name="Responsável Técnico",
        data_url=SIGNATURE_DATA_URL,
    )
    storage.save_visit_signature(
        visit_id,
        "evaluator",
        name="Avaliador",
        data_url=SIGNATURE_DATA_URL,
    )
    storage.save_visit_equipment(
        visit_id, ["CHR-2386", "INS-DOS-100X"]
    )

    pdf_path = export_manager.generate_pdf_report(visit_id)
    assert pdf_path and os.path.exists(pdf_path)

    visit = storage.load_visits()[visit_id]
    assert storage.visit_has_signature(visit, "technical")
    assert storage.visit_has_signature(visit, "evaluator")
    assert storage.missing_signatures(visit) == []
    assert storage.missing_equipment(visit) == []

    clients_xlsx = export_manager.export_clients_to_excel()
    assert clients_xlsx and os.path.exists(clients_xlsx)

    visits_xlsx = export_manager.export_visits_to_excel()
    assert visits_xlsx and os.path.exists(visits_xlsx)
    visits_df = pd.read_excel(visits_xlsx)
    assert "Equipamentos (Dosimetria de Ruído)" in visits_df.columns
    assert "Chrompack 2386" in visits_df.iloc[0][
        "Equipamentos (Dosimetria de Ruído)"
    ]


# ---------------------------------------------------------------------------
# CHANGE 02 — Identificação do funcionário com foto
# ---------------------------------------------------------------------------

def test_worker_photo_save_and_remove(isolated_storage):
    """save_worker_photo persiste o arquivo; remove_worker_photo apaga e limpa."""
    storage.init_storage()
    _ok, client_id, _ = storage.add_client(
        "Empresa X", "1", "Rua A", "Resp", "Tel", "x@x.com"
    )
    _ok, visit_id, _ = storage.add_visit(client_id, "Técnico", "2026-06-01")

    fake_bytes = b"\x89PNG\r\n\x1a\n" + b"\x00" * 20  # bytes mínimos de PNG fake
    success, path, msg = storage.save_worker_photo(visit_id, fake_bytes, "foto.png")
    assert success, msg
    assert path and os.path.exists(path)

    visit = storage.load_visits()[visit_id]
    assert isinstance(visit.get("worker"), dict)
    assert visit["worker"]["photo_path"] == path
    assert visit.get("worker_photo") == path

    # Remove a foto — arquivo deve ser deletado e campo limpo
    success, msg = storage.remove_worker_photo(visit_id)
    assert success, msg
    assert not os.path.exists(path)

    visit = storage.load_visits()[visit_id]
    assert visit["worker"]["photo_path"] == ""
    assert visit.get("worker_photo") == ""


def test_worker_photo_replaces_old_file(isolated_storage):
    """Salvar uma nova foto exclui a foto anterior do disco."""
    storage.init_storage()
    _ok, client_id, _ = storage.add_client(
        "Empresa Y", "2", "Rua B", "Resp2", "Tel2", "y@y.com"
    )
    _ok, visit_id, _ = storage.add_visit(client_id, "Técnico", "2026-06-02")

    fake_bytes = b"\x89PNG\r\n" + b"\x00" * 10
    _ok, path1, _ = storage.save_worker_photo(visit_id, fake_bytes, "foto1.png")
    assert os.path.exists(path1)

    _ok, path2, _ = storage.save_worker_photo(visit_id, fake_bytes, "foto2.jpg")
    assert os.path.exists(path2)
    assert not os.path.exists(path1), "O arquivo antigo deveria ter sido removido"


def test_update_worker_info(isolated_storage):
    """update_worker_info atualiza nome no dicionário worker e campo worker_name."""
    storage.init_storage()
    _ok, client_id, _ = storage.add_client(
        "Empresa Z", "3", "Rua C", "Resp3", "Tel3", "z@z.com"
    )
    _ok, visit_id, _ = storage.add_visit(client_id, "Técnico", "2026-06-03")

    success, msg = storage.update_worker_info(visit_id, "  João Silva  ")
    assert success, msg

    visit = storage.load_visits()[visit_id]
    assert visit["worker"]["name"] == "João Silva"
    assert visit["worker_name"] == "João Silva"


def test_worker_functions_reject_unknown_visit(isolated_storage):
    """Funções de worker retornam erro para visit_id inexistente."""
    storage.init_storage()
    fake_id = "nao-existe-999"

    success, path, msg = storage.save_worker_photo(fake_id, b"bytes", "f.jpg")
    assert not success
    assert path == ""

    success, msg = storage.remove_worker_photo(fake_id)
    assert not success

    success, msg = storage.update_worker_info(fake_id, "Alguém")
    assert not success


def test_add_visit_stores_worker_name(isolated_storage):
    """add_visit aceita worker_name e o persiste corretamente."""
    storage.init_storage()
    _ok, client_id, _ = storage.add_client(
        "Empresa W", "4", "Rua D", "Resp4", "Tel4", "w@w.com"
    )
    _ok, visit_id, _ = storage.add_visit(
        client_id, "Técnico", "2026-06-04", worker_name="Maria Costa"
    )

    visit = storage.load_visits()[visit_id]
    assert visit.get("worker_name") == "Maria Costa"
