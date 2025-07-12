"""
Extrator de notas do SIGAA com suporte a múltiplos métodos.
"""

import re
from typing import Dict, Any, List

from playwright.sync_api import Page

from src.config.settings import Config
from src.utils.logger import get_logger


class GradeExtractor:
    """Extrai notas das páginas do SIGAA."""
    
    def __init__(self) -> None:
        """Inicializa o extrator de notas."""
        self.logger = get_logger("grade_extractor")
        self.logger.debug("🔧 Extrator de notas inicializado")
    
    def extract_grades(self, page_content: str) -> List[Dict[str, Any]]:
        """
        Extrai notas do conteúdo HTML da página.
        
        Args:
            page_content: Conteúdo HTML da página
            
        Returns:
            List[Dict[str, Any]]: Lista de registros de notas extraídos
        """
        try:
            from bs4 import BeautifulSoup
            
            self.logger.info("📊 Iniciando extração de notas do HTML")
            soup = BeautifulSoup(page_content, 'html.parser')
            
            # Encontrar todas as tabelas de notas
            tables = soup.find_all('table', class_='tabelaRelatorio')
            all_grades = []
            
            self.logger.info(f"🔍 Encontradas {len(tables)} tabela(s) para processamento")
            
            for i, table in enumerate(tables):
                try:
                    table_grades = self._extract_table_grades(table, i)
                    all_grades.extend(table_grades)
                except Exception as e:
                    self.logger.warning(f"⚠️  Erro ao processar tabela {i+1}: {e}")
                    continue
            
            self.logger.info(f"✅ Extração concluída: {len(all_grades)} registro(s) de notas")
            return all_grades
            
        except Exception as e:
            self.logger.error(f"❌ Erro na extração de notas: {e}", exc_info=True)
            return []
    
    def _extract_table_grades(self, table, table_index: int) -> List[Dict[str, Any]]:
        """
        Extrai notas de uma tabela específica.
        
        Args:
            table: Elemento table do BeautifulSoup
            table_index: Índice da tabela
            
        Returns:
            List[Dict[str, Any]]: Lista de registros da tabela
        """
        grades = []
        
        try:
            # Encontrar cabeçalho da tabela
            headers = []
            header_row = table.find('tr')
            if header_row:
                header_cells = header_row.find_all(['th', 'td'])
                for cell in header_cells:
                    header_text = cell.get_text(strip=True)
                    headers.append(header_text if header_text else f"Coluna_{len(headers)+1}")
            
            if not headers:
                self.logger.warning(f"⚠️  Nenhum cabeçalho encontrado na tabela {table_index+1}")
                return grades
            
            # Processar linhas de dados
            rows = table.find_all('tr')[1:]  # Pular cabeçalho
            
            for row_index, row in enumerate(rows):
                try:
                    cells = row.find_all(['td', 'th'])
                    if len(cells) == 0:
                        continue
                    
                    row_data = {}
                    for cell_index, cell in enumerate(cells):
                        cell_text = cell.get_text(strip=True)
                        
                        # Determinar nome da coluna
                        if cell_index < len(headers):
                            column_name = headers[cell_index]
                        else:
                            column_name = f"Coluna_{cell_index+1}"
                        
                        row_data[column_name] = cell_text
                    
                    # Adicionar metadados
                    row_data['_tabela_index'] = table_index
                    row_data['_linha_index'] = row_index
                    
                    # Tentar identificar disciplina/componente
                    discipline = self._identify_discipline(row_data)
                    if discipline:
                        row_data['_disciplina'] = discipline
                    
                    # Tentar extrair nota
                    grade = self._extract_grade_value(row_data)
                    if grade is not None:
                        row_data['_nota_extraida'] = grade
                    
                    if row_data:  # Só adicionar se tiver dados
                        grades.append(row_data)
                        
                except Exception as e:
                    self.logger.warning(f"⚠️  Erro ao processar linha {row_index+1}: {e}")
                    continue
            
            self.logger.debug(f"📊 Tabela {table_index+1}: {len(grades)} registro(s) extraídos")
            return grades
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao extrair tabela {table_index+1}: {e}")
            return []
    
    def _identify_discipline(self, row_data: Dict[str, Any]) -> str:
        """
        Tenta identificar o nome da disciplina nos dados da linha.
        
        Args:
            row_data: Dados da linha
            
        Returns:
            str: Nome da disciplina identificada ou string vazia
        """
        # Procurar em campos que comumente contêm o nome da disciplina
        discipline_fields = [
            'Disciplina', 'Componente', 'Matéria', 'Nome',
            'Disciplina/Componente', 'Código - Nome'
        ]
        
        for field in discipline_fields:
            if field in row_data and row_data[field]:
                value = str(row_data[field]).strip()
                if len(value) > 3:  # Nome mínimo razoável
                    return value
        
        # Procurar em qualquer campo que tenha texto longo
        for key, value in row_data.items():
            if isinstance(value, str) and len(value) > 10:
                # Verificar se parece ser nome de disciplina
                if any(word in value.upper() for word in ['CÁLCULO', 'FÍSICA', 'QUÍMICA', 'HISTÓRIA', 'PROGRAMAÇÃO', 'ENGENHARIA']):
                    return value.strip()
        
        return ""
    
    def _extract_grade_value(self, row_data: Dict[str, Any]) -> float:
        """
        Tenta extrair valor numérico de nota dos dados da linha.
        
        Args:
            row_data: Dados da linha
            
        Returns:
            float or None: Valor da nota ou None se não encontrada
        """
        # Campos que comumente contêm notas
        grade_fields = [
            'Nota', 'Média', 'Resultado', 'Conceito',
            'Nota Final', 'Media Final', 'Avaliação'
        ]
        
        for field in grade_fields:
            if field in row_data and row_data[field]:
                grade = self._parse_grade_value(str(row_data[field]))
                if grade is not None:
                    return grade
        
        # Procurar em todos os campos por valores numéricos
        for key, value in row_data.items():
            if isinstance(value, str):
                grade = self._parse_grade_value(value)
                if grade is not None and 0 <= grade <= 10:  # Range típico de notas
                    return grade
        
        return None
    
    def _parse_grade_value(self, text: str) -> float:
        """
        Tenta extrair valor numérico de uma string.
        
        Args:
            text: Texto a ser analisado
            
        Returns:
            float or None: Valor numérico ou None se não encontrado
        """
        try:
            # Limpar texto
            text = text.strip().replace(',', '.')
            
            # Procurar por padrão numérico
            match = re.search(r'\d+\.?\d*', text)
            if match:
                value = float(match.group())
                return value
                
        except (ValueError, AttributeError):
            pass
        
        return None
    
    def organize_grades_by_semester(self, grades: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Organiza as notas por semestre/período.
        
        Args:
            grades: Lista de registros de notas
            
        Returns:
            Dict: Notas organizadas por período
        """
        organized = {}
        
        try:
            for grade in grades:
                # Tentar identificar período/semestre
                semester = self._identify_semester(grade)
                
                if semester not in organized:
                    organized[semester] = []
                
                organized[semester].append(grade)
            
            self.logger.info(f"📚 Notas organizadas em {len(organized)} período(s)")
            return organized
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao organizar notas por semestre: {e}")
            return {"Período_Único": grades}
    
    def _identify_semester(self, grade_data: Dict[str, Any]) -> str:
        """
        Tenta identificar o semestre/período de um registro de nota.
        
        Args:
            grade_data: Dados do registro de nota
            
        Returns:
            str: Identificação do período
        """
        # Procurar campos que indiquem período
        period_fields = ['Período', 'Semestre', 'Ano', 'Turma']
        
        for field in period_fields:
            if field in grade_data and grade_data[field]:
                return str(grade_data[field]).strip()
        
        # Usar índice da tabela como fallback
        table_index = grade_data.get('_tabela_index', 0)
        return f"Período_{table_index + 1}"
    
    def extract_from_page_direct(self, page: Page) -> Dict[str, Any]:
        """
        Extrai notas diretamente da página atual.
        
        Args:
            page: Página do navegador
            
        Returns:
            Dict: Notas extraídas organizadas
        """
        try:
            self.logger.info("📊 Extraindo notas da página atual")
            
            # Aguardar carregamento das tabelas
            page.wait_for_selector("table.tabelaRelatorio", timeout=Config.TIMEOUT_DEFAULT)
            
            # Obter conteúdo da página
            content = page.content()
            
            # Extrair notas
            grades = self.extract_grades(content)
            
            # Organizar por semestre
            organized_grades = self.organize_grades_by_semester(grades)
            
            self.logger.info(f"✅ Extração direta concluída: {len(organized_grades)} período(s)")
            return organized_grades
            
        except Exception as e:
            self.logger.error(f"❌ Erro na extração direta: {e}", exc_info=True)
            return {}
