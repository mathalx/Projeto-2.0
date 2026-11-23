query "visits/{id}" verb=PATCH {
  api_group = "ACNnorte"
  description = "Salva o progresso da visita e atualiza updated_at (autosave)."
  auth = "user"

  input {
    int id
    int current_step?
    json checklist_epi?
    json checklist_condicoes_gerais?
    json checklist_incendio?
    json checklist_maquinas?
    json checklist_documentacao?
    text general_observations?
    date visit_date?
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
      error = "Visita finalizada não pode ser editada."
    }

    precondition ($input.current_step == null || ($input.current_step >= 1 && $input.current_step <= 6)) {
      error_type = "standard"
      error = "A etapa atual deve estar entre 1 e 6."
    }

    var $changes {
      value = {updated_at: "now"}
    }

    conditional {
      if ($input.current_step != null) {
        var.update $changes {
          value = $changes|set:"current_step":$input.current_step
        }
      }
    }

    conditional {
      if ($input.checklist_epi != null) {
        var.update $changes {
          value = $changes|set:"checklist_epi":$input.checklist_epi
        }
      }
    }

    conditional {
      if ($input.checklist_condicoes_gerais != null) {
        var.update $changes {
          value = $changes|set:"checklist_condicoes_gerais":$input.checklist_condicoes_gerais
        }
      }
    }

    conditional {
      if ($input.checklist_incendio != null) {
        var.update $changes {
          value = $changes|set:"checklist_incendio":$input.checklist_incendio
        }
      }
    }

    conditional {
      if ($input.checklist_maquinas != null) {
        var.update $changes {
          value = $changes|set:"checklist_maquinas":$input.checklist_maquinas
        }
      }
    }

    conditional {
      if ($input.checklist_documentacao != null) {
        var.update $changes {
          value = $changes|set:"checklist_documentacao":$input.checklist_documentacao
        }
      }
    }

    conditional {
      if ($input.general_observations != null) {
        var.update $changes {
          value = $changes|set:"general_observations":$input.general_observations
        }
      }
    }

    conditional {
      if ($input.visit_date != null) {
        var.update $changes {
          value = $changes|set:"visit_date":$input.visit_date
        }
      }
    }

    db.patch visits {
      field_name = "id"
      field_value = $input.id
      data = $changes
    } as $updated_visit
  }

  response = $updated_visit
}
