"""
Notificador via Telegram para mudanças nas notas.
"""

import requests
import json
import os
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
        self.discipline_replacements = self._load_discipline_replacements()
        self.logger.debug("Notificador Telegram inicializado")
    
    def _load_discipline_replacements(self) -> Dict[str, str]:
        """
        Carrega o arquivo de substituições de disciplinas.
        
        Returns:
            Dict[str, str]: Mapeamento de nome original para nome abreviado
        """
        try:
            import json
            import os
            
            replacements_file = os.path.join(os.getcwd(), "discipline_replacements.json")
            
            if os.path.exists(replacements_file):
                with open(replacements_file, "r", encoding="utf-8") as f:
                    replacements = json.load(f)
                    self.logger.debug(f"Carregadas {len(replacements)} substituições de disciplinas")
                    return replacements
            else:
                self.logger.debug("Arquivo de substituições não encontrado")
                return {}
                
        except Exception as e:
            self.logger.warning(f"Erro ao carregar substituições de disciplinas: {e}")
            return {}
    
    def _apply_discipline_replacement(self, discipline_name: str) -> str:
        """
        Aplica substituição de nome de disciplina se disponível.
        
        Args:
            discipline_name: Nome original da disciplina
            
        Returns:
            str: Nome substituído ou original se não há substituição
        """
        return self.discipline_replacements.get(discipline_name, discipline_name)
    
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
                self.logger.info(f"{success_count} notificação(ões) enviada(s) com sucesso")
                return True
            else:
                self.logger.warning("Nenhuma notificação foi enviada")
                return False
                
        except Exception as e:
            self.logger.error(f"Erro ao enviar notificações: {e}", exc_info=True)
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
                self.logger.info("Notificação de grupo enviada")
            else:
                self.logger.error("Falha ao enviar notificação de grupo")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Erro ao enviar notificação de grupo: {e}")
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
                self.logger.info("Notificação privada enviada")
            else:
                self.logger.error("Falha ao enviar notificação privada")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Erro ao enviar notificação privada: {e}")
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
            status_messages: List[str] = []
            for change in changes:
                discipline = None
                detail = change

                if ":" in change:
                    discipline_part, detail_part = change.split(":", 1)
                    discipline = discipline_part.strip()
                    detail = detail_part.strip()

                if any(keyword in detail.lower() for keyword in ("resultado", "situação", "situacao")):
                    discipline_display = self._apply_discipline_replacement(
                        discipline if discipline else "Disciplina"
                    )
                    message = f"🏁 *A Matéria {discipline_display} fechou!*"
                    status_messages.append(message)

            if status_messages:
                # Retorna mensagem específica para mudanças de resultado
                unique_messages = list(dict.fromkeys(status_messages))
                return "\n\n".join(unique_messages)

            header = "🎓 *Novas notas detectadas no SIGAA!*\n\n"
            
            # Extrair disciplinas únicas
            disciplines = set()
            for change in changes:
                # Tentar extrair nome da disciplina da mudança
                if ":" in change:
                    discipline = change.split(":")[0].strip()
                    # Aplicar substituição se disponível
                    discipline = self._apply_discipline_replacement(discipline)
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
            
            return header + body
            
        except Exception:
            return "🎓 *Novas notas detectadas!*"
    
    def _format_private_message(self, changes: List[str]) -> str:
        """
        Formata mensagem para chat privado (detalhada com notas).
        
        Args:
            changes: Lista de mudanças
            
        Returns:
            str: Mensagem formatada
        """
        try:
            header = "🎓 *Detalhes das novas notas no SIGAA:*\n\n"
            
            body = ""
            for i, change in enumerate(changes, 1):
                # Formatar cada mudança com detalhes das notas
                formatted_change = self._format_change_with_grades(change)
                body += f"{i}. {formatted_change}\n"
            
            footer = "\n⏰ Verificação automática ativa"
            
            return header + body + footer
            
        except Exception:
            return "🎓 *Notas atualizadas!*"
    
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
                    # Aplicar substituição se disponível
                    discipline_display = self._apply_discipline_replacement(discipline)
                    return f"*{discipline_display}*: {detail}"
            
            return change
            
        except Exception:
            return change
    
    def _format_change_with_grades(self, change: str) -> str:
        """
        Formata mudanças incluindo detalhes das notas para mensagem privada.
        
        Args:
            change: Descrição da mudança
            
        Returns:
            str: Mudança formatada com notas
        """
        try:
            # Destacar disciplinas (texto antes dos dois pontos)
            if ":" in change:
                parts = change.split(":", 1)
                if len(parts) == 2:
                    discipline = parts[0].strip()
                    detail = parts[1].strip()
                    
                    # Aplicar substituição se disponível
                    discipline_display = self._apply_discipline_replacement(discipline)
                    
                    detail_lower = detail.lower()
                    if "→" in detail and not any(
                        keyword in detail_lower for keyword in ("situação", "situacao", "resultado")
                    ):
                        # Mudança de nota (antes → depois)
                        formatted_detail = self._format_grade_change(detail)
                        return f"*{discipline_display}*: {formatted_detail}"

                    segments = [segment.strip() for segment in detail.split(";") if segment.strip()]
                    field_lines: List[str] = []

                    for segment in segments:
                        key = None
                        value = None

                        if ":" in segment:
                            key_part, value_part = segment.split(":", 1)
                            key = key_part.strip()
                            value = value_part.strip()
                        else:
                            value = segment.strip()

                        key_lower = key.lower() if key else ""

                        if key_lower and ("situação" in key_lower or "situacao" in key_lower):
                            status_value = self._extract_status_from_detail(segment)
                            if not status_value and value:
                                status_value = self._extract_final_value(value)
                            if status_value:
                                field_lines.append(f"  - Situação: {status_value}")
                            continue

                        if key_lower and "resultado" in key_lower:
                            result_value = self._extract_status_from_detail(segment)
                            if not result_value and value:
                                result_value = self._extract_final_value(value)
                            if result_value:
                                result_value = self._highlight_grades_in_text(result_value)
                                field_lines.append(f"  - Resultado: {result_value}")
                            continue

                        if key and value:
                            formatted_value = self._highlight_grades_in_text(self._extract_final_value(value) or value)
                            field_lines.append(f"  - {key}: {formatted_value}")
                        elif segment:
                            field_lines.append(f"  - {self._highlight_grades_in_text(segment)}")

                    if field_lines:
                        formatted_fields = []
                        for idx, line in enumerate(field_lines):
                            suffix = "." if idx == len(field_lines) - 1 else ";"
                            formatted_fields.append(f"{line}{suffix}")
                        formatted_body = "\n".join(formatted_fields)
                        return f"*{discipline_display}*:\n{formatted_body}"

                    if "nova nota" in detail_lower or "nota" in detail_lower:
                        # Nova nota
                        formatted_detail = self._highlight_grades_in_text(detail)
                        return f"*{discipline_display}*: {formatted_detail}"

                    # Outras mudanças
                    return f"*{discipline_display}*: {detail}"
            
            # Se não há dois pontos, verificar se contém números (notas)
            if any(char.isdigit() for char in change):
                return self._highlight_grades_in_text(change)
            
            return change
            
        except Exception:
            return change
    
    def _format_grade_change(self, detail: str) -> str:
        """
        Formata mudanças de nota (antes → depois).
        
        Args:
            detail: Detalhe da mudança
            
        Returns:
            str: Mudança formatada
        """
        try:
            import re
            # Procurar padrão "valor → valor"
            arrow_pattern = r'([^→]+)→([^→]+)'
            match = re.search(arrow_pattern, detail)
            
            if match:
                before = match.group(1).strip()
                after = match.group(2).strip()
                
                # Destacar os valores
                before_highlighted = self._highlight_grades_in_text(before)
                after_highlighted = self._highlight_grades_in_text(after)
                
                return f"{before_highlighted} → *{after_highlighted}*"
            
            return detail
            
        except Exception:
            return detail
    
    def _highlight_grades_in_text(self, text: str) -> str:
        """
        Destaca valores numéricos (notas) no texto.
        
        Args:
            text: Texto a ser processado
            
        Returns:
            str: Texto com notas destacadas
        """
        try:
            import re
            # Destacar números (possíveis notas)
            # Padrão para números com vírgula ou ponto decimal
            grade_pattern = r'(\d+[.,]?\d*)'
            highlighted = re.sub(grade_pattern, r'*\1*', text)
            return highlighted
            
        except Exception:
            return text

    def _extract_final_value(self, text: str) -> Optional[str]:
        """Extrai o valor final relevante de um fragmento de texto indicando mudança."""
        try:
            import re

            if not text:
                return None

            candidate = text.strip()
            if not candidate:
                return None

            if "→" in candidate:
                candidate = candidate.split("→")[-1].strip()

            candidate = re.sub(
                r"(?i)^(resultado|situação|situacao|status)\s*[:\-]?\s*",
                "",
                candidate,
            )

            candidate = re.sub(
                r"(?i)^(foi|ficou|passou|passando|alterado|alterada|para|como)\s+",
                "",
                candidate,
            )

            candidate = candidate.strip("-: ")

            return candidate or None

        except Exception:
            return None

    def _extract_status_from_detail(self, detail: str) -> Optional[str]:
        """
        Extrai o valor final (após alteração) de campos como Situação/Resultado.
        Retorna apenas o novo estado para uso nas mensagens.
        """
        try:
            candidate = self._extract_final_value(detail)
            if not candidate:
                return None

            if candidate.lower() in {"alterado", "alterada"}:
                return None

            return candidate

        except Exception:
            return None
    
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
                self.logger.warning("Token do bot não configurado")
                return False
            
            if not chat_id:
                self.logger.warning("Chat ID não configurado")
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
                self.logger.debug("Mensagem enviada com sucesso")
                return True
            else:
                self.logger.error(f"Erro HTTP {response.status_code}: {response.text}")
                return False
                
        except requests.exceptions.Timeout:
            self.logger.error("Timeout ao enviar mensagem")
            return False
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Erro de rede: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Erro inesperado ao enviar mensagem: {e}")
            return False
    
    def test_notification(self) -> bool:
        """
        Testa conectividade com Telegram enviando mensagem de teste.
        No GitHub Actions, apenas valida configurações sem enviar mensagem.
        
        Returns:
            bool: True se teste foi bem-sucedido
        """
        import os
        
        # Detecta se está rodando no GitHub Actions
        is_github_actions = os.getenv('GITHUB_ACTIONS', 'false').lower() == 'true'
        
        if is_github_actions:
            # No GitHub Actions, apenas valida as configurações sem enviar mensagem
            has_config = bool(
                self.config.get("bot_token") and 
                (self.config.get("group_chat_id") or self.config.get("private_chat_id"))
            )
            if has_config:
                self.logger.info("Configuração do Telegram validada (GitHub Actions - sem envio de teste)")
                return True
            else:
                self.logger.warning("Configuração do Telegram incompleta")
                return False
        
        # Em ambiente local, envia mensagem de teste normalmente
        try:
            test_message = "Teste de Conectividade\n\nSIGAA Scraper funcionando corretamente!"
            
            success_count = 0
            
            # Testar grupo
            group_chat_id = self.config.get("group_chat_id")
            if group_chat_id:
                if self._send_message(group_chat_id, test_message + "\n\nMensagem de teste para o grupo"):
                    success_count += 1
                    self.logger.info("Teste de grupo bem-sucedido")
            
            # Testar privado
            private_chat_id = self.config.get("private_chat_id")
            if private_chat_id:
                if self._send_message(private_chat_id, test_message + "\n\nMensagem de teste privada"):
                    success_count += 1
                    self.logger.info("Teste privado bem-sucedido")
            
            return success_count > 0
            
        except Exception as e:
            self.logger.error(f"Erro no teste de notificação: {e}")
            return False
    
    def notify_error(self, error_message: str, send_to_group: bool = False) -> bool:
        """
        Envia notificação de erro para o Telegram.
        Por padrão, envia apenas para chat privado.
        
        Args:
            error_message: Mensagem de erro
            send_to_group: Se True, também envia para o grupo
            
        Returns:
            bool: True se pelo menos uma notificação foi enviada com sucesso
        """
        import os
        from datetime import datetime
        
        try:
            timestamp = datetime.now().strftime("%d/%m/%Y às %H:%M:%S")
            environment = "GitHub Actions" if os.getenv('GITHUB_ACTIONS', 'false').lower() == 'true' else "Local"
            
            error_msg = f"Erro no SIGAA Scraper\n\n"
            error_msg += f"Erro: {error_message}\n\n"
            error_msg += f"Ambiente: {environment}\n"
            error_msg += f"Horário: {timestamp}"
            
            success_count = 0
            
            # Sempre tenta enviar para chat privado em caso de erro
            private_chat_id = self.config.get("private_chat_id")
            if private_chat_id:
                if self._send_message(private_chat_id, error_msg):
                    success_count += 1
                    self.logger.info("Notificação de erro enviada para chat privado")
            
            # Opcionalmente envia para grupo se solicitado
            if send_to_group:
                group_chat_id = self.config.get("group_chat_id")
                if group_chat_id:
                    if self._send_message(group_chat_id, error_msg):
                        success_count += 1
                        self.logger.info("Notificação de erro enviada para grupo")
            
            return success_count > 0
            
        except Exception as e:
            self.logger.error(f"Erro ao enviar notificação de erro: {e}")
            return False
