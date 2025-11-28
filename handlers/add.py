"""
ConversationHandler for adding new question-answer pairs.
Handles the multi-step dialog for collecting question and answer from user.
"""

from telegram import Update
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CommandHandler,
    MessageHandler,
    filters
)
import logging
from utils.validators import validate_and_sanitize_question, validate_and_sanitize_answer
from storage.memory import MemoryStorage
from config import MAX_QUESTIONS_TOTAL

logger = logging.getLogger(__name__)

# Conversation states
WAITING_QUESTION = 0
WAITING_ANSWER = 1


async def add_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Start the conversation for adding a new question-answer pair.

    Sends instructions to the user and transitions to WAITING_QUESTION state.

    Args:
        update: The update object from Telegram
        context: The context object for the handler

    Returns:
        int: WAITING_QUESTION state
    """
    user = update.effective_user
    logger.info(f"User {user.id} ({user.username}) started adding a question")

    # Get storage from context
    storage: MemoryStorage = context.bot_data.get('storage')

    # Check if storage limit is reached
    if storage and storage.count() >= MAX_QUESTIONS_TOTAL:
        await update.message.reply_text(
            f"⚠️ Достигнут лимит вопросов ({MAX_QUESTIONS_TOTAL}).\n\n"
            "Пожалуйста, удалите некоторые старые вопросы перед добавлением новых.\n"
            "Используйте /list для просмотра и удаления вопросов."
        )
        return ConversationHandler.END

    message = (
        "➕ <b>Добавление нового вопроса</b>\n\n"
        "Шаг 1 из 2: Введите ваш вопрос\n\n"
        "📏 Требования:\n"
        "• Минимум 3 символа\n"
        "• Максимум 500 символов\n\n"
        "💡 Совет: Формулируйте вопрос чётко и кратко\n\n"
        "Используйте /cancel для отмены"
    )

    await update.message.reply_text(message, parse_mode='HTML')
    return WAITING_QUESTION


async def receive_question(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Receive and validate the question text from user.

    Validates the question, stores it in user context, and asks for the answer.

    Args:
        update: The update object from Telegram
        context: The context object for the handler

    Returns:
        int: WAITING_ANSWER state if valid, WAITING_QUESTION if invalid
    """
    user = update.effective_user
    question_text = update.message.text

    logger.info(f"User {user.id} provided question: {question_text[:50]}...")

    # Validate and sanitize the question
    is_valid, sanitized_question, error_message = validate_and_sanitize_question(question_text)

    if not is_valid:
        logger.warning(f"Invalid question from user {user.id}: {error_message}")
        await update.message.reply_text(
            f"❌ <b>Ошибка валидации:</b>\n\n"
            f"{error_message}\n\n"
            "Пожалуйста, попробуйте ещё раз или используйте /cancel для отмены.",
            parse_mode='HTML'
        )
        return WAITING_QUESTION

    # Store the question in user context
    context.user_data['temp_question'] = sanitized_question

    message = (
        "✅ Вопрос принят!\n\n"
        f"<b>Ваш вопрос:</b>\n{sanitized_question}\n\n"
        "Шаг 2 из 2: Теперь введите ответ\n\n"
        "📏 Требования:\n"
        "• Минимум 3 символа\n"
        "• Максимум 2000 символов\n\n"
        "💡 Совет: Дайте полный и понятный ответ\n\n"
        "Используйте /cancel для отмены"
    )

    await update.message.reply_text(message, parse_mode='HTML')
    return WAITING_ANSWER


async def receive_answer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Receive and validate the answer text, then save the Q&A pair.

    Validates the answer, saves the complete Q&A pair to storage,
    and confirms success to the user.

    Args:
        update: The update object from Telegram
        context: The context object for the handler

    Returns:
        int: ConversationHandler.END to end the conversation
    """
    user = update.effective_user
    answer_text = update.message.text

    logger.info(f"User {user.id} provided answer: {answer_text[:50]}...")

    # Validate and sanitize the answer
    is_valid, sanitized_answer, error_message = validate_and_sanitize_answer(answer_text)

    if not is_valid:
        logger.warning(f"Invalid answer from user {user.id}: {error_message}")
        await update.message.reply_text(
            f"❌ <b>Ошибка валидации:</b>\n\n"
            f"{error_message}\n\n"
            "Пожалуйста, попробуйте ещё раз или используйте /cancel для отмены.",
            parse_mode='HTML'
        )
        return WAITING_ANSWER

    # Get the question from user context
    question = context.user_data.get('temp_question')

    if not question:
        logger.error(f"Question not found in context for user {user.id}")
        await update.message.reply_text(
            "❌ Произошла ошибка: вопрос не найден.\n\n"
            "Пожалуйста, начните заново с команды /add"
        )
        return ConversationHandler.END

    # Get storage from context
    storage: MemoryStorage = context.bot_data.get('storage')

    if not storage:
        logger.error("Storage not found in bot_data")
        await update.message.reply_text(
            "❌ Произошла ошибка при сохранении.\n\n"
            "Пожалуйста, попробуйте позже."
        )
        return ConversationHandler.END

    try:
        # Save the Q&A pair to storage
        question_id = storage.add_question(question, sanitized_answer, user.id)

        logger.info(f"Question saved successfully: ID={question_id}, user={user.id}")

        # Clear temporary data
        context.user_data.pop('temp_question', None)

        # Send success message
        success_message = (
            "✅ <b>Вопрос успешно сохранён!</b>\n\n"
            f"<b>Вопрос:</b>\n{question}\n\n"
            f"<b>Ответ:</b>\n{sanitized_answer}\n\n"
            "Используйте /list чтобы увидеть все вопросы\n"
            "Используйте /add чтобы добавить ещё один вопрос"
        )

        await update.message.reply_text(success_message, parse_mode='HTML')

    except Exception as e:
        logger.error(f"Error saving question: {e}", exc_info=True)
        await update.message.reply_text(
            "❌ Произошла ошибка при сохранении вопроса.\n\n"
            "Пожалуйста, попробуйте позже."
        )

    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Cancel the current add operation.

    Clears any temporary data and informs the user that the operation was cancelled.

    Args:
        update: The update object from Telegram
        context: The context object for the handler

    Returns:
        int: ConversationHandler.END to end the conversation
    """
    user = update.effective_user
    logger.info(f"User {user.id} ({user.username}) cancelled add operation")

    # Clear temporary data
    context.user_data.pop('temp_question', None)

    await update.message.reply_text(
        "❌ Добавление вопроса отменено.\n\n"
        "Все несохранённые данные удалены.\n\n"
        "Используйте /add чтобы начать заново\n"
        "Используйте /list чтобы посмотреть существующие вопросы"
    )

    return ConversationHandler.END


def get_add_conversation_handler(storage: MemoryStorage) -> ConversationHandler:
    """
    Create and configure the ConversationHandler for adding questions.

    Args:
        storage: The MemoryStorage instance to use

    Returns:
        ConversationHandler: Configured conversation handler
    """
    return ConversationHandler(
        entry_points=[CommandHandler('add', add_start)],
        states={
            WAITING_QUESTION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_question)
            ],
            WAITING_ANSWER: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_answer)
            ],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
        name="add_conversation",
        persistent=False
    )
