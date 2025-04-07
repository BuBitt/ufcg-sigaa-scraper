"""
Arquivo de configurações centralizadas para o SIGAA Grade Scraper.
Todas as constantes e configurações estão agrupadas aqui para facilitar manutenção.
"""
import logging
import os

# Versão do aplicativo
VERSION = "1.0.1"
APP_NAME = "SIGAA Grade Scraper"

# Configurações gerais
CREATE_CSV = False
HEADLESS_BROWSER = True
LOG_DEPTH = logging.DEBUG
DEFAULT_ENCODING = "utf-8"

# Caminhos de arquivos
CSV_FILENAME = "notas_completas.csv"
CACHE_FILENAME = "grades_cache.json"
HTML_OUTPUT = "minhas_notas.html"
HTML_DEBUG_OUTPUT = "minhas_notas_debug.html"
LOG_FILENAME = os.path.join("logs", "sigaa_scraper.log")

# Garantir que o diretório de logs existe
os.makedirs(os.path.dirname(LOG_FILENAME), exist_ok=True)

# Configurações do Telegram
SEND_TELEGRAM_GROUP = True  # Habilitar notificações de grupo
SEND_TELEGRAM_PRIVATE = True  # Habilitar notificações de chat privado

# Configurações de segurança
MASK_CREDENTIALS = True  # Mascarar credenciais nos logs

# Configurações do navegador
TIMEOUT_DEFAULT = 30000  # 30 segundos em milissegundos
VIEWPORT_WIDTH = 1280
VIEWPORT_HEIGHT = 720

# Configurações de retry
MAX_RETRIES = 3
RETRY_DELAY = 2  # segundos
REQUEST_TIMEOUT = 10  # segundos

# Configurações de arquivo
MAX_BACKUP_FILES = 3
JSON_INDENT = 4
