# Captura de fotografia (upload + câmera)

## Objetivo

Permitir que todo campo de fotografia do ACNnorte aceite **upload de uma imagem
existente** ou **captura na hora** pela câmera do dispositivo que abriu o site,
com escolha entre câmera frontal e traseira.

Campos atendidos:

- **Etapa 4 — Formulário:** fotografia do funcionário avaliado.
- **Fotografias → Adicionar Fotografia:** evidências da visita.
- **Fotografias → Galeria → Substituir imagem:** troca de uma evidência.

O componente fica em `src/components/photo_capture/` e expõe:

```python
photo_input(
    label: str,
    key: str,
    allow_upload=True,
    allow_camera=True,
    default_camera="environment",
) -> bytes | None
```

## Como usar

1. Abra a visita em **Visitas Técnicas → ✍️ Preencher Visita → ETAPA 4** ou a
   página **Fotografias → 📷 Adicionar Fotografia**.
2. Escolha **📁 Carregar arquivo** para enviar uma imagem da galeria/arquivos do
   dispositivo, ou **📷 Usar câmera** para abrir a pré-visualização.
3. Na câmera, use **🔄 Usar câmera frontal/traseira** para alternar. Se houver
   mais de uma câmera, a lista de dispositivos também permite escolher.
4. Toque em **📸 Capturar**, confira a imagem e use **✅ Usar esta foto**. Se
   precisar, use **↩️ Refazer**.
5. Preencha a legenda/identificação e confirme o salvamento no formulário.

A foto é salva no mesmo local usado antes:

- `data/photos/workers/` — foto do funcionário;
- `data/photos/` — evidências da visita.

Portanto, a imagem continua aparecendo na galeria, no checklist e no PDF final
sem mudanças no `export_manager.py`.

## Requisito de HTTPS para câmera em dispositivos móveis

A API `navigator.mediaDevices.getUserMedia` exige um **contexto seguro**:

- endereço `https://...`; ou
- `http://localhost` / `http://127.0.0.1` no próprio computador.

Em celular/tablet acessando o servidor por **HTTP em rede local** (por exemplo
`http://192.168.0.10:8501`), o navegador bloqueia a câmera. Nesse cenário:

- o componente mostra uma mensagem clara sobre HTTPS;
- o upload de arquivo continua funcionando;
- são oferecidos `st.camera_input` e `st.file_uploader` como alternativa.

Para usar a câmera em campo, publique o aplicativo em HTTPS (proxy reverso,
Streamlit Community Cloud, servidor com certificado etc.) ou use um túnel HTTPS.

## Permissões e erros tratados

| Situação | Mensagem/alternativa |
| --- | --- |
| Permissão negada | Orienta autorizar no navegador ou usar upload. |
| Nenhuma câmera encontrada | Orienta usar upload. |
| Câmera em uso por outro app | Pede fechar o outro aplicativo ou usar upload. |
| HTTP sem HTTPS | Explica o requisito de HTTPS/localhost e oferece upload. |
| Navegador sem suporte | Oferece upload e câmera nativa quando disponível. |

## Privacidade e validação

- Nenhuma imagem é enviada a terceiros: o fluxo é navegador → servidor local.
- O stream é encerrado com `track.stop()` ao capturar, trocar de aba ou
  desmontar o componente.
- No cliente, o maior lado é limitado a **1600 px** e o JPEG usa qualidade
  aproximada de **0.85**.
- No servidor, o Pillow valida **JPG/PNG/WEBP**, limite de **10 MB**, corrige a
  orientação EXIF e converte tudo para **JPEG normalizado** antes de gravar.
- O salvamento continua local-first, com o `xano_sync` em modo best-effort.

## Estado e concorrência

Cada campo usa uma `key` própria. O componente deriva dessa chave as entradas de
`st.session_state` (foto confirmada, hash, cache de bytes, nonce de fallback e
token de reinício), evitando colisão entre vários campos de foto na mesma tela.

Após salvar, `clear_photo_input(key)` reinicia o componente para o próximo uso.

## Testes

`tests/test_photo_capture.py` cobre:

- formatos válidos e inválidos, limite de tamanho e conversão para JPEG;
- correção de orientação EXIF e redimensionamento;
- retorno `None` quando nenhuma imagem é fornecida;
- fallback de câmera por contexto seguro/dispositivos;
- salvamento da foto do funcionário e de evidências via `storage_manager`;
- compatibilidade com chamadas legadas sem validação estrita.
