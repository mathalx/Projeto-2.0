# Captura de fotografia (upload + câmera)

Componente reutilizável para todos os campos de fotografia do ACNnorte.

## Uso

```python
from src.components.photo_capture import clear_photo_input, photo_input

photo_bytes = photo_input(
    "Fotografia do funcionário",
    key=f"worker_photo_input_{visit_id}",
    allow_upload=True,
    allow_camera=True,
    default_camera="environment",  # "environment" (traseira) ou "user" (frontal)
)

if photo_bytes is not None:
    ok, path, message = save_worker_photo(
        visit_id, photo_bytes, "funcionario.jpg", validate_photo=True
    )
    if ok:
        clear_photo_input(f"worker_photo_input_{visit_id}")
```

`photo_input` devolve `bytes` JPEG normalizados somente depois que o usuário
confirma **“Usar esta foto”**. Enquanto nada for selecionado, devolve `None`.
Use uma `key` diferente para cada campo na mesma tela.

## Interface

- Aba **📁 Carregar arquivo**: JPG, PNG ou WEBP de até 10 MB.
- Aba **📷 Usar câmera**: pré-visualização ao vivo, captura, refazer e confirmação.
- Alternância entre **câmera frontal** (`facingMode: "user"`) e **traseira**
  (`facingMode: "environment"`), com lista de câmeras quando há mais de uma.
- No cliente, o maior lado é limitado a 1600 px e o JPEG é gerado com qualidade
  aproximada de 0.85. No servidor, o Pillow valida o formato/tamanho, corrige a
  orientação EXIF e normaliza tudo para JPEG.

## Permissões e HTTPS

A API `getUserMedia` só funciona em **contexto seguro**:

- `https://...`; ou
- `http://localhost` / `http://127.0.0.1`.

Em uma rede local acessada por HTTP (por exemplo `http://192.168.0.10:8501`), o
navegador bloqueia a câmera. Nesse caso o componente mostra uma mensagem e
oferece `st.camera_input` e `st.file_uploader` como alternativa.

O usuário precisa autorizar a câmera no navegador. Se negar, usar outro
aplicativo ou não houver câmera, a interface exibe uma mensagem em português e
mantém o upload disponível.

## Privacidade e limitações

- A imagem não é enviada a terceiros; o fluxo é navegador → servidor Streamlit.
- O stream da câmera é encerrado com `track.stop()` ao capturar, trocar de aba
  ou desmontar o componente.
- O componente não controla a qualidade do sensor nem a iluminação do local.
- Em navegadores muito antigos, a captura pode não estar disponível; use upload.
- Em dispositivos sem câmera traseira, o componente tenta a frontal
  automaticamente.

## Arquivos

| Arquivo | Responsabilidade |
| --- | --- |
| `__init__.py` | Exporta `photo_input`, `clear_photo_input` e helpers. |
| `photo_capture.py` | Validação/normalização Pillow e integração Streamlit. |
| `camera_component.html` | Marcação HTML do componente. |
| `tests/test_photo_capture.py` | Testes de validação, fallback e persistência. |
