"""Componente de geolocalização do dispositivo (Streamlit Components v2).

O navegador é responsável por solicitar a autorização ao usuário. O componente
pede a localização uma única vez por sessão do navegador e mantém um botão para
atualizar ou tentar novamente. Se o GPS não estiver disponível, a temperatura
pode ser informada manualmente no formulário da visita.

Observação importante sobre o CCv2: com ``isolate_styles=True`` (padrão), o
``parentElement`` recebido pelo JavaScript é um ``ShadowRoot``, e não um
elemento HTML. ``ShadowRoot`` não possui a propriedade ``dataset``; usar
``parentElement.dataset`` derrubava o componente com
``Cannot read properties of undefined (reading 'autoRequested')``.
"""

from __future__ import annotations

import math
from collections.abc import Mapping
from typing import Any

import streamlit as st

_HTML = """
<div class="acn-geo">
  <button id="geo-button" type="button">📍 Atualizar localização do dispositivo</button>
  <div id="geo-status" role="status" aria-live="polite">Solicitando autorização de localização...</div>
</div>
"""

_CSS = """
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
  font-size: 0.92rem;
  cursor: pointer;
  width: 100%;
  min-height: 46px;
}
.acn-geo button:hover { background: #216B45; }
#geo-status {
  font-size: 0.8rem;
  margin-top: 8px;
  color: #000000;
  line-height: 1.35;
}
"""

# O JavaScript roda dentro do ShadowRoot do componente (CCv2). Nunca use
# ``parentElement.dataset``: ShadowRoot não tem ``dataset``. O controle de
# "já solicitei automaticamente" fica em um WeakMap indexado pelo próprio
# parentElement, que sobrevive às re-renderizações do componente.
_JS = """
const INSTANCE_STATE = new WeakMap()

const MESSAGES = {
  unsupported: "Geolocalização indisponível neste navegador. Informe a temperatura manualmente.",
  insecure: "A localização exige uma conexão segura (HTTPS) ou localhost. Informe a temperatura manualmente.",
  denied: "Permissão de localização negada. Autorize o acesso nas configurações do navegador e use o botão para tentar novamente.",
  unavailable: "Localização indisponível neste dispositivo. Verifique o GPS ou a conexão e use o botão para tentar novamente.",
  timeout: "O tempo para obter a localização esgotou. Use o botão para tentar novamente.",
  invalid: "O dispositivo não retornou coordenadas válidas. Use o botão para tentar novamente.",
  retry: "Localização não capturada. Use o botão para tentar novamente.",
  requesting: "Solicitando autorização de localização...",
  waiting: "Aguardando autorização do navegador para acessar a localização...",
  generic: "Não foi possível obter a localização. Use o botão para tentar novamente ou informe a temperatura manualmente.",
}

function describeGeolocationError(error) {
  const code = error && typeof error === "object" ? error.code : undefined
  switch (code) {
    case 1:
      return MESSAGES.denied
    case 2:
      return MESSAGES.unavailable
    case 3:
      return MESSAGES.timeout
    default:
      return MESSAGES.generic
  }
}

function getInstanceState(parentElement) {
  let state = INSTANCE_STATE.get(parentElement)
  if (!state) {
    state = { autoAttempted: false, inFlight: false }
    INSTANCE_STATE.set(parentElement, state)
  }
  return state
}

function coordinateValue(value) {
  if (value === null || value === undefined || value === "") return null
  const number = Number(value)
  return Number.isFinite(number) ? number : null
}

function hasCoordinates(data) {
  return coordinateValue(data.latitude) !== null && coordinateValue(data.longitude) !== null
}

function successMessage(latitude, longitude, accuracy) {
  const accuracyLabel =
    accuracy !== null ? ` (precisão ${Math.round(accuracy)} m)` : ""
  return `Localização capturada: ${latitude.toFixed(5)}, ${longitude.toFixed(5)}${accuracyLabel}.`
}

function availableMessage(data) {
  const latitude = coordinateValue(data.latitude)
  const longitude = coordinateValue(data.longitude)
  const accuracy = coordinateValue(data.accuracy)
  const accuracyLabel =
    accuracy !== null ? ` (precisão ${Math.round(accuracy)} m)` : ""
  return `Localização disponível: ${latitude.toFixed(5)}, ${longitude.toFixed(5)}${accuracyLabel}.`
}

function idleMessage(data, state) {
  if (hasCoordinates(data)) {
    return { text: availableMessage(data), error: false }
  }
  if (data.error) {
    return { text: String(data.error), error: true }
  }
  if (state.autoAttempted || data.auto_request === false) {
    return { text: MESSAGES.retry, error: true }
  }
  return { text: MESSAGES.requesting, error: false }
}

export default function (component) {
  if (!component || typeof component !== "object") {
    return
  }

  const { data, parentElement, setStateValue, setTriggerValue } = component

  // Algumas versões/ambientes não entregam parentElement. Falhe de forma
  // controlada (sem derrubar o componente) em vez de acessar propriedades de
  // um objeto inexistente.
  if (!parentElement || typeof parentElement.querySelector !== "function") {
    console.error(
      "[acnnorte_geolocation] parentElement indisponível; componente não pode ser montado."
    )
    return
  }

  const button = parentElement.querySelector("#geo-button")
  const status = parentElement.querySelector("#geo-status")
  if (!button || !status) {
    return
  }

  const componentData = data && typeof data === "object" ? data : {}
  const state = getInstanceState(parentElement)
  const setState = typeof setStateValue === "function" ? setStateValue : () => {}
  const setTrigger =
    typeof setTriggerValue === "function" ? setTriggerValue : () => {}

  const showMessage = (message, isError) => {
    status.textContent = message
    status.setAttribute("data-state", isError ? "error" : "info")
  }

  const reportFailure = (message) => {
    state.inFlight = false
    setState("error", message)
    setTrigger("captured", false)
    showMessage(message, true)
  }

  const requestLocation = () => {
    // Evita chamadas duplicadas (cliques repetidos ou re-renderizações).
    if (state.inFlight) {
      return
    }

    if (typeof navigator === "undefined" || !navigator.geolocation) {
      reportFailure(MESSAGES.unsupported)
      return
    }

    if (typeof window !== "undefined" && window.isSecureContext === false) {
      reportFailure(MESSAGES.insecure)
      return
    }

    state.inFlight = true
    showMessage(MESSAGES.waiting, false)

    let settled = false

    const onSuccess = (position) => {
      if (settled) return
      settled = true

      const coords = position && position.coords ? position.coords : null
      const latitude = coords ? coordinateValue(coords.latitude) : null
      const longitude = coords ? coordinateValue(coords.longitude) : null

      if (latitude === null || longitude === null) {
        reportFailure(MESSAGES.invalid)
        return
      }

      const accuracy = coords ? coordinateValue(coords.accuracy) : null
      state.inFlight = false
      setState("latitude", latitude)
      setState("longitude", longitude)
      setState("accuracy", accuracy)
      setState("error", "")
      setTrigger("captured", true)
      showMessage(successMessage(latitude, longitude, accuracy), false)
    }

    const onError = (error) => {
      if (settled) return
      settled = true
      reportFailure(describeGeolocationError(error))
    }

    try {
      navigator.geolocation.getCurrentPosition(onSuccess, onError, {
        enableHighAccuracy: true,
        timeout: 15000,
        maximumAge: 60000,
      })
    } catch (error) {
      onError(error)
    }
  }

  button.onclick = (event) => {
    if (event && typeof event.preventDefault === "function") {
      event.preventDefault()
    }
    state.autoAttempted = true
    requestLocation()
  }

  // Reidrata a mensagem a partir do estado enviado pelo Python, sem apagar
  // uma solicitação em andamento.
  if (!state.inFlight) {
    const info = idleMessage(componentData, state)
    showMessage(info.text, info.error)
  }

  // Solicita automaticamente apenas uma vez. Depois de negado ou indisponível,
  // o Python envia auto_request=False e novas tentativas ficam por conta do
  // botão.
  if (
    componentData.auto_request === true &&
    !state.autoAttempted &&
    !state.inFlight
  ) {
    state.autoAttempted = true
    requestLocation()
  }

  return () => {
    button.onclick = null
  }
}
"""

_COMPONENT = st.components.v2.component(
    "acnnorte_geolocation",
    html=_HTML,
    css=_CSS,
    js=_JS,
)

_STATE_FIELDS = ("latitude", "longitude", "accuracy", "error", "captured")


def _as_float(value: Any) -> float | None:
    """Converte um valor em float finito, devolvendo ``None`` se inválido."""
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def _coordinate(value: Any, minimum: float, maximum: float) -> float | None:
    """Valida uma coordenada dentro do intervalo geográfico permitido."""
    number = _as_float(value)
    if number is None or not (minimum <= number <= maximum):
        return None
    return number


def _position(state: Mapping[str, Any]) -> tuple[float | None, float | None]:
    latitude = _coordinate(state.get("latitude"), -90.0, 90.0)
    longitude = _coordinate(state.get("longitude"), -180.0, 180.0)
    if latitude is None or longitude is None:
        return None, None
    return latitude, longitude


def _component_state(key: str, result: Any = None) -> dict:
    """Normaliza o estado do componente para um dicionário simples.

    Lê o estado persistido em ``st.session_state`` e complementa com os valores
    devolvidos pelo componente na execução atual. Nunca quebra quando o estado
    ainda não existe ou não é um dicionário.
    """
    raw_state = st.session_state.get(key, {})
    state = dict(raw_state) if isinstance(raw_state, Mapping) else {}

    if result is not None:
        for field in _STATE_FIELDS:
            value = getattr(result, field, None)
            if value is not None:
                state[field] = value
    return state


def geolocation(key: str, *, auto_request: bool = True) -> dict:
    """Monta o componente e devolve latitude/longitude/erro do dispositivo.

    ``auto_request`` controla a solicitação automática de localização. Ela só
    acontece enquanto não houver posição capturada nem erro registrado, e o
    JavaScript garante que ocorra no máximo uma vez por montagem. Depois disso,
    o usuário pode tentar novamente pelo botão.
    """
    state = _component_state(key)
    latitude, longitude = _position(state)
    has_position = latitude is not None and longitude is not None
    error = str(state.get("error") or "").strip()
    should_auto_request = bool(auto_request and not has_position and not error)

    result = _COMPONENT(
        key=key,
        data={
            "latitude": latitude,
            "longitude": longitude,
            "accuracy": _as_float(state.get("accuracy")),
            "error": error,
            "auto_request": should_auto_request,
        },
        on_latitude_change=lambda: None,
        on_longitude_change=lambda: None,
        on_accuracy_change=lambda: None,
        on_error_change=lambda: None,
        on_captured_change=lambda: None,
    )
    merged = _component_state(key, result)
    merged["latitude"], merged["longitude"] = _position(merged)
    merged["accuracy"] = _as_float(merged.get("accuracy"))
    return merged
