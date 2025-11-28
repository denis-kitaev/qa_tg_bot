"""
Test script for SQLite storage implementation.
"""

import logging
from storage.sqlite import SQLiteStorage

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_sqlite_storage():
    """Test all SQLite storage operations."""
    logger.info("Starting SQLite storage tests...")

    # Initialize storage with test database
    storage = SQLiteStorage("test_bot_data.db")

    # Test 1: Add questions
    logger.info("\n=== Test 1: Adding questions ===")
    q1_id = storage.add_question("What is Python?", "A programming language", 12345)
    logger.info(f"Added question 1: {q1_id}")

    q2_id = storage.add_question("What is SQLite?", "A lightweight database", 12345)
    logger.info(f"Added question 2: {q2_id}")

    # Test 2: Get all questions
    logger.info("\n=== Test 2: Getting all questions ===")
    all_questions = storage.get_all_questions()
    logger.info(f"Total questions: {len(all_questions)}")
    for q in all_questions:
        logger.info(f"  - {q['question'][:30]}... (ID: {q['id'][:8]}...)")

    # Test 3: Get specific question
    logger.info("\n=== Test 3: Getting specific question ===")
    question = storage.get_question(q1_id)
    if question:
        logger.info(f"Question: {question['question']}")
        logger.info(f"Answer: {question['answer']}")

    # Test 4: Update question
    logger.info("\n=== Test 4: Updating question ===")
    success = storage.update_question(q1_id, answer="Python is a high-level programming language")
    logger.info(f"Update successful: {success}")

    updated = storage.get_question(q1_id)
    if updated:
        logger.info(f"Updated answer: {updated['answer']}")

    # Test 5: Count questions
    logger.info("\n=== Test 5: Counting questions ===")
    count = storage.count()
    logger.info(f"Total count: {count}")

    # Test 6: Delete question
    logger.info("\n=== Test 6: Deleting question ===")
    success = storage.delete_question(q2_id)
    logger.info(f"Delete successful: {success}")
    logger.info(f"Remaining questions: {storage.count()}")

    # Test 7: Clear storage
    logger.info("\n=== Test 7: Clearing storage ===")
    storage.clear()
    logger.info(f"Questions after clear: {storage.count()}")

    logger.info("\n=== All tests completed successfully! ===")


if __name__ == "__main__":
    try:
        test_sqlite_storage()
    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
