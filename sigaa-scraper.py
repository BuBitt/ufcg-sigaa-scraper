from playwright.sync_api import Playwright, sync_playwright
import logging
import os
import json
from bs4 import BeautifulSoup, FeatureNotFound  # Importei FeatureNotFound
from telegram_notifier import notify_changes
import config

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


load_env()
username = os.getenv("SIGAA_USERNAME")
password = os.getenv("SIGAA_PASSWORD")
if not username or not password:
    logging.error("SIGAA_USERNAME e SIGAA_PASSWORD devem estar no .env")
    raise ValueError("SIGAA_USERNAME e SIGAA_PASSWORD devem estar no .env")


# Extrai notas do HTML com eficiência
def extract_grades(html_content):
    # Tenta usar lxml, com fallback pra html.parser
    try:
        soup = BeautifulSoup(html_content, "lxml")
    except FeatureNotFound:
        logging.warning("lxml não encontrado, usando html.parser (mais lento)")
        soup = BeautifulSoup(html_content, "html.parser")

    grades = []
    for table in soup.find_all("table", class_="tabelaRelatorio"):
        semester = (
            table.caption.text.strip() if table.caption else "Semestre Desconhecido"
        )
        for row in table.tbody.find_all("tr", class_=lambda x: x and "linha" in x):
            cols = [col.text.strip() for col in row.find_all("td")]
            if len(cols) >= 2:
                cols += [""] * (15 - len(cols))
                grades.append(
                    {
                        "Semestre": semester,
                        "Código": cols[0],
                        "Disciplina": cols[1],
                        "Unidade 1": "" if cols[2] == "--" else cols[2],
                        "Unidade 2": "" if cols[3] == "--" else cols[3],
                        "Unidade 3": "" if cols[4] == "--" else cols[4],
                        "Unidade 4": "" if cols[5] == "--" else cols[5],
                        "Unidade 5": "" if cols[6] == "--" else cols[6],
                        "Unidade 6": "" if cols[7] == "--" else cols[7],
                        "Unidade 7": "" if cols[8] == "--" else cols[8],
                        "Unidade 8": "" if cols[9] == "--" else cols[9],
                        "Unidade 9": "" if cols[10] == "--" else cols[10],
                        "Recuperação": "" if cols[11] == "--" else cols[11],
                        "Resultado": "" if cols[12] == "--" else cols[12],
                        "Faltas": cols[13],
                        "Situação": cols[14],
                    }
                )
    if not grades:
        logging.warning("Nenhuma nota encontrada")
    else:
        logging.info(f"{len(grades)} notas extraídas")
    return grades


# Carrega cache
def load_cache(filename=config.CACHE_FILENAME):
    try:
        with open(filename, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
    except Exception as e:
        logging.error(f"Erro ao carregar cache: {e}")
        return {}


# Salva cache
def save_cache(grades, filename=config.CACHE_FILENAME):
    cache = {}
    for grade in grades:
        cache.setdefault(grade["Semestre"], []).append(grade)
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False)
    logging.info(f"Cache salvo em {filename}")


# Compara notas
def compare_grades(old_grades, new_grades):
    changes = []
    grade_fields = ["Unidade " + str(i) for i in range(1, 10)] + [
        "Recuperação",
        "Resultado",
    ]
    old_dict = {
        f"{g['Semestre']}-{g['Código']}": g for s, gs in old_grades.items() for g in gs
    }
    new_dict = {
        f"{g['Semestre']}-{g['Código']}": g for s, gs in new_grades.items() for g in gs
    }

    for key, new_grade in new_dict.items():
        old_grade = old_dict.get(key, {})
        for field in grade_fields:
            old_value = old_grade.get(field, "")
            new_value = new_grade.get(field, "")
            if new_value and new_value != old_value:
                changes.append(
                    f"Alteração em {new_grade['Disciplina']} ({new_grade['Código']}) - Semestre {new_grade['Semestre']}: {field} mudou de '{old_value}' para '{new_value}'"
                )

    if changes:
        logging.info(f"{len(changes)} mudanças detectadas")
        for change in changes:
            logging.info(change)
    else:
        logging.info("Nenhuma mudança detectada")
    return changes


# Função principal
def run(playwright: Playwright):
    browser = playwright.chromium.launch(headless=config.HEADLESS_BROWSER)
    context = browser.new_context(
        viewport={"width": config.VIEWPORT_WIDTH, "height": config.VIEWPORT_HEIGHT}
    )
    page = context.new_page()
    changes_detected = []

    try:
        logging.info("Acessando SIGAA")
        page.goto("https://sigaa.ufcg.edu.br/sigaa", wait_until="domcontentloaded")

        logging.info("Fazendo login")
        page.fill("input[name='user.login']", username)
        page.fill("input[name='user.senha']", password)
        page.click("input[type='submit']", timeout=config.TIMEOUT_DEFAULT)

        logging.info("Lidando com modais")
        page.locator("button.btn-primary:has-text('Ciente')").click(
            timeout=5000, force=True
        )
        page.locator("#yuievtautoid-0").click(timeout=5000, force=True)

        logging.info("Navegando para notas")
        page.wait_for_selector(
            "#menu_form_menu_discente_discente_menu", timeout=config.TIMEOUT_DEFAULT
        )
        page.locator("#menu_form_menu_discente_discente_menu").hover()
        page.locator('span.ThemeOfficeMainFolderText:has-text("Ensino")').click(
            timeout=config.TIMEOUT_DEFAULT
        )
        page.locator(
            'td.ThemeOfficeMenuItemText:has-text("Consultar Minhas Notas")'
        ).first.click(timeout=15000)
        page.wait_for_selector("table.tabelaRelatorio", timeout=config.TIMEOUT_DEFAULT)

        logging.info("Extraindo notas")
        grades = extract_grades(page.content())
        if not grades:
            raise Exception("Nenhuma nota extraída")

        old_cache = load_cache()
        new_grades = {}
        for grade in grades:
            new_grades.setdefault(grade["Semestre"], []).append(grade)
        changes_detected = compare_grades(old_cache, new_grades)
        save_cache(grades)

    except Exception as e:
        logging.error(f"Erro: {e}")
        raise

    finally:
        browser.close()
        print("\nMudanças detectadas:")
        print("\n".join([f"- {c}" for c in changes_detected]) or "- Nenhuma mudança.")
        notify_changes(changes_detected)


if __name__ == "__main__":
    with sync_playwright() as playwright:
        try:
            run(playwright)
        except Exception as e:
            logging.error(f"Erro final: {e}")
            print(f"Erro: {e}")
