# Tasks: 008-formulario-campo-integral

## Change 08 — Acesso direto e clima
- [x] Remover a tela de login do fluxo principal
- [x] Abrir o Formulário de Campo como página inicial
- [x] Campos de empresa e datas no cabeçalho
- [x] Componente de geolocalização (CCv2)
- [x] Integração com OpenWeather
- [x] Fallback manual de coordenadas/temperatura/umidade
- [x] Persistir temperatura e umidade na inspeção

## Change 09 — Funcionário com foto
- [x] Nome, função e setor
- [x] Câmera ou upload da foto do rosto
- [x] Armazenamento da foto e URL no registro
- [x] Validação antes de finalizar

## Change 10 — Catálogo de equipamentos
- [x] Catálogo oficial ACN Norte (14 equipamentos)
- [x] Seletor rápido por categoria
- [x] Exibição automática da última calibração
- [x] Atualização local da data de calibração
- [x] Nomenclatura `[Horario]_[Identificacao]`
- [x] Persistência dos equipamentos da inspeção

## Change 11 — Scanner de EPI e galeria
- [x] Câmera/upload da foto do EPI
- [x] OCR opcional e reconhecimento de CA/EPI
- [x] Preenchimento automático do checklist NR-06
- [x] JSON `reconhecimento_epi`
- [x] Nome `[Horario]_[Identificacao]_[TagEPI].jpg`
- [x] Galeria do Dia em Fotografias
- [x] Botão flutuante de acesso rápido

## Change 12 — Assinaturas e laudo
- [x] Assinatura digital do responsável técnico
- [x] Assinatura digital do avaliador
- [x] Persistência em Base64
- [x] Foto do funcionário no cabeçalho do PDF
- [x] Tabela de equipamentos no PDF
- [x] Quadros de assinaturas no PDF
- [x] Novos campos na exportação Excel

## Validação
- [x] `python -m pytest -q`
- [x] Renderização de todas as páginas via `AppTest`
- [x] Testes de catálogo, nomes de arquivo, clima, scanner, inspeção e PDF
