"""
Serviço de navegação no SIGAA com suporte a múltiplos métodos de extração.
"""

import time
from typing import Dict, Any, List, Set

from playwright.sync_api import Page

from src.config.settings import Config
from src.utils.logger import get_logger


class NavigationService:
    """Gerencia a navegação dentro do sistema SIGAA."""
    
    def __init__(self) -> None:
        """Inicializa o serviço de navegação."""
        self.logger = get_logger("navigation")
        self.logger.debug("🔧 Serviço de navegação inicializado")
    
    def navigate_to_grades(self, page: Page) -> bool:
        """
        Navega para a seção de notas usando o método configurado.
        
        Args:
            page: Objeto page do Playwright
            
        Returns:
            bool: True se navegação foi bem-sucedida
        """
        method = Config.get_extraction_method()
        
        self.logger.info(f"📍 Navegando para notas usando método: {method}")
        
        if method == "menu_ensino":
            return self._navigate_via_menu_ensino(page)
        else:  # materia_individual
            return self._navigate_via_materia_individual(page)
    
    def _navigate_via_menu_ensino(self, page: Page) -> bool:
        """
        Navega via menu Ensino > Consultar Minhas Notas.
        
        Args:
            page: Página do navegador
            
        Returns:
            bool: True se navegação foi bem-sucedida
        """
        try:
            self.logger.info("📚 Usando método Menu Ensino > Consultar Minhas Notas")
            
            # Etapa 1: Aguardar menu principal
            self.logger.debug("⏳ Aguardando carregamento do menu principal")
            page.wait_for_selector("#menu_form_menu_discente_discente_menu", timeout=10000)
            self.logger.debug("✅ Menu principal encontrado")
            
            # Etapa 2: Fazer hover no menu discente
            self.logger.debug("🖱️  Fazendo hover no menu discente")
            page.locator("#menu_form_menu_discente_discente_menu").hover()
            time.sleep(0.5)  # Aguardar expansão do menu
            
            # Etapa 3: Clicar em "Ensino"
            self.logger.debug("📚 Clicando na opção 'Ensino'")
            page.locator('span.ThemeOfficeMainFolderText:has-text("Ensino")').click(timeout=5000)
            time.sleep(0.5)  # Aguardar expansão do submenu
            
            # Etapa 4: Clicar em "Consultar Minhas Notas"
            self.logger.debug("📊 Clicando em 'Consultar Minhas Notas'")
            page.locator('td.ThemeOfficeMenuItemText:has-text("Consultar Minhas Notas")').first.click(timeout=10000)
            
            # Etapa 5: Aguardar carregamento da tabela de notas
            self.logger.debug("⏳ Aguardando carregamento da tabela de notas")
            page.wait_for_selector("table.tabelaRelatorio", timeout=Config.TIMEOUT_DEFAULT)
            
            # Verificar tabelas encontradas
            tables = page.locator("table.tabelaRelatorio")
            table_count = tables.count()
            self.logger.info(f"📊 Encontradas {table_count} tabela(s) de notas")
            
            if table_count == 0:
                self.logger.warning("⚠️  Nenhuma tabela de notas encontrada")
                return False
            
            self.logger.info("✅ Navegação via menu concluída com sucesso!")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Erro na navegação via menu ensino: {e}", exc_info=True)
            return False
    
    def _navigate_via_materia_individual(self, page: Page) -> bool:
        """
        Prepara navegação via matéria individual (método original).
        
        Args:
            page: Página do navegador
            
        Returns:
            bool: True se preparação foi bem-sucedida
        """
        try:
            self.logger.info("🎯 Usando método Matéria Individual")
            
            # Aguardar carregamento da página principal
            self.logger.debug("⏳ Aguardando carregamento da página principal")
            page.wait_for_load_state("networkidle", timeout=Config.TIMEOUT_DEFAULT)
            
            # Verificar se há componentes curriculares disponíveis
            component_selector = "tbody tr td.descricao a"
            page.wait_for_selector(component_selector, timeout=Config.TIMEOUT_DEFAULT)
            
            components = page.locator(component_selector)
            component_count = components.count()
            
            self.logger.info(f"📋 Encontrados {component_count} componente(s) curricular(es)")
            
            if component_count == 0:
                self.logger.warning("⚠️  Nenhum componente curricular encontrado")
                return False
            
            self.logger.info("✅ Preparação para navegação individual concluída!")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Erro na preparação para navegação individual: {e}", exc_info=True)
            return False
    
    def get_available_components(self, page: Page) -> List[str]:
        """
        Obtém lista de componentes curriculares disponíveis.
        
        Args:
            page: Página do navegador
            
        Returns:
            List[str]: Lista de nomes dos componentes
        """
        try:
            component_selector = "tbody tr td.descricao a"
            components = page.locator(component_selector)
            component_count = components.count()
            
            component_names = []
            for i in range(component_count):
                name = components.nth(i).text_content()
                if name:
                    component_names.append(name.strip())
            
            self.logger.info(f"📋 Componentes disponíveis: {len(component_names)}")
            return component_names
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao obter componentes: {e}")
            return []
    
    def navigate_to_component_grades(self, page: Page, component_index: int) -> bool:
        """
        Navega para as notas de um componente específico.
        
        Args:
            page: Página do navegador
            component_index: Índice do componente (0-based)
            
        Returns:
            bool: True se navegação foi bem-sucedida
        """
        try:
            self.logger.debug(f"🎯 Navegando para componente {component_index + 1}")
            
            # Clicar no componente
            component_selector = "tbody tr td.descricao a"
            components = page.locator(component_selector)
            
            if component_index >= components.count():
                self.logger.error(f"❌ Índice de componente inválido: {component_index}")
                return False
            
            components.nth(component_index).click()
            time.sleep(2)  # Aguardar carregamento
            
            # Verificar se menu "Alunos" está presente
            alunos_menu = "div.itemMenuHeaderAlunos"
            if page.locator(alunos_menu).count() == 0:
                self.logger.warning("⚠️  Menu 'Alunos' não encontrado")
                return False
            
            # Expandir menu "Alunos"
            self.logger.debug("📂 Expandindo menu 'Alunos'")
            page.locator(alunos_menu).first.click()
            time.sleep(2)  # Aguardar expansão
            
            # Clicar em "Ver Notas"
            ver_notas_selectors = [
                "div.itemMenuHeaderAlunos + div a:has-text('Ver Notas')",
                "a:has-text('Ver Notas')",
                "a[onclick*='verNotas']"
            ]
            
            clicked = False
            for selector in ver_notas_selectors:
                try:
                    if page.locator(selector).count() > 0:
                        self.logger.debug(f"🎯 Clicando em 'Ver Notas' usando: {selector}")
                        page.locator(selector).first.click()
                        clicked = True
                        break
                except:
                    continue
            
            if not clicked:
                self.logger.error("❌ Não foi possível clicar em 'Ver Notas'")
                return False
            
            # Aguardar carregamento da página de notas
            time.sleep(2)
            self.logger.debug("✅ Navegação para componente concluída")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Erro na navegação para componente: {e}", exc_info=True)
            return False
    
    def go_back_to_main(self, page: Page) -> bool:
        """
        Volta para a página principal.
        
        Args:
            page: Página do navegador
            
        Returns:
            bool: True se navegação foi bem-sucedida
        """
        try:
            self.logger.debug("🔙 Voltando para página principal")
            
            # Tentar navegar via Portal Discente
            portal_selectors = [
                "a:has-text('Portal Discente')",
                "span:has-text('Portal Discente')"
            ]
            
            for selector in portal_selectors:
                try:
                    if page.locator(selector).count() > 0:
                        page.locator(selector).first.click()
                        page.wait_for_load_state("networkidle", timeout=Config.TIMEOUT_DEFAULT)
                        self.logger.debug("✅ Retorno via Portal Discente")
                        return True
                except:
                    continue
            
            # Fallback: navegar diretamente via URL
            page.goto(Config.SIGAA_URL + "/verPortalDiscente.do")
            page.wait_for_load_state("networkidle", timeout=Config.TIMEOUT_DEFAULT)
            self.logger.debug("✅ Retorno via URL direta")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao voltar para página principal: {e}")
            return False
