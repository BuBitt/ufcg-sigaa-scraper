"""
Serviço de cache para persistência de dados de notas.
"""

import json
import os
from datetime import datetime
from typing import Dict, Any, List

from src.config.settings import Config
from src.utils.logger import get_logger


class CacheService:
    """Gerencia o cache de dados de notas."""
    
    def __init__(self) -> None:
        """Inicializa o serviço de cache."""
        self.logger = get_logger("cache")
        self.cache_file = Config.CACHE_FILENAME
        self.logger.debug("Serviço de cache inicializado")
    
    def load_cache(self) -> Dict[str, Any]:
        """
        Carrega dados do cache.
        
        Returns:
            Dict[str, Any]: Dados do cache ou dict vazio se não existir
        """
        try:
            if not os.path.exists(self.cache_file):
                self.logger.info("Arquivo de cache não existe, criando novo")
                return {}
            
            with open(self.cache_file, 'r', encoding=Config.DEFAULT_ENCODING) as f:
                data = json.load(f)
            
            # Verificar estrutura do cache
            if 'metadata' in data:
                last_update = data['metadata'].get('last_update', 'desconhecido')
                self.logger.info(f"Cache carregado - última atualização: {last_update}")
            else:
                self.logger.info("Cache carregado (formato antigo)")
            
            return data.get('grades', data)  # Suporte a formato antigo
            
        except json.JSONDecodeError as e:
            self.logger.error(f"Erro ao decodificar JSON do cache: {e}")
            self._backup_corrupted_cache()
            return {}
        except Exception as e:
            self.logger.error(f"Erro ao carregar cache: {e}")
            return {}
    
    def save_cache(self, grades: List[Dict[str, Any]]) -> bool:
        """
        Salva dados no cache.
        
        Args:
            grades: Lista de notas para salvar
            
        Returns:
            bool: True se salvamento foi bem-sucedido
        """
        try:
            # Preparar dados com metadados
            cache_data = {
                'metadata': {
                    'last_update': datetime.now().isoformat(),
                    'extraction_method': Config.get_extraction_method(),
                    'total_records': len(grades),
                    'app_version': Config.VERSION
                },
                'grades': grades
            }
            
            # Fazer backup se arquivo existe
            if os.path.exists(self.cache_file):
                self._create_backup()
            
            # Salvar novo cache
            with open(self.cache_file, 'w', encoding=Config.DEFAULT_ENCODING) as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=Config.JSON_INDENT)
            
            self.logger.info(f"Cache salvo: {len(grades)} registro(s)")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao salvar cache: {e}")
            return False
    
    def _create_backup(self) -> None:
        """Cria backup do cache atual."""
        try:
            backup_file = f"{self.cache_file}.backup"
            
            # Se já existe backup, rotacionar
            if os.path.exists(backup_file):
                for i in range(Config.MAX_BACKUP_FILES - 1, 0, -1):
                    old_backup = f"{backup_file}.{i}"
                    new_backup = f"{backup_file}.{i + 1}"
                    
                    if os.path.exists(old_backup):
                        if i + 1 <= Config.MAX_BACKUP_FILES:
                            os.rename(old_backup, new_backup)
                        else:
                            os.remove(old_backup)
                
                os.rename(backup_file, f"{backup_file}.1")
            
            # Criar novo backup
            import shutil
            shutil.copy2(self.cache_file, backup_file)
            self.logger.debug("Backup do cache criado")
            
        except Exception as e:
            self.logger.warning(f"Erro ao criar backup: {e}")
    
    def _backup_corrupted_cache(self) -> None:
        """Faz backup de cache corrompido."""
        try:
            corrupted_file = f"{self.cache_file}.corrupted.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            os.rename(self.cache_file, corrupted_file)
            self.logger.warning(f"Cache corrompido movido para: {corrupted_file}")
        except Exception as e:
            self.logger.error(f"Erro ao fazer backup de cache corrompido: {e}")
    
    def get_cache_info(self) -> Dict[str, Any]:
        """
        Retorna informações sobre o cache.
        
        Returns:
            Dict: Informações do cache
        """
        info = {
            'exists': os.path.exists(self.cache_file),
            'file_path': self.cache_file,
            'size_bytes': 0,
            'last_modified': None,
            'metadata': {}
        }
        
        try:
            if info['exists']:
                stat = os.stat(self.cache_file)
                info['size_bytes'] = stat.st_size
                info['last_modified'] = datetime.fromtimestamp(stat.st_mtime).isoformat()
                
                # Tentar carregar metadados
                with open(self.cache_file, 'r', encoding=Config.DEFAULT_ENCODING) as f:
                    data = json.load(f)
                    info['metadata'] = data.get('metadata', {})
            
        except Exception as e:
            self.logger.warning(f"Erro ao obter informações do cache: {e}")
        
        return info
    
    def clear_cache(self) -> bool:
        """
        Remove o arquivo de cache.
        
        Returns:
            bool: True se remoção foi bem-sucedida
        """
        try:
            if os.path.exists(self.cache_file):
                os.remove(self.cache_file)
                self.logger.info("🗑️  Cache removido")
                return True
            else:
                self.logger.info("ℹ️  Cache não existe")
                return True
                
        except Exception as e:
            self.logger.error(f"Erro ao remover cache: {e}")
            return False
    
    def validate_cache_integrity(self) -> bool:
        """
        Valida a integridade do cache.
        
        Returns:
            bool: True se cache é válido
        """
        try:
            data = self.load_cache()
            
            # Verificações básicas
            if not isinstance(data, (dict, list)):
                self.logger.warning("Cache não é dict nem list")
                return False
            
            # Se é dict, verificar se tem estrutura esperada
            if isinstance(data, dict):
                # Pode ser formato antigo (dict direto) ou novo (com metadata)
                if 'metadata' in data and 'grades' in data:
                    grades = data['grades']
                else:
                    grades = data
                
                if not isinstance(grades, (dict, list)):
                    self.logger.warning("Estrutura de notas inválida no cache")
                    return False
            
            self.logger.debug("Cache válido")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro na validação do cache: {e}")
            return False
