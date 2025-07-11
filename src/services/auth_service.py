"""
Serviço de autenticação no SIGAA.
"""

import logging
import os
from playwright.sync_api import Page

from src.config.settings import Config
from src.utils.env_loader import load_environment


class AuthService:
    """Gerencia a autenticação no sistema SIGAA."""
    
    def __init__(self) -> None:
        """Inicializa o serviço de autenticação."""
        load_environment()
        self.username = os.getenv("SIGAA_USERNAME")
        self.password = os.getenv("SIGAA_PASSWORD")
        
        if not self.username or not self.password:
            raise ValueError("SIGAA_USERNAME e SIGAA_PASSWORD devem estar definidos no .env")
    
    def login(self, page: Page) -> None:
        """
        Realiza login no SIGAA.
        
        Args:
            page: Objeto page do Playwright
            
        Raises:
            Exception: Se o login falhar
        """
        logging.info("Acessando SIGAA")
        page.goto(Config.SIGAA_URL, wait_until="domcontentloaded")

        logging.info("Realizando login")
        page.fill("input[name='user.login']", self.username or "")
        page.fill("input[name='user.senha']", self.password or "")
        page.click("input[type='submit']", timeout=Config.TIMEOUT_DEFAULT)

        logging.info("Lidando com diálogos modais")
        try:
            page.locator("button.btn-primary:has-text('Ciente')").click(
                timeout=5000, force=True
            )
            page.locator("#yuievtautoid-0").click(timeout=5000, force=True)
        except Exception as e:
            logging.warning(f"Falha ao lidar com modal (pode não estar presente): {e}")
        
        logging.info("Login realizado com sucesso")
