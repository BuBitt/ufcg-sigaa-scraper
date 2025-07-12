"""
Testes de integração para o SIGAA Scraper.
"""

import pytest
from unittest.mock import patch, MagicMock
import sys
import os

# Adicionar o projeto ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.sigaa_scraper import SIGAAScraper


class TestSIGAAScraperIntegration:
    """Testes de integração para o SIGAA Scraper."""
    
    @patch('src.core.sigaa_scraper.sync_playwright')
    @patch('src.services.auth_service.AuthService.login')
    @patch('src.services.navigation_service.NavigationService.navigate_to_grades')
    @patch('src.services.grade_extractor.GradeExtractor.extract_from_page_direct')
    @patch('src.services.cache_service.CacheService.load_cache')
    @patch('src.services.cache_service.CacheService.save_cache')
    @patch('src.services.comparison_service.ComparisonService.compare_grades')
    @patch('src.notifications.telegram_notifier.TelegramNotifier.notify_changes')
    def test_full_scraper_workflow(
        self,
        mock_telegram,
        mock_compare,
        mock_save_cache,
        mock_load_cache,
        mock_extract,
        mock_navigate,
        mock_login,
        mock_playwright
    ):
        """Testa o fluxo completo do scraper."""
        
        # Configurar mocks
        mock_playwright_context = MagicMock()
        mock_browser = MagicMock()
        mock_context = MagicMock()
        mock_page = MagicMock()
        
        mock_playwright.return_value.__enter__.return_value = mock_playwright_context
        mock_playwright_context.chromium.launch.return_value = mock_browser
        mock_browser.new_context.return_value = mock_context
        mock_context.new_page.return_value = mock_page
        
        # Configurar retornos dos serviços
        mock_login.return_value = True
        mock_navigate.return_value = True
        mock_extract.return_value = {
            "Disciplina1": [{"Nota": "8.5", "Unidade": "1"}]
        }
        mock_load_cache.return_value = {}
        mock_save_cache.return_value = True
        mock_compare.return_value = ["Nova nota: Disciplina1 - 8.5"]  # Lista de strings
        mock_telegram.return_value = True
        
        # Executar scraper
        scraper = SIGAAScraper()
        result = scraper.run()
        
        # Verificar que o resultado são as mudanças detectadas (lista de strings)
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0] == "Nova nota: Disciplina1 - 8.5"
        
        # Verificar que os serviços principais foram chamados
        mock_login.assert_called_once()
        mock_navigate.assert_called_once()
        mock_extract.assert_called_once()
        mock_load_cache.assert_called_once()
        mock_save_cache.assert_called_once()
        mock_compare.assert_called_once()
        # Nota: mock_telegram não é chamado no run(), apenas no main()
    
    @patch('src.core.sigaa_scraper.sync_playwright')
    @patch('src.services.auth_service.AuthService.login')
    def test_scraper_login_failure(self, mock_login, mock_playwright):
        """Testa comportamento quando login falha."""
        
        # Configurar playwright mock
        mock_playwright_context = MagicMock()
        mock_browser = MagicMock()
        mock_context = MagicMock()
        mock_page = MagicMock()
        
        mock_playwright.return_value.__enter__.return_value = mock_playwright_context
        mock_playwright_context.chromium.launch.return_value = mock_browser
        mock_browser.new_context.return_value = mock_context
        mock_context.new_page.return_value = mock_page
        
        # Login falha
        mock_login.return_value = False
        
        # Executar scraper e capturar exceção
        scraper = SIGAAScraper()
        
        with pytest.raises(Exception, match="Falha na autenticação"):
            scraper.run()
    
    @patch.dict('os.environ', {
        'SIGAA_USERNAME': 'testuser',
        'SIGAA_PASSWORD': 'testpass'
    })
    def test_scraper_initialization(self):
        """Testa inicialização do scraper."""
        scraper = SIGAAScraper()
        
        assert scraper is not None
        assert hasattr(scraper, 'auth_service')
        assert hasattr(scraper, 'navigation_service')
        assert hasattr(scraper, 'grade_extractor')
        assert hasattr(scraper, 'cache_service')
        assert hasattr(scraper, 'comparison_service')
        assert hasattr(scraper, 'notifier')  # Corrigido: 'notifier' ao invés de 'telegram_notifier'


class TestMainEntryPoint:
    """Testes para o ponto de entrada principal."""
    
    @patch('src.core.sigaa_scraper.main')
    def test_main_entry_point(self, mock_main):
        """Testa o ponto de entrada principal."""
        mock_main.return_value = True
        
        # Importar e executar main
        import main
        
        # Verificar que não há erro de importação
        assert main is not None
    
    @patch('src.core.sigaa_scraper.SIGAAScraper.run')
    def test_main_function(self, mock_run):
        """Testa a função main."""
        mock_run.return_value = True
        
        from src.core.sigaa_scraper import main
        
        # Redirecionar sys.exit para não terminar os testes
        with patch('sys.exit'):
            result = main()
        
        mock_run.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__])
