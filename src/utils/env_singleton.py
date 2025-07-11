"""
Módulo singleton para carregamento de variáveis de ambiente.
"""

import logging
import os
from typing import Dict, Optional, Any


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
            logging.getLogger("environment").debug("🔄 Variáveis já carregadas, reutilizando cache")
            return
            
        logger = logging.getLogger("environment")
        logger.debug("📂 Iniciando carregamento de variáveis de ambiente")
        
        try:
            env_count = 0
            with open(".env", "r", encoding="utf-8") as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    
                    if "=" not in line:
                        logger.warning(f"⚠️  Linha {line_num} inválida no .env: {line}")
                        continue
                    
                    key, value = line.split("=", 1)
                    key = key.strip()
                    value = value.strip().strip('"').strip("'")  # Remove aspas se houver
                    
                    os.environ[key] = value
                    self._env_vars[key] = value
                    env_count += 1
                    
                    # Log seguro (sem expor valores sensíveis)
                    if any(sensitive in key.lower() for sensitive in ['password', 'token', 'secret']):
                        logger.debug(f"🔐 {key}: ***")
                    else:
                        logger.debug(f"📝 {key}: {value}")
            
            self._loaded = True
            logger.info(f"✅ {env_count} variáveis de ambiente carregadas com sucesso")
            
        except FileNotFoundError:
            logger.error("❌ Arquivo .env não encontrado")
            logger.info("💡 Crie um arquivo .env baseado no .env.example")
            raise
        except UnicodeDecodeError as e:
            logger.error(f"❌ Erro de codificação no arquivo .env: {e}")
            logger.info("💡 Verifique se o arquivo .env está em UTF-8")
            raise
        except Exception as e:
            logger.error(f"❌ Erro inesperado ao carregar .env: {e}")
            raise
    
    def get_env(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Obtém uma variável de ambiente, carregando se necessário."""
        if not self._loaded:
            self.load_environment()
        
        value = os.getenv(key, default)
        logger = logging.getLogger("environment")
        
        if value is None:
            logger.warning(f"⚠️  Variável '{key}' não encontrada")
        elif value == default and default is not None:
            logger.debug(f"🔄 Usando valor padrão para '{key}': {default}")
        
        return value
    
    @property
    def is_loaded(self) -> bool:
        """Verifica se as variáveis já foram carregadas."""
        return self._loaded
    
    def get_loaded_vars(self) -> Dict[str, str]:
        """Retorna as variáveis carregadas (para debug)."""
        return self._env_vars.copy()
    
    def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas do carregamento."""
        return {
            "loaded": self._loaded,
            "var_count": len(self._env_vars),
            "variables": list(self._env_vars.keys())
        }


# Instância singleton global
env_loader = EnvironmentLoader()


def load_environment() -> None:
    """Função de conveniência para manter compatibilidade."""
    env_loader.load_environment()


def get_env(key: str, default: Optional[str] = None) -> Optional[str]:
    """Função de conveniência para obter variáveis de ambiente."""
    return env_loader.get_env(key, default)
