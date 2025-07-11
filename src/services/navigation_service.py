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
        
        # Otimização: timeout menor para menu principal (normalmente carrega rápido)
        page.wait_for_selector(
            "#menu_form_menu_discente_discente_menu", 
            timeout=10000  # Reduzido de TIMEOUT_DEFAULT para 10s
        )
        page.locator("#menu_form_menu_discente_discente_menu").hover()
        
        # Clica em Ensino
        page.locator('span.ThemeOfficeMainFolderText:has-text("Ensino")').click(
            timeout=5000  # Reduzido para 5s - menu já está aberto
        )
        
        # Clica em Consultar Minhas Notas
        page.locator(
            'td.ThemeOfficeMenuItemText:has-text("Consultar Minhas Notas")'
        ).first.click(timeout=10000)  # Reduzido de 15000 para 10000
        
        # Aguarda carregamento da tabela de notas
        page.wait_for_selector("table.tabelaRelatorio", timeout=Config.TIMEOUT_DEFAULT)
        
        logging.info("Navegação para seção de notas concluída")
