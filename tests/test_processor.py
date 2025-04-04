import pytest
from unittest.mock import patch, MagicMock, call

from scraper.processor import handle_class_switch, process_all_courses


# Test handle_class_switch function
def test_handle_class_switch_success():
    mock_page = MagicMock()
    processed_classes = set()
    all_grades = {}

    # Mock the turmas locator with two classes
    mock_turmas = MagicMock()
    mock_turmas.count.return_value = 2

    mock_turma1 = MagicMock()
    mock_turma1_span = MagicMock()
    mock_turma1_span.text_content.return_value = "Turma 1"
    mock_turma1.locator.return_value = mock_turma1_span

    mock_turma2 = MagicMock()
    mock_turma2_span = MagicMock()
    mock_turma2_span.text_content.return_value = "Turma 2"
    mock_turma2.locator.return_value = mock_turma2_span

    # Set up the turmas.nth() method to return the mocked turmas
    mock_turmas.nth.side_effect = [mock_turma1, mock_turma2]

    # Set up the page.locator method to return different mocks based on the selector
    def mock_locator_side_effect(selector):
        if "div#j_id_jsp_1879301362_4 a.linkTurma" in selector:
            return mock_turmas
        return MagicMock()

    mock_page.locator.side_effect = mock_locator_side_effect

    with patch("scraper.extractor.extract_and_save_grades"):
        with patch("logging.info") as mock_log:
            result = handle_class_switch(mock_page, processed_classes, all_grades)

            assert result is True
            assert "Turma 1" in processed_classes
            assert "Turma 2" in processed_classes
            assert mock_page.go_back.call_count >= 2
            assert any(
                "Todas as turmas já foram processadas" in call.args[0]
                for call in mock_log.call_args_list
            )


def test_handle_class_switch_error():
    mock_page = MagicMock()
    mock_page.go_back.side_effect = Exception("Test error")
    processed_classes = set()
    all_grades = {}

    with patch("logging.error") as mock_log:
        result = handle_class_switch(mock_page, processed_classes, all_grades)

        assert result is False
        assert any(
            "Erro ao trocar de turma" in call[0][0] for call in mock_log.call_args_list
        )


# Test process_all_courses function
def test_process_all_courses_login_failed():
    mock_page = MagicMock()
    mock_browser = MagicMock()

    with patch("scraper.browser.perform_login", return_value=False):
        result = process_all_courses(
            mock_page, mock_browser, "test_user", "test_password"
        )

        assert result == {}


def test_process_all_courses_successful():
    mock_page = MagicMock()
    mock_browser = MagicMock()

    # Mock component_links with one component
    mock_links = MagicMock()
    mock_links.all.return_value = [MagicMock()]

    # Set up the page.locator method
    def mock_locator_side_effect(selector):
        if "tbody tr td.descricao a" in selector:
            return mock_links
        elif "div.itemMenuHeaderAlunos" in selector:
            mock_menu = MagicMock()
            mock_menu.first = MagicMock()
            return mock_menu
        return MagicMock()

    mock_page.locator.side_effect = mock_locator_side_effect

    with patch("scraper.browser.perform_login", return_value=True):
        with patch("scraper.extractor.extract_and_save_grades"):
            with patch("scraper.processor.handle_class_switch", return_value=True):
                result = process_all_courses(
                    mock_page, mock_browser, "test_user", "test_password"
                )

                assert isinstance(result, dict)
                mock_page.locator.assert_any_call("tbody tr td.descricao a")
                mock_page.locator.assert_any_call("div.itemMenuHeaderAlunos")


def test_process_all_courses_with_error():
    mock_page = MagicMock()
    mock_browser = MagicMock()

    with patch("scraper.browser.perform_login", return_value=True):
        with patch("scraper.processor.handle_class_switch"):
            with patch("logging.error") as mock_log:
                # Set up an error during processing
                mock_page.locator.side_effect = Exception("Test error")

                result = process_all_courses(
                    mock_page, mock_browser, "test_user", "test_password"
                )

                assert result == {}
                assert any(
                    "Erro ao processar os cursos" in call[0][0]
                    for call in mock_log.call_args_list
                )
