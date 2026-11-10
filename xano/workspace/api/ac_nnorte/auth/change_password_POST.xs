query "auth/change-password" verb=POST {
  api_group = "ACNnorte"
  description = "Altera a senha do usuário autenticado."
  auth = "user"

  input {
    text current_password
    text new_password filters=min:6
  }

  stack {
    db.get users {
      field_name = "id"
      field_value = $auth.id
      output = ["id", "password"]
    } as $user

    precondition ($user != null) {
      error_type = "notfound"
      error = "Usuário não encontrado."
    }

    security.check_password {
      text_password = $input.current_password
      hash_password = $user.password
    } as $password_ok

    precondition ($password_ok) {
      error_type = "accessdenied"
      error = "Senha atual incorreta."
    }

    db.patch users {
      field_name = "id"
      field_value = $auth.id
      data = {password: $input.new_password}
    } as $updated_user
  }

  response = {
    message: "Senha alterada com sucesso."
  }
}
