"""
Serviço para extração de notas do SIGAA.
"""

import logging
from typing import Dict, List, Any

from bs4 import BeautifulSoup, FeatureNotFound


class GradeExtractor:
    """Responsável pela extração e processamento das notas do HTML."""
    
    def extract_grades(self, html_content: str) -> List[Dict[str, str]]:
        """
        Extrai notas do conteúdo HTML usando BeautifulSoup.
        
        Args:
            html_content: Conteúdo HTML bruto da página de notas
            
        Returns:
            Lista de dicionários contendo informações das notas
        """
        try:
            soup = BeautifulSoup(html_content, "lxml")
        except FeatureNotFound:
            logging.warning("Parser lxml não encontrado, usando html.parser (mais lento)")
            soup = BeautifulSoup(html_content, "html.parser")

        grades = []
        # Usa find_all retornando Tag objects que têm os métodos necessários
        for table in soup.find_all("table", class_="tabelaRelatorio"):
            # table é do tipo Tag, que tem os métodos necessários
            semester = "Semestre Desconhecido"
            caption = getattr(table, 'caption', None)  # type: ignore
            if caption:
                semester = caption.text.strip()  # type: ignore
            
            tbody = table.find("tbody")  # type: ignore
            if not tbody:
                continue
                
            # Busca linhas que contêm a palavra "linha" na classe
            for row in tbody.find_all("tr"):  # type: ignore
                class_attr = row.get("class")  # type: ignore
                if class_attr and any("linha" in str(cls) for cls in class_attr):
                    cols = [col.text.strip() for col in row.find_all("td")]  # type: ignore
                    if len(cols) >= 2:
                        # Garante que temos colunas suficientes
                        cols += [""] * (15 - len(cols))
                        grades.append(self._create_grade_record(semester, cols))

        if not grades:
            logging.warning("Nenhuma nota encontrada no conteúdo HTML")
        else:
            logging.info(f"Extraídos {len(grades)} registros de notas")
            
        return grades
    
    def _create_grade_record(self, semester: str, cols: List[str]) -> Dict[str, str]:
        """
        Cria um registro de nota padronizado a partir das colunas da tabela.
        
        Args:
            semester: Nome do semestre
            cols: Lista de valores das colunas da linha da tabela
            
        Returns:
            Dicionário com informações padronizadas da nota
        """
        # Otimização: função helper para normalizar valores
        def normalize_value(value: str) -> str:
            return "" if value == "--" else value
        
        return {
            "Semestre": semester,
            "Código": cols[0],
            "Disciplina": cols[1],
            "Unidade 1": normalize_value(cols[2]),
            "Unidade 2": normalize_value(cols[3]),
            "Unidade 3": normalize_value(cols[4]),
            "Unidade 4": normalize_value(cols[5]),
            "Unidade 5": normalize_value(cols[6]),
            "Unidade 6": normalize_value(cols[7]),
            "Unidade 7": normalize_value(cols[8]),
            "Unidade 8": normalize_value(cols[9]),
            "Unidade 9": normalize_value(cols[10]),
            "Recuperação": normalize_value(cols[11]),
            "Resultado": normalize_value(cols[12]),
            "Faltas": cols[13],
            "Situação": cols[14],
        }
    
    def organize_grades_by_semester(self, grades: List[Dict[str, str]]) -> Dict[str, List[Dict[str, str]]]:
        """
        Organiza a lista de notas por semestre.
        
        Args:
            grades: Lista de registros de notas
            
        Returns:
            Dicionário com notas organizadas por semestre
        """
        organized = {}
        for grade in grades:
            semester = grade["Semestre"]
            organized.setdefault(semester, []).append(grade)
        return organized
