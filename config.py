"""
Configuration module for Telegram bot.
Loads settings from environment variables and defines constants.
"""

import os
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Bot configuration
BOT_TOKEN = os.getenv('BOT_TOKEN')

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN environment variable is not set. Please check your .env file.")

# Storage limits
MAX_QUESTIONS_TOTAL = 100
MAX_QUESTION_LENGTH = 500
MAX_ANSWER_LENGTH = 2000
MAX_QUESTIONS_PER_USER_PER_DAY = 20

# Semantic Search Configuration
SEMANTIC_SEARCH_ENABLED = os.getenv('SEMANTIC_SEARCH_ENABLED', 'true').lower() == 'true'
SEMANTIC_SEARCH_MODEL = os.getenv(
    'SEMANTIC_SEARCH_MODEL',
    'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2'
)
SEARCH_TOP_K = int(os.getenv('SEARCH_TOP_K', '5'))
SEARCH_SIMILARITY_THRESHOLD = float(os.getenv('SEARCH_SIMILARITY_THRESHOLD', '0.3'))
SEARCH_BATCH_SIZE = int(os.getenv('SEARCH_BATCH_SIZE', '10'))
MODEL_CACHE_DIR = os.getenv('MODEL_CACHE_DIR', './models')
MAX_QUERY_LENGTH = int(os.getenv('MAX_QUERY_LENGTH', '200'))

# Logging configuration
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOG_FILE = 'bot.log'

# Configure logging
logging.basicConfig(
    format=LOG_FORMAT,
    level=getattr(logging, LOG_LEVEL.upper()),
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)
logger.info("Configuration loaded successfully")
