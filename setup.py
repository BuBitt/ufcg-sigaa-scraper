#!/usr/bin/env python3
"""
Script de configuração e verificação do SIGAA Scraper.
"""

import os
import sys
from typing import Dict, Any

def check_environment() -> Dict[str, Any]:
    """
    Verifica o ambiente e configurações.
    
    Returns:
        Dict com status das verificações
    """
    status = {
        "env_file": False,
        "credentials": False,
        "telegram": False,
        "dependencies": False,
        "directories": False
    }
    
    # Verificar arquivo .env
    if os.path.exists(".env"):
        status["env_file"] = True
        print("✅ Arquivo .env encontrado")
    else:
        print("❌ Arquivo .env não encontrado")
        return status
    
    # Verificar credenciais
    from src.utils.env_loader import get_env_loader
    try:
        env_loader = get_env_loader()
        username, password = env_loader.get_credentials()
        if username and password:
            status["credentials"] = True
            print(f"✅ Credenciais configuradas para usuário: {username[:3]}***")
        else:
            print("❌ Credenciais não configuradas")
    except Exception as e:
        print(f"❌ Erro ao carregar credenciais: {e}")
    
    # Verificar configuração do Telegram
    try:
        telegram_config = env_loader.get_telegram_config()
        if telegram_config.get("bot_token"):
            status["telegram"] = True
            print("✅ Bot Telegram configurado")
        else:
            print("⚠️  Bot Telegram não configurado (opcional)")
    except Exception as e:
        print(f"⚠️  Telegram não configurado: {e}")
    
    # Verificar dependências
    try:
        import playwright
        import beautifulsoup4
        import requests
        status["dependencies"] = True
        print("✅ Dependências instaladas")
    except ImportError as e:
        print(f"❌ Dependência faltando: {e}")
    
    # Verificar diretórios
    if os.path.exists("logs"):
        status["directories"] = True
        print("✅ Diretórios criados")
    else:
        os.makedirs("logs", exist_ok=True)
        status["directories"] = True
        print("✅ Diretórios criados")
    
    return status

def setup_environment():
    """Configura o ambiente inicial."""
    print("🔧 Configurando ambiente...")
    
    # Criar arquivo .env se não existir
    if not os.path.exists(".env"):
        print("📝 Criando arquivo .env...")
        env_template = """# UFCG SIGAA Scraper - Configurações de Ambiente

# ====================================================================
# CREDENCIAIS DO SIGAA
# ====================================================================
SIGAA_USERNAME=seu_usuario_aqui
SIGAA_PASSWORD=sua_senha_aqui

# ====================================================================
# CONFIGURAÇÕES DE EXTRAÇÃO
# ====================================================================
# Método de extração: menu_ensino ou materia_individual
EXTRACTION_METHOD=menu_ensino

# ====================================================================
# CONFIGURAÇÕES DO BOT TELEGRAM (Opcional)
# ====================================================================
TELEGRAM_BOT_TOKEN=
TELEGRAM_GROUP_CHAT_ID=
TELEGRAM_PRIVATE_CHAT_ID=
"""
        with open(".env", "w") as f:
            f.write(env_template)
        print("✅ Arquivo .env criado")
        print("📝 Edite o arquivo .env com suas credenciais")
    
    # Criar diretórios necessários
    os.makedirs("logs", exist_ok=True)
    print("✅ Diretórios criados")

def test_login():
    """Testa apenas o login sem extrair notas."""
    print("🧪 Testando login...")
    
    try:
        from src.services.auth_service import AuthService
        from src.config.settings import Config
        from playwright.sync_api import sync_playwright
        
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=False)  # Modo visual para teste
            context = browser.new_context(
                viewport={"width": Config.VIEWPORT_WIDTH, "height": Config.VIEWPORT_HEIGHT},
                user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            page = context.new_page()
            
            auth_service = AuthService()
            success = auth_service.login(page)
            
            if success:
                print("✅ Login realizado com sucesso!")
                input("Pressione Enter para fechar o navegador...")
            else:
                print("❌ Falha no login")
            
            browser.close()
            
    except Exception as e:
        print(f"❌ Erro no teste: {e}")

def main():
    """Função principal do script de configuração."""
    if len(sys.argv) < 2:
        print("🔧 SIGAA Scraper - Script de Configuração")
        print("\nComandos disponíveis:")
        print("  setup    - Configurar ambiente inicial")
        print("  check    - Verificar configurações")
        print("  test     - Testar login (modo visual)")
        print("  run      - Executar scraper completo")
        return
    
    command = sys.argv[1]
    
    if command == "setup":
        setup_environment()
    elif command == "check":
        status = check_environment()
        
        print("\n📊 RESUMO:")
        all_good = all(status.values())
        if all_good:
            print("🎉 Tudo configurado corretamente!")
            print("💡 Execute: python main.py")
        else:
            print("⚠️  Algumas configurações precisam de atenção")
            if not status["credentials"]:
                print("   - Configure suas credenciais no arquivo .env")
            if not status["dependencies"]:
                print("   - Instale as dependências: pip install -r requirements.txt")
    
    elif command == "test":
        status = check_environment()
        if status["credentials"]:
            test_login()
        else:
            print("❌ Configure suas credenciais primeiro")
    
    elif command == "run":
        from main import main as run_scraper
        run_scraper()
    
    else:
        print(f"❌ Comando desconhecido: {command}")

if __name__ == "__main__":
    main()
