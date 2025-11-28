"""
Handler for semantic search functionality.
Handles /search command and provides natural language search over questions.
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CommandHandler,
    MessageHandler,
    filters
)
from telegram.error import BadRequest
import logging
from config import MAX_QUERY_LENGTH, SEMANTIC_SEARCH_ENABLED

logger = logging.getLogger(__name__)

# Conversation states
WAITING_SEARCH_QUERY = 0


async def search_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Start search conversation.

    Args:
        update: The update object from Telegram
        context: The context object for the handler

    Returns:
        WAITING_SEARCH_QUERY state
    """
    user = update.effective_user
    logger.info(f"User {user.id} ({user.username}) started search")

    # Check if semantic search is enabled
    if not SEMANTIC_SEARCH_ENABLED:
        await update.message.reply_text(
            "⚠️ <b>Поиск недоступен</b>\n\n"
            "Семантический поиск временно отключен.\n"
            "Используйте /list для просмотра всех вопросов.",
            parse_mode='HTML'
        )
        return ConversationHandler.END

    # Send search prompt
    message = (
        "🔍 <b>Поиск по вопросам</b>\n\n"
        "Введите поисковый запрос:\n\n"
        "<i>Например:</i>\n"
        "• как установить python\n"
        "• что такое API\n"
        "• настройка git\n\n"
        f"Максимальная длина запроса: {MAX_QUERY_LENGTH} символов\n\n"
        "Используйте /cancel для отмены"
    )

    await update.message.reply_text(message, parse_mode='HTML')

    return WAITING_SEARCH_QUERY


async def search_query(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Process search query and display results.

    Args:
        update: The update object from Telegram
        context: The context object for the handler

    Returns:
        ConversationHandler.END
    """
    user = update.effective_user
    query = update.message.text.strip()

    logger.info(f"User {user.id} searching for: '{query}'")

    # Validate query
    if not query:
        await update.message.reply_text(
            "⚠️ <b>Пустой запрос</b>\n\n"
            "Пожалуйста, введите текст для поиска.\n\n"
            "Используйте /cancel для отмены",
            parse_mode='HTML'
        )
        return WAITING_SEARCH_QUERY

    if len(query) > MAX_QUERY_LENGTH:
        await update.message.reply_text(
            f"⚠️ <b>Запрос слишком длинный</b>\n\n"
            f"Максимальная длина запроса: {MAX_QUERY_LENGTH} символов.\n"
            f"Ваш запрос: {len(query)} символов.\n\n"
            "Пожалуйста, сократите запрос.",
            parse_mode='HTML'
        )
        return WAITING_SEARCH_QUERY

    # Show searching message
    searching_msg = await update.message.reply_text("🔍 Поиск...")

    try:
        # Get storage from context
        storage = context.bot_data.get('storage')

        if not storage:
            logger.error("Storage not found in bot_data")
            await searching_msg.edit_text(
                "❌ <b>Ошибка</b>\n\n"
                "Не удалось получить доступ к базе данных.\n"
                "Попробуйте позже.",
                parse_mode='HTML'
            )
            return ConversationHandler.END

        # Perform search
        results = storage.search_questions(query)

        # Display results
        if not results:
            # No results found
            message = (
                "😕 <b>Ничего не найдено</b>\n\n"
                f"По запросу \"{query}\" не найдено подходящих вопросов.\n\n"
                "Попробуйте:\n"
                "• Изменить формулировку\n"
                "• Использовать другие слова\n"
                "• Просмотреть все вопросы /list"
            )

            # Create keyboard
            keyboard = [
                [InlineKeyboardButton("🔍 Новый поиск", callback_data="new_search")],
                [InlineKeyboardButton("📚 К списку", callback_data="back_to_list")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await searching_msg.edit_text(
                message,
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
        else:
            # Format results
            results_word = _get_results_word(len(results))
            message = (
                f"📊 <b>Результаты поиска</b>\n\n"
                f"Найдено {len(results)} {results_word}:\n\n"
            )

            # Add each result
            for i, result in enumerate(results, 1):
                score_percent = int(result['score'] * 100)
                question = result['question']
                answer = result['answer']

                # Truncate answer for preview
                answer_preview = answer[:100] + "..." if len(answer) > 100 else answer

                message += (
                    f"{i}. ⭐ {score_percent}% - {question}\n"
                    f"   💡 {answer_preview}\n\n"
                )

            # Create keyboard with buttons for each result
            keyboard = []
            for i, result in enumerate(results, 1):
                keyboard.append([
                    InlineKeyboardButton(
                        f"{i}. Показать полностью",
                        callback_data=f"view_{result['id']}"
                    )
                ])

            # Add navigation buttons
            keyboard.append([
                InlineKeyboardButton("🔍 Новый поиск", callback_data="new_search"),
                InlineKeyboardButton("📚 К списку", callback_data="back_to_list")
            ])

            reply_markup = InlineKeyboardMarkup(keyboard)

            await searching_msg.edit_text(
                message,
                reply_markup=reply_markup,
                parse_mode='HTML'
            )

        logger.info(f"Search completed for user {user.id}: {len(results)} results")

    except Exception as e:
        logger.error(f"Search failed for user {user.id}: {e}")
        await searching_msg.edit_text(
            "❌ <b>Ошибка поиска</b>\n\n"
            "Не удалось выполнить поиск.\n"
            "Попробуйте еще раз или используйте /list",
            parse_mode='HTML'
        )

    return ConversationHandler.END


async def search_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Cancel search operation.

    Args:
        update: The update object from Telegram
        context: The context object for the handler

    Returns:
        ConversationHandler.END
    """
    user = update.effective_user
    logger.info(f"User {user.id} cancelled search")

    await update.message.reply_text(
        "❌ Поиск отменён.\n\n"
        "Используйте /search для нового поиска или /list для просмотра всех вопросов."
    )

    return ConversationHandler.END


async def handle_new_search(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle "new search" button callback.

    Args:
        update: The update object from Telegram
        context: The context object for the handler
    """
    query = update.callback_query
    await query.answer()

    user = update.effective_user
    logger.info(f"User {user.id} requested new search")

    # Send search prompt
    message = (
        "🔍 <b>Поиск по вопросам</b>\n\n"
        "Введите поисковый запрос:\n\n"
        "<i>Например:</i>\n"
        "• как установить python\n"
        "• что такое API\n"
        "• настройка git\n\n"
        f"Максимальная длина запроса: {MAX_QUERY_LENGTH} символов"
    )

    try:
        await query.edit_message_text(message, parse_mode='HTML')
    except BadRequest as e:
        if "Message is not modified" not in str(e):
            logger.error(f"Error editing message: {e}")


def _get_results_word(count: int) -> str:
    """
    Get correct Russian word form for results count.

    Args:
        count: Number of results

    Returns:
        Correct word form (результат/результата/результатов)
    """
    if count % 10 == 1 and count % 100 != 11:
        return "результат"
    elif 2 <= count % 10 <= 4 and (count % 100 < 10 or count % 100 >= 20):
        return "результата"
    else:
        return "результатов"


def get_search_conversation_handler() -> ConversationHandler:
    """
    Create and return search conversation handler.

    Returns:
        ConversationHandler for search functionality
    """
    return ConversationHandler(
        entry_points=[CommandHandler("search", search_start)],
        states={
            WAITING_SEARCH_QUERY: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, search_query)
            ]
        },
        fallbacks=[CommandHandler("cancel", search_cancel)],
        name="search_conversation",
        persistent=False
    )
