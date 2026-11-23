"""Testes da seleção de equipamentos de Dosimetria de Ruído (CHANGE 05)."""

import pytest

import src.storage_manager as storage
from src.equipment_catalog import (
    DEFAULT_CATEGORY,
    equipment_catalog,
    equipment_grouped,
    normalize_equipment_codes,
)


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


def test_catalog_has_only_team_provided_options():
    catalog = equipment_catalog()
    assert len(catalog) == 6

    grouped = equipment_grouped()
    assert list(grouped.keys()) == [DEFAULT_CATEGORY]
    assert set(grouped[DEFAULT_CATEGORY].keys()) == {"Chrompack", "Instrutherm"}

    chrompack = {
        item["identificacao"]
        for item in grouped[DEFAULT_CATEGORY]["Chrompack"]
    }
    assert chrompack == {"2386", "3440", "2319", "3558", "5981"}

    instrutherm = grouped[DEFAULT_CATEGORY]["Instrutherm"]
    assert [item["identificacao"] for item in instrutherm] == ["DOS-100X"]

    assert all(item["categoria"] == DEFAULT_CATEGORY for item in catalog)


def test_new_visit_has_empty_equipment_and_measurements(isolated_storage):
    visit_id = _create_visit(isolated_storage)
    visit = isolated_storage.load_visits()[visit_id]

    assert visit["equipment"]["category"] == DEFAULT_CATEGORY
    assert visit["equipment"]["selected"] == []
    assert visit["measurements"] == []
    assert isolated_storage.get_visit_equipment(visit) == []
    assert isolated_storage.missing_equipment(visit) == [
        "Pelo menos um equipamento de Dosimetria de Ruído"
    ]


def test_save_equipment_creates_measurement_links(isolated_storage):
    visit_id = _create_visit(isolated_storage)

    ok, message = isolated_storage.save_visit_equipment(
        visit_id, ["CHR-2386", "INS-DOS-100X"]
    )

    assert ok, message
    visit = isolated_storage.load_visits()[visit_id]
    selected = isolated_storage.get_visit_equipment(visit)
    measurements = isolated_storage.get_visit_measurements(visit)

    assert [item["identificacao"] for item in selected] == ["2386", "DOS-100X"]
    assert [item["equipment_code"] for item in measurements] == [
        "CHR-2386",
        "INS-DOS-100X",
    ]
    assert all(item["measurement_id"] for item in selected)
    assert {item["measurement_id"] for item in selected} == {
        item["id"] for item in measurements
    }
    assert isolated_storage.missing_equipment(visit) == []
    assert isolated_storage.visit_equipment_labels(visit) == [
        "Chrompack · 2386",
        "Instrutherm · DOS-100X",
    ]


def test_save_equipment_preserves_catalog_order_and_removes_deselected(
    isolated_storage,
):
    visit_id = _create_visit(isolated_storage)

    ok, _ = isolated_storage.save_visit_equipment(
        visit_id,
        [
            "CHR-2386",
            "CHR-3440",
            "CHR-2319",
            "CHR-3558",
            "CHR-5981",
            "INS-DOS-100X",
        ],
    )
    assert ok

    ok, _ = isolated_storage.save_visit_equipment(
        visit_id, ["INS-DOS-100X", "CHR-3440"]
    )
    assert ok

    visit = isolated_storage.load_visits()[visit_id]
    selected = isolated_storage.get_visit_equipment(visit)
    measurements = isolated_storage.get_visit_measurements(visit)

    assert [item["identificacao"] for item in selected] == ["3440", "DOS-100X"]
    assert [item["equipment_code"] for item in measurements] == [
        "CHR-3440",
        "INS-DOS-100X",
    ]
    assert len(measurements) == 2


def test_unknown_equipment_code_is_rejected(isolated_storage):
    visit_id = _create_visit(isolated_storage)

    ok, message = isolated_storage.save_visit_equipment(
        visit_id, ["CHR-03611"]
    )

    assert ok is False
    assert "não cadastrado" in message.lower()
    visit = isolated_storage.load_visits()[visit_id]
    assert isolated_storage.get_visit_equipment(visit) == []


def test_measurement_extra_fields_are_preserved_on_resave(isolated_storage):
    visit_id = _create_visit(isolated_storage)
    isolated_storage.save_visit_equipment(visit_id, ["CHR-2386"])

    visits = isolated_storage.load_visits()
    visits[visit_id]["measurements"][0]["resultado_db"] = 87.5
    isolated_storage.save_visits(visits)

    isolated_storage.save_visit_equipment(
        visit_id, ["CHR-2386", "CHR-3440"]
    )

    visit = isolated_storage.load_visits()[visit_id]
    measurements = {
        item["equipment_code"]: item
        for item in isolated_storage.get_visit_measurements(visit)
    }
    assert measurements["CHR-2386"]["resultado_db"] == 87.5
    assert measurements["CHR-3440"]["id"] == "meas_CHR-3440"


def test_legacy_devices_are_read_as_equipment(isolated_storage):
    visit_id = _create_visit(isolated_storage)
    visits = isolated_storage.load_visits()
    visits[visit_id].pop("equipment", None)
    visits[visit_id].pop("measurements", None)
    visits[visit_id]["devices"] = [
        {"codigo": "CHR-SMARTDB-03440", "identificacao": "03440"},
        {"codigo": "CHR-SMARTDB-02386", "identificacao": "02386"},
    ]
    isolated_storage.save_visits(visits)

    visit = isolated_storage.load_visits()[visit_id]
    selected = isolated_storage.get_visit_equipment(visit)
    assert [item["codigo"] for item in selected] == ["CHR-2386", "CHR-3440"]
    assert len(isolated_storage.get_visit_measurements(visit)) == 2


def test_normalize_equipment_codes_rejects_unknown_codes():
    with pytest.raises(ValueError):
        normalize_equipment_codes(["CHR-2386", "NAO-EXISTE"])


def test_save_equipment_returns_error_for_unknown_visit(isolated_storage):
    ok, message = isolated_storage.save_visit_equipment(
        "nao-existe", ["CHR-2386"]
    )
    assert ok is False
    assert "não encontrada" in message.lower()
