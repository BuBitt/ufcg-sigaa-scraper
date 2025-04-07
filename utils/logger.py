import logging
import sys
import time
from functools import wraps
from typing import Optional, Union, Dict, Any, Type, Callable
import config


class CustomFormatter(logging.Formatter):
    """
    Custom logging formatter to include bold levels and adjusted gray tones for details.
    """
    # Define colors for log levels com melhor contraste e legibilidade
    COLORS = {
        "DEBUG": "\033[36m",     # Ciano - azul suave para debug (menos importante)
        "INFO": "\033[1;32m",    # Verde brilhante - para informações normais
        "WARNING": "\033[1;33m",  # Amarelo brilhante - para avisos
        "ERROR": "\033[1;31m",   # Vermelho brilhante - para erros
        "CRITICAL": "\033[1;35m", # Magenta brilhante - para erros críticos
    }
    RESET = "\033[0m"
    GRAY_DARKER = "\033[37m"     # Cinza claro para mensagem principal (melhor legibilidade)
    GRAY_DARKEST = "\033[36;2m"  # Ciano escuro para detalhes (distinguível mas secundário)

    def format(self, record: logging.LogRecord) -> str:
        """
        Format the log record with colors and styling.
        
        Args:
            record: The log record to format.
            
        Returns:
            str: The formatted log message.
        """
        # Add bold color to the log level
        levelname = record.levelname
        color = self.COLORS.get(levelname, "")
        record.levelname = f"{color}{levelname}{self.RESET}"

        # Adjust gray tones for the message and details - usando cinza mais escuro para detalhes
        if hasattr(record, "details"):
            # Armazenar os detalhes para não duplicá-los
            details = record.details
            # Remover detalhes do record para evitar duplicação
            delattr(record, "details")
            formatted_message = f"{self.GRAY_DARKER}{record.msg}{self.RESET} {self.GRAY_DARKEST}{details}{self.RESET}"
            record.msg = formatted_message
        else:
            record.msg = f"{self.GRAY_DARKER}{record.msg}{self.RESET}"
            
        # Remove context attribute if present (previously used for emoji selection)
        if hasattr(record, "context"):
            delattr(record, "context")

        return super().format(record)


def setup_logging(log_file: str = config.LOG_FILENAME) -> logging.Logger:
    """
    Configura o sistema de logs para a aplicação.
    
    Args:
        log_file: Arquivo onde os logs serão salvos. Default vem do config.
        
    Returns:
        logging.Logger: O logger configurado.
    """
    formatter = CustomFormatter(
        fmt="%(asctime)s %(levelname)s %(message)s",
        datefmt="%Y/%m/%d %H:%M:%S",
    )

    # Configure handlers
    # Usar "a" (append) ao invés de "w" (write) para preservar logs antigos
    file_handler = logging.FileHandler(log_file, mode="a", encoding="utf-8")
    file_handler.setFormatter(formatter)

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)

    # Configure logger
    logger = logging.getLogger()
    logger.setLevel(config.LOG_DEPTH)
    
    # Limpar handlers existentes para evitar duplicação de logs
    if logger.handlers:
        logger.handlers.clear()
        
    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)

    return logger


def log_error_and_raise(
    message: str, 
    exception_class: Type[Exception] = Exception, 
    extra: Optional[Dict[str, Any]] = None, 
    *args: Any, 
    **kwargs: Any
) -> None:
    """
    Registra uma mensagem de erro e lança uma exceção.

    Args:
        message: A mensagem de erro a ser registrada.
        exception_class: A classe da exceção a ser lançada.
        extra: Detalhes adicionais para incluir no log.
        *args, **kwargs: Argumentos a serem passados para o construtor da exceção.
    """
    log_kwargs = {"exc_info": True}
    if extra:
        log_kwargs["extra"] = extra
    
    logging.error(message, **log_kwargs)
    raise exception_class(message, *args, **kwargs)


def format_component_name(component_name: str) -> str:
    """
    Formata o nome do componente para exibição em logs.
    
    Args:
        component_name: Nome completo do componente curricular.
        
    Returns:
        str: Nome formatado mais curto e legível.
    """
    try:
        # Tentar extrair o nome principal da disciplina
        if " - " in component_name and " (" in component_name:
            # Formato: "1202024 - FARMACOLOGIA (60h) - Turma: 01 (2024.2)"
            code = component_name.split(" - ")[0].strip()
            discipline = component_name.split(" - ")[1].split(" (")[0].strip()
            return f"{discipline} ({code})"
        return component_name
    except Exception:
        return component_name


def log_operation(func=None, *, operation_name: str = None) -> Callable:
    """
    Decorator para registrar o início e fim de uma operação importante.
    
    Args:
        func: A função a ser decorada.
        operation_name: Nome opcional da operação (usa nome da função se não fornecido).
    """
    def decorator(f):
        nonlocal operation_name
        if operation_name is None:
            operation_name = f.__name__.replace('_', ' ').title()
        
        @wraps(f)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            logging.info(f"Iniciando {operation_name}")
            
            try:
                result = f(*args, **kwargs)
                execution_time = time.time() - start_time
                
                if hasattr(result, '__len__'):
                    items_count = len(result)
                    logging.info(
                        f"Concluído {operation_name}",
                        extra={
                            "details": f"tempo={execution_time:.2f}s, itens={items_count}"
                        }
                    )
                else:
                    logging.info(
                        f"Concluído {operation_name}",
                        extra={
                            "details": f"tempo={execution_time:.2f}s"
                        }
                    )
                
                return result
                
            except Exception as e:
                execution_time = time.time() - start_time
                logging.error(
                    f"Falha em {operation_name}: {str(e)}",
                    exc_info=True,
                    extra={
                        "details": f"tempo={execution_time:.2f}s, erro={e.__class__.__name__}"
                    }
                )
                raise
                
        return wrapper
    
    if func:
        return decorator(func)
    return decorator
