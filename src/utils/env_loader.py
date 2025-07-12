"""
Carregador de variáveis de ambiente para o SIGAA Scraper.
"""

import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

from src.utils.logger import get_logger


class EnvLoader:
    """Carregador de variáveis de ambiente."""
    
    def __init__(self) -> None:
        """Inicializa o carregador de ambiente."""
        self.logger = get_logger("env_loader")
        self._loaded = False
    
    def load_env_file(self, env_file: str = ".env") -> bool:
        """
        Carrega variáveis de ambiente do arquivo especificado.
        
        Args:
            env_file: Nome do arquivo de ambiente
            
        Returns:
            bool: True se carregado com sucesso, False caso contrário
        """
        if self._loaded:
            self.logger.debug("Variáveis de ambiente já carregadas")
            return True
        
        env_path = Path(env_file)
        
        if not env_path.exists():
            self.logger.warning(f"Arquivo {env_file} não encontrado")
            return False
        
        try:
            load_dotenv(env_path)
            self._loaded = True
            self.logger.info(f"✅ Variáveis carregadas de {env_file}")
            return True
        except Exception as e:
            self.logger.error(f"Erro ao carregar {env_file}: {e}")
            return False
    
    def get_required_var(self, var_name: str) -> str:
        """
        Obtém uma variável de ambiente obrigatória.
        
        Args:
            var_name: Nome da variável
            
        Returns:
            str: Valor da variável
            
        Raises:
            ValueError: Se a variável não estiver definida
        """
        value = os.getenv(var_name)
        if not value:
            raise ValueError(f"Variável de ambiente obrigatória não definida: {var_name}")
        return value
    
    def get_optional_var(self, var_name: str, default: str = "") -> str:
        """
        Obtém uma variável de ambiente opcional.
        
        Args:
            var_name: Nome da variável
            default: Valor padrão se não definida
            
        Returns:
            str: Valor da variável ou padrão
        """
        return os.getenv(var_name, default)
    
    def validate_credentials(self) -> tuple[str, str]:
        """
        Valida e retorna as credenciais do SIGAA.
        
        Returns:
            tuple[str, str]: Username e password
            
        Raises:
            ValueError: Se as credenciais forem inválidas
        """
        username = self.get_required_var("SIGAA_USERNAME")
        password = self.get_required_var("SIGAA_PASSWORD")
        
        if len(username) < 3:
            raise ValueError("Username deve ter pelo menos 3 caracteres")
        
        if len(password) < 6:
            raise ValueError("Password deve ter pelo menos 6 caracteres")
        
        return username, password
    
    def get_telegram_config(self) -> dict[str, Optional[str]]:
        """
        Retorna configuração do Telegram.
        
        Returns:
            dict: Configuração do Telegram
        """
        return {
            "bot_token": self.get_optional_var("TELEGRAM_BOT_TOKEN"),
            "group_chat_id": self.get_optional_var("TELEGRAM_GROUP_CHAT_ID"),
            "private_chat_id": self.get_optional_var("TELEGRAM_PRIVATE_CHAT_ID"),
        }


# Instância singleton
_env_loader: Optional[EnvLoader] = None


def get_env_loader() -> EnvLoader:
    """
    Retorna a instância singleton do carregador de ambiente.
    
    Returns:
        EnvLoader: Instância do carregador
    """
    global _env_loader
    if _env_loader is None:
        _env_loader = EnvLoader()
    return _env_loader


def load_environment() -> bool:
    """
    Carrega as variáveis de ambiente.
    
    Returns:
        bool: True se carregado com sucesso
    """
    return get_env_loader().load_env_file()
