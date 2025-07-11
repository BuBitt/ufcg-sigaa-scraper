"""
Módulo singleton para carregamento de variáveis de ambiente.
"""

import logging
import os
from typing import Dict


class EnvironmentLoader:
    """Singleton para carregar variáveis de ambiente uma única vez."""
    
    _instance = None
    _loaded = False
    _env_vars: Dict[str, str] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def load_environment(self) -> None:
        """Carrega variáveis de ambiente do arquivo .env apenas uma vez."""
        if self._loaded:
            return
            
        try:
            with open(".env", "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip() and not line.startswith("#"):
                        key, value = line.strip().split("=", 1)
                        os.environ[key] = value
                        self._env_vars[key] = value
            self._loaded = True
            logging.info("Variáveis de ambiente carregadas com sucesso")
        except FileNotFoundError:
            logging.error("Arquivo .env não encontrado")
            raise
        except Exception as e:
            logging.error(f"Erro ao carregar arquivo .env: {e}")
            raise
    
    def get_env(self, key: str, default: str = None) -> str:
        """Obtém uma variável de ambiente, carregando se necessário."""
        if not self._loaded:
            self.load_environment()
        return os.getenv(key, default)
    
    @property
    def is_loaded(self) -> bool:
        """Verifica se as variáveis já foram carregadas."""
        return self._loaded


# Instância singleton global
env_loader = EnvironmentLoader()


def load_environment() -> None:
    """Função de conveniência para manter compatibilidade."""
    env_loader.load_environment()


def get_env(key: str, default: str = None) -> str:
    """Função de conveniência para obter variáveis de ambiente."""
    return env_loader.get_env(key, default)
