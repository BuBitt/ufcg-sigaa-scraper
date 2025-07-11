"""
Módulo de configurações do SIGAA Scraper.

Contém todas as configurações centralizadas da aplicação.
"""

import logging
import os
from typing import Final


class Config:
    """Classe de configuração centralizada."""
    
    # Configuração do Navegador
    HEADLESS_BROWSER: Final[bool] = True
    TIMEOUT_DEFAULT: Final[int] = 30000
    VIEWPORT_WIDTH: Final[int] = 1280
    VIEWPORT_HEIGHT: Final[int] = 720
    
    # Configuração de Logging
    LOG_LEVEL: Final[int] = logging.DEBUG
    LOG_FILENAME: Final[str] = "script.log"
    
    # Configuração de Arquivos
    CACHE_FILENAME: Final[str] = "grades_cache.json"
    
    # Configuração de Notificações do Telegram
    SEND_TELEGRAM_GROUP: Final[bool] = True
    SEND_TELEGRAM_PRIVATE: Final[bool] = True
    
    # URLs do SIGAA
    SIGAA_URL: Final[str] = "https://sigaa.ufcg.edu.br/sigaa"
