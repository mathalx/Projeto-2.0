# Specification: Visual Assets Structure

## Purpose
Define a estrutura padrão para armazenamento de recursos visuais estáticos do
projeto ACNnorte.

## Requirements

1. O projeto deve possuir uma pasta `assets/` na raiz.
2. `assets/` deve conter as subpastas `images/`, `icons/`, `styles/` e `logo/`.
3. Cada subpasta deve conter um arquivo `.gitkeep` para preservação no Git.
4. A estrutura deve ser documentada em `assets/README.md`.
5. A documentação do projeto deve descrever a estrutura em
   `docs/acnnorte/05-recursos-visuais.md` e na árvore de
   `docs/acnnorte/01-arquitetura.md`.
6. A criação da estrutura não pode mover arquivos existentes, alterar imports,
   modificar funcionalidades, armazenamento de dados ou autenticação.

## Scenarios

### Estrutura disponível em novo clone
- **Given** um clone limpo do repositório
- **When** o desenvolvedor acessa a raiz do projeto
- **Then** as pastas `assets/images`, `assets/icons`, `assets/styles` e
  `assets/logo` existem e são rastreáveis pelo Git

### Aplicação inalterada
- **Given** a estrutura de assets criada
- **When** a aplicação é iniciada com `streamlit run src/main.py`
- **Then** o comportamento das telas, da autenticação e do armazenamento de
  dados permanece inalterado
