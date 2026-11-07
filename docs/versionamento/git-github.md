# Guia de Versionamento — Git e GitHub

Este documento define os padrões e fluxos de trabalho utilizando Git e GitHub no projeto **Aplicativo de Visitas Técnicas de Segurança do Trabalho**.

## 1. Estratégia de Branches

- **`main`**: Branch principal contendo o código estável e pronto para produção.
- **`develop`**: Branch de integração para novas funcionalidades em desenvolvimento.
- **`feature/*`**: Branches criadas para desenvolvimento de funcionalidades específicas (ex: `feature/002-database`).
- **`hotfix/*`**: Branches para correções urgentes na versão estável.

## 2. Padrão de Commits (Conventional Commits)

Utilizamos os seguintes prefixos nos commits:
- `feat:` Nova funcionalidade
- `fix:` Correção de erros
- `docs:` Alteração na documentação
- `style:` Ajustes de formatação / estilo
- `refactor:` Reestruturação de código
- `test:` Criação ou alteração de testes
- `chore:` Configurações, manutenção e build

Exemplo:
```bash
git commit -m "feat: adiciona estrutura inicial dos módulos"
```

## 3. Boas Práticas

1. Nunca versione arquivos contendo senhas, chaves de API ou dados confidenciais (conforme `.gitignore`).
2. Desenvolva sempre em uma branch `feature/` derivada de `develop`.
3. Abra Pull Requests para integração em `develop` após validação local.
4. O agente de IA (OpenCode/Gemini) não deve executar `git push` nem mesclar branches sem autorização explícita.
