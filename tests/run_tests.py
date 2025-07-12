"""
Script principal para executar todos os testes.
"""

import pytest
import sys
import os

# Adicionar o projeto ao path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)


def run_all_tests():
    """Executa todos os testes do projeto."""
    
    print("🧪 Executando todos os testes do SIGAA Scraper...")
    print("=" * 60)
    
    # Configurações do pytest
    pytest_args = [
        "-v",  # Verbose
        "--tb=short",  # Traceback curto
        "--color=yes",  # Cores
        os.path.dirname(__file__),  # Diretório de testes
    ]
    
    # Executar testes
    exit_code = pytest.main(pytest_args)
    
    if exit_code == 0:
        print("\n✅ Todos os testes passaram com sucesso!")
    else:
        print(f"\n❌ Alguns testes falharam (código de saída: {exit_code})")
    
    return exit_code


def run_specific_test_module(module_name):
    """
    Executa testes de um módulo específico.
    
    Args:
        module_name: Nome do módulo (ex: 'test_services')
    """
    
    print(f"🧪 Executando testes do módulo: {module_name}")
    print("=" * 60)
    
    test_file = os.path.join(os.path.dirname(__file__), f"{module_name}.py")
    
    if not os.path.exists(test_file):
        print(f"❌ Arquivo de teste não encontrado: {test_file}")
        return 1
    
    pytest_args = [
        "-v",
        "--tb=short",
        "--color=yes",
        test_file
    ]
    
    exit_code = pytest.main(pytest_args)
    
    if exit_code == 0:
        print(f"\n✅ Testes do módulo {module_name} passaram!")
    else:
        print(f"\n❌ Testes do módulo {module_name} falharam!")
    
    return exit_code


if __name__ == "__main__":
    
    if len(sys.argv) > 1:
        # Executar módulo específico
        module = sys.argv[1]
        exit_code = run_specific_test_module(module)
    else:
        # Executar todos os testes
        exit_code = run_all_tests()
    
    sys.exit(exit_code)
