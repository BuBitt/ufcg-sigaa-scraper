"""
Utilitário para configuração de logging.
"""

import logging
from src.config.settings import Config


def setup_logger() -> None:
    """Configura o logger da aplicação."""
    logging.basicConfig(
        level=Config.LOG_LEVEL,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(Config.LOG_FILENAME, mode="w"),
            logging.StreamHandler(),
        ],
    )
