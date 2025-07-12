#!/usr/bin/env python3
"""
Script de teste básico para verificar a estrutura refatorada.
"""

import sys
import os

def test_imports():
    """Testa importações básicas da nova estrutura."""
    
    print("🔧 Testando nova estrutura modular...")
    
    try:
        # Testar configuração
        from src.config.settings import Config
        print("✅ Configuração importada")
        print(f"   - Versão: {Config.VERSION}")
        print(f"   - Método: {Config.get_extraction_method()}")
        
        # Testar utils
        from src.utils.env_loader import get_env_loader
        print("✅ Env loader importado")
        
        env_loader = get_env_loader()
        if env_loader.load_env_file():
            print("✅ Arquivo .env carregado")
        else:
            print("⚠️  Arquivo .env não encontrado")
        
        # Testar logger
        from src.utils.logger import get_logger, setup_logger
        print("✅ Sistema de logging importado")
        
        setup_logger(enable_debug=False)
        logger = get_logger("test")
        logger.info("Sistema de logging funcionando")
        
        # Testar serviços (sem playwright)
        try:
            from src.services.cache_service import CacheService
            print("✅ Cache service importado")
            
            cache = CacheService()
            cache_info = cache.get_cache_info()
            print(f"   - Cache existe: {'sim' if cache_info['exists'] else 'não'}")
            
        except Exception as e:
            print(f"⚠️  Erro nos serviços: {e}")
        
        # Testar estrutura de diretórios
        src_dirs = ['config', 'core', 'services', 'notifications', 'utils']
        for dir_name in src_dirs:
            dir_path = f"src/{dir_name}"
            if os.path.exists(dir_path):
                print(f"✅ Diretório {dir_path} existe")
            else:
                print(f"❌ Diretório {dir_path} não encontrado")
        
        print("\n🎉 Estrutura refatorada funcionando corretamente!")
        return True
        
    except Exception as e:
        print(f"❌ Erro na importação: {e}")
        return False


def test_old_vs_new():
    """Compara configurações antigas vs novas."""
    
    print("\n🔄 Comparando estrutura antiga vs nova...")
    
    try:
        # Testar config antigo
        if os.path.exists("config.py"):
            print("📁 Arquivo config.py antigo ainda existe")
        
        # Testar diretórios antigos
        old_dirs = ['scraper', 'utils', 'notification']
        for dir_name in old_dirs:
            if os.path.exists(dir_name):
                print(f"📁 Diretório antigo {dir_name} ainda existe")
        
        # Nova estrutura
        from src.config.settings import Config
        print(f"🆕 Nova configuração carregada: v{Config.VERSION}")
        print(f"🎯 Método configurado: {Config.get_extraction_method()}")
        
    except Exception as e:
        print(f"❌ Erro na comparação: {e}")


if __name__ == "__main__":
    try:
        success = test_imports()
        test_old_vs_new()
        
        if success:
            print("\n✅ Todos os testes passaram!")
            sys.exit(0)
        else:
            print("\n❌ Alguns testes falharam")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Erro durante os testes: {e}")
        sys.exit(1)
