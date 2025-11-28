"""
Semantic search engine using sentence-transformers for embedding-based similarity search.
Provides functionality to encode text into embeddings and search for similar questions.
"""

import numpy as np
import logging
from typing import List, Dict, Optional, Tuple
from sentence_transformers import SentenceTransformer
from config import (
    SEMANTIC_SEARCH_MODEL,
    SEARCH_TOP_K,
    SEARCH_SIMILARITY_THRESHOLD,
    MODEL_CACHE_DIR
)

logger = logging.getLogger(__name__)


class SemanticSearchEngine:
    """
    Semantic search engine using sentence-transformers for embedding-based similarity search.

    Features:
    - Singleton pattern for model caching
    - Lazy loading of model
    - Cosine similarity computation
    - Configurable similarity threshold
    """

    _instance: Optional['SemanticSearchEngine'] = None
    _model: Optional[SentenceTransformer] = None
    _model_name: Optional[str] = None

    def __new__(cls, model_name: str = None):
        """
        Singleton pattern implementation.

        Args:
            model_name: Name of sentence-transformer model to use

        Returns:
            SemanticSearchEngine instance
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            logger.info("Creating new SemanticSearchEngine instance")
        return cls._instance

    def __init__(self, model_name: str = None):
        """
        Initialize semantic search engine.

        Args:
            model_name: Name of sentence-transformer model to use
        """
        # Only initialize if model hasn't been loaded yet
        if model_name and self._model is None:
            self._model_name = model_name
            logger.info(f"SemanticSearchEngine initialized with model: {model_name}")

    def _load_model(self) -> None:
        """
        Load sentence-transformer model (lazy loading).

        Raises:
            Exception: If model loading fails
        """
        if self._model is not None:
            logger.debug("Model already loaded, skipping")
            return

        try:
            logger.info(f"Loading sentence-transformer model: {self._model_name}")
            logger.info(f"Model cache directory: {MODEL_CACHE_DIR}")

            # Load model with caching
            self._model = SentenceTransformer(
                self._model_name,
                cache_folder=MODEL_CACHE_DIR
            )

            logger.info(f"Model loaded successfully: {self._model_name}")
            logger.info(f"Embedding dimension: {self._model.get_sentence_embedding_dimension()}")

        except Exception as e:
            logger.error(f"Failed to load model {self._model_name}: {e}")
            raise Exception(f"Model loading failed: {e}")

    def encode(self, text: str, show_progress: bool = False) -> np.ndarray:
        """
        Generate embedding for text.

        Args:
            text: Input text to encode
            show_progress: Whether to show progress bar

        Returns:
            numpy array of shape (embedding_dim,)

        Raises:
            Exception: If encoding fails
        """
        # Ensure model is loaded
        if self._model is None:
            self._load_model()

        try:
            # Generate embedding
            embedding = self._model.encode(
                text,
                convert_to_numpy=True,
                show_progress_bar=show_progress
            )

            logger.debug(f"Generated embedding for text: '{text[:50]}...' (shape: {embedding.shape})")
            return embedding

        except Exception as e:
            logger.error(f"Failed to encode text: {e}")
            raise Exception(f"Embedding generation failed: {e}")

    def encode_batch(self, texts: List[str], batch_size: int = 32, show_progress: bool = True) -> np.ndarray:
        """
        Generate embeddings for multiple texts in batch.

        Args:
            texts: List of texts to encode
            batch_size: Batch size for encoding
            show_progress: Whether to show progress bar

        Returns:
            numpy array of shape (n_texts, embedding_dim)

        Raises:
            Exception: If encoding fails
        """
        # Ensure model is loaded
        if self._model is None:
            self._load_model()

        try:
            logger.info(f"Encoding {len(texts)} texts in batch (batch_size={batch_size})")

            # Generate embeddings
            embeddings = self._model.encode(
                texts,
                batch_size=batch_size,
                convert_to_numpy=True,
                show_progress_bar=show_progress
            )

            logger.info(f"Generated {len(embeddings)} embeddings (shape: {embeddings.shape})")
            return embeddings

        except Exception as e:
            logger.error(f"Failed to encode batch: {e}")
            raise Exception(f"Batch embedding generation failed: {e}")

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
            Similarity scores of shape (n_docs,) with values in range [0, 1]
        """
        # Normalize embeddings
        query_norm = query_embedding / np.linalg.norm(query_embedding)
        doc_norms = doc_embeddings / np.linalg.norm(doc_embeddings, axis=1, keepdims=True)

        # Compute cosine similarity
        similarities = np.dot(doc_norms, query_norm)

        # Convert from [-1, 1] to [0, 1] range
        similarities = (similarities + 1) / 2

        logger.debug(f"Computed similarities: min={similarities.min():.3f}, max={similarities.max():.3f}, mean={similarities.mean():.3f}")

        return similarities

    def search(
        self,
        query: str,
        candidates: List[Dict],
        top_k: int = SEARCH_TOP_K,
        threshold: float = SEARCH_SIMILARITY_THRESHOLD
    ) -> List[Dict]:
        """
        Search for similar questions using semantic similarity.

        Args:
            query: Search query text
            candidates: List of question dicts with 'id', 'question', 'answer', 'embedding'
            top_k: Number of top results to return
            threshold: Minimum similarity score (0-1)

        Returns:
            List of dicts with 'id', 'question', 'answer', 'score' sorted by score (descending)
        """
        if not candidates:
            logger.warning("No candidates provided for search")
            return []

        try:
            # Generate query embedding
            logger.info(f"Searching for: '{query}' (top_k={top_k}, threshold={threshold})")
            query_embedding = self.encode(query)

            # Extract embeddings from candidates
            doc_embeddings = []
            valid_candidates = []

            for candidate in candidates:
                if 'embedding' in candidate and candidate['embedding'] is not None:
                    # Deserialize embedding from bytes if needed
                    if isinstance(candidate['embedding'], bytes):
                        embedding = np.frombuffer(candidate['embedding'], dtype=np.float32)
                    else:
                        embedding = candidate['embedding']

                    doc_embeddings.append(embedding)
                    valid_candidates.append(candidate)
                else:
                    logger.warning(f"Candidate {candidate.get('id', 'unknown')} has no embedding, skipping")

            if not doc_embeddings:
                logger.warning("No valid embeddings found in candidates")
                return []

            # Convert to numpy array
            doc_embeddings = np.array(doc_embeddings)

            # Compute similarities
            similarities = self.compute_similarity(query_embedding, doc_embeddings)

            # Create results with scores
            results = []
            for i, candidate in enumerate(valid_candidates):
                score = float(similarities[i])
                if score >= threshold:
                    results.append({
                        'id': candidate['id'],
                        'question': candidate['question'],
                        'answer': candidate['answer'],
                        'score': score,
                        'created_at': candidate.get('created_at'),
                        'updated_at': candidate.get('updated_at')
                    })

            # Sort by score (descending) and take top_k
            results.sort(key=lambda x: x['score'], reverse=True)
            results = results[:top_k]

            logger.info(f"Found {len(results)} results above threshold {threshold}")
            if results:
                logger.info(f"Top score: {results[0]['score']:.3f}, Bottom score: {results[-1]['score']:.3f}")

            return results

        except Exception as e:
            logger.error(f"Search failed: {e}")
            raise Exception(f"Search operation failed: {e}")

    def is_model_loaded(self) -> bool:
        """
        Check if model is loaded.

        Returns:
            True if model is loaded, False otherwise
        """
        return self._model is not None

    def get_embedding_dimension(self) -> Optional[int]:
        """
        Get embedding dimension of the model.

        Returns:
            Embedding dimension or None if model not loaded
        """
        if self._model is None:
            return None
        return self._model.get_sentence_embedding_dimension()


# Global instance for easy access
_search_engine: Optional[SemanticSearchEngine] = None


def get_search_engine(model_name: str = SEMANTIC_SEARCH_MODEL) -> SemanticSearchEngine:
    """
    Get or create global search engine instance.

    Args:
        model_name: Name of sentence-transformer model to use

    Returns:
        SemanticSearchEngine instance
    """
    global _search_engine
    if _search_engine is None:
        _search_engine = SemanticSearchEngine(model_name)
        logger.info("Global search engine instance created")
    return _search_engine
