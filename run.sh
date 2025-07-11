#!/bin/bash

# UFCG SIGAA Scraper - Script de Execução
# Este script facilita a execução do scraper com diferentes opções

set -e

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Função para exibir help
show_help() {
    echo -e "${BLUE}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                    UFCG SIGAA Scraper v2.0                  ║"
    echo "║                     Arquitetura Modular                     ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    echo
    echo -e "${CYAN}📋 COMANDOS DISPONÍVEIS:${NC}"
    echo
    echo -e "${GREEN}🚀 Execução:${NC}"
    echo -e "  ${YELLOW}./run.sh${NC}                    - Executar scraper (modo normal)"
    echo -e "  ${YELLOW}./run.sh run${NC}                - Executar scraper (modo normal)"
    echo -e "  ${YELLOW}./run.sh debug${NC}              - Executar scraper (modo debug)"
    echo -e "  ${YELLOW}./run.sh -d${NC}                 - Executar scraper (modo debug)"
    echo
    echo -e "${GREEN}📊 Logs e Dados:${NC}"
    echo -e "  ${YELLOW}./run.sh logs${NC}               - Visualizar logs recentes"
    echo -e "  ${YELLOW}./run.sh tail${NC}               - Seguir logs em tempo real"
    echo -e "  ${YELLOW}./run.sh clear-logs${NC}         - Limpar arquivos de log"
    echo
    echo -e "${GREEN}📄 Exportação:${NC}"
    echo -e "  ${YELLOW}./run.sh csv${NC}                - Converter notas para CSV"
    echo -e "  ${YELLOW}./run.sh export${NC}             - Converter notas para CSV"
    echo -e "  ${YELLOW}./run.sh csv notas.csv${NC}      - Converter para arquivo específico"
    echo
    echo -e "${GREEN}🔧 Manutenção:${NC}"
    echo -e "  ${YELLOW}./run.sh check${NC}              - Verificar dependências"
    echo -e "  ${YELLOW}./run.sh install${NC}            - Instalar dependências"
    echo -e "  ${YELLOW}./run.sh clean${NC}              - Limpar cache e arquivos temporários"
    echo
    echo -e "${GREEN}ℹ️  Informações:${NC}"
    echo -e "  ${YELLOW}./run.sh help${NC}               - Mostrar esta ajuda"
    echo -e "  ${YELLOW}./run.sh --help${NC}             - Mostrar esta ajuda"
    echo -e "  ${YELLOW}./run.sh -h${NC}                 - Mostrar esta ajuda"
    echo -e "  ${YELLOW}./run.sh status${NC}             - Status do sistema"
    echo
    echo -e "${PURPLE}💡 EXEMPLOS:${NC}"
    echo -e "  ${CYAN}# Execução normal${NC}"
    echo -e "  ./run.sh"
    echo
    echo -e "  ${CYAN}# Debug detalhado${NC}"
    echo -e "  ./run.sh debug"
    echo
    echo -e "  ${CYAN}# Exportar notas para Excel${NC}"
    echo -e "  ./run.sh csv relatorio_notas.csv"
    echo
    echo -e "  ${CYAN}# Monitorar logs ao vivo${NC}"
    echo -e "  ./run.sh tail"
    echo
}

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
    local debug_mode=$1
    
    if [ "$debug_mode" = "debug" ]; then
        echo -e "${BLUE}🚀 Iniciando SIGAA Scraper (Modo Debug)...${NC}"
        echo -e "${PURPLE}🔍 Logs detalhados serão exibidos${NC}"
        echo
        python3 main.py --debug
    else
        echo -e "${BLUE}🚀 Iniciando SIGAA Scraper...${NC}"
        echo -e "${YELLOW}📝 Logs serão salvos em logs/sigaa_scraper.log${NC}"
        echo
        python3 main.py
    fi
    
    if [ $? -eq 0 ]; then
        echo
        echo -e "${GREEN}✅ Execução concluída com sucesso!${NC}"
    else
        echo
        echo -e "${RED}❌ Erro durante a execução${NC}"
        echo -e "${YELLOW}📝 Verifique os logs para mais detalhes${NC}"
        exit 1
    fi
}

# Função para converter notas para CSV
convert_to_csv() {
    local output_file=$1
    
    echo -e "${BLUE}📄 Convertendo notas para CSV...${NC}"
    
    if [ ! -f "grades_cache.json" ]; then
        echo -e "${RED}❌ Arquivo grades_cache.json não encontrado!${NC}"
        echo -e "${YELLOW}💡 Execute o scraper primeiro para gerar dados${NC}"
        exit 1
    fi
    
    if [ -n "$output_file" ]; then
        python3 src/utils/csv_converter.py -o "$output_file"
    else
        python3 src/utils/csv_converter.py
    fi
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Conversão CSV concluída!${NC}"
        echo -e "${BLUE}📁 Arquivo disponível para análise externa${NC}"
    else
        echo -e "${RED}❌ Erro durante conversão${NC}"
        exit 1
    fi
}

# Função para mostrar status do sistema
show_status() {
    echo -e "${BLUE}📋 Status do Sistema:${NC}"
    echo "• Versão: 2.0.0"
    echo "• Arquitetura: Modular"
    echo "• Python: $(python3 --version 2>/dev/null || echo 'Não encontrado')"
    echo "• Diretório: $(pwd)"
    echo
    
    # Verificar arquivos importantes
    echo -e "${BLUE}📂 Arquivos:${NC}"
    [ -f ".env" ] && echo "  ✅ .env" || echo "  ❌ .env (não encontrado)"
    [ -f "grades_cache.json" ] && echo "  ✅ grades_cache.json" || echo "  ⚪ grades_cache.json (será criado)"
    [ -d "logs" ] && echo "  ✅ logs/" || echo "  ⚪ logs/ (será criado)"
    [ -f "grades_export.csv" ] && echo "  ✅ grades_export.csv" || echo "  ⚪ grades_export.csv (use: ./run.sh csv)"
    
    echo
    echo -e "${BLUE}🏗️  Estrutura Modular:${NC}"
    echo "  ├── src/core/           - Núcleo da aplicação"
    echo "  ├── src/services/       - Serviços especializados" 
    echo "  ├── src/utils/          - Utilitários e conversores"
    echo "  └── logs/               - Sistema de logging avançado"
    echo
}

# Função para mostrar logs
show_logs() {
    if [ -f "logs/sigaa_scraper.log" ]; then
        echo -e "${BLUE}📋 Últimos logs (logs/sigaa_scraper.log):${NC}"
        echo "────────────────────────────────────────"
        tail -30 logs/sigaa_scraper.log
        echo "────────────────────────────────────────"
        echo -e "${YELLOW}💡 Arquivo completo: logs/sigaa_scraper.log${NC}"
    elif [ -f "script.log" ]; then
        echo -e "${BLUE}📋 Últimos logs (script.log - legado):${NC}"
        echo "────────────────────────────────────────"
        tail -20 script.log
        echo "────────────────────────────────────────" 
        echo -e "${YELLOW}💡 Arquivo completo: script.log${NC}"
    else
        echo -e "${YELLOW}⚠️  Nenhum arquivo de log encontrado${NC}"
        echo -e "${BLUE}💡 Execute o scraper primeiro para gerar logs${NC}"
    fi
}

# Função para seguir logs em tempo real
tail_logs() {
    if [ -f "logs/sigaa_scraper.log" ]; then
        echo -e "${BLUE}📋 Seguindo logs em tempo real...${NC}"
        echo -e "${YELLOW}💡 Pressione Ctrl+C para sair${NC}"
        echo "────────────────────────────────────────"
        tail -f logs/sigaa_scraper.log
    else
        echo -e "${YELLOW}⚠️  Arquivo de log não encontrado${NC}"
        echo -e "${BLUE}💡 Execute o scraper primeiro para gerar logs${NC}"
    fi
}

# Função para limpar cache e logs
clean_cache() {
    echo -e "${YELLOW}🧹 Limpando cache e arquivos temporários...${NC}"
    
    # Remove cache Python
    find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
    find . -name "*.pyc" -delete 2>/dev/null || true
    
    echo -e "${GREEN}✅ Cache Python limpo!${NC}"
}

# Função para limpar logs
clear_logs() {
    echo -e "${YELLOW}🧹 Limpando arquivos de log...${NC}"
    
    # Remove logs
    [ -f "script.log" ] && rm script.log && echo "  ✅ script.log removido"
    [ -d "logs" ] && rm -rf logs/* && echo "  ✅ logs/ limpo"
    
    echo -e "${GREEN}✅ Logs limpos!${NC}"
}

# Função para instalar dependências
install_deps() {
    echo -e "${BLUE}📦 Instalando dependências...${NC}"
    
    # Verificar se requirements.txt existe
    if [ ! -f "requirements.txt" ]; then
        echo -e "${RED}❌ Arquivo requirements.txt não encontrado!${NC}"
        exit 1
    fi
    
    # Instalar dependências Python
    echo -e "${YELLOW}🐍 Instalando pacotes Python...${NC}"
    python3 -m pip install -r requirements.txt
    
    # Instalar Playwright
    echo -e "${YELLOW}🎭 Instalando navegador Chromium...${NC}"
    playwright install chromium
    
    echo -e "${GREEN}✅ Dependências instaladas com sucesso!${NC}"
}

# Main
main() {
    # Verificar se é help primeiro
    case "${1}" in
        "help"|"-h"|"--help")
            show_help
            exit 0
            ;;
    esac
    
    show_header
    
    case "${1:-run}" in
        "run"|"")
            check_dependencies
            run_scraper
            ;;
        "debug"|"-d")
            check_dependencies
            run_scraper debug
            ;;
        "csv"|"export")
            convert_to_csv "$2"
            ;;
        "check")
            check_dependencies
            echo -e "${GREEN}✅ Tudo configurado corretamente!${NC}"
            ;;
        "status")
            show_status
            ;;
        "logs")
            show_logs
            ;;
        "tail")
            tail_logs
            ;;
        "clear-logs")
            clear_logs
            ;;
        "clean")
            clean_cache
            ;;
        "install")
            install_deps
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