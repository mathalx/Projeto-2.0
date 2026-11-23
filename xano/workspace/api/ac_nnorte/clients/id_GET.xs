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
