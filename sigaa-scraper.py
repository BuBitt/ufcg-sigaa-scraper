from playwright.sync_api import Playwright, sync_playwright
import logging
import os
import csv
import json
from datetime import datetime
from bs4 import BeautifulSoup
from telegram_notifier import notify_changes
import config  # Importa o arquivo de configuração

# Configuração do logging
logging.basicConfig(
    level=config.LOG_DEPTH,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(config.LOG_FILENAME, mode="w"),
        logging.StreamHandler(),
    ],
)


def load_env_file(file_path=".env"):
    try:
        with open(file_path, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    key, value = line.split("=", 1)
                    os.environ[key] = value.strip()
        logging.info(f"Arquivo .env carregado com sucesso: {file_path}")
    except FileNotFoundError:
        logging.error(f"Arquivo .env não encontrado: {file_path}")
        raise
    except Exception as e:
        logging.error(f"Erro ao carregar o arquivo .env: {str(e)}")
        raise


load_env_file()
username = os.getenv("SIGAA_USERNAME")
password = os.getenv("SIGAA_PASSWORD")

if not username or not password:
    logging.error(
        "As variáveis SIGAA_USERNAME e SIGAA_PASSWORD devem ser definidas no arquivo .env"
    )
    raise ValueError(
        "As variáveis SIGAA_USERNAME e SIGAA_PASSWORD devem ser definidas no arquivo .env"
    )


# Função principal para extrair notas usando BeautifulSoup
def extract_all_grades(html_content):
    grades = []
    soup = BeautifulSoup(html_content, "html.parser")
    tables = soup.find_all("table", class_="tabelaRelatorio")

    logging.info(f"Encontradas {len(tables)} tabelas com class='tabelaRelatorio'")
    for table in tables:
        caption = table.find("caption")
        current_semester = caption.text.strip() if caption else "Semestre Desconhecido"
        logging.info(f"Processando tabela do semestre {current_semester}")
        rows = table.find("tbody").find_all("tr", class_=lambda x: x and "linha" in x)
        logging.info(f"Encontradas {len(rows)} linhas na tabela de {current_semester}")

        for row in rows:
            cols = row.find_all("td")
            if len(cols) >= 2:
                current_row = [col.text.strip() for col in cols]
                while len(current_row) < 15:
                    current_row.append("")
                grade_entry = {
                    "Semestre": current_semester,
                    "Código": current_row[0],
                    "Disciplina": current_row[1],
                    "Unidade 1": current_row[2] if current_row[2] != "--" else "",
                    "Unidade 2": current_row[3] if current_row[3] != "--" else "",
                    "Unidade 3": current_row[4] if current_row[4] != "--" else "",
                    "Unidade 4": current_row[5] if current_row[5] != "--" else "",
                    "Unidade 5": current_row[6] if current_row[6] != "--" else "",
                    "Unidade 6": current_row[7] if current_row[7] != "--" else "",
                    "Unidade 7": current_row[8] if current_row[8] != "--" else "",
                    "Unidade 8": current_row[9] if current_row[9] != "--" else "",
                    "Unidade 9": current_row[10] if current_row[10] != "--" else "",
                    "Recuperação": current_row[11] if current_row[11] != "--" else "",
                    "Resultado": current_row[12] if current_row[12] != "--" else "",
                    "Faltas": current_row[13],
                    "Situação": current_row[14],
                }
                grades.append(grade_entry)
                logging.info(
                    f"Linha capturada: {current_row[1]} (Semestre: {current_semester}) - Colunas: {len(current_row)}"
                )

    if not grades:
        logging.warning("Nenhuma nota encontrada em nenhuma tabela")
    else:
        logging.info(f"{len(grades)} notas extraídas de todas as tabelas")
    return grades


def save_to_csv(grades, filename=config.CSV_FILENAME):
    headers = [
        "Semestre",
        "Código",
        "Disciplina",
        "Unidade 1",
        "Unidade 2",
        "Unidade 3",
        "Unidade 4",
        "Unidade 5",
        "Unidade 6",
        "Unidade 7",
        "Unidade 8",
        "Unidade 9",
        "Recuperação",
        "Resultado",
        "Faltas",
        "Situação",
    ]
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(grades)
    logging.info(f"Notas salvas em {filename}")


def load_cache(filename=config.CACHE_FILENAME):
    try:
        with open(filename, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
    except Exception as e:
        logging.error(f"Erro ao carregar cache: {str(e)}")
        return {}


def save_cache(grades, filename=config.CACHE_FILENAME):
    cache = {}
    for grade in grades:
        semester = grade["Semestre"]
        if semester not in cache:
            cache[semester] = []
        cache[semester].append(grade)
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)
    logging.info(f"Cache salvo em {filename}")


def compare_grades(old_grades, new_grades):
    changes = []
    old_dict = {
        f"{g['Semestre']}-{g['Código']}": g
        for semester, grades in old_grades.items()
        for g in grades
    }
    new_dict = {
        f"{g['Semestre']}-{g['Código']}": g
        for semester, grades in new_grades.items()
        for g in grades
    }

    # Campos de notas a comparar
    grade_fields = [
        "Unidade 1",
        "Unidade 2",
        "Unidade 3",
        "Unidade 4",
        "Unidade 5",
        "Unidade 6",
        "Unidade 7",
        "Unidade 8",
        "Unidade 9",
        "Recuperação",
        "Resultado",
    ]

    # Processa disciplinas novas ou alteradas
    for key, new_grade in new_dict.items():
        if key not in old_dict:
            # Disciplina nova: só inclui se tiver notas preenchidas
            for field in grade_fields:
                new_value = new_grade.get(field, "")
                if new_value:  # Se a nota não for vazia
                    changes.append(
                        f"Alteração em {new_grade['Disciplina']} ({new_grade['Código']}) - Semestre {new_grade['Semestre']}: {field} mudou de '' para '{new_value}'"
                    )
        else:
            # Disciplina existente: compara notas
            old_grade = old_dict[key]
            for field in grade_fields:
                old_value = old_grade.get(field, "")
                new_value = new_grade.get(field, "")
                if (
                    new_value != old_value and new_value
                ):  # Só inclui se o novo valor não for vazio
                    changes.append(
                        f"Alteração em {new_grade['Disciplina']} ({new_grade['Código']}) - Semestre {new_grade['Semestre']}: {field} mudou de '{old_value}' para '{new_value}'"
                    )

    if not changes:
        logging.info("Nenhuma mudança em notas detectada na comparação")
    else:
        logging.info(f"{len(changes)} mudanças em notas detectadas na comparação")
        for change in changes:
            logging.info(change)
    return changes


def run(playwright: Playwright) -> None:
    browser = playwright.chromium.launch(headless=config.HEADLESS_BROWSER)
    context = browser.new_context(
        viewport={"width": config.VIEWPORT_WIDTH, "height": config.VIEWPORT_HEIGHT}
    )
    page = context.new_page()

    changes_detected = []

    try:
        logging.info("Acessando a página de login do SIGAA")
        page.goto("https://sigaa.ufcg.edu.br/sigaa")
        page.wait_for_load_state("domcontentloaded", timeout=config.TIMEOUT_DEFAULT)

        logging.info("Preenchendo formulário de login")
        page.fill("input[name='user.login']", username)
        page.fill("input[name='user.senha']", password)
        page.click("input[type='submit']")
        page.wait_for_load_state("domcontentloaded", timeout=config.TIMEOUT_DEFAULT)

        logging.info("Verificando modal de cookies")
        try:
            cookie_button = page.locator("button.btn-primary:has-text('Ciente')")
            cookie_button.wait_for(state="visible", timeout=5000)
            if cookie_button.is_visible():
                cookie_button.click()
                logging.info("Modal de cookies aceito")
        except Exception as e:
            logging.warning(f"Erro ao aceitar modal de cookies: {str(e)}")

        logging.info("Verificando modals de mensagem")
        try:
            modal_close_button = page.locator("#yuievtautoid-0")
            modal_close_button.wait_for(state="visible", timeout=5000)
            if modal_close_button.is_visible():
                modal_close_button.click()
                logging.info("Modal de mensagem fechado")
        except Exception as e:
            logging.warning(f"Erro ao fechar modal de mensagem: {str(e)}")

        logging.info("Aguardando o menu principal carregar")
        page.wait_for_selector(
            "#menu_form_menu_discente_discente_menu",
            state="visible",
            timeout=config.TIMEOUT_DEFAULT,
        )
        page.locator("#menu_form_menu_discente_discente_menu").hover()

        logging.info("Tentando localizar o menu 'Ensino'")
        ensino_locator = page.locator(
            'span.ThemeOfficeMainFolderText:has-text("Ensino")'
        )
        ensino_locator.wait_for(state="visible", timeout=config.TIMEOUT_DEFAULT)
        ensino_locator.hover()
        page.wait_for_timeout(500)
        ensino_locator.click()
        page.wait_for_load_state("domcontentloaded", timeout=config.TIMEOUT_DEFAULT)

        logging.info("Tentando localizar a opção 'Consultar Minhas Notas'")
        notas_locator = page.locator(
            'td.ThemeOfficeMenuItemText:has-text("Consultar Minhas Notas")'
        ).first
        notas_locator.wait_for(state="visible", timeout=15000)
        notas_locator.click()

        logging.info("Aguardando carregamento completo da página de notas")
        page.wait_for_selector(
            "table.tabelaRelatorio", state="visible", timeout=config.TIMEOUT_DEFAULT
        )
        page.wait_for_load_state("networkidle", timeout=config.TIMEOUT_DEFAULT)

        logging.info("Salvando conteúdo da página de notas")
        page_content = page.content()
        with open(config.HTML_OUTPUT, "w", encoding="utf-8") as f:
            f.write(page_content)
        with open(config.HTML_DEBUG_OUTPUT, "w", encoding="utf-8") as f:
            f.write(page_content)

        table_count = page_content.count("tabelaRelatorio")
        row_count = page_content.count("<tr")
        logging.info(
            f"HTML contém {table_count} ocorrências de 'tabelaRelatorio' e {row_count} linhas '<tr>'"
        )

        if "tabelaRelatorio" not in page_content:
            logging.error("Tabela de notas não encontrada no HTML salvo")
            raise Exception("Tabela de notas não encontrada no HTML")

        grades = extract_all_grades(page_content)
        if not grades:
            logging.error("Nenhuma nota extraída do HTML")
            raise Exception("Nenhuma nota extraída do HTML")

        if config.CREATE_CSV:
            save_to_csv(grades)

        old_cache = load_cache()
        cache_grades = {}
        for grade in grades:
            semester = grade["Semestre"]
            if semester not in cache_grades:
                cache_grades[semester] = []
            cache_grades[semester].append(grade)

        changes_detected = compare_grades(old_cache, cache_grades)
        if changes_detected:
            logging.info("Mudanças detectadas nas notas:")
            for change in changes_detected:
                logging.info(change)
        else:
            logging.info(
                "Nenhuma mudança detectada nas notas em relação ao cache anterior."
            )

        save_cache(grades)

    except Exception as e:
        logging.error(f"Erro durante a execução do script: {str(e)}")
        raise

    finally:
        logging.info("Fechando o navegador")
        context.close()
        browser.close()

        print("\nMudanças detectadas nas notas em relação ao cache anterior:")
        if changes_detected:
            for change in changes_detected:
                print(f"- {change}")
        else:
            print("- Nenhuma mudança detectada.")

        # Enviar mudanças pro Telegram
        notify_changes(changes_detected)


if __name__ == "__main__":
    with sync_playwright() as playwright:
        try:
            run(playwright)
        except Exception as e:
            logging.error(f"Script finalizado com erro: {str(e)}")
            print(f"Erro: {str(e)}")
            print(
                f"Verifique os logs em '{config.LOG_FILENAME}' e o arquivo '{config.HTML_DEBUG_OUTPUT}' para mais detalhes."
            )
