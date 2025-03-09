import os
import logging
import requests
from dotenv import load_dotenv
import config

# Configuração do logging
logging.basicConfig(
    level=config.LOG_DEPTH,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(config.LOG_FILENAME, mode="a"),
        logging.StreamHandler(),
    ],
)


def load_env_file(file_path=".env"):
    try:
        load_dotenv(file_path)
        logging.info(f"Arquivo .env carregado com sucesso: {file_path}")
    except Exception as e:
        logging.error(f"Erro ao carregar o arquivo .env: {str(e)}")
        raise


def get_telegram_credentials():
    load_env_file()
    group_chat_id = os.getenv("TELEGRAM_GROUP_CHAT_ID")
    private_chat_id = os.getenv("TELEGRAM_PRIVATE_CHAT_ID")
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")

    if not bot_token:
        logging.error("TELEGRAM_BOT_TOKEN deve ser definido no arquivo .env")
        raise ValueError("TELEGRAM_BOT_TOKEN deve ser definido no arquivo .env")

    if config.SEND_TELEGRAM_GROUP and not group_chat_id:
        logging.error(
            "TELEGRAM_GROUP_CHAT_ID deve ser definido no arquivo .env para envio ao grupo"
        )
        raise ValueError("TELEGRAM_GROUP_CHAT_ID deve ser definido no arquivo .env")

    if config.SEND_TELEGRAM_PRIVATE and not private_chat_id:
        logging.error(
            "TELEGRAM_PRIVATE_CHAT_ID deve ser definido no arquivo .env para envio ao chat privado"
        )
        raise ValueError("TELEGRAM_PRIVATE_CHAT_ID deve ser definido no arquivo .env")

    return group_chat_id, private_chat_id, bot_token


def generate_group_message(changes):
    if not changes:
        return None

    # Extrai disciplinas únicas com alterações
    disciplines = set()
    for change in changes:
        discipline_part = (
            change.split(" - ")[0].replace("Alteração em ", "").split(" (")[0]
        )
        disciplines.add(discipline_part)

    message = "*Novas notas foram adicionadas ao SIGAA:*\n\n"
    message += "\n".join(
        [f"{i+1}. {discipline}" for i, discipline in enumerate(sorted(disciplines))]
    )
    return message


def generate_private_message(changes):
    if not changes:
        return None

    # Agrupa alterações por disciplina
    updates_by_discipline = {}
    for change in changes:
        parts = change.split(" - ")
        discipline_part = parts[0].replace("Alteração em ", "").split(" (")[0]
        details = parts[1].split(": ")
        new_value = details[1].split(" mudou de ")[1].split(" para ")[1].strip("'")
        if discipline_part not in updates_by_discipline:
            updates_by_discipline[discipline_part] = []
        updates_by_discipline[discipline_part].append(new_value)

    # Gera mensagem com todas as notas por disciplina
    updates = []
    for discipline, notes in updates_by_discipline.items():
        notes_str = ", ".join([f"*{note}*" for note in notes])
        updates.append(f"{discipline}: {notes_str}")

    message = "*Novas notas foram adicionadas ao SIGAA:*\n\n"
    message += "\n".join([f"{i+1}. {update}" for i, update in enumerate(updates)])
    return message


def send_telegram_message(message, chat_id, bot_token):
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message, "parse_mode": "Markdown"}
    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            logging.info(f"Mensagem enviada com sucesso para o chat {chat_id}")
        else:
            logging.error(
                f"Falha ao enviar mensagem para o chat {chat_id}: {response.status_code} - {response.text}"
            )
    except Exception as e:
        logging.error(f"Erro ao enviar mensagem para o chat {chat_id}: {str(e)}")


def notify_changes(changes):
    if not (config.SEND_TELEGRAM_GROUP or config.SEND_TELEGRAM_PRIVATE):
        logging.info(
            "Envio para Telegram desativado em config.py (SEND_TELEGRAM_GROUP e SEND_TELEGRAM_PRIVATE = False)"
        )
        return

    if not changes:
        logging.info(
            "Nenhuma mudança em notas detectada, nenhuma mensagem será enviada ao Telegram"
        )
        return

    try:
        group_chat_id, private_chat_id, bot_token = get_telegram_credentials()

        # Envio pro grupo
        if config.SEND_TELEGRAM_GROUP:
            group_message = generate_group_message(changes)
            if group_message:
                send_telegram_message(group_message, group_chat_id, bot_token)

        # Envio pro chat privado
        if config.SEND_TELEGRAM_PRIVATE:
            private_message = generate_private_message(changes)
            if private_message:
                send_telegram_message(private_message, private_chat_id, bot_token)

    except Exception as e:
        logging.error(f"Erro no processo de notificação: {str(e)}")
