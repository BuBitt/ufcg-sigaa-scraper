import logging
import sys
import config
from scraper.browser import perform_login
from scraper.extractor import extract_and_save_grades


def get_all_turmas(page):
    """
    Retrieve all available turmas (classes) from the "Trocar de Turma" menu.

    Args:
        page: The browser page

    Returns:
        list: A list of turma names
    """
    try:
        logging.info("Identificando todas as turmas disponíveis")
        page.wait_for_selector(
            "div#j_id_jsp_1879301362_4 a.linkTurma",
            timeout=config.TIMEOUT_DEFAULT,
        )
        turmas = page.locator("div#j_id_jsp_1879301362_4 a.linkTurma")
        turma_names = [
            turmas.nth(i).locator("span").text_content().strip()
            for i in range(turmas.count())
        ]
        logging.info(f"Turmas identificadas: {turma_names}")
        return turma_names
    except Exception as e:
        logging.error(f"Erro ao identificar turmas: {e}")
        return []


def handle_class_switch(page, processed_classes, all_grades, turma_names):
    """
    Handle switching between classes (turmas) and process their grades.

    Args:
        page: The browser page
        processed_classes (set): Set of already processed classes
        all_grades (dict): Dictionary to store the extracted grades
        turma_names (list): List of all turma names
    """
    try:
        for turma_name in turma_names:
            if turma_name not in processed_classes:
                logging.info(f"Acessando turma: {turma_name}")
                processed_classes.add(turma_name)

                # Click on the turma
                page.locator(f"span:has-text('{turma_name}')").click()

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
        return True

    except Exception as e:
        logging.error(f"Erro ao trocar de turma e processar: {e}")
        return False


def process_all_courses(page, browser, username, password):
    """
    Process all courses and extract their grades.

    Args:
        page: The browser page
        browser: The browser instance
        username (str): SIGAA username
        password (str): SIGAA password

    Returns:
        dict: Dictionary containing all extracted grades
    """
    all_grades = {}
    processed_classes = set()

    try:
        # Perform login
        if not perform_login(page, username, password):
            return all_grades

        logging.info("Identificando todos os links de Componentes Curriculares")
        page.wait_for_selector(
            "tbody tr td.descricao a", timeout=config.TIMEOUT_DEFAULT
        )
        component_links = page.locator("tbody tr td.descricao a").all()

        logging.info(f"Encontrados {len(component_links)} componentes curriculares")

        for i in range(len(component_links)):
            logging.info(f"Acessando componente curricular {i + 1}")
            page.locator("tbody tr td.descricao a").nth(i).click()

            logging.info("Expandindo o menu 'Alunos'")
            try:
                alunos_menu = page.locator("div.itemMenuHeaderAlunos").first
                page.wait_for_selector(
                    "div.itemMenuHeaderAlunos",
                    timeout=config.TIMEOUT_DEFAULT,
                )
                alunos_menu.click()
            except Exception as e:
                logging.error(f"Erro ao expandir o menu 'Alunos': {e}")
                continue

            logging.info("Clicando em 'Ver Notas'")
            try:
                page.wait_for_selector(
                    "div.itemMenuHeaderAlunos + div a:has-text('Ver Notas')",
                    timeout=config.TIMEOUT_DEFAULT,
                )
                page.locator(
                    "div.itemMenuHeaderAlunos + div a:has-text('Ver Notas')"
                ).click()
            except Exception as e:
                logging.error(f"Erro ao clicar em 'Ver Notas': {e}")
                continue

            logging.info("Extraindo e salvando notas")
            extract_and_save_grades(page, all_grades)

            logging.info("Identificando todas as turmas disponíveis")
            page.go_back()
            page.wait_for_selector(
                "button#formAcoesTurma\\:botaoTrocarTurma",
                timeout=config.TIMEOUT_DEFAULT,
            )
            page.locator("button#formAcoesTurma\\:botaoTrocarTurma").click()

            turma_names = get_all_turmas(page)

            done = False
            while not done:
                try:
                    logging.info("Trocando para a próxima turma")
                    done = handle_class_switch(
                        page, processed_classes, all_grades, turma_names
                    )
                except Exception as e:
                    logging.info(f"Não há mais turmas para trocar: {e}")
                    break

            logging.info("Todas as turmas já foram processadas.")
            return all_grades  # Stop processing after all turmas are processed

    except Exception as e:
        logging.error(f"Erro ao processar os cursos: {e}")

    return all_grades
