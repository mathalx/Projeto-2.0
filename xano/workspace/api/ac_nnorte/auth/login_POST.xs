query "auth/login" verb=POST {
  api_group = "ACNnorte"
  description = "Autentica o usuário e retorna o authToken JWT + perfil."

  input {
    email email filters=trim|lower
    text password
  }

  stack {
    db.get users {
      field_name = "email"
      field_value = $input.email
      output = ["id", "created_at", "name", "email", "password", "role", "status"]
    } as $user

    precondition ($user != null) {
      error_type = "accessdenied"
      error = "Credenciais inválidas."
    }

    precondition ($user.status == "ativo") {
      error_type = "accessdenied"
      error = "Usuário bloqueado. Procure o administrador."
    }

    security.check_password {
      text_password = $input.password
      hash_password = $user.password
    } as $password_ok

    precondition ($password_ok) {
      error_type = "accessdenied"
      error = "Credenciais inválidas."
    }

    security.create_auth_token {
      table = "users"
      extras = {role: $user.role}
      expiration = 86400
      id = $user.id
    } as $authToken
  }

  response = {
    authToken: $authToken
    role: $user.role
    user: {
      id: $user.id
      created_at: $user.created_at
      name: $user.name
      email: $user.email
      role: $user.role
      status: $user.status
    }
  }
}
