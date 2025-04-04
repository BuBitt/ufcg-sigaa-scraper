import pytest
from unittest.mock import patch, MagicMock
from bs4 import BeautifulSoup

from scraper.extractor import extract_table_to_json, extract_and_save_grades


# Test extract_table_to_json function
@pytest.fixture
def sample_table_html():
    return """
    <table class="tabelaRelatorio">
        <thead>
            <tr>
                <th>Nome</th>
                <th>Matrícula</th>
                <th colspan="2">Unid. 1</th>
                <th>Faltas</th>
                <th>Sit.</th>
            </tr>
            <tr>
                <th></th>
                <th></th>
                <th>Prova</th>
                <th>Lista</th>
                <th></th>
                <th></th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td>Estudante Exemplo</td>
                <td>12345</td>
                <td>8.5</td>
                <td>9.0</td>
                <td>2</td>
                <td>APR</td>
            </tr>
        </tbody>
    </table>
    """


def test_extract_table_to_json_success(sample_table_html):
    result = extract_table_to_json(sample_table_html)
    assert result is not None
    assert len(result) == 1
    assert "Unid. 1 Prova" in result[0]
    assert result[0]["Unid. 1 Prova"] == "8.5"
    assert "Unid. 1 Lista" in result[0]
    assert result[0]["Unid. 1 Lista"] == "9.0"
    # Ensure excluded keys are not present
    assert "Nome" not in result[0]
    assert "Matrícula" not in result[0]
    assert "Faltas" not in result[0]
    assert "Sit." not in result[0]


def test_extract_table_to_json_no_table():
    html_without_table = "<div>No table here</div>"
    with patch("logging.error") as mock_log:
        result = extract_table_to_json(html_without_table)
        assert result is None
        assert any(
            "Tabela de notas não encontrada" in call[0][0]
            for call in mock_log.call_args_list
        )


def test_extract_table_to_json_error():
    with patch("bs4.BeautifulSoup", side_effect=Exception("Test error")):
        with patch("logging.error") as mock_log:
            result = extract_table_to_json("<table></table>")
            assert result is None
            # A verificação deve ser feita com o método assert_called() para confirmar que logging.error foi chamado
            mock_log.assert_called()
            # A mensagem de erro pode variar, então verificamos apenas se algum log de erro foi emitido


# Test extract_and_save_grades function
def test_extract_and_save_grades_with_table():
    # Mock page setup
    mock_page = MagicMock()
    mock_page.content.return_value = """
    <h3>Componente de Teste</h3>
    <table class="tabelaRelatorio">
        <thead><tr><th>Unid. 1</th></thead>
        <tbody><tr><td>8.5</td></tr></tbody>
    </table>
    """
    mock_page.locator.return_value.text_content.return_value = "Componente de Teste"
    mock_page.locator.return_value.count.return_value = 0

    # Mock extract_table_to_json
    grades_result = [{"Unid. 1": "8.5"}]

    all_grades = {}

    with patch("scraper.extractor.extract_table_to_json", return_value=grades_result):
        with patch("logging.info") as mock_log:
            extract_and_save_grades(mock_page, all_grades)

            assert "Componente de Teste" in all_grades
            assert all_grades["Componente de Teste"] == grades_result
            assert any(
                "Notas extraídas" in call[0][0] for call in mock_log.call_args_list
            )


def test_extract_and_save_grades_no_grades():
    # Mock page setup
    mock_page = MagicMock()
    mock_page.locator.return_value.text_content.return_value = "Componente de Teste"

    # Set up the first locator call to check for "Ainda não foram lançadas notas"
    no_grades_locator = MagicMock()
    no_grades_locator.count.return_value = 1

    component_name_locator = MagicMock()
    component_name_locator.text_content.return_value = "Componente de Teste"

    def mock_locator_side_effect(selector):
        if ":has-text('Ainda não foram lançadas notas.')" in selector:
            return no_grades_locator
        elif selector == "h3":
            return component_name_locator
        return MagicMock()

    mock_page.locator.side_effect = mock_locator_side_effect

    all_grades = {}

    with patch("logging.info") as mock_log:
        extract_and_save_grades(mock_page, all_grades)

        assert "Componente de Teste" in all_grades
        assert all_grades["Componente de Teste"] == "Ainda não foram lançadas notas."
        assert any(
            "Nenhuma nota lançada" in call[0][0] for call in mock_log.call_args_list
        )


def test_extract_and_save_grades_extraction_failure():
    # Mock page setup
    mock_page = MagicMock()
    mock_page.content.return_value = "<table class='tabelaRelatorio'></table>"
    mock_page.locator.return_value.text_content.return_value = "Componente de Teste"
    mock_page.locator.return_value.count.return_value = 0

    all_grades = {}

    with patch("scraper.extractor.extract_table_to_json", return_value=None):
        with patch("logging.error") as mock_log:
            extract_and_save_grades(mock_page, all_grades)

            assert "Componente de Teste" not in all_grades
            assert any(
                "Erro ao processar a tabela" in call[0][0]
                for call in mock_log.call_args_list
            )
