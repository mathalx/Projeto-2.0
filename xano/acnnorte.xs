table users {
  auth = true

  schema {
    int id
    timestamp created_at?=now
    text name filters=trim
    email email filters=trim|lower
    password password filters=min:6
    enum role?=usuario {
      values = ["administrador", "usuario"]
    }
    enum status?=ativo {
      values = ["ativo", "bloqueado"]
    }
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {type: "btree", field: [{name: "created_at", op: "desc"}]}
    {type: "btree|unique", field: [{name: "email", op: "asc"}]}
    {type: "btree", field: [{name: "role"}]}
    {type: "btree", field: [{name: "status"}]}
  ]
}
---
table clients {
  auth = false

  schema {
    int id
    timestamp created_at?=now
    text name filters=trim
    text cnpj filters=trim
    text responsible_person? filters=trim
    text phone? filters=trim
    email email? filters=trim|lower
    text address? filters=trim
    bool active?=true
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {type: "btree", field: [{name: "created_at", op: "desc"}]}
    {type: "btree|unique", field: [{name: "cnpj", op: "asc"}]}
    {type: "btree", field: [{name: "name", op: "asc"}]}
    {type: "btree", field: [{name: "active"}]}
  ]
}
---
table visits {
  auth = false

  schema {
    int id
    timestamp created_at?=now
    timestamp updated_at?=now
    int client_id {
      table = "clients"
    }
    int user_id {
      table = "users"
    }
    enum status?=rascunho {
      values = ["rascunho", "finalizado"]
    }
    date visit_date
    int current_step?=1
    json checklist_epi?
    json checklist_condicoes_gerais?
    json checklist_incendio?
    json checklist_maquinas?
    json checklist_documentacao?
    text general_observations?
    attachment pdf_report_url?
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {type: "btree", field: [{name: "created_at", op: "desc"}]}
    {type: "btree", field: [{name: "updated_at", op: "desc"}]}
    {type: "btree", field: [{name: "client_id"}]}
    {type: "btree", field: [{name: "user_id"}]}
    {type: "btree", field: [{name: "status"}]}
    {type: "btree", field: [{name: "visit_date", op: "desc"}]}
  ]
}
---
table photos {
  auth = false

  schema {
    int id
    timestamp created_at?=now
    int visit_id {
      table = "visits"
    }
    image image
    text caption? filters=trim
    int display_order?=0
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {type: "btree", field: [{name: "created_at", op: "desc"}]}
    {type: "btree", field: [{name: "visit_id"}]}
    {type: "btree", field: [{name: "display_order", op: "asc"}]}
  ]
}
---
api_group ACNnorte {
  description = "API da aplicação ACNnorte — gestão de visitas técnicas de segurança do trabalho."
  canonical = "acnnorte"
  tags = ["acnnorte", "visitas", "seguranca-do-trabalho"]
}
---
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
---
query "auth/me" verb=GET {
  api_group = "ACNnorte"
  description = "Retorna o perfil do usuário autenticado."
  auth = "user"

  input {
  }

  stack {
    db.get users {
      field_name = "id"
      field_value = $auth.id
      output = ["id", "created_at", "name", "email", "role", "status"]
    } as $user

    precondition ($user != null) {
      error_type = "notfound"
      error = "Usuário não encontrado."
    }
  }

  response = $user
}
---
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
---
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
---
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
---
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
---
query "clients" verb=GET {
  api_group = "ACNnorte"
  description = "Lista clientes ativos com filtros opcionais por nome ou CNPJ."
  auth = "user"

  input {
    text name?
    text cnpj?
    int page?=1
    int per_page?=50
  }

  stack {
    db.query clients {
      where = $db.clients.active == true && ($input.name == null || $db.clients.name ilike "%" ~ $input.name ~ "%") && ($input.cnpj == null || $db.clients.cnpj ilike "%" ~ $input.cnpj ~ "%")
      sort = {name: "asc"}
      return = {
        type: "list"
        paging: {
          page: $input.page
          per_page: $input.per_page
          totals: true
          metadata: true
        }
      }
    } as $clients
  }

  response = $clients
}
---
query "clients" verb=POST {
  api_group = "ACNnorte"
  description = "Cadastra um cliente. Valida se o CNPJ já existe."
  auth = "user"

  input {
    text name filters=trim
    text cnpj filters=trim
    text responsible_person? filters=trim
    text phone? filters=trim
    email email? filters=trim|lower
    text address? filters=trim
  }

  stack {
    db.get clients {
      field_name = "cnpj"
      field_value = $input.cnpj
    } as $existing_client

    precondition ($existing_client == null) {
      error_type = "standard"
      error = "Já existe um cliente cadastrado com este CNPJ."
    }

    db.add clients {
      data = {
        name: $input.name
        cnpj: $input.cnpj
        responsible_person: $input.responsible_person
        phone: $input.phone
        email: $input.email
        address: $input.address
        active: true
      }
    } as $client
  }

  response = $client
}
---
query "clients/{id}" verb=GET {
  api_group = "ACNnorte"
  description = "Retorna os dados do cliente e o histórico de visitas vinculadas."
  auth = "user"

  input {
    int id
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

    db.query visits {
      where = $db.visits.client_id == $input.id
      sort = {visit_date: "desc"}
      return = {type: "list"}
    } as $visits
  }

  response = {
    client: $client
    visits: $visits
  }
}
---
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
---
query "clients/{id}" verb=DELETE {
  api_group = "ACNnorte"
  description = "Desativa um cliente (active = false), preservando as visitas."
  auth = "user"

  input {
    int id
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

    db.patch clients {
      field_name = "id"
      field_value = $input.id
      data = {active: false}
    } as $updated_client
  }

  response = {
    message: "Cliente desativado com sucesso."
    id: $updated_client.id
    active: $updated_client.active
  }
}
---
query "visits" verb=GET {
  api_group = "ACNnorte"
  description = "Lista visitas com filtros opcionais por status, cliente, inspetor e intervalo de datas."
  auth = "user"

  input {
    enum status? {
      values = ["rascunho", "finalizado"]
    }
    int client_id?
    int user_id?
    date date_from?
    date date_to?
    int page?=1
    int per_page?=50
  }

  stack {
    db.query visits {
      where = ($input.status == null || $db.visits.status == $input.status) && ($input.client_id == null || $db.visits.client_id == $input.client_id) && ($input.user_id == null || $db.visits.user_id == $input.user_id) && ($input.date_from == null || $db.visits.visit_date >= $input.date_from) && ($input.date_to == null || $db.visits.visit_date <= $input.date_to)
      sort = {updated_at: "desc"}
      return = {
        type: "list"
        paging: {
          page: $input.page
          per_page: $input.per_page
          totals: true
          metadata: true
        }
      }
    } as $visits
  }

  response = $visits
}
---
query "visits/{id}" verb=GET {
  api_group = "ACNnorte"
  description = "Retorna uma visita com cliente, inspetor e fotografias."
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

    db.get clients {
      field_name = "id"
      field_value = $visit.client_id
    } as $client

    db.get users {
      field_name = "id"
      field_value = $visit.user_id
      output = ["id", "name", "email", "role", "status"]
    } as $inspector

    db.query photos {
      where = $db.photos.visit_id == $visit.id
      sort = {display_order: "asc"}
      return = {type: "list"}
    } as $photos
  }

  response = {
    visit: $visit
    client: $client
    inspector: $inspector
    photos: $photos
  }
}
---
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
---
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
---
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
---
query "photos" verb=GET {
  api_group = "ACNnorte"
  description = "Lista as fotografias de uma visita."
  auth = "user"

  input {
    int visit_id
    int page?=1
    int per_page?=100
  }

  stack {
    db.query photos {
      where = $db.photos.visit_id == $input.visit_id
      sort = {display_order: "asc"}
      return = {
        type: "list"
        paging: {
          page: $input.page
          per_page: $input.per_page
          totals: true
          metadata: true
        }
      }
    } as $photos
  }

  response = $photos
}
---
query "photos" verb=POST {
  api_group = "ACNnorte"
  description = "Faz upload de uma imagem vinculada a uma visita."
  auth = "user"

  input {
    int visit_id
    image image
    text caption?
    int display_order?=0
  }

  stack {
    db.get visits {
      field_name = "id"
      field_value = $input.visit_id
    } as $visit

    precondition ($visit != null) {
      error_type = "notfound"
      error = "Visita não encontrada."
    }

    storage.create_image {
      access = "public"
      value = $input.image
      filename = $input.image.name
    } as $image_metadata

    db.add photos {
      data = {
        visit_id: $input.visit_id
        image: $image_metadata
        caption: $input.caption
        display_order: $input.display_order
      }
    } as $photo

    db.patch visits {
      field_name = "id"
      field_value = $input.visit_id
      data = {updated_at: "now"}
    } as $updated_visit
  }

  response = $photo
}
---
query "photos/{id}" verb=PATCH {
  api_group = "ACNnorte"
  description = "Atualiza a legenda, a ordem ou substitui o arquivo de uma fotografia."
  auth = "user"

  input {
    int id
    text caption?
    int display_order?
    image image?
  }

  stack {
    db.get photos {
      field_name = "id"
      field_value = $input.id
    } as $photo

    precondition ($photo != null) {
      error_type = "notfound"
      error = "Fotografia não encontrada."
    }

    var $changes {
      value = {}
    }

    var $old_image_path {
      value = $photo.image.path
    }

    conditional {
      if ($input.caption != null) {
        var.update $changes {
          value = $changes|set:"caption":$input.caption
        }
      }
    }

    conditional {
      if ($input.display_order != null) {
        var.update $changes {
          value = $changes|set:"display_order":$input.display_order
        }
      }
    }

    conditional {
      if ($input.image != null) {
        storage.create_image {
          access = "public"
          value = $input.image
          filename = $input.image.name
        } as $new_image_metadata

        var.update $changes {
          value = $changes|set:"image":$new_image_metadata
        }
      }
    }

    db.patch photos {
      field_name = "id"
      field_value = $input.id
      data = $changes
    } as $updated_photo

    conditional {
      if ($input.image != null && $old_image_path != null) {
        try_catch {
          try {
            storage.delete_file {
              pathname = $old_image_path
            }
          }
          catch {
            debug.log {
              value = "Não foi possível remover a imagem antiga do storage."
            }
          }
        }
      }
    }
  }

  response = $updated_photo
}
---
query "photos/{id}" verb=DELETE {
  api_group = "ACNnorte"
  description = "Remove a fotografia do banco e do storage, preservando a visita."
  auth = "user"

  input {
    int id
  }

  stack {
    db.get photos {
      field_name = "id"
      field_value = $input.id
    } as $photo

    precondition ($photo != null) {
      error_type = "notfound"
      error = "Fotografia não encontrada."
    }

    var $image_path {
      value = $photo.image.path
    }

    db.del photos {
      field_name = "id"
      field_value = $input.id
    }

    conditional {
      if ($image_path != null) {
        try_catch {
          try {
            storage.delete_file {
              pathname = $image_path
            }
          }
          catch {
            debug.log {
              value = "Não foi possível remover a imagem do storage."
            }
          }
        }
      }
    }
  }

  response = {
    message: "Fotografia removida com sucesso."
    id: $input.id
  }
}
