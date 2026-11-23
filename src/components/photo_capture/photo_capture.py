"""Captura de fotografias por upload ou câmera frontal/traseira.

O componente usa a API nativa do navegador (``getUserMedia``) dentro de um
``st.components.v2``. A imagem escolhida é comprimida no cliente, validada e
normalizada no servidor com Pillow e devolvida como bytes JPEG para o
``storage_manager``. Nenhuma imagem é enviada a terceiros.
"""

from __future__ import annotations

import base64
import binascii
import hashlib
import io
import re
from pathlib import Path
from typing import Any, Mapping

import streamlit as st
from PIL import Image, ImageOps, UnidentifiedImageError

MAX_PHOTO_BYTES = 10 * 1024 * 1024  # 10 MB por fotografia
MAX_PHOTO_DIMENSION = 1600
JPEG_QUALITY = 85
ALLOWED_IMAGE_FORMATS = ("JPEG", "PNG", "WEBP")
ALLOWED_UPLOAD_TYPES = ["jpg", "jpeg", "png", "webp"]

_DATA_URL_RE = re.compile(
    r"^data:image/(?:jpeg|jpg|png|webp);base64,",
    re.IGNORECASE,
)
_LOCAL_HOSTS = {"localhost", "127.0.0.1", "::1", "0.0.0.0", "host.docker.internal"}
_HTTPS_MESSAGE = (
    "O acesso à câmera exige HTTPS ou localhost. Em uma rede local via HTTP, "
    "use “Carregar arquivo” ou publique o aplicativo em HTTPS."
)
_COMPONENT_FIELDS = (
    "image",
    "capture_token",
    "camera_error",
    "camera_available",
)


class PhotoValidationError(ValueError):
    """Erro amigável de validação de uma fotografia."""


def _format_size(max_bytes: int) -> str:
    """Formata o limite de bytes em MB/KB para mensagens ao usuário."""
    if max_bytes >= 1024 * 1024:
        return f"{max_bytes / (1024 * 1024):g} MB"
    return f"{max_bytes / 1024:g} KB"


def normalize_photo_bytes(
    data: bytes,
    *,
    max_bytes: int = MAX_PHOTO_BYTES,
    max_dimension: int = MAX_PHOTO_DIMENSION,
    jpeg_quality: int = JPEG_QUALITY,
) -> bytes:
    """Valida, corrige a orientação EXIF e converte a imagem para JPEG.

    Args:
        data: Conteúdo binário recebido do navegador ou de um upload.
        max_bytes: Tamanho máximo aceito antes e depois da normalização.
        max_dimension: Maior lado permitido, em pixels.
        jpeg_quality: Qualidade inicial do JPEG gerado (0 a 100).

    Returns:
        Bytes de uma imagem JPEG normalizada, sem metadados EXIF.

    Raises:
        PhotoValidationError: Quando o arquivo é vazio, grande demais ou não
            é uma imagem JPG/PNG/WEBP válida.
    """
    if not isinstance(data, (bytes, bytearray)) or not data:
        raise PhotoValidationError("Nenhuma imagem foi fornecida.")

    raw = bytes(data)
    if len(raw) > max_bytes:
        raise PhotoValidationError(
            f"A imagem excede o tamanho máximo de {_format_size(max_bytes)}."
        )

    try:
        with Image.open(io.BytesIO(raw)) as source:
            image_format = str(source.format or "").upper()
            if image_format not in ALLOWED_IMAGE_FORMATS:
                raise PhotoValidationError(
                    "Formato de imagem não suportado. Envie JPG, PNG ou WEBP."
                )
            source.load()
            image = ImageOps.exif_transpose(source)

            if image.mode in ("RGBA", "LA") or (
                image.mode == "P" and "transparency" in image.info
            ):
                rgba = image.convert("RGBA")
                background = Image.new("RGB", rgba.size, (255, 255, 255))
                background.paste(rgba, mask=rgba.getchannel("A"))
                image = background
            elif image.mode != "RGB":
                image = image.convert("RGB")
            else:
                image = image.copy()

            if max(image.size) > max_dimension:
                image.thumbnail(
                    (max_dimension, max_dimension), Image.Resampling.LANCZOS
                )

            result = _encode_jpeg(image, jpeg_quality)
            if len(result) > max_bytes:
                for quality in (75, 65, 55, 45):
                    result = _encode_jpeg(image, quality)
                    if len(result) <= max_bytes:
                        break
                else:
                    raise PhotoValidationError(
                        "A imagem continua acima do tamanho máximo de "
                        f"{_format_size(max_bytes)} após a compressão."
                    )
            return result
    except PhotoValidationError:
        raise
    except (
        UnidentifiedImageError,
        Image.DecompressionBombError,
        OSError,
        ValueError,
    ) as exc:
        raise PhotoValidationError(
            "O arquivo enviado não é uma imagem válida. Use JPG, PNG ou WEBP."
        ) from exc


def _encode_jpeg(image: Image.Image, quality: int) -> bytes:
    """Codifica uma imagem RGB como JPEG e devolve os bytes."""
    output = io.BytesIO()
    image.save(output, format="JPEG", quality=quality, optimize=True)
    return output.getvalue()


def photo_bytes_from_data_url(
    data_url: str | None,
    *,
    max_bytes: int = MAX_PHOTO_BYTES,
) -> bytes | None:
    """Converte um data URL de imagem em bytes JPEG normalizados.

    Retorna ``None`` quando nenhum data URL é informado (nenhuma foto
    selecionada). Data URLs em formatos não permitidos são rejeitados.
    """
    if not data_url:
        return None
    if not isinstance(data_url, str) or not _DATA_URL_RE.match(data_url):
        raise PhotoValidationError(
            "Formato de imagem inválido. Envie uma foto JPG, PNG ou WEBP."
        )

    encoded = data_url.split(",", 1)[1] if "," in data_url else ""
    if not encoded:
        raise PhotoValidationError("A imagem recebida está vazia.")
    if len(encoded) > ((max_bytes * 4) // 3) + 8:
        raise PhotoValidationError(
            f"A imagem excede o tamanho máximo de {_format_size(max_bytes)}."
        )

    try:
        raw = base64.b64decode(encoded, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise PhotoValidationError(
            "Não foi possível ler a imagem recebida. Tente novamente."
        ) from exc

    return normalize_photo_bytes(raw, max_bytes=max_bytes)


def camera_support_status(
    *,
    secure_context: bool,
    media_devices: bool,
) -> tuple[bool, str]:
    """Avalia, de forma testável, se a câmera pode ser usada no navegador.

    Args:
        secure_context: ``True`` quando a página está em HTTPS ou localhost.
        media_devices: ``True`` quando ``navigator.mediaDevices.getUserMedia``
            está disponível no navegador.

    Returns:
        ``(disponível, mensagem)``. Quando indisponível, a mensagem explica o
        motivo e a alternativa de upload.
    """
    if not secure_context:
        return False, _HTTPS_MESSAGE
    if not media_devices:
        return (
            False,
            "Este navegador não oferece suporte à captura pela câmera. "
            "Use “Carregar arquivo” para enviar uma imagem da galeria.",
        )
    return True, ""


def _host_is_local(host: str) -> bool:
    """Informa se o host HTTP é local (localhost/loopback)."""
    value = str(host or "").strip().lower()
    if not value:
        return False
    if value.startswith("["):
        value = value.split("]", 1)[0].lstrip("[")
    elif value.count(":") == 1:
        value = value.rsplit(":", 1)[0]
    return value in _LOCAL_HOSTS or value.endswith(".localhost")


def camera_support_from_headers(
    headers: Mapping[str, str] | None,
) -> tuple[bool, str]:
    """Deduz o contexto seguro a partir dos headers HTTP da requisição.

    A checagem definitiva continua sendo feita no navegador. Aqui só evitamos
    prometer câmera quando o próprio servidor informa que a página está em
    HTTP e não é localhost.
    """
    if not headers:
        return True, ""

    normalized = {str(key).lower(): str(value) for key, value in headers.items()}
    host = normalized.get("host") or normalized.get("x-forwarded-host") or ""
    proto = (
        normalized.get("x-forwarded-proto")
        or normalized.get("x-scheme")
        or ""
    ).split(",", 1)[0].strip().lower()

    if host and _host_is_local(host):
        return True, ""
    if proto == "https":
        return True, ""
    if proto == "http":
        return camera_support_status(secure_context=False, media_devices=True)
    return True, ""


def _request_headers() -> Mapping[str, str]:
    """Lê os headers da requisição atual, com fallback vazio em testes."""
    try:
        return dict(st.context.headers)
    except Exception:
        return {}


def _component_state(key: str, result: Any) -> dict:
    """Normaliza o estado do componente para um dicionário simples."""
    state = st.session_state.get(key, {})
    if not isinstance(state, dict):
        state = {}
    for field in _COMPONENT_FIELDS:
        if field in state:
            continue
        value = getattr(result, field, None)
        if value is not None:
            state[field] = value
    return state


def _normalize_or_error(data: bytes, *, label: str) -> bytes | None:
    """Normaliza bytes de um widget alternativo e mostra erros amigáveis."""
    try:
        return normalize_photo_bytes(data)
    except PhotoValidationError as exc:
        st.error(str(exc))
        return None


def _render_fallback(
    label: str,
    key: str,
    *,
    allow_upload: bool,
) -> bytes | None:
    """Exibe câmera nativa e uploader quando a câmera web não está disponível."""
    nonce = int(st.session_state.get(f"{key}__nonce", 0))
    st.caption("Alternativas para este dispositivo:")

    native = st.camera_input(
        "Câmera nativa do dispositivo",
        key=f"{key}__native_camera_{nonce}",
        help="Abre a câmera do aparelho sem usar a pré-visualização da página.",
    )
    if native is not None:
        return _normalize_or_error(native.getvalue(), label=label)

    if allow_upload:
        uploaded = st.file_uploader(
            f"{label} — enviar imagem da galeria/arquivo",
            type=ALLOWED_UPLOAD_TYPES,
            key=f"{key}__fallback_upload_{nonce}",
            help="Formatos aceitos: JPG, PNG e WEBP (até 10 MB).",
        )
        if uploaded is not None:
            return _normalize_or_error(uploaded.getvalue(), label=label)

    return None


def photo_input(
    label: str,
    key: str,
    allow_upload: bool = True,
    allow_camera: bool = True,
    default_camera: str = "environment",
) -> bytes | None:
    """Campo de fotografia com upload e câmera frontal/traseira.

    Args:
        label: Rótulo exibido acima do componente.
        key: Chave única do campo. Use uma chave por visita/foto para que
            vários campos na mesma tela não compartilhem estado.
        allow_upload: Permite escolher uma imagem existente.
        allow_camera: Permite capturar pela câmera do dispositivo.
        default_camera: Câmera preferida ao abrir: ``"environment"``
            (traseira) ou ``"user"`` (frontal).

    Returns:
        Bytes JPEG normalizados da foto selecionada ou ``None`` enquanto
        nenhuma foto foi confirmada.
    """
    if not str(key or "").strip():
        raise ValueError("O parâmetro 'key' é obrigatório para photo_input.")
    if not allow_upload and not allow_camera:
        raise ValueError(
            "photo_input precisa permitir upload ou câmera (ou ambos)."
        )
    if default_camera not in ("user", "environment"):
        default_camera = "environment"

    reset_token = int(st.session_state.get(f"{key}__reset", 0))
    result = _COMPONENT(
        key=key,
        data={
            "label": label,
            "default_camera": default_camera,
            "allow_upload": bool(allow_upload),
            "allow_camera": bool(allow_camera),
            "reset_token": reset_token,
        },
        on_image_change=lambda *_: None,
        on_capture_token_change=lambda *_: None,
        on_camera_error_change=lambda *_: None,
        on_camera_available_change=lambda *_: None,
    )

    state = _component_state(key, result)
    raw_image = str(state.get("image") or "")
    raw_token = str(state.get("capture_token") or "")
    image_hash = (
        hashlib.sha256(raw_image.encode("utf-8")).hexdigest() if raw_image else ""
    )
    ignored_hash = st.session_state.get(f"{key}__ignored_hash")
    ignored_token = st.session_state.get(f"{key}__ignored_token")
    ignored = bool(raw_image) and (
        (raw_token and ignored_token and raw_token == ignored_token)
        or (not raw_token and image_hash and image_hash == ignored_hash)
    )

    if raw_image and not ignored:
        if st.session_state.get(f"{key}__hash") == image_hash:
            cached = st.session_state.get(f"{key}__bytes")
            if isinstance(cached, (bytes, bytearray)) and cached:
                return bytes(cached)
        try:
            photo_bytes = photo_bytes_from_data_url(raw_image)
        except PhotoValidationError as exc:
            st.error(str(exc))
            st.session_state[f"{key}__ignored_hash"] = image_hash
        else:
            if photo_bytes is not None:
                st.session_state[f"{key}__hash"] = image_hash
                st.session_state[f"{key}__bytes"] = photo_bytes
                st.session_state.pop(f"{key}__ignored_hash", None)
                st.session_state.pop(f"{key}__ignored_token", None)
                return photo_bytes

    # Nenhuma foto confirmada: limpa apenas o cache Python (não mexe no widget).
    st.session_state.pop(f"{key}__hash", None)
    st.session_state.pop(f"{key}__bytes", None)
    if not raw_image:
        st.session_state.pop(f"{key}__ignored_hash", None)
        st.session_state.pop(f"{key}__ignored_token", None)

    if allow_camera:
        available, support_message = camera_support_from_headers(_request_headers())
        camera_error = str(state.get("camera_error") or "").strip()
        reason = support_message if not available else camera_error
        if reason:
            st.warning(reason)
            fallback_bytes = _render_fallback(
                label, key, allow_upload=allow_upload
            )
            if fallback_bytes is not None:
                return fallback_bytes

    return None


def clear_photo_input(key: str) -> None:
    """Descarta a foto confirmada e reinicia o componente para o próximo uso."""
    if not str(key or "").strip():
        return

    state = st.session_state.get(key, {})
    if isinstance(state, dict):
        image = str(state.get("image") or "")
        token = str(state.get("capture_token") or "")
        if image:
            st.session_state[f"{key}__ignored_hash"] = hashlib.sha256(
                image.encode("utf-8")
            ).hexdigest()
        if token:
            st.session_state[f"{key}__ignored_token"] = token

    st.session_state[f"{key}__reset"] = (
        int(st.session_state.get(f"{key}__reset", 0)) + 1
    )
    st.session_state[f"{key}__nonce"] = (
        int(st.session_state.get(f"{key}__nonce", 0)) + 1
    )
    st.session_state.pop(f"{key}__hash", None)
    st.session_state.pop(f"{key}__bytes", None)


_HTML = Path(__file__).with_name("camera_component.html").read_text(encoding="utf-8")

_CSS = """
.acn-photo {
  font-family: 'Segoe UI', Arial, sans-serif;
  background: #FFFFFF;
  border: 1px solid #CDE4D3;
  border-radius: 14px;
  padding: 12px;
  color: #000000;
  width: 100%;
  box-sizing: border-box;
}

.acn-photo-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 10px;
  flex-wrap: wrap;
}

.acn-photo-label {
  font-size: 0.92rem;
  font-weight: 700;
  color: #16834A;
}

.acn-photo-status {
  font-size: 0.76rem;
  color: #59636A;
}

.acn-tabs {
  display: flex;
  gap: 8px;
  margin-bottom: 10px;
}

.acn-tab {
  flex: 1 1 0;
  min-height: 46px;
  border: 1px solid #CDE4D3;
  border-radius: 10px;
  background: #F4F6F4;
  color: #59636A;
  font-size: 0.9rem;
  font-weight: 700;
  cursor: pointer;
  padding: 8px 10px;
}

.acn-tab-active {
  background: #16834A;
  border-color: #16834A;
  color: #FFFFFF;
}

.acn-pane { display: block; }

.acn-drop {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 4px;
  min-height: 120px;
  border: 2px dashed #A5CFAF;
  border-radius: 12px;
  background: #E8F2EA;
  color: #216B45;
  cursor: pointer;
  text-align: center;
  padding: 14px;
  box-sizing: border-box;
}

.acn-drop:hover { background: #DCEEDF; }
.acn-drop-title { font-weight: 700; font-size: 0.95rem; }
.acn-drop-hint { font-size: 0.78rem; color: #59636A; }

.acn-camera-toolbar {
  display: flex;
  gap: 8px;
  margin-bottom: 8px;
  flex-wrap: wrap;
}

.acn-camera-toolbar select {
  flex: 1 1 160px;
  min-height: 44px;
  border: 1px solid #CDE4D3;
  border-radius: 10px;
  padding: 8px;
  color: #000000;
  background: #FFFFFF;
}

.acn-stage {
  position: relative;
  width: 100%;
  min-height: 180px;
  background: #111827;
  border-radius: 12px;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
}

#pc-video, #pc-snapshot {
  display: block;
  width: 100%;
  max-height: 360px;
  object-fit: contain;
  background: #111827;
}

#pc-video[hidden], #pc-snapshot[hidden] { display: none !important; }

.acn-hint {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 16px;
  text-align: center;
  color: #FFFFFF;
  font-size: 0.84rem;
  line-height: 1.4;
  pointer-events: none;
}

.acn-hint[hidden] { display: none !important; }

.acn-camera-actions, .acn-preview-actions {
  display: flex;
  gap: 8px;
  margin-top: 10px;
  flex-wrap: wrap;
}

.acn-btn {
  flex: 1 1 130px;
  min-height: 48px;
  border-radius: 10px;
  font-size: 0.9rem;
  font-weight: 700;
  cursor: pointer;
  padding: 10px 12px;
  border: 1px solid transparent;
}

.acn-btn-primary {
  background: #16834A;
  border-color: #16834A;
  color: #FFFFFF;
}

.acn-btn-primary:hover { background: #216B45; }

.acn-btn-secondary {
  background: #FFFFFF;
  border-color: #CDE4D3;
  color: #216B45;
}

.acn-btn-secondary:hover { background: #E8F2EA; }
.acn-btn[hidden] { display: none !important; }

.acn-message {
  margin-top: 10px;
  font-size: 0.82rem;
  line-height: 1.4;
  color: #59636A;
}

.acn-message:empty { display: none; }
.acn-message-error { color: #B42318; font-weight: 600; }
.acn-message-success { color: #16834A; font-weight: 600; }
.acn-message-warning { color: #8A5A00; font-weight: 600; }

.acn-preview {
  margin-top: 12px;
  border-top: 1px solid #CDE4D3;
  padding-top: 12px;
}

.acn-preview[hidden] { display: none !important; }

#pc-preview {
  display: block;
  width: 100%;
  max-height: 320px;
  object-fit: contain;
  border-radius: 10px;
  background: #F4F6F4;
}

@media (max-width: 420px) {
  .acn-photo { padding: 10px; border-radius: 12px; }
  .acn-tabs { flex-direction: column; }
  .acn-btn { flex: 1 1 100%; }
}
"""

_JS = r"""
export default function (component) {
  const { data, parentElement, setStateValue } = component
  const root = parentElement.querySelector("#acn-photo")
  if (!root) return

  const el = (selector) => parentElement.querySelector(selector)
  const elements = {
    label: el("#pc-label"),
    status: el("#pc-status"),
    tabUpload: el("#pc-tab-upload"),
    tabCamera: el("#pc-tab-camera"),
    paneUpload: el("#pc-pane-upload"),
    paneCamera: el("#pc-pane-camera"),
    file: el("#pc-file"),
    drop: el("#pc-drop"),
    switch: el("#pc-switch"),
    device: el("#pc-device"),
    video: el("#pc-video"),
    snapshot: el("#pc-snapshot"),
    hint: el("#pc-hint"),
    start: el("#pc-start"),
    capture: el("#pc-capture"),
    retake: el("#pc-retake"),
    useCamera: el("#pc-use-camera"),
    message: el("#pc-message"),
    previewWrap: el("#pc-preview-wrap"),
    preview: el("#pc-preview"),
    use: el("#pc-use"),
    discard: el("#pc-discard"),
  }

  for (const value of Object.values(elements)) {
    if (!value) return
  }

  const MAX_DIMENSION = 1600
  const JPEG_QUALITY = 0.85
  const MAX_BYTES = 10 * 1024 * 1024

  const store = (globalThis.__acnPhotoCaptureStates ||= new WeakMap())
  let state = store.get(parentElement)
  if (!state) {
    state = {
      stream: null,
      facing: data?.default_camera === "user" ? "user" : "environment",
      deviceId: "",
      preview: "",
      captured: "",
      resetToken: Number(data?.reset_token || 0),
      tab: "upload",
      sentImage: "",
      hadError: false,
      busy: false,
    }
    store.set(parentElement, state)
  }

  const allowUpload = data?.allow_upload !== false
  const allowCamera = data?.allow_camera !== false
  const secureContext = window.isSecureContext !== false

  function setStatus(text) {
    elements.status.textContent = text || "Nenhuma foto selecionada"
  }

  function setMessage(text, kind = "info") {
    elements.message.textContent = text || ""
    elements.message.className = "acn-message"
    if (kind === "error") elements.message.classList.add("acn-message-error")
    if (kind === "success") elements.message.classList.add("acn-message-success")
    if (kind === "warning") elements.message.classList.add("acn-message-warning")
  }

  function updateSwitchLabel() {
    elements.switch.textContent =
      state.facing === "environment"
        ? "🔄 Usar câmera frontal"
        : "🔄 Usar câmera traseira"
  }

  function setCameraControls(mode) {
    elements.start.hidden = mode !== "idle"
    elements.capture.hidden = mode !== "live"
    elements.retake.hidden = mode !== "captured"
    elements.useCamera.hidden = mode !== "captured"
  }

  function stopStream() {
    if (state.stream) {
      for (const track of state.stream.getTracks()) {
        try { track.stop() } catch (error) { /* já encerrada */ }
      }
      state.stream = null
    }
    elements.video.srcObject = null
  }

  function hideUploadPreview() {
    elements.previewWrap.hidden = true
    elements.preview.removeAttribute("src")
  }

  function cameraSupport() {
    if (!secureContext) {
      return {
        ok: false,
        message:
          "O acesso à câmera exige HTTPS ou localhost. " +
          "Use “Carregar arquivo” ou publique o aplicativo em HTTPS.",
      }
    }
    if (
      !navigator.mediaDevices ||
      typeof navigator.mediaDevices.getUserMedia !== "function"
    ) {
      return {
        ok: false,
        message:
          "Este navegador não oferece suporte à captura pela câmera. " +
          "Use “Carregar arquivo” para enviar uma imagem da galeria.",
      }
    }
    return { ok: true, message: "" }
  }

  function friendlyError(error) {
    const name = error?.name || ""
    if (name === "NotAllowedError" || name === "PermissionDeniedError") {
      return (
        "Permissão de câmera negada. Autorize o acesso nas configurações do " +
        "navegador ou use “Carregar arquivo”."
      )
    }
    if (name === "NotFoundError" || name === "DevicesNotFoundError") {
      return (
        "Nenhuma câmera encontrada neste dispositivo. " +
        "Use “Carregar arquivo” para enviar uma imagem."
      )
    }
    if (name === "NotReadableError" || name === "TrackStartError") {
      return (
        "A câmera está em uso por outro aplicativo. Feche-o e tente novamente " +
        "ou use “Carregar arquivo”."
      )
    }
    if (name === "OverconstrainedError") {
      return (
        "A câmera selecionada não está disponível. Tente outra câmera ou use " +
        "“Carregar arquivo”."
      )
    }
    if (name === "SecurityError") {
      return (
        "O navegador bloqueou o acesso à câmera. Use HTTPS/localhost e permita " +
        "o acesso nas configurações do site."
      )
    }
    return (
      "Não foi possível abrir a câmera. Verifique a permissão do navegador ou " +
      "use “Carregar arquivo”."
    )
  }

  function showCameraError(message) {
    state.hadError = true
    setStatus("Câmera indisponível")
    setMessage(message, "error")
    elements.hint.textContent = message
    elements.hint.hidden = false
    elements.video.hidden = true
    elements.snapshot.hidden = true
    setCameraControls("idle")
    setStateValue("camera_error", message)
    setStateValue("camera_available", false)
  }

  async function refreshDevices() {
    if (!navigator.mediaDevices?.enumerateDevices) return
    try {
      const devices = (await navigator.mediaDevices.enumerateDevices()).filter(
        (device) => device.kind === "videoinput"
      )
      elements.device.innerHTML = ""
      for (let index = 0; index < devices.length; index += 1) {
        const device = devices[index]
        const option = document.createElement("option")
        option.value = device.deviceId
        option.textContent = device.label || `Câmera ${index + 1}`
        elements.device.appendChild(option)
      }
      if (state.deviceId) elements.device.value = state.deviceId
      elements.device.hidden = devices.length <= 1
    } catch (error) {
      elements.device.hidden = true
    }
  }

  function shouldRetry(error) {
    const name = error?.name || ""
    return (
      name === "OverconstrainedError" ||
      name === "NotFoundError" ||
      name === "DevicesNotFoundError"
    )
  }

  async function openCamera(deviceId = "") {
    if (state.busy) return
    const support = cameraSupport()
    if (!support.ok) {
      showCameraError(support.message)
      return
    }

    state.busy = true
    state.hadError = false
    state.captured = ""
    hideUploadPreview()
    stopStream()
    setMessage("Solicitando permissão de câmera...", "info")
    elements.hint.textContent = "Solicitando permissão de câmera..."
    elements.hint.hidden = false
    elements.video.hidden = true
    elements.snapshot.hidden = true
    setCameraControls("idle")

    const attempts = []
    if (deviceId) {
      attempts.push({ video: { deviceId: { exact: deviceId } }, audio: false })
    } else {
      attempts.push({
        video: {
          facingMode: { ideal: state.facing },
          width: { ideal: 1920 },
          height: { ideal: 1080 },
        },
        audio: false,
      })
      attempts.push({
        video: { facingMode: { ideal: state.facing } },
        audio: false,
      })
      attempts.push({ video: true, audio: false })
    }

    let lastError = null
    for (const constraints of attempts) {
      try {
        const stream = await navigator.mediaDevices.getUserMedia(constraints)
        state.stream = stream
        const track = stream.getVideoTracks()[0]
        state.deviceId = deviceId || track?.getSettings?.().deviceId || ""
        elements.video.srcObject = stream
        elements.video.hidden = false
        elements.snapshot.hidden = true
        elements.hint.hidden = true
        try { await elements.video.play() } catch (error) { /* autoplay pode ser bloqueado */ }
        setStatus("Câmera pronta. Enquadre e toque em Capturar.")
        setMessage("", "info")
        setCameraControls("live")
        updateSwitchLabel()
        await refreshDevices()
        if (track) {
          track.addEventListener("ended", () => {
            stopStream()
            setCameraControls("idle")
            setMessage(
              "A câmera foi desconectada. Toque em “Abrir câmera” para tentar novamente.",
              "warning"
            )
          })
        }
        state.busy = false
        return
      } catch (error) {
        lastError = error
        if (!shouldRetry(error)) break
      }
    }

    state.busy = false
    showCameraError(friendlyError(lastError))
  }

  function drawCompressed(source, width, height) {
    const scale = Math.min(1, MAX_DIMENSION / Math.max(width, height))
    const canvas = document.createElement("canvas")
    canvas.width = Math.max(1, Math.round(width * scale))
    canvas.height = Math.max(1, Math.round(height * scale))
    const context = canvas.getContext("2d")
    if (!context) throw new Error("Canvas indisponível")
    context.fillStyle = "#FFFFFF"
    context.fillRect(0, 0, canvas.width, canvas.height)
    context.drawImage(source, 0, 0, canvas.width, canvas.height)
    return canvas.toDataURL("image/jpeg", JPEG_QUALITY)
  }

  function loadImageFromFile(file) {
    return new Promise((resolve, reject) => {
      const url = URL.createObjectURL(file)
      const image = new Image()
      image.onload = () => {
        URL.revokeObjectURL(url)
        resolve(image)
      }
      image.onerror = () => {
        URL.revokeObjectURL(url)
        reject(new Error("Imagem inválida"))
      }
      image.src = url
    })
  }

  function capturePhoto() {
    const width = elements.video.videoWidth || 0
    const height = elements.video.videoHeight || 0
    if (!width || !height) {
      setMessage("A câmera ainda está carregando. Aguarde e tente novamente.", "warning")
      return
    }
    try {
      const image = drawCompressed(elements.video, width, height)
      state.captured = image
      state.preview = ""
      stopStream()
      hideUploadPreview()
      elements.snapshot.src = image
      elements.snapshot.hidden = false
      elements.video.hidden = true
      elements.hint.hidden = true
      setCameraControls("captured")
      setStatus("Foto capturada. Confira e toque em Usar esta foto.")
      setMessage("", "info")
    } catch (error) {
      setMessage("Não foi possível capturar a foto. Tente novamente.", "error")
    }
  }

  function retakePhoto() {
    state.captured = ""
    elements.snapshot.hidden = true
    elements.snapshot.removeAttribute("src")
    elements.video.hidden = false
    openCamera(state.deviceId || "")
  }

  function sourceForUse() {
    return state.captured || state.preview || ""
  }

  function usePhoto() {
    const source = sourceForUse()
    if (!source) {
      setMessage("Capture ou selecione uma foto antes de confirmar.", "warning")
      return
    }
    state.sentImage = source
    setStateValue("image", source)
    setStateValue(
      "capture_token",
      `${Date.now()}-${Math.random().toString(36).slice(2)}`
    )
    setStateValue("camera_error", "")
    setStateValue("camera_available", true)
    setStatus("Foto pronta para salvar.")
    setMessage(
      "Fotografia selecionada. Confirme no formulário para salvar no registro.",
      "success"
    )
  }

  function discardSelection() {
    state.preview = ""
    state.captured = ""
    state.deviceId = ""
    stopStream()
    elements.preview.removeAttribute("src")
    elements.previewWrap.hidden = true
    elements.snapshot.removeAttribute("src")
    elements.snapshot.hidden = true
    elements.video.hidden = false
    elements.hint.hidden = false
    elements.hint.textContent = "Toque em “Abrir câmera” para iniciar a pré-visualização."
    elements.device.hidden = true
    elements.device.innerHTML = ""
    setCameraControls("idle")
    setStatus("Nenhuma foto selecionada")
    setMessage("", "info")
    if (state.sentImage) {
      state.sentImage = ""
      setStateValue("image", "")
      setStateValue("capture_token", "")
    }
  }

  async function handleFile(file) {
    if (!file) return
    if (!/^image\/(jpeg|jpg|png|webp)$/i.test(file.type || "")) {
      setMessage("Formato não suportado. Envie uma imagem JPG, PNG ou WEBP.", "error")
      return
    }
    if (file.size > MAX_BYTES) {
      setMessage("A imagem excede o tamanho máximo de 10 MB.", "error")
      return
    }
    setMessage("Preparando imagem...", "info")
    try {
      const image = await loadImageFromFile(file)
      const dataUrl = drawCompressed(image, image.naturalWidth, image.naturalHeight)
      state.preview = dataUrl
      state.captured = ""
      elements.preview.src = dataUrl
      elements.previewWrap.hidden = false
      elements.snapshot.hidden = true
      setCameraControls("idle")
      setStatus("Imagem carregada. Confira e toque em Usar esta foto.")
      setMessage("", "info")
    } catch (error) {
      setMessage(
        "Não foi possível ler esta imagem. Tente outro arquivo JPG, PNG ou WEBP.",
        "error"
      )
    }
  }

  function showTab(name) {
    const cameraActive = name === "camera" && allowCamera
    state.tab = cameraActive ? "camera" : "upload"

    elements.tabUpload.classList.toggle("acn-tab-active", !cameraActive)
    elements.tabCamera.classList.toggle("acn-tab-active", cameraActive)
    elements.tabUpload.setAttribute("aria-selected", String(!cameraActive))
    elements.tabCamera.setAttribute("aria-selected", String(cameraActive))
    elements.paneUpload.hidden = cameraActive
    elements.paneCamera.hidden = !cameraActive

    if (!cameraActive) {
      stopStream()
      if (state.preview) {
        elements.preview.src = state.preview
        elements.previewWrap.hidden = false
      }
    } else {
      hideUploadPreview()
    }
  }

  function openCameraTab() {
    showTab("camera")
    if (!state.stream && !state.captured) {
      openCamera(state.deviceId || "")
    }
  }

  function restoreUi() {
    elements.label.textContent = data?.label || "Fotografia"
    elements.tabUpload.hidden = !allowUpload
    elements.tabCamera.hidden = !allowCamera
    updateSwitchLabel()

    if (!allowUpload && allowCamera) {
      showTab("camera")
    } else {
      showTab(state.tab === "camera" && allowCamera ? "camera" : "upload")
    }

    if (state.captured) {
      elements.snapshot.src = state.captured
      elements.snapshot.hidden = false
      elements.video.hidden = true
      elements.hint.hidden = true
      setCameraControls("captured")
      setStatus("Foto capturada. Confira e toque em Usar esta foto.")
    } else if (state.preview) {
      elements.preview.src = state.preview
      elements.previewWrap.hidden = false
      setStatus("Imagem carregada. Confira e toque em Usar esta foto.")
    } else {
      setCameraControls("idle")
    }
  }

  // Reinício solicitado pelo Python depois de salvar a foto.
  const incomingReset = Number(data?.reset_token || 0)
  if (incomingReset !== state.resetToken) {
    state.resetToken = incomingReset
    discardSelection()
    state.tab = "upload"
  }

  elements.tabUpload.onclick = (event) => {
    event.preventDefault()
    showTab("upload")
  }

  elements.tabCamera.onclick = (event) => {
    event.preventDefault()
    openCameraTab()
  }

  elements.file.onchange = async (event) => {
    const file = event.target?.files?.[0]
    await handleFile(file)
    try { elements.file.value = "" } catch (error) { /* alguns navegadores bloqueiam */ }
  }

  elements.start.onclick = (event) => {
    event.preventDefault()
    openCamera(state.deviceId || "")
  }

  elements.capture.onclick = (event) => {
    event.preventDefault()
    capturePhoto()
  }

  elements.retake.onclick = (event) => {
    event.preventDefault()
    retakePhoto()
  }

  elements.useCamera.onclick = (event) => {
    event.preventDefault()
    usePhoto()
  }

  elements.use.onclick = (event) => {
    event.preventDefault()
    usePhoto()
  }

  elements.discard.onclick = (event) => {
    event.preventDefault()
    discardSelection()
  }

  elements.switch.onclick = async (event) => {
    event.preventDefault()
    const options = Array.from(elements.device.options || [])
    if (!elements.device.hidden && options.length > 1) {
      const current = Math.max(
        0,
        options.findIndex((option) => option.value === state.deviceId)
      )
      const next = options[(current + 1) % options.length]
      elements.device.value = next.value
      await openCamera(next.value)
      return
    }
    state.facing = state.facing === "environment" ? "user" : "environment"
    state.deviceId = ""
    updateSwitchLabel()
    await openCamera()
  }

  elements.device.onchange = (event) => {
    const value = event.target?.value || ""
    if (value) openCamera(value)
  }

  restoreUi()

  return () => {
    stopStream()
    elements.tabUpload.onclick = null
    elements.tabCamera.onclick = null
    elements.file.onchange = null
    elements.start.onclick = null
    elements.capture.onclick = null
    elements.retake.onclick = null
    elements.useCamera.onclick = null
    elements.use.onclick = null
    elements.discard.onclick = null
    elements.switch.onclick = null
    elements.device.onchange = null
  }
}
"""

_COMPONENT = st.components.v2.component(
    "acnnorte_photo_capture",
    html=_HTML,
    css=_CSS,
    js=_JS,
)
