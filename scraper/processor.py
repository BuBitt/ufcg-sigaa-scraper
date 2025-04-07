import logging
import time
from typing import List, Dict, Any, Set, Optional
import config
from functools import wraps

from scraper.browser import perform_login, with_retry
from scraper.extractor import extract_and_save_grades
from utils.logger import log_operation

# Seletores CSS que podem mudar entre versões do SIGAA
SELECTORS = {
    "COMPONENTES": "tbody tr td.descricao a",
    "MENU_ALUNOS": "div.itemMenuHeaderAlunos",
    "VER_NOTAS": "div.itemMenuHeaderAlunos + div a:has-text('Ver Notas')",
    "VER_NOTAS_ALT1": "a:has-text('Ver Notas')",
    "VER_NOTAS_ALT2": "a[onclick*='verNotas']",
    "TROCAR_TURMA": "button#formAcoesTurma\\:botaoTrocarTurma",
    "TURMAS": "div#j_id_jsp_1879301362_4 a.linkTurma",
    "PORTAL_DISCENTE": "a:has-text('Portal Discente')"
}


def measure_processing_time(func):
    """
    Mede e registra o tempo de processamento de uma função.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        execution_time = time.time() - start_time
        logging.debug(
            f"Processamento concluído em {execution_time:.2f} segundos",
            extra={"details": f"function={func.__name__}, time={execution_time:.2f}s"}
        )
        return result
    return wrapper


@with_retry(max_attempts=2)
def get_all_turmas(page) -> List[str]:
    """
    Recupera todas as turmas disponíveis no menu "Trocar de Turma".

    Args:
        page: A página do navegador.

    Returns:
        list: Uma lista com os nomes das turmas.
    """
    try:
        logging.info("Identificando turmas disponíveis")
        
        # Verificar se o seletor existe na página
        if page.locator(SELECTORS["TURMAS"]).count() == 0:
            # Tentar seletor alternativo
            alt_selector = "a.linkTurma"
            if page.locator(alt_selector).count() > 0:
                SELECTORS["TURMAS"] = alt_selector
                logging.info("Usando seletor alternativo para turmas")
        
        # Esperar seletor
        page.wait_for_selector(SELECTORS["TURMAS"], timeout=config.TIMEOUT_DEFAULT)
        
        # Obter turmas
        turmas = page.locator(SELECTORS["TURMAS"])
        count = turmas.count()
        
        if count == 0:
            logging.info("Nenhuma turma encontrada")
            return []
        
        # Extrair nomes das turmas
        turma_names = []
        for i in range(count):
            # Tentar obter o nome da turma pelo span (padrão) ou pelo próprio elemento
            nome_element = turmas.nth(i).locator("span")
            if nome_element.count() > 0:
                turma_names.append(nome_element.text_content().strip())
            else:
                turma_names.append(turmas.nth(i).text_content().strip())
                
        logging.info(
            f"Turmas identificadas: {len(turma_names)}",
            extra={"details": f"count={len(turma_names)}"}
        )
        return turma_names
        
    except Exception as e:
        logging.error(
            f"Erro ao identificar turmas: {e}",
            exc_info=True,
            extra={"details": "function=get_all_turmas"}
        )
        return []


@with_retry(max_attempts=2)
def handle_class_switch(
    page, 
    processed_classes: Set[str], 
    all_grades: Dict[str, Any], 
    turma_names: List[str]
) -> bool:
    """
    Lida com a troca entre turmas e processa suas notas.

    Args:
        page: A página do navegador.
        processed_classes: Conjunto de turmas já processadas.
        all_grades: Dicionário para armazenar as notas extraídas.
        turma_names: Lista com os nomes de todas as turmas.
        
    Returns:
        bool: True se o processamento foi bem-sucedido, False caso contrário.
    """
    try:
        if not turma_names:
            logging.info("Nenhuma turma para processar")
            return True
            
        for turma_name in turma_names:
            if turma_name not in processed_classes:
                logging.info(f"Acessando turma", extra={"details": f"turma={turma_name}"})
                processed_classes.add(turma_name)

                # Clicar na turma
                turma_seletor = f"span:has-text('{turma_name}')"
                if page.locator(turma_seletor).count() == 0:
                    # Escape special characters in turma name for selector
                    escaped_name = turma_name.replace("'", "\\'").replace('"', '\\"')
                    turma_seletor = f"a:has-text('{escaped_name}')"
                
                page.locator(turma_seletor).click()

                # Clicar em Ver Notas
                logging.info("Acessando página de notas")
                page.wait_for_selector(SELECTORS["VER_NOTAS"], timeout=config.TIMEOUT_DEFAULT)
                page.locator(SELECTORS["VER_NOTAS"]).click()

                # Extrair notas
                extract_and_save_grades(page, all_grades)

                # Voltar para a lista de turmas
                logging.info("Retornando para lista de turmas")
                page.go_back()
                page.wait_for_selector(SELECTORS["TROCAR_TURMA"], timeout=config.TIMEOUT_DEFAULT)
                page.locator(SELECTORS["TROCAR_TURMA"]).click()
                
                # Breve espera para garantir carregamento
                time.sleep(1)

        logging.info(
            "Processamento de turmas concluído",
            extra={"details": f"processed={len(processed_classes)}"}
        )
        return True

    except Exception as e:
        logging.error(
            f"Erro ao processar turmas: {e}",
            exc_info=True,
            extra={"details": f"function=handle_class_switch, processed_count={len(processed_classes)}"}
        )
        return False


@with_retry(max_attempts=2)
def click_with_fallback(page, selectors: List[str], timeout: int = None) -> bool:
    """
    Tenta clicar em um elemento usando vários seletores como fallback.
    
    Args:
        page: A página do navegador.
        selectors: Lista de seletores CSS para tentar na ordem.
        timeout: Timeout em ms para espera (usa o padrão se None).
        
    Returns:
        bool: True se o clique foi bem-sucedido, False caso contrário.
    """
    if timeout is None:
        timeout = config.TIMEOUT_DEFAULT // 2  # Usar metade do timeout padrão para cada tentativa
        
    for i, selector in enumerate(selectors):
        try:
            # Verificar se o elemento existe e está visível
            if page.locator(selector).count() > 0:
                logging.info(f"Encontrado elemento para clique", 
                            extra={"details": f"selector={selector}, attempt={i+1}/{len(selectors)}"})
                
                # Esperar o seletor estar visível com timeout reduzido
                page.wait_for_selector(selector, timeout=timeout, state="visible")
                page.locator(selector).click()
                time.sleep(0.5)  # Pequena pausa para garantir que o clique seja processado
                return True
        except Exception as e:
            logging.warning(
                f"Falha ao clicar usando seletor {i+1}/{len(selectors)}",
                extra={"details": f"selector={selector}, error={str(e)[:100]}"}
            )
    
    logging.error(
        f"Não foi possível clicar em nenhum dos {len(selectors)} seletores",
        extra={"details": f"selectors={', '.join(selectors[:2])}..."}
    )
    return False


def navigate_back_to_main_page(page) -> bool:
    """
    Tenta navegar de volta para a página principal do SIGAA.
    
    Args:
        page: A página do navegador.
        
    Returns:
        bool: True se a navegação foi bem-sucedida, False caso contrário.
    """
    try:
        # Verificar se já estamos na página principal
        if page.url.endswith("/sigaa/portais/discente/discente.jsf"):
            return True
            
        # Tentar clicar no link para o Portal Discente
        if click_with_fallback(page, [SELECTORS["PORTAL_DISCENTE"]]):
            logging.info("Navegado de volta para o Portal Discente")
            return True
            
        # Se não funcionar, tente navegar diretamente para a URL
        page.goto("https://sigaa.ufcg.edu.br/sigaa/portais/discente/discente.jsf", 
                  timeout=config.TIMEOUT_DEFAULT)
        logging.info("Navegado diretamente para o Portal Discente via URL")
        return True
    except Exception as e:
        logging.error(
            f"Falha ao navegar de volta para a página principal: {e}",
            extra={"details": f"current_url={page.url}"}
        )
        return False


@measure_processing_time
@log_operation(operation_name="Processamento de Componentes")
def process_all_courses(page, browser, username: str, password: str) -> Dict[str, Any]:
    """
    Processa todos os cursos e extrai suas notas.

    Args:
        page: A página do navegador.
        browser: A instância do navegador.
        username: Nome de usuário do SIGAA.
        password: Senha do SIGAA.

    Returns:
        dict: Dicionário contendo todas as notas extraídas.
    """
    all_grades = {}
    processed_classes = set()
    start_time = time.time()

    try:
        # Realizar login
        if not perform_login(page, username, password):
            logging.error("Não foi possível realizar login, abortando extração")
            return all_grades

        # Encontrar todos os componentes curriculares
        logging.info("Identificando componentes curriculares")
        page.wait_for_selector(SELECTORS["COMPONENTES"], timeout=config.TIMEOUT_DEFAULT)
        component_links = page.locator(SELECTORS["COMPONENTES"]).all()
        
        component_count = len(component_links)
        logging.info(
            f"Componentes curriculares encontrados: {component_count}",
            extra={"details": f"count={component_count}"}
        )

        # Processar apenas o primeiro componente
        if component_count > 0:
            component_start = time.time()
            logging.info(
                f"Processando primeiro componente curricular",
                extra={"details": f"total_disponivel={component_count}"}
            )
            
            # Clicar no primeiro componente curricular
            page.locator(SELECTORS["COMPONENTES"]).first.click()
            time.sleep(1)  # Pequeno delay para garantir carregamento da página

            # Verificar se o menu "Alunos" está presente
            alunos_menu_present = page.locator(SELECTORS["MENU_ALUNOS"]).count() > 0
            
            if not alunos_menu_present:
                logging.warning(
                    "Menu 'Alunos' não encontrado, verificando página atual",
                    extra={"details": f"url={page.url}"}
                )
                # Se estivermos em uma página não esperada, tentar voltar à principal
                navigate_back_to_main_page(page)
                return all_grades
                
            # Expandir o menu "Alunos"
            try:
                logging.info("Expandindo o menu 'Alunos'")
                page.wait_for_selector(
                    SELECTORS["MENU_ALUNOS"],
                    timeout=config.TIMEOUT_DEFAULT // 2,
                    state="visible"
                )
                page.locator(SELECTORS["MENU_ALUNOS"]).first.click()
                time.sleep(1)  # Aumentado para garantir que o menu expanda
            except Exception as e:
                logging.error(
                    f"Erro ao expandir o menu 'Alunos': {e}",
                    extra={"details": f"component_index=1"}
                )
                # Continua tentando clicar em Ver Notas mesmo assim

            # Clicar em "Ver Notas" com fallback para seletores alternativos
            try:
                logging.info("Clicando em 'Ver Notas'")
                ver_notas_clicked = click_with_fallback(
                    page, 
                    [
                        SELECTORS["VER_NOTAS"],
                        SELECTORS["VER_NOTAS_ALT1"],
                        SELECTORS["VER_NOTAS_ALT2"]
                    ],
                    config.TIMEOUT_DEFAULT // 2
                )
                
                if not ver_notas_clicked:
                    logging.error("Não foi possível clicar em 'Ver Notas' após múltiplas tentativas")
                    return all_grades
                    
                time.sleep(1)  # Espera para carregamento da página
                
            except Exception as e:
                logging.error(
                    f"Erro ao clicar em 'Ver Notas': {e}",
                    extra={"details": f"component_index=1"}
                )
                return all_grades

            # Extrair notas do componente principal com tratamento de erro
            try:
                extract_and_save_grades(page, all_grades)
            except Exception as e:
                logging.error(
                    f"Erro ao extrair notas do componente principal: {e}",
                    extra={"details": f"component_index=1"}
                )
                # Verificamos se conseguimos capturar o título do componente para registrar uma entrada vazia
                try:
                    if page.locator("h3").count() > 0:
                        component_name = page.locator("h3").text_content().strip()
                        all_grades[component_name] = "Erro ao extrair notas"
                        logging.info(f"Registrado erro para o componente {component_name}")
                except Exception:
                    pass

            # Verificar turmas disponíveis (se conseguiu acessar a página de notas)
            try:
                logging.info("Identificando todas as turmas disponíveis")
                # Tentar voltar para a página anterior
                page.go_back()
                time.sleep(1)  # Espera para carregamento
                
                # Verificar se o botão de trocar turma está presente
                if page.locator(SELECTORS["TROCAR_TURMA"]).count() > 0:
                    page.locator(SELECTORS["TROCAR_TURMA"]).click()
                    time.sleep(1)  # Espera para carregamento
                    
                    turma_names = get_all_turmas(page)

                    # Processar todas as turmas deste componente
                    if turma_names:
                        handle_class_switch(page, processed_classes, all_grades, turma_names)
                        logging.info("Todas as turmas foram processadas")
                    else:
                        logging.info("Nenhuma turma adicional encontrada")
                else:
                    logging.warning("Botão 'Trocar Turma' não encontrado")
            except Exception as e:
                logging.warning(
                    f"Erro ao processar turmas adicionais: {e}",
                    extra={"details": "component_index=1"}
                )
                
            component_time = time.time() - component_start
            # Atualizar a mensagem para refletir que processamos todas as turmas
            if len(processed_classes) > 0:
                logging.info(
                    f"Componente e todas as turmas processados",
                    extra={
                        "details": f"turmas={len(processed_classes)}, time={component_time:.2f}s"
                    }
                )
            else:
                logging.info(
                    f"Componente processado",
                    extra={
                        "details": f"time={component_time:.2f}s"
                    }
                )
        else:
            logging.warning("Nenhum componente curricular encontrado")

        total_time = time.time() - start_time
        logging.info(
            f"Processamento de componentes concluído",
            extra={
                "details": f"components={len(all_grades)}, time={total_time:.2f}s"
            }
        )
        return all_grades

    except Exception as e:
        logging.error(
            f"Erro ao processar componentes curriculares: {e}",
            exc_info=True,
            extra={"details": "function=process_all_courses"}
        )
        # Não precisamos mais tentar navegar de volta para a página principal
        # já que vamos fechar o navegador logo em seguida

    # Este bloco será executado apenas em caso de exceção
    total_time = time.time() - start_time
    return all_grades
