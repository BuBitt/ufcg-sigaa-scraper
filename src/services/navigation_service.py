"""
Serviço de navegação no SIGAA.
"""

import logging
from playwright.sync_api import Page

from src.config.settings import Config


class NavigationService:
    """Gerencia a navegação dentro do sistema SIGAA."""
    
    def navigate_to_grades(self, page: Page) -> None:
        """
        Navega para a seção de notas no SIGAA.
        
        Args:
            page: Objeto page do Playwright
        """
        logging.info("Navegando para seção de notas")
        page.wait_for_selector(
            "#menu_form_menu_discente_discente_menu", 
            timeout=Config.TIMEOUT_DEFAULT
        )
        page.locator("#menu_form_menu_discente_discente_menu").hover()
        page.locator('span.ThemeOfficeMainFolderText:has-text("Ensino")').click(
            timeout=Config.TIMEOUT_DEFAULT
        )
        page.locator(
            'td.ThemeOfficeMenuItemText:has-text("Consultar Minhas Notas")'
        ).first.click(timeout=15000)
        page.wait_for_selector("table.tabelaRelatorio", timeout=Config.TIMEOUT_DEFAULT)
        
        logging.info("Navegação para seção de notas concluída")
