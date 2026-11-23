table users {
  auth = true

  schema {
    int id
    timestamp created_at?=now
    text name filters=trim
    email email filters=trim|lower
    password password filters=min:6
    enum role?=usuario {
      values = ["administrador", "usuario"]
    }
    enum status?=ativo {
      values = ["ativo", "bloqueado"]
    }
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {type: "btree", field: [{name: "created_at", op: "desc"}]}
    {type: "btree|unique", field: [{name: "email", op: "asc"}]}
    {type: "btree", field: [{name: "role"}]}
    {type: "btree", field: [{name: "status"}]}
  ]
}
