#!/usr/bin/env python3
"""
Script de teste para verificar a configuração do método de extração.
"""

import os
import sys
import config
from utils.file_handler import load_env

def test_extraction_method():
    """Testa a configuração do método de extração."""
    
    print("🔧 Testando configuração do método de extração...")
    
    # Carregar .env se existir
    try:
        load_env()
        print("✅ Arquivo .env carregado")
    except FileNotFoundError:
        print("⚠️  Arquivo .env não encontrado, usando configurações padrão")
    
    # Verificar método configurado
    method = config.EXTRACTION_METHOD
    print(f"📊 Método configurado: {method}")
    
    if method.lower() == "menu_ensino":
        print("✅ Usando método Menu Ensino (recomendado)")
        print("   - Mais rápido e direto")
        print("   - Acessa via menu Ensino > Consultar Minhas Notas")
    elif method.lower() == "materia_individual":
        print("✅ Usando método Matéria Individual")
        print("   - Método original")
        print("   - Acessa cada matéria separadamente")
    else:
        print(f"⚠️  Método inválido '{method}', será usado 'menu_ensino' por padrão")
    
    # Verificar outras configurações relevantes
    print(f"\n🔍 Outras configurações:")
    print(f"   - Headless: {config.HEADLESS_BROWSER}")
    print(f"   - Timeout: {config.TIMEOUT_DEFAULT}ms")
    print(f"   - Cache: {config.CACHE_FILENAME}")
    
    # Verificar variáveis de ambiente
    env_method = os.getenv("EXTRACTION_METHOD")
    if env_method:
        print(f"   - EXTRACTION_METHOD definido: {env_method}")
    else:
        print("   - EXTRACTION_METHOD não definido (usando padrão)")
    
    print("\n✅ Teste de configuração concluído!")
    return method

if __name__ == "__main__":
    test_extraction_method()
