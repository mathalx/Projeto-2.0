"""Testes de persistência das assinaturas digitais (CHANGE 04)."""

import os

import pytest

import src.storage_manager as storage

# PNG 1x1 válido, usado apenas para simular o desenho exportado pelo canvas.
_PNG_1X1 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk"
    "+A8AAQUBAScY42YAAAAASUVORK5CYII="
)
_DATA_URL = f"data:image/png;base64,{_PNG_1X1}"


@pytest.fixture()
def isolated_storage(tmp_path, monkeypatch):
    data_dir = tmp_path / "data"
    photos_dir = data_dir / "photos"

    monkeypatch.setattr(storage, "DATA_DIR", str(data_dir))
    monkeypatch.setattr(storage, "CLIENTS_FILE", str(data_dir / "clients.json"))
    monkeypatch.setattr(storage, "VISITS_FILE", str(data_dir / "visits.json"))
    monkeypatch.setattr(storage, "PHOTOS_DIR", str(photos_dir))
    storage.init_storage()
    return storage


def _create_visit(store):
    ok, client_id, _ = store.add_client(
        "Empresa Teste",
        "00.000.000/0001-00",
        "Rua A",
        "Resp",
        "11999999999",
        "a@b.com",
    )
    assert ok
    ok, visit_id, _ = store.add_visit(
        client_id, "Ana.norte", "2026-11-12", status="Em Andamento"
    )
    assert ok
    return visit_id


def test_new_visit_has_empty_signature_records(isolated_storage):
    visit_id = _create_visit(isolated_storage)
    visit = isolated_storage.load_visits()[visit_id]

    for role in ("technical", "evaluator"):
        signature = visit["signatures"][role]
        assert signature["name"] == ""
        assert signature["path"] == ""
        assert signature["signed_at"] == ""
        assert isolated_storage.visit_has_signature(visit, role) is False


def test_save_signature_name_and_image(isolated_storage):
    visit_id = _create_visit(isolated_storage)

    ok, message = isolated_storage.save_visit_signature(
        visit_id,
        "technical",
        name="  Maria Silva  ",
        data_url=_DATA_URL,
    )

    assert ok, message
    visit = isolated_storage.load_visits()[visit_id]
    signature = visit["signatures"]["technical"]
    assert signature["name"] == "Maria Silva"
    assert signature["signed_at"]
    assert os.path.exists(signature["path"])
    assert isolated_storage.visit_has_signature(visit, "technical") is True
    assert isolated_storage.missing_signatures(visit) == ["Avaliador"]


def test_save_both_signatures_clears_pending_list(isolated_storage):
    visit_id = _create_visit(isolated_storage)

    isolated_storage.save_visit_signature(
        visit_id, "technical", name="Maria", data_url=_DATA_URL
    )
    isolated_storage.save_visit_signature(
        visit_id, "evaluator", name="João", data_url=_DATA_URL
    )

    visit = isolated_storage.load_visits()[visit_id]
    assert isolated_storage.missing_signatures(visit) == []
    assert isolated_storage.visit_has_signature(visit, "technical") is True
    assert isolated_storage.visit_has_signature(visit, "evaluator") is True


def test_clearing_signature_removes_file_but_keeps_name(isolated_storage):
    visit_id = _create_visit(isolated_storage)
    isolated_storage.save_visit_signature(
        visit_id, "technical", name="Maria", data_url=_DATA_URL
    )
    saved_path = isolated_storage.load_visits()[visit_id]["signatures"][
        "technical"
    ]["path"]

    ok, _ = isolated_storage.save_visit_signature(
        visit_id, "technical", data_url=""
    )

    assert ok
    visit = isolated_storage.load_visits()[visit_id]
    signature = visit["signatures"]["technical"]
    assert signature["name"] == "Maria"
    assert signature["path"] == ""
    assert os.path.exists(saved_path) is False
    assert isolated_storage.visit_has_signature(visit, "technical") is False


def test_invalid_signature_payload_is_rejected(isolated_storage):
    visit_id = _create_visit(isolated_storage)

    ok, message = isolated_storage.save_visit_signature(
        visit_id,
        "technical",
        data_url="data:text/plain;base64,abc",
    )

    assert ok is False
    assert "inválido" in message.lower() or "formato" in message.lower()


def test_remove_signature_keeps_name(isolated_storage):
    visit_id = _create_visit(isolated_storage)
    isolated_storage.save_visit_signature(
        visit_id, "evaluator", name="João", data_url=_DATA_URL
    )

    ok, _ = isolated_storage.remove_visit_signature(visit_id, "evaluator")

    assert ok
    visit = isolated_storage.load_visits()[visit_id]
    signature = visit["signatures"]["evaluator"]
    assert signature["name"] == "João"
    assert signature["path"] == ""
    assert isolated_storage.visit_has_signature(visit, "evaluator") is False


def test_signature_returns_error_for_unknown_visit(isolated_storage):
    ok, message = isolated_storage.save_visit_signature(
        "nao-existe", "technical", name="Maria", data_url=_DATA_URL
    )

    assert ok is False
    assert "não encontrada" in message.lower()
