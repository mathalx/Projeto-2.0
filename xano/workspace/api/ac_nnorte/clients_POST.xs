query "clients" verb=POST {
  api_group = "ACNnorte"
  description = "Cadastra um cliente. Valida se o CNPJ já existe."
  auth = "user"

  input {
    text name filters=trim
    text cnpj filters=trim
    text responsible_person? filters=trim
    text phone? filters=trim
    email email? filters=trim|lower
    text address? filters=trim
  }

  stack {
    db.get clients {
      field_name = "cnpj"
      field_value = $input.cnpj
    } as $existing_client

    precondition ($existing_client == null) {
      error_type = "standard"
      error = "Já existe um cliente cadastrado com este CNPJ."
    }

    db.add clients {
      data = {
        name: $input.name
        cnpj: $input.cnpj
        responsible_person: $input.responsible_person
        phone: $input.phone
        email: $input.email
        address: $input.address
        active: true
      }
    } as $client
  }

  response = $client
}
