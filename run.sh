#!/bin/bash

# UFCG SIGAA Scraper - Script de Execução
# Este script facilita a execução do scraper com diferentes opções

set -e

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Função para exibir header
show_header() {
    echo -e "${BLUE}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                    UFCG SIGAA Scraper v2.0                  ║"
    echo "║                     Arquitetura Modular                     ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

# Função para verificar dependências
check_dependencies() {
    echo -e "${YELLOW}Verificando dependências...${NC}"
    
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}❌ Python 3 não encontrado!${NC}"
        exit 1
    fi
    
    if [ ! -f ".env" ]; then
        echo -e "${RED}❌ Arquivo .env não encontrado!${NC}"
        echo -e "${YELLOW}💡 Crie o arquivo .env com suas credenciais${NC}"
        exit 1
    fi
    
    if [ ! -d "venv" ] && [ ! -d ".venv" ]; then
        echo -e "${YELLOW}⚠️  Ambiente virtual não encontrado${NC}"
        echo -e "${BLUE}💡 Recomendamos usar um ambiente virtual${NC}"
    fi
    
    echo -e "${GREEN}✅ Dependências verificadas${NC}"
}

# Função para executar o scraper
run_scraper() {
    echo -e "${BLUE}🚀 Iniciando SIGAA Scraper...${NC}"
    echo -e "${YELLOW}📝 Logs serão salvos em script.log${NC}"
    echo
    
    python3 main.py
    
    if [ $? -eq 0 ]; then
        echo
        echo -e "${GREEN}✅ Execução concluída com sucesso!${NC}"
    else
        echo
        echo -e "${RED}❌ Erro durante a execução${NC}"
        echo -e "${YELLOW}📝 Verifique os logs em script.log para mais detalhes${NC}"
        exit 1
    fi
}

# Função para mostrar informações do projeto
show_info() {
    echo -e "${BLUE}📋 Informações do Projeto:${NC}"
    echo "• Versão: 2.0.0"
    echo "• Arquitetura: Modular"
    echo "• Python: $(python3 --version 2>/dev/null || echo 'Não encontrado')"
    echo "• Estrutura:"
    echo "  ├── src/core/           - Núcleo da aplicação"
    echo "  ├── src/services/       - Serviços especializados" 
    echo "  ├── src/notifications/  - Sistema de notificações"
    echo "  ├── src/utils/          - Utilitários"
    echo "  └── src/config/         - Configurações"
    echo
}

# Função para mostrar ajuda
show_help() {
    echo -e "${BLUE}🆘 Ajuda - UFCG SIGAA Scraper${NC}"
    echo
    echo "Uso: $0 [OPÇÃO]"
    echo
    echo "Opções:"
    echo "  run        Executa o scraper (padrão)"
    echo "  check      Verifica dependências"
    echo "  info       Mostra informações do projeto"
    echo "  logs       Mostra os últimos logs"
    echo "  clean      Limpa cache e logs"
    echo "  help       Mostra esta ajuda"
    echo
    echo "Exemplos:"
    echo "  $0          # Executa o scraper"
    echo "  $0 run      # Executa o scraper" 
    echo "  $0 check    # Verifica se tudo está configurado"
    echo "  $0 logs     # Mostra os logs mais recentes"
    echo
}

# Função para mostrar logs
show_logs() {
    if [ -f "script.log" ]; then
        echo -e "${BLUE}📋 Últimos logs:${NC}"
        echo "────────────────────────────────────────"
        tail -20 script.log
        echo "────────────────────────────────────────"
        echo -e "${YELLOW}💡 Arquivo completo: script.log${NC}"
    else
        echo -e "${YELLOW}⚠️  Arquivo de log não encontrado${NC}"
        echo -e "${BLUE}💡 Execute o scraper primeiro para gerar logs${NC}"
    fi
}

# Função para limpar cache
clean_cache() {
    echo -e "${YELLOW}🧹 Limpando cache e logs...${NC}"
    
    # Remove cache Python
    find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
    find . -name "*.pyc" -delete 2>/dev/null || true
    
    # Remove logs antigos
    [ -f "script.log" ] && rm script.log
    
    echo -e "${GREEN}✅ Cache limpo!${NC}"
}

# Main
main() {
    show_header
    
    case "${1:-run}" in
        "run")
            check_dependencies
            run_scraper
            ;;
        "check")
            check_dependencies
            echo -e "${GREEN}✅ Tudo configurado corretamente!${NC}"
            ;;
        "info")
            show_info
            ;;
        "logs")
            show_logs
            ;;
        "clean")
            clean_cache
            ;;
        "help"|"-h"|"--help")
            show_help
            ;;
        *)
            echo -e "${RED}❌ Opção inválida: $1${NC}"
            echo
            show_help
            exit 1
            ;;
    esac
}

main "$@"
