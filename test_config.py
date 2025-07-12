#!/usr/bin/env python3
"""
Script de teste para verificar a configuração do sistema refatorado.
"""

import sys
from src.core.sigaa_scraper import SIGAAScraper
from src.config.settings import Config


def test_extraction_method():
    """Testa a configuração do método de extração."""
    
    print("🔧 Testando configuração do sistema refatorado...")
    
    # Criar instância do scraper
    scraper = SIGAAScraper(debug_mode=True)
    
    # Verificar método configurado
    method = Config.get_extraction_method()
    print(f"📊 Método configurado: {method}")
    
    if method == "menu_ensino":
        print("✅ Usando método Menu Ensino (recomendado)")
        print("   - Mais rápido e direto")
        print("   - Acessa via menu Ensino > Consultar Minhas Notas")
    elif method == "materia_individual":
        print("✅ Usando método Matéria Individual")
        print("   - Método original")
        print("   - Acessa cada matéria separadamente")
    else:
        print(f"⚠️  Método inválido '{method}', será usado 'menu_ensino' por padrão")
    
    # Verificar outras configurações relevantes
    print(f"\n🔍 Outras configurações:")
    print(f"   - Versão: {Config.VERSION}")
    print(f"   - Headless: {Config.HEADLESS_BROWSER}")
    print(f"   - Timeout: {Config.TIMEOUT_DEFAULT}ms")
    print(f"   - Cache: {Config.CACHE_FILENAME}")
    print(f"   - Logs: {Config.LOG_FILENAME}")
    
    # Testar configuração completa
    print(f"\n🧪 Testando configuração completa...")
    if scraper.test_configuration():
        print("✅ Configuração válida!")
    else:
        print("❌ Problemas na configuração detectados")
    
    print("\n✅ Teste de configuração concluído!")
    return method


if __name__ == "__main__":
    try:
        test_extraction_method()
    except Exception as e:
        print(f"❌ Erro durante o teste: {e}")
        sys.exit(1)
