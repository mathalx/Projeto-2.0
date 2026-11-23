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
