# Módulo de Inspeção de Campo v2 — Layout ACN Norte

Este documento descreve o novo fluxo isolado em
`src/features/field_inspection/`. A separação preserva as regras de negócio,
o armazenamento local e as rotas existentes, mas reorganiza a experiência de
campo em componentes menores e testáveis.

## Estrutura do módulo

| Arquivo | Responsabilidade |
| --- | --- |
| `view.py` | Orquestra a página principal, o seletor de avaliação e o resumo do topo. |
| `sidebar.py` | Menu lateral em blocos, perfil ativo e atalhos de acesso rápido. |
| `header.py` | Empresa, datas e captura automática/manual de clima. |
| `geolocation.py` | Componente de GPS que solicita a localização automaticamente. |
| `worker.py` | Identificação do trabalhador e foto obrigatória do rosto. |
| `equipment.py` | Botoeira dinâmica (chips) com o catálogo oficial ACN Norte. |
| `epi.py` | Scanner de EPI com OCR opcional e gravação na galeria. |
| `checklist.py` | Checklist NR-06, NR-24/08, IT/NR-23, NR-12 e PGR/PCMSO/CIPA. |
| `signatures.py` | Canvas/touch de assinatura do responsável técnico e do avaliador. |
| `actions.py` | Salvar, finalizar, emitir PDF/Excel e atalho para a galeria do dia. |
| `documents.py` | Planilha Excel por inspeção e ponte para o laudo PDF homologado. |
| `services.py` | Orquestração de persistência e validação das regras existentes. |
| `constants.py` | Estrutura visual do menu e chaves compartilhadas. |

## Navegação

O menu lateral segue o Layout ACN Norte:

```text
👤 Ana.norte
   Ana.norte - Administrador
   Perfil ativo neste dispositivo

NAVEGAÇÃO
🏠 Painel Inicial
👥 Clientes
📋 Visitas Técnicas / Inspeções de Campo
📷 Fotografias (Galeria de Fotos do Dia)
📊 Relatórios & Exportação

ACESSO RÁPIDO
➕ Cadastrar Cliente
🚀 Nova Visita / Nova Inspeção
```

A página **Visitas Técnicas / Inspeções de Campo** abre o formulário principal.
As telas legadas de lista de visitas, senha e administração continuam
acessíveis no bloco recolhível **Registros e administração**.

## Acesso direto e cabeçalho

- O aplicativo abre no formulário de inspeção, sem tela de login.
- O perfil padrão é `Ana.norte - Administrador`, configurável por sessão.
- O cabeçalho contém nome da empresa, data inicial e data final.
- A localização é solicitada automaticamente pelo navegador.
- A temperatura e a umidade são consultadas primeiro na OpenWeather (quando
  `OPENWEATHER_API_KEY` está configurada) e, em seguida, na Open-Meteo como
  alternativa gratuita. Há ajuste manual para ambientes sem GPS/rede.

## Trabalhador e equipamentos

- O nome do trabalhador é obrigatório.
- A foto do rosto é capturada por câmera ou upload em um quadro lateral e é
  obrigatória para finalizar o laudo.
- A botoeira de equipamentos usa chips por categoria, com os IDs oficiais.
- A data da última calibração é exibida em cada equipamento selecionado e pode
  ser atualizada no próprio formulário.
- A nomenclatura dos arquivos permanece
  `[Horário]_[IdentificaçãoAparelho]_[TagEPI].jpg`, por exemplo
  `1430_03440_EPI_ProtetorAuditivo.jpg`.

## Scanner de EPI e galeria

- A foto do EPI é analisada com OCR opcional.
- O resultado preenche o checklist NR-06 e é salvo como JSON no registro da
  fotografia.
- A imagem é anexada à galeria com o nome padronizado.
- O botão **➡️ Ir para Galeria do Dia** no final do formulário abre a aba
  **Galeria do Dia** já filtrada pela data da avaliação.

## Assinaturas e documentos

- Dois quadros de assinatura em canvas aceitam toque, stylus e mouse.
- O laudo PDF mantém a foto do trabalhador ao lado do nome, a tabela técnica
  completa (tipo, marca/modelo, série, certificado e calibração) e as
  assinaturas no rodapé.
- A planilha Excel por inspeção consolida os dados, o checklist, as fotos e as
  assinaturas (com as imagens incorporadas quando disponíveis).
- A finalização continua exigindo empresa, funcionário com foto, equipamentos,
  checklist completo e duas assinaturas.

## Compatibilidade

- Os dados continuam em `data/visits.json`, `data/photos/`,
  `data/equipments.json` e `data/exports/`.
- As funções centrais de `storage_manager`, `equipment_catalog`,
  `form_template`, `epi_scanner`, `weather_service` e `export_manager` foram
  preservadas.
- As rotas antigas (painel, clientes, visitas, fotografias, relatórios, perfil
  e administração) continuam renderizando.
