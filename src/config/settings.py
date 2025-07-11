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
    LOG_LEVEL: Final[int] = logging.INFO
    LOG_FILENAME: Final[str] = "logs/sigaa_scraper.log"
    LOG_MAX_BYTES: Final[int] = 10 * 1024 * 1024  # 10MB
    LOG_BACKUP_COUNT: Final[int] = 5
    LOG_FORMAT_DETAILED: Final[str] = (
        "%(asctime)s | %(levelname)-8s | %(name)-20s | "
        "%(funcName)-20s:%(lineno)-4d | %(message)s"
    )
    LOG_FORMAT_SIMPLE: Final[str] = "%(asctime)s | %(levelname)-8s | %(message)s"
    LOG_DATE_FORMAT: Final[str] = "%Y-%m-%d %H:%M:%S"
    
    # Configuração de Arquivos
    CACHE_FILENAME: Final[str] = "grades_cache.json"
    
    # Configuração de Notificações do Telegram
    SEND_TELEGRAM_GROUP: Final[bool] = True
    SEND_TELEGRAM_PRIVATE: Final[bool] = True
    
    # URLs do SIGAA
    SIGAA_URL: Final[str] = "https://sigaa.ufcg.edu.br/sigaa"
