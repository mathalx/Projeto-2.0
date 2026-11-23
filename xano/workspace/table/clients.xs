table clients {
  auth = false

  schema {
    int id
    timestamp created_at?=now
    text name filters=trim
    text cnpj filters=trim
    text responsible_person? filters=trim
    text phone? filters=trim
    email email? filters=trim|lower
    text address? filters=trim
    bool active?=true
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {type: "btree", field: [{name: "created_at", op: "desc"}]}
    {type: "btree|unique", field: [{name: "cnpj", op: "asc"}]}
    {type: "btree", field: [{name: "name", op: "asc"}]}
    {type: "btree", field: [{name: "active"}]}
  ]
}
