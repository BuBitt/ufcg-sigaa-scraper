import logging
import config


def setup_logging():
    """
    Configura o sistema de logs para a aplicação.
    """
    logging.basicConfig(
        level=config.LOG_DEPTH,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(config.LOG_FILENAME, mode="w"),
            logging.StreamHandler(),
        ],
    )
    return logging.getLogger()


def log_error_and_raise(message, exception_class=Exception, *args, **kwargs):
    """
    Registra uma mensagem de erro e lança uma exceção.

    Args:
        message (str): A mensagem de erro a ser registrada.
        exception_class (Exception): A classe da exceção a ser lançada.
        *args, **kwargs: Argumentos a serem passados para o construtor da exceção.
    """
    logging.error(message)
    raise exception_class(message, *args, **kwargs)
