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
