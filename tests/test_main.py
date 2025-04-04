import pytest
from unittest.mock import patch, MagicMock
import sys
import os

# Make sure the project root is in the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import main


def test_main_success():
    # Mock all dependencies
    with patch("utils.logger.setup_logging"):
        with patch("utils.file_handler.load_env"):
            with patch.dict(
                "os.environ", {"SIGAA_USERNAME": "test", "SIGAA_PASSWORD": "test"}
            ):
                with patch("playwright.sync_api.sync_playwright") as mock_playwright:
                    # Set up mocked browser components
                    mock_browser = MagicMock()
                    mock_context = MagicMock()
                    mock_page = MagicMock()

                    # Mock create_browser return
                    with patch(
                        "scraper.browser.create_browser",
                        return_value=(mock_browser, mock_context, mock_page),
                    ):
                        # Mock process_all_courses with example data
                        example_grades = {"Component 1": [{"Unid. 1": "8.5"}]}
                        with patch(
                            "scraper.processor.process_all_courses",
                            return_value=example_grades,
                        ):
                            # Mock remaining functions
                            with patch(
                                "utils.file_handler.load_grades", return_value={}
                            ):
                                with patch(
                                    "utils.file_handler.compare_grades",
                                    return_value={
                                        "Component 1": [
                                            {"Unid. 1": {"old": "", "new": "8.5"}}
                                        ]
                                    },
                                ):
                                    with patch("notification.telegram.notify_changes") as mock_notify:
                                        "notification.telegram.notify_changes"ades"):
                                    ) as mock_notify:h("scraper.browser.close_browser"):
                                        with patch("utils.file_handler.save_grades"):
                                            with patch("scraper.browser.close_browser"):
                                                # Execute main
                                                main.main()tifications were called
                                                mock_notify.assert_called_once()
                                                # Verify notifications were called
                                                main.notify_changes.assert_called_once()
def test_main_missing_credentials():
    with patch("utils.logger.setup_logging"):
def test_main_missing_credentials():er.load_env"):
    with patch("utils.logger.setup_logging"): clear=True):
        with patch("utils.file_handler.load_env"):k_log:
            with patch.dict("os.environ", {}, clear=True):
                with patch("logging.error") as mock_log:
                    with pytest.raises(ERNAME e SIGAA_PASSWORD devem estar no .env",ValueError, match="SIGAA_USERNAME e SIGAA_PASSWORD devem estar no .env"):
                        ValueError,
                        match="SIGAA_USERNAME e SIGAA_PASSWORD devem estar no .env",
                    ):  "SIGAA_USERNAME e SIGAA_PASSWORD" in call[0][0]sert any(
                        for call in mock_log.call_args_listNAME e SIGAA_PASSWORD" in call[0][0]
                    )l in mock_log.call_args_list


def test_main_with_execution_error():
    with patch("utils.logger.setup_logging"):
        def test_main_with_execution_error():
        with patch("utils.file_handler.load_env"):    with patch("utils.logger.setup_logging"):
            with patch.dict("os.environ", {"SIGAA_USERNAME": "test", "SIGAA_PASSWORD": "test"}):
                "os.environ", {"SIGAA_USERNAME": "test", "SIGAA_PASSWORD": "test"}
            ):test", "SIGAA_PASSWORD": "test"}
                with patch("playwright.sync_api.sync_playwright"):
                    with patch(
                        "scraper.browser.create_browser",      with patch(
                        side_effect=Exception("Test error"),
                    ):fect=Exception("Test error"),
                        with patch("logging.error") as mock_log:
                            with patch("scraper.browser.close_browser"):log:
                                main.main()      with patch("scraper.browser.close_browser"):
                                assert any(
                                    "Erro durante a execução" in call[0][0]
                                    for call in mock_log.call_args_listurante a execução" in call[0][0]
                                )l in mock_log.call_args_list


def test_main_program_fatal_error():
    with patch("main.main", side_effect=Exception("Fatal error")):def test_main_program_fatal_error():
        with patch("logging.error") as mock_log:    with patch("main.main", side_effect=Exception("Fatal error")):
            try:as mock_log:
                main.main()
            except Exception:
                passpt Exception:
            assert any("Erro fatal" in call.args[0] for call in mock_log.call_args_list)
