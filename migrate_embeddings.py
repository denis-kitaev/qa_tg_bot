#!/usr/bin/env python3
"""
Migration script to generate embeddings for existing questions.

This script should be run after installing the semantic search dependencies
and before using the /search command for the first time.

Usage:
    python migrate_embeddings.py
"""

import sys
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


def main():
    """Run the embedding migration."""
    try:
        logger.info("=" * 60)
        logger.info("Semantic Search Embedding Migration")
        logger.info("=" * 60)

        # Import after logging is configured
        from storage.sqlite import SQLiteStorage
        from utils.semantic_search import get_search_engine
        from config import SEMANTIC_SEARCH_MODEL, SEARCH_BATCH_SIZE, SEMANTIC_SEARCH_ENABLED

        # Check if semantic search is enabled
        if not SEMANTIC_SEARCH_ENABLED:
            logger.warning("Semantic search is disabled in configuration")
            logger.warning("Set SEMANTIC_SEARCH_ENABLED=true in .env to enable it")
            return 1

        logger.info(f"Model: {SEMANTIC_SEARCH_MODEL}")
        logger.info(f"Batch size: {SEARCH_BATCH_SIZE}")
        logger.info("")

        # Initialize search engine
        logger.info("Initializing search engine...")
        search_engine = get_search_engine(SEMANTIC_SEARCH_MODEL)
        logger.info("Search engine initialized")
        logger.info("")

        # Initialize storage
        logger.info("Connecting to database...")
        storage = SQLiteStorage(db_path='sqlite.db', search_engine=search_engine)
        logger.info("Database connected")
        logger.info("")

        # Check current state
        total_questions = storage.count()
        logger.info(f"Total questions in database: {total_questions}")

        if total_questions == 0:
            logger.info("No questions found. Nothing to migrate.")
            logger.info("Add some questions first using /add command")
            return 0

        # Run migration
        logger.info("")
        logger.info("Starting migration...")
        logger.info("This may take a few minutes depending on the number of questions")
        logger.info("")

        generated_count = storage.migrate_embeddings(batch_size=SEARCH_BATCH_SIZE)

        logger.info("")
        logger.info("=" * 60)
        logger.info(f"Migration completed successfully!")
        logger.info(f"Generated {generated_count} embeddings")
        logger.info("=" * 60)
        logger.info("")
        logger.info("You can now use the /search command in the bot")

        return 0

    except KeyboardInterrupt:
        logger.info("")
        logger.warning("Migration interrupted by user")
        return 1

    except Exception as e:
        logger.error("")
        logger.error("=" * 60)
        logger.error(f"Migration failed: {e}")
        logger.error("=" * 60)
        logger.exception("Full error details:")
        return 1


if __name__ == "__main__":
    sys.exit(main())
