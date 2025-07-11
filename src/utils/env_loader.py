"""
Serviço para carregar variáveis de ambiente (compatibilidade).
"""

from src.utils.env_singleton import load_environment, get_env

# Re-exporta as funções para manter compatibilidade
__all__ = ['load_environment', 'get_env']
