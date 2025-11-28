"""
ConversationHandler for editing existing question-answer pairs.
Handles the multi-step dialog for updating question or answer text.
"""

from telegram import Update
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CallbackQueryHandler,
    MessageHandler,
    CommandHandler,
    filters
)
from telegram.error import BadRequest
import logging
from utils.validators import validate_and_sanitize_question, validate_and_sanitize_answer
from utils.keyboards import create_edit_menu_keyboard
from storage.memory import MemoryStorage

logger = logging.getLogger(__name__)

# Conversation states
EDIT_CHOICE = 0
EDIT_QUESTION = 1
EDIT_ANSWER = 2


async def edit_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Start the edit conversation by showing the edit menu.

    Displays current question and answer, then shows buttons to choose
    what to edit (question or answer).

    Args:
        update: The update object from Telegram
        context: The context object for the handler

    Returns:
        int: EDIT_CHOICE state or ConversationHandler.END on error
    """
    query = update.callback_query
    await query.answer()

    user = update.effective_user

    # Extract question_id from callback_data (format: "edit_<question_id>")
    callback_data = query.data
    if not callback_data.startswith("edit_"):
        logger.error(f"Invalid callback data format: {callback_data}")
        await query.edit_message_text(
            "❌ Ошибка: неверный формат данных.\n\n"
            "Используйте /list для возврата к списку."
        )
        return ConversationHandler.END

    question_id = callback_data[5:]  # Remove "edit_" prefix
    logger.info(f"User {user.id} started editing question {question_id}")

    # Get storage from context
    storage: MemoryStorage = context.bot_data.get('storage')

    if not storage:
        logger.error("Storage not found in bot_data")
        await query.edit_message_text(
            "❌ Произошла ошибка при получении данных.\n\n"
            "Пожалуйста, попробуйте позже."
        )
        return ConversationHandler.END

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
        return ConversationHandler.END

    # Store question_id in user context for later use
    context.user_data['editing_question_id'] = question_id

    # Display current question and edit menu
    message = (
        f"✏️ <b>Редактирование вопроса</b>\n\n"
        f"<b>Текущий вопрос:</b>\n{question_data['question']}\n\n"
        f"<b>Текущий ответ:</b>\n{question_data['answer']}\n\n"
        "Что вы хотите изменить?"
    )

    keyboard = create_edit_menu_keyboard(question_id)

    try:
        await query.edit_message_text(
            message,
            reply_markup=keyboard,
            parse_mode='HTML'
        )
    except BadRequest as e:
        if "Message is not modified" in str(e):
            logger.debug("Message not modified in edit_start")
        else:
            logger.error(f"Error editing message: {e}")
            raise

    return EDIT_CHOICE


async def edit_question_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Start editing the question text.

    Shows current question and asks user to enter new question text.

    Args:
        update: The update object from Telegram
        context: The context object for the handler

    Returns:
        int: EDIT_QUESTION state
    """
    query = update.callback_query
    await query.answer()

    user = update.effective_user

    # Extract question_id from callback_data (format: "edit_q_<question_id>")
    callback_data = query.data
    if not callback_data.startswith("edit_q_"):
        logger.error(f"Invalid callback data format: {callback_data}")
        await query.edit_message_text(
            "❌ Ошибка: неверный формат данных.\n\n"
            "Используйте /cancel для отмены."
        )
        return ConversationHandler.END

    question_id = callback_data[7:]  # Remove "edit_q_" prefix
    logger.info(f"User {user.id} started editing question text for {question_id}")

    # Get storage from context
    storage: MemoryStorage = context.bot_data.get('storage')

    if not storage:
        logger.error("Storage not found in bot_data")
        await query.edit_message_text(
            "❌ Произошла ошибка при получении данных.\n\n"
            "Используйте /cancel для отмены."
        )
        return ConversationHandler.END

    # Get the question data
    question_data = storage.get_question(question_id)

    if not question_data:
        logger.warning(f"Question {question_id} not found")
        await query.edit_message_text(
            "❌ <b>Вопрос не найден</b>\n\n"
            "Используйте /list чтобы увидеть актуальный список.",
            parse_mode='HTML'
        )
        return ConversationHandler.END

    # Store question_id in user context
    context.user_data['editing_question_id'] = question_id

    message = (
        f"📝 <b>Редактирование вопроса</b>\n\n"
        f"<b>Текущий вопрос:</b>\n{question_data['question']}\n\n"
        "Введите новый текст вопроса:\n\n"
        "📏 Требования:\n"
        "• Минимум 3 символа\n"
        "• Максимум 500 символов\n\n"
        "Используйте /cancel для отмены"
    )

    await query.edit_message_text(message, parse_mode='HTML')

    return EDIT_QUESTION


async def receive_new_question(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Receive and save the new question text.

    Validates the new question text and updates it in storage.

    Args:
        update: The update object from Telegram
        context: The context object for the handler

    Returns:
        int: ConversationHandler.END
    """
    user = update.effective_user
    new_question = update.message.text

    logger.info(f"User {user.id} provided new question: {new_question[:50]}...")

    # Validate and sanitize the new question
    is_valid, sanitized_question, error_message = validate_and_sanitize_question(new_question)

    if not is_valid:
        logger.warning(f"Invalid question from user {user.id}: {error_message}")
        await update.message.reply_text(
            f"❌ <b>Ошибка валидации:</b>\n\n"
            f"{error_message}\n\n"
            "Пожалуйста, попробуйте ещё раз или используйте /cancel для отмены.",
            parse_mode='HTML'
        )
        return EDIT_QUESTION

    # Get question_id from user context
    question_id = context.user_data.get('editing_question_id')

    if not question_id:
        logger.error(f"Question ID not found in context for user {user.id}")
        await update.message.reply_text(
            "❌ Произошла ошибка: ID вопроса не найден.\n\n"
            "Пожалуйста, начните заново с команды /list"
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
        # Update the question in storage
        success = storage.update_question(question_id, question=sanitized_question)

        if not success:
            logger.error(f"Failed to update question {question_id}")
            await update.message.reply_text(
                "❌ Не удалось обновить вопрос.\n\n"
                "Возможно, он был удалён.\n\n"
                "Используйте /list чтобы увидеть актуальный список."
            )
            return ConversationHandler.END

        logger.info(f"Question {question_id} updated successfully by user {user.id}")

        # Get updated question data
        question_data = storage.get_question(question_id)

        # Clear temporary data
        context.user_data.pop('editing_question_id', None)

        # Send success message
        success_message = (
            "✅ <b>Вопрос успешно обновлён!</b>\n\n"
            f"<b>Новый вопрос:</b>\n{question_data['question']}\n\n"
            f"<b>Ответ:</b>\n{question_data['answer']}\n\n"
            "Используйте /list чтобы вернуться к списку"
        )

        await update.message.reply_text(success_message, parse_mode='HTML')

    except Exception as e:
        logger.error(f"Error updating question: {e}", exc_info=True)
        await update.message.reply_text(
            "❌ Произошла ошибка при обновлении вопроса.\n\n"
            "Пожалуйста, попробуйте позже."
        )

    return ConversationHandler.END


async def edit_answer_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Start editing the answer text.

    Shows current answer and asks user to enter new answer text.

    Args:
        update: The update object from Telegram
        context: The context object for the handler

    Returns:
        int: EDIT_ANSWER state
    """
    query = update.callback_query
    await query.answer()

    user = update.effective_user

    # Extract question_id from callback_data (format: "edit_a_<question_id>")
    callback_data = query.data
    if not callback_data.startswith("edit_a_"):
        logger.error(f"Invalid callback data format: {callback_data}")
        await query.edit_message_text(
            "❌ Ошибка: неверный формат данных.\n\n"
            "Используйте /cancel для отмены."
        )
        return ConversationHandler.END

    question_id = callback_data[7:]  # Remove "edit_a_" prefix
    logger.info(f"User {user.id} started editing answer text for {question_id}")

    # Get storage from context
    storage: MemoryStorage = context.bot_data.get('storage')

    if not storage:
        logger.error("Storage not found in bot_data")
        await query.edit_message_text(
            "❌ Произошла ошибка при получении данных.\n\n"
            "Используйте /cancel для отмены."
        )
        return ConversationHandler.END

    # Get the question data
    question_data = storage.get_question(question_id)

    if not question_data:
        logger.warning(f"Question {question_id} not found")
        await query.edit_message_text(
            "❌ <b>Вопрос не найден</b>\n\n"
            "Используйте /list чтобы увидеть актуальный список.",
            parse_mode='HTML'
        )
        return ConversationHandler.END

    # Store question_id in user context
    context.user_data['editing_question_id'] = question_id

    message = (
        f"💬 <b>Редактирование ответа</b>\n\n"
        f"<b>Вопрос:</b>\n{question_data['question']}\n\n"
        f"<b>Текущий ответ:</b>\n{question_data['answer']}\n\n"
        "Введите новый текст ответа:\n\n"
        "📏 Требования:\n"
        "• Минимум 3 символа\n"
        "• Максимум 2000 символов\n\n"
        "Используйте /cancel для отмены"
    )

    await query.edit_message_text(message, parse_mode='HTML')

    return EDIT_ANSWER


async def receive_new_answer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Receive and save the new answer text.

    Validates the new answer text and updates it in storage.

    Args:
        update: The update object from Telegram
        context: The context object for the handler

    Returns:
        int: ConversationHandler.END
    """
    user = update.effective_user
    new_answer = update.message.text

    logger.info(f"User {user.id} provided new answer: {new_answer[:50]}...")

    # Validate and sanitize the new answer
    is_valid, sanitized_answer, error_message = validate_and_sanitize_answer(new_answer)

    if not is_valid:
        logger.warning(f"Invalid answer from user {user.id}: {error_message}")
        await update.message.reply_text(
            f"❌ <b>Ошибка валидации:</b>\n\n"
            f"{error_message}\n\n"
            "Пожалуйста, попробуйте ещё раз или используйте /cancel для отмены.",
            parse_mode='HTML'
        )
        return EDIT_ANSWER

    # Get question_id from user context
    question_id = context.user_data.get('editing_question_id')

    if not question_id:
        logger.error(f"Question ID not found in context for user {user.id}")
        await update.message.reply_text(
            "❌ Произошла ошибка: ID вопроса не найден.\n\n"
            "Пожалуйста, начните заново с команды /list"
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
        # Update the answer in storage
        success = storage.update_question(question_id, answer=sanitized_answer)

        if not success:
            logger.error(f"Failed to update answer for question {question_id}")
            await update.message.reply_text(
                "❌ Не удалось обновить ответ.\n\n"
                "Возможно, вопрос был удалён.\n\n"
                "Используйте /list чтобы увидеть актуальный список."
            )
            return ConversationHandler.END

        logger.info(f"Answer for question {question_id} updated successfully by user {user.id}")

        # Get updated question data
        question_data = storage.get_question(question_id)

        # Clear temporary data
        context.user_data.pop('editing_question_id', None)

        # Send success message
        success_message = (
            "✅ <b>Ответ успешно обновлён!</b>\n\n"
            f"<b>Вопрос:</b>\n{question_data['question']}\n\n"
            f"<b>Новый ответ:</b>\n{question_data['answer']}\n\n"
            "Используйте /list чтобы вернуться к списку"
        )

        await update.message.reply_text(success_message, parse_mode='HTML')

    except Exception as e:
        logger.error(f"Error updating answer: {e}", exc_info=True)
        await update.message.reply_text(
            "❌ Произошла ошибка при обновлении ответа.\n\n"
            "Пожалуйста, попробуйте позже."
        )

    return ConversationHandler.END


async def cancel_edit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Cancel the current edit operation.

    Clears any temporary data and informs the user that the operation was cancelled.

    Args:
        update: The update object from Telegram
        context: The context object for the handler

    Returns:
        int: ConversationHandler.END to end the conversation
    """
    user = update.effective_user
    logger.info(f"User {user.id} cancelled edit operation")

    # Clear temporary data
    context.user_data.pop('editing_question_id', None)

    await update.message.reply_text(
        "❌ Редактирование отменено.\n\n"
        "Все несохранённые изменения удалены.\n\n"
        "Используйте /list чтобы вернуться к списку вопросов"
    )

    return ConversationHandler.END


async def handle_back_to_question(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handle the back button from edit menu to return to question view.

    Args:
        update: The update object from Telegram
        context: The context object for the handler

    Returns:
        int: ConversationHandler.END
    """
    query = update.callback_query
    await query.answer()

    # Extract question_id from callback_data (format: "back_to_question_<question_id>")
    callback_data = query.data
    if not callback_data.startswith("back_to_question_"):
        logger.error(f"Invalid callback data format: {callback_data}")
        await query.edit_message_text(
            "❌ Ошибка: неверный формат данных.\n\n"
            "Используйте /list для возврата к списку."
        )
        return ConversationHandler.END

    question_id = callback_data[17:]  # Remove "back_to_question_" prefix

    # Clear temporary data
    context.user_data.pop('editing_question_id', None)

    # Import here to avoid circular dependency
    from handlers.list import show_question

    # Modify callback data to view the question
    query.data = f"view_{question_id}"
    await show_question(update, context)

    return ConversationHandler.END


def get_edit_conversation_handler() -> ConversationHandler:
    """
    Create and configure the ConversationHandler for editing questions.

    Returns:
        ConversationHandler: Configured conversation handler
    """
    return ConversationHandler(
        entry_points=[
            CallbackQueryHandler(edit_start, pattern=r'^edit_[a-f0-9\-]+$')
        ],
        states={
            EDIT_CHOICE: [
                CallbackQueryHandler(edit_question_start, pattern=r'^edit_q_[a-f0-9\-]+$'),
                CallbackQueryHandler(edit_answer_start, pattern=r'^edit_a_[a-f0-9\-]+$'),
                CallbackQueryHandler(handle_back_to_question, pattern=r'^back_to_question_[a-f0-9\-]+$'),
            ],
            EDIT_QUESTION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_new_question)
            ],
            EDIT_ANSWER: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_new_answer)
            ],
        },
        fallbacks=[CommandHandler('cancel', cancel_edit)],
        name="edit_conversation",
        persistent=False
    )
