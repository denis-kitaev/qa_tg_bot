"""
SQLite storage module for question-answer pairs.
Provides persistent CRUD operations for managing Q&A data.
"""

import sqlite3
import uuid
import numpy as np
from datetime import datetime
from typing import Dict, List, Optional
import logging
from pathlib import Path
from config import SEMANTIC_SEARCH_ENABLED, SEARCH_BATCH_SIZE

logger = logging.getLogger(__name__)


class SQLiteStorage:
    """
    SQLite-based storage for question-answer pairs.

    Stores data in a SQLite database with the following schema:
    CREATE TABLE questions (
        id TEXT PRIMARY KEY,
        question TEXT NOT NULL,
        answer TEXT NOT NULL,
        created_at TEXT NOT NULL,
        created_by INTEGER NOT NULL,
        updated_at TEXT NOT NULL,
        embedding BLOB
    )
    """

    def __init__(self, db_path: str = "bot_data.db", search_engine=None):
        """
        Initialize SQLite storage.

        Args:
            db_path: Path to the SQLite database file
            search_engine: Optional SemanticSearchEngine instance for embedding generation
        """
        self.db_path = db_path
        self.search_engine = search_engine
        self._init_database()
        logger.info(f"SQLiteStorage initialized with database: {db_path}")

    def _init_database(self) -> None:
        """Create the questions table if it doesn't exist and add embedding column if needed."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Create table with embedding column
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS questions (
                    id TEXT PRIMARY KEY,
                    question TEXT NOT NULL,
                    answer TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    created_by INTEGER NOT NULL,
                    updated_at TEXT NOT NULL,
                    embedding BLOB
                )
            """)

            # Check if embedding column exists (for migration from old schema)
            cursor.execute("PRAGMA table_info(questions)")
            columns = [column[1] for column in cursor.fetchall()]

            if 'embedding' not in columns:
                logger.info("Adding embedding column to existing table")
                cursor.execute("ALTER TABLE questions ADD COLUMN embedding BLOB")
                logger.info("Embedding column added successfully")

            conn.commit()
            logger.debug("Database table initialized")

    def _get_connection(self) -> sqlite3.Connection:
        """
        Get a database connection with row factory set.

        Returns:
            sqlite3.Connection: Database connection
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def add_question(self, question: str, answer: str, user_id: int, generate_embedding: bool = True) -> str:
        """
        Add a new question-answer pair to storage with optional embedding generation.

        Args:
            question: The question text
            answer: The answer text
            user_id: Telegram user ID who created the question
            generate_embedding: Whether to generate embedding for the question

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

        # Generate embedding if enabled and search engine is available
        embedding_bytes = None
        if generate_embedding and SEMANTIC_SEARCH_ENABLED and self.search_engine:
            try:
                embedding = self.search_engine.encode(question.strip())
                embedding_bytes = embedding.astype(np.float32).tobytes()
                logger.debug(f"Generated embedding for question {question_id}")
            except Exception as e:
                logger.warning(f"Failed to generate embedding for question {question_id}: {e}")

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO questions (id, question, answer, created_at, created_by, updated_at, embedding)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (question_id, question.strip(), answer.strip(), timestamp, user_id, timestamp, embedding_bytes))
            conn.commit()

        logger.info(f"Question added: ID={question_id}, user={user_id}, embedding={'yes' if embedding_bytes else 'no'}")
        return question_id

    def get_all_questions(self, include_embeddings: bool = False) -> List[Dict]:
        """
        Get all questions from storage.

        Args:
            include_embeddings: Whether to include embeddings in the result

        Returns:
            List[Dict]: List of all question-answer pairs with their IDs.
                       Each dict contains: id, question, answer, created_at,
                       created_by, updated_at, and optionally embedding
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if include_embeddings:
                cursor.execute("""
                    SELECT id, question, answer, created_at, created_by, updated_at, embedding
                    FROM questions
                    ORDER BY created_at DESC
                """)
            else:
                cursor.execute("""
                    SELECT id, question, answer, created_at, created_by, updated_at
                    FROM questions
                    ORDER BY created_at DESC
                """)
            rows = cursor.fetchall()

        questions = [dict(row) for row in rows]
        logger.debug(f"Retrieved {len(questions)} questions (embeddings={'included' if include_embeddings else 'excluded'})")
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
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, question, answer, created_at, created_by, updated_at
                FROM questions
                WHERE id = ?
            """, (question_id,))
            row = cursor.fetchone()

        if row is None:
            logger.warning(f"Question not found: ID={question_id}")
            return None

        question_data = dict(row)
        logger.debug(f"Retrieved question: ID={question_id}")
        return question_data

    def update_question(self, question_id: str, question: Optional[str] = None,
                       answer: Optional[str] = None, regenerate_embedding: bool = True) -> bool:
        """
        Update an existing question-answer pair and optionally regenerate embedding.

        Args:
            question_id: The unique question identifier
            question: New question text (optional, keeps old if None)
            answer: New answer text (optional, keeps old if None)
            regenerate_embedding: Whether to regenerate embedding if question text changed

        Returns:
            bool: True if updated successfully, False if question not found

        Raises:
            ValueError: If both question and answer are None, or if provided
                       values are empty strings
        """
        if question is None and answer is None:
            raise ValueError("At least one of question or answer must be provided")

        # Check if question exists
        existing = self.get_question(question_id)
        if existing is None:
            logger.warning(f"Cannot update: Question not found: ID={question_id}")
            return False

        # Validate inputs
        if question is not None and not question.strip():
            raise ValueError("Question cannot be empty")
        if answer is not None and not answer.strip():
            raise ValueError("Answer cannot be empty")

        # Build update query dynamically
        updates = []
        params = []

        if question is not None:
            updates.append("question = ?")
            params.append(question.strip())
            logger.info(f"Question text updated: ID={question_id}")

            # Regenerate embedding if question text changed
            if regenerate_embedding and SEMANTIC_SEARCH_ENABLED and self.search_engine:
                try:
                    embedding = self.search_engine.encode(question.strip())
                    embedding_bytes = embedding.astype(np.float32).tobytes()
                    updates.append("embedding = ?")
                    params.append(embedding_bytes)
                    logger.debug(f"Regenerated embedding for question {question_id}")
                except Exception as e:
                    logger.warning(f"Failed to regenerate embedding for question {question_id}: {e}")

        if answer is not None:
            updates.append("answer = ?")
            params.append(answer.strip())
            logger.info(f"Answer text updated: ID={question_id}")

        updates.append("updated_at = ?")
        params.append(datetime.utcnow().isoformat())
        params.append(question_id)

        with self._get_connection() as conn:
            cursor = conn.cursor()
            query = f"UPDATE questions SET {', '.join(updates)} WHERE id = ?"
            cursor.execute(query, params)
            conn.commit()


    def migrate_embeddings(self, batch_size: int = SEARCH_BATCH_SIZE) -> int:
        """
        Generate embeddings for all questions that don't have them.

        Args:
            batch_size: Number of questions to process at once

        Returns:
            int: Number of embeddings generated
        """
        if not SEMANTIC_SEARCH_ENABLED or not self.search_engine:
            logger.warning("Semantic search not enabled or search engine not available")
            return 0

        logger.info("Starting embedding migration...")

        # Get questions without embeddings
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, question
                FROM questions
                WHERE embedding IS NULL
            """)
            rows = cursor.fetchall()

        if not rows:
            logger.info("No questions need embedding generation")
            return 0

        questions_to_process = [(row['id'], row['question']) for row in rows]
        total = len(questions_to_process)
        logger.info(f"Found {total} questions without embeddings")

        # Process in batches
        generated_count = 0
        for i in range(0, total, batch_size):
            batch = questions_to_process[i:i + batch_size]
            batch_ids = [q[0] for q in batch]
            batch_texts = [q[1] for q in batch]

            try:
                # Generate embeddings for batch
                logger.info(f"Processing batch {i//batch_size + 1}/{(total + batch_size - 1)//batch_size}")
                embeddings = self.search_engine.encode_batch(
                    batch_texts,
                    batch_size=batch_size,
                    show_progress=True
                )

                # Update database
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    for question_id, embedding in zip(batch_ids, embeddings):
                        embedding_bytes = embedding.astype(np.float32).tobytes()
                        cursor.execute(
                            "UPDATE questions SET embedding = ? WHERE id = ?",
                            (embedding_bytes, question_id)
                        )
                    conn.commit()

                generated_count += len(batch)
                logger.info(f"Generated {generated_count}/{total} embeddings")

            except Exception as e:
                logger.error(f"Failed to process batch: {e}")
                continue

        logger.info(f"Migration complete: {generated_count} embeddings generated")
        return generated_count

    def get_all_questions_with_embeddings(self) -> List[Dict]:
        """
        Get all questions with their embeddings for search.

        Returns:
            List[Dict]: List of questions with embeddings
        """
        return self.get_all_questions(include_embeddings=True)

    def search_questions(
        self,
        query: str,
        top_k: int = None,
        threshold: float = None
    ) -> List[Dict]:
        """
        Search questions using semantic similarity.

        Args:
            query: Search query text
            top_k: Number of top results to return (uses config default if None)
            threshold: Minimum similarity score (uses config default if None)

        Returns:
            List of matching questions with scores, sorted by relevance
        """
        if not SEMANTIC_SEARCH_ENABLED or not self.search_engine:
            logger.warning("Semantic search not enabled or search engine not available")
            return []

        # Get all questions with embeddings
        candidates = self.get_all_questions_with_embeddings()

        if not candidates:
            logger.warning("No questions available for search")
            return []

        # Use search engine to find similar questions
        from config import SEARCH_TOP_K, SEARCH_SIMILARITY_THRESHOLD
        results = self.search_engine.search(
            query=query,
            candidates=candidates,
            top_k=top_k or SEARCH_TOP_K,
            threshold=threshold or SEARCH_SIMILARITY_THRESHOLD
        )

        return results
        return True

    def delete_question(self, question_id: str) -> bool:
        """
        Delete a question from storage.

        Args:
            question_id: The unique question identifier

        Returns:
            bool: True if deleted successfully, False if question not found
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM questions WHERE id = ?", (question_id,))
            conn.commit()
            deleted = cursor.rowcount > 0

        if not deleted:
            logger.warning(f"Cannot delete: Question not found: ID={question_id}")
            return False

        logger.info(f"Question deleted: ID={question_id}")
        return True

    def count(self) -> int:
        """
        Get the total number of questions in storage.

        Returns:
            int: Number of questions
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM questions")
            count = cursor.fetchone()[0]

        return count

    def clear(self) -> None:
        """
        Clear all questions from storage.
        Warning: This operation cannot be undone!
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM questions")
            count = cursor.fetchone()[0]
            cursor.execute("DELETE FROM questions")
            conn.commit()

        logger.warning(f"Storage cleared: {count} questions removed")
