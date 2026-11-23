"""Catálogo configurável de equipamentos da ACN Norte.

As opções são organizadas por **categoria → marca → equipamentos**. Para
incluir uma nova marca, categoria ou identificação, basta acrescentar uma
entrada em :data:`EQUIPMENT_CATALOG`.

O catálogo contém somente as opções fornecidas pela equipe. Nenhum
equipamento é criado automaticamente a partir de planilhas, arquivos externos
ou suposições.
"""

from __future__ import annotations

from typing import Iterable

DEFAULT_CATEGORY = "Dosimetria de Ruído"

# Estrutura configurável: categoria -> marca -> lista de equipamentos.
# Cada equipamento possui um ``codigo`` interno estável e a ``identificacao``
# exibida ao técnico. O campo ``modelo`` é opcional.
EQUIPMENT_CATALOG = {
    DEFAULT_CATEGORY: {
        "Chrompack": [
            {"codigo": "CHR-2386", "identificacao": "2386"},
            {"codigo": "CHR-3440", "identificacao": "3440"},
            {"codigo": "CHR-2319", "identificacao": "2319"},
            {"codigo": "CHR-3558", "identificacao": "3558"},
            {"codigo": "CHR-5981", "identificacao": "5981"},
        ],
        "Instrutherm": [
            {
                "codigo": "INS-DOS-100X",
                "identificacao": "DOS-100X",
                "modelo": "DOS-100X",
            },
        ],
    },
}


def equipment_catalog() -> list[dict]:
    """Retorna uma cópia normalizada de todo o catálogo.

    A ordem segue a estrutura de :data:`EQUIPMENT_CATALOG`, garantindo que a
    interface e os relatórios mantenham uma ordem previsível.
    """
    catalog: list[dict] = []
    for category, brands in EQUIPMENT_CATALOG.items():
        for brand, items in brands.items():
            for item in items:
                catalog.append(
                    {
                        "codigo": str(item["codigo"]),
                        "categoria": category,
                        "marca": brand,
                        "modelo": str(item.get("modelo") or ""),
                        "identificacao": str(item["identificacao"]),
                    }
                )
    return catalog


def equipment_by_code() -> dict[str, dict]:
    """Indexa o catálogo pelo código interno do equipamento."""
    return {item["codigo"]: item for item in equipment_catalog()}


def equipment_grouped() -> dict[str, dict[str, list[dict]]]:
    """Agrupa o catálogo por categoria e marca para renderização na tela."""
    grouped: dict[str, dict[str, list[dict]]] = {}
    for item in equipment_catalog():
        grouped.setdefault(item["categoria"], {}).setdefault(item["marca"], []).append(item)
    return grouped


def equipment_label(item: dict) -> str:
    """Rótulo legível do equipamento, no formato ``Marca · Identificação``."""
    brand = str(item.get("marca") or "").strip()
    identification = str(item.get("identificacao") or "").strip()
    if brand and identification:
        return f"{brand} · {identification}"
    return identification or brand or "Equipamento"


def normalize_equipment_codes(codes: Iterable[str]) -> list[dict]:
    """Resolve códigos válidos preservando a ordem oficial do catálogo.

    Levanta :class:`ValueError` quando algum código não pertence ao catálogo,
    impedindo que opções não fornecidas pela equipe sejam gravadas.
    """
    requested = {
        str(code).strip()
        for code in (codes or [])
        if str(code).strip()
    }
    catalog = equipment_catalog()
    known = {item["codigo"] for item in catalog}
    unknown = sorted(requested - known)
    if unknown:
        raise ValueError(
            "Equipamento(s) não cadastrado(s): " + ", ".join(unknown) + "."
        )
    return [item for item in catalog if item["codigo"] in requested]
