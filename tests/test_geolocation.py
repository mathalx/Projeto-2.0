"""Testes do componente de geolocalização (CCv2).

Cobrem o wrapper Python e o comportamento do JavaScript do componente. O teste
de JavaScript roda em Node (quando disponível) e simula um ``ShadowRoot`` sem
``dataset``, que era exatamente a condição que derrubava o componente com
``Cannot read properties of undefined (reading 'autoRequested')``.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from pathlib import Path
from types import SimpleNamespace

import pytest

from src import geolocation as geo_module

# ---------------------------------------------------------------------------
# Wrapper Python
# ---------------------------------------------------------------------------


class _FakeComponent:
    def __init__(self, result: object | None = None) -> None:
        self.calls: list[dict] = []
        self.result = result if result is not None else SimpleNamespace()

    def __call__(self, **kwargs):
        self.calls.append(kwargs)
        return self.result


@pytest.fixture()
def fake_component(monkeypatch):
    fake = _FakeComponent()
    monkeypatch.setattr(geo_module, "_COMPONENT", fake)
    return fake


@pytest.fixture()
def session_state(monkeypatch):
    state: dict = {}
    monkeypatch.setattr(geo_module.st, "session_state", state)
    return state


def test_monta_com_auto_request_quando_nao_ha_estado(fake_component, session_state):
    result = geo_module.geolocation("geo")

    assert result["latitude"] is None
    assert result["longitude"] is None

    call = fake_component.calls[0]
    assert call["key"] == "geo"
    assert call["data"] == {
        "latitude": None,
        "longitude": None,
        "accuracy": None,
        "error": "",
        "auto_request": True,
    }

    callbacks = {name for name in call if name.startswith("on_")}
    assert callbacks == {
        "on_latitude_change",
        "on_longitude_change",
        "on_accuracy_change",
        "on_error_change",
        "on_captured_change",
    }


def test_nao_solicita_novamente_quando_ja_existe_posicao(fake_component, session_state):
    session_state["geo"] = {
        "latitude": "-23.5505",
        "longitude": "-46.6333",
        "accuracy": "12.4",
        "error": "",
    }

    result = geo_module.geolocation("geo")

    data = fake_component.calls[0]["data"]
    assert data["auto_request"] is False
    assert data["latitude"] == pytest.approx(-23.5505)
    assert data["longitude"] == pytest.approx(-46.6333)
    assert data["accuracy"] == pytest.approx(12.4)
    assert result["latitude"] == pytest.approx(-23.5505)


def test_nao_repete_solicitacao_automatica_apos_erro(fake_component, session_state):
    session_state["geo"] = {"error": "Permissão de localização negada."}

    geo_module.geolocation("geo")

    data = fake_component.calls[0]["data"]
    assert data["auto_request"] is False
    assert data["error"] == "Permissão de localização negada."


def test_permite_desativar_solicitacao_automatica(fake_component, session_state):
    geo_module.geolocation("geo", auto_request=False)

    assert fake_component.calls[0]["data"]["auto_request"] is False


@pytest.mark.parametrize(
    ("latitude", "longitude"),
    [
        ("abc", -46.6),
        (95.0, -46.6),
        (-23.5, 200.0),
        (None, None),
        (float("nan"), -46.6),
        (float("inf"), -46.6),
    ],
)
def test_coordenadas_invalidas_nao_bloqueiam_nova_tentativa(
    fake_component, session_state, latitude, longitude
):
    session_state["geo"] = {"latitude": latitude, "longitude": longitude}

    result = geo_module.geolocation("geo")

    data = fake_component.calls[0]["data"]
    assert data["auto_request"] is True
    assert data["latitude"] is None
    assert data["longitude"] is None
    assert result["latitude"] is None
    assert result["longitude"] is None


def test_estado_nao_dicionario_e_ignorado(fake_component, session_state):
    session_state["geo"] = object()

    result = geo_module.geolocation("geo")

    assert fake_component.calls[0]["data"]["auto_request"] is True
    assert result["latitude"] is None


def test_resultado_do_componente_complementa_estado(fake_component, session_state):
    fake_component.result = SimpleNamespace(
        latitude=-23.5, longitude=-46.6, accuracy=8.0, error="", captured=True
    )

    result = geo_module.geolocation("geo")

    assert result["latitude"] == pytest.approx(-23.5)
    assert result["longitude"] == pytest.approx(-46.6)
    assert result["accuracy"] == pytest.approx(8.0)
    assert result["error"] == ""
    assert result["captured"] is True


def test_js_nao_usa_dataset_do_parent_element():
    """ShadowRoot não possui ``dataset``; acessá-lo derruba o componente."""
    assert "parentElement.dataset" not in geo_module._JS
    assert "parentElement?.dataset" not in geo_module._JS


# ---------------------------------------------------------------------------
# Comportamento do JavaScript (Node)
# ---------------------------------------------------------------------------

_NODE_HARNESS = r"""
import assert from "node:assert/strict"
import renderComponent from "./component.mjs"

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms))

function setEnvironment({ geolocation, secureContext = true, hasNavigator = true } = {}) {
  Object.defineProperty(globalThis, "navigator", {
    configurable: true,
    value: hasNavigator ? { geolocation } : undefined,
  })
  globalThis.window = { isSecureContext: secureContext }
}

function makeInstance(data) {
  const statusElement = {
    textContent: "",
    attributes: {},
    setAttribute(name, value) {
      this.attributes[name] = value
    },
  }
  const buttonElement = { onclick: null }
  // ShadowRoot: tem querySelector, mas NÃO tem dataset.
  const parentElement = {
    querySelector(selector) {
      if (selector === "#geo-button") return buttonElement
      if (selector === "#geo-status") return statusElement
      return null
    },
  }
  assert.equal("dataset" in parentElement, false)

  const stateValues = []
  const triggerValues = []
  let cleanup = null

  const component = {
    name: "acnnorte_geolocation",
    key: "geo-test",
    data,
    parentElement,
    setStateValue(key, value) {
      stateValues.push([key, value])
    },
    setTriggerValue(key, value) {
      triggerValues.push([key, value])
    },
  }

  const mount = (nextData) => {
    component.data = nextData
    cleanup = renderComponent(component)
  }

  mount(data)

  return {
    component,
    parentElement,
    buttonElement,
    statusElement,
    stateValues,
    triggerValues,
    state() {
      return Object.fromEntries(stateValues)
    },
    remount(nextData) {
      mount(nextData)
    },
    cleanup() {
      if (cleanup) cleanup()
    },
  }
}

const tests = []
const test = (name, fn) => tests.push([name, fn])

test("autoriza e captura latitude/longitude", async () => {
  const calls = []
  setEnvironment({
    geolocation: {
      getCurrentPosition(success, error, options) {
        calls.push(options)
        setTimeout(() => {
          success({ coords: { latitude: -23.5505, longitude: -46.6333, accuracy: 12.4 } })
        }, 0)
      },
    },
  })

  const instance = makeInstance({ auto_request: true })
  assert.equal(calls.length, 1)
  assert.match(instance.statusElement.textContent, /Aguardando autorização/)

  await sleep(10)

  const state = instance.state()
  assert.equal(state.latitude, -23.5505)
  assert.equal(state.longitude, -46.6333)
  assert.equal(state.accuracy, 12.4)
  assert.equal(state.error, "")
  assert.deepEqual(instance.triggerValues.at(-1), ["captured", true])
  assert.equal(instance.statusElement.attributes["data-state"], "info")
  assert.match(instance.statusElement.textContent, /Localização capturada/)
  assert.equal(calls[0].enableHighAccuracy, true)
})

for (const [code, pattern] of [
  [1, /negada/i],
  [2, /indisponível neste dispositivo/i],
  [3, /esgotou/i],
]) {
  test(`trata erro de geolocalização ${code}`, async () => {
    setEnvironment({
      geolocation: {
        getCurrentPosition(success, error) {
          setTimeout(() => error({ code }), 0)
        },
      },
    })

    const instance = makeInstance({ auto_request: true })
    await sleep(10)

    const state = instance.state()
    assert.match(state.error, pattern)
    assert.equal(state.latitude, undefined)
    assert.deepEqual(instance.triggerValues.at(-1), ["captured", false])
    assert.equal(instance.statusElement.attributes["data-state"], "error")
  })
}

test("trata navegador sem geolocalização", () => {
  setEnvironment({ geolocation: undefined })
  const instance = makeInstance({ auto_request: true })
  assert.match(instance.state().error, /indisponível neste navegador/i)
})

test("trata ambiente sem navigator", () => {
  setEnvironment({ hasNavigator: false })
  const instance = makeInstance({ auto_request: true })
  assert.match(instance.state().error, /indisponível neste navegador/i)
})

test("trata contexto inseguro (HTTP)", () => {
  setEnvironment({
    secureContext: false,
    geolocation: {
      getCurrentPosition() {
        throw new Error("não deveria solicitar em contexto inseguro")
      },
    },
  })
  const instance = makeInstance({ auto_request: true })
  assert.match(instance.state().error, /HTTPS/)
})

test("permite nova tentativa após permissão negada", async () => {
  let mode = "deny"
  let calls = 0
  setEnvironment({
    geolocation: {
      getCurrentPosition(success, error) {
        calls += 1
        setTimeout(() => {
          if (mode === "deny") {
            error({ code: 1 })
          } else {
            success({ coords: { latitude: 1.5, longitude: 2.5, accuracy: 5 } })
          }
        }, 0)
      },
    },
  })

  const instance = makeInstance({ auto_request: true })
  await sleep(10)
  assert.match(instance.state().error, /negada/i)

  mode = "grant"
  instance.remount({ auto_request: false, error: instance.state().error })
  assert.match(instance.statusElement.textContent, /tentar novamente/i)

  instance.buttonElement.onclick({ preventDefault() {} })
  assert.equal(calls, 2)
  await sleep(10)

  assert.equal(instance.state().latitude, 1.5)
  assert.equal(instance.state().longitude, 2.5)
  assert.match(instance.statusElement.textContent, /Localização capturada/)
})

test("não repete a solicitação automática em re-renderizações", async () => {
  let calls = 0
  let pending = null
  setEnvironment({
    geolocation: {
      getCurrentPosition(success, error) {
        calls += 1
        pending = { success, error }
      },
    },
  })

  const instance = makeInstance({ auto_request: true })
  assert.equal(calls, 1)

  instance.remount({ auto_request: true })
  instance.remount({ auto_request: true })
  assert.equal(calls, 1)
  assert.match(instance.statusElement.textContent, /Aguardando autorização/)

  pending.success({ coords: { latitude: -1, longitude: -2, accuracy: 3 } })
  await sleep(0)
  assert.equal(instance.state().latitude, -1)
  assert.equal(instance.state().longitude, -2)
})

test("não solicita quando auto_request é falso", () => {
  let calls = 0
  setEnvironment({
    geolocation: {
      getCurrentPosition() {
        calls += 1
      },
    },
  })

  const instance = makeInstance({ auto_request: false })
  assert.equal(calls, 0)
  assert.match(instance.statusElement.textContent, /Use o botão para tentar novamente/)

  instance.buttonElement.onclick({ preventDefault() {} })
  assert.equal(calls, 1)
})

test("tolera data ausente ou inválido", () => {
  setEnvironment({
    geolocation: {
      getCurrentPosition() {
        throw new Error("não deveria solicitar automaticamente")
      },
    },
  })

  const withoutData = makeInstance(undefined)
  assert.match(withoutData.statusElement.textContent, /Solicitando autorização/)

  const invalidCoordinates = makeInstance({
    latitude: "abc",
    longitude: null,
    auto_request: false,
  })
  assert.match(invalidCoordinates.statusElement.textContent, /tentar novamente/i)
})

test("ignora componente/parentElement inválidos sem lançar erro", () => {
  setEnvironment({ geolocation: undefined })
  assert.equal(renderComponent(undefined), undefined)
  assert.equal(renderComponent({ data: {}, parentElement: null }), undefined)
  assert.equal(
    renderComponent({ data: {}, parentElement: { querySelector: "não é função" } }),
    undefined
  )
})

test("remove o handler ao desmontar", () => {
  setEnvironment({ geolocation: undefined })
  const instance = makeInstance({ auto_request: false })
  assert.equal(typeof instance.buttonElement.onclick, "function")
  instance.cleanup()
  assert.equal(instance.buttonElement.onclick, null)
})

async function main() {
  for (const [name, fn] of tests) {
    await fn()
    console.error(`PASS ${name}`)
  }
  console.log(JSON.stringify({ passed: tests.length }))
}

main().catch((error) => {
  console.error(error)
  process.exit(1)
})
"""


def test_javascript_do_componente(tmp_path: Path):
    node = shutil.which("node")
    if not node:
        pytest.skip("Node.js não está disponível para executar o componente.")

    (tmp_path / "component.mjs").write_text(geo_module._JS, encoding="utf-8")
    (tmp_path / "harness.mjs").write_text(_NODE_HARNESS, encoding="utf-8")

    completed = subprocess.run(
        [node, str(tmp_path / "harness.mjs")],
        capture_output=True,
        text=True,
        timeout=120,
        cwd=tmp_path,
    )

    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert json.loads(completed.stdout.strip().splitlines()[-1])["passed"] >= 13
