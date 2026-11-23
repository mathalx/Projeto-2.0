# Relatório de Implementação das Changes (01 a 07)

- **CHANGE 01**: Criada a estrutura visual da tela de login com aparência moderna, profissional, minimalista e responsiva, aplicando a identidade visual ACNnorte (ACN em `#16834A` e norte em `#59636A`).
- **CHANGE 02**: Implementados campos de usuário e senha (com senha oculta por padrão e validações completas contra campos vazios e credenciais incorretas).
- **CHANGE 03**: Implementados os três usuários iniciais (`Ana.norte`, `anaju.mãe`, `anaju.pai`) com hash seguro PBKDF2.
- **CHANGE 04**: Implementado o gerenciamento interno de usuários na área administrativa protegida (adicionar, alterar, ativar/desativar e remover).
- **CHANGE 05**: Implementada a alteração e recuperação segura de senha com verificação de senha atual e confirmação.
- **CHANGE 06**: Implementado o fluxo completo de autenticação, navegação, proteção de páginas e logout.
- **CHANGE 07**: Responsividade e acabamento visual refinados com CSS customizado, garantindo consistência em computadores, tablets e celulares.

> As melhorias posteriores de navegação, formulários, painel, fotografias,
> mensagens, design e desempenho estão documentadas em
> `docs/acnnorte/06-melhorias-experiencia.md`.
