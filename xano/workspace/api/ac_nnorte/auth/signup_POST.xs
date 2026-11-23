query "auth/signup" verb=POST {
  api_group = "ACNnorte"
  description = "Cria um novo usuário. Apenas administradores podem chamar este endpoint."
  auth = "user"

  input {
    text name filters=trim
    email email filters=trim|lower
    text password filters=min:6
    enum role?=usuario {
      values = ["administrador", "usuario"]
    }
  }

  stack {
    db.get users {
      field_name = "id"
      field_value = $auth.id
    } as $current_user

    precondition ($current_user != null && $current_user.status == "ativo" && $current_user.role == "administrador") {
      error_type = "accessdenied"
      error = "Apenas administradores podem cadastrar usuários."
    }

    db.get users {
      field_name = "email"
      field_value = $input.email
    } as $existing_user

    precondition ($existing_user == null) {
      error_type = "standard"
      error = "Já existe um usuário com este e-mail."
    }

    db.add users {
      data = {
        name: $input.name
        email: $input.email
        password: $input.password
        role: $input.role
        status: "ativo"
      }
    } as $new_user
  }

  response = {
    id: $new_user.id
    created_at: $new_user.created_at
    name: $new_user.name
    email: $new_user.email
    role: $new_user.role
    status: $new_user.status
  }
}
