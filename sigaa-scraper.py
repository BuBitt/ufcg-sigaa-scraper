from playwright.sync_api import Playwright, sync_playwright
import logging
import os
import config
import json
from bs4 import BeautifulSoup
from telegram_notifier import notify_changes  # Import the notifier

# Configuração mínima do logging
logging.basicConfig(
    level=config.LOG_DEPTH,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(config.LOG_FILENAME, mode="w"),
        logging.StreamHandler(),
    ],
)


# Carrega variáveis de ambiente
def load_env():
    try:
        with open(".env", "r") as f:
            for line in f:
                if line.strip() and not line.startswith("#"):
                    key, value = line.strip().split("=", 1)
                    os.environ[key] = value
        logging.info(".env carregado com sucesso")
    except FileNotFoundError:
        logging.error(".env não encontrado")
        raise
    except Exception as e:
        logging.error(f"Erro ao carregar .env: {e}")
        raise


def extract_table_to_json(html_content):
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
        for tr in table.find("tbody").find_all("tr"):
            row_data = {}
            for idx, td in enumerate(tr.find_all("td")):
                if idx < len(headers):
                    row_data[headers[idx]] = td.get_text(strip=True)
            rows.append(row_data)

        return rows

    except Exception as e:
        logging.error(f"Erro ao processar a tabela: {e}")
        return None


def extract_and_save_grades(page, all_grades):
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


def handle_trocar_turma_and_process(page, processed_turmas, all_grades, browser):
    try:
        logging.info("Voltando para a página da turma")
        page.go_back()

        logging.info("Clicando no botão 'Trocar de Turma'")
        page.wait_for_selector(
            "button#formAcoesTurma\\:botaoTrocarTurma",
            timeout=config.TIMEOUT_DEFAULT,
        )
        page.locator("button#formAcoesTurma\\:botaoTrocarTurma").click()

        logging.info("Selecionando a próxima turma não processada")
        turmas = page.locator("div#j_id_jsp_1879301362_4 a.linkTurma")
        for i in range(1, turmas.count()):
            turma = turmas.nth(i)
            turma_name = turma.locator("span").text_content().strip()
            if turma_name not in processed_turmas:
                processed_turmas.add(turma_name)
                turma.click()
                logging.info(f"Acessando turma: {turma_name}")

                logging.info("Clicando em 'Ver Notas'")
                page.wait_for_selector(
                    "div.itemMenuHeaderAlunos + div a:has-text('Ver Notas')",
                    timeout=config.TIMEOUT_DEFAULT,
                )
                page.locator(
                    "div.itemMenuHeaderAlunos + div a:has-text('Ver Notas')"
                ).click()

                logging.info("Extraindo e salvando notas")
                extract_and_save_grades(page, all_grades)

                logging.info("Voltando para a lista de turmas")
                page.go_back()
                page.wait_for_selector(
                    "button#formAcoesTurma\\:botaoTrocarTurma",
                    timeout=config.TIMEOUT_DEFAULT,
                )
                page.locator("button#formAcoesTurma\\:botaoTrocarTurma").click()

        logging.info("Todas as turmas já foram processadas.")
        browser.close()
        logging.info("Navegador fechado após processar todas as turmas.")
        exit(0)

    except Exception as e:
        logging.error(f"Erro ao trocar de turma e processar: {e}")
        raise


def compare_grades(new_grades, saved_grades):
    try:
        differences = {}
        for component, new_data in new_grades.items():
            if component not in saved_grades:
                differences[component] = {"status": "Novo componente", "data": new_data}
                continue

            saved_data = saved_grades[component]
            if isinstance(new_data, list) and isinstance(saved_data, list):
                for new_row, saved_row in zip(new_data, saved_data):
                    diff = {
                        key: {
                            "old": saved_row.get(key, ""),
                            "new": new_row.get(key, ""),
                        }
                        for key in new_row
                        if new_row.get(key, "") != saved_row.get(key, "")
                    }
                    if diff:
                        if component not in differences:
                            differences[component] = []
                        differences[component].append(diff)
            elif new_data != saved_data:
                differences[component] = {
                    "status": "Alterado",
                    "old": saved_data,
                    "new": new_data,
                }

        for component in saved_grades:
            if component not in new_grades:
                differences[component] = {"status": "Removido"}

        if differences:
            logging.info("Diferenças encontradas:")
            print(json.dumps(differences, ensure_ascii=False, indent=4))
            notify_changes(differences)  # Notify changes via Telegram
        else:
            logging.info("Nenhuma diferença encontrada nas notas.")

    except Exception as e:
        logging.error(f"Erro ao comparar notas: {e}")


def run(playwright: Playwright):
    browser = playwright.chromium.launch(headless=config.HEADLESS_BROWSER)
    context = browser.new_context(
        viewport={
            "width": config.VIEWPORT_WIDTH,
            "height": config.VIEWPORT_HEIGHT,
        }
    )
    page = context.new_page()

    all_grades = {}

    try:
        logging.info("Acessando SIGAA")
        page.goto("https://sigaa.ufcg.edu.br/sigaa", wait_until="domcontentloaded")

        logging.info("Fazendo login")
        page.fill("input[name='user.login']", username)
        page.fill("input[name='user.senha']", password)
        page.click("input[type='submit']", timeout=config.TIMEOUT_DEFAULT)
        page.wait_for_load_state("domcontentloaded")
        if "login" in page.url:
            logging.error("Falha no login. Verifique suas credenciais.")
            raise ValueError("Falha no login.")
        logging.info("Login realizado com sucesso.")

        logging.info("Identificando todos os links de Componentes Curriculares")
        page.wait_for_selector(
            "tbody tr td.descricao a", timeout=config.TIMEOUT_DEFAULT
        )
        component_links = page.locator("tbody tr td.descricao a").all()

        logging.info(f"Encontrados {len(component_links)} componentes curriculares")

        processed_turmas = set()

        for i in range(len(component_links)):
            logging.info(f"Acessando componente curricular {i + 1}")
            page.locator("tbody tr td.descricao a").nth(i).click()

            logging.info("Expandindo o menu 'Alunos'")
            alunos_menu = page.locator("div.itemMenuHeaderAlunos").first
            alunos_menu.click()

            logging.info("Clicando em 'Ver Notas'")
            page.wait_for_selector(
                "div.itemMenuHeaderAlunos + div a:has-text('Ver Notas')",
                timeout=config.TIMEOUT_DEFAULT,
            )
            page.locator(
                "div.itemMenuHeaderAlunos + div a:has-text('Ver Notas')"
            ).click()

            logging.info("Extraindo e salvando notas")
            extract_and_save_grades(page, all_grades)

            while True:
                try:
                    logging.info("Trocando para a próxima turma")
                    handle_trocar_turma_and_process(
                        page, processed_turmas, all_grades, browser
                    )
                except Exception:
                    logging.info("Não há mais turmas para trocar.")
                    break

    except Exception as e:
        logging.error(f"Erro: {e}")
        raise
    finally:
        try:
            if os.path.exists("grades_cache.json"):
                with open("grades_cache.json", "r", encoding="utf-8") as f:
                    saved_grades = json.load(f)
                compare_grades(all_grades, saved_grades)
            else:
                logging.info(
                    "Nenhum arquivo grades_cache.json encontrado. Salvando novo arquivo."
                )

            with open("grades_cache.json", "w", encoding="utf-8") as f:
                json.dump(all_grades, f, ensure_ascii=False, indent=4)
            logging.info("Todas as notas foram salvas em grades_cache.json")

        except Exception as e:
            logging.error(f"Erro ao salvar ou comparar grades_cache.json: {e}")

        try:
            browser.close()
        except Exception as e:
            logging.error(f"Erro ao fechar o navegador: {e}")


if __name__ == "__main__":
    load_env()
    username = os.getenv("SIGAA_USERNAME")
    password = os.getenv("SIGAA_PASSWORD")
    if not username or not password:
        logging.error("SIGAA_USERNAME e SIGAA_PASSWORD devem estar no .env")
        raise ValueError("SIGAA_USERNAME e SIGAA_PASSWORD devem estar no .env")

    with sync_playwright() as playwright:
        try:
            run(playwright)
        except Exception as e:
            logging.error(f"Erro final: {e}")
            print(f"Erro: {e}")
