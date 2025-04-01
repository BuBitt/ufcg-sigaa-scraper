import os
import logging
import requests
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


# Gera mensagem pro grupo
def generate_group_message(changes):
    if not changes:
        return None
    disciplines = sorted(
        {c.split(" - ")[0].replace("Alteração em ", "").split(" (")[0] for c in changes}
    )
    return "*Novas notas foram adicionadas ao SIGAA:*\n\n" + "\n".join(
        f"{i + 1}. {d}" for i, d in enumerate(disciplines)
    )


# Gera mensagem pro chat pessoal
def generate_private_message(changes):
    if not changes:
        return None
    updates = {}
    for c in changes:
        parts = c.split(" - ")
        discipline = parts[0].replace("Alteração em ", "").split(" (")[0]
        note = parts[1].split(" mudou de ")[1].split(" para ")[1].strip("'")
        updates.setdefault(discipline, []).append(f"*{note}*")
    return "*Novas notas foram adicionadas ao SIGAA:*\n\n" + "\n".join(
        f"{i + 1}. {d}: {', '.join(ns)}" for i, (d, ns) in enumerate(updates.items())
    )


# Envia mensagem pro Telegram
def send_telegram_message(message, chat_id, bot_token):
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
    if not changes or not (config.SEND_TELEGRAM_GROUP or config.SEND_TELEGRAM_PRIVATE):
        return
    group_chat_id, private_chat_id, bot_token = get_telegram_credentials()

    if config.SEND_TELEGRAM_GROUP and group_chat_id:
        send_telegram_message(generate_group_message(changes), group_chat_id, bot_token)
    if config.SEND_TELEGRAM_PRIVATE and private_chat_id:
        send_telegram_message(
            generate_private_message(changes), private_chat_id, bot_token
        )
