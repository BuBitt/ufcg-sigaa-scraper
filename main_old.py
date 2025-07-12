from playwright.sync_api import sync_playwright, Page, Browser, BrowserContext
import os
import logging
import time
import hashlib
from typing import Optional, Dict, Any, Tuple, List
import config
from functools import wraps

from utils.logger import setup_logging, log_error_and_raise, log_operation
from utils.file_handler import load_env, load_grades, save_grades, compare_grades
from scraper.browser import create_browser, close_browser
from scraper.processor import process_all_courses
from scraper.menu_navigation import navigate_to_grades_via_menu, extract_grades_from_menu_page
from notification.telegram import notify_changes


# Constantes
ENV_FILE = ".env"
USERNAME_ENV = "SIGAA_USERNAME"
PASSWORD_ENV = "SIGAA_PASSWORD"
MAX_RETRIES = 3
RETRY_DELAY = 2


def measure_execution_time(func):
    """
    Decorator para medir o tempo de execução de uma função.
    
    Args:
        func: A função a ser medida.
        
    Returns:
        Uma função wrapper que mede e registra o tempo de execução.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        execution_time = end_time - start_time
        logging.debug(
            f"Tempo de execução de {func.__name__}",
            extra={"details": f"time={execution_time:.2f}s"},
        )
        return result
    return wrapper


def mask_sensitive_data(data: str) -> str:
    """
    Oculta informações sensíveis para registro em logs.
    
    Args:
        data: Dados sensíveis para mascarar.
        
    Returns:
        str: Versão mascarada dos dados.
    """
    if not data or len(data) <= 4:
        return "***"
    
    # Cria um hash dos dados para identificação única, mas não reversível
    hash_id = hashlib.md5(data.encode()).hexdigest()[:6]
    visible_chars = min(3, len(data) // 3)
    
    return f"{data[:visible_chars]}***{hash_id}"


def validate_credentials() -> Tuple[str, str]:
    """
    Valida a presença e formato das credenciais SIGAA nas variáveis de ambiente.
    
    Returns:
        Tuple[str, str]: Username e password validados.
        
    Raises:
        ValueError: Se as credenciais estiverem ausentes ou tiverem formato inválido.
    """
    username = os.getenv(USERNAME_ENV)
    password = os.getenv(PASSWORD_ENV)

    if not username or not password:
        log_error_and_raise(
            "Credenciais SIGAA ausentes no arquivo .env",
            ValueError,
            extra={"details": f"file={ENV_FILE}"},
        )
    
    # Assert para garantir que username e password não são None após a verificação
    assert username is not None and password is not None
    
    # Validação básica de formato (agora sabemos que não são None)
    if len(username) < 3 or len(password) < 6:
        log_error_and_raise(
            "Credenciais SIGAA inválidas: formato incorreto",
            ValueError,
            extra={"details": f"file={ENV_FILE}"},
        )
    
    return username, password


@measure_execution_time
@log_operation(operation_name="Extração de Notas")
def process_grades(page: Page, browser: Browser, username: str, password: str) -> Dict[str, Any]:
    """
    Processa e recupera as notas do SIGAA, com mecanismo de retry.
    Escolhe entre duas rotas baseado na configuração EXTRACTION_METHOD:
    - "menu_ensino": Menu Ensino > Consultar Minhas Notas (mais rápido)
    - "materia_individual": Acessa matéria por matéria (método original)
    
    Args:
        page: Objeto de página do navegador.
        browser: Instância do navegador.
        username: Nome de usuário do SIGAA.
        password: Senha do SIGAA.
        
    Returns:
        Dict[str, Any]: Dicionário contendo todas as notas extraídas.
    """
    masked_username = mask_sensitive_data(username)
    retry_count = 0
    last_error = None
    
    # Verificar método de extração configurado
    extraction_method = config.EXTRACTION_METHOD.lower()
    if extraction_method not in ["menu_ensino", "materia_individual"]:
        logging.warning(
            f"Método de extração inválido '{extraction_method}', usando 'menu_ensino' por padrão",
            extra={"details": f"available_methods=['menu_ensino', 'materia_individual']"}
        )
        extraction_method = "menu_ensino"
    
    logging.info(
        f"Usando método de extração: {extraction_method}",
        extra={"details": f"method={extraction_method}"}
    )
    
    while retry_count < MAX_RETRIES:
        try:
            logging.info(
                "Iniciando extração de notas", 
                extra={"details": f"user={masked_username}, method={extraction_method}, attempt={retry_count+1}/{MAX_RETRIES}"}
            )
            
            if extraction_method == "menu_ensino":
                return process_grades_via_menu(page, username, password)
            else:  # materia_individual
                return process_all_courses(page, browser, username, password)
                
        except Exception as e:
            last_error = e
            retry_count += 1
            if retry_count < MAX_RETRIES:
                logging.warning(
                    f"Tentativa {retry_count} falhou, tentando novamente em {RETRY_DELAY} segundos",
                    extra={"details": f"error={str(e)[:50]}..., method={extraction_method}"},
                )
                time.sleep(RETRY_DELAY)
            else:
                logging.error(
                    f"Falha na extração de notas após {MAX_RETRIES} tentativas: {e}",
                    exc_info=True,
                    extra={"details": f"method={extraction_method}"},
                )
    
    return {}  # Retorna dict vazio após esgotar tentativas


def process_grades_via_menu(page: Page, username: str, password: str) -> Dict[str, Any]:
    """
    Processa notas usando o método do menu Ensino > Consultar Minhas Notas.
    
    Args:
        page: Objeto de página do navegador.
        username: Nome de usuário do SIGAA.
        password: Senha do SIGAA.
        
    Returns:
        Dict[str, Any]: Dicionário contendo todas as notas extraídas.
    """
    from scraper.browser import perform_login
    
    # Realizar login
    if not perform_login(page, username, password):
        logging.error("Não foi possível realizar login via menu, abortando extração")
        return {}
    
    # Navegar para a página de notas via menu
    if not navigate_to_grades_via_menu(page):
        logging.error("Não foi possível navegar para a página de notas via menu")
        return {}
    
    # Extrair notas da página
    grades = extract_grades_from_menu_page(page)
    
    if grades:
        logging.info(
            f"Extração via menu concluída com sucesso",
            extra={"details": f"datasets={len(grades)}"}
        )
    else:
        logging.warning("Nenhuma nota extraída via menu")
    
    return grades


def handle_grade_changes(all_grades: Dict[str, Any]) -> None:
    """
    Handle grade changes by comparing with saved grades and notifying if necessary.
    
    Args:
        all_grades: Dictionary containing all extracted grades.
    """
    try:
        # Compare with previous grades
        saved_grades = load_grades()
        logging.info("Notas carregadas do cache", extra={"details": f"file={config.CACHE_FILENAME}"})

        differences = compare_grades(all_grades, saved_grades)

        # Notify if there are changes
        if differences:
            diff_count = len(differences)
            logging.info(
                f"Encontradas {diff_count} diferenças nas notas",
                extra={"details": f"count={diff_count}"}
            )
            notify_changes(differences)
        else:
            logging.info("Nenhuma diferença encontrada nas notas", extra={"details": "status=unchanged"})

        # Save new grades
        save_grades(all_grades)
        # Não precisamos de outro log aqui, pois save_grades já registra um log
    except Exception as e:
        logging.error(
            f"Erro ao processar alterações nas notas: {e}",
            exc_info=True,
            extra={"details": "module=handle_grade_changes"},
        )


def run_scraper(playwright) -> None:
    """
    Run the SIGAA grade scraper process.
    
    Args:
        playwright: Playwright instance.
    """
    browser: Optional[Browser] = None
    
    try:
        # Initialize browser and extract grades
        browser, context, page = create_browser(playwright)
        username, password = validate_credentials()
        
        all_grades = process_grades(page, browser, username, password)
        
        if all_grades:
            handle_grade_changes(all_grades)
        else:
            logging.warning(
                "Nenhuma nota extraída para processamento",
                extra={"details": "status=empty_grades"},
            )

    except Exception as e:
        logging.error(
            f"Erro durante a execução do scraper: {e}",
            exc_info=True,
            extra={"details": "process=run_scraper"},
        )
    finally:
        if browser:
            close_browser(browser)
            # Não precisamos do segundo log aqui


def main():
    """
    Main entry point for the SIGAA grade scraper application.
    """
    # Setup logging
    setup_logging()
    logging.info("Configuração de logging concluída", extra={"details": "action=setup_logging"})

    # Load environment variables and validate credentials
    try:
        load_env()
        logging.info(".env carregado com sucesso", extra={"details": "file=.env"})
    except FileNotFoundError:
        logging.critical("Arquivo .env não encontrado", extra={"details": "file=.env"})
        return
    except Exception as e:
        logging.critical(
            f"Erro ao carregar .env: {e}",
            exc_info=True,
            extra={"details": "file=.env"},
        )
        return

    try:
        with sync_playwright() as playwright:
            logging.info("Playwright iniciado", extra={"details": "action=sync_playwright"})
            run_scraper(playwright)
    except Exception as e:
        logging.critical(
            f"Erro ao inicializar Playwright: {e}",
            exc_info=True,
            extra={"details": "module=sync_playwright"},
        )


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logging.critical(
            f"Erro fatal: {e}",
            exc_info=True,
            extra={"details": "process=main"},
        )
