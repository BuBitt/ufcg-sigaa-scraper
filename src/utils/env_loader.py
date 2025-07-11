"""
Serviço para carregar variáveis de ambiente.
"""

import logging
import os


def load_environment() -> None:
    """Carrega variáveis de ambiente do arquivo .env."""
    try:
        with open(".env", "r", encoding="utf-8") as f:
            for line in f:
                if line.strip() and not line.startswith("#"):
                    key, value = line.strip().split("=", 1)
                    os.environ[key] = value
        logging.info("Variáveis de ambiente carregadas com sucesso")
    except FileNotFoundError:
        logging.error("Arquivo .env não encontrado")
        raise
    except Exception as e:
        logging.error(f"Erro ao carregar arquivo .env: {e}")
        raise
