# Pasta de Histórico de Alterações do Projeto

Esta pasta é o **repositório central e oficial de histórico de todas as alterações** do sistema **ACNnorte**.

---

## 📌 Diretriz Obrigatória

> **Toda e qualquer nova alteração no projeto deve ser registrada nesta pasta.**  
> Nenhuma mudança técnica, funcional, visual ou de infraestrutura deve ser concluída sem a respectiva atualização dos arquivos desta pasta.

---

## 📂 Arquivos Disponíveis

| Arquivo | Formato | Descrição |
| :--- | :--- | :--- |
| [`HISTORICO_CONSOLIDADO.txt`](file:///c:/Users/Matheus%20Alexandre/Desktop/projeto/historico-alteracoes/HISTORICO_CONSOLIDADO.txt) | Texto Puro (`.txt`) | Registro integral em texto puro legível em qualquer editor simples (ex: Bloco de Notas). |
| [`HISTORICO_CONSOLIDADO.md`](file:///c:/Users/Matheus%20Alexandre/Desktop/projeto/historico-alteracoes/HISTORICO_CONSOLIDADO.md) | Markdown (`.md`) | Registro estruturado com links navegáveis para os arquivos do projeto, seções e tabelas. |

---

## 🛠️ Procedimento para Novas Alterações

Ao realizar qualquer alteração futura no projeto:
1. Abra o arquivo [`HISTORICO_CONSOLIDADO.txt`](file:///c:/Users/Matheus%20Alexandre/Desktop/projeto/historico-alteracoes/HISTORICO_CONSOLIDADO.txt) (ou `.md`).
2. Adicione um novo Marco ou seção numerada com a data, objetivo da mudança, arquivos impactados e descrição detalhada.
3. Não duplique informações já registradas nas seções anteriores.
4. Mantenha os testes automatizados atualizados executando:
   ```bash
   python -m pytest -q
   ```

