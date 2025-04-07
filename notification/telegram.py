import os
import logging
import requests
import hashlib
from typing import Dict, Any, List, Tuple, Optional, Union
import config
from functools import wraps
from utils.file_handler import load_discipline_replacements

# Constantes
TELEGRAM_API_BASE = "https://api.telegram.org/bot"
TELEGRAM_BOT_TOKEN_ENV = "TELEGRAM_BOT_TOKEN"
TELEGRAM_GROUP_CHAT_ID_ENV = "TELEGRAM_GROUP_CHAT_ID"
TELEGRAM_PRIVATE_CHAT_ID_ENV = "TELEGRAM_PRIVATE_CHAT_ID"
REQUEST_TIMEOUT = 10  # segundos
MAX_MESSAGE_LENGTH = 4000


def with_retry(max_attempts=2, delay_seconds=1):
    """
    Decorator para fazer retry em funções de rede.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_attempts:
                        logging.warning(
                            f"Tentativa {attempt} falhou: {str(e)[:50]}...", 
                            extra={
                                "details": f"function={func.__name__}, retry_in={delay_seconds}s"
                            }
                        )
                        import time
                        time.sleep(delay_seconds)
                        
            # Se chegou aqui, todas as tentativas falharam
            logging.error(
                f"Todas as {max_attempts} tentativas falharam",
                exc_info=last_exception,
                extra={"details": f"function={func.__name__}"}
            )
            # Permitir que a função original retorne silenciosamente, já que logamos o erro
            return None
        return wrapper
    return decorator


def mask_chat_id(chat_id: str) -> str:
    """
    Mascara o ID do chat para logs.
    """
    if not chat_id:
        return "none"
    
    if chat_id.startswith("-"):  # Grupo
        return f"-****{chat_id[-4:]}"
    else:  # Chat privado
        return f"****{chat_id[-4:]}"


def get_telegram_credentials() -> Tuple[Optional[str], Optional[str], str]:
    """
    Obtém credenciais do Telegram das variáveis de ambiente.

    Returns:
        tuple: (group_chat_id, private_chat_id, bot_token)
        
    Raises:
        ValueError: Se as credenciais estiverem incompletas.
    """
    bot_token = os.getenv(TELEGRAM_BOT_TOKEN_ENV)
    group_chat_id = (
        os.getenv(TELEGRAM_GROUP_CHAT_ID_ENV) if config.SEND_TELEGRAM_GROUP else None
    )
    private_chat_id = (
        os.getenv(TELEGRAM_PRIVATE_CHAT_ID_ENV) if config.SEND_TELEGRAM_PRIVATE else None
    )

    # Validar token do bot (sempre necessário)
    if not bot_token:
        error_msg = f"Token do bot Telegram não encontrado na variável {TELEGRAM_BOT_TOKEN_ENV}"
        logging.error(error_msg, extra={"details": "file=.env"})
        raise ValueError(error_msg)
    
    # Validar IDs de chat conforme configuração
    if config.SEND_TELEGRAM_GROUP and not group_chat_id:
        warning_msg = f"ID do chat de grupo não encontrado, mas notificação está habilitada"
        logging.warning(warning_msg, extra={"details": f"env={TELEGRAM_GROUP_CHAT_ID_ENV}"})
    
    if config.SEND_TELEGRAM_PRIVATE and not private_chat_id:
        warning_msg = f"ID do chat privado não encontrado, mas notificação está habilitada"
        logging.warning(warning_msg, extra={"details": f"env={TELEGRAM_PRIVATE_CHAT_ID_ENV}"})
    
    # Se nenhum dos canais estiver disponível, não faz sentido continuar
    if not group_chat_id and not private_chat_id:
        error_msg = "Nenhum canal de notificação Telegram disponível"
        logging.error(error_msg)
        raise ValueError(error_msg)
        
    logging.info(
        f"Credenciais Telegram carregadas",
        extra={
            "details": (
                f"group={'enabled' if group_chat_id else 'disabled'}, "
                f"private={'enabled' if private_chat_id else 'disabled'}"
            )
        }
    )
    return group_chat_id, private_chat_id, bot_token


def replace_discipline_name(discipline_name: str, replacements: Dict[str, str]) -> str:
    """
    Substitui nomes de disciplinas usando dicionário de substituições.

    Args:
        discipline_name: Nome original da disciplina
        replacements: Dicionário de substituições

    Returns:
        str: Nome substituído ou o original se não houver substituição
    """
    return replacements.get(discipline_name, discipline_name)


def generate_message(
    changes: Dict[str, Any], 
    replacements: Dict[str, str], 
    detailed: bool = False
) -> Optional[str]:
    """
    Gera uma mensagem para o Telegram com base nas alterações de notas.

    Args:
        changes: Dicionário de alterações nas notas
        replacements: Dicionário de substituições de nomes de disciplinas
        detailed: Se deve incluir informações detalhadas de notas

    Returns:
        str: Mensagem formatada ou None se não houver alterações
    """
    if not changes:
        return None

    updates = {}

    for component, changes_list in changes.items():
        # Extrair e formatar nome da disciplina
        try:
            # Tentar extrair o nome da disciplina do formato padrão
            discipline_name = component.split(" - ")[1].split(" (")[0]
            discipline_name = replace_discipline_name(discipline_name, replacements)
        except (IndexError, AttributeError):
            # Usar o nome completo se não for possível extrair
            discipline_name = replace_discipline_name(component, replacements)

        # Processar cada alteração
        if isinstance(changes_list, list):
            for change in changes_list:
                for key, value in change.items():
                    if "Unid." in key:
                        # Identificar subdivisão (ex: "Unid. 1 Prova" -> "Prova")
                        parts = key.split(" ")
                        if len(parts) > 2:
                            subdivision = parts[-1]
                            discipline_entry = f"{discipline_name} ({subdivision})"
                        else:
                            discipline_entry = discipline_name

                        # Adicionar ao dicionário de atualizações
                        if discipline_entry not in updates:
                            updates[discipline_entry] = []
                        updates[discipline_entry].append(value["new"])
        elif isinstance(changes_list, dict) and "status" in changes_list:
            # Lidar com status especiais (novo componente, removido, etc.)
            status = changes_list["status"]
            if status == "Novo componente" and "data" in changes_list:
                # Mostrar que é um novo componente
                if discipline_name not in updates:
                    updates[discipline_name] = ["Novo componente"]
            elif status == "Alterado" and "new" in changes_list:
                # Mostrar que foi alterado
                if discipline_name not in updates:
                    updates[discipline_name] = ["Atualizado"]

    # Construir a mensagem
    if not updates:
        return None

    message = "*Novas notas foram adicionadas ao SIGAA:*\n\n"
    
    for i, (discipline, grades) in enumerate(sorted(updates.items())):
        if detailed and grades and not any(g in ["Novo componente", "Atualizado"] for g in grades):
            # Formato detalhado com notas
            message += f"{i + 1}. {discipline}: *{', '.join(grades)}*\n"
        else:
            # Formato simples, apenas disciplina
            status = ""
            if grades and any(g in ["Novo componente", "Atualizado"] for g in grades):
                status = f" ({grades[0]})"
            message += f"{i + 1}. {discipline}{status}\n"

    # Garantir que a mensagem não exceda o limite do Telegram
    if len(message) > MAX_MESSAGE_LENGTH:
        message = message[:MAX_MESSAGE_LENGTH - 100] + "...\n\n*Mensagem truncada devido ao tamanho*"

    return message


@with_retry()
def send_telegram_message(message: Optional[str], chat_id: str, bot_token: str) -> bool:
    """
    Envia mensagem para um chat do Telegram.

    Args:
        message: Mensagem a ser enviada
        chat_id: ID do chat do Telegram
        bot_token: Token do bot do Telegram
        
    Returns:
        bool: True se a mensagem foi enviada com sucesso, False caso contrário
    """
    if not message or not chat_id or not bot_token:
        return False

    try:
        masked_chat = mask_chat_id(chat_id)
        
        response = requests.post(
            f"{TELEGRAM_API_BASE}{bot_token}/sendMessage",
            json={
                "chat_id": chat_id,
                "text": message, 
                "parse_mode": "Markdown",
                "disable_web_page_preview": True
            },
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        
        msg_length = len(message)
        logging.info(
            f"Mensagem enviada com sucesso",
            extra={
                "details": f"chat_id={masked_chat}, length={msg_length} chars"
            }
        )
        return True
        
    except requests.exceptions.RequestException as e:
        error_msg = str(e)
        
        # Tentar extrair código e mensagem de erro da API Telegram
        try:
            error_data = e.response.json()
            if "description" in error_data:
                error_msg = f"{error_data.get('error_code', 'Error')}: {error_data['description']}"
        except:
            pass
            
        logging.error(
            f"Erro na API do Telegram: {error_msg}",
            extra={
                "details": f"chat_id={mask_chat_id(chat_id)}"
            }
        )
        return False
        
    except Exception as e:
        logging.error(
            f"Erro ao enviar mensagem: {e}",
            exc_info=True,
            extra={"details": f"chat_id={mask_chat_id(chat_id)}"}
        )
        return False


def notify_changes(changes: Dict[str, Any]) -> None:
    """
    Envia notificações sobre alterações de notas para o Telegram.

    Args:
        changes: Dicionário de alterações nas notas
    """
    if not changes:
        logging.info("Sem alterações para notificar")
        return
        
    if not (config.SEND_TELEGRAM_GROUP or config.SEND_TELEGRAM_PRIVATE):
        logging.info("Notificações do Telegram desabilitadas nas configurações")
        return

    try:
        group_chat_id, private_chat_id, bot_token = get_telegram_credentials()
        replacements = load_discipline_replacements()
        
        notifications_sent = 0

        # Enviar para o chat de grupo
        if config.SEND_TELEGRAM_GROUP and group_chat_id:
            group_message = generate_message(changes, replacements, detailed=False)
            if group_message and send_telegram_message(group_message, group_chat_id, bot_token):
                notifications_sent += 1

        # Enviar para o chat privado
        if config.SEND_TELEGRAM_PRIVATE and private_chat_id:
            private_message = generate_message(changes, replacements, detailed=True)
            if private_message and send_telegram_message(private_message, private_chat_id, bot_token):
                notifications_sent += 1

        logging.info(
            f"Notificações processadas",
            extra={"details": f"sent={notifications_sent}, changes={len(changes)}"}
        )

    except Exception as e:
        logging.error(
            f"Erro ao processar notificações: {e}",
            exc_info=True,
            extra={"details": "function=notify_changes"}
        )
