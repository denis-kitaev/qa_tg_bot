"""
In-memory storage module for question-answer pairs.
Provides CRUD operations for managing Q&A data.
"""

import uuid
from datetime import datetime
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class MemoryStorage:
    """
    In-memory storage for question-answer pairs.

    Stores data in a dictionary with the following structure:
    {
        "question_id": {
            "question": "Question text",
            "answer": "Answer text",
            "created_at": "ISO timestamp",
            "created_by": "user_id",
            "updated_at": "ISO timestamp"
        }
    }
    """

    def __init__(self):
        """Initialize empty storage."""
        self._storage: Dict[str, Dict] = {}
        logger.info("MemoryStorage initialized")

    def add_question(self, question: str, answer: str, user_id: int) -> str:
        """
        Add a new question-answer pair to storage.

        Args:
            question: The question text
            answer: The answer text
            user_id: Telegram user ID who created the question

        Returns:
            str: The generated question ID

        Raises:
            ValueError: If question or answer is empty
        """
        if not question or not question.strip():
            raise ValueError("Question cannot be empty")
        if not answer or not answer.strip():
            raise ValueError("Answer cannot be empty")

        question_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat()

        self._storage[question_id] = {
            "question": question.strip(),
            "answer": answer.strip(),
            "created_at": timestamp,
            "created_by": user_id,
            "updated_at": timestamp
        }

        logger.info(f"Question added: ID={question_id}, user={user_id}")
        return question_id

    def get_all_questions(self) -> List[Dict]:
        """
        Get all questions from storage.

        Returns:
            List[Dict]: List of all question-answer pairs with their IDs.
                       Each dict contains: id, question, answer, created_at,
                       created_by, updated_at
        """
        questions = []
        for question_id, data in self._storage.items():
            question_data = data.copy()
            question_data["id"] = question_id
            questions.append(question_data)

        # Sort by creation date (newest first)
        questions.sort(key=lambda x: x["created_at"], reverse=True)

        logger.debug(f"Retrieved {len(questions)} questions")
        return questions

    def get_question(self, question_id: str) -> Optional[Dict]:
        """
        Get a specific question by ID.

        Args:
            question_id: The unique question identifier

        Returns:
            Optional[Dict]: Question data with ID, or None if not found.
                           Dict contains: id, question, answer, created_at,
                           created_by, updated_at
        """
        if question_id not in self._storage:
            logger.warning(f"Question not found: ID={question_id}")
            return None

        question_data = self._storage[question_id].copy()
        question_data["id"] = question_id

        logger.debug(f"Retrieved question: ID={question_id}")
        return question_data

    def update_question(self, question_id: str, question: Optional[str] = None,
                       answer: Optional[str] = None) -> bool:
        """
        Update an existing question-answer pair.

        Args:
            question_id: The unique question identifier
            question: New question text (optional, keeps old if None)
            answer: New answer text (optional, keeps old if None)

        Returns:
            bool: True if updated successfully, False if question not found

        Raises:
            ValueError: If both question and answer are None, or if provided
                       values are empty strings
        """
        if question_id not in self._storage:
            logger.warning(f"Cannot update: Question not found: ID={question_id}")
            return False

        if question is None and answer is None:
            raise ValueError("At least one of question or answer must be provided")

        if question is not None:
            if not question.strip():
                raise ValueError("Question cannot be empty")
            self._storage[question_id]["question"] = question.strip()
            logger.info(f"Question text updated: ID={question_id}")

        if answer is not None:
            if not answer.strip():
                raise ValueError("Answer cannot be empty")
            self._storage[question_id]["answer"] = answer.strip()
            logger.info(f"Answer text updated: ID={question_id}")

        self._storage[question_id]["updated_at"] = datetime.utcnow().isoformat()

        return True

    def delete_question(self, question_id: str) -> bool:
        """
        Delete a question from storage.

        Args:
            question_id: The unique question identifier

        Returns:
            bool: True if deleted successfully, False if question not found
        """
        if question_id not in self._storage:
            logger.warning(f"Cannot delete: Question not found: ID={question_id}")
            return False

        del self._storage[question_id]
        logger.info(f"Question deleted: ID={question_id}")
        return True

    def count(self) -> int:
        """
        Get the total number of questions in storage.

        Returns:
            int: Number of questions
        """
        return len(self._storage)

    def clear(self) -> None:
        """
        Clear all questions from storage.
        Warning: This operation cannot be undone!
        """
        count = len(self._storage)
        self._storage.clear()
        logger.warning(f"Storage cleared: {count} questions removed")
