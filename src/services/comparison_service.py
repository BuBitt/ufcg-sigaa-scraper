"""
Serviço de comparação de notas para detectar mudanças.
"""

from typing import Dict, Any, List, Set
import json

from src.utils.logger import get_logger


class ComparisonService:
    """Compara notas para detectar mudanças."""
    
    def __init__(self) -> None:
        """Inicializa o serviço de comparação."""
        self.logger = get_logger("comparison")
        self.logger.debug("🔧 Serviço de comparação inicializado")
    
    def compare_grades(self, old_grades: Dict[str, Any], new_grades: Dict[str, Any]) -> List[str]:
        """
        Compara notas antigas com novas e detecta mudanças.
        
        Args:
            old_grades: Notas antigas do cache
            new_grades: Novas notas extraídas
            
        Returns:
            List[str]: Lista de mudanças detectadas
        """
        try:
            self.logger.info("🔍 Iniciando comparação de notas")
            
            changes = []
            
            # Se não há notas antigas, tudo é novo
            if not old_grades:
                self.logger.info("📝 Primeira execução - todas as notas são novas")
                changes.extend(self._format_all_as_new(new_grades))
                return changes
            
            # Normalizar estruturas para comparação
            old_normalized = self._normalize_grades_structure(old_grades)
            new_normalized = self._normalize_grades_structure(new_grades)
            
            # Comparar cada período/disciplina
            all_keys = set(old_normalized.keys()) | set(new_normalized.keys())
            
            for key in all_keys:
                old_data = old_normalized.get(key, [])
                new_data = new_normalized.get(key, [])
                
                key_changes = self._compare_grade_section(key, old_data, new_data)
                changes.extend(key_changes)
            
            self.logger.info(f"🔍 Comparação concluída: {len(changes)} mudança(s) detectada(s)")
            return changes
            
        except Exception as e:
            self.logger.error(f"❌ Erro na comparação de notas: {e}", exc_info=True)
            return []
    
    def _normalize_grades_structure(self, grades: Any) -> Dict[str, List[Dict[str, Any]]]:
        """
        Normaliza estrutura de notas para comparação consistente.
        
        Args:
            grades: Estrutura de notas em qualquer formato
            
        Returns:
            Dict: Estrutura normalizada
        """
        try:
            # Se é lista, converter para dict
            if isinstance(grades, list):
                normalized = {}
                for i, item in enumerate(grades):
                    if isinstance(item, dict):
                        # Tentar identificar chave (disciplina, período, etc)
                        key = self._extract_key_from_record(item, i)
                        if key not in normalized:
                            normalized[key] = []
                        normalized[key].append(item)
                    else:
                        normalized[f"Item_{i}"] = [{"value": str(item)}]
                return normalized
            
            # Se é dict, verificar estrutura
            elif isinstance(grades, dict):
                normalized = {}
                for key, value in grades.items():
                    if isinstance(value, list):
                        normalized[key] = value
                    elif isinstance(value, dict):
                        normalized[key] = [value]
                    else:
                        normalized[key] = [{"value": str(value)}]
                return normalized
            
            else:
                # Tipo não reconhecido
                return {"Dados_Desconhecidos": [{"value": str(grades)}]}
                
        except Exception as e:
            self.logger.warning(f"⚠️  Erro na normalização: {e}")
            return {}
    
    def _extract_key_from_record(self, record: Dict[str, Any], index: int) -> str:
        """
        Extrai chave identificadora de um registro.
        
        Args:
            record: Registro de nota
            index: Índice do registro
            
        Returns:
            str: Chave identificadora
        """
        # Procurar campos que identifiquem a disciplina/período
        key_fields = [
            '_disciplina', 'Disciplina', 'Componente', 'Matéria',
            'Nome', 'Código', 'Período', 'Semestre'
        ]
        
        for field in key_fields:
            if field in record and record[field]:
                return str(record[field]).strip()
        
        # Fallback para índice
        return f"Registro_{index + 1}"
    
    def _compare_grade_section(self, section_key: str, old_data: List[Dict[str, Any]], 
                              new_data: List[Dict[str, Any]]) -> List[str]:
        """
        Compara uma seção específica de notas.
        
        Args:
            section_key: Chave da seção (disciplina, período, etc)
            old_data: Dados antigos da seção
            new_data: Dados novos da seção
            
        Returns:
            List[str]: Mudanças detectadas na seção
        """
        changes = []
        
        try:
            # Seção completamente nova
            if not old_data and new_data:
                changes.append(f"Nova seção adicionada: {section_key}")
                return changes
            
            # Seção removida
            if old_data and not new_data:
                changes.append(f"Seção removida: {section_key}")
                return changes
            
            # Comparar registros dentro da seção
            old_records = {self._create_record_signature(record): record for record in old_data}
            new_records = {self._create_record_signature(record): record for record in new_data}
            
            # Registros novos
            for signature, record in new_records.items():
                if signature not in old_records:
                    change_desc = self._describe_new_record(section_key, record)
                    changes.append(change_desc)
            
            # Registros modificados
            for signature, new_record in new_records.items():
                if signature in old_records:
                    old_record = old_records[signature]
                    record_changes = self._compare_records(old_record, new_record)
                    if record_changes:
                        change_desc = f"{section_key}: {record_changes}"
                        changes.append(change_desc)
            
            # Registros removidos
            for signature, record in old_records.items():
                if signature not in new_records:
                    change_desc = f"{section_key}: Registro removido"
                    changes.append(change_desc)
            
        except Exception as e:
            self.logger.warning(f"⚠️  Erro ao comparar seção {section_key}: {e}")
        
        return changes
    
    def _create_record_signature(self, record: Dict[str, Any]) -> str:
        """
        Cria assinatura única para um registro.
        
        Args:
            record: Registro de nota
            
        Returns:
            str: Assinatura do registro
        """
        try:
            # Usar campos mais estáveis como identificadores
            identifier_fields = [
                'Disciplina', 'Componente', 'Código', 'Nome',
                '_disciplina', 'Matéria'
            ]
            
            identifiers = []
            for field in identifier_fields:
                if field in record and record[field]:
                    identifiers.append(str(record[field]).strip())
            
            if identifiers:
                return "_".join(identifiers)
            
            # Fallback: usar hash do registro (excluindo campos voláteis)
            stable_record = {k: v for k, v in record.items() 
                           if not k.startswith('_') and k not in ['Data', 'Hora']}
            return str(hash(json.dumps(stable_record, sort_keys=True)))
            
        except Exception:
            # Último fallback
            return str(hash(str(record)))
    
    def _compare_records(self, old_record: Dict[str, Any], new_record: Dict[str, Any]) -> str:
        """
        Compara dois registros e retorna descrição das mudanças.
        
        Args:
            old_record: Registro antigo
            new_record: Registro novo
            
        Returns:
            str: Descrição das mudanças ou string vazia se não há mudanças
        """
        try:
            changes = []
            
            # Campos que indicam notas/valores importantes
            important_fields = [
                'Nota', 'Média', 'Resultado', 'Conceito',
                'Nota Final', 'Media Final', '_nota_extraida'
            ]
            
            # Verificar mudanças em campos importantes
            all_fields = set(old_record.keys()) | set(new_record.keys())
            
            # Adicionar campos de unidades dinamicamente
            for field in all_fields:
                if field.startswith('Unidade.') or field == 'Final':
                    important_fields.append(field)
            
            for field in all_fields:
                old_value = old_record.get(field, "")
                new_value = new_record.get(field, "")
                
                if old_value != new_value:
                    if field in important_fields:
                        changes.append(f"{field}: {old_value} → {new_value}")
                    elif not field.startswith('_'):  # Ignorar campos de metadados
                        changes.append(f"{field} alterado")
            
            return "; ".join(changes)
            
        except Exception:
            return "Registro modificado"
    
    def _describe_new_record(self, section_key: str, record: Dict[str, Any]) -> str:
        """
        Cria descrição de um novo registro.
        
        Args:
            section_key: Chave da seção
            record: Novo registro
            
        Returns:
            str: Descrição do novo registro
        """
        try:
            # Procurar por campos de nota principais
            grade_fields = ['Resultado', 'Nota', 'Média']
            for field in grade_fields:
                if field in record and record[field] and record[field] != "--" and record[field].strip():
                    return f"{section_key}: {field} {record[field]}"
            
            # Se não encontrou resultado, procurar por unidades com notas
            unit_notes = []
            for field, value in record.items():
                if field.startswith('Unidade.') and value and value.strip() and value != "--":
                    unit_notes.append(f"{field}: {value}")
            
            if unit_notes:
                # Mostrar apenas as primeiras unidades para não ficar muito longo
                units_text = "; ".join(unit_notes[:2])
                if len(unit_notes) > 2:
                    units_text += f" (+ {len(unit_notes) - 2} mais)"
                return f"{section_key}: {units_text}"
            
            # Tentar extrair nota do campo especial
            grade_value = record.get('_nota_extraida')
            if grade_value is not None and str(grade_value).strip() and str(grade_value) != "0":
                return f"{section_key}: Nova nota {grade_value}"
            
            return f"{section_key}: Novo registro adicionado"
            
        except Exception:
            return f"{section_key}: Novo registro"
    
    def _format_all_as_new(self, grades: Dict[str, Any]) -> List[str]:
        """
        Formata todas as notas como novas (primeira execução).
        
        Args:
            grades: Estrutura de notas
            
        Returns:
            List[str]: Lista de mudanças
        """
        try:
            changes = []
            normalized = self._normalize_grades_structure(grades)
            
            for section_key, records in normalized.items():
                for record in records:
                    change_desc = self._describe_new_record(section_key, record)
                    changes.append(change_desc)
            
            return changes
            
        except Exception as e:
            self.logger.warning(f"⚠️  Erro ao formatar como novos: {e}")
            return ["Novas notas detectadas"]
