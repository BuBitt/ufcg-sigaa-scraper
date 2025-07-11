"""
Módulo de notificação via Telegram.
"""

import logging
from typing import Dict, List, Optional, Set

import requests

from src.config.settings import Config
from src.utils.env_singleton import get_env


class TelegramNotifier:
    """
    Lida com notificações do Telegram para mudanças de notas do SIGAA.
    
    Esta classe gerencia a formatação e envio de notificações para ambos
    chats de grupo e chats privados quando novas notas são detectadas.
    """

    def __init__(self) -> None:
        """Inicializa o notificador do Telegram com credenciais."""
        self._load_credentials()

    def _load_credentials(self) -> None:
        """Carrega e valida credenciais do Telegram do ambiente."""
        self.bot_token = get_env("TELEGRAM_BOT_TOKEN")
        self.group_chat_id = (
            get_env("TELEGRAM_GROUP_CHAT_ID") 
            if Config.SEND_TELEGRAM_GROUP 
            else None
        )
        self.private_chat_id = (
            get_env("TELEGRAM_PRIVATE_CHAT_ID") 
            if Config.SEND_TELEGRAM_PRIVATE 
            else None
        )

        # Valida credenciais necessárias
        missing_credentials = []
        if not self.bot_token:
            missing_credentials.append("TELEGRAM_BOT_TOKEN")
        if Config.SEND_TELEGRAM_GROUP and not self.group_chat_id:
            missing_credentials.append("TELEGRAM_GROUP_CHAT_ID")
        if Config.SEND_TELEGRAM_PRIVATE and not self.private_chat_id:
            missing_credentials.append("TELEGRAM_PRIVATE_CHAT_ID")

        if missing_credentials:
            error_msg = f"Credenciais do Telegram faltando: {', '.join(missing_credentials)}"
            logging.error(error_msg)
            raise ValueError(error_msg)

    def _extract_disciplines_from_changes(self, changes: List[str]) -> Set[str]:
        """
        Extrai nomes únicos de disciplinas das descrições de mudanças.
        
        Args:
            changes: Lista de strings de descrição de mudanças
            
        Returns:
            Conjunto de nomes únicos de disciplinas
        """
        disciplines = set()
        for change in changes:
            try:
                # Extrai nome da disciplina da descrição de mudança
                # Formato: "Alteração em NOME_DISCIPLINA (CODIGO) - ..."
                discipline_part = change.split(" - ")[0]
                discipline_name = discipline_part.replace("Alteração em ", "")
                discipline_name = discipline_name.split(" (")[0].strip()
                disciplines.add(discipline_name)
            except (IndexError, AttributeError) as e:
                logging.warning(f"Não foi possível analisar disciplina da mudança: {change}, erro: {e}")
                
        return disciplines

    def _extract_grade_updates_from_changes(self, changes: List[str]) -> Dict[str, List[str]]:
        """
        Extrai atualizações de notas organizadas por disciplina.
        
        Args:
            changes: Lista de strings de descrição de mudanças
            
        Returns:
            Dicionário mapeando nomes de disciplinas para listas de novas notas
        """
        updates = {}
        for change in changes:
            try:
                parts = change.split(" - ")
                if len(parts) < 2:
                    continue
                    
                discipline_part = parts[0].replace("Alteração em ", "")
                discipline_name = discipline_part.split(" (")[0].strip()
                
                # Extrai o valor da nova nota
                grade_part = parts[1]
                if " mudou de " in grade_part and " para " in grade_part:
                    new_grade = grade_part.split(" para ")[1].strip("'")
                    updates.setdefault(discipline_name, []).append(f"*{new_grade}*")
                    
            except (IndexError, AttributeError) as e:
                logging.warning(f"Não foi possível analisar nota da mudança: {change}, erro: {e}")
                
        return updates

    def generate_group_message(self, changes: List[str]) -> Optional[str]:
        """
        Gera uma mensagem para notificações de chat em grupo.
        
        Args:
            changes: Lista de descrições de mudanças
            
        Returns:
            String da mensagem formatada ou None se não houver mudanças
        """
        if not changes:
            return None
            
        disciplines = sorted(self._extract_disciplines_from_changes(changes))
        if not disciplines:
            return None
            
        message_lines = ["*Novas notas foram adicionadas ao SIGAA:*", ""]
        message_lines.extend(
            f"{i+1}. {discipline}" 
            for i, discipline in enumerate(disciplines)
        )
        
        return "\n".join(message_lines)

    def generate_private_message(self, changes: List[str]) -> Optional[str]:
        """
        Gera uma mensagem detalhada para notificações de chat privado.
        
        Args:
            changes: Lista de descrições de mudanças
            
        Returns:
            String da mensagem formatada ou None se não houver mudanças
        """
        if not changes:
            return None
            
        updates = self._extract_grade_updates_from_changes(changes)
        if not updates:
            return None
            
        message_lines = ["*Novas notas foram adicionadas ao SIGAA:*", ""]
        message_lines.extend(
            f"{i+1}. {discipline}: {', '.join(grades)}"
            for i, (discipline, grades) in enumerate(updates.items())
        )
        
        return "\n".join(message_lines)

    def send_message(self, message: str, chat_id: str) -> bool:
        """
        Envia uma mensagem para um chat específico do Telegram.
        
        Args:
            message: Texto da mensagem para enviar
            chat_id: ID do chat do Telegram
            
        Returns:
            True se a mensagem foi enviada com sucesso, False caso contrário
        """
        try:
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            payload = {
                "chat_id": chat_id,
                "text": message,
                "parse_mode": "Markdown"
            }
            
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
            
            logging.debug(f"Mensagem enviada com sucesso para o chat {chat_id}")
            return True
            
        except requests.exceptions.RequestException as e:
            logging.error(f"Erro HTTP ao enviar mensagem para o chat {chat_id}: {e}")
            return False
        except Exception as e:
            logging.error(f"Erro inesperado ao enviar mensagem para o chat {chat_id}: {e}")
            return False

    def notify_changes(self, changes: List[str]) -> None:
        """
        Envia notificações sobre mudanças de notas para chats configurados.
        
        Args:
            changes: Lista de descrições de mudanças para notificar
        """
        if not changes:
            logging.info("Nenhuma mudança para notificar")
            return
            
        if not (Config.SEND_TELEGRAM_GROUP or Config.SEND_TELEGRAM_PRIVATE):
            logging.info("Notificações do Telegram estão desabilitadas")
            return

        notifications_sent = 0

        # Envia notificação do grupo
        if Config.SEND_TELEGRAM_GROUP and self.group_chat_id:
            group_message = self.generate_group_message(changes)
            if group_message and self.send_message(group_message, self.group_chat_id):
                notifications_sent += 1
                logging.info("Notificação do grupo enviada com sucesso")
            else:
                logging.error("Falha ao enviar notificação do grupo")

        # Envia notificação privada
        if Config.SEND_TELEGRAM_PRIVATE and self.private_chat_id:
            private_message = self.generate_private_message(changes)
            if private_message and self.send_message(private_message, self.private_chat_id):
                notifications_sent += 1
                logging.info("Notificação privada enviada com sucesso")
            else:
                logging.error("Falha ao enviar notificação privada")

        logging.info(f"Enviadas {notifications_sent} notificação(ões) para {len(changes)} mudança(s)")
