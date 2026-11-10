# Recursos Visuais e Experiência do Usuário

## Objetivo

Centralizar os recursos visuais do ACNnorte em uma estrutura única e previsível,
facilitando futuras melhorias de experiência do usuário sem impactar o código
existente.

## Estrutura criada

```text
assets/
├── images/    # Imagens gerais (banners, ilustrações, fundos)
├── icons/     # Ícones avulsos (PNG, SVG, ICO)
├── styles/    # Folhas de estilo e CSS externos
├── logo/      # Logotipos e variações da marca ACNnorte
└── README.md  # Convenções de uso
```

Cada subpasta contém um arquivo `.gitkeep` para que a estrutura seja preservada
no controle de versão enquanto estiver vazia.

## Escopo desta etapa

Esta change apenas prepara a estrutura de pastas. Ela **não**:

- move arquivos existentes;
- altera imports do aplicativo;
- modifica funcionalidades, telas ou componentes;
- altera o armazenamento de dados (`data/`) ou a autenticação;
- recria componentes já existentes em `src/ui_components.py`.

## Convenções

- Nomes de arquivo em minúsculas, separados por hífen
  (ex.: `logo-acnnorte-horizontal.svg`).
- Preferência por formatos vetoriais (`.svg`) em logos e ícones.
- Os recursos devem ser referenciados por caminho absoluto calculado a partir da
  raiz do projeto, evitando dependência do diretório de execução.

## Uso futuro

As telas continuam usando os componentes atuais. Melhorias visuais que venham a
consumir `assets/` devem ser tratadas em changes posteriores, com testes e
validação próprios.
