"""Componente de assinatura digital (Streamlit Components v2).

Permite desenhar com mouse ou tela sensível ao toque, desfazer, limpar e
refazer. O desenho é exportado como PNG (data URL) e salvo pelo aplicativo no
registro da visita. Não há declaração de validade jurídica automática.
"""

from __future__ import annotations

from typing import Any, Callable

import streamlit as st

_HTML = """
<div class="acn-sign">
  <div class="acn-sign-head">
    <span id="sig-status">Assine com o mouse ou o dedo</span>
    <div class="acn-sign-actions">
      <button id="sig-undo" type="button">Desfazer</button>
      <button id="sig-clear" type="button">Limpar</button>
    </div>
  </div>
  <div class="acn-sign-canvas-wrap">
    <canvas id="sig-canvas"></canvas>
    <span id="sig-placeholder">Assine aqui</span>
  </div>
</div>
"""

_CSS = """
.acn-sign {
  font-family: 'Segoe UI', Arial, sans-serif;
  background: #FFFFFF;
  border: 1px solid #CDE4D3;
  border-radius: 12px;
  padding: 10px;
  color: #000000;
}
.acn-sign-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 8px;
}
#sig-status { font-size: 0.78rem; color: #000000; }
.acn-sign-actions { display: flex; gap: 6px; }
.acn-sign-actions button {
  background: #F3F4F6;
  color: #111827;
  border: 1px solid #D1D5DB;
  border-radius: 8px;
  padding: 6px 10px;
  font-size: 0.78rem;
  font-weight: 600;
  cursor: pointer;
}
.acn-sign-actions button:hover { background: #E5E7EB; }
.acn-sign-canvas-wrap {
  position: relative;
  width: 100%;
  height: 180px;
  background: #FFFFFF;
  border: 1px dashed #9CA3AF;
  border-radius: 10px;
  overflow: hidden;
}
#sig-canvas {
  display: block;
  width: 100%;
  height: 100%;
  touch-action: none;
  cursor: crosshair;
}
#sig-placeholder {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #9CA3AF;
  font-size: 0.9rem;
  pointer-events: none;
  user-select: none;
}
"""

_JS = """
export default function (component) {
  const { data, parentElement, setStateValue } = component
  const canvas = parentElement.querySelector("#sig-canvas")
  const placeholder = parentElement.querySelector("#sig-placeholder")
  const status = parentElement.querySelector("#sig-status")
  const undoButton = parentElement.querySelector("#sig-undo")
  const clearButton = parentElement.querySelector("#sig-clear")
  if (!canvas || !placeholder || !status || !undoButton || !clearButton) return

  const ctx = canvas.getContext("2d")
  if (!ctx) return

  // O runtime do Components v2 reinvoca esta função sempre que `data` muda.
  // O estado do desenho fica num WeakMap ligado ao parentElement para
  // sobreviver a essas reinvocações e permitir desfazer vários traços.
  const store = (globalThis.__acnSignatureStates ||= new WeakMap())
  let state = store.get(parentElement)
  if (!state) {
    state = {
      strokes: [],
      currentStroke: null,
      hydratedImage: null,
      hydratedUrl: "",
      lastExported: "",
      undoStack: [],
      loadToken: 0,
      cssWidth: 0,
      cssHeight: 0,
    }
    store.set(parentElement, state)
  }

  const hasInk = () => state.strokes.length > 0 || state.hydratedImage !== null

  function resize() {
    const rect = canvas.getBoundingClientRect()
    const dpr = window.devicePixelRatio || 1
    state.cssWidth = Math.max(1, rect.width)
    state.cssHeight = Math.max(1, rect.height)
    canvas.width = Math.round(state.cssWidth * dpr)
    canvas.height = Math.round(state.cssHeight * dpr)
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0)
    redraw()
  }

  function drawStroke(stroke) {
    if (!stroke || !stroke.points.length) return
    ctx.beginPath()
    ctx.lineWidth = 2.4
    ctx.lineCap = "round"
    ctx.lineJoin = "round"
    ctx.strokeStyle = "#111827"
    const first = stroke.points[0]
    ctx.moveTo(first.x, first.y)
    if (stroke.points.length === 1) {
      ctx.lineTo(first.x + 0.1, first.y + 0.1)
    } else {
      for (let i = 1; i < stroke.points.length; i += 1) {
        ctx.lineTo(stroke.points[i].x, stroke.points[i].y)
      }
    }
    ctx.stroke()
  }

  function redraw() {
    ctx.clearRect(0, 0, state.cssWidth, state.cssHeight)
    if (state.hydratedImage) {
      ctx.drawImage(state.hydratedImage, 0, 0, state.cssWidth, state.cssHeight)
    }
    for (const stroke of state.strokes) drawStroke(stroke)
    placeholder.style.display = hasInk() ? "none" : "flex"
    status.textContent = hasInk()
      ? "Assinatura registrada — você pode desfazer ou limpar"
      : "Assine com o mouse ou o dedo"
  }

  function exportNow() {
    const url = hasInk() ? canvas.toDataURL("image/png") : ""
    if (url === state.lastExported) return
    state.undoStack.push(state.lastExported)
    state.lastExported = url
    setStateValue("data_url", url)
  }

  function loadImage(url, onLoad) {
    const token = (state.loadToken += 1)
    const image = new Image()
    image.onload = () => {
      if (token !== state.loadToken) return
      onLoad(image)
    }
    image.src = url
  }

  function setCanvasFromUrl(url) {
    state.strokes = []
    state.currentStroke = null
    state.hydratedImage = null
    state.hydratedUrl = ""
    if (!url) {
      state.loadToken += 1
      state.lastExported = ""
      redraw()
      setStateValue("data_url", "")
      return
    }
    loadImage(url, (image) => {
      state.hydratedImage = image
      state.hydratedUrl = url
      state.lastExported = url
      redraw()
      setStateValue("data_url", url)
    })
  }

  function pointFromEvent(event) {
    const rect = canvas.getBoundingClientRect()
    return { x: event.clientX - rect.left, y: event.clientY - rect.top }
  }

  const controller = new AbortController()
  const listenerOptions = { signal: controller.signal }

  canvas.addEventListener("pointerdown", (event) => {
    event.preventDefault()
    try {
      canvas.setPointerCapture(event.pointerId)
    } catch (error) {
      // Alguns navegadores podem recusar a captura; o desenho continua.
    }
    state.currentStroke = { points: [pointFromEvent(event)] }
    state.strokes.push(state.currentStroke)
    redraw()
  }, listenerOptions)

  canvas.addEventListener("pointermove", (event) => {
    if (!state.currentStroke) return
    event.preventDefault()
    state.currentStroke.points.push(pointFromEvent(event))
    redraw()
  }, listenerOptions)

  function finishStroke(event) {
    if (!state.currentStroke) return
    if (event) event.preventDefault()
    state.currentStroke = null
    redraw()
    exportNow()
  }

  canvas.addEventListener("pointerup", finishStroke, listenerOptions)
  canvas.addEventListener("pointercancel", finishStroke, listenerOptions)

  undoButton.onclick = (event) => {
    event.preventDefault()
    if (state.undoStack.length === 0) return
    setCanvasFromUrl(state.undoStack.pop())
  }

  clearButton.onclick = (event) => {
    event.preventDefault()
    if (state.lastExported !== "") {
      state.undoStack.push(state.lastExported)
    }
    state.strokes = []
    state.currentStroke = null
    state.hydratedImage = null
    state.hydratedUrl = ""
    state.lastExported = ""
    redraw()
    setStateValue("data_url", "")
  }

  const incoming = data?.image || ""
  if (
    incoming &&
    incoming !== state.lastExported &&
    incoming !== state.hydratedUrl
  ) {
    loadImage(incoming, (image) => {
      state.hydratedImage = image
      state.hydratedUrl = incoming
      state.lastExported = incoming
      redraw()
    })
  }

  const observer = new ResizeObserver(() => resize())
  observer.observe(canvas)
  resize()

  return () => {
    observer.disconnect()
    controller.abort()
    undoButton.onclick = null
    clearButton.onclick = null
  }
}
"""

_COMPONENT = st.components.v2.component(
    "acnnorte_signature_pad",
    html=_HTML,
    css=_CSS,
    js=_JS,
)


def signature_pad(
    *,
    key: str,
    image: str = "",
    on_change: Callable[[], None] | None = None,
) -> dict:
    """Monta a área de assinatura e devolve o estado atual do desenho.

    Args:
        key: chave única do componente (por visita e por responsável).
        image: data URL da assinatura já salva, para visualização/reedição.
        on_change: callback executado quando o desenho muda.
    """
    if on_change is None:
        on_change = lambda: None

    result = _COMPONENT(
        key=key,
        data={"image": image or ""},
        on_data_url_change=on_change,
    )

    state = st.session_state.get(key, {})
    if not isinstance(state, dict):
        state = {}
    if "data_url" not in state:
        value = getattr(result, "data_url", None)
        if value is not None:
            state["data_url"] = value
    return state


def signature_data_url(state: Any) -> str:
    """Extrai o data URL do estado do componente, com fallback seguro."""
    if isinstance(state, dict):
        value = state.get("data_url")
    else:
        value = getattr(state, "data_url", None)
    return str(value) if value else ""


def signature_state_has_drawing(state: Any) -> bool:
    """Informa se o estado do componente já possui a chave ``data_url``."""
    if isinstance(state, dict):
        return "data_url" in state
    return state is not None and getattr(state, "data_url", None) is not None
