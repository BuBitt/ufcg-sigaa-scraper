"""
Serviço de autenticação no SIGAA.
"""

import hashlib
import time
from typing import Optional

from playwright.sync_api import Page

from src.config.settings import Config
from src.utils.env_loader import get_env_loader
from src.utils.logger import get_logger


class AuthService:
    """Serviço responsável pela autenticação no SIGAA."""
    
    def __init__(self) -> None:
        """Inicializa o serviço de autenticação."""
        self.logger = get_logger("auth")
        self.env_loader = get_env_loader()
        self.logger.debug("🔧 Serviço de autenticação inicializado")
    
    def _mask_credential(self, credential: str) -> str:
        """
        Mascarar credencial para logs seguros.
        
        Args:
            credential: Credencial a ser mascarada
            
        Returns:
            str: Credencial mascarada
        """
        if not credential or len(credential) <= 4:
            return "***"
        
        # Criar hash para identificação única mas não reversível
        hash_id = hashlib.md5(credential.encode()).hexdigest()[:6]
        visible_chars = min(3, len(credential) // 3)
        
        return f"{credential[:visible_chars]}***{hash_id}"
    
    def login(self, page: Page) -> bool:
        """
        Realiza login no SIGAA.
        
        Args:
            page: Página do navegador
            
        Returns:
            bool: True se login foi bem-sucedido
        """
        try:
            # Obter credenciais
            username, password = self.env_loader.validate_credentials()
            masked_username = self._mask_credential(username)
            
            self.logger.info(f"🔐 Iniciando login no SIGAA para usuário {masked_username}")
            
            # Navegar para página de login
            self.logger.debug("🌐 Navegando para página do SIGAA")
            page.goto(Config.SIGAA_URL)
            
            # Aguardar carregamento da página
            page.wait_for_load_state("networkidle", timeout=Config.TIMEOUT_DEFAULT)
            
            # Verificar se já está logado
            if self._is_already_logged_in(page):
                self.logger.info("✅ Usuário já está logado")
                return True
            
            # Preencher formulário de login
            self.logger.debug("📝 Preenchendo formulário de login")
            
            # Aguardar campos de login
            page.wait_for_selector("input[name='user.login']", timeout=10000)
            page.wait_for_selector("input[name='user.senha']", timeout=10000)
            
            # Preencher credenciais
            page.fill("input[name='user.login']", username)
            page.fill("input[name='user.senha']", password)
            
            # Clicar no botão de login
            self.logger.debug("🚀 Submetendo formulário de login")
            page.click("input[type='submit'][value='Acessar']")
            
            # Aguardar redirecionamento
            page.wait_for_load_state("networkidle", timeout=Config.TIMEOUT_DEFAULT)
            
            # Verificar sucesso do login
            if self._verify_login_success(page):
                self.logger.info("✅ Login realizado com sucesso")
                return True
            else:
                self.logger.error("❌ Falha na autenticação - credenciais inválidas")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Erro durante o login: {e}", exc_info=True)
            return False
    
    def _is_already_logged_in(self, page: Page) -> bool:
        """
        Verifica se o usuário já está logado.
        
        Args:
            page: Página do navegador
            
        Returns:
            bool: True se já está logado
        """
        try:
            # Procurar por elementos que indicam que está logado
            login_indicators = [
                "#menu_form_menu_discente_discente_menu",
                "a:has-text('Portal Discente')",
                ".menuHeader"
            ]
            
            for indicator in login_indicators:
                if page.locator(indicator).count() > 0:
                    return True
            
            return False
            
        except Exception:
            return False
    
    def _verify_login_success(self, page: Page) -> bool:
        """
        Verifica se o login foi bem-sucedido.
        
        Args:
            page: Página do navegador
            
        Returns:
            bool: True se login foi bem-sucedido
        """
        try:
            # Aguardar um pouco para carregamento
            time.sleep(2)
            
            # Verificar presença de elementos pós-login
            success_indicators = [
                "#menu_form_menu_discente_discente_menu",
                "span:has-text('Portal Discente')",
                ".menuHeader"
            ]
            
            for indicator in success_indicators:
                try:
                    page.wait_for_selector(indicator, timeout=5000)
                    self.logger.debug(f"✅ Indicador de sucesso encontrado: {indicator}")
                    return True
                except:
                    continue
            
            # Verificar se ainda está na página de login (falha)
            if page.locator("input[name='user.login']").count() > 0:
                self.logger.error("❌ Ainda na página de login - credenciais incorretas")
                return False
            
            # Verificar mensagens de erro
            error_selectors = [
                ".erroFormulario",
                ".mensagemErro",
                "div:has-text('Dados de acesso inválidos')"
            ]
            
            for error_selector in error_selectors:
                if page.locator(error_selector).count() > 0:
                    error_text = page.locator(error_selector).first.text_content()
                    self.logger.error(f"❌ Erro de login detectado: {error_text}")
                    return False
            
            # Se chegou até aqui, assumir sucesso
            self.logger.debug("✅ Login parece ter sido bem-sucedido")
            return True
            
        except Exception as e:
            self.logger.warning(f"⚠️  Erro na verificação de login: {e}")
            return False
