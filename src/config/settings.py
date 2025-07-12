"""
Módulo de configurações do SIGAA Scraper.

Contém todas as configurações centralizadas da aplicação.
"""

import logging
import os
from typing import Final


class Config:
    """Classe de configuração centralizada."""
    
    # Informações da aplicação
    VERSION: Final[str] = "2.0.0"
    APP_NAME: Final[str] = "SIGAA Grade Scraper"
    
    # Configuração do Navegador
    HEADLESS_BROWSER: Final[bool] = True  # Modo headless para produção
    TIMEOUT_DEFAULT: Final[int] = 45000  # 45 segundos em milissegundos
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
    CSV_FILENAME: Final[str] = "notas_completas.csv"
    HTML_OUTPUT: Final[str] = "minhas_notas.html"
    HTML_DEBUG_OUTPUT: Final[str] = "minhas_notas_debug.html"
    CREATE_CSV: Final[bool] = False
    DEFAULT_ENCODING: Final[str] = "utf-8"
    MAX_BACKUP_FILES: Final[int] = 3
    JSON_INDENT: Final[int] = 4
    
    # Configuração de Notificações do Telegram
    SEND_TELEGRAM_GROUP: Final[bool] = True
    SEND_TELEGRAM_PRIVATE: Final[bool] = True
    
    # Configurações de segurança
    MASK_CREDENTIALS: Final[bool] = True
    
    # Configurações de retry
    MAX_RETRIES: Final[int] = 3
    RETRY_DELAY: Final[int] = 2  # segundos
    REQUEST_TIMEOUT: Final[int] = 10  # segundos
    
    # URLs do SIGAA
    SIGAA_URL: Final[str] = "https://sigaa.ufcg.edu.br/sigaa"
    
    # Configurações de extração
    # Escolha do método de extração de notas:
    # "menu_ensino" - Usa o menu Ensino > Consultar Minhas Notas (mais rápido e direto)
    # "materia_individual" - Acessa matéria por matéria pelo menu lateral (método original)
    EXTRACTION_METHOD: Final[str] = os.getenv("EXTRACTION_METHOD", "menu_ensino")
    
    @classmethod
    def ensure_directories(cls) -> None:
        """Garante que os diretórios necessários existem."""
        os.makedirs(os.path.dirname(cls.LOG_FILENAME), exist_ok=True)
    
    @classmethod
    def get_extraction_method(cls) -> str:
        """
        Retorna o método de extração configurado, validando se é válido.
        
        Returns:
            str: Método de extração válido.
        """
        method = cls.EXTRACTION_METHOD.lower()
        valid_methods = ["menu_ensino", "materia_individual"]
        
        if method not in valid_methods:
            return "menu_ensino"  # Padrão
            
        return method


# Garantir que diretórios existem na importação
Config.ensure_directories()
