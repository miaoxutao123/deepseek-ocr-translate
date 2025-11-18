import httpx
import json
import logging
import numpy as np
from typing import List, Optional

from ..utils import retry_on_failure
from ..utils.limiter import embedding_limiter

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Service for text embedding using Gemini API"""

    def __init__(self, api_base: str, api_key: str, model: str = "text-embedding-004"):
        self.api_base = api_base.rstrip("/")
        self.api_key = api_key
        self.model = model

    @retry_on_failure(max_retries=3, delays=[2, 4, 8])
    async def get_embedding(self, text: str) -> List[float]:
        """
        Get embedding vector for text

        Args:
            text: Text to embed

        Returns:
            Embedding vector as list of floats
        """
        async with embedding_limiter:
            headers = {
                "Content-Type": "application/json",
            }

            payload = {
                "model": f"models/{self.model}",
                "content": {
                    "parts": [{"text": text}]
                }
            }

            # Gemini API uses API key as query parameter
            url = f"{self.api_base}/models/{self.model}:embedContent?key={self.api_key}"

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    url,
                    headers=headers,
                    json=payload
                )
                response.raise_for_status()
                result = response.json()

            # Extract embedding from response
            embedding = result.get("embedding", {}).get("values", [])
            return embedding

    @retry_on_failure(max_retries=3, delays=[2, 4, 8])
    async def get_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Get embeddings for multiple texts

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors
        """
        # Gemini API doesn't support batch embedding in a single call
        # We need to call multiple times
        embeddings = []
        for text in texts:
            embedding = await self.get_embedding(text)
            embeddings.append(embedding)

        return embeddings

    @staticmethod
    def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
        """
        Calculate cosine similarity between two vectors

        Args:
            vec1: First vector
            vec2: Second vector

        Returns:
            Similarity score (0-1)
        """
        if not vec1 or not vec2:
            return 0.0

        a = np.array(vec1)
        b = np.array(vec2)

        # Cosine similarity
        similarity = np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
        return float(similarity)

    @staticmethod
    def find_most_similar(
        query_embedding: List[float],
        embeddings: List[List[float]],
        threshold: float = 0.85
    ) -> List[int]:
        """
        Find indices of embeddings most similar to query

        Args:
            query_embedding: Query embedding vector
            embeddings: List of embedding vectors to compare
            threshold: Minimum similarity threshold

        Returns:
            List of indices with similarity >= threshold
        """
        similar_indices = []

        for idx, embedding in enumerate(embeddings):
            similarity = EmbeddingService.cosine_similarity(query_embedding, embedding)
            if similarity >= threshold:
                similar_indices.append(idx)

        return similar_indices
