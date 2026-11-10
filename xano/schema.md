# Schema do banco — ACNnorte

Este documento descreve exatamente o que o arquivo `acnnorte.xs` cria no Xano. Use-o
como referência para conferir o schema no painel e para planejar a migração dos dados
locais.

## Visão geral

| Tabela | Finalidade | Autenticação |
| --- | --- | --- |
| `users` | Usuários, login e papéis | `auth = true` |
| `clients` | Empresas clientes | `auth = false` |
| `visits` | Visitas técnicas e checklists | `auth = false` |
| `photos` | Fotografias das visitas | `auth = false` |
| `inspections` | Avaliações de campo (empresa, datas e clima) | `auth = false` |
| `inspection_workers` | Funcionário avaliado e foto do rosto | `auth = false` |
| `equipments` | Catálogo oficial de equipamentos ACN Norte | `auth = false` |
| `inspection_devices` | Equipamentos usados em cada inspeção | `auth = false` |
| `inspection_photos` | Fotos padronizadas e reconhecimento de EPI | `auth = false` |
| `inspection_signatures` | Assinaturas digitais do laudo | `auth = false` |

Relacionamentos:

```text
users 1 ─── N visits
clients 1 ─── N visits
visits 1 ─── N photos
inspections 1 ─── 1 inspection_workers
inspections 1 ─── N inspection_devices
equipments 1 ─── N inspection_devices
inspections 1 ─── N inspection_photos
inspections 1 ─── 1 inspection_signatures
```

Os campos de referência usam o tipo `int` com `table = "..."`. No Xano, isso cria uma
referência de tabela; a exclusão de um cliente é lógica, então o histórico de visitas
não é afetado.

---

## 1. `users`

Usuários do sistema. A autenticação é nativa do Xano (`auth = true`).

| Campo | Tipo Xano | Obrigatório | Padrão | Observações |
| --- | --- | --- | --- | --- |
| `id` | `int` | Sim | auto increment | Chave primária |
| `created_at` | `timestamp` | Sim | `now` | Data de criação |
| `name` | `text` | Sim | — | Nome completo, com `trim` |
| `email` | `email` | Sim | — | Único, `trim` + `lower`; usado no login |
| `password` | `password` | Sim | — | Hash nativo do Xano; mínimo de 6 caracteres |
| `role` | `enum` | Sim | `usuario` | Valores: `administrador`, `usuario` |
| `status` | `enum` | Sim | `ativo` | Valores: `ativo`, `bloqueado` |

Índices:

- Primário em `id`.
- B-tree em `created_at` (desc).
- **Unique** em `email`.
- B-tree em `role`.
- B-tree em `status`.

Regras:

- O e-mail é normalizado para minúsculas e sem espaços nas pontas.
- O login recusa usuários com `status = "bloqueado"`.
- O endpoint de criação de usuários exige `role = "administrador"` no token atual.
- O próprio administrador não pode se bloquear.

---

## 2. `clients`

Empresas clientes. A exclusão é lógica (`active = false`).

| Campo | Tipo Xano | Obrigatório | Padrão | Observações |
| --- | --- | --- | --- | --- |
| `id` | `int` | Sim | auto increment | Chave primária |
| `created_at` | `timestamp` | Sim | `now` | Data de criação |
| `name` | `text` | Sim | — | Razão social / nome fantasia, `trim` |
| `cnpj` | `text` | Sim | — | **Único**; `trim` |
| `responsible_person` | `text` | Não | — | Responsável na empresa |
| `phone` | `text` | Não | — | Telefone / WhatsApp |
| `email` | `email` | Não | — | E-mail de contato, `trim` + `lower` |
| `address` | `text` | Não | — | Campo de compatibilidade com o cadastro local |
| `active` | `bool` | Sim | `true` | Exclusão lógica |

Índices:

- Primário em `id`.
- B-tree em `created_at` (desc).
- **Unique** em `cnpj`.
- B-tree em `name` (asc).
- B-tree em `active`.

Regras:

- `POST /clients` e `PATCH /clients/{id}` verificam se o CNPJ já pertence a outro
  registro e retornam erro antes de gravar.
- `DELETE /clients/{id}` apenas grava `active = false`; as visitas continuam vinculadas.
- `GET /clients` retorna somente clientes ativos.
- O CNPJ é comparado como texto. Para evitar duplicidade por formatação, normalize no
  cliente da API (recomendado: somente dígitos, sem pontos, barra ou traço).

> **Campo extra:** `address` não estava na especificação original, mas é usado pelo
> formulário de cadastro atual da ACNnorte. Se você não quiser esse campo, remova a
> linha `text address? filters=trim` do `acnnorte.xs` e os trechos correspondentes dos
> endpoints de cliente.

---

## 3. `visits`

Visita técnica com cinco checklists independentes em JSON, além dos dados de
acompanhamento.

| Campo | Tipo Xano | Obrigatório | Padrão | Observações |
| --- | --- | --- | --- | --- |
| `id` | `int` | Sim | auto increment | Chave primária |
| `created_at` | `timestamp` | Sim | `now` | Data de criação |
| `updated_at` | `timestamp` | Sim | `now` | Renovado em cada autosave |
| `client_id` | `int` → `clients.id` | Sim | — | Cliente da visita |
| `user_id` | `int` → `users.id` | Sim | — | Inspetor responsável |
| `status` | `enum` | Sim | `rascunho` | Valores: `rascunho`, `finalizado` |
| `visit_date` | `date` | Sim | — | Data de realização |
| `current_step` | `int` | Sim | `1` | Etapa atual do formulário (1 a 6) |
| `checklist_epi` | `json` | Não | — | EPI / NR-06 |
| `checklist_condicoes_gerais` | `json` | Não | — | Ambiente e estrutura |
| `checklist_incendio` | `json` | Não | — | Extintores e rotas de fuga |
| `checklist_maquinas` | `json` | Não | — | Proteções e NR-12 |
| `checklist_documentacao` | `json` | Não | — | PGR, PCMSO, CIPA etc. |
| `general_observations` | `text` | Não | — | Observações gerais do inspetor |
| `pdf_report_url` | `attachment` | Não | — | Metadados do PDF gerado (inclui `url`) |

Índices:

- Primário em `id`.
- B-tree em `created_at` (desc).
- B-tree em `updated_at` (desc).
- B-tree em `client_id`.
- B-tree em `user_id`.
- B-tree em `status`.
- B-tree em `visit_date` (desc).

Ciclo de vida:

```text
POST /visits
  └── status = "rascunho", current_step = 1, checklists = {}

PATCH /visits/{id}  (autosave)
  └── atualiza apenas os campos enviados
  └── updated_at = now
  └── recusa se status = "finalizado"

POST /visits/{id}/finalize
  └── exige cliente, inspetor, data e os 5 checklists não vazios
  └── status = "finalizado", current_step = 6
```

Formato dos checklists: um objeto JSON por seção, com as respostas do formulário. O
formato é livre para o banco, mas a aplicação usa as chaves do arquivo
`src/form_template.py` (por exemplo, `epi_fornecimento`, `cond_sanitarios`,
`inc_extintores`, `maq_protecoes`, `doc_pgr`). O endpoint de finalização verifica se cada
objeto está não vazio; a validação fina de cada resposta obrigatória continua no
formulário da aplicação.

---

## 4. `photos`

Fotografias vinculadas a uma visita.

| Campo | Tipo Xano | Obrigatório | Padrão | Observações |
| --- | --- | --- | --- | --- |
| `id` | `int` | Sim | auto increment | Chave primária |
| `created_at` | `timestamp` | Sim | `now` | Data do upload |
| `visit_id` | `int` → `visits.id` | Sim | — | Visita pai |
| `image` | `image` | Sim | — | Upload direto; o Xano grava no storage e retorna metadados |
| `caption` | `text` | Não | — | Legenda descritiva |
| `display_order` | `int` | Sim | `0` | Ordem de exibição na galeria |

Índices:

- Primário em `id`.
- B-tree em `created_at` (desc).
- B-tree em `visit_id`.
- B-tree em `display_order` (asc).

Regras:

- O upload é feito com `multipart/form-data` no campo `image`.
- A resposta inclui os metadados da imagem (`id`, `name`, `size`, `mime`, `path`,
  `url`, `created_at`).
- A troca de imagem remove o arquivo antigo do storage.
- A exclusão remove o registro de `photos` e o arquivo do storage, sem tocar na visita.
- As imagens são públicas por padrão. Para fotos sensíveis, use armazenamento privado e
  URLs assinadas.

---

## 5. `inspections`

Avaliação de campo do formulário principal (CHANGE 08).

| Campo | Tipo Xano | Obrigatório | Padrão | Observações |
| --- | --- | --- | --- | --- |
| `id` | `int` | Sim | auto increment | Chave primária |
| `created_at` | `timestamp` | Sim | `now` | Data de criação |
| `updated_at` | `timestamp` | Sim | `now` | Renovado em cada autosave |
| `empresa_nome` | `text` | Sim | — | Nome da empresa |
| `data_avaliacao` | `date` | Sim | — | Data inicial |
| `data_avaliacao_fim` | `date` | Não | — | Data final do período |
| `temperatura_capturada` | `decimal` | Não | — | °C |
| `umidade_capturada` | `decimal` | Não | — | % |
| `clima` | `json` | Não | — | Descrição, cidade, latitude e longitude |
| `worker_id` | `int` → `inspection_workers.id` | Não | — | Funcionário avaliado |
| `status` | `enum` | Sim | `rascunho` | `rascunho`, `finalizado` |
| `checklist_epi` | `json` | Não | — | NR-06 |
| `checklist_condicoes_gerais` | `json` | Não | — | Ambiente |
| `checklist_incendio` | `json` | Não | — | NR-23 |
| `checklist_maquinas` | `json` | Não | — | NR-12 |
| `checklist_documentacao` | `json` | Não | — | PGR/PCMSO/CIPA |
| `observations` | `text` | Não | — | Observações |
| `conclusions` | `text` | Não | — | Conclusões |

> No armazenamento local atual, `inspections` é persistida dentro de
> `data/visits.json`, mantendo compatibilidade com o painel, a galeria e os
> relatórios existentes.

## 6. `inspection_workers`

| Campo | Tipo Xano | Obrigatório | Padrão | Observações |
| --- | --- | --- | --- | --- |
| `id` | `int` | Sim | auto increment | Chave primária |
| `inspection_id` | `int` → `inspections.id` | Sim | — | Inspeção pai |
| `funcionario_nome` | `text` | Sim | — | Nome completo |
| `funcionario_foto_url` | `text` | Sim | — | Foto do rosto |
| `funcao` | `text` | Não | — | Função exercida |
| `setor` | `text` | Não | — | Setor avaliado |

## 7. `equipments`

| Campo | Tipo Xano | Obrigatório | Padrão | Observações |
| --- | --- | --- | --- | --- |
| `id` | `int` | Sim | auto increment | Chave primária |
| `codigo` | `text` | Sim | — | Identificador interno |
| `tipo` | `text` | Sim | — | Audiodosímetro, bomba etc. |
| `marca` | `text` | Sim | — | Fabricante |
| `modelo` | `text` | Sim | — | Modelo |
| `num_serie` | `text` | Não | — | Número de série |
| `num_equipamento` | `text` | Não | — | Número patrimonial/equipamento |
| `data_ultima_calibracao` | `date` | Não | — | Data da última calibração |

O catálogo inicial contém os 14 equipamentos oficiais da ACN Norte
(audiodosímetros, bombas, vibração e IBUTG).

## 8. `inspection_devices`

| Campo | Tipo Xano | Obrigatório | Padrão | Observações |
| --- | --- | --- | --- | --- |
| `id` | `int` | Sim | auto increment | Chave primária |
| `inspection_id` | `int` → `inspections.id` | Sim | — | Inspeção |
| `equipment_id` | `int` → `equipments.id` | Sim | — | Equipamento |
| `codigo` | `text` | Sim | — | Snapshot do código |
| `marca` | `text` | Sim | — | Snapshot da marca |
| `modelo` | `text` | Sim | — | Snapshot do modelo |
| `num_serie` | `text` | Não | — | Snapshot da série |
| `num_equipamento` | `text` | Não | — | Snapshot do equipamento |
| `data_ultima_calibracao` | `date` | Não | — | Snapshot da calibração |

## 9. `inspection_photos`

| Campo | Tipo Xano | Obrigatório | Padrão | Observações |
| --- | --- | --- | --- | --- |
| `id` | `int` | Sim | auto increment | Chave primária |
| `inspection_id` | `int` → `inspections.id` | Sim | — | Inspeção |
| `foto_url` | `text` | Sim | — | URL/armazenamento da imagem |
| `nome_arquivo` | `text` | Sim | — | `[Horario]_[Aparelho]_[TagEPI].jpg` |
| `horario_registro` | `time` | Sim | — | Horário da foto |
| `equipamento_id` | `int` → `equipments.id` | Não | — | Equipamento relacionado |
| `reconhecimento_epi` | `json` | Não | — | Itens, CA, confiança e texto OCR |

## 10. `inspection_signatures`

| Campo | Tipo Xano | Obrigatório | Padrão | Observações |
| --- | --- | --- | --- | --- |
| `id` | `int` | Sim | auto increment | Chave primária |
| `inspection_id` | `int` → `inspections.id` | Sim | — | Inspeção |
| `ass_responsavel_tecnico` | `text` | Sim | — | PNG em Base64/data URL |
| `ass_avaliador` | `text` | Sim | — | PNG em Base64/data URL |

## Mapeamento do JSON local para o Xano

| JSON local | Xano | Tratamento |
| --- | --- | --- |
| `users.<username>.password` | `users.password` | Rehash nativo: recrie os usuários no Xano ou migre com um endpoint de importação que grave a senha em texto puro no campo `password`. |
| `users.<username>.is_admin` | `users.role` | `true` → `administrador`; `false` → `usuario`. |
| `users.<username>.active` | `users.status` | `true` → `ativo`; `false` → `bloqueado`. |
| `users.<username>` (chave) | `users.email` | O login passa a ser por e-mail. |
| `clients.<id>.responsible` | `clients.responsible_person` | Renomear. |
| `clients.<id>.address` | `clients.address` | Campo extra preservado. |
| `clients.<id>.created_at` | `clients.created_at` | Converter para timestamp. |
| `visits.<id>.client_id` | `visits.client_id` | Referência por `id` numérico (o JSON usa UUID de 8 caracteres; será preciso remapear). |
| `visits.<id>.technician` | `visits.user_id` | Criar/associar um registro em `users`. |
| `visits.<id>.date` | `visits.visit_date` | Converter para `date`. |
| `visits.<id>.status` | `visits.status` | `Rascunho`/`Em Andamento` → `rascunho`; `Finalizada` → `finalizado`. |
| `visits.<id>.forms.epi` | `visits.checklist_epi` | JSON direto. |
| `visits.<id>.forms.condicoes` | `visits.checklist_condicoes_gerais` | JSON direto. |
| `visits.<id>.forms.incendio` | `visits.checklist_incendio` | JSON direto. |
| `visits.<id>.forms.maquinas` | `visits.checklist_maquinas` | JSON direto. |
| `visits.<id>.forms.documentacao` | `visits.checklist_documentacao` | JSON direto. |
| `visits.<id>.observations` | `visits.general_observations` | Texto. |
| `visits.<id>.conclusions` | `visits.general_observations` | Concatenar ao texto ou criar um campo `conclusions` se quiser preservar separado. |
| `visits.<id>.photos[]` | linhas em `photos` | Migrar arquivos para o storage do Xano e criar os registros com `visit_id`. |
| `visits.<id>.updated_at` | `visits.updated_at` | Converter para timestamp. |

### Observações sobre a migração

1. Os IDs locais são UUIDs curtos; os IDs do Xano são inteiros. Faça a migração em duas
   passagens: crie clientes/usuários, guarde o mapa `id_local → id_xano` e depois crie as
   visitas/fotos com os novos IDs.
2. As senhas locais usam PBKDF2 e não são compatíveis com o hash do Xano. O caminho mais
   seguro é recriar os usuários e exigir redefinição de senha, ou importar as senhas em
   texto puro uma única vez (não recomendado em produção).
3. Faça um backup do diretório `data/` antes de qualquer migração.
4. Valide a migração em um workspace de teste antes de apontar a aplicação para produção.
