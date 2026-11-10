"""Geolocalização automática para captura do clima (Streamlit Components v2).

Diferente do componente legado (que exige um clique), este componente solicita
a localização assim que é montado, mantendo um botão visível para atualizar ou
tentar novamente. O navegador continua responsável por pedir a permissão ao
usuário.
"""

from __future__ import annotations

import streamlit as st

_HTML = """
<div class="acn-auto-geo">
  <button id="geo-button" type="button">📍 Atualizar minha localização</button>
  <div id="geo-status">Solicitando a localização do dispositivo para capturar o clima...</div>
</div>
"""

_CSS = """
.acn-auto-geo {
  font-family: 'Segoe UI', Arial, sans-serif;
  background: #E8F2EA;
  border: 1px solid #CDE4D3;
  border-radius: 12px;
  padding: 12px;
  color: #000000;
}
.acn-auto-geo button {
  background: #16834A;
  color: #FFFFFF;
  border: 1px solid #16834A;
  border-radius: 10px;
  padding: 10px 14px;
  font-weight: 700;
  cursor: pointer;
  width: 100%;
  min-height: 46px;
}
.acn-auto-geo button:hover { background: #216B45; }
#geo-status { font-size: 0.8rem; margin-top: 8px; color: #000000; line-height: 1.35; }
"""

_JS = """
export default function (component) {
  const { data, parentElement, setStateValue, setTriggerValue } = component
  const button = parentElement.querySelector("#geo-button")
  const status = parentElement.querySelector("#geo-status")
  if (!button || !status) return

  if (data?.latitude != null && data?.longitude != null) {
    status.textContent = `Localização capturada: ${Number(data.latitude).toFixed(5)}, ${Number(data.longitude).toFixed(5)}`
  }

  const requestLocation = () => {
    if (!navigator.geolocation) {
      status.textContent = "Geolocalização não disponível. Informe as coordenadas manualmente."
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

  button.onclick = (event) => {
    event.preventDefault()
    requestLocation()
  }

  // A localização é solicitada automaticamente uma vez por montagem do
  // componente. Em recarregamentos do Streamlit, o iframe é preservado.
  if (!parentElement.dataset.autoRequested) {
    parentElement.dataset.autoRequested = "1"
    requestLocation()
  }
}
"""

_NAME = "acnnorte_auto_geolocation"

_COMPONENT = st.components.v2.component(_NAME, html=_HTML, css=_CSS, js=_JS)


def _registered(name: str) -> bool:
    try:
        from streamlit.runtime import Runtime

        runtime = Runtime.instance()
        if runtime is None:
            return False
        return runtime.bidi_component_registry.get(name) is not None
    except Exception:
        return True


def _ensure_component():
    global _COMPONENT
    if not _registered(_NAME):
        _COMPONENT = st.components.v2.component(_NAME, html=_HTML, css=_CSS, js=_JS)
    return _COMPONENT


def auto_geolocation(*, key: str):
    """Solicita o GPS automaticamente e retorna o estado do componente."""
    return _ensure_component()(
        key=key,
        data={},
        on_latitude_change=lambda: None,
        on_longitude_change=lambda: None,
        on_accuracy_change=lambda: None,
        on_error_change=lambda: None,
        on_captured_change=lambda: None,
    )


def geolocation_state(key: str, result=None) -> dict:
    """Normaliza o estado devolvido pelo componente para um dicionário."""
    state = st.session_state.get(key, {})
    if isinstance(state, dict) and state:
        return state

    if result is None:
        return {}

    normalized = {}
    for field in ("latitude", "longitude", "accuracy", "error", "captured"):
        value = getattr(result, field, None)
        if value is not None:
            normalized[field] = value
    return normalized
