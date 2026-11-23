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
