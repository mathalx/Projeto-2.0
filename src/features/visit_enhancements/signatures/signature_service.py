"""Serviço/bloco de assinaturas (CHANGE 04).

Reaproveita ``src.signature_pad`` e ``src.storage_manager``.
Não declara validade jurídica automática.
"""

from __future__ import annotations

import base64
import os
from functools import partial

import streamlit as st

from src.signature_pad import signature_data_url, signature_pad, signature_state_has_drawing
from src.storage_manager import (
    SIGNATURE_LABELS,
    SIGNATURE_ROLES,
    missing_signatures,
    save_visit_signature,
    visit_has_signature,
)
from src.ui_components import record_sync, set_flash


def _signatures_of(visit: dict) -> dict:
    signatures = visit.get("signatures") if isinstance(visit, dict) else None
    return signatures if isinstance(signatures, dict) else {}


def _saved_signature_data_url(signature: dict) -> str:
    path = signature.get("path") if isinstance(signature, dict) else None
    if not path or not os.path.exists(path):
        return ""
    try:
        with open(path, "rb") as file:
            encoded = base64.b64encode(file.read()).decode("ascii")
        return f"data:image/png;base64,{encoded}"
    except Exception:
        return ""


def validate_signatures_for_completion(visit: dict) -> list[str]:
    """Retorna rótulos das assinaturas pendentes (ambas obrigatórias para concluir)."""
    return missing_signatures(visit)


def render_signatures_block(
    visit_id: str,
    visit: dict,
    *,
    key_prefix: str = "ve_sig",
    read_only: bool = False,
    allow_draft_without_signatures: bool = True,
) -> dict:
    """Renderiza bloco com Responsável Técnico e Avaliador."""
    _ = allow_draft_without_signatures  # regra aplicada no fluxo de finalização
    signatures = _signatures_of(visit)

    st.markdown("#### Assinaturas")
    st.caption(
        "Responsável Técnico e Avaliador: informe nome e desenhe a assinatura (mouse ou toque). "
        "As duas assinaturas são obrigatórias para concluir a visita, mas rascunhos podem ser salvos sem elas. "
        "Registro eletrônico sem validade jurídica automática."
    )

    if read_only:
        for role in SIGNATURE_ROLES:
            label = SIGNATURE_LABELS[role]
            signature = signatures.get(role) if isinstance(signatures.get(role), dict) else {}
            name = str(signature.get("name") or "").strip() or "Não informado"
            st.markdown(f"**{label}:** {name}")
            if visit_has_signature(visit, role):
                st.caption(f"Assinado em {signature.get('signed_at') or 'data não informada'}.")
                st.image(signature.get("path"), width=320)
            else:
                st.caption("Não assinado.")
        return {"pending": validate_signatures_for_completion(visit), "read_only": True}

    def _on_name_change(vid: str, role: str, nkey: str):
        success, message = save_visit_signature(vid, role, name=st.session_state.get(nkey, ""))
        if success:
            record_sync()
        else:
            st.session_state[f"{key_prefix}_error"] = message

    def _on_draw_change(vid: str, role: str, pkey: str):
        state = st.session_state.get(pkey, {})
        success, message = save_visit_signature(vid, role, data_url=signature_data_url(state))
        if success:
            record_sync()
        else:
            st.session_state[f"{key_prefix}_error"] = message

    for role in SIGNATURE_ROLES:
        label = SIGNATURE_LABELS[role]
        signature = signatures.get(role) if isinstance(signatures.get(role), dict) else {}
        with st.container(border=True):
            st.markdown(f"**{label}**")
            name_key = f"{key_prefix}_{visit_id}_{role}_name"
            st.session_state.setdefault(name_key, signature.get("name", ""))
            st.text_input(
                f"Nome do {label} *",
                key=name_key,
                placeholder="Nome completo",
                on_change=_on_name_change,
                args=(visit_id, role, name_key),
            )
            pad_key = f"{key_prefix}_{visit_id}_{role}_pad"
            signature_pad(
                key=pad_key,
                image=_saved_signature_data_url(signature),
                on_change=partial(_on_draw_change, visit_id, role, pad_key),
            )
            if visit_has_signature(visit, role):
                st.caption(f"Assinatura registrada em {signature.get('signed_at') or 'data não informada'}.")
                with st.expander("Visualizar assinatura salva", expanded=False):
                    st.image(signature.get("path"), width=320)
            else:
                st.caption("Ainda não assinado.")

    if st.button("Salvar assinaturas", key=f"{key_prefix}_{visit_id}_save", width="stretch"):
        # persiste nomes e desenhos presentes no estado atual
        ok = True
        for role in SIGNATURE_ROLES:
            name_key = f"{key_prefix}_{visit_id}_{role}_name"
            pad_key = f"{key_prefix}_{visit_id}_{role}_pad"
            name = st.session_state.get(name_key) if name_key in st.session_state else None
            state = st.session_state.get(pad_key)
            if signature_state_has_drawing(state):
                ok = save_visit_signature(visit_id, role, data_url=signature_data_url(state), name=name)[0] and ok
            elif name is not None:
                ok = save_visit_signature(visit_id, role, name=name)[0] and ok
        if ok:
            record_sync()
            set_flash("Assinaturas salvas.")
            st.rerun()
        else:
            st.error("Não foi possível salvar as assinaturas.")

    error = st.session_state.pop(f"{key_prefix}_error", None)
    if error:
        st.error(error)

    return {"pending": validate_signatures_for_completion(visit), "read_only": False}
