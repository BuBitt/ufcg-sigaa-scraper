"""
Sistema de logging avançado para o SIGAA Scraper.

Fornece configuração centralizada de logging com diferentes níveis
e formatação personalizada para desenvolvimento e produção.
"""

import logging
import logging.handlers
import os
import platform
import sys
import time
from typing import Dict, Optional

from src.config.settings import Config


class PerformanceLogger:
    """Logger especializado para medição de performance."""
    
    def __init__(self) -> None:
        """Inicializa o logger de performance."""
        self.timers: Dict[str, float] = {}
        self.logger = logging.getLogger("performance")
    
    def start_timer(self, operation: str) -> None:
        """
        Inicia um timer para uma operação.
        
        Args:
            operation: Nome da operação sendo medida
        """
        self.timers[operation] = time.time()
    self.logger.debug(f"Timer iniciado: {operation}")
    
    def end_timer(self, operation: str) -> float:
        """
        Finaliza um timer e retorna o tempo decorrido.
        
        Args:
            operation: Nome da operação sendo medida
            
        Returns:
            float: Tempo decorrido em segundos
        """
        if operation not in self.timers:
            self.logger.warning(f"Timer não encontrado: {operation}")
            return 0.0
        
        elapsed = time.time() - self.timers[operation]
        del self.timers[operation]
        
    self.logger.info(f"{operation}: {elapsed:.2f}s")
        return elapsed


def setup_logger(enable_debug: bool = False) -> None:
    """
    Configura o sistema de logging da aplicação.
    
    Args:
        enable_debug: Habilita logging detalhado para desenvolvimento
    """
    # Configurar nível de log
    log_level = logging.DEBUG if enable_debug else Config.LOG_LEVEL
    
    # Configurar formatador
    formatter = logging.Formatter(
        Config.LOG_FORMAT_DETAILED if enable_debug else Config.LOG_FORMAT_SIMPLE,
        datefmt=Config.LOG_DATE_FORMAT
    )
    
    # Configurar handler para arquivo
    file_handler = logging.handlers.RotatingFileHandler(
        Config.LOG_FILENAME,
        maxBytes=Config.LOG_MAX_BYTES,
        backupCount=Config.LOG_BACKUP_COUNT,
        encoding=Config.DEFAULT_ENCODING
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)
    
    # Configurar handler para console
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(
        logging.Formatter(Config.LOG_FORMAT_SIMPLE, datefmt=Config.LOG_DATE_FORMAT)
    )
    
    # Configurar logger raiz
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Remover handlers existentes
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Adicionar novos handlers
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    # Silenciar logs de bibliotecas externas em produção
    if not enable_debug:
        logging.getLogger("urllib3").setLevel(logging.WARNING)
        logging.getLogger("playwright").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """
    Retorna um logger configurado para um módulo específico.
    
    Args:
        name: Nome do módulo/componente
        
    Returns:
        logging.Logger: Logger configurado
    """
    return logging.getLogger(name)


def get_performance_logger() -> PerformanceLogger:
    """
    Retorna uma instância do logger de performance.
    
    Returns:
        PerformanceLogger: Instância do logger de performance
    """
    return PerformanceLogger()


def log_system_info() -> None:
    """Registra informações do sistema para debug."""
    logger = get_logger("system")
    
    logger.debug("Informações do Sistema:")
    logger.debug(f"   Python: {sys.version}")
    logger.debug(f"   OS: {platform.system()} {platform.release()}")
    logger.debug(f"   Arquitetura: {platform.machine()}")
    logger.debug(f"   Diretório: {os.getcwd()}")


def log_environment_vars() -> None:
    """Registra variáveis de ambiente relevantes (sem expor dados sensíveis)."""
    logger = get_logger("environment")
    
    env_vars = [
        "EXTRACTION_METHOD",
        "CI", "GITHUB_ACTIONS",
        "HEADLESS", "DEBUG"
    ]
    
    logger.debug("Variáveis de Ambiente:")
    for var in env_vars:
        value = os.getenv(var, "não definida")
        logger.debug(f"   {var}: {value}")
