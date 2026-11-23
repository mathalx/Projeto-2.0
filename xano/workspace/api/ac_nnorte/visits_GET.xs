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
