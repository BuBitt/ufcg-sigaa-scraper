import os
import pytest
from unittest.mock import patch, MagicMock

from notification.telegram import (
    get_telegram_credentials,
    replace_discipline_name,
    generate_message,
    send_telegram_message,
    notify_changes,
)


# Test get_telegram_credentials function
def test_get_telegram_credentials_success():
    with patch.dict(
        os.environ,
        {
            "TELEGRAM_BOT_TOKEN": "test_token",
            "TELEGRAM_GROUP_CHAT_ID": "test_group_id",
            "TELEGRAM_PRIVATE_CHAT_ID": "test_private_id",
        },
    ):
        with patch("config.SEND_TELEGRAM_GROUP", True):
            with patch("config.SEND_TELEGRAM_PRIVATE", True):
                group_id, private_id, token = get_telegram_credentials()
                assert group_id == "test_group_id"
                assert private_id == "test_private_id"
                assert token == "test_token"


def test_get_telegram_credentials_missing():
    with patch.dict(os.environ, {}):
        with patch("config.SEND_TELEGRAM_GROUP", True):
            with patch("config.SEND_TELEGRAM_PRIVATE", True):
                with pytest.raises(ValueError, match="Credenciais do Telegram incompletas no .env"):
                    get_telegram_credentials()


# Test replace_discipline_name function
def test_replace_discipline_name():
    replacements = {"Long Name": "Short Name"}
    assert replace_discipline_name("Long Name", replacements) == "Short Name"
    assert replace_discipline_name("Unknown Name", replacements) == "Unknown Name"


# Test generate_message function
def test_generate_message_detailed():
    changes = {
        "Component 1 - Test Discipline (2022.1)": [
            {"Unid. 1 Prova": {"old": "", "new": "8.5"}}
        ]
    }
    replacements = {"Test Discipline": "TD"}

    result = generate_message(changes, replacements, detailed=True)
    assert result is not None
    assert "Novas notas foram adicionadas" in result
    assert "TD" in result
    assert "8.5" in result


def test_generate_message_simple():
    changes = {
        "Component 1 - Test Discipline (2022.1)": [
            {"Unid. 1 Prova": {"old": "", "new": "8.5"}}
        ]
    }
    replacements = {"Test Discipline": "TD"}

    result = generate_message(changes, replacements, detailed=False)
    assert result is not None
    assert "Novas notas foram adicionadas" in result
    assert "TD" in result
    assert "8.5" not in result


def test_generate_message_empty():
    assert generate_message({}, {}) is None


# Test send_telegram_message function
def test_send_telegram_message_success():
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None

    with patch("requests.post", return_value=mock_response):
        with patch("logging.debug") as mock_log:
            send_telegram_message("Test message", "123456", "test_token")
            assert any(
                "Mensagem enviada" in call[0][0] for call in mock_log.call_args_list
            )


def test_send_telegram_message_error():
    with patch("requests.post", side_effect=Exception("Test error")):
        with patch("logging.error") as mock_log:
            send_telegram_message("Test message", "123456", "test_token")
            assert any(
                "Erro ao enviar mensagem" in call[0][0]
                for call in mock_log.call_args_list
            )


def test_send_telegram_message_empty():
    with patch("requests.post") as mock_post:
        send_telegram_message(None, "123456", "test_token")
        mock_post.assert_not_called()


# Test notify_changes function
def test_notify_changes_all_enabled():
    changes = {
        "Component 1 - Test Discipline (2022.1)": [
            {"Unid. 1 Prova": {"old": "", "new": "8.5"}}
        ]
    }

    # Mock credentials and message generation
    with patch(
        "notification.telegram.get_telegram_credentials",
        return_value=("group_id", "private_id", "token"),
    ):
        with patch(
            "notification.telegram.load_discipline_replacements", return_value={}
        ):
            with patch(
                "notification.telegram.generate_message", return_value="Test message"
            ):
                with patch("notification.telegram.send_telegram_message") as mock_send:
                    with patch("config.SEND_TELEGRAM_GROUP", True):
                        with patch("config.SEND_TELEGRAM_PRIVATE", True):
                            notify_changes(changes)
                            assert mock_send.call_count == 2


def test_notify_changes_group_only():
    changes = {
        "Component 1 - Test Discipline (2022.1)": [
            {"Unid. 1 Prova": {"old": "", "new": "8.5"}}
        ]
    }

    # Mock credentials and message generation
    with patch(
        "notification.telegram.get_telegram_credentials",
        return_value=("group_id", None, "token"),
    ):
        with patch(
            "notification.telegram.load_discipline_replacements", return_value={}
        ):
            with patch(
                "notification.telegram.generate_message", return_value="Test message"
            ):
                with patch("notification.telegram.send_telegram_message") as mock_send:
                    with patch("config.SEND_TELEGRAM_GROUP", True):
                        with patch("config.SEND_TELEGRAM_PRIVATE", False):
                            notify_changes(changes)
                            assert mock_send.call_count == 1


def test_notify_changes_empty():
    with patch("notification.telegram.send_telegram_message") as mock_send:
        with patch("config.SEND_TELEGRAM_GROUP", True):
            with patch("config.SEND_TELEGRAM_PRIVATE", True):
                notify_changes({})
                mock_send.assert_not_called()


def test_notify_changes_disabled():
    changes = {"Component 1": [{"Unid. 1": {"old": "", "new": "8.5"}}]}

    with patch("notification.telegram.send_telegram_message") as mock_send:
        with patch("config.SEND_TELEGRAM_GROUP", False):
            with patch("config.SEND_TELEGRAM_PRIVATE", False):
                notify_changes(changes)
                mock_send.assert_not_called()
