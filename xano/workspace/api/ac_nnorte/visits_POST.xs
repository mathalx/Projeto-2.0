query "visits" verb=POST {
  api_group = "ACNnorte"
  description = "Inicia um novo rascunho de visita técnica."
  auth = "user"

  input {
    int client_id
    date visit_date
    int user_id?
  }

  stack {
    db.get clients {
      field_name = "id"
      field_value = $input.client_id
    } as $client

    precondition ($client != null && $client.active == true) {
      error_type = "notfound"
      error = "Cliente não encontrado ou inativo."
    }

    conditional {
      if ($input.user_id != null) {
        db.get users {
          field_name = "id"
          field_value = $input.user_id
          output = ["id", "status"]
        } as $inspector_user

        precondition ($inspector_user != null && $inspector_user.status == "ativo") {
          error_type = "standard"
          error = "Inspetor não encontrado ou bloqueado."
        }
      }
    }

    var $assigned_user {
      value = $auth.id
    }

    conditional {
      if ($input.user_id != null) {
        var.update $assigned_user {
          value = $input.user_id
        }
      }
    }

    db.add visits {
      data = {
        client_id: $input.client_id
        user_id: $assigned_user
        status: "rascunho"
        visit_date: $input.visit_date
        current_step: 1
        checklist_epi: {}
        checklist_condicoes_gerais: {}
        checklist_incendio: {}
        checklist_maquinas: {}
        checklist_documentacao: {}
        general_observations: ""
        updated_at: "now"
      }
    } as $visit
  }

  response = $visit
}
