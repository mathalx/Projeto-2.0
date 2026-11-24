"""Testes específicos para a extensão modular visit_enhancements (CHANGES 03–09)."""

import src.storage_manager as sm


def _patch_storage(monkeypatch, tmp_path):
    data_dir = tmp_path / "data"
    monkeypatch.setattr(sm, "DATA_DIR", str(data_dir))
    monkeypatch.setattr(sm, "CLIENTS_FILE", str(data_dir / "clients.json"))
    monkeypatch.setattr(sm, "VISITS_FILE", str(data_dir / "visits.json"))
    monkeypatch.setattr(sm, "PHOTOS_DIR", str(data_dir / "photos"))
    monkeypatch.setattr(sm, "get_worker_photos_dir", lambda: str(data_dir / "photos" / "workers"))
    monkeypatch.setattr(sm, "get_signatures_dir", lambda: str(data_dir / "photos" / "signatures"))


def test_equipment_selector_wrappers(tmp_path, monkeypatch):
    """CHANGE 05: catálogos/equipamentos reutilizados e validados."""
    _patch_storage(monkeypatch, tmp_path)
    from src.features.visit_enhancements.equipment.equipment_selector import (
        EQUIPMENT_CATEGORY,
        validate_equipment_for_completion,
    )
    from src.features.visit_enhancements.integration.visit_integration import finalize_visit_guard

    from src.equipment_catalog import DEFAULT_CATEGORY
    assert EQUIPMENT_CATEGORY == DEFAULT_CATEGORY
    sm.init_storage()
    success, cid, _ = sm.add_client("Acme", "11.111.111/0001-11", "Rua A", "Resp", "11", "a@b.c")
    assert success
    success, vid, _ = sm.add_visit(cid, "Tec", "2026-01-01")
    assert success
    visits = sm.load_visits()
    visit = visits[vid]

    assert validate_equipment_for_completion(visit)  # pendente
    ok, problems = finalize_visit_guard(visit)
    assert not ok and any("Equipamento" in p for p in problems)

    ok2, msg2 = sm.save_visit_equipment(vid, ["CHR-3440"])
    assert ok2
    visits = sm.load_visits()
    visit = visits[vid]
    assert len(sm.get_visit_equipment(visit)) == 1
    assert validate_equipment_for_completion(visit) == []


def test_temperature_service_wrappers(tmp_path, monkeypatch):
    """CHANGE 03: integra com storage/weather sem duplicar regras."""
    _patch_storage(monkeypatch, tmp_path)
    from src.features.visit_enhancements.temperature.temperature_service import save_manual_weather

    sm.init_storage()
    success, cid, _ = sm.add_client("Acme2", "22.222.222/0001-22", "Rua B", "Resp", "11", "b@b.c")
    assert success
    success, vid, _ = sm.add_visit(cid, "Tec", "2026-01-02")
    assert success
    ok, msg = save_manual_weather(
        vid,
        temperature_c=25.5,
        humidity_pct=60,
        internal_temperature_c=24.0,
        latitude=-23.5,
        longitude=-46.6,
        source="Manual",
    )
    assert ok
    visits = sm.load_visits()
    w = visits[vid].get("weather", {})
    assert w.get("temperature_c") == 25.5
    assert w.get("internal_temperature_c") == 24.0
    assert w.get("humidity_pct") == 60


def test_signature_service_wrappers(tmp_path, monkeypatch):
    """CHANGE 04: assinaturas e validação."""
    _patch_storage(monkeypatch, tmp_path)
    from src.features.visit_enhancements.signatures.signature_service import validate_signatures_for_completion
    from src.features.visit_enhancements.integration.visit_integration import finalize_visit_guard

    sm.init_storage()
    success, cid, _ = sm.add_client("Acme3", "33.333.333/0001-33", "Rua C", "Resp", "11", "c@b.c")
    assert success
    success, vid, _ = sm.add_visit(cid, "Tec", "2026-01-03")
    assert success
    visits = sm.load_visits()
    visit = visits[vid]
    pending = validate_signatures_for_completion(visit)
    assert len(pending) == 2  # ambas pendentes
    ok, problems = finalize_visit_guard(visit)
    assert not ok


def test_photographs_integration_helpers():
    """CHANGE 07: helpers de padronização de identificação."""
    from src.features.visit_enhancements.photographs.photo_manager import build_photo_identification
    assert build_photo_identification("08:30", "Dosímetro 3440") == "08:30 — Dosímetro 3440"
    assert build_photo_identification("", "Bomba 2386") == "Bomba 2386"


def test_reports_wrappers_exist():
    """CHANGE 08: wrappers de exportação reutilizam export_manager."""
    from src.features.visit_enhancements.reports import report_extensions
    assert callable(getattr(report_extensions, "generate_visit_pdf_bytes", None))
    assert callable(getattr(report_extensions, "generate_visit_excel_bytes", None))


def test_integration_package_exposes_blocks():
    """CHANGE 09/integração: pacote modular disponível."""
    from src.features.visit_enhancements.integration.visit_integration import (
        get_available_enhancement_blocks,
    )
    blocks = get_available_enhancement_blocks()
    assert "temperature" in blocks
    assert "signatures" in blocks
    assert "equipment" in blocks
    assert "photographs" in blocks
    assert "reports" in blocks


def test_visit_form_flow_helpers():
    """CHANGE 06: fluxo modular disponível."""
    from src.features.visit_enhancements.visit_form.visit_form_flow import VISIT_FLOW_STEPS
    assert len(VISIT_FLOW_STEPS) == 4


def test_feature_registry_initializes_all_modules():
    """O registro central usado pelo main carrega todas as extensões."""
    from src.features import FEATURE_MODULES, available_features, initialize_features

    modules = initialize_features()
    assert set(modules) == set(FEATURE_MODULES)
    assert all(module is not None for module in modules.values())
    assert "integration" in available_features()


def test_shared_identification_and_report_wrappers_are_reused_by_views():
    """As telas consomem os helpers modulares em vez de duplicá-los."""
    from src.features.visit_enhancements.reports import (
        generate_visit_pdf_download,
    )
    from src.views import photos_view, reports_view

    assert photos_view.build_photo_identification("08:30", "Dosímetro 3440") == (
        "08:30 — Dosímetro 3440"
    )
    assert reports_view.generate_visit_pdf_download is generate_visit_pdf_download
