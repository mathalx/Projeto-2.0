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
