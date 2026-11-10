import html
from datetime import date

import streamlit as st

from src.form_template import (
    TECHNICAL_FORM_SECTIONS,
    UNANSWERED_LABEL,
    first_unanswered_section,
    section_completion,
    visit_completion,
)
from src.storage_manager import (
    add_visit,
    load_clients,
    load_visits,
    update_visit,
)
from src.ui_components import (
    PAGE_VISITS,
    VISITS_TAB_FILL,
    VISITS_TAB_LIST,
    VISITS_TAB_NEW,
    VISITS_TABS,
    navigate_to,
    record_sync,
    render_acnnorte_logo,
    render_empty_state,
    render_section_title,
    set_flash,
    status_badge,
)

SECTIONS = list(TECHNICAL_FORM_SECTIONS.items())
TOTAL_STEPS = len(SECTIONS) + 1  # 5 seções + etapa final


# ---------------------------------------------------------------------------
# Chaves de estado (mantêm o preenchimento ao navegar entre etapas)
# ---------------------------------------------------------------------------
def _draft_key(visit_id: str) -> str:
    return f"draft_{visit_id}"


def _step_key(visit_id: str) -> str:
    return f"form_step_{visit_id}"


def _field_key(visit_id: str, category: str, field_id: str) -> str:
    return f"form_{visit_id}_{category}_{field_id}"


def _obs_key(visit_id: str) -> str:
    return f"obs_{visit_id}"


def _conc_key(visit_id: str) -> str:
    return f"conc_{visit_id}"


def _status_key(visit_id: str) -> str:
    return f"status_{visit_id}"


def _select_visits_tab() -> str:
    if st.session_state.get("visits_tab") not in VISITS_TABS:
        st.session_state["visits_tab"] = VISITS_TAB_LIST
    return st.radio(
        "Seção de visitas",
        VISITS_TABS,
        key="visits_tab",
        horizontal=True,
        label_visibility="collapsed",
    )


# ---------------------------------------------------------------------------
# Rascunho e salvamento automático
# ---------------------------------------------------------------------------
def _build_draft(visit: dict) -> dict:
    forms = {}
    for cat_key in TECHNICAL_FORM_SECTIONS:
        forms[cat_key] = dict((visit.get("forms") or {}).get(cat_key, {}))
    status = visit.get("status", "Rascunho")
    if status not in ("Rascunho", "Em Andamento"):
        status = "Em Andamento"
    return {
        "forms": forms,
        "observations": visit.get("observations", ""),
        "conclusions": visit.get("conclusions", ""),
        "status": status,
    }


def _collect_widgets(visit_id: str, draft: dict) -> dict:
    """Copia para o rascunho todos os valores já presentes nos widgets."""
    for cat_key, cat_info in SECTIONS:
        for field in cat_info["fields"]:
            key = _field_key(visit_id, cat_key, field["id"])
            if key in st.session_state:
                value = st.session_state[key]
                if value == UNANSWERED_LABEL:
                    value = ""
                draft["forms"].setdefault(cat_key, {})[field["id"]] = value

    obs_key = _obs_key(visit_id)
    if obs_key in st.session_state:
        draft["observations"] = st.session_state[obs_key]
    conc_key = _conc_key(visit_id)
    if conc_key in st.session_state:
        draft["conclusions"] = st.session_state[conc_key]
    status_key = _status_key(visit_id)
    if status_key in st.session_state:
        draft["status"] = st.session_state[status_key]
    return draft


def _persist_draft(visit_id: str, draft: dict, status: str = None) -> bool:
    visits = load_visits()
    current = visits.get(visit_id, {})
    final_status = status or current.get("status", "Rascunho")
    success, _message = update_visit(
        visit_id,
        draft["forms"],
        draft["observations"],
        draft["conclusions"],
        final_status,
    )
    if success:
        record_sync()
    return success


def _autosave_field(visit_id: str, category: str, field_id: str):
    draft = st.session_state.get(_draft_key(visit_id))
    if draft is None:
        return
    value = st.session_state.get(_field_key(visit_id, category, field_id), "")
    if value == UNANSWERED_LABEL:
        value = ""
    draft["forms"].setdefault(category, {})[field_id] = value
    _collect_widgets(visit_id, draft)
    _persist_draft(visit_id, draft)


def _autosave_text(visit_id: str, field: str):
    draft = st.session_state.get(_draft_key(visit_id))
    if draft is None:
        return
    key = _obs_key(visit_id) if field == "observations" else _conc_key(visit_id)
    if key in st.session_state:
        draft[field] = st.session_state[key]
    _collect_widgets(visit_id, draft)
    _persist_draft(visit_id, draft)


def _autosave_status(visit_id: str):
    draft = st.session_state.get(_draft_key(visit_id))
    key = _status_key(visit_id)
    if draft is None or key not in st.session_state:
        return
    draft["status"] = st.session_state[key]
    _collect_widgets(visit_id, draft)
    _persist_draft(visit_id, draft)


def _open_visit_for_editing(visit: dict):
    visit_id = visit.get("id", "")
    st.session_state["active_visit_id"] = visit_id
    st.session_state[_step_key(visit_id)] = first_unanswered_section(visit.get("forms", {}))
    navigate_to(PAGE_VISITS, visits_tab=VISITS_TAB_FILL)


# ---------------------------------------------------------------------------
# Lista de visitas
# ---------------------------------------------------------------------------
def _render_visit_list(visits: dict):
    render_section_title(
        "Histórico e situação das visitas",
        "Pesquise por cliente, técnico ou código e continue de onde parou.",
        "📋",
    )

    if not visits:
        render_empty_state(
            "📋",
            "Nenhuma visita registrada",
            "Use a seção “Iniciar Visita” para começar a primeira visita técnica.",
        )
        return

    filter_col1, filter_col2 = st.columns([2, 1])
    with filter_col1:
        search = st.text_input(
            "Pesquisar visita",
            key="visits_search",
            placeholder="Nome do cliente, técnico ou código da visita...",
        ).strip().lower()
    with filter_col2:
        status_filter = st.selectbox(
            "Situação",
            ["Todas", "Rascunho", "Em Andamento", "Finalizada"],
            key="visits_status_filter",
        )

    filtered = []
    for v_id, visit in visits.items():
        status = visit.get("status", "Rascunho")
        if status_filter != "Todas" and status != status_filter:
            continue
        haystack = " ".join(
            [
                str(visit.get("client_name", "")),
                str(visit.get("technician", "")),
                str(visit.get("date", "")),
                str(v_id),
            ]
        ).lower()
        if search and search not in haystack:
            continue
        filtered.append((v_id, visit))

    st.caption(f"{len(filtered)} de {len(visits)} visita(s) exibida(s).")

    if not filtered:
        render_empty_state("🔍", "Nenhuma visita encontrada", "Ajuste a pesquisa ou o filtro de situação.")
        return

    filtered.sort(key=lambda item: item[1].get("date", ""), reverse=True)

    for v_id, visit in filtered:
        status = visit.get("status", "Rascunho")
        label = (
            f"🛡️ Visita #{v_id} — {visit.get('client_name', '—')} "
            f"({visit.get('date', '—')}) • {status}"
        )
        with st.expander(label):
            answered, total = visit_completion(visit.get("forms", {}))
            percent = (answered / total) if total else 0.0
            st.progress(percent, text=f"Checklist: {answered} de {total} campos respondidos")

            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"**Técnico:** {visit.get('technician', '—')}")
                st.markdown(f"**Data:** {visit.get('date', '—')}")
            with col2:
                st.markdown(f"**Fotografias:** {len(visit.get('photos', []))}")
                st.markdown(
                    f"**Situação:** {status_badge(status)}",
                    unsafe_allow_html=True,
                )

            st.markdown(f"**Observações:** {visit.get('observations') or 'Nenhuma observação registrada.'}")
            st.markdown(f"**Conclusões:** {visit.get('conclusions') or 'Nenhuma conclusão registrada.'}")

            if st.button(
                "✍️ Continuar preenchimento",
                key=f"edit_v_{v_id}",
                type="primary",
                width="stretch",
            ):
                _open_visit_for_editing({**visit, "id": v_id})


# ---------------------------------------------------------------------------
# Nova visita
# ---------------------------------------------------------------------------
def _render_new_visit(clients: dict):
    render_section_title(
        "Iniciar nova visita técnica",
        "Escolha a empresa e confirme o técnico responsável.",
        "➕",
    )

    if not clients:
        render_empty_state(
            "🏢",
            "Cadastre um cliente primeiro",
            "É necessário ter pelo menos uma empresa cadastrada para iniciar uma visita.",
        )
        return

    with st.form("new_visit_form"):
        client_options = {
            f"{c.get('name', '—')} — {c.get('cnpj', '—')}": c_id
            for c_id, c in clients.items()
        }
        selected_client_label = st.selectbox("Empresa cliente *", list(client_options.keys()))
        technician_name = st.text_input(
            "Técnico responsável *",
            value=st.session_state.get("username", "Eng. Técnico"),
        )
        visit_date = st.date_input("Data da visita *", value=date.today())

        submitted = st.form_submit_button("Iniciar visita", type="primary", width="stretch")
        if submitted:
            if not technician_name.strip():
                st.error("Informe o nome do técnico responsável para iniciar a visita.")
            else:
                with st.spinner("Criando visita..."):
                    success, visit_id, message = add_visit(
                        client_options[selected_client_label],
                        technician_name.strip(),
                        str(visit_date),
                        status="Em Andamento",
                    )
                if success:
                    st.session_state["active_visit_id"] = visit_id
                    st.session_state[_step_key(visit_id)] = 0
                    record_sync()
                    set_flash("Visita iniciada com sucesso! Preencha o checklist abaixo.")
                    navigate_to(PAGE_VISITS, visits_tab=VISITS_TAB_FILL)
                else:
                    st.error("Não foi possível iniciar a visita. Verifique os dados e tente novamente.")


# ---------------------------------------------------------------------------
# Preenchimento em etapas
# ---------------------------------------------------------------------------
def _render_field(visit_id: str, cat_key: str, field: dict, answers: dict):
    required = field.get("type") == "select"
    label = field["label"] + (" *" if required else "")
    key = _field_key(visit_id, cat_key, field["id"])
    current_value = answers.get(field["id"], "")

    if field["type"] == "select":
        options = list(field.get("options", []))
        options = [UNANSWERED_LABEL] + options
        if key not in st.session_state:
            index = options.index(current_value) if current_value in options else 0
            st.selectbox(
                label,
                options,
                index=index,
                key=key,
                on_change=_autosave_field,
                args=(visit_id, cat_key, field["id"]),
            )
        else:
            st.selectbox(
                label,
                options,
                key=key,
                on_change=_autosave_field,
                args=(visit_id, cat_key, field["id"]),
            )
    else:
        if key not in st.session_state:
            st.text_area(
                label,
                value=str(current_value or ""),
                key=key,
                on_change=_autosave_field,
                args=(visit_id, cat_key, field["id"]),
            )
        else:
            st.text_area(
                label,
                key=key,
                on_change=_autosave_field,
                args=(visit_id, cat_key, field["id"]),
            )


def _render_progress(visit_id: str, draft: dict, step: int):
    answered, total = visit_completion(draft["forms"])
    percent = (answered / total) if total else 0.0
    st.progress(percent, text=f"Checklist: {answered} de {total} campos obrigatórios respondidos")
    st.caption(
        f"Etapa {step + 1} de {TOTAL_STEPS} — as respostas são salvas automaticamente."
    )


def _validate_required(forms: dict):
    pending = []
    for cat_key, cat_info in SECTIONS:
        answered, total = section_completion(cat_key, forms.get(cat_key, {}))
        if answered < total:
            pending.append((cat_info["title"], total - answered))
    return pending


def _render_final_step(visit_id: str, visit: dict, draft: dict):
    render_section_title(
        "Observações e conclusão da visita",
        "Registre os pontos relevantes e finalize quando o checklist estiver completo.",
        "📝",
    )

    obs_key = _obs_key(visit_id)
    if obs_key not in st.session_state:
        st.text_area(
            "Observações gerais da visita",
            value=draft.get("observations", ""),
            key=obs_key,
            on_change=_autosave_text,
            args=(visit_id, "observations"),
        )
    else:
        st.text_area(
            "Observações gerais da visita",
            key=obs_key,
            on_change=_autosave_text,
            args=(visit_id, "observations"),
        )

    conc_key = _conc_key(visit_id)
    if conc_key not in st.session_state:
        st.text_area(
            "Conclusões e recomendações de segurança",
            value=draft.get("conclusions", ""),
            key=conc_key,
            on_change=_autosave_text,
            args=(visit_id, "conclusions"),
        )
    else:
        st.text_area(
            "Conclusões e recomendações de segurança",
            key=conc_key,
            on_change=_autosave_text,
            args=(visit_id, "conclusions"),
        )

    current_status = visit.get("status", "Rascunho")
    if current_status == "Finalizada":
        st.success("Esta visita está finalizada e pronta para geração de relatório.")
    else:
        status_key = _status_key(visit_id)
        options = ["Rascunho", "Em Andamento"]
        if status_key not in st.session_state:
            default = draft.get("status", "Em Andamento")
            index = options.index(default) if default in options else 1
            st.selectbox(
                "Situação da visita",
                options,
                index=index,
                key=status_key,
                on_change=_autosave_status,
                args=(visit_id,),
            )
        else:
            st.selectbox(
                "Situação da visita",
                options,
                key=status_key,
                on_change=_autosave_status,
                args=(visit_id,),
            )

    st.markdown("#### Resumo por seção")
    for cat_key, cat_info in SECTIONS:
        answered, total = section_completion(cat_key, draft["forms"].get(cat_key, {}))
        if answered == total:
            st.markdown(f"✅ {cat_info['title']} — completo")
        else:
            st.markdown(f"⚠️ {cat_info['title']} — {answered}/{total} respondidos")


def _render_fill_tab(visits: dict):
    render_section_title(
        "Preenchimento e edição de visita",
        "Responda uma etapa por vez. Você pode voltar sem perder as respostas.",
        "✍️",
    )

    if not visits:
        render_empty_state("✍️", "Nenhuma visita para preencher", "Inicie uma nova visita primeiro.")
        return

    visit_options = {
        f"Visita #{v_id} — {v.get('client_name', '—')} ({v.get('date', '—')})": v_id
        for v_id, v in visits.items()
    }
    labels = list(visit_options.keys())
    ids = list(visit_options.values())

    desired_id = st.session_state.get("active_visit_id")
    already_synced = st.session_state.get("visit_select_active_synced")
    if desired_id in ids and desired_id != already_synced:
        st.session_state["visit_select"] = labels[ids.index(desired_id)]

    selected_label = st.selectbox("Selecione a visita", labels, key="visit_select")
    selected_id = visit_options[selected_label]
    st.session_state["active_visit_id"] = selected_id
    st.session_state["visit_select_active_synced"] = selected_id
    visit = visits[selected_id]

    if st.session_state.get("draft_loaded_vid") != selected_id:
        st.session_state["draft_loaded_vid"] = selected_id
        st.session_state[_draft_key(selected_id)] = _build_draft(visit)
        st.session_state.setdefault(_step_key(selected_id), first_unanswered_section(visit.get("forms", {})))

    draft = st.session_state[_draft_key(selected_id)]
    _collect_widgets(selected_id, draft)

    step = int(st.session_state.get(_step_key(selected_id), 0))
    step = max(0, min(step, TOTAL_STEPS - 1))
    st.session_state[_step_key(selected_id)] = step

    st.markdown(
        f"**Empresa:** {visit.get('client_name', '—')} &nbsp;|&nbsp; "
        f"**Técnico:** {visit.get('technician', '—')} &nbsp;|&nbsp; "
        f"**Data:** {visit.get('date', '—')} &nbsp;|&nbsp; "
        f"**Situação:** {status_badge(visit.get('status', 'Rascunho'))}",
        unsafe_allow_html=True,
    )
    _render_progress(selected_id, draft, step)
    st.markdown("---")

    if step < len(SECTIONS):
        cat_key, cat_info = SECTIONS[step]
        st.markdown(f"#### {cat_info['title']}")
        answers = draft["forms"].get(cat_key, {})
        for field in cat_info["fields"]:
            _render_field(selected_id, cat_key, field, answers)
    else:
        _render_final_step(selected_id, visit, draft)

    st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)

    # --------------------------------------------------------------
    # Navegação entre etapas
    # --------------------------------------------------------------
    nav_left, nav_center, nav_right = st.columns([1, 1.4, 1])

    with nav_left:
        if step > 0 and st.button("⬅️ Voltar", key=f"prev_{selected_id}", width="stretch"):
            _collect_widgets(selected_id, draft)
            _persist_draft(selected_id, draft)
            st.session_state[_step_key(selected_id)] = step - 1
            st.rerun()

    with nav_center:
        if st.button("💾 Salvar agora", key=f"save_{selected_id}", width="stretch"):
            _collect_widgets(selected_id, draft)
            with st.spinner("Salvando..."):
                if _persist_draft(selected_id, draft):
                    st.success("Alterações salvas com sucesso.")
                else:
                    st.error("Não foi possível salvar. Tente novamente.")

    with nav_right:
        if step < TOTAL_STEPS - 1:
            if st.button("Avançar ➡️", key=f"next_{selected_id}", type="primary", width="stretch"):
                _collect_widgets(selected_id, draft)
                _persist_draft(selected_id, draft)
                st.session_state[_step_key(selected_id)] = step + 1
                st.rerun()

    # --------------------------------------------------------------
    # Finalização com confirmação
    # --------------------------------------------------------------
    pending_key = "finalize_pending"
    if step == TOTAL_STEPS - 1 and visit.get("status") != "Finalizada":
        if st.button(
            "✅ Finalizar visita",
            key=f"finalize_{selected_id}",
            type="primary",
            width="stretch",
        ):
            _collect_widgets(selected_id, draft)
            pending = _validate_required(draft["forms"])
            if pending:
                detail = "; ".join(f"{title}: {count} pendente(s)" for title, count in pending)
                st.error(f"Responda os campos obrigatórios antes de finalizar. {detail}")
            else:
                st.session_state[pending_key] = selected_id

    if st.session_state.get(pending_key) == selected_id:
        st.warning(
            "Confirmar a finalização desta visita? Depois de finalizada, ela ficará pronta para o relatório PDF."
        )
        confirm_col, cancel_col = st.columns(2)
        with confirm_col:
            if st.button("Sim, finalizar", key=f"confirm_finalize_{selected_id}", type="primary", width="stretch"):
                _collect_widgets(selected_id, draft)
                with st.spinner("Finalizando visita..."):
                    success = _persist_draft(selected_id, draft, status="Finalizada")
                st.session_state.pop(pending_key, None)
                if success:
                    st.session_state[f"draft_loaded_vid"] = None
                    set_flash("Visita finalizada com sucesso! Pronta para geração de relatório PDF.")
                    st.rerun()
                else:
                    st.error("Não foi possível finalizar a visita. Tente novamente.")
        with cancel_col:
            if st.button("Cancelar", key=f"cancel_finalize_{selected_id}", width="stretch"):
                st.session_state.pop(pending_key, None)
                st.rerun()


# ---------------------------------------------------------------------------
# Entrada da página
# ---------------------------------------------------------------------------
def render_visits_view():
    render_acnnorte_logo(size="medium", subtitle="Gerenciamento de Visitas e Formulários Técnicos")

    clients = load_clients()
    visits = load_visits()
    selected_tab = _select_visits_tab()

    if selected_tab == VISITS_TAB_NEW:
        _render_new_visit(clients)
    elif selected_tab == VISITS_TAB_FILL:
        _render_fill_tab(visits)
    else:
        _render_visit_list(visits)
