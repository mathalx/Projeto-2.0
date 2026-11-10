# Design: Estrutura de Recursos Visuais

## Decisão
Adotar uma pasta única `assets/` na raiz do projeto, subdividida por tipo de
recurso. A separação por tipo evita arquivos misturados e facilita a localização
de logos, ícones, imagens e estilos.

## Estrutura

```text
assets/
├── images/    # Imagens gerais (banners, ilustrações, fundos)
├── icons/     # Ícones avulsos (PNG, SVG, ICO)
├── styles/    # Folhas de estilo e CSS externos
├── logo/      # Logotipos e variações da marca ACNnorte
└── README.md  # Convenções de uso
```

## Preservação no Git
Pastas vazias não são versionadas pelo Git. Por isso, cada subpasta recebe um
arquivo `.gitkeep`, mantendo a estrutura disponível em novos clones.

## Compatibilidade
A criação das pastas é puramente aditiva. Os componentes visuais continuam em
`src/ui_components.py` e nenhum import é alterado, garantindo que a aplicação
continue funcionando exatamente como antes.

## Referência de caminhos
Arquivos de estilo ou imagem devem ser resolvidos a partir da raiz do projeto
(ex.: `os.path.join(PROJECT_ROOT, "assets", "logo", ...)`), evitando depender do
diretório de execução do Streamlit.
