query "users/{id}/status" verb=PATCH {
  api_group = "ACNnorte"
  description = "Ativa ou bloqueia um usuário. Apenas administradores."
  auth = "user"

  input {
    int id
    enum status {
      values = ["ativo", "bloqueado"]
    }
  }

  stack {
    db.get users {
      field_name = "id"
      field_value = $auth.id
    } as $current_user

    precondition ($current_user != null && $current_user.status == "ativo" && $current_user.role == "administrador") {
      error_type = "accessdenied"
      error = "Apenas administradores podem alterar o status de usuários."
    }

    db.get users {
      field_name = "id"
      field_value = $input.id
    } as $target_user

    precondition ($target_user != null) {
      error_type = "notfound"
      error = "Usuário não encontrado."
    }

    precondition ($input.id != $auth.id || $input.status == "ativo") {
      error_type = "standard"
      error = "Não é permitido bloquear o próprio usuário."
    }

    db.patch users {
      field_name = "id"
      field_value = $input.id
      data = {status: $input.status}
    } as $updated_user
  }

  response = {
    id: $updated_user.id
    name: $updated_user.name
    email: $updated_user.email
    role: $updated_user.role
    status: $updated_user.status
  }
}
