"""
Main bot application file.
Initializes the bot, registers handlers, and starts polling.
"""

import logging
from telegram.ext import Application, CommandHandler, CallbackQueryHandler
from config import BOT_TOKEN, SEMANTIC_SEARCH_ENABLED
from storage.sqlite import SQLiteStorage
from utils.semantic_search import get_search_engine
from handlers import (
    start,
    help_command,
    cancel,
    get_add_conversation_handler,
    get_edit_conversation_handler,
    get_search_conversation_handler,
    list_questions,
    button_callback,
    delete_start,
    confirm_delete,
    cancel_delete
)

# Configure logging
logger = logging.getLogger(__name__)


def main() -> None:
    """
    Main function to initialize and run the bot.
    """
    logger.info("Starting Telegram bot...")

    # Create the Application
    application = Application.builder().token(BOT_TOKEN).build()

    # Initialize semantic search engine if enabled
    search_engine = None
    if SEMANTIC_SEARCH_ENABLED:
        try:
            from config import SEMANTIC_SEARCH_MODEL
            search_engine = get_search_engine(SEMANTIC_SEARCH_MODEL)
            logger.info(f"Semantic search engine initialized with model: {SEMANTIC_SEARCH_MODEL}")
        except Exception as e:
            logger.warning(f"Failed to initialize search engine: {e}")
            logger.warning("Semantic search will be disabled")

    # Initialize storage with search engine
    storage = SQLiteStorage(db_path='sqlite.db', search_engine=search_engine)
    application.bot_data['storage'] = storage
    logger.info("Storage initialized")

    # Register basic command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    logger.info("Basic command handlers registered")

    # Register conversation handler for adding questions
    add_handler = get_add_conversation_handler(storage)
    application.add_handler(add_handler)
    logger.info("Add conversation handler registered")

    # Register conversation handler for editing questions
    edit_handler = get_edit_conversation_handler()
    application.add_handler(edit_handler)
    logger.info("Edit conversation handler registered")

    # Register conversation handler for search (if enabled)
    if SEMANTIC_SEARCH_ENABLED:
        search_handler = get_search_conversation_handler()
        application.add_handler(search_handler)
        logger.info("Search conversation handler registered")

    # Register list command handler
    application.add_handler(CommandHandler("list", list_questions))
    logger.info("List command handler registered")

    # Register callback query handler for button interactions
    application.add_handler(CallbackQueryHandler(button_callback))
    logger.info("Callback query handler registered")

    # Register fallback cancel handler (for when not in conversation)
    application.add_handler(CommandHandler("cancel", cancel))
    logger.info("Fallback cancel handler registered")

    # Start the bot
    logger.info("Bot is starting polling...")
    application.run_polling(allowed_updates=["message", "callback_query"])


if __name__ == '__main__':
    main()
