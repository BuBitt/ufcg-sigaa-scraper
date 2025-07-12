"""
Notificador via Telegram para mudanças nas notas.
"""

import requests
from typing import List, Dict, Any, Optional

from src.config.settings import Config
from src.utils.env_loader import get_env_loader
from src.utils.logger import get_logger


class TelegramNotifier:
    """Envia notificações via Telegram."""
    
    def __init__(self) -> None:
        """Inicializa o notificador Telegram."""
        self.logger = get_logger("telegram")
        self.env_loader = get_env_loader()
        self.config = self.env_loader.get_telegram_config()
        self.logger.debug("🔧 Notificador Telegram inicializado")
    
    def notify_changes(self, changes: List[str]) -> bool:
        """
        Envia notificações sobre mudanças detectadas.
        
        Args:
            changes: Lista de mudanças detectadas
            
        Returns:
            bool: True se pelo menos uma notificação foi enviada com sucesso
        """
        if not changes:
            self.logger.info("ℹ️  Nenhuma mudança para notificar")
            return True
        
        try:
            self.logger.info(f"📬 Enviando notificações para {len(changes)} mudança(s)")
            
            success_count = 0
            
            # Enviar para grupo (resumo)
            if Config.SEND_TELEGRAM_GROUP and self.config.get("group_chat_id"):
                if self._send_group_notification(changes):
                    success_count += 1
            
            # Enviar para chat privado (detalhado)
            if Config.SEND_TELEGRAM_PRIVATE and self.config.get("private_chat_id"):
                if self._send_private_notification(changes):
                    success_count += 1
            
            if success_count > 0:
                self.logger.info(f"✅ {success_count} notificação(ões) enviada(s) com sucesso")
                return True
            else:
                self.logger.warning("⚠️  Nenhuma notificação foi enviada")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Erro ao enviar notificações: {e}", exc_info=True)
            return False
    
    def _send_group_notification(self, changes: List[str]) -> bool:
        """
        Envia notificação resumida para grupo.
        
        Args:
            changes: Lista de mudanças
            
        Returns:
            bool: True se enviado com sucesso
        """
        try:
            # Criar mensagem resumida
            message = self._format_group_message(changes)
            
            chat_id = self.config["group_chat_id"]
            success = self._send_message(chat_id, message)
            
            if success:
                self.logger.info("📢 Notificação de grupo enviada")
            else:
                self.logger.error("❌ Falha ao enviar notificação de grupo")
            
            return success
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao enviar notificação de grupo: {e}")
            return False
    
    def _send_private_notification(self, changes: List[str]) -> bool:
        """
        Envia notificação detalhada para chat privado.
        
        Args:
            changes: Lista de mudanças
            
        Returns:
            bool: True se enviado com sucesso
        """
        try:
            # Criar mensagem detalhada
            message = self._format_private_message(changes)
            
            chat_id = self.config["private_chat_id"]
            success = self._send_message(chat_id, message)
            
            if success:
                self.logger.info("👤 Notificação privada enviada")
            else:
                self.logger.error("❌ Falha ao enviar notificação privada")
            
            return success
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao enviar notificação privada: {e}")
            return False
    
    def _format_group_message(self, changes: List[str]) -> str:
        """
        Formata mensagem para grupo (resumida).
        
        Args:
            changes: Lista de mudanças
            
        Returns:
            str: Mensagem formatada
        """
        try:
            header = "🎓 *Novas notas detectadas no SIGAA!*\n\n"
            
            # Extrair disciplinas únicas
            disciplines = set()
            for change in changes:
                # Tentar extrair nome da disciplina da mudança
                if ":" in change:
                    discipline = change.split(":")[0].strip()
                    disciplines.add(discipline)
                else:
                    disciplines.add(change)
            
            # Limitar número de disciplinas mostradas
            max_show = 10
            discipline_list = list(disciplines)[:max_show]
            
            body = ""
            for i, discipline in enumerate(discipline_list, 1):
                body += f"{i}. {discipline}\n"
            
            if len(disciplines) > max_show:
                body += f"... e mais {len(disciplines) - max_show} disciplina(s)\n"
            
            footer = f"\n📊 Total: {len(changes)} mudança(s) detectada(s)"
            
            return header + body + footer
            
        except Exception:
            return f"🎓 *Novas notas detectadas!*\n\n📊 {len(changes)} mudança(s) encontrada(s)"
    
    def _format_private_message(self, changes: List[str]) -> str:
        """
        Formata mensagem para chat privado (detalhada).
        
        Args:
            changes: Lista de mudanças
            
        Returns:
            str: Mensagem formatada
        """
        try:
            header = "🎓 *Detalhes das novas notas no SIGAA:*\n\n"
            
            body = ""
            for i, change in enumerate(changes, 1):
                # Formatar cada mudança
                formatted_change = self._format_change_detail(change)
                body += f"{i}. {formatted_change}\n"
            
            footer = f"\n📊 Total: {len(changes)} mudança(s) detectada(s)"
            footer += f"\n⏰ Verificação automática ativa"
            
            return header + body + footer
            
        except Exception:
            return f"🎓 *Notas atualizadas!*\n\n📊 {len(changes)} mudança(s) detectada(s)"
    
    def _format_change_detail(self, change: str) -> str:
        """
        Formata detalhes de uma mudança específica.
        
        Args:
            change: Descrição da mudança
            
        Returns:
            str: Mudança formatada
        """
        try:
            # Se contém nota numérica, destacar
            if any(char.isdigit() for char in change):
                # Tentar destacar valores numéricos
                import re
                change = re.sub(r'(\d+[.,]?\d*)', r'*\1*', change)
            
            # Destacar disciplinas (texto antes dos dois pontos)
            if ":" in change:
                parts = change.split(":", 1)
                if len(parts) == 2:
                    discipline = parts[0].strip()
                    detail = parts[1].strip()
                    return f"*{discipline}*: {detail}"
            
            return change
            
        except Exception:
            return change
    
    def _send_message(self, chat_id: str, message: str) -> bool:
        """
        Envia mensagem via API do Telegram.
        
        Args:
            chat_id: ID do chat
            message: Mensagem a ser enviada
            
        Returns:
            bool: True se enviado com sucesso
        """
        try:
            bot_token = self.config.get("bot_token")
            if not bot_token:
                self.logger.warning("⚠️  Token do bot não configurado")
                return False
            
            if not chat_id:
                self.logger.warning("⚠️  Chat ID não configurado")
                return False
            
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            
            payload = {
                "chat_id": chat_id,
                "text": message,
                "parse_mode": "Markdown",
                "disable_web_page_preview": True
            }
            
            self.logger.debug(f"📤 Enviando mensagem para chat {chat_id}")
            
            response = requests.post(
                url, 
                json=payload, 
                timeout=Config.REQUEST_TIMEOUT
            )
            
            if response.status_code == 200:
                self.logger.debug("✅ Mensagem enviada com sucesso")
                return True
            else:
                self.logger.error(f"❌ Erro HTTP {response.status_code}: {response.text}")
                return False
                
        except requests.exceptions.Timeout:
            self.logger.error("❌ Timeout ao enviar mensagem")
            return False
        except requests.exceptions.RequestException as e:
            self.logger.error(f"❌ Erro de rede: {e}")
            return False
        except Exception as e:
            self.logger.error(f"❌ Erro inesperado ao enviar mensagem: {e}")
            return False
    
    def test_notification(self) -> bool:
        """
        Testa conectividade com Telegram enviando mensagem de teste.
        
        Returns:
            bool: True se teste foi bem-sucedido
        """
        try:
            test_message = "🔧 *Teste de Conectividade*\n\nSIGAA Scraper funcionando corretamente!"
            
            success_count = 0
            
            # Testar grupo
            if self.config.get("group_chat_id"):
                if self._send_message(self.config["group_chat_id"], test_message + "\n\n📢 Mensagem de teste para o grupo"):
                    success_count += 1
                    self.logger.info("✅ Teste de grupo bem-sucedido")
            
            # Testar privado
            if self.config.get("private_chat_id"):
                if self._send_message(self.config["private_chat_id"], test_message + "\n\n👤 Mensagem de teste privada"):
                    success_count += 1
                    self.logger.info("✅ Teste privado bem-sucedido")
            
            return success_count > 0
            
        except Exception as e:
            self.logger.error(f"❌ Erro no teste de notificação: {e}")
            return False
