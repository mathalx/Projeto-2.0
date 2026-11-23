# ACNnorte no Xano

Pacote de backend pronto para importar no Xano. Ele substitui a persistência local em
JSON por quatro tabelas relacionais e vinte endpoints REST, com autenticação nativa,
checklists em JSON, upload de fotografias e regras de ciclo de vida da visita.

## Arquivos

| Arquivo | Conteúdo |
| --- | --- |
| `acnnorte.xs` | Multidoc XanoScript com 4 tabelas, 1 API group e 20 endpoints. É o arquivo que você importa no painel do Xano. |
| `workspace/` | A mesma definição dividida no formato de um documento por arquivo, exigido pelo CLI (`xano workspace push -d ./xano/workspace`). Gerado com `xano flatten`. |
| `schema.md` | Especificação detalhada das tabelas, campos, índices, defaults e mapeamento do JSON local. |
| `api.md` | Referência dos endpoints, payloads, respostas e códigos de erro. |
| `integracao.md` | Como apontar a aplicação Streamlit para o Xano e exemplos de chamadas. |

O arquivo `acnnorte.xs` e os 25 arquivos de `workspace/` foram validados com o parser
oficial do XanoScript (`@xano/xanoscript-language-server`): **0 erros e 0 avisos de
sintaxe**.

## Pré-requisitos

- Uma conta e um workspace no Xano.
- Para importar pelo painel: plano que permita criar workspace (o plano gratuito serve).
- Para importar via CLI: Node.js 20+ e o CLI do Xano.

## Opção A — Criar um workspace novo pelo painel (mais simples)

1. Abra o Xano e vá para **Workspaces**.
2. No menu **⋮** do workspace, escolha **Create Workspace (Multi-Doc)**.
3. Cole o conteúdo de `acnnorte.xs` ou clique em **Upload File** e selecione o arquivo.
4. Confirme a criação. O Xano vai criar as 4 tabelas, o API group `ACNnorte` e os 20
   endpoints.
5. Abra o API group e confira a URL base gerada, no formato:
   `https://SEU-INSTANCIA.xano.io/api:acnnorte`.

> O `canonical` do API group está fixado em `acnnorte`. Se o nome já estiver em uso no
> seu workspace, o Xano pode gerar outro sufixo; nesse caso, copie a URL exibida no
> painel e use-a como `XANO_BASE_URL`.

## Opção B — Aplicar em um workspace existente via CLI

O CLI exige **um documento por arquivo**. Por isso o pacote inclui a pasta `workspace/`,
gerada a partir de `acnnorte.xs` com `xano flatten`. O push usa o `guid` de cada
definição para decidir entre criar e atualizar. Como os arquivos novos não têm `guid`, o
primeiro push **cria** os objetos. Não faça o mesmo push duas vezes sem antes rodar
`pull`; caso contrário, serão criados objetos duplicados.

```bash
npm install -g @xano/cli
xano auth

# Sempre veja o preview antes de aplicar
xano workspace push -d ./xano/workspace --dry-run

# Aplique
xano workspace push -d ./xano/workspace
```

Se o CLI pedir confirmação, revise o preview: devem aparecer 25 operações `CREATE`
(4 tabelas, 1 API group e 20 endpoints).

> Em planos pagos, o push direto pode estar bloqueado. Nesse caso, use
> `xano sandbox push -d ./xano/workspace` e promova pelo sandbox, ou habilite
> **Allow Direct Workspace Push** nas configurações do workspace.

Se você editar `acnnorte.xs` (por exemplo, para adicionar um campo), regenere a pasta do
CLI antes do push:

```bash
xano flatten xano/acnnorte.xs -o xano/workspace --keep-source -f
```

## Criar o primeiro administrador (obrigatório)

O endpoint `POST /auth/signup` exige um administrador autenticado. Em um workspace novo
não existe nenhum usuário, então crie o primeiro administrador manualmente:

1. No Xano, abra a tabela `users`.
2. Clique em **Add Record**.
3. Preencha:
   - `name`: nome do administrador.
   - `email`: e-mail de login.
   - `password`: senha desejada. O campo é do tipo **Password** e o Xano aplica o hash
     nativo automaticamente.
   - `role`: `administrador`.
   - `status`: `ativo`.
4. Salve e teste o login em `POST /auth/login`.

Depois disso, os demais usuários podem ser criados pelo endpoint `POST /auth/signup`
usando o token desse administrador.

> Se você criar o registro via API/importação de dados, envie a senha em texto puro
> apenas no campo `password`; não envie hash. O Xano faz o hash na gravação.

## Configurar a aplicação

Adicione ao `.env` (ou aos secrets do Streamlit):

```dotenv
XANO_BASE_URL=https://SEU-INSTANCIA.xano.io/api:acnnorte
XANO_AUTH_TOKEN=
```

- `XANO_BASE_URL` é a URL do API group, **sem** barra no final.
- `XANO_AUTH_TOKEN` é preenchido em tempo de execução após o login; não versione esse
  valor. Para testes manuais, você pode colar o token retornado por `/auth/login`.
- A aplicação Streamlit chama o Xano pelo servidor Python; não há necessidade de
  configurar CORS para esse cenário.

## Teste rápido (smoke test)

Substitua `SEU-INSTANCIA` pela instância e `EMAIL`/`SENHA` pelas credenciais do
administrador criado.

```bash
# 1. Login
curl -X POST "https://SEU-INSTANCIA.xano.io/api:acnnorte/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"EMAIL\",\"password\":\"SENHA\"}"

# 2. Guarde o authToken retornado e liste clientes
curl "https://SEU-INSTANCIA.xano.io/api:acnnorte/clients" \
  -H "Authorization: Bearer SEU_AUTH_TOKEN"

# 3. Crie um cliente
curl -X POST "https://SEU-INSTANCIA.xano.io/api:acnnorte/clients" \
  -H "Authorization: Bearer SEU_AUTH_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"name\":\"Indústria Norte Ltda\",\"cnpj\":\"00000000000100\",\"responsible_person\":\"Carlos\",\"phone\":\"(92) 99999-9999\",\"email\":\"contato@norte.com.br\"}"

# 4. Inicie uma visita (use o id do cliente retornado)
curl -X POST "https://SEU-INSTANCIA.xano.io/api:acnnorte/visits" \
  -H "Authorization: Bearer SEU_AUTH_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"client_id\":1,\"visit_date\":\"2026-11-08\"}"
```

## Regras implementadas

- **CNPJ único**: índice `unique` na tabela `clients` e verificação prévia no
  `POST /clients` e no `PATCH /clients/{id}`. O CNPJ é comparado como texto; envie
  sempre no mesmo formato (recomendado: somente dígitos).
- **Autosave**: `PATCH /visits/{id}` atualiza somente os campos enviados e sempre
  renova `updated_at`.
- **Bloqueio após finalizar**: o `PATCH /visits/{id}` recusa visitas com
  `status = "finalizado"`. A finalização exige cliente, inspetor, data e os cinco
  checklists não vazios.
- **Exclusão lógica de cliente**: `DELETE /clients/{id}` grava `active = false` e
  preserva o histórico de visitas.
- **Fotografias independentes**: `DELETE /photos/{id}` remove o registro e o arquivo do
  storage sem apagar a visita; `PATCH /photos/{id}` permite trocar a imagem e remove o
  arquivo antigo.
- **Papéis**: `administrador` pode criar/listar usuários e alterar status; `usuario`
  usa o restante da API. O auto-bloqueio do próprio administrador é impedido.

## Segurança

- O token JWT é emitido pelo Xano com validade de 24 horas (`86400` segundos).
- Bloquear um usuário impede **novos logins**. Tokens já emitidos continuam válidos até
  expirar; para revogação imediata, reduza a expiração, rotacione o segredo de
  autenticação do workspace ou aplique um middleware de status (recurso de plano pago).
- Senhas usam o campo nativo **Password** do Xano; nunca são retornadas nas respostas
  (exceto a leitura interna do login, que não sai no response).
- As imagens são gravadas com acesso `public` para simplificar a exibição no Streamlit.
  Se as fotos forem sensíveis, troque para `access = "private"` no `storage.create_image`
  e use `storage.sign_private_url` para gerar URLs temporárias.
- Não coloque o token de administrador do Xano em código versionado. Use `.env` ou
  secrets do Streamlit.
- Recomenda-se habilitar rate limiting e revisar as configurações de CORS no Xano antes
  de expor a API publicamente.

## Solução de problemas

| Sintoma | Causa provável | Ação |
| --- | --- | --- |
| `401/403` em todos os endpoints | Token ausente, expirado ou sem permissão | Faça login novamente e confira o `role`/`status` do usuário. |
| `404` em `/clients` | `XANO_BASE_URL` sem o API group correto | Copie a URL base exibida no painel do Xano. |
| Erro de unicidade ao criar cliente | CNPJ já cadastrado (inclusive cliente inativo) | Localize o registro na tabela `clients` e reative com `PATCH /clients/{id}` e `{"active": true}`. |
| `PATCH /visits/{id}` retorna erro | Visita já finalizada | Use uma visita em `rascunho` ou crie outra. |
| Upload de foto falha | Campo enviado como JSON em vez de `multipart/form-data` | Envie o arquivo no campo `image` com `multipart/form-data`. |
| Push do CLI cria duplicatas | Push repetido sem `guid` | Rode `xano workspace pull` e depois `push`; ou apague os duplicados. |

## Próximo passo na aplicação

A aplicação continua usando `data/*.json` até que a camada de acesso seja trocada. O
passo a passo de migração, incluindo o mapeamento de campos e exemplos em Python, está
em [`integracao.md`](integracao.md).
