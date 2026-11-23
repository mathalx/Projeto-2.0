"""Testes da captura de fotografia (upload + câmera).

Cobrem validação/normalização com Pillow, retorno vazio, fallback de câmera e
persistência das fotos do funcionário e de evidências.
"""

import base64
import io
import os
from types import SimpleNamespace

import pytest
from PIL import Image

import src.components.photo_capture.photo_capture as photo_capture_module
import src.storage_manager as storage
from src.components.photo_capture import (
    PhotoValidationError,
    camera_support_from_headers,
    camera_support_status,
    normalize_photo_bytes,
    photo_bytes_from_data_url,
)

JPEG_MAGIC = b"\xff\xd8\xff"


def _image_bytes(
    size: tuple[int, int] = (80, 60),
    image_format: str = "PNG",
    color: tuple[int, int, int] = (22, 131, 74),
) -> bytes:
    """Gera uma imagem válida em memória para os testes."""
    output = io.BytesIO()
    Image.new("RGB", size, color).save(output, format=image_format)
    return output.getvalue()


def _assert_jpeg(data: bytes) -> Image.Image:
    assert data.startswith(JPEG_MAGIC)
    image = Image.open(io.BytesIO(data))
    assert image.format == "JPEG"
    return image


def _read_file(path: str) -> bytes:
    with open(path, "rb") as file:
        return file.read()


@pytest.fixture()
def isolated_storage(tmp_path, monkeypatch):
    """Redireciona o armazenamento para uma pasta temporária isolada."""
    data_dir = tmp_path / "data"
    photos_dir = data_dir / "photos"

    monkeypatch.setattr(storage, "DATA_DIR", str(data_dir))
    monkeypatch.setattr(storage, "CLIENTS_FILE", str(data_dir / "clients.json"))
    monkeypatch.setattr(storage, "VISITS_FILE", str(data_dir / "visits.json"))
    monkeypatch.setattr(storage, "PHOTOS_DIR", str(photos_dir))
    storage.init_storage()
    return storage


def _create_visit(store) -> str:
    ok, client_id, _ = store.add_client(
        "Empresa Foto",
        "00.000.000/0001-00",
        "Rua A",
        "Resp",
        "11999999999",
        "foto@acn.test",
    )
    assert ok
    ok, visit_id, _ = store.add_visit(
        client_id, "Ana.norte", "2026-11-14", status="Em Andamento"
    )
    assert ok
    return visit_id


# ---------------------------------------------------------------------------
# Validação, compressão e orientação EXIF
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("image_format", ["PNG", "JPEG", "WEBP"])
def test_valid_formats_are_normalized_to_jpeg(image_format):
    normalized = normalize_photo_bytes(_image_bytes(image_format=image_format))

    image = _assert_jpeg(normalized)
    assert image.size == (80, 60)


def test_png_with_transparency_is_flattened_on_white():
    output = io.BytesIO()
    Image.new("RGBA", (40, 30), (22, 131, 74, 0)).save(output, format="PNG")

    normalized = normalize_photo_bytes(output.getvalue())

    image = _assert_jpeg(normalized)
    assert image.mode == "RGB"
    # A área transparente vira fundo branco, não preto.
    assert image.getpixel((0, 0)) == (255, 255, 255)


def test_large_image_is_resized_to_max_dimension():
    normalized = normalize_photo_bytes(
        _image_bytes(size=(3200, 200), image_format="JPEG"),
        max_dimension=1600,
    )

    image = _assert_jpeg(normalized)
    assert max(image.size) == 1600
    assert image.size == (1600, 100)


def test_exif_orientation_is_corrected():
    source = Image.new("RGB", (40, 20), (22, 131, 74))
    exif = Image.Exif()
    exif[274] = 6  # gira 90 graus no sentido horário
    output = io.BytesIO()
    source.save(output, format="JPEG", exif=exif)

    normalized = normalize_photo_bytes(output.getvalue())

    image = _assert_jpeg(normalized)
    assert image.size == (20, 40)


def test_invalid_bytes_are_rejected():
    with pytest.raises(PhotoValidationError, match="não é uma imagem válida"):
        normalize_photo_bytes(b"isto nao e uma imagem")


def test_unsupported_format_is_rejected():
    output = io.BytesIO()
    Image.new("RGB", (10, 10), (0, 0, 0)).save(output, format="GIF")

    with pytest.raises(PhotoValidationError, match="Formato de imagem"):
        normalize_photo_bytes(output.getvalue())


def test_oversized_image_is_rejected_before_processing():
    data = _image_bytes()
    with pytest.raises(PhotoValidationError, match="tamanho máximo"):
        normalize_photo_bytes(data, max_bytes=len(data) - 1)


def test_empty_payload_is_rejected():
    with pytest.raises(PhotoValidationError, match="Nenhuma imagem"):
        normalize_photo_bytes(b"")


# ---------------------------------------------------------------------------
# Data URL e retorno vazio
# ---------------------------------------------------------------------------
def test_no_image_returns_none():
    assert photo_bytes_from_data_url(None) is None
    assert photo_bytes_from_data_url("") is None


def test_data_url_is_normalized_to_jpeg():
    encoded = base64.b64encode(_image_bytes()).decode("ascii")
    normalized = photo_bytes_from_data_url(f"data:image/png;base64,{encoded}")

    assert normalized is not None
    _assert_jpeg(normalized)


def test_invalid_data_url_is_rejected():
    with pytest.raises(PhotoValidationError, match="Formato de imagem inválido"):
        photo_bytes_from_data_url("data:text/plain;base64,b2k=")


def test_photo_input_returns_none_without_selected_image(monkeypatch):
    class FakeComponent:
        def __call__(self, **kwargs):
            return SimpleNamespace(
                image="",
                capture_token="",
                camera_error="",
                camera_available=None,
            )

    monkeypatch.setattr(photo_capture_module, "_COMPONENT", FakeComponent())

    assert photo_capture_module.photo_input(
        "Fotografia", "teste_sem_imagem"
    ) is None


# ---------------------------------------------------------------------------
# Fallback de câmera (lógica Python testável)
# ---------------------------------------------------------------------------
def test_camera_requires_secure_context():
    available, message = camera_support_status(
        secure_context=False, media_devices=True
    )

    assert available is False
    assert "HTTPS" in message


def test_camera_unavailable_when_browser_has_no_media_devices():
    available, message = camera_support_status(
        secure_context=True, media_devices=False
    )

    assert available is False
    assert "não oferece suporte" in message
    assert "Carregar arquivo" in message


def test_camera_is_available_on_https_or_localhost():
    assert camera_support_status(secure_context=True, media_devices=True) == (
        True,
        "",
    )


def test_camera_headers_detect_http_and_localhost():
    assert camera_support_from_headers(
        {"Host": "exemplo.com", "X-Forwarded-Proto": "http"}
    )[0] is False
    assert camera_support_from_headers(
        {"Host": "exemplo.com", "X-Forwarded-Proto": "https"}
    )[0] is True
    assert camera_support_from_headers(
        {"Host": "localhost:8501", "X-Forwarded-Proto": "http"}
    )[0] is True
    assert camera_support_from_headers({})[0] is True


# ---------------------------------------------------------------------------
# Persistência via storage_manager
# ---------------------------------------------------------------------------
def test_save_worker_photo_with_normalized_capture(isolated_storage):
    visit_id = _create_visit(isolated_storage)
    photo = normalize_photo_bytes(_image_bytes(image_format="PNG"))

    ok, path, message = isolated_storage.save_worker_photo(
        visit_id, photo, "funcionario.png", validate_photo=True
    )

    assert ok, message
    assert path.endswith(".jpg")
    assert os.path.exists(path)
    _assert_jpeg(_read_file(path))

    visit = isolated_storage.load_visits()[visit_id]
    assert visit["worker"]["photo_path"] == path
    assert visit["worker"]["photo_filename"].endswith(".jpg")
    assert visit["worker_photo"] == path


def test_save_worker_photo_rejects_invalid_file_when_validating(isolated_storage):
    visit_id = _create_visit(isolated_storage)

    ok, path, message = isolated_storage.save_worker_photo(
        visit_id, b"arquivo invalido", "foto.jpg", validate_photo=True
    )

    assert ok is False
    assert path == ""
    assert "não é uma imagem válida" in message


def test_add_and_replace_evidence_photo_with_normalized_capture(isolated_storage):
    visit_id = _create_visit(isolated_storage)
    photo = normalize_photo_bytes(_image_bytes(image_format="JPEG"))

    ok, message = isolated_storage.add_photo_to_visit(
        visit_id,
        photo,
        "evidencia.png",
        "Legenda da evidência",
        validate_photo=True,
    )

    assert ok, message
    visit = isolated_storage.load_visits()[visit_id]
    saved = visit["photos"][0]
    assert saved["path"].endswith(".jpg")
    assert saved["filename"].endswith(".jpg")
    assert os.path.exists(saved["path"])
    _assert_jpeg(_read_file(saved["path"]))

    replacement = normalize_photo_bytes(_image_bytes(color=(89, 99, 106)))
    ok, message = isolated_storage.replace_photo_in_visit(
        visit_id,
        saved["id"],
        replacement,
        "nova.webp",
        "Legenda substituída",
        validate_photo=True,
    )

    assert ok, message
    replaced = isolated_storage.load_visits()[visit_id]["photos"][0]
    assert replaced["path"].endswith(".jpg")
    assert replaced["description"] == "Legenda substituída"
    assert not os.path.exists(saved["path"])
    _assert_jpeg(_read_file(replaced["path"]))


def test_add_photo_rejects_invalid_file_when_validating(isolated_storage):
    visit_id = _create_visit(isolated_storage)

    ok, message = isolated_storage.add_photo_to_visit(
        visit_id,
        b"nao-e-imagem",
        "evidencia.jpg",
        "Legenda",
        validate_photo=True,
    )

    assert ok is False
    assert "não é uma imagem válida" in message
    assert isolated_storage.load_visits()[visit_id]["photos"] == []


def test_legacy_storage_call_without_validation_keeps_compatibility(isolated_storage):
    """Chamadas antigas com bytes arbitrários continuam aceitas."""
    visit_id = _create_visit(isolated_storage)

    ok, _, message = isolated_storage.save_worker_photo(
        visit_id, b"bytes-legados", "foto.png"
    )

    assert ok, message
    path = isolated_storage.load_visits()[visit_id]["worker"]["photo_path"]
    assert path.endswith(".png")
    assert os.path.exists(path)
