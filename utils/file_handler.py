import os
import json
import logging
import tempfile
import shutil
from typing import Dict, Any, Optional, List, Union
import config

# Constantes
DEFAULT_ENCODING = "utf-8"
JSON_INDENT = 4
MAX_BACKUP_FILES = 3


def load_env(env_file: str = ".env") -> None:
    """
    Carrega as variáveis de ambiente do arquivo .env para o ambiente do sistema.
    
    Args:
        env_file: Caminho para o arquivo .env.
    
    Raises:
        FileNotFoundError: Se o arquivo .env não for encontrado.
        Exception: Se houver um erro ao carregar o arquivo .env.
    """
    try:
        if not os.path.exists(env_file):
            logging.error(
                f"Arquivo de ambiente não encontrado",
                extra={"details": f"file={env_file}"}
            )
            raise FileNotFoundError(f"Arquivo {env_file} não encontrado")

        with open(env_file, "r", encoding=DEFAULT_ENCODING) as f:
            for line in f:
                if line.strip() and not line.startswith("#"):
                    try:
                        key, value = line.strip().split("=", 1)
                        os.environ[key] = value
                    except ValueError:
                        logging.warning(
                            f"Formato inválido na linha: {line.strip()}",
                            extra={"details": f"file={env_file}"}
                        )

        logging.info(
            "Variáveis de ambiente carregadas com sucesso",
            extra={"details": f"file={env_file}"}
        )
    except FileNotFoundError:
        logging.error(
            "Arquivo de ambiente não encontrado",
            extra={"details": f"file={env_file}"}
        )
        raise
    except Exception as e:
        logging.error(
            f"Erro ao carregar arquivo de ambiente: {e}",
            exc_info=True,
            extra={"details": f"file={env_file}"}
        )
        raise


def create_backup(filepath: str) -> Optional[str]:
    """
    Cria um backup do arquivo especificado.
    
    Args:
        filepath: O caminho do arquivo a ser copiado.
        
    Returns:
        Optional[str]: O caminho do arquivo de backup, ou None se falhar.
    """
    if not os.path.exists(filepath):
        return None
        
    try:
        backup_path = f"{filepath}.bak"
        shutil.copy2(filepath, backup_path)
        logging.debug(
            "Backup criado com sucesso",
            extra={"details": f"file={backup_path}"}
        )
        return backup_path
    except Exception as e:
        logging.warning(
            f"Não foi possível criar backup: {e}",
            extra={"details": f"file={filepath}"}
        )
        return None


def load_grades(filepath: str = config.CACHE_FILENAME) -> Dict[str, Any]:
    """
    Carrega as notas do arquivo de cache com fallback para backup.

    Args:
        filepath: Caminho para o arquivo de cache.

    Returns:
        dict: As notas carregadas ou um dicionário vazio se o arquivo não existir.
    """
    try:
        if os.path.exists(filepath):
            with open(filepath, "r", encoding=DEFAULT_ENCODING) as f:
                try:
                    data = json.load(f)
                    logging.info(
                        "Notas carregadas com sucesso",
                        extra={"details": f"file={filepath}, entries={len(data)}"}
                    )
                    return data or {}
                except json.JSONDecodeError as e:
                    logging.warning(
                        f"Arquivo de cache corrompido: {e}",
                        extra={"details": f"file={filepath}"}
                    )
                    
                    # Tentar carregar do backup
                    backup_file = f"{filepath}.bak"
                    if os.path.exists(backup_file):
                        logging.info(
                            "Tentando restaurar do backup",
                            extra={"details": f"file={backup_file}"}
                        )
                        try:
                            with open(backup_file, "r", encoding=DEFAULT_ENCODING) as bf:
                                return json.load(bf) or {}
                        except Exception:
                            pass
                    
                    return {}
        else:
            logging.info(
                "Arquivo de cache não encontrado. Criando novo.",
                extra={"details": f"file={filepath}"}
            )
            return {}
    except Exception as e:
        logging.error(
            f"Erro ao carregar arquivo de cache: {e}",
            exc_info=True,
            extra={"details": f"file={filepath}"}
        )
        return {}


def save_grades(grades: Dict[str, Any], filepath: str = config.CACHE_FILENAME) -> bool:
    """
    Salva as notas no arquivo de cache de forma segura.

    Args:
        grades: As notas a serem salvas.
        filepath: Caminho para o arquivo de cache.
        
    Returns:
        bool: True se o salvamento foi bem-sucedido, False caso contrário.
    """
    # Criar backup do arquivo existente
    if os.path.exists(filepath):
        create_backup(filepath)
    
    try:
        # Usar arquivo temporário para escrita atômica
        with tempfile.NamedTemporaryFile(mode="w", delete=False, encoding=DEFAULT_ENCODING) as temp_file:
            json.dump(grades, temp_file, ensure_ascii=False, indent=JSON_INDENT)
        
        # Substituir arquivo original pelo temporário
        shutil.move(temp_file.name, filepath)
        
        logging.info(
            "Notas salvas com sucesso",
            extra={"details": f"file={filepath}, entries={len(grades)}"}
        )
        return True
    except Exception as e:
        logging.error(
            f"Erro ao salvar arquivo de cache: {e}",
            exc_info=True,
            extra={"details": f"file={filepath}"}
        )
        
        # Tentar limpar o arquivo temporário em caso de falha
        try:
            if os.path.exists(temp_file.name):
                os.unlink(temp_file.name)
        except:
            pass
        
        return False


def compare_grades(
    new_grades: Dict[str, Any], 
    saved_grades: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Compara as novas notas com as notas salvas e identifica diferenças.

    Args:
        new_grades: As novas notas extraídas.
        saved_grades: As notas salvas anteriormente.

    Returns:
        dict: Um dicionário com as diferenças entre os dois conjuntos de notas.
    """
    try:
        differences = {}
        
        # Verificar componentes novos ou alterados
        for component, new_data in new_grades.items():
            # Componente novo ou de tipos diferentes
            if component not in saved_grades or type(saved_grades[component]) != type(new_data):
                differences[component] = {"status": "Novo componente", "data": new_data}
                continue

            saved_data = saved_grades[component]
            
            # Processar componentes com listas de dados (notas)
            if isinstance(new_data, list) and isinstance(saved_data, list):
                for new_row in new_data:
                    diff = {}
                    for key, new_value in new_row.items():
                        # Encontrar valor correspondente nas notas salvas
                        old_value = next(
                            (
                                saved_row.get(key, "")
                                for saved_row in saved_data
                                if key in saved_row
                            ),
                            "",
                        )
                        
                        if new_value != old_value:
                            diff[key] = {"old": old_value, "new": new_value}
                    
                    if diff:
                        if component not in differences:
                            differences[component] = []
                        differences[component].append(diff)
            
            # Processar componentes com valores simples (textos)
            elif new_data != saved_data:
                differences[component] = {
                    "status": "Alterado",
                    "old": saved_data,
                    "new": new_data,
                }
        
        # Verificar componentes removidos
        for component in saved_grades:
            if component not in new_grades:
                differences[component] = {"status": "Removido"}

        # Registrar resultados
        if differences:
            logging.info(
                "Diferenças encontradas nas notas",
                extra={"details": f"count={len(differences)}"}
            )
        else:
            # Apenas um log, para não duplicar
            pass

        return differences

    except Exception as e:
        logging.error(
            f"Erro ao comparar notas: {e}",
            exc_info=True,
            extra={"details": "function=compare_grades"}
        )
        return {}


def load_discipline_replacements(filepath: str = "discipline_replacements.json") -> Dict[str, str]:
    """
    Carrega o dicionário de substituições de nomes de disciplinas.

    Args:
        filepath: Caminho para o arquivo de substituições.

    Returns:
        dict: O dicionário de substituições ou um dicionário vazio se o arquivo não existir.
    """
    try:
        if not os.path.exists(filepath):
            logging.warning(
                "Arquivo de substituições não encontrado. Usando padrões.",
                extra={"details": f"file={filepath}"}
            )
            return {}
            
        with open(filepath, "r", encoding=DEFAULT_ENCODING) as f:
            replacements = json.load(f)
            logging.info(
                "Substituições de disciplinas carregadas",
                extra={"details": f"file={filepath}, count={len(replacements)}"}
            )
            return replacements
            
    except json.JSONDecodeError as e:
        logging.error(
            f"Formato inválido no arquivo de substituições: {e}",
            extra={"details": f"file={filepath}"}
        )
        return {}
    except Exception as e:
        logging.error(
            f"Erro ao carregar substituições: {e}",
            exc_info=True,
            extra={"details": f"file={filepath}"}
        )
        return {}
