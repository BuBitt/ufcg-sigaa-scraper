import logging
import config


def setup_logging():
    """
    Configure the logging system for the application.
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
    Log an error message and raise an exception.

    Args:
        message (str): The error message to log
        exception_class (Exception): The exception class to raise
        *args, **kwargs: Arguments to pass to the exception constructor
    """
    logging.error(message)
    raise exception_class(message, *args, **kwargs)
