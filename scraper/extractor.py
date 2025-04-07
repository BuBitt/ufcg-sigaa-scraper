import logging
import time
from bs4 import BeautifulSoup
from typing import Dict, Any, List, Optional, Union
import config
from functools import wraps
from playwright.sync_api import Page

from utils.logger import log_operation, format_component_name


def measure_processing_time(func):
    """
    Decorator para medir tempo de processamento de funções.
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


@measure_processing_time
def extract_table_to_json(html_content: str) -> Optional[List[Dict[str, str]]]:
    """
    Extrai uma tabela de notas do conteúdo HTML e a converte para JSON.

    Args:
        html_content: O conteúdo HTML com a tabela de notas.

    Returns:
        list: Uma lista de dicionários com os dados da tabela, ou None se a extração falhar.
    """
    try:
        soup = BeautifulSoup(html_content, "html.parser")
        table = soup.find("table", class_="tabelaRelatorio")
        
        if not table:
            logging.error(
                "Tabela de notas não encontrada no HTML",
                extra={"details": "element=table.tabelaRelatorio"}
            )
            return None

        # Verificar se a tabela tem cabeçalho e corpo
        thead = table.find("thead")
        tbody = table.find("tbody")
        
        if not thead or not tbody:
            logging.error(
                "Estrutura da tabela incompleta",
                extra={"details": f"thead_found={bool(thead)}, tbody_found={bool(tbody)}"}
            )
            return None

        # Extract headers
        headers = []
        main_headers = []
        
        for tr in thead.find_all("tr"):
            row_headers = []
            for th in tr.find_all("th"):
                header_text = th.get_text(strip=True)
                colspan = int(th.get("colspan", 1))
                if colspan > 1:
                    # Expand subdivided headers
                    row_headers.extend([header_text] * colspan)
                else:
                    row_headers.append(header_text)

            if not main_headers:
                main_headers = row_headers
            else:
                # Combine main headers with subdivisions
                headers = [
                    f"{main_headers[i]} {row_headers[i]}".strip()
                    if i < len(main_headers) and i < len(row_headers) and main_headers[i].startswith("Unid.") and row_headers[i]
                    else (main_headers[i] if i < len(main_headers) else "")
                    for i in range(max(len(main_headers), len(row_headers)))
                ]

        # If no subdivisions, use the main headers
        if not headers:
            headers = main_headers

        # Extract rows
        rows = []
        excluded_keys = {
            "Reposição", "Resultado", "Faltas", "Sit.", "Nome", "Matrícula",
        }
        
        for tr in tbody.find_all("tr"):
            row_data = {}
            cells = tr.find_all("td")
            
            for idx, td in enumerate(cells):
                if idx < len(headers) and headers[idx] not in excluded_keys and headers[idx]:
                    row_data[headers[idx]] = td.get_text(strip=True)
                    
            if row_data:  # Adicionar apenas se tiver dados
                rows.append(row_data)

        logging.info(
            f"Extração de tabela bem-sucedida",
            extra={"details": f"rows={len(rows)}, columns={len(headers)}"}
        )
        return rows

    except Exception as e:
        logging.error(
            f"Erro ao processar tabela HTML: {e}",
            exc_info=True,
            extra={"details": "function=extract_table_to_json"}
        )
        return None


@log_operation(operation_name="Extração de Tabela")
def extract_and_save_grades(page: Page, all_grades: Dict[str, Any]) -> None:
    """
    Extrai as notas da página atual e as salva no dicionário fornecido.

    Args:
        page: A página do navegador.
        all_grades: Dicionário para armazenar as notas extraídas.
    """
    try:
        logging.info("Extraindo tabela de notas", extra={"context": "STEP"})
        
        # Esperar por um dos possíveis estados: tabela ou mensagem de "sem notas"
        page.wait_for_selector(
            "table.tabelaRelatorio, :has-text('Ainda não foram lançadas notas.')",
            timeout=config.TIMEOUT_DEFAULT,
        )

        # Extrair nome do componente curricular
        component_name = ""
        if page.locator("h3").count() > 0:
            component_name = page.locator("h3").text_content().strip()
        else:
            logging.warning("Nome do componente não encontrado")
            component_name = "Componente Desconhecido"

        # Verificar se há a mensagem "Ainda não foram lançadas notas"
        if page.locator(":has-text('Ainda não foram lançadas notas.')").count() > 0:
            formatted_name = format_component_name(component_name)
            
            logging.info(
                f"Nenhuma nota lançada",
                extra={"context": "STEP", "details": f"disciplina={formatted_name}"}
            )
            all_grades[component_name] = "Ainda não foram lançadas notas."
            return

        # Obter o HTML e extrair a tabela
        html_content = page.content()
        grades = extract_table_to_json(html_content)
        
        if grades is None or len(grades) == 0:
            logging.error(
                f"Erro ao processar tabela de notas",
                extra={"details": f"component={component_name}"}
            )
            return

        # Adicionar ao dicionário de notas
        all_grades[component_name] = grades
        
        # Formatar o nome para o log
        formatted_name = format_component_name(component_name)
        
        # Contar notas não vazias
        non_empty_grades = 0
        if isinstance(grades, list) and len(grades) > 0:
            for grade_item in grades[0].values():
                if grade_item and grade_item.strip():
                    non_empty_grades += 1
        
        logging.info(
            f"Notas extraídas com sucesso",
            extra={"context": "END", "details": f"disciplina={formatted_name}, notas={non_empty_grades}"}
        )

    except Exception as e:
        logging.error(
            f"Erro ao extrair notas: {e}",
            exc_info=True,
            extra={"details": "function=extract_and_save_grades"}
        )
        raise
