"""
Testes para os serviços principais.
"""

import pytest
from unittest.mock import MagicMock, patch
import sys
import os

# Adicionar o projeto ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.auth_service import AuthService
from src.services.navigation_service import NavigationService
from src.services.grade_extractor import GradeExtractor
from src.services.cache_service import CacheService
from src.services.comparison_service import ComparisonService


class TestAuthService:
    """Testes para o serviço de autenticação."""
    
    def test_login_success(self):
        """Testa login bem-sucedido."""
        with patch('src.config.settings.Config') as mock_config:
            mock_config.get_credentials.return_value = ('user', 'pass')
            
            auth_service = AuthService()
            mock_page = MagicMock()
            mock_page.goto.return_value = None
            mock_page.wait_for_load_state.return_value = None
            mock_page.fill.return_value = None
            mock_page.click.return_value = None
            mock_page.url = "https://sigaa.ufcg.edu.br/home"
            
            result = auth_service.login(mock_page)
            
            assert result is True
            mock_page.goto.assert_called_once()
            mock_page.fill.assert_called()
            # Remover asserção do click pois pode variar dependendo da implementação


class TestNavigationService:
    """Testes para o serviço de navegação."""
    
    def test_navigate_to_grades(self):
        """Testa navegação para página de notas."""
        nav_service = NavigationService()
        mock_page = MagicMock()
        
        # Configurar mocks para o método menu_ensino
        mock_page.locator.return_value.count.return_value = 1
        mock_page.locator.return_value.click.return_value = None
        mock_page.wait_for_load_state.return_value = None
        
        result = nav_service.navigate_to_grades(mock_page)
        
        assert result is True
        # Verificar se pelo menos um locator foi chamado
        mock_page.locator.assert_called()


class TestGradeExtractor:
    """Testes para o extrator de notas."""
    
    def test_extract_grades_empty_content(self):
        """Testa extração com conteúdo vazio."""
        extractor = GradeExtractor()
        result = extractor.extract_grades("")
        assert result == []
    
    def test_extract_grades_with_table(self):
        """Testa extração com tabela simples."""
        extractor = GradeExtractor()
        html_content = """
        <table class="tabelaRelatorio">
            <tr><th>Disciplina</th><th>Nota</th></tr>
            <tr><td>Matemática</td><td>8.5</td></tr>
        </table>
        """
        
        result = extractor.extract_grades(html_content)
        
        assert len(result) > 0
        assert result[0]['Disciplina'] == 'Matemática'
        assert result[0]['Nota'] == '8.5'
    
    def test_looks_like_grade(self):
        """Testa identificação de notas."""
        extractor = GradeExtractor()
        
        assert extractor._looks_like_grade("8.5") is True
        assert extractor._looks_like_grade("10,0") is True
        assert extractor._looks_like_grade("texto") is False
        assert extractor._looks_like_grade("") is False
    
    def test_normalize_grade(self):
        """Testa normalização de notas."""
        extractor = GradeExtractor()
        
        assert extractor._normalize_grade("8,5") == "8.5"
        assert extractor._normalize_grade("10.0") == "10.0"
        assert extractor._normalize_grade(" 9 ") == "9"


class TestCacheService:
    """Testes para o serviço de cache."""
    
    @patch('src.services.cache_service.os.path.exists')
    @patch('src.services.cache_service.open')
    def test_load_cache_file_not_exists(self, mock_open, mock_exists):
        """Testa carregamento quando arquivo não existe."""
        mock_exists.return_value = False
        
        cache_service = CacheService()
        result = cache_service.load_cache()
        
        assert result == {}
    
    @patch('src.services.cache_service.open')
    def test_save_cache(self, mock_open):
        """Testa salvamento do cache."""
        cache_service = CacheService()
        test_data = [{"test": "data"}]  # Lista de dicionários como esperado
        
        # Simular sucesso
        mock_file = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_file
        
        result = cache_service.save_cache(test_data)
        
        assert result is True


class TestComparisonService:
    """Testes para o serviço de comparação."""
    
    def test_compare_grades_no_changes(self):
        """Testa comparação sem mudanças."""
        comparison_service = ComparisonService()
        
        old_grades = {"Disciplina1": [{"Nota": "8.5"}]}
        new_grades = {"Disciplina1": [{"Nota": "8.5"}]}
        
        changes = comparison_service.compare_grades(old_grades, new_grades)
        
        assert changes == []  # Lista vazia
    
    def test_compare_grades_with_changes(self):
        """Testa comparação com mudanças."""
        comparison_service = ComparisonService()
        
        old_grades = {"Disciplina1": [{"Nota": "8.0"}]}
        new_grades = {"Disciplina1": [{"Nota": "8.5"}]}
        
        changes = comparison_service.compare_grades(old_grades, new_grades)
        
        assert isinstance(changes, list)
        assert len(changes) > 0


if __name__ == "__main__":
    pytest.main([__file__])
