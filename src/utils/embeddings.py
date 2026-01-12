"""
Embeddings module for semantic similarity analysis of failures
"""

from typing import List, Optional, Tuple

# Try to import optional dependencies
try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    SentenceTransformer = None

try:
    import chromadb
    from chromadb.config import Settings
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False
    chromadb = None
    Settings = None

import os
from pathlib import Path

from ..models.config import SystemConfig, FailureEntry


class EmbeddingsManager:
    """Manages embeddings for semantic similarity analysis"""

    def __init__(self, config: SystemConfig):
        self.config = config
        self.embeddings_model = None
        self.chroma_client = None
        self.collection = None

        # Initialize embeddings
        self._initialize_embeddings()

    def _initialize_embeddings(self):
        """Initialize embeddings model and vector database"""
        # Check if dependencies are available
        if not SENTENCE_TRANSFORMERS_AVAILABLE or not CHROMADB_AVAILABLE:
            missing = []
            if not SENTENCE_TRANSFORMERS_AVAILABLE:
                missing.append("sentence-transformers")
            if not CHROMADB_AVAILABLE:
                missing.append("chromadb")
            
            print(f"Warning: Optional dependencies not available: {', '.join(missing)}")
            print("Install with: pip install -e \".[local]\" for local embeddings support")
            print("Falling back to simple text similarity")
            self.embeddings_model = None
            return
        
        try:
            # Initialize sentence transformer model
            model_name = os.getenv("EMBEDDINGS_MODEL", "all-MiniLM-L6-v2")
            self.embeddings_model = SentenceTransformer(model_name)

            # Initialize ChromaDB
            persist_directory = os.getenv("CHROMA_PERSIST_DIRECTORY", "./chroma_db")
            Path(persist_directory).mkdir(parents=True, exist_ok=True)

            self.chroma_client = chromadb.PersistentClient(
                path=persist_directory, settings=Settings(anonymized_telemetry=False)
            )

            # Create or get collection
            self.collection = self.chroma_client.get_or_create_collection(
                name="failure_embeddings",
                metadata={"description": "Failure embeddings for semantic similarity"},
            )

            print(f"✓ Embeddings initialized with model: {model_name}")

        except Exception as e:
            print(f"Warning: Could not initialize embeddings: {e}")
            print("Falling back to simple text similarity")
            self.embeddings_model = None

    def get_embedding(self, text: str) -> Optional[List[float]]:
        """Get embedding for a text string"""
        if not self.embeddings_model:
            return None

        try:
            # Clean and prepare text
            clean_text = text.strip()
            if not clean_text:
                return None

            # Generate embedding
            embedding = self.embeddings_model.encode(clean_text)
            return embedding.tolist()

        except Exception as e:
            print(f"Error generating embedding: {e}")
            return None

    def add_failure_embedding(self, failure: FailureEntry):
        """Add failure embedding to vector database"""
        if not self.embeddings_model or not self.collection:
            return

        try:
            # Create text for embedding
            failure_text = self._create_failure_text(failure)
            embedding = self.get_embedding(failure_text)

            if embedding:
                # Add to ChromaDB
                self.collection.add(
                    embeddings=[embedding],
                    documents=[failure_text],
                    metadatas=[
                        {
                            "failure_id": failure.id,
                            "timestamp": failure.timestamp,
                            "severity": failure.severity,
                            "trigger_type": failure.trigger_type,
                            "signature": failure.failure_signature,
                        }
                    ],
                    ids=[failure.id],
                )

        except Exception as e:
            print(f"Error adding failure embedding: {e}")

    def find_similar_failures(
        self, failure: FailureEntry, threshold: float = 0.7, top_k: int = 5
    ) -> List[Tuple[FailureEntry, float]]:
        """
        Find similar failures using semantic similarity

        Returns list of (failure_entry, similarity_score) tuples
        """
        if not self.embeddings_model or not self.collection:
            return self._find_similar_text_based(failure, top_k)

        try:
            # Create query embedding
            query_text = self._create_failure_text(failure)
            query_embedding = self.get_embedding(query_text)

            if not query_embedding:
                return []

            # Query ChromaDB
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                include=["metadatas", "distances"],
            )

            # Process results
            similar_failures = []
            if results and results["ids"][0]:
                for i, failure_id in enumerate(results["ids"][0]):
                    if failure_id == failure.id:
                        continue  # Skip the query failure itself

                    distance = results["distances"][0][i]
                    similarity = 1.0 - distance  # Convert distance to similarity

                    if similarity >= threshold:
                        # Create minimal failure entry from metadata
                        metadata = results["metadatas"][0][i]
                        similar_failure = FailureEntry(
                            trigger_type=metadata["trigger_type"],
                            failure_description=f"Similar failure (score: {similarity:.2f})",
                            id=metadata["failure_id"],
                            timestamp=metadata["timestamp"],
                            severity=metadata["severity"],
                            failure_signature=metadata["signature"],
                        )
                        similar_failures.append((similar_failure, similarity))

            return similar_failures

        except Exception as e:
            print(f"Error finding similar failures: {e}")
            return self._find_similar_text_based(failure, top_k)

    def _find_similar_text_based(
        self, failure: FailureEntry, top_k: int = 5
    ) -> List[Tuple[FailureEntry, float]]:
        """Fallback text-based similarity when embeddings are not available"""
        # This is a simple implementation - in production, you'd want
        # a more sophisticated text similarity approach
        return []

    def _create_failure_text(self, failure: FailureEntry) -> str:
        """Create text representation of failure for embedding"""
        text_parts = [
            failure.failure_description,
            f"Trigger type: {failure.trigger_type}",
            f"Severity: {failure.severity}",
        ]

        if failure.user_query:
            text_parts.append(f"User query: {failure.user_query}")

        if failure.validation_errors:
            text_parts.append(f"Validation errors: {failure.validation_errors}")

        return " ".join(text_parts)

    def cleanup_old_embeddings(self, max_age_days: int = 30):
        """Clean up old embeddings (placeholder implementation)"""
        # In production, you'd implement age-based cleanup
        # For now, this is a placeholder
        pass


class SimpleTextSimilarity:
    """Simple text similarity fallback when embeddings are not available"""

    @staticmethod
    def calculate_similarity(text1: str, text2: str) -> float:
        """Calculate simple text similarity (0.0 to 1.0)"""
        if not text1 or not text2:
            return 0.0

        # Convert to lowercase and split into words
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())

        if not words1 or not words2:
            return 0.0

        # Calculate Jaccard similarity
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))

        return intersection / union if union > 0 else 0.0
