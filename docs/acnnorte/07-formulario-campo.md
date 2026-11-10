# Formulário de Campo — Changes 08 a 12

Este documento registra a implementação das changes 08 a 12 no aplicativo
Streamlit do ACNnorte. O acesso passou a ser direto ao formulário de campo:
não existe mais tela de login.

## CHANGE 08 — Autenticação direta e cabeçalho

- `src/views/login_view.py` foi removida e o `src/main.py` abre diretamente a
  página **Formulário de Campo**.
- O cabeçalho do formulário contém:
  - **Nome da empresa**;
  - **Data de avaliação** e **data final da avaliação**;
  - cartões de **temperatura** e **umidade**.
- A localização é obtida pelo GPS do navegador com um componente
  `st.components.v2` (`src/components.py`). As coordenadas são enviadas à
  OpenWeather (`src/weather_service.py`), que retorna temperatura (°C),
  umidade (%) e a descrição do clima.
- Também é possível informar latitude/longitude ou temperatura/umidade
  manualmente quando o navegador bloqueia o GPS.
- Configuração: `OPENWEATHER_API_KEY` no arquivo `.env` (veja
  `.env.example`). Sem a chave, o GPS continua sendo capturado e o clima pode
  ser preenchido manualmente.

Campos persistidos na tabela lógica `inspections`:

| Campo | Tipo |
| --- | --- |
| `empresa_nome` | TEXT |
| `data_avaliacao` | DATE |
| `data_avaliacao_fim` | DATE |
| `temperatura_capturada` | DECIMAL |
| `umidade_capturada` | DECIMAL |

## CHANGE 09 — Funcionário com foto facial

- A seção **Identificação do funcionário** exibe, lado a lado:
  - nome do funcionário (obrigatório);
  - função;
  - setor;
  - quadro lateral para câmera ou upload da **foto do rosto**.
- A foto é salva em `data/photos/workers/` e referenciada em
  `funcionario_foto_url`.
- O PDF do laudo posiciona a foto ao lado do nome do avaliado.

Campos da tabela lógica `inspection_workers`:

| Campo | Tipo |
| --- | --- |
| `funcionario_nome` | TEXT |
| `funcionario_foto_url` | TEXT |
| `funcao` | TEXT |
| `setor` | TEXT |

## CHANGE 10 — Catálogo de equipamentos ACN Norte

O catálogo oficial fica em `src/equipment_catalog.py` e é complementado por
`data/equipments.json` (datas de calibração e ajustes locais).

Equipamentos incluídos:

- **Audiodosímetros:** Chrompack SmartdB (03440, 03558, 03611, 05981, 02319,
  02386) e Instrutherm DOS-1000X (DOS1000_04_02385).
- **Bombas de amostragem:** Criffer Accura 3 (22000098), Gilian BDXII
  (20170104107) e Inlite Ventuspro.
- **Vibração:** Chrompack SmartVib (certificado RBC5-12181-610) e Instrutherm
  MV-2000 (04_328).
- **IBUTG e outros:** Chrompack Net.Temp (IBU000000724) e Instrutherm THDL-400
  (181123417).

A interface usa `st.segmented_control` para o tipo e `st.multiselect` como
seletor rápido. Ao selecionar, a **data da última calibração** é exibida
automaticamente. Quando a data ainda não foi cadastrada, a interface mostra
“Não informada” e oferece a opção de registrá-la.

Tabela `equipments`:

| Campo | Tipo |
| --- | --- |
| `codigo` | TEXT (chave) |
| `tipo` | TEXT |
| `marca` | TEXT |
| `modelo` | TEXT |
| `num_serie` | TEXT |
| `num_equipamento` | TEXT |
| `data_ultima_calibracao` | DATE |

Tabela `inspection_devices`: relaciona a inspeção aos equipamentos usados,
guardando um retrato dos dados do catálogo no momento da avaliação.

### Nomenclatura padrão dos arquivos

`[Horário]_[IdentificaçãoAparelho]` e, quando houver EPI,
`[Horário]_[IdentificaçãoAparelho]_[TagEPI].jpg`.

Exemplos gerados por `build_photo_filename()`:

- `1430_03440.jpg`
- `1430_03440_EPI_ProtetorAuditivo.jpg`
- `0915_DOS1000_04_02385.jpg`

## CHANGE 11 — Scanner de EPI e galeria do dia

- O módulo `src/epi_scanner.py` analisa a foto do EPI com OCR opcional
  (Tesseract/pytesseract).
- O scanner procura nomes de EPIs, siglas e o número do **CA**. O resultado é
  gravado como JSON em `reconhecimento_epi` e o checklist NR-06 é preenchido
  automaticamente.
- Sem OCR instalado, a foto continua sendo registrada e o formulário recebe
  uma sugestão conservadora (`Parcial`) para revisão humana.
- Para habilitar o OCR, instale o Tesseract e, se necessário, defina
  `TESSERACT_CMD` no `.env`.
- O formulário tem um botão flutuante **➡️ Galeria do dia** no final.
- A página **Fotografias** ganhou a aba **📅 Galeria do Dia**, que reúne as
  fotos de todas as avaliações em uma data.

Tabela `inspection_photos`:

| Campo | Tipo |
| --- | --- |
| `foto_url` | TEXT |
| `nome_arquivo` | TEXT |
| `horario_registro` | TIME |
| `equipamento_id` | INTEGER/TEXT |
| `reconhecimento_epi` | JSON |

## CHANGE 12 — Assinaturas digitais e laudo

- Dois quadros de assinatura (`st.components.v2`, canvas com suporte a toque,
  stylus e mouse) capturam:
  - **Responsável Técnico**;
  - **Avaliador**.
- As assinaturas são salvas em Base64/data URL.
- O gerador de PDF (`src/export_manager.py`) inclui:
  - foto do rosto e identificação do funcionário no cabeçalho;
  - tabela detalhada dos equipamentos (código, marca, modelo, série e
    calibração);
  - quadros visuais das assinaturas no rodapé;
  - empresa, período de avaliação, temperatura e umidade.
- A exportação Excel inclui os novos campos de funcionário, clima,
  equipamentos e status das assinaturas.

Tabela `inspection_signatures`:

| Campo | Tipo |
| --- | --- |
| `ass_responsavel_tecnico` | TEXT/Base64 |
| `ass_avaliador` | TEXT/Base64 |

## Persistência local

O aplicativo continua usando JSON local. A tabela lógica `inspections` é
persistida em `data/visits.json`, preservando o histórico, o painel e os
relatórios já existentes. Funcionários, equipamentos, fotos e assinaturas são
gravados dentro do registro da avaliação com os nomes de campo das tabelas
acima.

Arquivos:

- `data/visits.json` — inspeções/visitas, funcionário, equipamentos, fotos e
  assinaturas;
- `data/equipments.json` — catálogo e datas de calibração;
- `data/photos/` — fotos da galeria e do scanner de EPI;
- `data/photos/workers/` — fotos do rosto dos funcionários;
- `data/exports/` — PDFs e planilhas gerados.

## Validação

A finalização exige:

- nome da empresa;
- nome e foto do funcionário;
- pelo menos um equipamento;
- todos os campos obrigatórios do checklist;
- as duas assinaturas digitais.

Testes automatizados: `python -m pytest -q`.
