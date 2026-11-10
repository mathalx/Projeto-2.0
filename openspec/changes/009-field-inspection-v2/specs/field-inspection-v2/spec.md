# Specification: Field Inspection v2

## Purpose

Definir o fluxo isolado de inspeção de campo do ACNnorte, com navegação em
blocos, captura automática de clima, identificação do trabalhador, botoeira de
equipamentos, scanner de EPI, assinaturas e emissão de laudos.

## Requirements

### Navegação
1. O aplicativo deve abrir diretamente no formulário principal, sem login.
2. O menu lateral deve exibir o perfil ativo no formato `Nome - Perfil`.
3. O grupo **Navegação** deve conter Painel Inicial, Clientes, Visitas
   Técnicas / Inspeções de Campo, Fotografias (Galeria de Fotos do Dia) e
   Relatórios & Exportação.
4. O grupo **Acesso rápido** deve conter Cadastrar Cliente e Nova Visita /
   Nova Inspeção.

### Cabeçalho e clima
5. O cabeçalho deve registrar nome da empresa e datas da avaliação.
6. O GPS deve ser solicitado automaticamente.
7. Temperatura e umidade devem ser obtidas por API meteorológica, com
   OpenWeather quando configurada e Open-Meteo como fallback.
8. Deve existir ajuste manual para GPS ou clima indisponíveis.

### Trabalhador e equipamentos
9. O nome do funcionário e a foto do rosto são obrigatórios.
10. O formulário deve conter as seções NR-06, NR-24/08, IT/NR-23, NR-12 e
    PGR/PCMSO/CIPA.
11. A botoeira deve usar chips por categoria e o catálogo oficial ACN Norte.
12. Cada equipamento deve exibir identificação, série e última calibração.
13. Arquivos devem seguir `[Horário]_[IdentificaçãoAparelho]_[TagEPI].jpg`.

### EPI e galeria
14. O scanner deve analisar a imagem, sugerir respostas NR-06 e salvar a foto
    com o nome padronizado.
15. O formulário deve terminar com o atalho **Ir para Galeria do Dia**.

### Assinaturas e laudos
16. As assinaturas do responsável técnico e do avaliador devem ser capturadas
    por canvas/touch.
17. A finalização deve validar empresa, trabalhador com foto, equipamentos,
    checklist e assinaturas.
18. O PDF deve conter foto ao lado do nome, tabela técnica e assinaturas no
    rodapé.
19. Deve ser possível emitir uma planilha Excel consolidada da inspeção.

## Scenarios

### Captura automática
- **Given** um dispositivo com GPS e conexão
- **When** o formulário é aberto e a permissão é concedida
- **Then** temperatura e umidade são salvas e exibidas automaticamente

### Seleção rápida de equipamento
- **Given** o catálogo oficial carregado
- **When** o avaliador toca em um chip
- **Then** o equipamento é persistido com identificação e calibração

### Finalização protegida
- **Given** uma inspeção sem foto ou assinatura
- **When** o avaliador tenta finalizar
- **Then** o sistema lista as pendências e não finaliza

### Emissão do laudo
- **Given** uma inspeção finalizada
- **When** o avaliador gera o PDF ou Excel
- **Then** o documento inclui trabalhador, equipamentos e assinaturas
