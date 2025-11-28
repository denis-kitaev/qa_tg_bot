"""
Validation utilities for user input.
Provides functions to validate question and answer text.
"""

import re
import logging
from typing import Tuple
from config import MAX_QUESTION_LENGTH, MAX_ANSWER_LENGTH

logger = logging.getLogger(__name__)


def validate_question_length(text: str) -> Tuple[bool, str]:
    """
    Validate the length of a question text.

    Args:
        text: The question text to validate

    Returns:
        Tuple[bool, str]: (is_valid, error_message)
                         If valid: (True, "")
                         If invalid: (False, "error description")
    """
    if not text or not text.strip():
        return False, "Вопрос не может быть пустым"

    text = text.strip()

    if len(text) < 3:
        return False, "Вопрос слишком короткий (минимум 3 символа)"

    if len(text) > MAX_QUESTION_LENGTH:
        return False, f"Вопрос слишком длинный (максимум {MAX_QUESTION_LENGTH} символов, у вас {len(text)})"

    logger.debug(f"Question validated: length={len(text)}")
    return True, ""


def validate_answer_length(text: str) -> Tuple[bool, str]:
    """
    Validate the length of an answer text.

    Args:
        text: The answer text to validate

    Returns:
        Tuple[bool, str]: (is_valid, error_message)
                         If valid: (True, "")
                         If invalid: (False, "error description")
    """
    if not text or not text.strip():
        return False, "Ответ не может быть пустым"

    text = text.strip()

    if len(text) < 3:
        return False, "Ответ слишком короткий (минимум 3 символа)"

    if len(text) > MAX_ANSWER_LENGTH:
        return False, f"Ответ слишком длинный (максимум {MAX_ANSWER_LENGTH} символов, у вас {len(text)})"

    logger.debug(f"Answer validated: length={len(text)}")
    return True, ""


def sanitize_text(text: str) -> str:
    """
    Sanitize text by removing or escaping potentially dangerous characters.

    This function:
    - Strips leading/trailing whitespace
    - Removes null bytes
    - Normalizes whitespace (multiple spaces to single space)
    - Removes control characters except newlines and tabs

    Args:
        text: The text to sanitize

    Returns:
        str: Sanitized text
    """
    if not text:
        return ""

    # Strip leading/trailing whitespace
    text = text.strip()

    # Remove null bytes
    text = text.replace('\x00', '')

    # Remove other control characters except newline and tab
    # Control characters are in range 0x00-0x1F except \n (0x0A) and \t (0x09)
    text = ''.join(char for char in text
                   if char == '\n' or char == '\t' or ord(char) >= 0x20)

    # Normalize multiple spaces to single space (but preserve newlines)
    lines = text.split('\n')
    lines = [' '.join(line.split()) for line in lines]
    text = '\n'.join(lines)

    logger.debug(f"Text sanitized: original_length={len(text)}")
    return text


def validate_and_sanitize_question(text: str) -> Tuple[bool, str, str]:
    """
    Validate and sanitize a question text in one step.

    Args:
        text: The question text to validate and sanitize

    Returns:
        Tuple[bool, str, str]: (is_valid, sanitized_text, error_message)
                               If valid: (True, sanitized_text, "")
                               If invalid: (False, "", error_description)
    """
    sanitized = sanitize_text(text)
    is_valid, error = validate_question_length(sanitized)

    if is_valid:
        return True, sanitized, ""
    else:
        return False, "", error


def validate_and_sanitize_answer(text: str) -> Tuple[bool, str, str]:
    """
    Validate and sanitize an answer text in one step.

    Args:
        text: The answer text to validate and sanitize

    Returns:
        Tuple[bool, str, str]: (is_valid, sanitized_text, error_message)
                               If valid: (True, sanitized_text, "")
                               If invalid: (False, "", error_description)
    """
    sanitized = sanitize_text(text)
    is_valid, error = validate_answer_length(sanitized)

    if is_valid:
        return True, sanitized, ""
    else:
        return False, "", error


def is_valid_question_id(question_id: str) -> bool:
    """
    Check if a string is a valid UUID question ID.

    Args:
        question_id: The ID to validate

    Returns:
        bool: True if valid UUID format, False otherwise
    """
    if not question_id:
        return False

    # UUID v4 pattern
    uuid_pattern = re.compile(
        r'^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$',
        re.IGNORECASE
    )

    return bool(uuid_pattern.match(question_id))
