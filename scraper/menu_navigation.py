"""
Módulo para navegação via menu Ensino > Consultar Minhas Notas.
Implementação baseada na branch menu-ensino-notas.
"""

import logging
import time
from typing import Dict, Any
from playwright.sync_api import Page
import config


def navigate_to_grades_via_menu(page: Page) -> bool:
    """
    Navega para a seção de notas através do menu Ensino > Consultar Minhas Notas.
    
    Args:
        page: Página do navegador.
        
    Returns:
        bool: True se a navegação foi bem-sucedida, False caso contrário.
    """
    try:
        logging.info("📍 Iniciando navegação via menu Ensino > Consultar Minhas Notas")
        
        # Etapa 1: Aguardar menu principal
        logging.debug("⏳ Aguardando carregamento do menu principal")
        try:
            page.wait_for_selector(
                "#menu_form_menu_discente_discente_menu", 
                timeout=10000
            )
            logging.debug("✅ Menu principal encontrado")
        except Exception as e:
            logging.error(f"❌ Menu principal não encontrado: {e}")
            return False
        
        # Etapa 2: Fazer hover no menu discente
        logging.debug("🖱️  Fazendo hover no menu discente")
        try:
            page.locator("#menu_form_menu_discente_discente_menu").hover()
            logging.debug("✅ Hover realizado com sucesso")
            time.sleep(0.5)  # Aguardar expansão do menu
        except Exception as e:
            logging.error(f"❌ Falha no hover do menu: {e}")
            return False
        
        # Etapa 3: Clicar em "Ensino"
        logging.debug("📚 Clicando na opção 'Ensino'")
        try:
            page.locator('span.ThemeOfficeMainFolderText:has-text("Ensino")').click(
                timeout=5000
            )
            logging.debug("✅ Seção 'Ensino' aberta")
            time.sleep(0.5)  # Aguardar expansão do submenu
        except Exception as e:
            logging.error(f"❌ Falha ao clicar em 'Ensino': {e}")
            return False
        
        # Etapa 4: Clicar em "Consultar Minhas Notas"
        logging.debug("📊 Clicando em 'Consultar Minhas Notas'")
        try:
            page.locator(
                'td.ThemeOfficeMenuItemText:has-text("Consultar Minhas Notas")'
            ).first.click(timeout=10000)
            logging.debug("✅ Opção 'Consultar Minhas Notas' clicada")
        except Exception as e:
            logging.error(f"❌ Falha ao clicar em 'Consultar Minhas Notas': {e}")
            return False
        
        # Etapa 5: Aguardar carregamento da tabela de notas
        logging.debug("⏳ Aguardando carregamento da tabela de notas")
        try:
            page.wait_for_selector("table.tabelaRelatorio", timeout=config.TIMEOUT_DEFAULT)
            logging.debug("✅ Tabela de notas carregada")
        except Exception as e:
            logging.error(f"❌ Tabela de notas não carregou: {e}")
            return False
        
        # Verificação adicional: contar tabelas encontradas
        try:
            tables = page.locator("table.tabelaRelatorio")
            table_count = tables.count()
            logging.info(f"📊 Encontradas {table_count} tabela(s) de notas")
            
            if table_count == 0:
                logging.warning("⚠️  Nenhuma tabela de notas encontrada")
                return False
            
        except Exception as e:
            logging.warning(f"⚠️  Erro ao verificar tabelas: {e}")
            return False
        
        logging.info("✅ Navegação para seção de notas via menu concluída com sucesso!")
        return True
        
    except Exception as e:
        logging.error(
            f"Erro geral na navegação via menu: {e}",
            exc_info=True,
            extra={"details": "module=navigate_via_menu"}
        )
        return False


def extract_grades_from_menu_page(page: Page) -> Dict[str, Any]:
    """
    Extrai as notas da página de Consultar Minhas Notas.
    
    Args:
        page: Página do navegador.
        
    Returns:
        dict: Dicionário contendo as notas extraídas.
    """
    try:
        logging.info("📊 Iniciando extração de notas da página menu")
        grades = {}
        
        # Aguardar carregamento completo das tabelas
        page.wait_for_selector("table.tabelaRelatorio", timeout=config.TIMEOUT_DEFAULT)
        
        # Encontrar todas as tabelas de notas
        tables = page.locator("table.tabelaRelatorio")
        table_count = tables.count()
        
        logging.info(f"Processando {table_count} tabela(s) de notas")
        
        for i in range(table_count):
            try:
                table = tables.nth(i)
                
                # Extrair cabeçalho da tabela (nome da disciplina/período)
                # Procurar por cabeçalho antes da tabela
                preceding_headers = page.locator(f"table.tabelaRelatorio:nth-child({i+1})").locator("xpath=preceding-sibling::*[self::h3 or self::h2 or self::div[contains(@class,'cabecalho')]]")
                
                table_name = f"Disciplinas_Periodo_{i+1}"
                if preceding_headers.count() > 0:
                    header_text = preceding_headers.last.text_content()
                    if header_text:
                        table_name = header_text.strip()
                
                # Extrair linhas da tabela
                rows = table.locator("tr")
                row_count = rows.count()
                
                if row_count > 1:  # Pelo menos cabeçalho + 1 linha de dados
                    table_data = []
                    
                    # Processar cabeçalho
                    header_row = rows.nth(0)
                    headers = []
                    header_cells = header_row.locator("th, td")
                    for j in range(header_cells.count()):
                        header_text = header_cells.nth(j).text_content()
                        headers.append(header_text.strip() if header_text else f"Coluna_{j+1}")
                    
                    # Processar linhas de dados
                    for row_idx in range(1, row_count):
                        row = rows.nth(row_idx)
                        cells = row.locator("td")
                        
                        if cells.count() > 0:
                            row_data = {}
                            for cell_idx in range(cells.count()):
                                cell_text = cells.nth(cell_idx).text_content()
                                cell_value = cell_text.strip() if cell_text else ""
                                header_key = headers[cell_idx] if cell_idx < len(headers) else f"Coluna_{cell_idx+1}"
                                row_data[header_key] = cell_value
                            
                            if row_data:  # Só adicionar se tiver dados
                                table_data.append(row_data)
                    
                    if table_data:
                        grades[table_name] = table_data
                        logging.info(f"Extraídas {len(table_data)} linhas da tabela: {table_name}")
                
            except Exception as e:
                logging.warning(f"Erro ao processar tabela {i+1}: {e}")
                continue
        
        logging.info(f"✅ Extração concluída: {len(grades)} conjunto(s) de notas extraídos")
        return grades
        
    except Exception as e:
        logging.error(
            f"Erro na extração de notas via menu: {e}",
            exc_info=True,
            extra={"details": "module=extract_grades_from_menu_page"}
        )
        return {}
