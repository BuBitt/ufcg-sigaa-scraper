# config.py
import logging

CREATE_CSV = False
HEADLESS_BROWSER = True
LOG_DEPTH = logging.DEBUG

CSV_FILENAME = "notas_completas.csv"
CACHE_FILENAME = "grades_cache.json"
HTML_OUTPUT = "minhas_notas.html"
HTML_DEBUG_OUTPUT = "minhas_notas_debug.html"
LOG_FILENAME = "script.log"

SEND_TELEGRAM_GROUP = False  # Ativar envio pro grupo
SEND_TELEGRAM_PRIVATE = True  # Ativar envio pro chat privado

TIMEOUT_DEFAULT = 30000
VIEWPORT_WIDTH = 1280
VIEWPORT_HEIGHT = 720
