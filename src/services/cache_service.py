"""
Serviço de cache para armazenamento e recuperação de notas.
"""

import json
import logging
from typing import Dict, List

from src.config.settings import Config


class CacheService:
    """Gerencia o cache de notas para comparação."""
    
    def load_cache(self, filename: str = Config.CACHE_FILENAME) -> Dict[str, List[Dict[str, str]]]:
        """
        Carrega notas em cache do arquivo.
        
        Args:
            filename: Caminho para o arquivo de cache
            
        Returns:
            Dicionário contendo notas em cache organizadas por semestre
        """
        try:
            with open(filename, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            logging.info("Arquivo de cache não encontrado, começando do zero")
            return {}
        except Exception as e:
            logging.error(f"Erro ao carregar cache: {e}")
            return {}

    def save_cache(self, grades: List[Dict[str, str]], filename: str = Config.CACHE_FILENAME) -> None:
        """
        Salva notas no arquivo de cache.
        
        Args:
            grades: Lista de registros de notas para armazenar em cache
            filename: Caminho para o arquivo de cache
        """
        cache = {}
        for grade in grades:
            semester = grade["Semestre"]
            cache.setdefault(semester, []).append(grade)
            
        try:
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(cache, f, ensure_ascii=False, indent=2)
            logging.info(f"Cache salvo em {filename}")
        except Exception as e:
            logging.error(f"Erro ao salvar cache: {e}")
