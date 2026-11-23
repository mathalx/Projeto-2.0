# Assinaturas Digitais da Visita (CHANGE 04)

## Objetivo

Registrar as assinaturas do **Responsável Técnico** e do **Avaliador** ao final
da visita, com nome e desenho, e incluí-las no relatório PDF.

As assinaturas são obrigatórias para **concluir** a visita, mas não para salvar
um rascunho.

> **Aviso:** as assinaturas são registros eletrônicos de desenho e nome. Elas
> **não possuem validade jurídica automática** e não substituem certificação
> digital, ICP-Brasil ou outro processo formal de assinatura.

## Como assinar

1. Abra a visita em **Visitas Técnicas → ✍️ Preencher Visita**.
2. Avance até a etapa final (**Observações e conclusão da visita**).
3. Na seção **“✍️ Assinaturas obrigatórias”**:
   - Informe o **Nome do Responsável Técnico**.
   - Desenhe a assinatura na área branca com o mouse ou o dedo.
   - Repita para o **Avaliador**.
4. Use **Desfazer** para remover o último traço ou **Limpar** para recomeçar.
5. Clique em **“💾 Salvar assinaturas”** para confirmar o salvamento.
6. Finalize a visita normalmente.

O desenho também é salvo automaticamente a cada traço, evitando perda ao
navegar entre etapas.

## Regras

- **Finalizar visita:** exige as duas assinaturas, com nome e imagem.
- **Salvar rascunho / Salvar agora:** funciona mesmo sem assinaturas.
- **Visitas finalizadas:** exibem as assinaturas em modo somente leitura.
- **Visitas antigas:** aparecem como “não assinadas” até serem assinadas.

## Onde os dados ficam

Cada visita recebe um campo aditivo `signatures`:

```json
{
  "signatures": {
    "technical": {
      "name": "Maria Silva",
      "path": "data/photos/signatures/abc123_technical.png",
      "filename": "abc123_technical.png",
      "signed_at": "2026-11-12 10:00:00"
    },
    "evaluator": {
      "name": "João Souza",
      "path": "data/photos/signatures/abc123_evaluator.png",
      "filename": "abc123_evaluator.png",
      "signed_at": "2026-11-12 10:05:00"
    }
  }
}
```

- `technical`: Responsável Técnico.
- `evaluator`: Avaliador.
- As imagens ficam em `data/photos/signatures/` e são referenciadas pelo caminho
  no registro da visita.
- O campo é aditivo: visitas existentes continuam funcionando.

## Relatório PDF

O PDF inclui, ao final:

- as duas imagens de assinatura;
- o nome de cada signatário;
- o horário do registro;
- o aviso de que o documento não possui validade jurídica automática.

Se uma assinatura estiver ausente (por exemplo, em um rascunho exportado), o PDF
mostra **“Não assinado”** naquele campo.

## Limitações e cuidados

- O desenho é capturado pelo navegador; não há verificação biométrica.
- O nome é informado manualmente e não é validado contra um cadastro externo.
- Para validade jurídica, é necessário um processo específico de certificação
  digital, fora do escopo desta change.
- Em caso de falha ao salvar, verifique permissões de escrita em
  `data/photos/signatures/`.

## Testes

- `tests/test_visit_signatures.py`: persistência, limpeza, validação de PNG e
  regras de pendência.
- `streamlit.testing.v1.AppTest`: renderização da etapa final e dos campos.
- Geração de PDF com assinaturas validada manualmente.
