"""Testes de persistência da temperatura capturada na visita."""

import pytest

import src.storage_manager as storage


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
        "Empresa Teste", "00.000.000/0001-00", "Rua A", "Resp", "11999999999", "a@b.com"
    )
    assert ok
    ok, visit_id, _ = store.add_visit(client_id, "Ana.norte", "2026-11-12", status="Em Andamento")
    assert ok
    return visit_id


def test_new_visit_has_empty_weather_record(isolated_storage):
    visit_id = _create_visit(isolated_storage)
    visit = isolated_storage.load_visits()[visit_id]

    assert visit["weather"]["temperature_c"] is None
    assert visit["weather"]["internal_temperature_c"] is None
    assert visit["weather"]["humidity_pct"] is None
    assert visit["weather"]["source"] == ""
    assert visit["weather"]["captured_at"] == ""


def test_save_visit_weather_persists_reading_and_source(isolated_storage):
    visit_id = _create_visit(isolated_storage)

    ok, message = isolated_storage.save_visit_weather(
        visit_id,
        27.34,
        61,
        internal_temperature_c=22.46,
        description="Parcialmente nublado",
        city="São Paulo",
        latitude=-23.5505,
        longitude=-46.6333,
        source="Open-Meteo",
        captured_at="2026-11-12 09:30:00",
    )

    assert ok, message
    weather = isolated_storage.load_visits()[visit_id]["weather"]
    assert weather["temperature_c"] == 27.3
    assert weather["internal_temperature_c"] == 22.5
    assert weather["humidity_pct"] == 61.0
    assert weather["description"] == "Parcialmente nublado"
    assert weather["city"] == "São Paulo"
    assert weather["latitude"] == -23.5505
    assert weather["longitude"] == -46.6333
    assert weather["source"] == "Open-Meteo"
    assert weather["captured_at"] == "2026-11-12 09:30:00"


def test_save_visit_weather_manual_ignores_invalid_numbers(isolated_storage):
    visit_id = _create_visit(isolated_storage)

    ok, _ = isolated_storage.save_visit_weather(
        visit_id, "abc", "", source="Manual"
    )

    assert ok
    weather = isolated_storage.load_visits()[visit_id]["weather"]
    assert weather["temperature_c"] is None
    assert weather["humidity_pct"] is None
    assert weather["source"] == "Manual"
    assert weather["captured_at"]


def test_save_visit_weather_returns_error_for_unknown_visit(isolated_storage):
    ok, message = isolated_storage.save_visit_weather("nao-existe", 20, 50)

    assert ok is False
    assert "não encontrada" in message.lower()
