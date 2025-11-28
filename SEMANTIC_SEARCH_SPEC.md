# Semantic Search Technical Specification

## 1. API Design

### 1.1 SemanticSearchEngine Class

```python
class SemanticSearchEngine:
    """
    Semantic search engine using sentence-transformers for embedding-based similarity search.

    Features:
    - Singleton pattern for model caching
    - Lazy loading of model
    - Cosine similarity computation
    - Configurable similarity threshold
    """

    _instance = None
    _model = None

    def __new__(cls, model_name: str = None):
        """Singleton pattern implementation"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, model_name: str = None):
        """
        Initialize semantic search engine.

        Args:
            model_name: Name of sentence-transformer model to use
        """
        if model_name and self._model is None:
            self.model_name = model_name
            self._load_model()

    def _load_model(self) -> None:
        """Load sentence-transformer model (lazy loading)"""
        pass

    def encode(self, text: str) -> np.ndarray:
        """
        Generate embedding for text.

        Args:
            text: Input text to encode

        Returns:
            numpy array of shape (embedding_dim,)
        """
        pass

    def search(
        self,
        query: str,
        candidates: List[Dict],
        top_k: int = 5,
        threshold: float = 0.3
    ) -> List[Dict]:
        """
        Search for similar questions using semantic similarity.

        Args:
            query: Search query text
            candidates: List of question dicts with 'id', 'question', 'embedding'
            top_k: Number of top results to return
            threshold: Minimum similarity score (0-1)

        Returns:
            List of dicts with 'id', 'question', 'answer', 'score' sorted by score
        """
        pass

    def compute_similarity(
        self,
        query_embedding: np.ndarray,
        doc_embeddings: np.ndarray
    ) -> np.ndarray:
        """
        Compute cosine similarity between query and documents.

        Args:
            query_embedding: Query embedding of shape (embedding_dim,)
            doc_embeddings: Document embeddings of shape (n_docs, embedding_dim)

        Returns:
            Similarity scores of shape (n_docs,)
        """
        pass
```

### 1.2 Storage Extension

```python
class SQLiteStorage:
    """Extended SQLite storage with embedding support"""

    def __init__(self, db_path: str = "bot_data.db", search_engine: SemanticSearchEngine = None):
        """
        Initialize storage with optional search engine.

        Args:
            db_path: Path to SQLite database
            search_engine: Optional semantic search engine instance
        """
        self.db_path = db_path
        self.search_engine = search_engine
        self._init_database()

    def _init_database(self) -> None:
        """Create tables with embedding column"""
        # CREATE TABLE with embedding BLOB column
        pass

    def add_question(
        self,
        question: str,
        answer: str,
        user_id: int,
        generate_embedding: bool = True
    ) -> str:
        """
        Add question with automatic embedding generation.

        Args:
            question: Question text
            answer: Answer text
            user_id: User ID
            generate_embedding: Whether to generate embedding

        Returns:
            Question ID
        """
        pass

    def update_question(
        self,
        question_id: str,
        question: Optional[str] = None,
        answer: Optional[str] = None,
        regenerate_embedding: bool = True
    ) -> bool:
        """
        Update question and regenerate embedding if question text changed.

        Args:
            question_id: Question ID
            question: New question text (optional)
            answer: New answer text (optional)
            regenerate_embedding: Whether to regenerate embedding

        Returns:
            True if successful
        """
        pass

    def get_all_questions_with_embeddings(self) -> List[Dict]:
        """
        Get all questions with their embeddings.

        Returns:
            List of dicts with 'id', 'question', 'answer', 'embedding'
        """
        pass

    def migrate_embeddings(self, batch_size: int = 10) -> int:
        """
        Generate embeddings for all questions without embeddings.

        Args:
            batch_size: Number of questions to process at once

        Returns:
            Number of embeddings generated
        """
        pass

    def search_questions(
        self,
        query: str,
        top_k: int = 5,
        threshold: float = 0.3
    ) -> List[Dict]:
        """
        Search questions using semantic similarity.

        Args:
            query: Search query
            top_k: Number of results
            threshold: Minimum similarity

        Returns:
            List of matching questions with scores
        """
        pass
```

### 1.3 Search Handler

```python
# States
WAITING_SEARCH_QUERY = 0

async def search_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Start search conversation.

    Returns:
        WAITING_SEARCH_QUERY state
    """
    pass

async def search_query(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Process search query and display results.

    Returns:
        ConversationHandler.END
    """
    pass

async def search_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Cancel search operation.

    Returns:
        ConversationHandler.END
    """
    pass

def get_search_conversation_handler() -> ConversationHandler:
    """
    Create and return search conversation handler.

    Returns:
        ConversationHandler for search
    """
    pass
```

## 2. Database Schema

### 2.1 Migration SQL

```sql
-- Add embedding column to existing table
ALTER TABLE questions ADD COLUMN embedding BLOB;

-- Create index for faster retrieval (optional)
CREATE INDEX IF NOT EXISTS idx_questions_id ON questions(id);

-- Check if migration is needed
SELECT COUNT(*) FROM questions WHERE embedding IS NULL;
```

### 2.2 Embedding Storage Format

```python
# Serialize embedding to bytes
embedding_bytes = embedding.astype(np.float32).tobytes()

# Store in database
cursor.execute(
    "UPDATE questions SET embedding = ? WHERE id = ?",
    (embedding_bytes, question_id)
)

# Deserialize from bytes
embedding = np.frombuffer(embedding_bytes, dtype=np.float32)
```

## 3. Configuration

### 3.1 New Config Parameters

```python
# config.py additions

# Semantic Search Configuration
SEMANTIC_SEARCH_ENABLED = os.getenv('SEMANTIC_SEARCH_ENABLED', 'true').lower() == 'true'
SEMANTIC_SEARCH_MODEL = os.getenv(
    'SEMANTIC_SEARCH_MODEL',
    'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2'
)
SEARCH_TOP_K = int(os.getenv('SEARCH_TOP_K', '5'))
SEARCH_SIMILARITY_THRESHOLD = float(os.getenv('SEARCH_SIMILARITY_THRESHOLD', '0.3'))
SEARCH_CACHE_MODEL = os.getenv('SEARCH_CACHE_MODEL', 'true').lower() == 'true'
SEARCH_BATCH_SIZE = int(os.getenv('SEARCH_BATCH_SIZE', '10'))

# Model paths
MODEL_CACHE_DIR = os.getenv('MODEL_CACHE_DIR', './models')
```

### 3.2 Environment Variables

```bash
# .env additions
SEMANTIC_SEARCH_ENABLED=true
SEMANTIC_SEARCH_MODEL=sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
SEARCH_TOP_K=5
SEARCH_SIMILARITY_THRESHOLD=0.3
SEARCH_CACHE_MODEL=true
SEARCH_BATCH_SIZE=10
MODEL_CACHE_DIR=./models
```

## 4. User Interface Specifications

### 4.1 Search Command Flow

```
┌─────────────────────────────────────┐
│ User: /search                       │
└─────────────────────────────────────┘
           ↓
┌─────────────────────────────────────┐
│ Bot: 🔍 Введите поисковый запрос:   │
│                                     │
│ Например:                           │
│ • как установить python             │
│ • что такое API                     │
│ • настройка git                     │
│                                     │
│ [Отмена]                            │
└─────────────────────────────────────┘
           ↓
┌─────────────────────────────────────┐
│ User: как установить python         │
└─────────────────────────────────────┘
           ↓
┌─────────────────────────────────────┐
│ Bot: 🔍 Поиск...                    │
└─────────────────────────────────────┘
           ↓
┌─────────────────────────────────────┐
│ Bot: 📊 Найдено 3 результата:       │
│                                     │
│ 1. ⭐ 95% - Как установить Python?  │
│    💡 Скачайте с python.org...      │
│    [Показать полностью]             │
│                                     │
│ 2. ⭐ 78% - Установка Python на Win │
│    💡 Для Windows скачайте...       │
│    [Показать полностью]             │
│                                     │
│ 3. ⭐ 65% - Настройка окружения     │
│    💡 После установки...            │
│    [Показать полностью]             │
│                                     │
│ [Новый поиск] [К списку]            │
└─────────────────────────────────────┘
```

### 4.2 No Results Flow

```
┌─────────────────────────────────────┐
│ Bot: 😕 Ничего не найдено           │
│                                     │
│ По запросу "xyz" не найдено         │
│ подходящих вопросов.                │
│                                     │
│ Попробуйте:                         │
│ • Изменить формулировку             │
│ • Использовать другие слова         │
│ • Просмотреть все вопросы /list     │
│                                     │
│ [Новый поиск] [К списку]            │
└─────────────────────────────────────┘
```

### 4.3 Message Templates

```python
# Search prompt
SEARCH_PROMPT = (
    "🔍 <b>Поиск по вопросам</b>\n\n"
    "Введите поисковый запрос:\n\n"
    "<i>Например:</i>\n"
    "• как установить python\n"
    "• что такое API\n"
    "• настройка git\n\n"
    "Используйте /cancel для отмены"
)

# Search results header
SEARCH_RESULTS_HEADER = (
    "📊 <b>Результаты поиска</b>\n\n"
    "Найдено {count} {results_word}:\n"
)

# Single result format
SEARCH_RESULT_ITEM = (
    "{number}. ⭐ {score}% - {question}\n"
    "   💡 {answer_preview}...\n"
)

# No results message
NO_RESULTS_MESSAGE = (
    "😕 <b>Ничего не найдено</b>\n\n"
    "По запросу \"{query}\" не найдено подходящих вопросов.\n\n"
    "Попробуйте:\n"
    "• Изменить формулировку\n"
    "• Использовать другие слова\n"
    "• Просмотреть все вопросы /list"
)

# Search in progress
SEARCH_IN_PROGRESS = "🔍 Поиск..."
```

## 5. Performance Specifications

### 5.1 Timing Requirements

| Operation | Target Time | Maximum Time |
|-----------|-------------|--------------|
| Model Loading (first time) | < 3s | < 5s |
| Model Loading (cached) | < 0.5s | < 1s |
| Query Embedding | < 100ms | < 200ms |
| Similarity Computation (100 questions) | < 5ms | < 10ms |
| Total Search Time | < 200ms | < 500ms |

### 5.2 Memory Requirements

| Component | Memory Usage |
|-----------|--------------|
| Model (loaded) | ~500MB |
| Embeddings (100 questions) | ~150KB |
| Query Processing | ~10MB |
| **Total** | **~510MB** |

### 5.3 Disk Requirements

| Component | Disk Space |
|-----------|------------|
| Model Files | ~420MB |
| Dependencies | ~250MB |
| Database (embeddings) | ~150KB |
| **Total** | **~670MB** |

## 6. Error Handling Specifications

### 6.1 Error Types and Responses

```python
class SearchError(Exception):
    """Base exception for search errors"""
    pass

class ModelLoadError(SearchError):
    """Model loading failed"""
    pass

class EmbeddingError(SearchError):
    """Embedding generation failed"""
    pass

class SearchQueryError(SearchError):
    """Invalid search query"""
    pass

# Error messages
ERROR_MESSAGES = {
    'model_load': (
        "❌ <b>Ошибка загрузки модели</b>\n\n"
        "Не удалось загрузить модель для поиска.\n"
        "Попробуйте позже или используйте /list"
    ),
    'embedding_generation': (
        "❌ <b>Ошибка обработки запроса</b>\n\n"
        "Не удалось обработать ваш запрос.\n"
        "Попробуйте еще раз или используйте /list"
    ),
    'empty_query': (
        "⚠️ <b>Пустой запрос</b>\n\n"
        "Пожалуйста, введите текст для поиска."
    ),
    'query_too_long': (
        "⚠️ <b>Запрос слишком длинный</b>\n\n"
        "Максимальная длина запроса: {max_length} символов."
    ),
    'search_disabled': (
        "⚠️ <b>Поиск недоступен</b>\n\n"
        "Семантический поиск временно отключен.\n"
        "Используйте /list для просмотра вопросов."
    )
}
```

### 6.2 Graceful Degradation

```python
def search_with_fallback(query: str) -> List[Dict]:
    """
    Search with fallback to simple text search.

    Priority:
    1. Try semantic search
    2. Fall back to keyword search
    3. Fall back to showing all questions
    """
    try:
        # Try semantic search
        results = semantic_search(query)
        if results:
            return results
    except ModelLoadError:
        logger.warning("Model not available, using keyword search")
    except Exception as e:
        logger.error(f"Semantic search failed: {e}")

    # Fallback to keyword search
    try:
        results = keyword_search(query)
        if results:
            return results
    except Exception as e:
        logger.error(f"Keyword search failed: {e}")

    # Last resort: return all questions
    return get_all_questions()
```

## 7. Testing Specifications

### 7.1 Unit Test Cases

```python
class TestSemanticSearchEngine:
    def test_model_loading(self):
        """Test model loads successfully"""
        pass

    def test_embedding_generation(self):
        """Test embedding generation for text"""
        pass

    def test_similarity_computation(self):
        """Test cosine similarity calculation"""
        pass

    def test_search_ranking(self):
        """Test results are ranked by similarity"""
        pass

    def test_threshold_filtering(self):
        """Test results below threshold are filtered"""
        pass

    def test_singleton_pattern(self):
        """Test only one model instance is created"""
        pass

class TestStorageExtension:
    def test_add_question_with_embedding(self):
        """Test question is added with embedding"""
        pass

    def test_update_question_regenerates_embedding(self):
        """Test embedding is regenerated on update"""
        pass

    def test_migration_generates_embeddings(self):
        """Test migration creates embeddings for existing questions"""
        pass

    def test_search_returns_results(self):
        """Test search returns relevant results"""
        pass
```

### 7.2 Integration Test Scenarios

```python
class TestSearchIntegration:
    def test_search_flow_end_to_end(self):
        """Test complete search flow from command to results"""
        pass

    def test_search_with_no_results(self):
        """Test search with query that matches nothing"""
        pass

    def test_search_with_exact_match(self):
        """Test search with exact question text"""
        pass

    def test_search_with_paraphrase(self):
        """Test search with paraphrased question"""
        pass

    def test_search_with_typos(self):
        """Test search handles typos gracefully"""
        pass

    def test_search_multilingual(self):
        """Test search works with Russian and English"""
        pass
```

### 7.3 Manual Test Cases

| Test Case | Input | Expected Output |
|-----------|-------|-----------------|
| Exact match | "Как установить Python?" | 95%+ similarity |
| Paraphrase | "установка питона" | 70%+ similarity |
| Partial keywords | "python установка" | 60%+ similarity |
| Typos | "как устоновить python" | 50%+ similarity |
| No match | "xyz123abc" | No results |
| Empty query | "" | Error message |
| Very long query | 1000+ chars | Error or truncation |

## 8. Migration Script Specification

```python
# scripts/migrate_embeddings.py

import sys
import logging
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from storage.sqlite import SQLiteStorage
from utils.semantic_search import SemanticSearchEngine
from config import SEMANTIC_SEARCH_MODEL, SEARCH_BATCH_SIZE

logger = logging.getLogger(__name__)

def migrate_embeddings(db_path: str = "sqlite.db") -> None:
    """
    Generate embeddings for all questions in database.

    Args:
        db_path: Path to SQLite database
    """
    logger.info("Starting embedding migration...")

    # Initialize search engine
    search_engine = SemanticSearchEngine(SEMANTIC_SEARCH_MODEL)

    # Initialize storage
    storage = SQLiteStorage(db_path, search_engine)

    # Run migration
    count = storage.migrate_embeddings(batch_size=SEARCH_BATCH_SIZE)

    logger.info(f"Migration complete: {count} embeddings generated")

if __name__ == "__main__":
    migrate_embeddings()
```

## 9. Deployment Checklist

- [ ] Install dependencies: `pip install -r requirements.txt`
- [ ] Download model (first run): ~420MB download
- [ ] Run migration script: `python scripts/migrate_embeddings.py`
- [ ] Test search command: `/search`
- [ ] Verify model caching works
- [ ] Check memory usage: `< 1GB`
- [ ] Verify search response time: `< 500ms`
- [ ] Test with Russian queries
- [ ] Test with English queries
- [ ] Test error handling
- [ ] Update documentation
- [ ] Monitor logs for errors

## 10. Monitoring and Metrics

### 10.1 Metrics to Track

```python
# Metrics to log
SEARCH_METRICS = {
    'total_searches': 0,
    'successful_searches': 0,
    'failed_searches': 0,
    'no_results_searches': 0,
    'avg_search_time_ms': 0,
    'avg_results_per_search': 0,
    'model_load_time_ms': 0,
    'model_load_count': 0
}
```

### 10.2 Logging Format

```python
# Search event logging
logger.info(
    f"Search: user={user_id}, query='{query}', "
    f"results={len(results)}, time={elapsed_ms}ms, "
    f"top_score={results[0]['score'] if results else 0}"
)
```

## 11. Security Considerations

### 11.1 Input Validation

```python
def validate_search_query(query: str) -> tuple[bool, str]:
    """
    Validate search query.

    Returns:
        (is_valid, error_message)
    """
    if not query or not query.strip():
        return False, "Query cannot be empty"

    if len(query) > MAX_QUERY_LENGTH:
        return False, f"Query too long (max {MAX_QUERY_LENGTH} chars)"

    # Check for malicious patterns
    if contains_sql_injection(query):
        return False, "Invalid query format"

    return True, ""
```

### 11.2 Rate Limiting

```python
# Limit searches per user per minute
SEARCH_RATE_LIMIT = 10  # searches per minute
SEARCH_COOLDOWN = 60  # seconds

# Track user search timestamps
user_search_times = {}
```

## 12. Conclusion

This specification provides complete technical details for implementing semantic search with:
- Clear API contracts
- Detailed error handling
- Performance requirements
- Testing strategy
- Deployment procedures
- Monitoring approach

Ready for implementation in Code mode.
