# Semantic Search Feature - User Guide

## Overview

The Telegram Q&A bot now includes **semantic search** functionality powered by AI. This allows you to find relevant questions using natural language, even if your search query uses different words than the original question.

## What is Semantic Search?

Traditional keyword search only finds exact word matches. Semantic search understands the **meaning** of your query and finds questions that are conceptually similar.

### Example:
- **Your search**: "как установить python"
- **Will find**:
  - "Как установить Python?" (95% match)
  - "Установка Python на Windows" (78% match)
  - "Настройка окружения Python" (65% match)

## Installation

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

This will install:
- `sentence-transformers` - AI model for semantic understanding
- `torch` - Deep learning framework
- `numpy` - Numerical computations

**Note**: First installation will download ~670MB of data (model + dependencies).

### 2. Configure (Optional)

Create or edit `.env` file:

```bash
# Enable/disable semantic search
SEMANTIC_SEARCH_ENABLED=true

# Model to use (default is recommended)
SEMANTIC_SEARCH_MODEL=sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2

# Number of search results to show
SEARCH_TOP_K=5

# Minimum similarity threshold (0.0 to 1.0)
SEARCH_SIMILARITY_THRESHOLD=0.3

# Batch size for embedding generation
SEARCH_BATCH_SIZE=10

# Maximum query length
MAX_QUERY_LENGTH=200

# Model cache directory
MODEL_CACHE_DIR=./models
```

### 3. Migrate Existing Questions

If you have existing questions in the database, run the migration script to generate embeddings:

```bash
python migrate_embeddings.py
```

This will:
- Load the AI model (~420MB, one-time download)
- Generate embeddings for all existing questions
- Store embeddings in the database

**Time estimate**: ~1-2 minutes for 100 questions

### 4. Start the Bot

```bash
python bot.py
```

The bot will automatically:
- Load the semantic search model
- Generate embeddings for new questions
- Enable the `/search` command

## Usage

### Basic Search

1. Send `/search` command to the bot
2. Enter your search query in natural language
3. View ranked results with similarity scores

### Example Queries

| Query | Description |
|-------|-------------|
| `как установить python` | Find Python installation guides |
| `что такое апи` | Find API explanations |
| `настройка гита` | Find Git configuration help |
| `python setup` | Works in English too! |

### Understanding Results

Results show:
- **Similarity score** (0-100%): How relevant the question is
- **Question text**: The matched question
- **Answer preview**: First 100 characters of the answer
- **"Show full" button**: View complete answer

Example result:
```
1. ⭐ 95% - Как установить Python?
   💡 Скачайте с python.org...
   [Показать полностью]
```

## Features

### ✅ What Works

- **Natural language queries**: Use everyday language
- **Multilingual**: Works with Russian and English
- **Fuzzy matching**: Handles typos and variations
- **Semantic understanding**: Finds similar concepts
- **Offline operation**: Works without internet after setup
- **Fast results**: < 500ms search time
- **Automatic embeddings**: New questions indexed automatically

### 🎯 Search Quality

The search uses a state-of-the-art multilingual model that:
- Understands context and meaning
- Handles synonyms and paraphrases
- Works across languages
- Ranks results by relevance

### 📊 Performance

- **Model loading**: 2-5 seconds (first time only)
- **Search time**: 100-200ms per query
- **Memory usage**: ~500MB (model in RAM)
- **Disk space**: ~670MB (model + dependencies)

## Configuration Options

### Search Parameters

#### `SEARCH_TOP_K` (default: 5)
Number of results to return. Increase for more results.

```bash
SEARCH_TOP_K=10  # Show top 10 results
```

#### `SEARCH_SIMILARITY_THRESHOLD` (default: 0.3)
Minimum similarity score (0.0 to 1.0). Lower = more results, higher = more precise.

```bash
SEARCH_SIMILARITY_THRESHOLD=0.5  # Only show 50%+ matches
```

#### `SEARCH_BATCH_SIZE` (default: 10)
Batch size for embedding generation during migration. Increase for faster migration.

```bash
SEARCH_BATCH_SIZE=20  # Process 20 questions at once
```

### Model Selection

The default model is optimized for:
- ✅ Multilingual support (Russian + English)
- ✅ Compact size (~420MB)
- ✅ Fast inference
- ✅ Good quality

Alternative models:

```bash
# Larger, better quality (470MB)
SEMANTIC_SEARCH_MODEL=sentence-transformers/LaBSE

# Smaller, Russian-only (120MB)
SEMANTIC_SEARCH_MODEL=cointegrated/rubert-tiny2
```

## Troubleshooting

### Model Download Fails

**Problem**: Network error during model download

**Solution**:
```bash
# Download manually
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')"
```

### Out of Memory

**Problem**: Bot crashes with memory error

**Solutions**:
1. Use a smaller model:
   ```bash
   SEMANTIC_SEARCH_MODEL=cointegrated/rubert-tiny2
   ```

2. Reduce batch size:
   ```bash
   SEARCH_BATCH_SIZE=5
   ```

3. Disable search temporarily:
   ```bash
   SEMANTIC_SEARCH_ENABLED=false
   ```

### Slow Search

**Problem**: Search takes > 1 second

**Solutions**:
1. Ensure model is cached (first search is slower)
2. Reduce number of questions in database
3. Check system resources (CPU/RAM)

### No Results Found

**Problem**: Search returns no results

**Solutions**:
1. Lower similarity threshold:
   ```bash
   SEARCH_SIMILARITY_THRESHOLD=0.2
   ```

2. Try different query phrasing
3. Check if questions have embeddings:
   ```bash
   python migrate_embeddings.py
   ```

### Migration Fails

**Problem**: `migrate_embeddings.py` crashes

**Solutions**:
1. Check dependencies are installed:
   ```bash
   pip install -r requirements.txt
   ```

2. Verify database exists:
   ```bash
   ls -la sqlite.db
   ```

3. Check disk space (need ~1GB free)

## Advanced Usage

### Programmatic Access

```python
from storage.sqlite import SQLiteStorage
from utils.semantic_search import get_search_engine

# Initialize
search_engine = get_search_engine()
storage = SQLiteStorage('sqlite.db', search_engine)

# Search
results = storage.search_questions(
    query="как установить python",
    top_k=5,
    threshold=0.3
)

# Process results
for result in results:
    print(f"{result['score']:.2%} - {result['question']}")
```

### Custom Model

```python
from utils.semantic_search import SemanticSearchEngine

# Use custom model
engine = SemanticSearchEngine('your-model-name')

# Generate embedding
embedding = engine.encode("your text here")

# Search
results = engine.search(
    query="search query",
    candidates=questions_list,
    top_k=10,
    threshold=0.4
)
```

## Best Practices

### For Users

1. **Use natural language**: Write queries as you would ask a person
2. **Be specific**: "python installation windows" better than "python"
3. **Try variations**: If no results, rephrase your query
4. **Check scores**: 70%+ usually means good match

### For Administrators

1. **Run migration** after bulk imports
2. **Monitor memory** usage in production
3. **Adjust threshold** based on user feedback
4. **Keep model cached** for better performance
5. **Regular backups** of database with embeddings

## Technical Details

### Architecture

```
User Query
    ↓
Generate Query Embedding (384 dimensions)
    ↓
Compare with All Question Embeddings
    ↓
Compute Cosine Similarity
    ↓
Rank by Score
    ↓
Filter by Threshold
    ↓
Return Top K Results
```

### Embedding Storage

- **Format**: Binary BLOB in SQLite
- **Size**: 1,536 bytes per question (384 floats × 4 bytes)
- **Total**: ~150KB for 100 questions

### Model Details

- **Name**: paraphrase-multilingual-MiniLM-L12-v2
- **Type**: Sentence Transformer
- **Languages**: 50+ including Russian and English
- **Dimensions**: 384
- **Size**: ~420MB
- **Speed**: ~100ms per query

## FAQ

**Q: Does search work offline?**
A: Yes, after initial model download.

**Q: Can I use my own model?**
A: Yes, set `SEMANTIC_SEARCH_MODEL` in `.env`

**Q: How accurate is the search?**
A: Very accurate for paraphrases, good for related concepts.

**Q: Does it work with typos?**
A: Partially. It handles some typos but not all.

**Q: Can I disable search?**
A: Yes, set `SEMANTIC_SEARCH_ENABLED=false`

**Q: How much RAM does it need?**
A: ~500MB for the model, plus ~100MB for the bot.

**Q: Can I search in English?**
A: Yes, the model is multilingual.

**Q: What if I have 1000+ questions?**
A: Search will still work but may be slower. Consider using a vector database.

## Support

For issues or questions:
1. Check this README
2. Review logs in `bot.log`
3. Check configuration in `.env`
4. Review technical specs in `SEMANTIC_SEARCH_SPEC.md`

## Updates

### Version 1.0 (Current)
- ✅ Basic semantic search
- ✅ Multilingual support
- ✅ Automatic embedding generation
- ✅ Migration script
- ✅ Configurable parameters

### Planned Features
- 🔄 Query expansion with synonyms
- 🔄 Hybrid search (semantic + keyword)
- 🔄 Search analytics
- 🔄 Category filtering
- 🔄 Search history

## License

Same as the main bot project.
