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
