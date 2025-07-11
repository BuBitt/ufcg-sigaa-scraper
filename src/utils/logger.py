"""
Utilitário para configuração de logging.
"""

import logging
from src.config.settings import Config


# Flag para evitar configuração duplicada
_logger_configured = False


def setup_logger() -> None:
    """Configura o logger da aplicação apenas uma vez."""
    global _logger_configured
    
    if _logger_configured:
        return
    
    # Remove handlers existentes para evitar duplicação
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    logging.basicConfig(
        level=Config.LOG_LEVEL,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(Config.LOG_FILENAME, mode="w"),
            logging.StreamHandler(),
        ],
    )
    
    _logger_configured = True


def is_logger_configured() -> bool:
    """Verifica se o logger já foi configurado."""
    return _logger_configured
