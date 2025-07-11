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
        
        # Otimização: campos de interesse definidos como constante de classe
        GRADE_FIELDS = (
            "Unidade 1", "Unidade 2", "Unidade 3", "Unidade 4", "Unidade 5",
            "Unidade 6", "Unidade 7", "Unidade 8", "Unidade 9", 
            "Recuperação", "Resultado"
        )

        # Normaliza notas em dicionários para comparação
        old_dict = self._normalize_grades_for_comparison(old_grades)
        new_dict = self._normalize_grades_for_comparison(new_grades)

        # Otimização: itera apenas sobre novas notas para detectar mudanças
        for key, new_grade in new_dict.items():
            old_grade = old_dict.get(key, {})
            
            # Otimização: verifica campos em uma única iteração
            for field in GRADE_FIELDS:
                old_value = old_grade.get(field, "")
                new_value = new_grade.get(field, "")
                
                # Otimização: condição mais específica para reduzir comparações desnecessárias
                if new_value and new_value != old_value and new_value.strip():
                    change_description = (
                        f"Alteração em {new_grade['Disciplina']} "
                        f"({new_grade['Código']}) - Semestre {new_grade['Semestre']}: "
                        f"{field} mudou de '{old_value}' para '{new_value}'"
                    )
                    changes.append(change_description)

        # Otimização: log em batch para reduzir I/O
        if changes:
            logging.info(f"Detectadas {len(changes)} mudanças")
            # Log detalhado apenas em debug para não sobrecarregar
            if logging.getLogger().isEnabledFor(logging.DEBUG):
                for change in changes:
                    logging.debug(change)
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
        if not isinstance(grades, dict):
            return {}
        
        # Otimização: dictionary comprehension para melhor performance
        normalized = {}
        
        for semester, grade_list in grades.items():
            if isinstance(grade_list, list):
                for grade in grade_list:
                    # Otimização: verifica se é um dicionário válido de uma vez
                    if (isinstance(grade, dict) and 
                        'Semestre' in grade and 
                        'Código' in grade and
                        grade['Semestre'] and 
                        grade['Código']):
                        
                        key = f"{grade['Semestre']}-{grade['Código']}"
                        normalized[key] = grade
                        
        return normalized
