# Semantic Search Deployment Guide

## Quick Start

### 1. Install Dependencies

```bash
# Install all required packages
pip install -r requirements.txt
```

**What gets installed:**
- `sentence-transformers==2.2.2` - AI model for semantic search
- `torch>=2.0.0` - Deep learning framework
- `numpy>=1.24.0` - Numerical computations
- `python-telegram-bot==21.9` - Telegram bot framework
- `python-dotenv==1.0.0` - Environment variables

**Download size:** ~670MB (first time only)

### 2. Configure Environment (Optional)

Create `.env` file if it doesn't exist:

```bash
# Bot token (required)
BOT_TOKEN=your_bot_token_here

# Semantic search settings (optional)
SEMANTIC_SEARCH_ENABLED=true
SEMANTIC_SEARCH_MODEL=sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
SEARCH_TOP_K=5
SEARCH_SIMILARITY_THRESHOLD=0.3
SEARCH_BATCH_SIZE=10
MAX_QUERY_LENGTH=200
MODEL_CACHE_DIR=./models
```

### 3. Migrate Existing Questions (If Any)

If you have existing questions in the database:

```bash
python migrate_embeddings.py
```

**Expected output:**
```
============================================================
Semantic Search Embedding Migration
============================================================
Model: sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
Batch size: 10

Initializing search engine...
Search engine initialized

Connecting to database...
Database connected

Total questions in database: 25

Starting migration...
This may take a few minutes depending on the number of questions

Processing batch 1/3
Processing batch 2/3
Processing batch 3/3

============================================================
Migration completed successfully!
Generated 25 embeddings
============================================================

You can now use the /search command in the bot
```

### 4. Start the Bot

```bash
python bot.py
```

**Expected output:**
```
2025-11-28 22:00:00,000 - config - INFO - Configuration loaded successfully
2025-11-28 22:00:00,100 - __main__ - INFO - Starting Telegram bot...
2025-11-28 22:00:01,500 - __main__ - INFO - Semantic search engine initialized with model: sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
2025-11-28 22:00:01,600 - __main__ - INFO - Storage initialized
2025-11-28 22:00:01,700 - __main__ - INFO - Basic command handlers registered
2025-11-28 22:00:01,800 - __main__ - INFO - Add conversation handler registered
2025-11-28 22:00:01,900 - __main__ - INFO - Edit conversation handler registered
2025-11-28 22:00:02,000 - __main__ - INFO - Search conversation handler registered
2025-11-28 22:00:02,100 - __main__ - INFO - List command handler registered
2025-11-28 22:00:02,200 - __main__ - INFO - Callback query handler registered
2025-11-28 22:00:02,300 - __main__ - INFO - Fallback cancel handler registered
2025-11-28 22:00:02,400 - __main__ - INFO - Bot is starting polling...
```

### 5. Test the Search

In Telegram:
1. Send `/search` to the bot
2. Enter a search query (e.g., "как установить python")
3. View the ranked results

## Verification Checklist

- [ ] Dependencies installed successfully
- [ ] Bot token configured in `.env`
- [ ] Migration completed (if had existing questions)
- [ ] Bot starts without errors
- [ ] `/search` command available
- [ ] Search returns relevant results
- [ ] New questions get embeddings automatically

## Common Issues and Solutions

### Issue: Model Download Fails

**Symptoms:**
```
Failed to load model: HTTPError 503
```

**Solution:**
```bash
# Download model manually
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')"
```

### Issue: Out of Memory

**Symptoms:**
```
MemoryError: Unable to allocate array
```

**Solutions:**

1. Use smaller model:
```bash
# In .env
SEMANTIC_SEARCH_MODEL=cointegrated/rubert-tiny2
```

2. Reduce batch size:
```bash
# In .env
SEARCH_BATCH_SIZE=5
```

3. Disable search temporarily:
```bash
# In .env
SEMANTIC_SEARCH_ENABLED=false
```

### Issue: Slow Search

**Symptoms:**
- Search takes > 1 second
- Bot feels sluggish

**Solutions:**

1. First search is always slower (model loading)
2. Ensure model is cached in `./models` directory
3. Check system resources (CPU/RAM usage)
4. Reduce number of questions in database

### Issue: No Results Found

**Symptoms:**
- Search always returns "Ничего не найдено"

**Solutions:**

1. Lower similarity threshold:
```bash
# In .env
SEARCH_SIMILARITY_THRESHOLD=0.2
```

2. Check if questions have embeddings:
```bash
python migrate_embeddings.py
```

3. Try different query phrasing

### Issue: Migration Fails

**Symptoms:**
```
Migration failed: No module named 'sentence_transformers'
```

**Solutions:**

1. Verify dependencies:
```bash
pip list | grep sentence-transformers
```

2. Reinstall if needed:
```bash
pip install --force-reinstall sentence-transformers
```

3. Check Python version (need 3.8+):
```bash
python --version
```

## Performance Tuning

### For Better Speed

```bash
# .env
SEARCH_BATCH_SIZE=20  # Faster migration
SEARCH_TOP_K=3        # Fewer results = faster
```

### For Better Quality

```bash
# .env
SEARCH_SIMILARITY_THRESHOLD=0.5  # Higher threshold = more precise
SEARCH_TOP_K=10                  # More results
```

### For Lower Memory Usage

```bash
# .env
SEMANTIC_SEARCH_MODEL=cointegrated/rubert-tiny2  # Smaller model (~120MB)
SEARCH_BATCH_SIZE=5                               # Smaller batches
```

## Production Deployment

### System Requirements

**Minimum:**
- CPU: 2 cores
- RAM: 1GB
- Disk: 2GB free space
- Python: 3.8+

**Recommended:**
- CPU: 4 cores
- RAM: 2GB
- Disk: 5GB free space
- Python: 3.10+

### Production Configuration

```bash
# .env for production
BOT_TOKEN=your_production_token
LOG_LEVEL=INFO
SEMANTIC_SEARCH_ENABLED=true
SEMANTIC_SEARCH_MODEL=sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
SEARCH_TOP_K=5
SEARCH_SIMILARITY_THRESHOLD=0.3
MODEL_CACHE_DIR=/var/cache/bot/models
```

### Using systemd (Linux)

Create `/etc/systemd/system/telegram-bot.service`:

```ini
[Unit]
Description=Telegram Q&A Bot with Semantic Search
After=network.target

[Service]
Type=simple
User=botuser
WorkingDirectory=/opt/telegram-bot
Environment="PATH=/opt/telegram-bot/.venv/bin"
ExecStart=/opt/telegram-bot/.venv/bin/python bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable telegram-bot
sudo systemctl start telegram-bot
sudo systemctl status telegram-bot
```

### Using Docker

Create `Dockerfile`:

```dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Download model at build time
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')"

# Run bot
CMD ["python", "bot.py"]
```

Build and run:
```bash
docker build -t telegram-bot .
docker run -d --name telegram-bot --env-file .env telegram-bot
```

### Monitoring

Check logs:
```bash
# systemd
sudo journalctl -u telegram-bot -f

# Docker
docker logs -f telegram-bot

# Direct
tail -f bot.log
```

Monitor resources:
```bash
# CPU and memory
top -p $(pgrep -f bot.py)

# Disk usage
du -sh ./models
du -sh sqlite.db
```

## Backup and Recovery

### Backup Database

```bash
# Backup with embeddings
cp sqlite.db sqlite.db.backup

# Scheduled backup (cron)
0 2 * * * cp /opt/telegram-bot/sqlite.db /backup/sqlite.db.$(date +\%Y\%m\%d)
```

### Restore Database

```bash
# Stop bot
systemctl stop telegram-bot  # or docker stop telegram-bot

# Restore
cp sqlite.db.backup sqlite.db

# Start bot
systemctl start telegram-bot  # or docker start telegram-bot
```

### Backup Model Cache

```bash
# Backup model (optional, can be re-downloaded)
tar -czf models.tar.gz ./models
```

## Updating

### Update Dependencies

```bash
# Update all packages
pip install --upgrade -r requirements.txt

# Update specific package
pip install --upgrade sentence-transformers
```

### Update Model

```bash
# Change model in .env
SEMANTIC_SEARCH_MODEL=new-model-name

# Regenerate embeddings
python migrate_embeddings.py
```

## Health Checks

### Manual Check

```bash
# Check if bot is running
ps aux | grep bot.py

# Check if model is loaded
ls -lh ./models

# Check database
sqlite3 sqlite.db "SELECT COUNT(*) FROM questions WHERE embedding IS NOT NULL;"
```

### Automated Health Check Script

Create `health_check.sh`:

```bash
#!/bin/bash

# Check if bot process is running
if ! pgrep -f bot.py > /dev/null; then
    echo "ERROR: Bot is not running"
    exit 1
fi

# Check if database exists
if [ ! -f sqlite.db ]; then
    echo "ERROR: Database not found"
    exit 1
fi

# Check if model cache exists
if [ ! -d ./models ]; then
    echo "WARNING: Model cache not found"
fi

echo "OK: All checks passed"
exit 0
```

Run periodically:
```bash
*/5 * * * * /opt/telegram-bot/health_check.sh || systemctl restart telegram-bot
```

## Support

For issues:
1. Check logs in `bot.log`
2. Review this deployment guide
3. Check `SEMANTIC_SEARCH_README.md`
4. Review technical specs in `SEMANTIC_SEARCH_SPEC.md`

## Next Steps

After successful deployment:
1. ✅ Test search with various queries
2. ✅ Monitor performance and resource usage
3. ✅ Adjust configuration based on usage patterns
4. ✅ Set up automated backups
5. ✅ Configure monitoring and alerts
6. ✅ Document any custom configurations

## Success Criteria

Your deployment is successful when:
- ✅ Bot responds to `/search` command
- ✅ Search returns relevant results in < 500ms
- ✅ Memory usage stays under 1GB
- ✅ New questions get embeddings automatically
- ✅ No errors in logs
- ✅ Users can find information easily

Congratulations! Your semantic search is now live! 🎉
