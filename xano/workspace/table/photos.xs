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
