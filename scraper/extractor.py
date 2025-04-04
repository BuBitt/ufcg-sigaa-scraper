import logging
from bs4 import BeautifulSoup
import config


def extract_table_to_json(html_content):
    """
    Extrai uma tabela de notas do conteúdo HTML e a converte para JSON.

    Args:
        html_content (str): O conteúdo HTML com a tabela de notas.

    Returns:
        list: Uma lista de dicionários com os dados da tabela, ou None se a extração falhar.
    """
    try:
        soup = BeautifulSoup(html_content, "html.parser")
        table = soup.find("table", class_="tabelaRelatorio")
        if not table:
            logging.error("Tabela de notas não encontrada.")
            return None

        # Extract headers
        headers = []
        main_headers = []
        for tr in table.find("thead").find_all("tr"):
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
                    if main_headers[i].startswith("Unid.") and row_headers[i]
                    else main_headers[i]
                    for i in range(len(main_headers))
                ]

        # If no subdivisions, use the main headers
        if not headers:
            headers = main_headers

        # Extract rows
        rows = []
        excluded_keys = {
            "Reposição",
            "Resultado",
            "Faltas",
            "Sit.",
            "Nome",
            "Matrícula",
        }
        for tr in table.find("tbody").find_all("tr"):
            row_data = {}
            for idx, td in enumerate(tr.find_all("td")):
                if idx < len(headers) and headers[idx] not in excluded_keys:
                    row_data[headers[idx]] = td.get_text(strip=True)
            rows.append(row_data)

        return rows

    except Exception as e:
        logging.error(f"Erro ao processar a tabela: {e}")
        return None


def extract_and_save_grades(page, all_grades):
    """
    Extrai as notas da página atual e as salva no dicionário fornecido.

    Args:
        page: A página do navegador.
        all_grades (dict): Dicionário para armazenar as notas extraídas.
    """
    try:
        logging.info("Extraindo tabela de notas")
        page.wait_for_selector(
            "table.tabelaRelatorio, :has-text('Ainda não foram lançadas notas.')",
            timeout=config.TIMEOUT_DEFAULT,
        )

        # Check if the message "Ainda não foram lançadas notas." is present
        if page.locator(":has-text('Ainda não foram lançadas notas.')").count() > 0:
            component_name = page.locator("h3").text_content().strip()
            logging.info(f"Nenhuma nota lançada para o componente {component_name}")
            all_grades[component_name] = "Ainda não foram lançadas notas."
            return

        # Extract the component name
        component_name = page.locator("h3").text_content().strip()

        # Get the HTML content of the page
        html_content = page.content()

        # Extract the table into JSON
        grades = extract_table_to_json(html_content)
        if grades is None:
            logging.error(
                f"Erro ao processar a tabela para o componente {component_name}"
            )
            return

        # Add grades to the unified JSON object
        all_grades[component_name] = grades
        logging.info(f"Notas extraídas para o componente {component_name}")

    except Exception as e:
        logging.error(f"Erro ao extrair notas: {e}")
        raise
