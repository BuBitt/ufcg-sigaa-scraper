import os
import json
import logging
import config


def load_env():
    """
    Load environment variables from the .env file into the OS environment.

    Raises:
        FileNotFoundError: If the .env file is not found
        Exception: If there is an error loading the .env file
    """
    try:
        with open(".env", "r") as f:
            for line in f:
                if line.strip() and not line.startswith("#"):
                    key, value = line.strip().split("=", 1)
                    os.environ[key] = value
        logging.info(".env carregado com sucesso")
    except FileNotFoundError:
        logging.error(".env não encontrado")
        raise
    except Exception as e:
        logging.error(f"Erro ao carregar .env: {e}")
        raise


def load_grades(filepath=config.CACHE_FILENAME):
    """
    Load grades from the cache file.

    Args:
        filepath (str): Path to the cache file

    Returns:
        dict: The loaded grades or an empty dictionary if the file doesn't exist
    """
    try:
        if os.path.exists(filepath):
            with open(filepath, "r", encoding="utf-8") as f:
                try:
                    return json.load(f) or {}
                except json.JSONDecodeError:
                    logging.warning(
                        f"{filepath} está vazio ou corrompido. Inicializando como vazio."
                    )
                    return {}
        else:
            logging.info(f"Arquivo {filepath} não encontrado. Criando novo.")
            return {}
    except Exception as e:
        logging.error(f"Erro ao carregar {filepath}: {e}")
        return {}


def save_grades(grades, filepath=config.CACHE_FILENAME):
    """
    Save grades to the cache file.

    Args:
        grades (dict): The grades to save
        filepath (str): Path to the cache file
    """
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(grades, f, ensure_ascii=False, indent=4)
        logging.info(f"Notas salvas em {filepath}")
    except Exception as e:
        logging.error(f"Erro ao salvar {filepath}: {e}")


def compare_grades(new_grades, saved_grades):
    """
    Compare new grades with saved grades and identify differences.

    Args:
        new_grades (dict): The newly extracted grades
        saved_grades (dict): The previously saved grades

    Returns:
        dict: A dictionary of differences between the two sets of grades
    """
    try:
        differences = {}
        for component, new_data in new_grades.items():
            # Handle new components or mismatched types
            if component not in saved_grades or type(saved_grades[component]) != type(
                new_data
            ):
                differences[component] = {"status": "Novo componente", "data": new_data}
                continue

            saved_data = saved_grades[component]
            if isinstance(new_data, list) and isinstance(saved_data, list):
                for new_row in new_data:
                    diff = {}
                    for key, new_value in new_row.items():
                        # Find the corresponding saved row with the same key, if it exists
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
            elif new_data != saved_data:
                differences[component] = {
                    "status": "Alterado",
                    "old": saved_data,
                    "new": new_data,
                }

        for component in saved_grades:
            if component not in new_grades:
                differences[component] = {"status": "Removido"}

        if differences:
            logging.info("Diferenças encontradas:")
            print(json.dumps(differences, ensure_ascii=False, indent=4))
        else:
            logging.info("Nenhuma diferença encontrada nas notas.")

        return differences

    except Exception as e:
        logging.error(f"Erro ao comparar notas: {e}")
        return {}


def load_discipline_replacements(filepath="discipline_replacements.json"):
    """
    Load the discipline replacements dictionary.

    Args:
        filepath (str): Path to the replacements file

    Returns:
        dict: The replacements dictionary or an empty dictionary if the file doesn't exist
    """
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        logging.warning(
            f"Arquivo {filepath} não encontrado. Usando substituições padrão."
        )
        return {}
    except Exception as e:
        logging.error(f"Erro ao carregar {filepath}: {e}")
        return {}
