import os
import logging
import requests
import json  # Import to handle the dictionary file
from dotenv import load_dotenv
import config

# Configuração mínima do logging
logging.basicConfig(
    level=config.LOG_DEPTH,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(config.LOG_FILENAME, mode="a"),
        logging.StreamHandler(),
    ],
)


# Carrega credenciais do Telegram
def get_telegram_credentials():
    """
    Loads Telegram credentials from the .env file.

    Returns:
        tuple: A tuple containing the group chat ID, private chat ID, and bot token.

    Raises:
        ValueError: If the credentials are incomplete or missing.
    """
    load_dotenv(".env")
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    group_chat_id = (
        os.getenv("TELEGRAM_GROUP_CHAT_ID") if config.SEND_TELEGRAM_GROUP else None
    )
    private_chat_id = (
        os.getenv("TELEGRAM_PRIVATE_CHAT_ID") if config.SEND_TELEGRAM_PRIVATE else None
    )

    if (
        not bot_token
        or (config.SEND_TELEGRAM_GROUP and not group_chat_id)
        or (config.SEND_TELEGRAM_PRIVATE and not private_chat_id)
    ):
        logging.error("Credenciais do Telegram incompletas no .env")
        raise ValueError("Credenciais do Telegram incompletas no .env")
    return group_chat_id, private_chat_id, bot_token


# Carrega o dicionário de substituição de nomes de disciplinas
def load_discipline_replacements():
    """
    Loads the discipline replacements dictionary from a JSON file.

    Returns:
        dict: A dictionary of discipline replacements, or an empty dictionary if the file is not found.
    """
    try:
        with open("discipline_replacements.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        logging.warning(
            "Arquivo discipline_replacements.json não encontrado. Usando substituições padrão."
        )
        return {}
    except Exception as e:
        logging.error(f"Erro ao carregar discipline_replacements.json: {e}")
        return {}


# Substitui o nome da disciplina com base no dicionário
def replace_discipline_name(discipline_name, replacements):
    """
    Replaces the discipline name using the replacements dictionary.

    Args:
        discipline_name (str): The original discipline name.
        replacements (dict): The dictionary of replacements.

    Returns:
        str: The replaced discipline name, or the original name if no replacement is found.
    """
    return replacements.get(discipline_name, discipline_name)


# Gera mensagem pro grupo
def generate_group_message(changes):
    """
    Generates a Telegram message for the group chat summarizing the changes.

    Args:
        changes (dict): A dictionary of changes in grades.

    Returns:
        str: The formatted message, or None if there are no changes.
    """
    if not changes:
        return None
    replacements = load_discipline_replacements()
    disciplines = []
    for component, updates in changes.items():
        discipline_name = component.split(" - ")[1].split(" (")[
            0
        ]  # Extract discipline name
        discipline_name = replace_discipline_name(discipline_name, replacements)
        for update in updates:
            for key in update:
                if "Unid." in key:
                    parts = key.split(" ")
                    if (
                        len(parts) > 2
                    ):  # Check if there is something after "Unid. ~Numero~"
                        subdivision = parts[-1]
                        discipline_name += f" ({subdivision})"
        disciplines.append(discipline_name)
    disciplines = sorted(set(disciplines))  # Remove duplicates and sort
    return "*Novas notas foram adicionadas ao SIGAA:*\n\n" + "\n".join(
        f"{i + 1}. {d}" for i, d in enumerate(disciplines)
    )


# Gera mensagem pro chat pessoal
def generate_private_message(changes):
    """
    Generates a Telegram message for the private chat with detailed changes.

    Args:
        changes (dict): A dictionary of changes in grades.

    Returns:
        str: The formatted message, or None if there are no changes.
    """
    if not changes:
        return None
    replacements = load_discipline_replacements()
    updates = {}
    for component, changes_list in changes.items():
        discipline_name = component.split(" - ")[1].split(" (")[
            0
        ]  # Extract discipline name
        discipline_name = replace_discipline_name(discipline_name, replacements)
        for change in changes_list:
            for key, value in change.items():
                if "Unid." in key:
                    parts = key.split(" ")
                    if (
                        len(parts) > 2
                    ):  # Check if there is something after "Unid. ~Numero~"
                        subdivision = parts[-1]
                        discipline_name += f" ({subdivision})"
                updates.setdefault(discipline_name, []).append(
                    value["new"]
                )  # Add the new value
    return "*Novas notas foram adicionadas ao SIGAA:*\n\n" + "\n".join(
        f"{i + 1}. {d}: {', '.join(ns)}" for i, (d, ns) in enumerate(updates.items())
    )


# Envia mensagem pro Telegram
def send_telegram_message(message, chat_id, bot_token):
    """
    Sends a message to a Telegram chat.

    Args:
        message (str): The message to send.
        chat_id (str): The Telegram chat ID.
        bot_token (str): The Telegram bot token.
    """
    try:
        requests.post(
            f"https://api.telegram.org/bot{bot_token}/sendMessage",
            json={"chat_id": chat_id, "text": message, "parse_mode": "Markdown"},
            timeout=5,
        ).raise_for_status()
        logging.debug(f"Mensagem enviada para {chat_id}")
    except Exception as e:
        logging.error(f"Erro ao enviar mensagem para {chat_id}: {e}")


# Notifica mudanças
def notify_changes(changes):
    """
    Sends notifications to Telegram chats about the changes in grades.

    Args:
        changes (dict): A dictionary of changes in grades.
    """
    if not changes or not (config.SEND_TELEGRAM_GROUP or config.SEND_TELEGRAM_PRIVATE):
        return
    group_chat_id, private_chat_id, bot_token = get_telegram_credentials()

    if config.SEND_TELEGRAM_GROUP and group_chat_id:
        send_telegram_message(generate_group_message(changes), group_chat_id, bot_token)
    if config.SEND_TELEGRAM_PRIVATE and private_chat_id:
        send_telegram_message(
            generate_private_message(changes), private_chat_id, bot_token
        )
