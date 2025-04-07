import logging
import os
import json
import time
from typing import Tuple, List, Dict, Any, Optional
from functools import wraps
from playwright.sync_api import sync_playwright, Browser, BrowserContext, Page, Playwright
import config
from utils.logger import log_operation

# Constantes
COOKIES_FILE = "cookies.json"
DEFAULT_ENCODING = "utf-8"
SIGAA_BASE_URL = "https://sigaa.ufcg.edu.br/sigaa"
RETRY_ATTEMPTS = 3
RETRY_DELAY = 2


def with_retry(max_attempts: int = RETRY_ATTEMPTS, delay: int = RETRY_DELAY):
    """
    Decorator para adicionar funcionalidade de retry a uma função.
    
    Args:
        max_attempts: Número máximo de tentativas.
        delay: Tempo de espera entre tentativas em segundos.
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
                            f"Tentativa {attempt} falhou: {str(e)[:100]}...",
                            extra={
                                "details": f"function={func.__name__}, retry_in={delay}s, attempt={attempt}/{max_attempts}"
                            }
                        )
                        time.sleep(delay)
            
            # Se chegou aqui, todas as tentativas falharam
            logging.error(
                f"Todas as {max_attempts} tentativas falharam",
                exc_info=last_exception,
                extra={"details": f"function={func.__name__}"}
            )
            raise last_exception
        return wrapper
    return decorator


def create_browser(playwright: Playwright) -> Tuple[Browser, BrowserContext, Page]:
    """
    Cria e configura uma instância do navegador.

    Args:
        playwright: A instância do Playwright.

    Returns:
        tuple: (browser, context, page) - Os objetos do navegador.
    """
    try:
        browser = playwright.chromium.launch(
            headless=config.HEADLESS_BROWSER,
            # Melhorar estabilidade para CI e containers
            args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage"]
        )
        
        context = browser.new_context(
            viewport={
                "width": config.VIEWPORT_WIDTH,
                "height": config.VIEWPORT_HEIGHT,
            },
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36"
        )
        
        page = context.new_page()
        
        # Configurar timeouts
        page.set_default_timeout(config.TIMEOUT_DEFAULT)
        
        logging.info("Navegador iniciado com sucesso")
        return browser, context, page
        
    except Exception as e:
        logging.error(
            f"Erro ao criar navegador: {e}",
            exc_info=True,
            extra={"details": "function=create_browser"}
        )
        raise


def close_browser(browser: Browser) -> None:
    """
    Fecha o navegador de forma segura.

    Args:
        browser: A instância do navegador a ser fechada.
    """
    try:
        if browser:
            browser.close()
            logging.info("Navegador fechado com sucesso", extra={"details": "action=close_browser"})
    except Exception as e:
        logging.error(
            f"Erro ao fechar navegador: {e}",
            exc_info=True,
            extra={"details": "function=close_browser"}
        )


def save_cookies(context: BrowserContext, filepath: str = COOKIES_FILE) -> None:
    """
    Salva os cookies do navegador em um arquivo.

    Args:
        context: O contexto do navegador.
        filepath: Caminho para salvar os cookies.
    """
    try:
        cookies = context.cookies()
        with open(filepath, "w", encoding=DEFAULT_ENCODING) as f:
            json.dump(cookies, f, ensure_ascii=False, indent=4)
        logging.info("Cookies salvos com sucesso", extra={"details": f"file={filepath}, count={len(cookies)}"})
    except Exception as e:
        logging.error(
            f"Erro ao salvar cookies: {e}",
            exc_info=True,
            extra={"details": f"file={filepath}"}
        )


def load_cookies(context: BrowserContext, filepath: str = COOKIES_FILE) -> bool:
    """
    Carrega os cookies de um arquivo para o contexto do navegador.

    Args:
        context: O contexto do navegador.
        filepath: Caminho para o arquivo de cookies.
        
    Returns:
        bool: True se cookies foram carregados com sucesso, False caso contrário.
    """
    try:
        if not os.path.exists(filepath):
            logging.info("Arquivo de cookies não encontrado", extra={"details": f"file={filepath}"})
            return False
            
        with open(filepath, "r", encoding=DEFAULT_ENCODING) as f:
            cookies = json.load(f)
            
        for cookie in cookies:
            # Garantir que atributos obrigatórios estejam presentes
            if "domain" not in cookie or not cookie["domain"]:
                cookie["domain"] = "sigaa.ufcg.edu.br"
            if "path" not in cookie or not cookie["path"]:
                cookie["path"] = "/"
            if "secure" not in cookie:
                cookie["secure"] = True
                
        context.add_cookies(cookies)
        logging.info(
            "Cookies carregados com sucesso",
            extra={"details": f"file={filepath}, count={len(cookies)}"}
        )
        return True
        
    except Exception as e:
        logging.error(
            f"Erro ao carregar cookies: {e}",
            exc_info=True,
            extra={"details": f"file={filepath}"}
        )
        return False


@with_retry(max_attempts=2)
def are_cookies_valid(page: Page) -> bool:
    """
    Verifica se os cookies carregados ainda são válidos.

    Args:
        page: A página do navegador.

    Returns:
        bool: True se os cookies forem válidos, False caso contrário.
    """
    try:
        logging.info("Verificando validade dos cookies")
        page.goto(SIGAA_BASE_URL, wait_until="domcontentloaded")
        
        # Verificar se estamos na página de login ou na página inicial logada
        if "login" in page.url or page.locator("input[name='user.login']").count() > 0:
            logging.info("Sessão inválida. Cookies expirados ou inválidos.")
            return False
            
        logging.info("Sessão válida. Cookies são válidos.")
        return True
        
    except Exception as e:
        logging.error(
            f"Erro ao verificar validade de cookies: {e}",
            exc_info=True,
            extra={"details": "function=are_cookies_valid"}
        )
        return False


@with_retry()
@log_operation(operation_name="Login no SIGAA")
def perform_login(page: Page, username: str, password: str) -> bool:
    """
    Realiza o login na plataforma SIGAA.

    Args:
        page: A página do navegador.
        username: Nome de usuário do SIGAA.
        password: Senha do SIGAA.

    Returns:
        bool: True se o login foi bem-sucedido, False caso contrário.
    """
    try:
        logging.info("Acessando SIGAA", extra={"context": "STEP"})
        page.goto(SIGAA_BASE_URL, wait_until="domcontentloaded")

        # Se já estamos logados, retornar sucesso
        if not ("login" in page.url or page.locator("input[name='user.login']").count() > 0):
            logging.info("Usuário já está logado")
            return True

        logging.info("Preenchendo credenciais e realizando login", extra={"context": "STEP"})
        page.fill("input[name='user.login']", username)
        page.fill("input[name='user.senha']", password)
        
        # Clicar no botão de login e esperar carregamento
        with page.expect_navigation():
            page.click("input[type='submit']")
        
        # Verificar se login foi bem-sucedido
        if "login" in page.url:
            error_message = page.locator(".erro").text_content() if page.locator(".erro").count() > 0 else "Motivo desconhecido"
            logging.error(
                f"Falha no login: {error_message}",
                extra={"context": "ERROR", "details": "function=perform_login"}
            )
            return False

        logging.info("Login realizado com sucesso", extra={"context": "END"})
        return True

    except Exception as e:
        logging.error(
            f"Erro durante o processo de login: {e}",
            exc_info=True,
            extra={"details": "function=perform_login"}
        )
        return False
