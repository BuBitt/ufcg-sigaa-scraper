"""
Módulo principal do SIGAA Scraper.

Este módulo contém a classe principal que coordena o processo de scraping
das notas do SIGAA da UFCG.
"""

import logging
from typing import Dict, List

from playwright.sync_api import Playwright, sync_playwright

from src.config.settings import Config
from src.services.auth_service import AuthService
from src.services.navigation_service import NavigationService
from src.services.grade_extractor import GradeExtractor
from src.services.cache_service import CacheService
from src.services.comparison_service import ComparisonService
from src.notifications.telegram_notifier import TelegramNotifier
from src.utils.logger import setup_logger


class SIGAAScraper:
    """
    Classe principal do scraper para extração e monitoramento de notas do UFCG SIGAA.
    
    Coordena todos os serviços necessários para o processo completo de:
    - Autenticação no SIGAA
    - Navegação para seção de notas
    - Extração dos dados
    - Comparação com cache
    - Notificação de mudanças
    """

    def __init__(self) -> None:
        """Inicializa o scraper com todos os serviços necessários."""
        setup_logger()
        self.config = Config()
        self.auth_service = AuthService()
        self.navigation_service = NavigationService()
        self.grade_extractor = GradeExtractor()
        self.cache_service = CacheService()
        self.comparison_service = ComparisonService()
        self.notifier = TelegramNotifier()
        
    def run(self) -> List[str]:
        """
        Executa o processo completo de scraping.
        
        Returns:
            Lista de mudanças detectadas
            
        Raises:
            Exception: Se o processo de scraping falhar
        """
        logging.info("Iniciando processo de scraping do SIGAA")
        
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=self.config.HEADLESS_BROWSER)
            context = browser.new_context(
                viewport={
                    "width": self.config.VIEWPORT_WIDTH, 
                    "height": self.config.VIEWPORT_HEIGHT
                }
            )
            page = context.new_page()
            
            try:
                # Autenticação
                self.auth_service.login(page)
                
                # Navegação para seção de notas
                self.navigation_service.navigate_to_grades(page)
                
                # Extração das notas
                grades = self.grade_extractor.extract_grades(page.content())
                
                if not grades:
                    raise Exception("Nenhuma nota extraída da página")
                
                # Comparação com cache
                old_cache = self.cache_service.load_cache()
                new_grades = self.grade_extractor.organize_grades_by_semester(grades)
                
                changes_detected = self.comparison_service.compare_grades(old_cache, new_grades)
                
                # Atualização do cache
                self.cache_service.save_cache(grades)
                
                logging.info(f"Processo concluído. {len(changes_detected)} mudanças detectadas")
                return changes_detected
                
            except Exception as e:
                logging.error(f"Erro no processo de scraping: {e}")
                raise
            finally:
                browser.close()


def main() -> None:
    """Ponto de entrada principal da aplicação."""
    scraper = SIGAAScraper()
    
    try:
        changes = scraper.run()
        
        print("\nMudanças detectadas:")
        if changes:
            for change in changes:
                print(f"- {change}")
            scraper.notifier.notify_changes(changes)
        else:
            print("- Nenhuma mudança detectada.")
            
    except Exception as e:
        logging.error(f"Erro da aplicação: {e}")
        print(f"Erro: {e}")


if __name__ == "__main__":
    main()
