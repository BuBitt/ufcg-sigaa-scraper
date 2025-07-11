"""
Serviço de navegação no SIGAA.
"""

import logging
from playwright.sync_api import Page

from src.config.settings import Config


class NavigationService:
    """Gerencia a navegação dentro do sistema SIGAA."""
    
    def __init__(self) -> None:
        """Inicializa o serviço de navegação."""
        self.logger = logging.getLogger("navigation")
        self.logger.debug("🔧 Serviço de navegação inicializado")
    
    def navigate_to_grades(self, page: Page) -> None:
        """
        Navega para a seção de notas no SIGAA.
        
        Args:
            page: Objeto page do Playwright
        """
        self.logger.info("📍 Iniciando navegação para seção de notas")
        
        # Etapa 1: Aguardar menu principal
        self.logger.debug("⏳ Aguardando carregamento do menu principal")
        try:
            page.wait_for_selector(
                "#menu_form_menu_discente_discente_menu", 
                timeout=10000
            )
            self.logger.debug("✅ Menu principal encontrado")
        except Exception as e:
            self.logger.error(f"❌ Menu principal não encontrado: {e}")
            raise
        
        # Etapa 2: Fazer hover no menu discente
        self.logger.debug("🖱️  Fazendo hover no menu discente")
        try:
            page.locator("#menu_form_menu_discente_discente_menu").hover()
            self.logger.debug("✅ Hover realizado com sucesso")
        except Exception as e:
            self.logger.error(f"❌ Falha no hover do menu: {e}")
            raise
        
        # Etapa 3: Clicar em "Ensino"
        self.logger.debug("📚 Clicando na opção 'Ensino'")
        try:
            page.locator('span.ThemeOfficeMainFolderText:has-text("Ensino")').click(
                timeout=5000
            )
            self.logger.debug("✅ Seção 'Ensino' aberta")
        except Exception as e:
            self.logger.error(f"❌ Falha ao clicar em 'Ensino': {e}")
            raise
        
        # Etapa 4: Clicar em "Consultar Minhas Notas"
        self.logger.debug("📊 Clicando em 'Consultar Minhas Notas'")
        try:
            page.locator(
                'td.ThemeOfficeMenuItemText:has-text("Consultar Minhas Notas")'
            ).first.click(timeout=10000)
            self.logger.debug("✅ Opção 'Consultar Minhas Notas' clicada")
        except Exception as e:
            self.logger.error(f"❌ Falha ao clicar em 'Consultar Minhas Notas': {e}")
            raise
        
        # Etapa 5: Aguardar carregamento da tabela de notas
        self.logger.debug("⏳ Aguardando carregamento da tabela de notas")
        try:
            page.wait_for_selector("table.tabelaRelatorio", timeout=Config.TIMEOUT_DEFAULT)
            self.logger.debug("✅ Tabela de notas carregada")
        except Exception as e:
            self.logger.error(f"❌ Tabela de notas não carregou: {e}")
            raise
        
        # Verificação adicional: contar tabelas encontradas
        try:
            tables = page.locator("table.tabelaRelatorio")
            table_count = tables.count()
            self.logger.info(f"📊 Encontradas {table_count} tabela(s) de notas")
            
            if table_count == 0:
                self.logger.warning("⚠️  Nenhuma tabela de notas encontrada")
            
        except Exception as e:
            self.logger.warning(f"⚠️  Erro ao verificar tabelas: {e}")
        
        self.logger.info("✅ Navegação para seção de notas concluída com sucesso!")
