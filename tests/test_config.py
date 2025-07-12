"""
Testes para configuração e utilitários.
"""

import pytest
from unittest.mock import patch, MagicMock
import sys
import os

# Adicionar o projeto ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config.settings import Config
from src.utils.logger import get_logger, PerformanceLogger


class TestConfig:
    """Testes para a classe de configuração."""
    
    def test_config_constants(self):
        """Testa constantes da configuração."""
        assert Config.VERSION == "2.0.0"
        assert Config.APP_NAME == "SIGAA Grade Scraper"
        assert Config.HEADLESS_BROWSER is True
        assert Config.TIMEOUT_DEFAULT == 45000  # Atualizado para 45s
    
    def test_config_extraction_method(self):
        """Testa método de extração padrão."""
        method = Config.get_extraction_method()
        assert method in ['menu_ensino', 'materia_individual']
    
    @patch.dict('os.environ', {'EXTRACTION_METHOD': 'menu_ensino'})
    def test_config_extraction_method_env(self):
        """Testa método de extração via variável de ambiente."""
        method = Config.get_extraction_method()
        assert method == 'menu_ensino'
    
    @patch.dict('os.environ', {'EXTRACTION_METHOD': 'invalid_method'})
    def test_config_extraction_method_invalid(self):
        """Testa comportamento com método inválido."""
        method = Config.get_extraction_method()
        assert method == 'menu_ensino'  # Deve retornar padrão
    
    def test_config_ensure_directories(self):
        """Testa criação de diretórios."""
        # Não deve gerar erro
        Config.ensure_directories()


class TestLogger:
    """Testes para o sistema de logging."""
    
    def test_get_logger(self):
        """Testa obtenção de logger."""
        logger = get_logger("test_module")
        
        assert logger is not None
        assert "test_module" in logger.name
    
    def test_performance_logger(self):
        """Testa logger de performance."""
        perf_logger = PerformanceLogger()
        
        assert perf_logger is not None
        
        # Testar timers
        perf_logger.start_timer("test_operation")
        elapsed = perf_logger.end_timer("test_operation")
        
        assert elapsed >= 0


class TestProjectStructure:
    """Testes para validar a estrutura do projeto."""
    
    def test_required_directories_exist(self):
        """Testa se diretórios obrigatórios existem."""
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        required_dirs = [
            'src',
            'src/config',
            'src/core',
            'src/services',
            'src/notifications',
            'src/utils',
            'tests'
        ]
        
        for dir_name in required_dirs:
            dir_path = os.path.join(base_path, dir_name)
            assert os.path.exists(dir_path), f"Diretório {dir_name} não existe"
    
    def test_required_files_exist(self):
        """Testa se arquivos obrigatórios existem."""
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        required_files = [
            'main.py',
            'requirements.txt',
            'src/config/settings.py',
            'src/core/sigaa_scraper.py',
            'src/services/auth_service.py',
            'src/services/navigation_service.py',
            'src/services/grade_extractor.py',
            'src/services/cache_service.py',
            'src/services/comparison_service.py',
            'src/notifications/telegram_notifier.py',
            'src/utils/logger.py'
        ]
        
        for file_name in required_files:
            file_path = os.path.join(base_path, file_name)
            assert os.path.exists(file_path), f"Arquivo {file_name} não existe"


if __name__ == "__main__":
    pytest.main([__file__])
