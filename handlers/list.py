"""
Handler for listing and viewing questions.
Handles /list command and callback queries for viewing individual questions.
"""

from telegram import Update
from telegram.ext import ContextTypes
from telegram.error import BadRequest
import logging
from storage.memory import MemoryStorage
from utils.keyboards import create_questions_keyboard, create_question_actions_keyboard

logger = logging.getLogger(__name__)


async def list_questions(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle the /list command to display all questions.

    Shows a list of all questions as inline keyboard buttons.
    If no questions exist, prompts user to add the first one.

    Args:
        update: The update object from Telegram
        context: The context object for the handler
    """
    user = update.effective_user
    logger.info(f"User {user.id} ({user.username}) requested question list")

    # Get storage from context
    storage: MemoryStorage = context.bot_data.get('storage')

    if not storage:
        logger.error("Storage not found in bot_data")
        await update.message.reply_text(
            "❌ Произошла ошибка при получении данных.\n\n"
            "Пожалуйста, попробуйте позже."
        )
        return

    # Get all questions
    questions = storage.get_all_questions()

    if not questions:
        logger.info(f"No questions found for user {user.id}")
        message = (
            "📭 <b>Список вопросов пуст</b>\n\n"
            "Пока не добавлено ни одного вопроса.\n\n"
            "Используйте /add чтобы добавить первый вопрос!"
        )
        await update.message.reply_text(message, parse_mode='HTML')
        return

    # Create message with question count
    message = (
        f"📚 <b>Список вопросов</b>\n\n"
        f"Всего вопросов: {len(questions)}\n\n"
        "Нажмите на вопрос, чтобы увидеть ответ:"
    )

    # Create keyboard with all questions
    keyboard = create_questions_keyboard(questions)

    await update.message.reply_text(
        message,
        reply_markup=keyboard,
        parse_mode='HTML'
    )

    logger.info(f"Sent list of {len(questions)} questions to user {user.id}")


async def show_question(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Display a specific question with its answer and action buttons.

    This is called when user clicks on a question from the list.
    Shows the full question text, answer, and buttons for edit/delete/back.

    Args:
        update: The update object from Telegram
        context: The context object for the handler
    """
    query = update.callback_query
    await query.answer()

    user = update.effective_user

    # Extract question_id from callback_data (format: "view_<question_id>")
    callback_data = query.data
    if not callback_data.startswith("view_"):
        logger.error(f"Invalid callback data format: {callback_data}")
        await query.edit_message_text(
            "❌ Ошибка: неверный формат данных.\n\n"
            "Пожалуйста, вернитесь к списку и попробуйте снова."
        )
        return

    question_id = callback_data[5:]  # Remove "view_" prefix
    logger.info(f"User {user.id} requested question {question_id}")

    # Get storage from context
    storage: MemoryStorage = context.bot_data.get('storage')

    if not storage:
        logger.error("Storage not found in bot_data")
        await query.edit_message_text(
            "❌ Произошла ошибка при получении данных.\n\n"
            "Пожалуйста, попробуйте позже."
        )
        return

    # Get the question data
    question_data = storage.get_question(question_id)

    if not question_data:
        logger.warning(f"Question {question_id} not found")
        await query.edit_message_text(
            "❌ <b>Вопрос не найден</b>\n\n"
            "Возможно, он был удалён.\n\n"
            "Используйте /list чтобы увидеть актуальный список.",
            parse_mode='HTML'
        )
        return

    # Format the message with question and answer
    message = (
        f"❓ <b>Вопрос:</b>\n{question_data['question']}\n\n"
        f"💡 <b>Ответ:</b>\n{question_data['answer']}\n\n"
        f"<i>Создан: {question_data['created_at'][:10]}</i>"
    )

    # Add update timestamp if question was edited
    if question_data['updated_at'] != question_data['created_at']:
        message += f"\n<i>Обновлён: {question_data['updated_at'][:10]}</i>"

    # Create action buttons
    keyboard = create_question_actions_keyboard(question_id)

    try:
        await query.edit_message_text(
            message,
            reply_markup=keyboard,
            parse_mode='HTML'
        )
        logger.info(f"Displayed question {question_id} to user {user.id}")
    except BadRequest as e:
        # Handle case where message content hasn't changed
        if "Message is not modified" in str(e):
            logger.debug(f"Message not modified for question {question_id}")
        else:
            logger.error(f"Error editing message: {e}")
            raise


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Router for callback query buttons.

    Handles various callback queries and routes them to appropriate handlers:
    - view_<id>: Show question details
    - back_to_list: Return to question list
    - edit_<id>: Start editing (to be implemented in Stage 7)
    - delete_<id>: Start deletion (to be implemented in Stage 8)

    Args:
        update: The update object from Telegram
        context: The context object for the handler
    """
    query = update.callback_query
    callback_data = query.data
    user = update.effective_user

    logger.info(f"User {user.id} triggered callback: {callback_data}")

    # Route to appropriate handler based on callback_data
    if callback_data.startswith("view_"):
        await show_question(update, context)

    elif callback_data == "back_to_list":
        await handle_back_to_list(update, context)

    elif callback_data.startswith("delete_"):
        # Route to delete handler
        from handlers.delete import delete_start
        await delete_start(update, context)

    elif callback_data.startswith("confirm_delete_"):
        # Route to confirm delete handler
        from handlers.delete import confirm_delete
        await confirm_delete(update, context)

    elif callback_data.startswith("cancel_delete_"):
        # Route to cancel delete handler
        from handlers.delete import cancel_delete
        await cancel_delete(update, context)

    elif callback_data == "new_search":
        # Route to new search handler
        from handlers.search import handle_new_search
        await handle_new_search(update, context)

    else:
        logger.warning(f"Unknown callback data: {callback_data}")
        await query.answer("❌ Неизвестная команда")


async def handle_back_to_list(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle the "back to list" button callback.

    Returns user to the list of all questions.

    Args:
        update: The update object from Telegram
        context: The context object for the handler
    """
    query = update.callback_query
    await query.answer()

    user = update.effective_user
    logger.info(f"User {user.id} returning to question list")

    # Get storage from context
    storage: MemoryStorage = context.bot_data.get('storage')

    if not storage:
        logger.error("Storage not found in bot_data")
        await query.edit_message_text(
            "❌ Произошла ошибка при получении данных.\n\n"
            "Пожалуйста, используйте /list чтобы увидеть список."
        )
        return

    # Get all questions
    questions = storage.get_all_questions()

    if not questions:
        message = (
            "📭 <b>Список вопросов пуст</b>\n\n"
            "Пока не добавлено ни одного вопроса.\n\n"
            "Используйте /add чтобы добавить первый вопрос!"
        )
        await query.edit_message_text(message, parse_mode='HTML')
        return

    # Create message with question count
    message = (
        f"📚 <b>Список вопросов</b>\n\n"
        f"Всего вопросов: {len(questions)}\n\n"
        "Нажмите на вопрос, чтобы увидеть ответ:"
    )

    # Create keyboard with all questions
    keyboard = create_questions_keyboard(questions)

    try:
        await query.edit_message_text(
            message,
            reply_markup=keyboard,
            parse_mode='HTML'
        )
        logger.info(f"Returned user {user.id} to question list")
    except BadRequest as e:
        if "Message is not modified" in str(e):
            logger.debug("Message not modified when returning to list")
        else:
            logger.error(f"Error editing message: {e}")
            raise
