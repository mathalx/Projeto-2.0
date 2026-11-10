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
