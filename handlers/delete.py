"""
Handler for deleting questions.
Handles the deletion confirmation flow with callbacks.
"""

from telegram import Update
from telegram.ext import ContextTypes
from telegram.error import BadRequest
import logging
from storage.memory import MemoryStorage
from utils.keyboards import create_delete_confirmation_keyboard

logger = logging.getLogger(__name__)


async def delete_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Start the deletion process by showing confirmation dialog.

    Displays the question that will be deleted and asks for confirmation.

    Args:
        update: The update object from Telegram
        context: The context object for the handler
    """
    query = update.callback_query
    await query.answer()

    user = update.effective_user

    # Extract question_id from callback_data (format: "delete_<question_id>")
    callback_data = query.data
    if not callback_data.startswith("delete_"):
        logger.error(f"Invalid callback data format: {callback_data}")
        await query.edit_message_text(
            "❌ Ошибка: неверный формат данных.\n\n"
            "Используйте /list для возврата к списку."
        )
        return

    question_id = callback_data[7:]  # Remove "delete_" prefix
    logger.info(f"User {user.id} initiated deletion for question {question_id}")

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
            "Возможно, он уже был удалён.\n\n"
            "Используйте /list чтобы увидеть актуальный список.",
            parse_mode='HTML'
        )
        return

    # Show confirmation dialog
    message = (
        f"🗑️ <b>Подтверждение удаления</b>\n\n"
        f"⚠️ <b>Внимание!</b> Это действие необратимо.\n\n"
        f"<b>Вопрос:</b>\n{question_data['question']}\n\n"
        f"<b>Ответ:</b>\n{question_data['answer']}\n\n"
        "Вы уверены, что хотите удалить этот вопрос?"
    )

    keyboard = create_delete_confirmation_keyboard(question_id)

    try:
        await query.edit_message_text(
            message,
            reply_markup=keyboard,
            parse_mode='HTML'
        )
        logger.info(f"Displayed delete confirmation for question {question_id}")
    except BadRequest as e:
        if "Message is not modified" in str(e):
            logger.debug("Message not modified in delete_start")
        else:
            logger.error(f"Error editing message: {e}")
            raise


async def confirm_delete(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Execute the deletion after user confirmation.

    Deletes the question from storage and shows success message.

    Args:
        update: The update object from Telegram
        context: The context object for the handler
    """
    query = update.callback_query
    await query.answer()

    user = update.effective_user

    # Extract question_id from callback_data (format: "confirm_delete_<question_id>")
    callback_data = query.data
    if not callback_data.startswith("confirm_delete_"):
        logger.error(f"Invalid callback data format: {callback_data}")
        await query.edit_message_text(
            "❌ Ошибка: неверный формат данных.\n\n"
            "Используйте /list для возврата к списку."
        )
        return

    question_id = callback_data[15:]  # Remove "confirm_delete_" prefix
    logger.info(f"User {user.id} confirmed deletion for question {question_id}")

    # Get storage from context
    storage: MemoryStorage = context.bot_data.get('storage')

    if not storage:
        logger.error("Storage not found in bot_data")
        await query.edit_message_text(
            "❌ Произошла ошибка при удалении.\n\n"
            "Пожалуйста, попробуйте позже."
        )
        return

    # Get question data before deletion (for confirmation message)
    question_data = storage.get_question(question_id)

    if not question_data:
        logger.warning(f"Question {question_id} not found")
        await query.edit_message_text(
            "❌ <b>Вопрос не найден</b>\n\n"
            "Возможно, он уже был удалён.\n\n"
            "Используйте /list чтобы увидеть актуальный список.",
            parse_mode='HTML'
        )
        return

    # Store question text for success message
    question_text = question_data['question']

    # Delete the question
    success = storage.delete_question(question_id)

    if not success:
        logger.error(f"Failed to delete question {question_id}")
        await query.edit_message_text(
            "❌ Не удалось удалить вопрос.\n\n"
            "Пожалуйста, попробуйте позже."
        )
        return

    logger.info(f"Question {question_id} deleted successfully by user {user.id}")

    # Show success message
    success_message = (
        f"✅ <b>Вопрос успешно удалён!</b>\n\n"
        f"<b>Удалённый вопрос:</b>\n{question_text}\n\n"
        "Используйте /list чтобы вернуться к списку вопросов"
    )

    await query.edit_message_text(success_message, parse_mode='HTML')


async def cancel_delete(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Cancel the deletion and return to question view.

    Args:
        update: The update object from Telegram
        context: The context object for the handler
    """
    query = update.callback_query
    await query.answer()

    user = update.effective_user

    # Extract question_id from callback_data (format: "cancel_delete_<question_id>")
    callback_data = query.data
    if not callback_data.startswith("cancel_delete_"):
        logger.error(f"Invalid callback data format: {callback_data}")
        await query.edit_message_text(
            "❌ Ошибка: неверный формат данных.\n\n"
            "Используйте /list для возврата к списку."
        )
        return

    question_id = callback_data[14:]  # Remove "cancel_delete_" prefix
    logger.info(f"User {user.id} cancelled deletion for question {question_id}")

    # Import here to avoid circular dependency
    from handlers.list import show_question

    # Modify callback data to view the question
    query.data = f"view_{question_id}"
    await show_question(update, context)
