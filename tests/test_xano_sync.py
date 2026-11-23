import json
import os
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from io import BytesIO
from urllib.parse import parse_qs, urlparse

import pytest

import src.storage_manager as storage
import src.xano_sync as xano_sync


class MockXanoDB:
    def __init__(self):
        self.clients = {}
        self.visits = {}
        self.photos = {}
        self._cid = 1
        self._vid = 1
        self._pid = 1
        self.lock = threading.Lock()

    def reset(self):
        with self.lock:
            self.clients.clear()
            self.visits.clear()
            self.photos.clear()
            self._cid = 1
            self._vid = 1
            self._pid = 1


DB = MockXanoDB()


def _json(handler, status, payload):
    body = json.dumps(payload).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def _read_json_body(handler):
    length = int(handler.headers.get("Content-Length") or 0)
    raw = handler.rfile.read(length) if length else b""
    if not raw:
        return {}
    try:
        return json.loads(raw.decode("utf-8"))
    except Exception:
        return {}


def _parse_multipart(handler):
    ctype = handler.headers.get("Content-Type") or ""
    if "multipart/form-data" not in ctype:
        return {}, {}
    # boundary
    boundary = None
    for part in ctype.split(";"):
        part = part.strip()
        if part.startswith("boundary="):
            boundary = part.split("=", 1)[1].strip().strip('"')
    if not boundary:
        return {}, {}
    length = int(handler.headers.get("Content-Length") or 0)
    raw = handler.rfile.read(length) if length else b""
    sep = ("--" + boundary).encode()
    fields = {}
    files = {}
    for chunk in raw.split(sep):
        if not chunk or chunk in (b"--\r\n", b"--", b"\r\n"):
            continue
        chunk = chunk.strip(b"\r\n")
        if chunk == b"--":
            continue
        header_blob, _, content = chunk.partition(b"\r\n\r\n")
        if not _:
            continue
        content = content.rstrip(b"\r\n")
        headers = header_blob.decode("utf-8", errors="ignore")
        name = None
        filename = None
        for line in headers.split("\r\n"):
            if line.lower().startswith("content-disposition"):
                for item in line.split(";"):
                    item = item.strip()
                    if item.startswith("name="):
                        name = item.split("=", 1)[1].strip().strip('"')
                    if item.startswith("filename="):
                        filename = item.split("=", 1)[1].strip().strip('"')
        if name is None:
            continue
        if filename is not None:
            files[name] = {"filename": filename, "content": content}
        else:
            fields[name] = content.decode("utf-8", errors="ignore")
    return fields, files


class Handler(BaseHTTPRequestHandler):
    server_version = "MockXano/1.0"

    def log_message(self, format, *args):
        return

    def _auth_ok(self):
        auth = self.headers.get("Authorization") or ""
        return auth.startswith("Bearer ") and len(auth) > 7

    def do_GET(self):
        if not self._auth_ok():
            return _json(self, 401, {"message": "Unauthorized"})
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")
        qs = parse_qs(parsed.query)
        # /clients
        if path.endswith("/clients"):
            with DB.lock:
                items = list(DB.clients.values())
            return _json(self, 200, {"items": items, "curPage": 1, "nextPage": None, "pageTotal": 1})
        # /clients/{id}
        if "/clients/" in path:
            try:
                cid = int(path.rsplit("/", 1)[-1])
            except Exception:
                return _json(self, 404, {"message": "Not found"})
            with DB.lock:
                client = DB.clients.get(cid)
                if not client:
                    return _json(self, 404, {"message": "Cliente não encontrado"})
                visits = [v for v in DB.visits.values() if v.get("client_id") == cid]
            return _json(self, 200, {"client": client, "visits": visits})
        # /visits
        if path.endswith("/visits"):
            with DB.lock:
                items = list(DB.visits.values())
            client_id = qs.get("client_id", [None])[0]
            if client_id is not None:
                try:
                    items = [v for v in items if int(v.get("client_id")) == int(client_id)]
                except Exception:
                    pass
            return _json(self, 200, {"items": items, "curPage": 1, "nextPage": None, "pageTotal": 1})
        # /visits/{id}
        if "/visits/" in path:
            try:
                vid = int(path.rsplit("/", 1)[-1])
            except Exception:
                return _json(self, 404, {"message": "Not found"})
            with DB.lock:
                visit = DB.visits.get(vid)
                if not visit:
                    return _json(self, 404, {"message": "Visita não encontrada"})
                photos = [p for p in DB.photos.values() if p.get("visit_id") == vid]
            return _json(self, 200, {"visit": dict(visit), "photos": photos})
        # /photos
        if path.endswith("/photos"):
            visit_id = qs.get("visit_id", [None])[0]
            with DB.lock:
                items = list(DB.photos.values())
            if visit_id is not None:
                try:
                    items = [p for p in items if int(p.get("visit_id")) == int(visit_id)]
                except Exception:
                    pass
            return _json(self, 200, {"items": items, "curPage": 1, "nextPage": None, "pageTotal": 1})
        return _json(self, 404, {"message": "Not found"})

    def do_POST(self):
        if not self._auth_ok():
            return _json(self, 401, {"message": "Unauthorized"})
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")
        ctype = self.headers.get("Content-Type") or ""
        if "multipart/form-data" in ctype:
            body, files = _parse_multipart(self)
        else:
            body = _read_json_body(self)
            files = {}

        if path.endswith("/clients"):
            with DB.lock:
                cid = DB._cid
                DB._cid += 1
                record = {"id": cid, "active": True, **body}
                DB.clients[cid] = record
            return _json(self, 200, record)

        if path.endswith("/visits"):
            with DB.lock:
                client_id = int(body.get("client_id"))
                if client_id not in DB.clients:
                    return _json(self, 404, {"message": "Cliente não encontrado"})
                vid = DB._vid
                DB._vid += 1
                record = {
                    "id": vid,
                    "created_at": "2026-11-12T00:00:00Z",
                    "updated_at": "2026-11-12T00:00:00Z",
                    "client_id": client_id,
                    "user_id": body.get("user_id"),
                    "status": body.get("status", "rascunho"),
                    "visit_date": body.get("visit_date"),
                    "current_step": body.get("current_step", 1),
                    "checklist_epi": body.get("checklist_epi", {}),
                    "checklist_condicoes_gerais": body.get("checklist_condicoes_gerais", {}),
                    "checklist_incendio": body.get("checklist_incendio", {}),
                    "checklist_maquinas": body.get("checklist_maquinas", {}),
                    "checklist_documentacao": body.get("checklist_documentacao", {}),
                    "general_observations": body.get("general_observations", ""),
                }
                DB.visits[vid] = record
            return _json(self, 200, dict(record))

        if path.endswith("/photos"):
            visit_id = int(body.get("visit_id"))
            with DB.lock:
                if visit_id not in DB.visits:
                    return _json(self, 404, {"message": "Visita não encontrada"})
                pid = DB._pid
                DB._pid += 1
                image = files.get("image") or {}
                record = {
                    "id": pid,
                    "visit_id": visit_id,
                    "caption": body.get("caption", ""),
                    "display_order": int(body.get("display_order") or 0),
                    "image": {
                        "path": f"/vault/{pid}_{image.get('filename','foto.jpg')}",
                        "name": image.get("filename", "foto.jpg"),
                        "type": "image",
                        "size": len(image.get("content", b"")),
                        "mime": "image/png",
                        "url": f"https://mock.xano.test/vault/{pid}.png",
                    },
                }
                DB.photos[pid] = record
            return _json(self, 200, record)

        return _json(self, 404, {"message": "Not found"})

    def do_PATCH(self):
        if not self._auth_ok():
            return _json(self, 401, {"message": "Unauthorized"})
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")
        ctype = self.headers.get("Content-Type") or ""
        if "multipart/form-data" in ctype:
            body, _files = _parse_multipart(self)
        else:
            body = _read_json_body(self)

        if "/clients/" in path:
            cid = int(path.rsplit("/", 1)[-1])
            with DB.lock:
                client = DB.clients.get(cid)
                if not client:
                    return _json(self, 404, {"message": "Cliente não encontrado"})
                client.update(body)
                DB.clients[cid] = client
            return _json(self, 200, dict(client))

        if "/visits/" in path and not path.endswith("/finalize"):
            vid = int(path.rsplit("/", 1)[-1])
            with DB.lock:
                visit = DB.visits.get(vid)
                if not visit:
                    return _json(self, 404, {"message": "Visita não encontrada"})
                if visit.get("status") == "finalizado":
                    return _json(self, 400, {"message": "Visita finalizada não pode ser editada."})
                visit.update(body)
                visit["updated_at"] = "2026-11-12T01:00:00Z"
                DB.visits[vid] = visit
            return _json(self, 200, dict(visit))

        if "/photos/" in path:
            pid = int(path.rsplit("/", 1)[-1])
            with DB.lock:
                photo = DB.photos.get(pid)
                if not photo:
                    return _json(self, 404, {"message": "Fotografia não encontrada"})
                photo.update({k: v for k, v in body.items() if k in ("caption", "display_order")})
                DB.photos[pid] = photo
            return _json(self, 200, dict(photo))

        return _json(self, 404, {"message": "Not found"})


@pytest.fixture(scope="module")
def mock_xano_server():
    DB.reset()
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{port}/api:acnnorte"
    yield base
    server.shutdown()
    server.server_close()


@pytest.fixture()
def xano_env(mock_xano_server, monkeypatch):
    monkeypatch.setenv("XANO_BASE_URL", mock_xano_server)
    monkeypatch.setenv("XANO_AUTH_TOKEN", "")
    monkeypatch.setattr(xano_sync, "_session_token", lambda: "test-token")
    monkeypatch.setattr(xano_sync, "_session_user_id", lambda: 1)
    yield
    DB.reset()


@pytest.fixture()
def local_store(tmp_path, monkeypatch):
    data_dir = tmp_path / "data"
    monkeypatch.setattr(storage, "DATA_DIR", str(data_dir))
    monkeypatch.setattr(storage, "CLIENTS_FILE", str(data_dir / "clients.json"))
    monkeypatch.setattr(storage, "VISITS_FILE", str(data_dir / "visits.json"))
    monkeypatch.setattr(storage, "PHOTOS_DIR", str(data_dir / "photos"))
    storage.init_storage()
    yield data_dir


def _seed_visit(local_store):
    ok, cid, _ = storage.add_client("Empresa Xano", "12.345.678/0001-90", "Rua X", "Resp", "1199", "x@e.com")
    assert ok
    ok, vid, _ = storage.add_visit(cid, "Técnico", "2026-11-10", status="Em Andamento", date_start="2026-11-10", date_end="2026-11-11")
    assert ok
    # worker
    png = (b"\x89PNG\r\n\x1a\n" + b"\x00" * 32)
    storage.save_worker_photo(vid, png, "worker.png")
    storage.update_worker_info(vid, "João Silva")
    # equipment/measurement
    storage.save_visit_equipment(vid, ["CHR-2386"])
    storage.update_visit_measurement(vid, "CHR-2386", horario="08:30")
    # weather
    storage.save_visit_weather(vid, 27.5, 60.0, internal_temperature_c=24.0, source="Manual", captured_at="2026-11-10 08:00:00", city="Manaus")
    # form/conclusions
    storage.update_visit(vid, {"epi": {"ok": "Sim"}}, "Obs local", "Conclusões", "Em Andamento")
    # photo
    storage.add_photo_to_visit(vid, png, "foto.png", "Legenda", horario="08:30", equipment_label="Chrompack 2386", equipment_code="CHR-2386", observations="Obs foto")
    return cid, vid


def test_sync_create_and_persist_client_visit_photo(xano_env, local_store):
    _cid, vid = _seed_visit(local_store)
    visit = storage.load_visits()[vid]

    # IDs remotos atribuídos sem duplicar
    assert visit.get("xano_id"), "visita deve ter xano_id após sincronização"
    assert visit.get("xano_synced_at")
    photo = visit["photos"][0]
    assert photo.get("xano_id"), "foto deve ter xano_id após upload"

    # Confirma persistência no "banco" Xano (consulta direta)
    with xano_sync._client("test-token") as client:
        remote = client.get(f"/visits/{int(visit['xano_id'])}")
    assert isinstance(remote, dict)
    rv = remote.get("visit") or remote
    assert rv.get("id") == visit["xano_id"]
    obs, ext = xano_sync._unpack_observations(rv.get("general_observations"))
    assert obs == "Obs local"
    assert ext.get("technician") == "Técnico"
    assert ext.get("date_start") == "2026-11-10"
    assert ext.get("worker", {}).get("name") == "João Silva"
    assert ext.get("weather", {}).get("source") == "Manual"
    assert (ext.get("equipment", {}).get("selected") or []), "equipamentos devem persistir"
    assert (ext.get("measurements") or []), "medições devem persistir"
    assert ext.get("forms", {}).get("epi") == {"ok": "Sim"}
    assert remote.get("photos"), "fotos devem estar vinculadas à visita no Xano"


def test_sync_update_and_query(xano_env, local_store):
    _cid, vid = _seed_visit(local_store)
    visit = storage.load_visits()[vid]
    xid = visit["xano_id"]

    ok, _ = storage.update_visit(vid, {"epi": {"ok": "Atualizado"}}, "Obs atualizada", "Conc", "Em Andamento")
    assert ok

    with xano_sync._client("test-token") as client:
        remote = client.get(f"/visits/{int(xid)}")
        listing = client.get("/visits", params={"client_id": remote["visit"]["client_id"]})
    rv = remote.get("visit") or remote
    _, ext = xano_sync._unpack_observations(rv.get("general_observations"))
    assert ext.get("forms", {}).get("epi") == {"ok": "Atualizado"}
    assert ext.get("observations") == "Obs atualizada"
    items = listing.get("items") if isinstance(listing, dict) else listing
    assert any(int(it.get("id", -1)) == int(xid) for it in (items or []))


def test_sync_no_duplicates_on_repeated_saves(xano_env, local_store):
    cid, vid = _seed_visit(local_store)
    visit = storage.load_visits()[vid]
    xid = visit["xano_id"]
    # salva novamente (dispara sync)
    storage.update_visit(vid, {"epi": {"ok": "Sim"}}, "Obs local", "Conclusões", "Em Andamento")
    storage.save_visit_weather(vid, 28.0, 55.0, source="Manual")
    visit2 = storage.load_visits()[vid]
    assert visit2["xano_id"] == xid

    with xano_sync._client("test-token") as client:
        visits = client.get("/visits")
        photos = client.get("/photos", params={"visit_id": xid})
    vitems = visits.get("items") if isinstance(visits, dict) else visits
    pitems = photos.get("items") if isinstance(photos, dict) else photos
    assert sum(1 for it in vitems if int(it.get("id", -1)) == int(xid)) == 1
    assert len([p for p in pitems if int(p.get("visit_id", -1)) == int(xid)]) == 1
    # cliente também não duplica
    citems = client.get("/clients").get("items") if False else None
    with xano_sync._client("test-token") as client:
        clients = client.get("/clients").get("items", [])
    assert sum(1 for c in clients if c.get("name") == "Empresa Xano") == 1


def test_recovery_pull_from_xano(xano_env, local_store):
    _cid, vid = _seed_visit(local_store)
    visit = storage.load_visits()[vid]
    xid = int(visit["xano_id"])

    recovered = xano_sync.fetch_visit(xid)
    assert recovered is not None
    local = xano_sync._remote_visit_to_local(recovered)
    assert str(local.get("xano_id")) == str(xid)
    assert local.get("technician") == "Técnico"
    assert local.get("worker", {}).get("name") == "João Silva"
    assert (local.get("equipment", {}).get("selected") or [])
    assert local.get("weather", {}).get("source") == "Manual"
    assert local.get("photos"), "fotos vinculadas devem ser recuperáveis"


def test_local_mode_without_xano(local_store, monkeypatch):
    monkeypatch.setenv("XANO_BASE_URL", "")
    monkeypatch.setattr(xano_sync, "_session_token", lambda: "")
    ok, cid, _ = storage.add_client("Empresa Local", "00", "R", "R", "1", "a@b.com")
    assert ok
    ok, vid, _ = storage.add_visit(cid, "Técnico", "2026-11-10")
    assert ok
    visit = storage.load_visits()[vid]
    assert not visit.get("xano_id")
    assert storage.load_clients()[cid].get("xano_id") in (None, "")
