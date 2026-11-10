"""Constantes e contratos visuais do fluxo de inspeção de campo (v2).

O módulo isola o novo fluxo sem alterar as chaves de navegação e os formatos
de dados usados pelo restante do aplicativo. Todas as páginas continuam sendo
renderizadas pelos mesmos roteadores já existentes.
"""

from __future__ import annotations

from dataclasses import dataclass

from src.ui_components import (
    CLIENTS_TAB_NEW,
    PAGE_ADMIN,
    PAGE_CLIENTS,
    PAGE_DASHBOARD,
    PAGE_FORM,
    PAGE_PHOTOS,
    PAGE_PROFILE,
    PAGE_REPORTS,
    PAGE_VISITS,
    PHOTOS_TAB_TODAY,
)

APP_TITLE = "ACNnorte — Inspeções de Campo"
FORM_SUBTITLE = "Avaliação de Segurança do Trabalho"
WORKER_PHOTO_EXTENSIONS = ["jpg", "jpeg", "png", "webp"]
IMAGE_EXTENSIONS = ["jpg", "jpeg", "png", "webp"]

# Perfil ativo exibido no menu lateral. O usuário administrador padrão do
# projeto é a Ana.norte (data/users.json). O fluxo continua sem autenticação,
# apenas apresenta o perfil ativo da sessão.
DEFAULT_USERNAME = "Ana.norte"
DEFAULT_ROLE = "Administrador"

GALLERY_FAB_KEY = "gallery_fab"


@dataclass(frozen=True)
class NavItem:
    """Item do menu lateral em blocos."""

    icon: str
    label: str
    page: str
    description: str
    quick: bool = False
    create_inspection: bool = False
    extra_state: tuple[tuple[str, str], ...] = ()


# Estrutura visual solicitada para o Layout ACN Norte.
NAV_GROUPS: tuple[tuple[str, tuple[NavItem, ...]], ...] = (
    (
        "Navegação",
        (
            NavItem("🏠", "Painel Inicial", PAGE_DASHBOARD, "Visão geral e indicadores"),
            NavItem("👥", "Clientes", PAGE_CLIENTS, "Cadastro e consulta de empresas"),
            NavItem(
                "📋",
                "Visitas Técnicas / Inspeções de Campo",
                PAGE_FORM,
                "Formulário principal de inspeção em campo",
            ),
            NavItem(
                "📷",
                "Fotografias (Galeria de Fotos do Dia)",
                PAGE_PHOTOS,
                "Galeria do dia e fotos das visitas",
                extra_state=(("photos_tab", PHOTOS_TAB_TODAY),),
            ),
            NavItem(
                "📊",
                "Relatórios & Exportação",
                PAGE_REPORTS,
                "Laudos PDF e planilhas Excel",
            ),
        ),
    ),
    (
        "Acesso rápido",
        (
            NavItem(
                "➕",
                "Cadastrar Cliente",
                PAGE_CLIENTS,
                "Abrir o cadastro de uma nova empresa",
                quick=True,
                extra_state=(("clients_tab", CLIENTS_TAB_NEW),),
            ),
            NavItem(
                "🚀",
                "Nova Visita / Nova Inspeção",
                PAGE_FORM,
                "Criar uma nova inspeção e abrir o formulário",
                quick=True,
                create_inspection=True,
            ),
        ),
    ),
)

# Páginas legadas mantidas acessíveis para preservar todas as regras e rotinas
# já existentes (lista de visitas, senha e administração).
SECONDARY_NAV_ITEMS: tuple[NavItem, ...] = (
    NavItem("🗂️", "Visitas registradas", PAGE_VISITS, "Lista completa de visitas"),
    NavItem("🔑", "Alterar senha", PAGE_PROFILE, "Perfil e segurança"),
)

ADMIN_NAV_ITEM = NavItem(
    "⚙️", "Gerenciar usuários", PAGE_ADMIN, "Gestão de usuários (administrador)"
)
