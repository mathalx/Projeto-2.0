# Design: Assinaturas Obrigatórias

## Fluxo

1. A etapa final da visita exibe a seção **“Assinaturas obrigatórias”**.
2. Para cada papel, o técnico informa o nome e desenha a assinatura no canvas.
3. O componente `acnnorte_signature_pad` exporta o desenho como PNG (data URL).
4. O callback do componente grava o PNG em `data/photos/signatures/` e atualiza
   o registro `signatures` da visita.
5. Ao finalizar, o sistema verifica se as duas assinaturas têm nome e arquivo.
6. O PDF inclui as imagens, os nomes, os horários e o aviso de que o registro
   não possui validade jurídica automática.

## Modelo de dados

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

- `technical`: assinatura do Responsável Técnico.
- `evaluator`: assinatura do Avaliador.
- O campo é aditivo; visitas antigas são tratadas como “não assinadas”.

## Decisões

- **Obrigatório apenas para finalizar:** o rascunho pode ser salvo a qualquer
  momento, permitindo que a assinatura seja coletada depois.
- **Persistência imediata:** cada alteração no canvas é salva, evitando perda do
  desenho ao navegar entre etapas.
- **Sem validade jurídica automática:** a interface e o PDF deixam claro que se
  trata de registro eletrônico, não de certificação digital.
- **Arquivo PNG transparente:** o canvas exporta somente o traço, facilitando a
  leitura no PDF e a reidratação ao retornar à visita.
- **Sem dependências externas:** o desenho usa Pointer Events, compatível com
  mouse e toque, sem bibliotecas de terceiros.
