import os
import json
import pytest
from unittest.mock import mock_open, patch, MagicMock
import logging

from utils.file_handler import (
    load_env,
    load_grades,
    save_grades,
    compare_grades,
    load_discipline_replacements,
)


# Test load_env function
@pytest.fixture
def mock_env_file():
    return """
SIGAA_USERNAME=test_user
SIGAA_PASSWORD=test_password
TELEGRAM_BOT_TOKEN=1234:token
TELEGRAM_GROUP_CHAT_ID=-1001234567890
TELEGRAM_PRIVATE_CHAT_ID=1234567890
    """


def test_load_env_success(mock_env_file):
    with patch("builtins.open", mock_open(read_data=mock_env_file)):
        load_env()
        assert os.environ["SIGAA_USERNAME"] == "test_user"
        assert os.environ["SIGAA_PASSWORD"] == "test_password"
        assert os.environ["TELEGRAM_BOT_TOKEN"] == "1234:token"
        assert os.environ["TELEGRAM_GROUP_CHAT_ID"] == "-1001234567890"
        assert os.environ["TELEGRAM_PRIVATE_CHAT_ID"] == "1234567890"


def test_load_env_file_not_found():
    with patch("builtins.open", side_effect=FileNotFoundError):
        with pytest.raises(FileNotFoundError):
            load_env()


def test_load_env_format_error():
    with patch("builtins.open", mock_open(read_data="INVALID_FORMAT")):
        with pytest.raises(Exception):
            load_env()


# Test load_grades function
def test_load_grades_existing_file():
    test_data = {"Component 1": [{"Unid. 1": "8.5"}]}
    with patch("os.path.exists", return_value=True):
        with patch("builtins.open", mock_open(read_data=json.dumps(test_data))):
            grades = load_grades()
            assert grades == test_data


def test_load_grades_empty_file():
    with patch("os.path.exists", return_value=True):
        with patch("builtins.open", mock_open(read_data="")):
            with patch("logging.warning") as mock_log:
                grades = load_grades()
                assert grades == {}
                mock_log.assert_called_once()


def test_load_grades_non_existing_file():
    with patch("os.path.exists", return_value=False):
        with patch("logging.info") as mock_log:
            grades = load_grades()
            assert grades == {}
            mock_log.assert_called_once()


# Test save_grades function
def test_save_grades_success():
    test_data = {"Component 1": [{"Unid. 1": "8.5"}]}
    mock_file = mock_open()
    with patch("builtins.open", mock_file):
        with patch("logging.info") as mock_log:
            save_grades(test_data)
            mock_log.assert_called_once()

    # Verify the data was written correctly
    handle = mock_file()
    handle.write.assert_called_once_with(
        json.dumps(test_data, ensure_ascii=False, indent=4)
    )


# Test compare_grades function
def test_compare_grades_no_differences():
    old_grades = {"Component 1": [{"Unid. 1": "8.5"}]}
    new_grades = {"Component 1": [{"Unid. 1": "8.5"}]}

    with patch("logging.info") as mock_log:
        differences = compare_grades(new_grades, old_grades)
        assert differences == {}
        # Check logging
        assert any(
            "Nenhuma diferença" in call[0][0] for call in mock_log.call_args_list
        )


def test_compare_grades_new_component():
    old_grades = {"Component 1": [{"Unid. 1": "8.5"}]}
    new_grades = {
        "Component 1": [{"Unid. 1": "8.5"}],
        "Component 2": [{"Unid. 1": "7.0"}],
    }

    with patch("logging.info") as mock_log:
        differences = compare_grades(new_grades, old_grades)
        assert "Component 2" in differences
        assert differences["Component 2"]["status"] == "Novo componente"
        # Check logging
        assert any(
            "Diferenças encontradas" in call[0][0] for call in mock_log.call_args_list
        )


def test_compare_grades_changed_grade():
    old_grades = {"Component 1": [{"Unid. 1": "8.5"}]}
    new_grades = {"Component 1": [{"Unid. 1": "9.0"}]}

    differences = compare_grades(new_grades, old_grades)
    assert "Component 1" in differences
    assert "Unid. 1" in differences["Component 1"][0]
    assert differences["Component 1"][0]["Unid. 1"]["old"] == "8.5"
    assert differences["Component 1"][0]["Unid. 1"]["new"] == "9.0"


def test_compare_grades_removed_component():
    old_grades = {
        "Component 1": [{"Unid. 1": "8.5"}],
        "Component 2": [{"Unid. 1": "7.0"}],
    }
    new_grades = {"Component 1": [{"Unid. 1": "8.5"}]}

    differences = compare_grades(new_grades, old_grades)
    assert "Component 2" in differences
    assert differences["Component 2"]["status"] == "Removido"


# Test load_discipline_replacements function
def test_load_discipline_replacements_success():
    test_data = {"Long Name": "Short Name"}
    with patch("os.path.exists", return_value=True):
        with patch("builtins.open", mock_open(read_data=json.dumps(test_data))):
            replacements = load_discipline_replacements()
            assert replacements == test_data


def test_load_discipline_replacements_file_not_found():
    with patch("builtins.open", side_effect=FileNotFoundError):
        with patch("logging.warning") as mock_log:
            replacements = load_discipline_replacements()
            assert replacements == {}
            mock_log.assert_called_once()
