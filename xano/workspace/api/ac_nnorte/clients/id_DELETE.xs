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
