"""
Serviço de autenticação no SIGAA.
"""

import logging
from playwright.sync_api import Page

from src.config.settings import Config
from src.utils.env_singleton import get_env


class AuthService:
    """Gerencia a autenticação no sistema SIGAA."""
    
    def __init__(self) -> None:
        """Inicializa o serviço de autenticação."""
        self.logger = logging.getLogger("auth")
        self.logger.debug("🔧 Inicializando serviço de autenticação")
        
        self.username = get_env("SIGAA_USERNAME")
        self.password = get_env("SIGAA_PASSWORD")
        
        if not self.username or not self.password:
            self.logger.error("❌ Credenciais do SIGAA não encontradas")
            self.logger.info("💡 Defina SIGAA_USERNAME e SIGAA_PASSWORD no arquivo .env")
            raise ValueError("SIGAA_USERNAME e SIGAA_PASSWORD devem estar definidos no .env")
        
        self.logger.info(f"✅ Credenciais carregadas para usuário: {self.username}")
    
    def login(self, page: Page) -> None:
        """
        Realiza login no SIGAA.
        
        Args:
            page: Objeto page do Playwright
            
        Raises:
            Exception: Se o login falhar
        """
        self.logger.info("🌐 Acessando página do SIGAA")
        self.logger.debug(f"🔗 URL: {Config.SIGAA_URL}")
        
        try:
            page.goto(Config.SIGAA_URL, wait_until="domcontentloaded")
            self.logger.debug("✅ Página carregada com sucesso")
        except Exception as e:
            self.logger.error(f"❌ Falha ao acessar SIGAA: {e}")
            raise

        self.logger.info("🔐 Preenchendo credenciais de login")
        try:
            page.fill("input[name='user.login']", self.username or "")
            page.fill("input[name='user.senha']", self.password or "")
            self.logger.debug("✅ Credenciais preenchidas")
        except Exception as e:
            self.logger.error(f"❌ Falha ao preencher credenciais: {e}")
            raise

        self.logger.info("🚀 Enviando formulário de login")
        try:
            page.click("input[type='submit']", timeout=Config.TIMEOUT_DEFAULT)
            self.logger.debug("✅ Formulário enviado")
        except Exception as e:
            self.logger.error(f"❌ Falha ao enviar formulário: {e}")
            raise

        self.logger.debug("🔍 Verificando modais do sistema")
        try:
            # Tenta lidar com modal "Ciente"
            modal_ciente = page.locator("button.btn-primary:has-text('Ciente')")
            if modal_ciente.is_visible(timeout=5000):
                self.logger.debug("🔧 Modal 'Ciente' detectado, clicando...")
                modal_ciente.click(timeout=5000, force=True)
                self.logger.debug("✅ Modal 'Ciente' fechado")
            
            # Tenta lidar com outro modal comum
            modal_auto = page.locator("#yuievtautoid-0")
            if modal_auto.is_visible(timeout=5000):
                self.logger.debug("🔧 Modal auto detectado, clicando...")
                modal_auto.click(timeout=5000, force=True)
                self.logger.debug("✅ Modal auto fechado")
                
        except Exception as e:
            self.logger.warning(f"⚠️  Falha ao lidar com modais (pode ser normal): {e}")
        
        # Verifica se o login foi bem-sucedido
        self._verify_login_success(page)
        
        self.logger.info("✅ Login realizado com sucesso!")
    
    def _verify_login_success(self, page: Page) -> None:
        """Verifica se o login foi bem-sucedido."""
        self.logger.debug("🔍 Verificando sucesso do login")
        
        try:
            # Verifica se ainda está na página de login (indicativo de falha)
            if page.locator("input[name='user.login']").is_visible(timeout=5000):
                self.logger.error("❌ Ainda na página de login - credenciais podem estar incorretas")
                raise Exception("Login falhou - verifique suas credenciais")
            
            # Verifica se chegou ao portal principal
            if page.locator("#menu_form_menu_discente_discente_menu").is_visible(timeout=10000):
                self.logger.debug("✅ Portal principal detectado - login bem-sucedido")
                return
                
        except Exception as e:
            self.logger.warning(f"⚠️  Não foi possível verificar automaticamente o login: {e}")
            # Continua mesmo assim, pois pode ser uma mudança na interface
            return
