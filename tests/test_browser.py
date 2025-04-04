import pytest
from unittest.mock import patch, MagicMock

from scraper.browser import (
    create_browser,
    close_browser,
    save_cookies,
    load_cookies,
    are_cookies_valid,
    perform_login,
)


# Test create_browser function
def test_create_browser():
    # Mock Playwright objects
    mock_playwright = MagicMock()
    mock_browser = MagicMock()
    mock_context = MagicMock()
    mock_page = MagicMock()

    # Setup mock return values
    mock_playwright.chromium.launch.return_value = mock_browser
    mock_browser.new_context.return_value = mock_context
    mock_context.new_page.return_value = mock_page

    # Call the function
    browser, context, page = create_browser(mock_playwright)

    # Verify the results
    assert browser == mock_browser
    assert context == mock_context
    assert page == mock_page
    mock_playwright.chromium.launch.assert_called_once()
    mock_browser.new_context.assert_called_once()
    mock_context.new_page.assert_called_once()


# Test close_browser function
def test_close_browser_success():
    mock_browser = MagicMock()

    with patch("logging.info") as mock_log:
        close_browser(mock_browser)
        mock_browser.close.assert_called_once()
        assert any(
            "fechado com sucesso" in call[0][0] for call in mock_log.call_args_list
        )


def test_close_browser_error():
    mock_browser = MagicMock()
    mock_browser.close.side_effect = Exception("Test error")

    with patch("logging.error") as mock_log:
        close_browser(mock_browser)
        mock_browser.close.assert_called_once()
        assert any("Erro ao fechar" in call[0][0] for call in mock_log.call_args_list)


# Test save_cookies function
def test_save_cookies_success():
    mock_context = MagicMock()
    mock_context.cookies.return_value = [{"name": "test", "value": "test"}]

    with patch("builtins.open", MagicMock()):
        with patch("json.dump") as mock_dump:
            with patch("logging.info") as mock_log:
                save_cookies(mock_context)
                mock_context.cookies.assert_called_once()
                mock_dump.assert_called_once()
                assert any(
                    "salvos com sucesso" in call[0][0]
                    for call in mock_log.call_args_list
                )


def test_save_cookies_error():
    mock_context = MagicMock()
    mock_context.cookies.side_effect = Exception("Test error")

    with patch("logging.error") as mock_log:
        save_cookies(mock_context)
        mock_context.cookies.assert_called_once()
        assert any(
            "Erro ao salvar cookies" in call[0][0] for call in mock_log.call_args_list
        )


# Test load_cookies function
def test_load_cookies_success():
    mock_context = MagicMock()
    test_cookies = [{"name": "test", "value": "test"}]

    with patch("os.path.exists", return_value=True):
        with patch("builtins.open", MagicMock()):
            with patch("json.load", return_value=test_cookies):
                with patch("logging.info") as mock_log:
                    load_cookies(mock_context)
                    mock_context.add_cookies.assert_called_once()
                    assert any(
                        "carregados com sucesso" in call[0][0]
                        for call in mock_log.call_args_list
                    )


def test_load_cookies_file_not_found():
    mock_context = MagicMock()

    with patch("os.path.exists", return_value=False):
        with patch("logging.info") as mock_log:
            load_cookies(mock_context)
            assert not mock_context.add_cookies.called
            assert any(
                "não encontrado" in call[0][0] for call in mock_log.call_args_list
            )


# Test are_cookies_valid function
def test_are_cookies_valid_success():
    mock_page = MagicMock()
    mock_page.url = "https://sigaa.ufcg.edu.br/sigaa/home"
    mock_locator = MagicMock()
    mock_locator.count.return_value = 0
    mock_page.locator.return_value = mock_locator

    with patch("logging.info") as mock_log:
        result = are_cookies_valid(mock_page)
        assert result is True
        assert any("Sessão válida" in call[0][0] for call in mock_log.call_args_list)


def test_are_cookies_valid_invalid():
    mock_page = MagicMock()
    mock_page.url = "https://sigaa.ufcg.edu.br/sigaa/login"
    mock_page.locator.return_value.count.return_value = 1

    with patch("logging.info") as mock_log:
        result = are_cookies_valid(mock_page)
        assert result is False
        assert any("Sessão inválida" in call[0][0] for call in mock_log.call_args_list)


# Test perform_login function
def test_perform_login_success():
    mock_page = MagicMock()
    mock_page.url = "https://sigaa.ufcg.edu.br/sigaa/home"

    with patch("logging.info") as mock_log:
        result = perform_login(mock_page, "test_user", "test_password")
        assert result is True
        mock_page.fill.assert_any_call("input[name='user.login']", "test_user")
        mock_page.fill.assert_any_call("input[name='user.senha']", "test_password")
        mock_page.click.assert_called_once()
        assert any(
            "Login realizado com sucesso" in call[0][0]
            for call in mock_log.call_args_list
        )


def test_perform_login_failure():
    mock_page = MagicMock()
    mock_page.url = "https://sigaa.ufcg.edu.br/sigaa/login"

    with patch("logging.error") as mock_log:
        result = perform_login(mock_page, "test_user", "test_password")
        assert result is False
        assert any("Falha no login" in call[0][0] for call in mock_log.call_args_list)
