import logging
import os
import json
import config


def create_browser(playwright):
    """
    Cria e configura uma instância do navegador.

    Args:
        playwright: A instância do Playwright.

    Returns:
        tuple: (browser, context, page) - Os objetos do navegador.
    """
    browser = playwright.chromium.launch(headless=config.HEADLESS_BROWSER)
    context = browser.new_context(
        viewport={
            "width": config.VIEWPORT_WIDTH,
            "height": config.VIEWPORT_HEIGHT,
        }
    )
    page = context.new_page()
    return browser, context, page


def close_browser(browser):
    """
    Fecha o navegador de forma segura.

    Args:
        browser: A instância do navegador a ser fechada.
    """
    try:
        if browser:
            browser.close()
            logging.info("Navegador fechado com sucesso.")
    except Exception as e:
        logging.error(f"Erro ao fechar o navegador: {e}")


def save_cookies(context, filepath="cookies.json"):
    """
    Salva os cookies do navegador em um arquivo.

    Args:
        context: O contexto do navegador.
        filepath (str): Caminho para salvar os cookies.
    """
    try:
        cookies = context.cookies()
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(cookies, f, ensure_ascii=False, indent=4)
        logging.info("Cookies salvos com sucesso.")
    except Exception as e:
        logging.error(f"Erro ao salvar cookies: {e}")


def load_cookies(context, filepath="cookies.json"):
    """
    Carrega os cookies de um arquivo para o contexto do navegador.

    Args:
        context: O contexto do navegador.
        filepath (str): Caminho para o arquivo de cookies.
    """
    try:
        if os.path.exists(filepath):
            with open(filepath, "r", encoding="utf-8") as f:
                cookies = json.load(f)
            for cookie in cookies:
                # Ensure the domain, path, and secure attributes are set correctly
                if "domain" not in cookie or not cookie["domain"]:
                    cookie["domain"] = "sigaa.ufcg.edu.br"
                if "path" not in cookie or not cookie["path"]:
                    cookie["path"] = "/"
                if "secure" not in cookie:
                    cookie["secure"] = True
            context.add_cookies(cookies)
            logging.info("Cookies carregados com sucesso.")
        else:
            logging.info("Arquivo de cookies não encontrado.")
    except Exception as e:
        logging.error(f"Erro ao carregar cookies: {e}")


def are_cookies_valid(page):
    """
    Verifica se os cookies carregados ainda são válidos.

    Args:
        page: A página do navegador.

    Returns:
        bool: True se os cookies forem válidos, False caso contrário.
    """
    try:
        logging.info("Verificando validade dos cookies.")
        page.goto("https://sigaa.ufcg.edu.br/sigaa", wait_until="domcontentloaded")
        if "login" in page.url or page.locator("input[name='user.login']").count() > 0:
            logging.info("Sessão inválida. Cookies não são válidos.")
            return False
        logging.info("Sessão válida. Cookies são válidos.")
        return True
    except Exception as e:
        logging.error(f"Erro ao verificar validade dos cookies: {e}")
        return False


def perform_login(page, username, password):
    """
    Realiza o login na plataforma SIGAA.

    Args:
        page: A página do navegador.
        username (str): Nome de usuário do SIGAA.
        password (str): Senha do SIGAA.

    Returns:
        bool: True se o login foi bem-sucedido, False caso contrário.
    """
    try:
        logging.info("Acessando SIGAA")
        page.goto("https://sigaa.ufcg.edu.br/sigaa", wait_until="domcontentloaded")

        logging.info("Realizando login.")
        page.fill("input[name='user.login']", username)
        page.fill("input[name='user.senha']", password)
        page.click("input[type='submit']", timeout=config.TIMEOUT_DEFAULT)
        page.wait_for_load_state("domcontentloaded")

        if "login" in page.url:
            logging.error("Falha no login. Verifique suas credenciais.")
            return False

        logging.info("Login realizado com sucesso.")
        return True

    except Exception as e:
        logging.error(f"Erro durante o login: {e}")
        return False
