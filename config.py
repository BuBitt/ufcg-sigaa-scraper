# config.py
import logging

# General settings
CREATE_CSV = False
HEADLESS_BROWSER = True
LOG_DEPTH = logging.DEBUG

# File paths
CSV_FILENAME = "notas_completas.csv"
CACHE_FILENAME = "grades_cache.json"
HTML_OUTPUT = "minhas_notas.html"
HTML_DEBUG_OUTPUT = "minhas_notas_debug.html"
LOG_FILENAME = "script.log"

# Telegram settings
SEND_TELEGRAM_GROUP = True  # Enable group notifications
SEND_TELEGRAM_PRIVATE = True  # Enable private chat notifications

# Browser settings
TIMEOUT_DEFAULT = 30000
VIEWPORT_WIDTH = 1280
VIEWPORT_HEIGHT = 720
