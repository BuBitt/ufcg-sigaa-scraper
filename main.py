from playwright.sync_api import sync_playwright
import os
import logging

from utils.logger import setup_logging
from utils.file_handler import load_env, load_grades, save_grades, compare_grades
from scraper.browser import create_browser, close_browser
from scraper.processor import process_all_courses
from notification.telegram import notify_changes


def main():
    """
    Main entry point for the SIGAA grade scraper application.
    """
    # Setup logging
    setup_logging()

    # Load environment variables and get credentials
    load_env()
    username = os.getenv("SIGAA_USERNAME")
    password = os.getenv("SIGAA_PASSWORD")

    if not username or not password:
        logging.error("SIGAA_USERNAME e SIGAA_PASSWORD devem estar no .env")
        raise ValueError("SIGAA_USERNAME e SIGAA_PASSWORD devem estar no .env")

    with sync_playwright() as playwright:
        try:
            # Initialize browser and extract grades
            browser, context, page = create_browser(playwright)
            all_grades = process_all_courses(page, browser, username, password)

            # Compare with previous grades
            saved_grades = load_grades()
            differences = compare_grades(all_grades, saved_grades)

            # Notify if there are changes
            if differences:
                notify_changes(differences)

            # Save new grades
            save_grades(all_grades)

        except Exception as e:
            logging.error(f"Erro durante a execução: {e}")
        finally:
            close_browser(browser)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logging.error(f"Erro fatal: {e}")
        print(f"Erro: {e}")
