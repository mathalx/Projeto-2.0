query "users" verb=GET {
  api_group = "ACNnorte"
  description = "Lista usuários. Apenas administradores."
  auth = "user"

  input {
    text search?
    enum status? {
      values = ["ativo", "bloqueado"]
    }
    enum role? {
      values = ["administrador", "usuario"]
    }
    int page?=1
    int per_page?=50
  }

  stack {
    db.get users {
      field_name = "id"
      field_value = $auth.id
    } as $current_user

    precondition ($current_user != null && $current_user.status == "ativo" && $current_user.role == "administrador") {
      error_type = "accessdenied"
      error = "Apenas administradores podem listar usuários."
    }

    db.query users {
      where = ($input.search == null || $db.users.name ilike "%" ~ $input.search ~ "%" || $db.users.email ilike "%" ~ $input.search ~ "%") && ($input.status == null || $db.users.status == $input.status) && ($input.role == null || $db.users.role == $input.role)
      sort = {created_at: "desc"}
      return = {
        type: "list"
        paging: {
          page: $input.page
          per_page: $input.per_page
          totals: true
          metadata: true
        }
      }
      output = ["itemsReceived", "curPage", "nextPage", "prevPage", "offset", "itemsTotal", "pageTotal", "items.id", "items.created_at", "items.name", "items.email", "items.role", "items.status"]
    } as $users
  }

  response = $users
}
