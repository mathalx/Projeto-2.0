"""Gerenciamento de fotografias por visita (CHANGE 07).

Integra com ``src.views.photos_view`` e ``src.storage_manager`` sem duplicar
armazenamento ou navega??o. Fotografias permanecem associadas ? visita correta.
"""

from __future__ import annotations

import streamlit as st

from src.ui_components import PAGE_PHOTOS, PHOTOS_TAB_GALLERY, navigate_to


def build_photo_identification(horario: str, equipment_label: str) -> str:
    horario = str(horario or "").strip()
    equipment_label = str(equipment_label or "").strip()
    if horario and equipment_label:
        return f"{horario} ? {equipment_label}"
    return equipment_label or horario


def render_photographs_block(
    visit_id: str,
    visit: dict,
    *,
    key_prefix: str = "ve_photo",
    embed_gallery_hint: bool = True,
) -> dict:
    """Bloco auxiliar para o fluxo de visita com acesso integrado ? galeria."""
    st.markdown("#### Fotografias")
    st.caption(
        "Capture pelo celular ou selecione da galeria, visualize, edite identifica??o/legenda/observa??es, "
        "substitua ou exclua. Registre hor?rio e equipamento. Padr?o: `Hor?rio + identifica??o do equipamento`."
    )
    photos = visit.get("photos", []) if isinstance(visit, dict) else []
    st.markdown(f"**Fotografias nesta visita:** {len(photos)}")

    if embed_gallery_hint:
        st.info(
            "As fotografias s?o gerenciadas na tela **Fotografias** (galeria por visita, sem mistura entre visitas/empresas). "
            "Use o bot?o abaixo para abrir a galeria desta visita."
        )

    if st.button(
        "Avan?ar para fotografias ?",
        key=f"{key_prefix}_{visit_id}_go_photos",
        type="primary",
        width="stretch",
    ):
        st.session_state["active_visit_id"] = visit_id
        st.session_state["photo_active_visit_id"] = visit_id
        navigate_to(PAGE_PHOTOS, photos_tab=PHOTOS_TAB_GALLERY)

    return {"count": len(photos), "visit_id": visit_id}
