# Design: Formulário de Campo Integral

## Acesso direto
`src/main.py` não importa mais uma tela de login. A página padrão é
`Formulário de Campo`, e a sessão assume o perfil de avaliador ACNnorte. As
páginas administrativas continuam disponíveis no menu.

## Cabeçalho e clima
O cabeçalho usa widgets nativos para empresa e datas. A geolocalização é feita
por um componente `st.components.v2` que devolve latitude/longitude para o
Python. `weather_service.py` consulta a OpenWeather com
`OPENWEATHER_API_KEY`. Há fallback de coordenadas e clima manuais.

## Funcionário e equipamentos
A foto do rosto é salva em `data/photos/workers/`. O catálogo é definido em
`equipment_catalog.py`, persistido/complementado em `data/equipments.json` e
selecionado com `st.segmented_control` + `st.multiselect`. A nomenclatura dos
arquivos é centralizada em `build_photo_filename()`.

## Scanner de EPI
`epi_scanner.py` usa Pillow para validar a imagem e, quando disponível,
pytesseract/Tesseract para OCR. O resultado é um JSON com itens, CA, confiança
e texto. `suggest_epi_answers()` converte o resultado em respostas do checklist
NR-06. Sem OCR, a sugestão é conservadora e revisável.

## Assinaturas e laudo
Dois componentes de canvas capturam assinaturas por toque/stylus/mouse e
devolvem PNG em data URL. O PDF inclui foto do funcionário, tabela de
equipamentos e quadros de assinaturas. A exportação Excel recebe os novos
campos.

## Persistência
`storage_manager.py` adiciona funções para inspeção, funcionário, dispositivos,
fotos e assinaturas, mantendo o formato de `visits.json` e a compatibilidade
com o painel e os relatórios existentes.
