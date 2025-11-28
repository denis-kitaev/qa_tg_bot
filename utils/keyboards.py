"""
Keyboard generation utilities for Telegram bot.
Provides functions to create inline keyboards for various bot interactions.
"""

from typing import List, Dict
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
import logging

logger = logging.getLogger(__name__)


def create_questions_keyboard(questions: List[Dict]) -> InlineKeyboardMarkup:
    """
    Create an inline keyboard with a list of questions.

    Each question becomes a button that shows the question text (truncated if too long)
    and triggers a callback to view the full question and answer.

    Args:
        questions: List of question dictionaries, each containing at least 'id' and 'question'

    Returns:
        InlineKeyboardMarkup: Keyboard with question buttons
    """
    keyboard = []

    for idx, question in enumerate(questions, 1):
        question_id = question.get('id')
        question_text = question.get('question', 'Без названия')

        # Truncate long questions for button display
        max_button_length = 60
        if len(question_text) > max_button_length:
            display_text = question_text[:max_button_length - 3] + "..."
        else:
            display_text = question_text

        # Add number prefix for easier navigation
        button_text = f"{idx}. {display_text}"

        # Create button with callback data to view this question
        button = InlineKeyboardButton(
            text=button_text,
            callback_data=f"view_{question_id}"
        )

        # Each question gets its own row
        keyboard.append([button])

    logger.debug(f"Created questions keyboard with {len(questions)} buttons")
    return InlineKeyboardMarkup(keyboard)


def create_question_actions_keyboard(question_id: str) -> InlineKeyboardMarkup:
    """
    Create an inline keyboard with action buttons for a specific question.

    Provides buttons to edit, delete, or go back to the list.

    Args:
        question_id: The unique identifier of the question

    Returns:
        InlineKeyboardMarkup: Keyboard with action buttons
    """
    keyboard = [
        [
            InlineKeyboardButton("✏️ Редактировать", callback_data=f"edit_{question_id}"),
            InlineKeyboardButton("🗑️ Удалить", callback_data=f"delete_{question_id}")
        ],
        [
            InlineKeyboardButton("⬅️ К списку", callback_data="back_to_list")
        ]
    ]

    logger.debug(f"Created action keyboard for question {question_id}")
    return InlineKeyboardMarkup(keyboard)


def create_edit_menu_keyboard(question_id: str) -> InlineKeyboardMarkup:
    """
    Create an inline keyboard for choosing what to edit (question or answer).

    Args:
        question_id: The unique identifier of the question

    Returns:
        InlineKeyboardMarkup: Keyboard with edit options
    """
    keyboard = [
        [
            InlineKeyboardButton("📝 Изменить вопрос", callback_data=f"edit_q_{question_id}")
        ],
        [
            InlineKeyboardButton("💬 Изменить ответ", callback_data=f"edit_a_{question_id}")
        ],
        [
            InlineKeyboardButton("❌ Отмена", callback_data=f"back_to_question_{question_id}")
        ]
    ]

    logger.debug(f"Created edit menu keyboard for question {question_id}")
    return InlineKeyboardMarkup(keyboard)


def create_delete_confirmation_keyboard(question_id: str) -> InlineKeyboardMarkup:
    """
    Create an inline keyboard for confirming deletion of a question.

    Args:
        question_id: The unique identifier of the question to delete

    Returns:
        InlineKeyboardMarkup: Keyboard with confirmation buttons
    """
    keyboard = [
        [
            InlineKeyboardButton("✅ Да, удалить", callback_data=f"confirm_delete_{question_id}"),
            InlineKeyboardButton("❌ Отмена", callback_data=f"cancel_delete_{question_id}")
        ]
    ]

    logger.debug(f"Created delete confirmation keyboard for question {question_id}")
    return InlineKeyboardMarkup(keyboard)


def create_back_button() -> InlineKeyboardMarkup:
    """
    Create a simple keyboard with just a back button to return to the list.

    Returns:
        InlineKeyboardMarkup: Keyboard with a single back button
    """
    keyboard = [
        [
            InlineKeyboardButton("⬅️ К списку", callback_data="back_to_list")
        ]
    ]

    logger.debug("Created back button keyboard")
    return InlineKeyboardMarkup(keyboard)


def create_pagination_keyboard(
    current_page: int,
    total_pages: int,
    prefix: str = "page"
) -> InlineKeyboardMarkup:
    """
    Create a pagination keyboard for navigating through multiple pages.

    This is an optional helper function for future pagination support.

    Args:
        current_page: Current page number (1-indexed)
        total_pages: Total number of pages
        prefix: Prefix for callback data (default: "page")

    Returns:
        InlineKeyboardMarkup: Keyboard with pagination buttons
    """
    keyboard = []
    buttons = []

    # Previous button
    if current_page > 1:
        buttons.append(
            InlineKeyboardButton("⬅️ Назад", callback_data=f"{prefix}_{current_page - 1}")
        )

    # Page indicator
    buttons.append(
        InlineKeyboardButton(f"📄 {current_page}/{total_pages}", callback_data="noop")
    )

    # Next button
    if current_page < total_pages:
        buttons.append(
            InlineKeyboardButton("Вперёд ➡️", callback_data=f"{prefix}_{current_page + 1}")
        )

    if buttons:
        keyboard.append(buttons)

    # Back to list button
    keyboard.append([
        InlineKeyboardButton("⬅️ К списку", callback_data="back_to_list")
    ])

    logger.debug(f"Created pagination keyboard: page {current_page}/{total_pages}")
    return InlineKeyboardMarkup(keyboard)
