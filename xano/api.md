# API — ACNnorte

Referência dos endpoints criados pelo `acnnorte.xs`. Todos os caminhos abaixo são
relativos à URL base do API group:

```text
https://SEU-INSTANCIA.xano.io/api:acnnorte
```

Exemplo: `GET /clients` → `https://SEU-INSTANCIA.xano.io/api:acnnorte/clients`.

## Autenticação

Exceto `POST /auth/login`, todos os endpoints exigem o token JWT no cabeçalho:

```http
Authorization: Bearer <authToken>
```

O token é retornado pelo login e expira em 24 horas. O Xano também aceita o token via
query string (`?authToken=...`), mas o cabeçalho é o formato recomendado.

## Formato de erro

O Xano retorna JSON com a mensagem definida no endpoint. Em geral:

| Situação | HTTP |
| --- | --- |
| Validação de negócio (`error_type = "standard"`) | `400` |
| Token ausente/inválido | `401` |
| Sem permissão (`accessdenied`) | `403` |
| Registro inexistente (`notfound`) | `404` |
| Erro inesperado | `500` |

```json
{
  "message": "Já existe um cliente cadastrado com este CNPJ."
}
```

## Paginação

Endpoints de lista aceitam `page` (padrão `1`) e `per_page` (padrão `50`; fotos usam
`100`). A resposta segue o formato de paginação do Xano:

```json
{
  "itemsReceived": 2,
  "curPage": 1,
  "nextPage": null,
  "prevPage": null,
  "offset": 0,
  "itemsTotal": 2,
  "pageTotal": 1,
  "items": [
    { "id": 1, "name": "Indústria Norte Ltda" },
    { "id": 2, "name": "Metalúrgica Sul Ltda" }
  ]
}
```

> Alguns endpoints podem retornar apenas o array `items` quando a paginação não é
> solicitada. Trate a resposta verificando se existe a chave `items`.

---

# Auth & Users

## POST `/auth/login`

Autentica por e-mail e senha. Não exige token.

**Body (JSON)**

```json
{
  "email": "admin@acnnorte.com.br",
  "password": "senha-forte"
}
```

**Resposta 200**

```json
{
  "authToken": "eyJhbGciOi...",
  "role": "administrador",
  "user": {
    "id": 1,
    "created_at": "2026-11-08T12:00:00+00:00",
    "name": "Ana Norte",
    "email": "admin@acnnorte.com.br",
    "role": "administrador",
    "status": "ativo"
  }
}
```

**Erros**

- `403` — credenciais inválidas ou usuário bloqueado.

## GET `/auth/me`

Retorna o perfil do usuário autenticado.

**Resposta 200**

```json
{
  "id": 1,
  "created_at": "2026-11-08T12:00:00+00:00",
  "name": "Ana Norte",
  "email": "admin@acnnorte.com.br",
  "role": "administrador",
  "status": "ativo"
}
```

## POST `/auth/signup`

Cria um usuário. **Somente administradores.**

**Body (JSON)**

```json
{
  "name": "João Inspetor",
  "email": "joao@acnnorte.com.br",
  "password": "senha-forte",
  "role": "usuario"
}
```

`role` é opcional; o padrão é `usuario`. `status` sempre inicia como `ativo`.

**Resposta 200**

```json
{
  "id": 2,
  "created_at": "2026-11-08T12:10:00+00:00",
  "name": "João Inspetor",
  "email": "joao@acnnorte.com.br",
  "role": "usuario",
  "status": "ativo"
}
```

**Erros**

- `400` — e-mail já cadastrado.
- `403` — solicitante não é administrador.

## POST `/auth/change-password`

Altera a senha do usuário autenticado.

**Body (JSON)**

```json
{
  "current_password": "senha-atual",
  "new_password": "nova-senha-forte"
}
```

**Resposta 200**

```json
{ "message": "Senha alterada com sucesso." }
```

**Erros**

- `403` — senha atual incorreta.
- `400` — nova senha com menos de 6 caracteres.

## GET `/users`

Lista usuários. **Somente administradores.**

**Query**

| Parâmetro | Tipo | Descrição |
| --- | --- | --- |
| `search` | texto | Busca parcial em `name` ou `email` |
| `status` | enum | `ativo` ou `bloqueado` |
| `role` | enum | `administrador` ou `usuario` |
| `page` | inteiro | Página (padrão 1) |
| `per_page` | inteiro | Itens por página (padrão 50) |

**Resposta 200** — lista paginada com `id`, `created_at`, `name`, `email`, `role`,
`status` (sem senha).

## PATCH `/users/{id}/status`

Ativa ou bloqueia um usuário. **Somente administradores.**

**Body (JSON)**

```json
{ "status": "bloqueado" }
```

**Resposta 200**

```json
{
  "id": 2,
  "name": "João Inspetor",
  "email": "joao@acnnorte.com.br",
  "role": "usuario",
  "status": "bloqueado"
}
```

**Erros**

- `400` — tentativa de bloquear o próprio usuário.
- `404` — usuário não encontrado.

---

# Clientes

## GET `/clients`

Lista clientes **ativos**, com filtros opcionais.

**Query**

| Parâmetro | Tipo | Descrição |
| --- | --- | --- |
| `name` | texto | Busca parcial, sem diferenciar maiúsculas/minúsculas |
| `cnpj` | texto | Busca parcial por CNPJ |
| `page` | inteiro | Página (padrão 1) |
| `per_page` | inteiro | Itens por página (padrão 50) |

**Resposta 200** — lista paginada de clientes com todos os campos.

## POST `/clients`

Cadastra um cliente. Valida duplicidade de CNPJ.

**Body (JSON)**

```json
{
  "name": "Indústria Norte Ltda",
  "cnpj": "00000000000100",
  "responsible_person": "Carlos Alberto",
  "phone": "(92) 99999-9999",
  "email": "contato@norte.com.br",
  "address": "Av. Industrial, 1000 — Manaus/AM"
}
```

`name` e `cnpj` são obrigatórios; os demais campos são opcionais.

**Resposta 200**

```json
{
  "id": 1,
  "created_at": "2026-11-08T12:20:00+00:00",
  "name": "Indústria Norte Ltda",
  "cnpj": "00000000000100",
  "responsible_person": "Carlos Alberto",
  "phone": "(92) 99999-9999",
  "email": "contato@norte.com.br",
  "address": "Av. Industrial, 1000 — Manaus/AM",
  "active": true
}
```

**Erros**

- `400` — CNPJ já cadastrado.

> O índice `unique` em `cnpj` também protege contra duplicidade em chamadas
> simultâneas. A verificação prévia garante uma mensagem amigável no caso comum.

## GET `/clients/{id}`

Retorna o cliente e o histórico de visitas vinculadas.

**Resposta 200**

```json
{
  "client": {
    "id": 1,
    "name": "Indústria Norte Ltda",
    "cnpj": "00000000000100",
    "active": true
  },
  "visits": [
    {
      "id": 10,
      "client_id": 1,
      "user_id": 2,
      "status": "finalizado",
      "visit_date": "2026-11-01",
      "current_step": 6
    }
  ]
}
```

**Erros**

- `404` — cliente não encontrado.

## PATCH `/clients/{id}`

Atualiza os dados cadastrais. Envie apenas os campos que deseja alterar.

**Body (JSON)**

```json
{
  "name": "Indústria Norte S/A",
  "responsible_person": "Maria Souza",
  "phone": "(92) 98888-8888",
  "email": "contato@norte.com.br",
  "address": "Av. Industrial, 2000 — Manaus/AM",
  "active": true
}
```

Também é possível alterar `cnpj`; a API valida se o novo CNPJ já pertence a outro
cliente.

**Resposta 200** — cliente atualizado.

**Erros**

- `400` — CNPJ já cadastrado em outro cliente.
- `404` — cliente não encontrado.

## DELETE `/clients/{id}`

Desativa o cliente (`active = false`), preservando as visitas.

**Resposta 200**

```json
{
  "message": "Cliente desativado com sucesso.",
  "id": 1,
  "active": false
}
```

**Erros**

- `404` — cliente não encontrado.

---

# Visitas técnicas

## GET `/visits`

Lista visitas com filtros opcionais.

**Query**

| Parâmetro | Tipo | Descrição |
| --- | --- | --- |
| `status` | enum | `rascunho` ou `finalizado` |
| `client_id` | inteiro | Filtrar por cliente |
| `user_id` | inteiro | Filtrar por inspetor |
| `date_from` | data (`YYYY-MM-DD`) | Início do intervalo de `visit_date` |
| `date_to` | data (`YYYY-MM-DD`) | Fim do intervalo de `visit_date` |
| `page` | inteiro | Página (padrão 1) |
| `per_page` | inteiro | Itens por página (padrão 50) |

**Resposta 200** — lista paginada, ordenada por `updated_at` decrescente.

## POST `/visits`

Inicia um rascunho de visita.

**Body (JSON)**

```json
{
  "client_id": 1,
  "visit_date": "2026-11-08",
  "user_id": 2
}
```

`user_id` é opcional; se omitido, o inspetor é o usuário autenticado.

**Resposta 200**

```json
{
  "id": 10,
  "created_at": "2026-11-08T12:30:00+00:00",
  "updated_at": "2026-11-08T12:30:00+00:00",
  "client_id": 1,
  "user_id": 2,
  "status": "rascunho",
  "visit_date": "2026-11-08",
  "current_step": 1,
  "checklist_epi": {},
  "checklist_condicoes_gerais": {},
  "checklist_incendio": {},
  "checklist_maquinas": {},
  "checklist_documentacao": {},
  "general_observations": "",
  "pdf_report_url": null
}
```

**Erros**

- `404` — cliente não encontrado ou inativo.
- `400` — `user_id` informado não existe ou está bloqueado.

## GET `/visits/{id}`

Retorna a visita completa, com cliente, inspetor e fotografias.

**Resposta 200**

```json
{
  "visit": {
    "id": 10,
    "client_id": 1,
    "user_id": 2,
    "status": "rascunho",
    "visit_date": "2026-11-08",
    "current_step": 3,
    "checklist_epi": { "epi_fornecimento": "Sim" },
    "checklist_condicoes_gerais": {},
    "checklist_incendio": {},
    "checklist_maquinas": {},
    "checklist_documentacao": {},
    "general_observations": "Área de expedição com acesso restrito.",
    "pdf_report_url": null
  },
  "client": { "id": 1, "name": "Indústria Norte Ltda" },
  "inspector": { "id": 2, "name": "João Inspetor" },
  "photos": []
}
```

## PATCH `/visits/{id}`

Autosave. Envie apenas os campos alterados; `updated_at` é renovado automaticamente.

**Body (JSON)**

```json
{
  "current_step": 3,
  "checklist_epi": {
    "epi_fornecimento": "Sim",
    "epi_uso": "Parcial",
    "epi_conservacao": "Sim",
    "epi_ca": "Sim",
    "epi_obs": "Reposição pendente para dois colaboradores."
  },
  "checklist_condicoes_gerais": {
    "cond_sanitarios": "Sim",
    "cond_iluminacao": "Parcial",
    "cond_ventilacao": "Sim",
    "cond_ordem": "Sim"
  },
  "general_observations": "Recomendada revisão da iluminação no setor B."
}
```

Campos aceitos: `current_step`, os cinco `checklist_*`, `general_observations` e
`visit_date`.

**Resposta 200** — visita atualizada.

**Erros**

- `400` — visita finalizada (não pode ser editada).
- `400` — `current_step` fora do intervalo 1–6.
- `404` — visita não encontrada.

## POST `/visits/{id}/finalize`

Valida os campos obrigatórios e muda o status para `finalizado`.

**Body (JSON)**

```json
{}
```

**Resposta 200**

```json
{
  "message": "Visita finalizada com sucesso.",
  "visit": {
    "id": 10,
    "status": "finalizado",
    "current_step": 6,
    "updated_at": "2026-11-08T15:00:00+00:00"
  }
}
```

**Erros**

- `400` — visita já finalizada.
- `400` — cliente, inspetor ou data ausentes.
- `400` — um ou mais checklists vazios.
- `404` — visita não encontrada.

---

# Fotografias

## GET `/photos`

Lista as fotografias de uma visita.

**Query**

| Parâmetro | Tipo | Descrição |
| --- | --- | --- |
| `visit_id` | inteiro | Obrigatório |
| `page` | inteiro | Página (padrão 1) |
| `per_page` | inteiro | Itens por página (padrão 100) |

**Resposta 200** — lista paginada, ordenada por `display_order` crescente.

## POST `/photos`

Faz upload de uma imagem vinculada a uma visita.

**Content-Type:** `multipart/form-data`

| Campo | Tipo | Obrigatório | Descrição |
| --- | --- | --- | --- |
| `visit_id` | inteiro | Sim | Visita pai |
| `image` | arquivo | Sim | Imagem (JPG, PNG etc.) |
| `caption` | texto | Não | Legenda |
| `display_order` | inteiro | Não | Padrão `0` |

**Exemplo com curl**

```bash
curl -X POST "https://SEU-INSTANCIA.xano.io/api:acnnorte/photos" \
  -H "Authorization: Bearer SEU_AUTH_TOKEN" \
  -F "visit_id=10" \
  -F "caption=Extintor do setor A" \
  -F "display_order=1" \
  -F "image=@/caminho/foto.jpg"
```

**Resposta 200**

```json
{
  "id": 5,
  "created_at": "2026-11-08T13:00:00+00:00",
  "visit_id": 10,
  "image": {
    "id": "file_abc123",
    "name": "foto.jpg",
    "size": 245678,
    "mime": "image/jpeg",
    "path": "/uploads/foto.jpg",
    "url": "https://.../foto.jpg"
  },
  "caption": "Extintor do setor A",
  "display_order": 1
}
```

**Erros**

- `404` — visita não encontrada.

## PATCH `/photos/{id}`

Atualiza legenda/ordem e/ou substitui o arquivo.

**Content-Type:** `multipart/form-data`

| Campo | Tipo | Obrigatório | Descrição |
| --- | --- | --- | --- |
| `caption` | texto | Não | Nova legenda |
| `display_order` | inteiro | Não | Nova ordem |
| `image` | arquivo | Não | Novo arquivo; o antigo é removido do storage |

**Exemplo com curl**

```bash
curl -X PATCH "https://SEU-INSTANCIA.xano.io/api:acnnorte/photos/5" \
  -H "Authorization: Bearer SEU_AUTH_TOKEN" \
  -F "caption=Extintor do setor A — atualizado" \
  -F "image=@/caminho/foto-nova.jpg"
```

**Resposta 200** — fotografia atualizada.

**Erros**

- `404` — fotografia não encontrada.

## DELETE `/photos/{id}`

Remove a fotografia do banco e do storage, preservando a visita.

**Resposta 200**

```json
{
  "message": "Fotografia removida com sucesso.",
  "id": 5
}
```

**Erros**

- `404` — fotografia não encontrada.

---

# Endpoints extras

Além dos endpoints solicitados, o pacote inclui estes endpoints de apoio para a
aplicação:

| Endpoint | Motivo |
| --- | --- |
| `GET /auth/me` | Recuperar o perfil após recarregar a página. |
| `GET /users` | Tela administrativa de usuários. |
| `GET /visits/{id}` | Abrir uma visita com cliente, inspetor e fotos em uma única chamada. |
| `PATCH /clients/{id}` | Edição de cliente (o fluxo original já permitia atualização). |
| `GET /photos?visit_id=` | Carregar a galeria da visita. |
