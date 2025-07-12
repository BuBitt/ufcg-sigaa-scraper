"""
Extrator de notas do SIGAA com suporte a múltiplos métodos.
"""

import re
from datetime import datetime
from typing import Dict, Any, List

from playwright.sync_api import Page
from bs4 import BeautifulSoup

from src.config.settings import Config
from src.utils.logger import get_logger


class GradeExtractor:
    """Extrai notas das páginas do SIGAA."""
    
    def __init__(self) -> None:
        """Inicializa o extrator de notas."""
        self.logger = get_logger("grade_extractor")
        self.logger.debug("🔧 Extrator de notas inicializado")
    
    def extract_from_page_direct(self, page: Page) -> Dict[str, Any]:
        """
        Extrai notas diretamente da página usando Playwright.
        
        Args:
            page: Página do navegador
            
        Returns:
            Dict[str, Any]: Notas extraídas organizadas
        """
        try:
            self.logger.info("📊 Extraindo notas da página atual")
            
            # Obter conteúdo HTML
            content = page.content()
            
            # Extrair usando BeautifulSoup
            grades = self.extract_grades(content)
            
            # Organizar por semestre/período
            organized = self.organize_grades_by_semester(grades)
            
            self.logger.info(f"✅ Extração concluída: {len(grades)} registro(s)")
            return organized
            
        except Exception as e:
            self.logger.error(f"❌ Erro na extração direta: {e}", exc_info=True)
            return {}
    
    def extract_grades(self, page_content: str) -> List[Dict[str, Any]]:
        """
        Extrai notas do conteúdo HTML da página.
        
        Args:
            page_content: Conteúdo HTML da página
            
        Returns:
            List[Dict[str, Any]]: Lista de registros de notas extraídos
        """
        try:
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
            
            self.logger.info(f"📊 Total de registros extraídos: {len(all_grades)}")
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
            List[Dict[str, Any]]: Registros da tabela
        """
        grades = []
        
        try:
            # Extrair cabeçalho
            header_row = table.find('tr')
            if not header_row:
                return grades
            
            headers = []
            for th in header_row.find_all(['th', 'td']):
                text = th.get_text(strip=True)
                headers.append(text if text else f"Coluna_{len(headers)+1}")
            
            # Extrair linhas de dados
            rows = table.find_all('tr')[1:]  # Pular cabeçalho
            
            for row_index, row in enumerate(rows):
                try:
                    cells = row.find_all(['td', 'th'])
                    if len(cells) == 0:
                        continue
                    
                    record = {
                        '_tabela_index': table_index,
                        '_linha_index': row_index,
                        '_timestamp': datetime.now().isoformat()
                    }
                    
                    # Extrair dados das células
                    for cell_index, cell in enumerate(cells):
                        header = headers[cell_index] if cell_index < len(headers) else f"Coluna_{cell_index+1}"
                        cell_text = cell.get_text(strip=True)
                        
                        record[header] = cell_text
                        
                        # Tentar extrair nota numérica
                        if self._looks_like_grade(cell_text):
                            record['_nota_extraida'] = self._normalize_grade(cell_text)
                    
                    # Identificar disciplina
                    discipline = self._identify_discipline(record)
                    if discipline:
                        record['_disciplina'] = discipline
                    
                    grades.append(record)
                    
                except Exception as e:
                    self.logger.warning(f"⚠️  Erro ao processar linha {row_index+1}: {e}")
                    continue
            
            self.logger.debug(f"✅ Tabela {table_index+1}: {len(grades)} registro(s) extraídos")
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao extrair tabela {table_index+1}: {e}")
        
        return grades
    
    def _looks_like_grade(self, text: str) -> bool:
        """
        Verifica se o texto parece uma nota.
        
        Args:
            text: Texto a verificar
            
        Returns:
            bool: True se parece uma nota
        """
        if not text:
            return False
        
        # Padrões de nota
        grade_patterns = [
            r'^\d+[.,]?\d*$',  # 10, 10.0, 10,5
            r'^\d+[.,]\d+$',   # 10.5, 10,5
            r'^[0-9]+$'        # 10
        ]
        
        for pattern in grade_patterns:
            if re.match(pattern, text.strip()):
                return True
        
        return False
    
    def _normalize_grade(self, text: str) -> str:
        """
        Normaliza formato de nota.
        
        Args:
            text: Texto da nota
            
        Returns:
            str: Nota normalizada
        """
        return text.strip().replace(',', '.')
    
    def _identify_discipline(self, record: Dict[str, Any]) -> str:
        """
        Identifica o nome da disciplina no registro.
        
        Args:
            record: Registro de dados
            
        Returns:
            str: Nome da disciplina ou string vazia
        """
        # Campos que podem conter nome da disciplina
        discipline_fields = [
            'Disciplina', 'Componente Curricular', 'Nome',
            'Componente', 'Matéria', 'Código'
        ]
        
        for field in discipline_fields:
            if field in record and record[field]:
                return str(record[field]).strip()
        
        # Procurar por texto mais longo (provavelmente disciplina)
        longest_text = ""
        for key, value in record.items():
            if not key.startswith('_') and isinstance(value, str):
                if len(value.strip()) > len(longest_text) and len(value.strip()) > 10:
                    longest_text = value.strip()
        
        return longest_text
    
    def organize_grades_by_semester(self, grades: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Organiza notas por semestre/período.
        
        Args:
            grades: Lista de notas
            
        Returns:
            Dict: Notas organizadas por período
        """
        try:
            organized = {}
            
            for grade in grades:
                # Tentar identificar período/semestre
                period = self._identify_period(grade)
                
                if period not in organized:
                    organized[period] = []
                
                organized[period].append(grade)
            
            self.logger.info(f"📅 Notas organizadas em {len(organized)} período(s)")
            return organized
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao organizar por semestre: {e}")
            return {"Periodo_Unico": grades}
    
    def _identify_period(self, grade: Dict[str, Any]) -> str:
        """
        Identifica o período/semestre de uma nota.
        
        Args:
            grade: Registro de nota
            
        Returns:
            str: Nome do período
        """
        # Procurar campos que indiquem período
        period_fields = ['Período', 'Semestre', 'Ano', 'Turma']
        
        for field in period_fields:
            if field in grade and grade[field]:
                return f"{field}_{grade[field]}"
        
        # Usar disciplina como agrupador
        if '_disciplina' in grade and grade['_disciplina']:
            return grade['_disciplina']
        
        # Fallback para tabela
        table_index = grade.get('_tabela_index', 0)
        return f"Tabela_{table_index + 1}"
