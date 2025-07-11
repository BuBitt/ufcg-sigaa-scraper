#!/usr/bin/env python3
"""
Conversor de grades_cache.json para CSV
Converte os dados de notas armazenados em JSON para formato CSV para análise externa.
"""

import json
import csv
import os
import sys
from datetime import datetime
from typing import Dict, List, Any

# Adicionar o diretório raiz ao path para imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

try:
    from src.utils.logger import get_logger
except ImportError:
    # Fallback para logging básico se não conseguir importar
    import logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    def get_logger(name):
        return logging.getLogger(name)

class GradesToCSVConverter:
    """Conversor de dados de notas do JSON para CSV"""
    
    def __init__(self):
        self.logger = get_logger('csv_converter')
        self.cache_file = "grades_cache.json"
        self.csv_file = "grades_export.csv"
    
    def load_grades_data(self) -> Dict[str, Any]:
        """Carrega dados do arquivo de cache JSON"""
        try:
            if not os.path.exists(self.cache_file):
                self.logger.error(f"❌ Arquivo {self.cache_file} não encontrado")
                return {}
            
            with open(self.cache_file, 'r', encoding='utf-8') as file:
                data = json.load(file)
                self.logger.info(f"📊 Dados carregados de {self.cache_file}")
                return data
                
        except json.JSONDecodeError as e:
            self.logger.error(f"❌ Erro ao decodificar JSON: {e}")
            return {}
        except Exception as e:
            self.logger.error(f"❌ Erro ao carregar dados: {e}")
            return {}
    
    def convert_to_csv(self, output_file: str | None = None) -> bool:
        """
        Converte dados de notas para CSV
        
        Args:
            output_file: Nome do arquivo CSV de saída (opcional)
            
        Returns:
            bool: True se conversão foi bem-sucedida
        """
        if output_file:
            self.csv_file = output_file
        
        # Carregar dados
        grades_data = self.load_grades_data()
        if not grades_data:
            return False
        
        # Preparar linhas do CSV
        csv_rows = []
        
        try:
            # Processar cada semestre
            for semester, subjects_list in grades_data.items():
                if not isinstance(subjects_list, list):
                    continue
                
                self.logger.debug(f"🔍 Processando semestre: {semester}")
                
                # Processar cada disciplina no semestre
                for subject_data in subjects_list:
                    if not isinstance(subject_data, dict):
                        continue
                    
                    disciplina = subject_data.get('Disciplina', 'Sem nome')
                    codigo = subject_data.get('Código', '')
                    resultado = subject_data.get('Resultado', '')
                    faltas = subject_data.get('Faltas', '0')
                    situacao = subject_data.get('Situação', '--')
                    
                    # Coletar todas as notas das unidades
                    notas = []
                    for i in range(1, 10):  # Unidades 1 a 9
                        unidade = subject_data.get(f'Unidade {i}', '')
                        if unidade and unidade.strip() and unidade != '--':
                            notas.append(unidade.strip())
                    
                    # Adicionar recuperação se existir
                    recuperacao = subject_data.get('Recuperação', '')
                    if recuperacao and recuperacao.strip() and recuperacao != '--':
                        notas.append(f"Rec: {recuperacao.strip()}")
                    
                    # Calcular média se há notas numéricas
                    numeric_grades = []
                    for nota in notas:
                        try:
                            # Remover prefixos como "Rec:" para cálculo
                            clean_nota = nota.replace('Rec:', '').strip()
                            numeric_grades.append(float(clean_nota.replace(',', '.')))
                        except (ValueError, AttributeError):
                            pass
                    
                    media = sum(numeric_grades) / len(numeric_grades) if numeric_grades else 0
                    
                    # Determinar status baseado na situação ou média
                    if situacao and situacao != '--':
                        status = situacao
                    elif media >= 7.0:
                        status = "Aprovado"
                    elif media > 0:
                        status = "Reprovado"
                    else:
                        status = "Pendente"
                    
                    # Se há notas, criar uma linha para cada nota
                    if notas:
                        for i, nota in enumerate(notas, 1):
                            csv_rows.append({
                                'semestre': semester,
                                'codigo': codigo,
                                'disciplina': disciplina,
                                'nota': nota,
                                'numero_nota': i,
                                'total_notas': len(notas),
                                'media': f"{media:.2f}" if media > 0 else '',
                                'resultado_final': resultado if resultado else '',
                                'faltas': faltas,
                                'status': status,
                                'data_exportacao': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            })
                    else:
                        # Se não há notas, criar linha básica
                        csv_rows.append({
                            'semestre': semester,
                            'codigo': codigo,
                            'disciplina': disciplina,
                            'nota': '',
                            'numero_nota': 0,
                            'total_notas': 0,
                            'media': '',
                            'resultado_final': resultado if resultado else '',
                            'faltas': faltas,
                            'status': status,
                            'data_exportacao': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        })
            
            # Escrever CSV
            if csv_rows:
                with open(self.csv_file, 'w', newline='', encoding='utf-8') as csvfile:
                    fieldnames = [
                        'semestre', 'codigo', 'disciplina', 'nota', 'numero_nota', 
                        'total_notas', 'media', 'resultado_final', 'faltas', 'status', 'data_exportacao'
                    ]
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    
                    # Escrever cabeçalho
                    writer.writeheader()
                    
                    # Escrever dados
                    writer.writerows(csv_rows)
                
                self.logger.info(f"✅ Conversão concluída: {len(csv_rows)} registros salvos em {self.csv_file}")
                self._print_summary(csv_rows)
                return True
            else:
                self.logger.warning("⚠️ Nenhum dado encontrado para exportar")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Erro durante conversão: {e}")
            return False
    
    def _print_summary(self, csv_rows: List[Dict]):
        """Imprime resumo da conversão"""
        if not csv_rows:
            return
        
        # Estatísticas
        total_subjects = len(set(row['disciplina'] for row in csv_rows))
        total_semesters = len(set(row['semestre'] for row in csv_rows))
        total_grades = len([row for row in csv_rows if row['nota'] and row['nota'].strip()])
        
        # Notas por status
        approved = len([row for row in csv_rows if 'Aprovado' in row['status']])
        failed = len([row for row in csv_rows if 'Reprovado' in row['status']])
        pending = len([row for row in csv_rows if row['status'] in ['Pendente', '--', 'Sem notas']])
        
        # Disciplinas com notas vs sem notas
        with_grades = len([row for row in csv_rows if row['total_notas'] > 0])
        without_grades = len([row for row in csv_rows if row['total_notas'] == 0])
        
        print(f"\n📊 Resumo da Exportação:")
        print(f"   📁 Arquivo: {self.csv_file}")
        print(f"   📚 Semestres: {total_semesters}")
        print(f"   📖 Disciplinas: {total_subjects}")
        print(f"   📝 Total de registros: {len(csv_rows)}")
        print(f"   🔢 Notas encontradas: {total_grades}")
        print(f"   📈 Com notas: {with_grades}")
        print(f"   📉 Sem notas: {without_grades}")
        print(f"\n📋 Status das Disciplinas:")
        print(f"   ✅ Aprovadas: {approved}")
        print(f"   ❌ Reprovadas: {failed}")
        print(f"   ⏳ Pendentes: {pending}")

def main():
    """Função principal para execução standalone"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Conversor de grades_cache.json para CSV')
    parser.add_argument('-o', '--output', 
                       help='Nome do arquivo CSV de saída (padrão: grades_export.csv)',
                       default='grades_export.csv')
    parser.add_argument('-v', '--verbose', 
                       action='store_true',
                       help='Modo verboso (debug)')
    
    args = parser.parse_args()
    
    # Configurar logging
    if args.verbose:
        import logging
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Executar conversão
    converter = GradesToCSVConverter()
    success = converter.convert_to_csv(args.output)
    
    if success:
        print(f"\n🎉 Conversão realizada com sucesso!")
        print(f"📄 Arquivo CSV disponível em: {args.output}")
        sys.exit(0)
    else:
        print(f"\n❌ Falha na conversão!")
        sys.exit(1)

if __name__ == "__main__":
    main()
