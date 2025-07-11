"""
Sistema de logging avançado para o SIGAA Scraper.

Fornece logging estruturado, rotação de arquivos e diferentes níveis
de verbosidade para desenvolvimento e produção.
"""

import logging
import logging.handlers
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

from src.config.settings import Config


# Flag para evitar configuração duplicada
_logger_configured = False


class ColoredFormatter(logging.Formatter):
    """Formatter colorido para saída no terminal."""
    
    # Códigos de cores ANSI
    COLORS = {
        'DEBUG': '\033[36m',    # Ciano
        'INFO': '\033[32m',     # Verde
        'WARNING': '\033[33m',  # Amarelo
        'ERROR': '\033[31m',    # Vermelho
        'CRITICAL': '\033[35m', # Magenta
        'RESET': '\033[0m'      # Reset
    }
    
    def format(self, record):
        # Aplica cor baseada no nível
        color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        reset = self.COLORS['RESET']
        
        # Formata a mensagem original
        original = super().format(record)
        
        # Adiciona cores apenas ao levelname
        colored = original.replace(
            f"{record.levelname}",
            f"{color}{record.levelname}{reset}"
        )
        
        return colored


class PerformanceLogger:
    """Logger especializado para métricas de performance."""
    
    def __init__(self, logger_name: str = "performance"):
        self.logger = logging.getLogger(logger_name)
        self.start_times = {}
    
    def start_timer(self, operation: str) -> None:
        """Inicia um timer para uma operação."""
        self.start_times[operation] = datetime.now()
        self.logger.debug(f"⏱️  Iniciando: {operation}")
    
    def end_timer(self, operation: str) -> float:
        """Finaliza um timer e registra o tempo decorrido."""
        if operation not in self.start_times:
            self.logger.warning(f"⚠️  Timer não encontrado para: {operation}")
            return 0.0
        
        elapsed = (datetime.now() - self.start_times[operation]).total_seconds()
        self.logger.info(f"✅ Concluído: {operation} em {elapsed:.2f}s")
        del self.start_times[operation]
        return elapsed


def setup_logger(log_level: Optional[int] = None, enable_debug: bool = False) -> None:
    """
    Configura o sistema de logging avançado.
    
    Args:
        log_level: Nível de log personalizado (opcional)
        enable_debug: Habilita logging detalhado para desenvolvimento
    """
    global _logger_configured
    
    if _logger_configured:
        return
    
    # Determina o nível de log
    level = log_level or Config.LOG_LEVEL
    if enable_debug:
        level = logging.DEBUG
    
    # Cria diretório de logs se não existir
    log_dir = Path(Config.LOG_FILENAME).parent
    log_dir.mkdir(exist_ok=True)
    
    # Remove handlers existentes
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Handler para arquivo com rotação
    file_handler = logging.handlers.RotatingFileHandler(
        filename=Config.LOG_FILENAME,
        maxBytes=Config.LOG_MAX_BYTES,
        backupCount=Config.LOG_BACKUP_COUNT,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)  # Arquivo sempre detalhado
    file_formatter = logging.Formatter(
        fmt=Config.LOG_FORMAT_DETAILED,
        datefmt=Config.LOG_DATE_FORMAT
    )
    file_handler.setFormatter(file_formatter)
    
    # Handler para console com cores
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_formatter = ColoredFormatter(
        fmt=Config.LOG_FORMAT_SIMPLE,
        datefmt=Config.LOG_DATE_FORMAT
    )
    console_handler.setFormatter(console_formatter)
    
    # Configura o logger raiz
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    # Configura loggers específicos
    _setup_module_loggers(enable_debug)
    
    # Log inicial do sistema
    logger = logging.getLogger("system")
    logger.info("🚀 Sistema de logging inicializado")
    logger.info(f"📁 Arquivo de log: {Config.LOG_FILENAME}")
    logger.info(f"📊 Nível do console: {logging.getLevelName(level)}")
    logger.info(f"🔍 Debug habilitado: {'✅' if enable_debug else '❌'}")
    
    _logger_configured = True


def _setup_module_loggers(debug_enabled: bool) -> None:
    """Configura loggers específicos para cada módulo."""
    
    # Logger para autenticação
    auth_logger = logging.getLogger("auth")
    auth_logger.setLevel(logging.DEBUG if debug_enabled else logging.INFO)
    
    # Logger para navegação
    nav_logger = logging.getLogger("navigation")
    nav_logger.setLevel(logging.DEBUG if debug_enabled else logging.INFO)
    
    # Logger para extração
    extract_logger = logging.getLogger("extraction")
    extract_logger.setLevel(logging.DEBUG if debug_enabled else logging.INFO)
    
    # Logger para cache
    cache_logger = logging.getLogger("cache")
    cache_logger.setLevel(logging.DEBUG if debug_enabled else logging.INFO)
    
    # Logger para comparação
    compare_logger = logging.getLogger("comparison")
    compare_logger.setLevel(logging.DEBUG if debug_enabled else logging.INFO)
    
    # Logger para notificações
    notify_logger = logging.getLogger("notifications")
    notify_logger.setLevel(logging.DEBUG if debug_enabled else logging.INFO)
    
    # Logger para performance
    perf_logger = logging.getLogger("performance")
    perf_logger.setLevel(logging.INFO)


def get_logger(name: str) -> logging.Logger:
    """
    Obtém um logger configurado para um módulo específico.
    
    Args:
        name: Nome do módulo/componente
        
    Returns:
        Logger configurado
    """
    return logging.getLogger(name)


def get_performance_logger() -> PerformanceLogger:
    """Obtém o logger de performance."""
    return PerformanceLogger()


def is_logger_configured() -> bool:
    """Verifica se o logger já foi configurado."""
    return _logger_configured


def log_system_info() -> None:
    """Registra informações do sistema para debug."""
    logger = get_logger("system")
    
    logger.debug("📋 Informações do Sistema:")
    logger.debug(f"🐍 Python: {sys.version}")
    logger.debug(f"💻 Plataforma: {sys.platform}")
    logger.debug(f"📂 Diretório de trabalho: {os.getcwd()}")
    logger.debug(f"👤 Usuário: {os.getenv('USER', 'Desconhecido')}")


def log_environment_vars() -> None:
    """Registra variáveis de ambiente relevantes (sem valores sensíveis)."""
    logger = get_logger("environment")
    
    env_vars = [
        'SIGAA_USERNAME', 'TELEGRAM_BOT_TOKEN', 
        'TELEGRAM_GROUP_CHAT_ID', 'TELEGRAM_PRIVATE_CHAT_ID'
    ]
    
    logger.debug("🔧 Variáveis de Ambiente:")
    for var in env_vars:
        value = os.getenv(var)
        if value:
            # Mostra apenas se está definida, não o valor
            masked = f"{value[:3]}{'*' * (len(value) - 6)}{value[-3:]}" if len(value) > 6 else "***"
            logger.debug(f"   {var}: {masked}")
        else:
            logger.warning(f"   {var}: ❌ Não definida")


# Funções de conveniência para logging contextual
def log_step(step: str, logger_name: str = "main") -> None:
    """Log de etapa do processo."""
    logger = get_logger(logger_name)
    logger.info(f"📋 {step}")


def log_success(message: str, logger_name: str = "main") -> None:
    """Log de sucesso."""
    logger = get_logger(logger_name)
    logger.info(f"✅ {message}")


def log_warning(message: str, logger_name: str = "main") -> None:
    """Log de aviso."""
    logger = get_logger(logger_name)
    logger.warning(f"⚠️  {message}")


def log_error(message: str, logger_name: str = "main") -> None:
    """Log de erro."""
    logger = get_logger(logger_name)
    logger.error(f"❌ {message}")


def log_debug(message: str, logger_name: str = "main") -> None:
    """Log de debug."""
    logger = get_logger(logger_name)
    logger.debug(f"🔍 {message}")
