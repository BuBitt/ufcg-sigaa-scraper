"""
Serviço de comparação de notas para detectar mudanças.
"""

import logging
from typing import Dict, List


class ComparisonService:
    """Responsável por comparar notas e detectar mudanças."""
    
    def compare_grades(
        self, 
        old_grades: Dict[str, List[Dict[str, str]]], 
        new_grades: Dict[str, List[Dict[str, str]]]
    ) -> List[str]:
        """
        Compara notas antigas e novas para detectar mudanças.
        
        Args:
            old_grades: Notas previamente armazenadas em cache
            new_grades: Notas recém-extraídas
            
        Returns:
            Lista de descrições de mudanças
        """
        changes = []
        grade_fields = [
            f"Unidade {i}" for i in range(1, 10)
        ] + ["Recuperação", "Resultado"]

        # Normaliza notas em dicionários para comparação
        old_dict = self._normalize_grades_for_comparison(old_grades)
        new_dict = self._normalize_grades_for_comparison(new_grades)

        for key, new_grade in new_dict.items():
            old_grade = old_dict.get(key, {})
            for field in grade_fields:
                old_value = old_grade.get(field, "")
                new_value = new_grade.get(field, "")
                
                if new_value and new_value != old_value:
                    change_description = (
                        f"Alteração em {new_grade['Disciplina']} "
                        f"({new_grade['Código']}) - Semestre {new_grade['Semestre']}: "
                        f"{field} mudou de '{old_value}' para '{new_value}'"
                    )
                    changes.append(change_description)

        if changes:
            logging.info(f"Detectadas {len(changes)} mudanças")
            for change in changes:
                logging.info(change)
        else:
            logging.info("Nenhuma mudança detectada")
            
        return changes

    def _normalize_grades_for_comparison(
        self, 
        grades: Dict[str, List[Dict[str, str]]]
    ) -> Dict[str, Dict[str, str]]:
        """
        Normaliza dicionário de notas para comparação eficiente.
        
        Args:
            grades: Notas organizadas por semestre
            
        Returns:
            Dicionário achatado com chaves únicas para cada registro de nota
        """
        normalized = {}
        if not isinstance(grades, dict):
            return normalized
            
        for semester, grade_list in grades.items():
            if isinstance(grade_list, list):
                for grade in grade_list:
                    if isinstance(grade, dict) and all(
                        key in grade for key in ['Semestre', 'Código']
                    ):
                        key = f"{grade['Semestre']}-{grade['Código']}"
                        normalized[key] = grade
                        
        return normalized
