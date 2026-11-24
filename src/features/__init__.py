"""Feature packages (extensões modulares).

Este pacote é o registro central das extensões carregadas pelo orquestrador
``src.main``. As implementações permanecem em seus módulos de origem; aqui
apenas declaramos os pontos de entrada para que a aplicação possa inicializá-las
sem conhecer os detalhes de cada funcionalidade.
"""

from importlib import import_module

# Nome lógico -> módulo Python responsável. A ordem segue o fluxo da visita.
FEATURE_MODULES = {
    "temperature": "src.features.visit_enhancements.temperature.temperature_service",
    "signatures": "src.features.visit_enhancements.signatures.signature_service",
    "equipment": "src.features.visit_enhancements.equipment.equipment_selector",
    "visit_form_flow": "src.features.visit_enhancements.visit_form.visit_form_flow",
    "photographs": "src.features.visit_enhancements.photographs.photo_manager",
    "reports": "src.features.visit_enhancements.reports.report_extensions",
    "integration": "src.features.visit_enhancements.integration.visit_integration",
}

__all__ = ["FEATURE_MODULES", "available_features", "initialize_features"]


def available_features() -> dict[str, str]:
    """Devolve uma cópia do registro de módulos de extensão."""
    return dict(FEATURE_MODULES)


def initialize_features() -> dict[str, object]:
    """Importa todas as extensões e devolve ``nome -> módulo``.

    O ``src.main`` chama esta função durante a inicialização para que falhas de
    import sejam detectadas já na abertura do sistema. Os imports são
    idempotentes (cache do Python), portanto chamadas em reruns não recriam
    módulos, conexões ou estado.
    """
    return {name: import_module(path) for name, path in FEATURE_MODULES.items()}
