# Specification: Formulário de Campo Integral

## Purpose
Definir o formulário principal do ACNnorte, acessado diretamente sem login, com
clima automático, funcionário identificado, equipamentos oficiais, scanner de
EPI e assinaturas digitais.

## Requirements

### Acesso e cabeçalho
1. O aplicativo deve abrir no Formulário de Campo, sem exigir login.
2. O cabeçalho deve conter nome da empresa e datas de avaliação.
3. A temperatura e a umidade devem ser capturadas automaticamente a partir do
   GPS e da OpenWeather.
4. Deve existir fallback manual quando o GPS ou a chave da OpenWeather não
   estiverem disponíveis.

### Funcionário
5. O nome do funcionário deve ser obrigatório.
6. A foto do rosto deve ser capturada por câmera ou upload e exibida ao lado
   do nome.
7. Função e setor devem ser registrados.

### Equipamentos
8. O catálogo deve conter todos os equipamentos oficiais da ACN Norte.
9. A seleção deve ser rápida, por categoria e com múltipla escolha.
10. A data da última calibração deve ser exibida ao selecionar o equipamento.
11. O nome padrão dos arquivos deve seguir
    `[Horario]_[IdentificacaoAparelho]` e, com EPI,
    `[Horario]_[IdentificacaoAparelho]_[TagEPI].jpg`.

### Scanner de EPI e galeria
12. O scanner deve analisar a foto e preencher o checklist NR-06.
13. O resultado do reconhecimento deve ser salvo como JSON.
14. A galeria do dia deve reunir as fotos da data selecionada.
15. O formulário deve oferecer um botão flutuante para a galeria do dia.

### Assinaturas e laudo
16. As assinaturas do responsável técnico e do avaliador devem ser capturadas
    por toque, stylus ou mouse.
17. As assinaturas devem ser persistidas em Base64.
18. O PDF deve exibir a foto do funcionário, a tabela de equipamentos e os
    quadros de assinaturas.
19. A finalização deve validar empresa, funcionário, foto, equipamentos,
    checklist e assinaturas.

## Scenarios

### Captura automática de clima
- **Given** um dispositivo com GPS e chave OpenWeather configurada
- **When** o avaliador autoriza a localização
- **Then** temperatura e umidade são exibidas e salvas na inspeção

### Scanner de EPI
- **Given** uma foto de EPI com CA legível
- **When** o avaliador solicita a análise
- **Then** o checklist NR-06 é preenchido e a foto é salva na galeria com o
  nome padronizado

### Finalização protegida
- **Given** uma avaliação sem assinaturas
- **When** o avaliador tenta finalizar
- **Then** o sistema lista as pendências e não finaliza
