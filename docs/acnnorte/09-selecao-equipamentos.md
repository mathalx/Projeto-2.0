# Seleção dos Equipamentos de Dosimetria de Ruído (CHANGE 05)

## Objetivo

Substituir o preenchimento manual da identificação do equipamento por botões
selecionáveis, com destaque visual para as opções escolhidas. O técnico pode
selecionar **mais de um equipamento**, e cada identificação fica vinculada à
visita e à sua respectiva medição.

## Opções cadastradas

As opções abaixo foram fornecidas pela equipe. Nenhum outro modelo, marca ou
identificação é cadastrado automaticamente.

| Categoria | Marca | Identificação |
| --- | --- | --- |
| Dosimetria de Ruído | Chrompack | 2386 |
| Dosimetria de Ruído | Chrompack | 3440 |
| Dosimetria de Ruído | Chrompack | 2319 |
| Dosimetria de Ruído | Chrompack | 3558 |
| Dosimetria de Ruído | Chrompack | 5981 |
| Dosimetria de Ruído | Instrutherm | DOS-100X |

## Como usar

1. Abra a visita em **Visitas Técnicas → ✍️ Preencher Visita**.
2. Avance até a etapa **“Dosimetria de Ruído — equipamentos utilizados”**.
3. Toque nos botões das identificações utilizadas:
   - o botão fica **verde** quando selecionado;
   - toque novamente para desmarcar;
   - é possível selecionar vários equipamentos.
4. Confira os cartões em **“✅ Equipamentos selecionados”**. Cada cartão mostra
   a marca, a identificação e a **medição vinculada**.
5. Avance para a etapa final normalmente.

A seleção é salva imediatamente a cada toque, sem depender do botão
“Salvar agora”.

## Regras

- **Finalizar visita:** exige pelo menos um equipamento de Dosimetria de Ruído.
- **Salvar rascunho / Salvar agora:** funciona mesmo sem equipamento
  selecionado.
- **Visitas finalizadas:** exibem a seleção em modo somente leitura.
- **Visitas antigas:** continuam abrindo normalmente; a etapa mostra “nenhum
  equipamento selecionado” até que o técnico faça a seleção.

## Onde os dados ficam

Cada visita recebe dois campos aditivos:

```json
{
  "equipment": {
    "category": "Dosimetria de Ruído",
    "selected": [
      {
        "codigo": "CHR-2386",
        "categoria": "Dosimetria de Ruído",
        "marca": "Chrompack",
        "modelo": "",
        "identificacao": "2386",
        "measurement_id": "meas_CHR-2386"
      }
    ]
  },
  "measurements": [
    {
      "id": "meas_CHR-2386",
      "category": "Dosimetria de Ruído",
      "equipment_code": "CHR-2386",
      "equipment_brand": "Chrompack",
      "equipment_model": "",
      "equipment_identification": "2386",
      "created_at": "2026-11-12 10:00:00"
    }
  ]
}
```

- `equipment.selected`: equipamentos escolhidos, na ordem oficial do catálogo.
- `measurements`: um registro de medição para cada equipamento selecionado.
- `measurement_id` liga o equipamento à sua medição; `equipment_code` faz o
  caminho inverso.
- Os campos são aditivos: visitas existentes continuam funcionando.

## Catálogo configurável

As opções ficam em `src/equipment_catalog.py`, na estrutura
`EQUIPMENT_CATALOG`:

```python
EQUIPMENT_CATALOG = {
    "Dosimetria de Ruído": {
        "Chrompack": [
            {"codigo": "CHR-2386", "identificacao": "2386"},
            # ...
        ],
        "Instrutherm": [
            {"codigo": "INS-DOS-100X", "identificacao": "DOS-100X"},
        ],
    }
}
```

Para incluir uma nova marca, categoria ou equipamento, acrescente uma entrada
nessa estrutura. O código interno (`codigo`) deve ser único. Não é necessário
alterar a tela nem o armazenamento.

Códigos fora do catálogo são rejeitados pela camada de persistência, evitando
que opções não fornecidas pela equipe sejam gravadas.

## Relatório PDF e Excel

- O PDF inclui a seção **“Equipamentos Utilizados — Dosimetria de Ruído”** com
  categoria, marca, identificação e número da medição.
- A planilha de visitas inclui as colunas **Qtd Equipamentos (Dosimetria)**,
  **Equipamentos (Dosimetria de Ruído)** e **Medições Vinculadas**.

## Compatibilidade

Visitas antigas que ainda usam o campo `devices` são lidas como compatibilidade:
o sistema tenta relacionar a identificação antiga (por exemplo, `03440`) com a
opção correspondente do catálogo atual (`3440`). A conversão só é gravada quando
o técnico salva uma nova seleção.

## Testes

- `tests/test_visit_equipment.py`: catálogo, seleção múltipla, vínculo com
  medições, remoção de equipamentos desmarcados, códigos inválidos e
  compatibilidade com `devices`.
- `tests/test_storage_manager.py`: geração de PDF e Excel com equipamentos.
- `streamlit.testing.v1.AppTest`: renderização da etapa, clique/deseleção dos
  botões e bloqueio da finalização sem equipamento.
