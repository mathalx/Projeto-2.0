query "clients/{id}" verb=PATCH {
  api_group = "ACNnorte"
  description = "Atualiza os dados cadastrais de um cliente."
  auth = "user"

  input {
    int id
    text name?
    text cnpj?
    text responsible_person?
    text phone?
    email email?
    text address?
    bool active?
  }

  stack {
    db.get clients {
      field_name = "id"
      field_value = $input.id
    } as $client

    precondition ($client != null) {
      error_type = "notfound"
      error = "Cliente não encontrado."
    }

    var $changes {
      value = {}
    }

    conditional {
      if ($input.name != null) {
        var.update $changes {
          value = $changes|set:"name":$input.name
        }
      }
    }

    conditional {
      if ($input.cnpj != null) {
        db.get clients {
          field_name = "cnpj"
          field_value = $input.cnpj
        } as $duplicate

        precondition ($duplicate == null || $duplicate.id == $input.id) {
          error_type = "standard"
          error = "Já existe um cliente cadastrado com este CNPJ."
        }

        var.update $changes {
          value = $changes|set:"cnpj":$input.cnpj
        }
      }
    }

    conditional {
      if ($input.responsible_person != null) {
        var.update $changes {
          value = $changes|set:"responsible_person":$input.responsible_person
        }
      }
    }

    conditional {
      if ($input.phone != null) {
        var.update $changes {
          value = $changes|set:"phone":$input.phone
        }
      }
    }

    conditional {
      if ($input.email != null) {
        var.update $changes {
          value = $changes|set:"email":$input.email
        }
      }
    }

    conditional {
      if ($input.address != null) {
        var.update $changes {
          value = $changes|set:"address":$input.address
        }
      }
    }

    conditional {
      if ($input.active != null) {
        var.update $changes {
          value = $changes|set:"active":$input.active
        }
      }
    }

    db.patch clients {
      field_name = "id"
      field_value = $input.id
      data = $changes
    } as $updated_client
  }

  response = $updated_client
}
