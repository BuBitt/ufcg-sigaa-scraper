import os
import logging
import requests
import config
from utils.file_handler import load_discipline_replacements


def get_telegram_credentials():
    """
    Get Telegram credentials from environment variables.

    Returns:
        tuple: (group_chat_id, private_chat_id, bot_token)
    """
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
        error_msg = "Credenciais do Telegram incompletas no .env"
        logging.error(error_msg)
        raise ValueError(error_msg)
    return group_chat_id, private_chat_id, bot_token


def replace_discipline_name(discipline_name, replacements):
    """
    Replace discipline names using a dictionary of replacements.

    Args:
        discipline_name (str): The original discipline name
        replacements (dict): Dictionary of name replacements

    Returns:
        str: The replaced name or the original if no replacement exists
    """
    return replacements.get(discipline_name, discipline_name)


def generate_message(changes, replacements, detailed=False):
    """
    Generate a message for Telegram based on grade changes.

    Args:
        changes (dict): Dictionary of grade changes
        replacements (dict): Dictionary of discipline name replacements
        detailed (bool): Whether to include detailed grade information

    Returns:
        str: Formatted message or None if there are no changes
    """
    if not changes:
        return None

    updates = {}

    for component, changes_list in changes.items():
        # Extract and format discipline name
        try:
            discipline_name = component.split(" - ")[1].split(" (")[0]
            discipline_name = replace_discipline_name(discipline_name, replacements)
        except IndexError:
            discipline_name = component

        # Process each change
        for change in changes_list:
            for key, value in change.items():
                if "Unid." in key:
                    parts = key.split(" ")
                    if len(parts) > 2:
                        subdivision = parts[-1]
                        discipline_entry = f"{discipline_name} ({subdivision})"
                    else:
                        discipline_entry = discipline_name

                    # Add to updates dictionary
                    if discipline_entry not in updates:
                        updates[discipline_entry] = []
                    updates[discipline_entry].append(value["new"])

    # Build the message
    message = "*Novas notas foram adicionadas ao SIGAA:*\n\n"
    for i, (discipline, grades) in enumerate(sorted(updates.items())):
        if detailed:
            message += f"{i + 1}. {discipline}: {', '.join(grades)}\n"
        else:
            message += f"{i + 1}. {discipline}\n"

    return message


def send_telegram_message(message, chat_id, bot_token):
    """
    Send a message to a Telegram chat.

    Args:
        message (str): The message to send
        chat_id (str): The Telegram chat ID
        bot_token (str): The Telegram bot token
    """
    if not message:
        return

    try:
        response = requests.post(
            f"https://api.telegram.org/bot{bot_token}/sendMessage",
            json={"chat_id": chat_id, "text": message, "parse_mode": "Markdown"},
            timeout=5,
        )
        response.raise_for_status()
        logging.debug(f"Mensagem enviada para {chat_id}")
    except Exception as e:
        logging.error(f"Erro ao enviar mensagem para {chat_id}: {e}")


def notify_changes(changes):
    """
    Send notifications about grade changes to Telegram.

    Args:
        changes (dict): Dictionary of grade changes
    """
    if not changes or not (config.SEND_TELEGRAM_GROUP or config.SEND_TELEGRAM_PRIVATE):
        return

    try:
        group_chat_id, private_chat_id, bot_token = get_telegram_credentials()
        replacements = load_discipline_replacements()

        # Send to group chat
        if config.SEND_TELEGRAM_GROUP and group_chat_id:
            group_message = generate_message(changes, replacements, detailed=False)
            send_telegram_message(group_message, group_chat_id, bot_token)

        # Send to private chat
        if config.SEND_TELEGRAM_PRIVATE and private_chat_id:
            private_message = generate_message(changes, replacements, detailed=True)
            send_telegram_message(private_message, private_chat_id, bot_token)

    except Exception as e:
        logging.error(f"Erro ao notificar mudanças: {e}")
