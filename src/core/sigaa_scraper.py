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
from src.utils.logger import (
    setup_logger, get_logger, get_performance_logger,
    log_system_info, log_environment_vars
)


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

    def __init__(self, debug_mode: bool = False) -> None:
        """
        Inicializa o scraper com todos os serviços necessários.
        
        Args:
            debug_mode: Habilita logging detalhado para desenvolvimento
        """
        # Configura logging avançado
        setup_logger(enable_debug=debug_mode)
        self.logger = get_logger("main")
        self.perf_logger = get_performance_logger()
        
        self.logger.info("🚀 Inicializando UFCG SIGAA Scraper")
        
        if debug_mode:
            self.logger.debug("🔍 Modo debug habilitado")
            log_system_info()
            log_environment_vars()
        
        # Inicializa serviços
        self.logger.debug("🔧 Inicializando serviços...")
        self.auth_service = AuthService()
        self.navigation_service = NavigationService()
        self.grade_extractor = GradeExtractor()
        self.cache_service = CacheService()
        self.comparison_service = ComparisonService()
        self.notifier = TelegramNotifier()
        self.logger.info("✅ Todos os serviços inicializados")
        
    def run(self) -> List[str]:
        """
        Executa o processo completo de scraping.
        
        Returns:
            Lista de mudanças detectadas
            
        Raises:
            Exception: Se o processo de scraping falhar
        """
        self.logger.info("🎯 Iniciando processo de scraping do SIGAA")
        self.perf_logger.start_timer("scraping_total")
        
        with sync_playwright() as playwright:
            self.logger.debug("🌐 Iniciando navegador")
            self.perf_logger.start_timer("browser_setup")
            
            browser = playwright.chromium.launch(headless=Config.HEADLESS_BROWSER)
            context = browser.new_context(
                viewport={
                    "width": Config.VIEWPORT_WIDTH, 
                    "height": Config.VIEWPORT_HEIGHT
                }
            )
            page = context.new_page()
            
            self.perf_logger.end_timer("browser_setup")
            self.logger.debug("✅ Navegador configurado")
            
            try:
                # Autenticação
                self.perf_logger.start_timer("authentication")
                self.auth_service.login(page)
                auth_time = self.perf_logger.end_timer("authentication")
                
                # Navegação para seção de notas
                self.perf_logger.start_timer("navigation")
                self.navigation_service.navigate_to_grades(page)
                nav_time = self.perf_logger.end_timer("navigation")
                
                # Extração das notas
                self.perf_logger.start_timer("extraction")
                grades = self.grade_extractor.extract_grades(page.content())
                extract_time = self.perf_logger.end_timer("extraction")
                
                if not grades:
                    self.logger.error("❌ Nenhuma nota extraída da página")
                    raise Exception("Nenhuma nota extraída da página")
                
                self.logger.info(f"📊 {len(grades)} registros de notas extraídos")
                
                # Comparação com cache
                self.perf_logger.start_timer("comparison")
                old_cache = self.cache_service.load_cache()
                new_grades = self.grade_extractor.organize_grades_by_semester(grades)
                
                changes_detected = self.comparison_service.compare_grades(old_cache, new_grades)
                comp_time = self.perf_logger.end_timer("comparison")
                
                # Atualização do cache
                self.perf_logger.start_timer("cache_save")
                self.cache_service.save_cache(grades)
                cache_time = self.perf_logger.end_timer("cache_save")
                
                # Log de performance
                total_time = self.perf_logger.end_timer("scraping_total")
                self.logger.info("📈 Resumo de Performance:")
                self.logger.info(f"   🔐 Autenticação: {auth_time:.2f}s")
                self.logger.info(f"   🧭 Navegação: {nav_time:.2f}s")
                self.logger.info(f"   📊 Extração: {extract_time:.2f}s")
                self.logger.info(f"   🔍 Comparação: {comp_time:.2f}s")
                self.logger.info(f"   💾 Cache: {cache_time:.2f}s")
                self.logger.info(f"   ⏱️  Total: {total_time:.2f}s")
                
                self.logger.info(f"🎉 Processo concluído! {len(changes_detected)} mudança(s) detectada(s)")
                return changes_detected
                
            except Exception as e:
                self.logger.error(f"💥 Erro no processo de scraping: {e}")
                self.logger.debug("🔍 Salvando screenshot para debug...")
                try:
                    page.screenshot(path="logs/error_screenshot.png")
                    self.logger.debug("📸 Screenshot salvo em logs/error_screenshot.png")
                except:
                    pass
                raise
            finally:
                self.logger.debug("🧹 Fechando navegador")
                browser.close()


def main() -> None:
    """Ponto de entrada principal da aplicação."""
    import sys
    
    # Verifica se deve rodar em modo debug
    debug_mode = "--debug" in sys.argv or "-d" in sys.argv
    
    scraper = SIGAAScraper(debug_mode=debug_mode)
    logger = get_logger("main")
    
    try:
        changes = scraper.run()
        
        print("\n" + "="*60)
        print("🎯 RESULTADO DO SCRAPING")
        print("="*60)
        
        if changes:
            print(f"✅ {len(changes)} mudança(s) detectada(s):")
            for i, change in enumerate(changes, 1):
                print(f"   {i}. {change}")
            
            logger.info("📬 Enviando notificações...")
            scraper.notifier.notify_changes(changes)
            print("📬 Notificações enviadas!")
        else:
            print("ℹ️  Nenhuma mudança detectada nas notas.")
            
        print("="*60)
        print("✅ Processo finalizado com sucesso!")
        
    except Exception as e:
        logger.error(f"💥 Erro crítico da aplicação: {e}")
        print(f"\n❌ Erro: {e}")
        print("📋 Verifique o arquivo de log para mais detalhes:")
        print(f"   {Config.LOG_FILENAME}")
        sys.exit(1)


if __name__ == "__main__":
    main()
