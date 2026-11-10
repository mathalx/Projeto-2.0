"""Componentes interativos (Streamlit Custom Components v2).

- ``signature_pad``: captura de assinatura por toque, stylus ou mouse.
- ``geolocation_button``: solicita as coordenadas GPS do dispositivo.
"""

from __future__ import annotations

import streamlit as st

_SIGNATURE_HTML = """
<div class="acn-signature">
  <div class="acn-signature-label" id="sig-label"></div>
  <canvas id="sig-canvas"></canvas>
  <div class="acn-signature-actions">
    <button id="sig-clear" type="button">Limpar</button>
    <span id="sig-hint">Assine com o dedo, stylus ou mouse.</span>
  </div>
</div>
"""

_SIGNATURE_CSS = """
.acn-signature {
  font-family: 'Segoe UI', Arial, sans-serif;
  background: #FFFFFF;
  border: 1px solid #CDD5D0;
  border-radius: 12px;
  padding: 10px;
  color: #000000;
}
.acn-signature-label {
  font-weight: 700;
  font-size: 0.9rem;
  margin-bottom: 6px;
  color: #000000;
}
#sig-canvas {
  width: 100%;
  height: 170px;
  display: block;
  background: #FFFFFF;
  border: 1px dashed #A5CFAF;
  border-radius: 8px;
  touch-action: none;
  cursor: crosshair;
}
.acn-signature-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin-top: 8px;
}
.acn-signature-actions button {
  background: #E8F2EA;
  border: 1px solid #16834A;
  color: #000000;
  border-radius: 8px;
  padding: 6px 12px;
  font-weight: 600;
  cursor: pointer;
}
.acn-signature-actions button:hover { background: #A5CFAF; }
#sig-hint { font-size: 0.78rem; color: #59636A; }
"""

_SIGNATURE_JS = """
export default function (component) {
  const { data, parentElement, setStateValue } = component
  const canvas = parentElement.querySelector("#sig-canvas")
  const label = parentElement.querySelector("#sig-label")
  if (!canvas || !label) return

  label.textContent = data?.label ?? "Assinatura"

  if (!canvas.dataset.ready) {
    canvas.width = 720
    canvas.height = 200
    canvas.dataset.ready = "1"
  }

  const ctx = canvas.getContext("2d")
  ctx.lineWidth = 2.4
  ctx.lineCap = "round"
  ctx.lineJoin = "round"
  ctx.strokeStyle = "#000000"

  const nextValue = data?.value ?? ""
  if (nextValue !== (canvas.dataset.lastValue ?? "")) {
    ctx.clearRect(0, 0, canvas.width, canvas.height)
    if (nextValue && nextValue.startsWith("data:image")) {
      const image = new Image()
      image.onload = () => ctx.drawImage(image, 0, 0, canvas.width, canvas.height)
      image.src = nextValue
    }
    canvas.dataset.lastValue = nextValue
  }

  let drawing = false
  let lastX = 0
  let lastY = 0

  const position = (event) => {
    const rect = canvas.getBoundingClientRect()
    return {
      x: ((event.clientX - rect.left) / rect.width) * canvas.width,
      y: ((event.clientY - rect.top) / rect.height) * canvas.height,
    }
  }

  const finish = () => {
    if (!drawing) return
    drawing = false
    const value = canvas.toDataURL("image/png")
    canvas.dataset.lastValue = value
    setStateValue("value", value)
  }

  canvas.onpointerdown = (event) => {
    event.preventDefault()
    drawing = true
    const point = position(event)
    lastX = point.x
    lastY = point.y
    canvas.setPointerCapture?.(event.pointerId)
  }

  canvas.onpointermove = (event) => {
    if (!drawing) return
    event.preventDefault()
    const point = position(event)
    ctx.beginPath()
    ctx.moveTo(lastX, lastY)
    ctx.lineTo(point.x, point.y)
    ctx.stroke()
    lastX = point.x
    lastY = point.y
  }

  canvas.onpointerup = finish
  canvas.onpointercancel = finish
  canvas.onpointerleave = finish

  const clearButton = parentElement.querySelector("#sig-clear")
  if (clearButton) {
    clearButton.onclick = (event) => {
      event.preventDefault()
      ctx.clearRect(0, 0, canvas.width, canvas.height)
      canvas.dataset.lastValue = ""
      setStateValue("value", "")
    }
  }
}
"""

_GEO_HTML = """
<div class="acn-geo">
  <button id="geo-button" type="button">📍 Usar minha localização</button>
  <div id="geo-status">O GPS do dispositivo será usado apenas para capturar o clima.</div>
</div>
"""

_GEO_CSS = """
.acn-geo {
  font-family: 'Segoe UI', Arial, sans-serif;
  background: #E8F2EA;
  border: 1px solid #CDE4D3;
  border-radius: 12px;
  padding: 12px;
  color: #000000;
}
.acn-geo button {
  background: #16834A;
  color: #FFFFFF;
  border: 1px solid #16834A;
  border-radius: 10px;
  padding: 10px 14px;
  font-weight: 700;
  cursor: pointer;
  width: 100%;
}
.acn-geo button:hover { background: #216B45; }
#geo-status { font-size: 0.8rem; margin-top: 8px; color: #000000; }
"""

_GEO_JS = """
export default function (component) {
  const { data, parentElement, setStateValue, setTriggerValue } = component
  const button = parentElement.querySelector("#geo-button")
  const status = parentElement.querySelector("#geo-status")
  if (!button || !status) return

  if (data?.latitude != null && data?.longitude != null) {
    status.textContent = `Localização capturada: ${data.latitude.toFixed(5)}, ${data.longitude.toFixed(5)}`
  }

  button.onclick = (event) => {
    event.preventDefault()
    if (!navigator.geolocation) {
      status.textContent = "Geolocalização não disponível neste navegador. Informe as coordenadas manualmente."
      setStateValue("error", "Geolocalização indisponível.")
      return
    }
    status.textContent = "Obtendo localização do GPS..."
    navigator.geolocation.getCurrentPosition(
      (position) => {
        const latitude = position.coords.latitude
        const longitude = position.coords.longitude
        const accuracy = position.coords.accuracy
        setStateValue("latitude", latitude)
        setStateValue("longitude", longitude)
        setStateValue("accuracy", accuracy)
        setStateValue("error", "")
        setTriggerValue("captured", true)
        status.textContent = `Localização capturada: ${latitude.toFixed(5)}, ${longitude.toFixed(5)} (precisão ${Math.round(accuracy)} m)`
      },
      (error) => {
        const message = error?.message || "Não foi possível obter a localização."
        setStateValue("error", message)
        setTriggerValue("captured", false)
        status.textContent = "Permissão negada ou GPS indisponível. Informe as coordenadas manualmente."
      },
      { enableHighAccuracy: true, timeout: 10000, maximumAge: 300000 }
    )
  }
}
"""

_SIGNATURE_NAME = "acnnorte_signature_pad"
_GEOLOCATION_NAME = "acnnorte_geolocation"

_SIGNATURE_COMPONENT = st.components.v2.component(
    _SIGNATURE_NAME,
    html=_SIGNATURE_HTML,
    css=_SIGNATURE_CSS,
    js=_SIGNATURE_JS,
)

_GEOLOCATION_COMPONENT = st.components.v2.component(
    _GEOLOCATION_NAME,
    html=_GEO_HTML,
    css=_GEO_CSS,
    js=_GEO_JS,
)


def _registered(name: str) -> bool:
    """Confirma o registro no Runtime ativo (necessário em sessões de teste)."""
    try:
        from streamlit.runtime import Runtime

        runtime = Runtime.instance()
        if runtime is None:
            return False
        return runtime.bidi_component_registry.get(name) is not None
    except Exception:
        return True


def _ensure_signature_component():
    global _SIGNATURE_COMPONENT
    if not _registered(_SIGNATURE_NAME):
        _SIGNATURE_COMPONENT = st.components.v2.component(
            _SIGNATURE_NAME,
            html=_SIGNATURE_HTML,
            css=_SIGNATURE_CSS,
            js=_SIGNATURE_JS,
        )
    return _SIGNATURE_COMPONENT


def _ensure_geolocation_component():
    global _GEOLOCATION_COMPONENT
    if not _registered(_GEOLOCATION_NAME):
        _GEOLOCATION_COMPONENT = st.components.v2.component(
            _GEOLOCATION_NAME,
            html=_GEO_HTML,
            css=_GEO_CSS,
            js=_GEO_JS,
        )
    return _GEOLOCATION_COMPONENT


def signature_pad(
    label: str,
    *,
    key: str,
    initial_value: str = "",
    height: int = 220,
) -> str:
    """Renderiza um quadro de assinatura e retorna o PNG em Base64 (data URL)."""
    component_state = st.session_state.get(key, {})
    if isinstance(component_state, dict) and "value" in component_state:
        current_value = component_state.get("value") or ""
    else:
        current_value = initial_value or ""

    result = _ensure_signature_component()(
        key=key,
        data={"label": label, "value": current_value},
        default={"value": current_value},
        height=height,
        on_value_change=lambda: None,
    )
    value = getattr(result, "value", None)
    if value is None:
        value = current_value
    return value or ""


def geolocation_button(*, key: str):
    """Renderiza o botão de GPS e retorna o estado do componente."""
    return _ensure_geolocation_component()(
        key=key,
        data={},
        on_latitude_change=lambda: None,
        on_longitude_change=lambda: None,
        on_accuracy_change=lambda: None,
        on_error_change=lambda: None,
        on_captured_change=lambda: None,
    )
