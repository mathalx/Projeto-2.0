query "visits/{id}/finalize" verb=POST {
  api_group = "ACNnorte"
  description = "Valida os campos obrigatórios e altera o status para finalizado."
  auth = "user"

  input {
    int id
  }

  stack {
    db.get visits {
      field_name = "id"
      field_value = $input.id
    } as $visit

    precondition ($visit != null) {
      error_type = "notfound"
      error = "Visita não encontrada."
    }

    precondition ($visit.status == "rascunho") {
      error_type = "standard"
      error = "Esta visita já foi finalizada."
    }

    precondition ($visit.client_id != null && $visit.user_id != null && $visit.visit_date != null) {
      error_type = "standard"
      error = "Preencha cliente, inspetor e data da visita antes de finalizar."
    }

    precondition ($visit.checklist_epi != null && ($visit.checklist_epi|is_empty) == false) {
      error_type = "standard"
      error = "O checklist de EPI precisa estar preenchido antes de finalizar."
    }

    precondition ($visit.checklist_condicoes_gerais != null && ($visit.checklist_condicoes_gerais|is_empty) == false) {
      error_type = "standard"
      error = "O checklist de condições gerais precisa estar preenchido antes de finalizar."
    }

    precondition ($visit.checklist_incendio != null && ($visit.checklist_incendio|is_empty) == false) {
      error_type = "standard"
      error = "O checklist de incêndio precisa estar preenchido antes de finalizar."
    }

    precondition ($visit.checklist_maquinas != null && ($visit.checklist_maquinas|is_empty) == false) {
      error_type = "standard"
      error = "O checklist de máquinas precisa estar preenchido antes de finalizar."
    }

    precondition ($visit.checklist_documentacao != null && ($visit.checklist_documentacao|is_empty) == false) {
      error_type = "standard"
      error = "O checklist de documentação precisa estar preenchido antes de finalizar."
    }

    db.patch visits {
      field_name = "id"
      field_value = $input.id
      data = {
        status: "finalizado"
        current_step: 6
        updated_at: "now"
      }
    } as $finalized_visit
  }

  response = {
    message: "Visita finalizada com sucesso."
    visit: $finalized_visit
  }
}
