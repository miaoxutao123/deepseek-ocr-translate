import json
import logging
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime

from ..models import Correction, User
from ..schemas import CorrectionCreate
from .embedding_service import EmbeddingService
from ..config import settings
from ..utils import EncryptionManager

logger = logging.getLogger(__name__)


class CorrectionService:
    """Service for managing translation corrections"""

    def __init__(self, db: Session, user: User):
        self.db = db
        self.user = user
        self.embedding_service = None

        # Initialize embedding service if user has API key
        if user.embedding_api_key:
            decrypted_key = EncryptionManager.decrypt_api_key(
                user.embedding_api_key, user.id, settings.SECRET_KEY
            )
            api_base = user.embedding_api_base or "https://generativelanguage.googleapis.com/v1beta"
            self.embedding_service = EmbeddingService(api_base, decrypted_key)

    async def create_correction(
        self,
        correction_data: CorrectionCreate
    ) -> Correction:
        """
        Create a new correction entry

        Args:
            correction_data: Correction data

        Returns:
            Created correction object
        """
        # Create embedding for source text if service available
        embedding = None
        if self.embedding_service:
            try:
                embedding_vec = await self.embedding_service.get_embedding(
                    correction_data.source_text
                )
                embedding = json.dumps(embedding_vec)
            except Exception as e:
                logger.error(f"Failed to create embedding: {str(e)}")

        correction = Correction(
            user_id=self.user.id,
            source_text=correction_data.source_text,
            corrected_translation=correction_data.corrected_translation,
            source_language=correction_data.source_language,
            target_language=correction_data.target_language,
            embedding=embedding,
            history_id=correction_data.history_id,
        )

        self.db.add(correction)
        self.db.commit()
        self.db.refresh(correction)

        return correction

    async def find_similar_corrections(
        self,
        source_text: str,
        source_language: str,
        target_language: str,
        threshold: float = None
    ) -> List[Correction]:
        """
        Find corrections similar to given source text

        Args:
            source_text: Source text to match
            source_language: Source language
            target_language: Target language
            threshold: Similarity threshold (default from settings)

        Returns:
            List of similar corrections
        """
        if threshold is None:
            threshold = settings.VECTOR_SIMILARITY_THRESHOLD

        # Get all corrections for this language pair
        corrections = self.db.query(Correction).filter(
            Correction.user_id == self.user.id,
            Correction.source_language == source_language,
            Correction.target_language == target_language,
            Correction.embedding.isnot(None)
        ).all()

        if not corrections or not self.embedding_service:
            return []

        # Get embedding for query text
        try:
            query_embedding = await self.embedding_service.get_embedding(source_text)
        except Exception as e:
            logger.error(f"Failed to get query embedding: {str(e)}")
            return []

        # Find similar corrections
        similar_corrections = []
        for correction in corrections:
            if not correction.embedding:
                continue

            try:
                correction_embedding = json.loads(correction.embedding)
                similarity = EmbeddingService.cosine_similarity(
                    query_embedding, correction_embedding
                )

                if similarity >= threshold:
                    similar_corrections.append(correction)
                    logger.info(f"Found similar correction (similarity: {similarity:.3f})")

            except Exception as e:
                logger.error(f"Failed to compare embeddings: {str(e)}")

        return similar_corrections

    def get_corrections_for_prompt(
        self,
        source_language: str,
        target_language: str,
        max_tokens: int = None
    ) -> List[Dict[str, str]]:
        """
        Get corrections to include in translation prompt

        Args:
            source_language: Source language
            target_language: Target language
            max_tokens: Maximum tokens to include (default from settings)

        Returns:
            List of correction dicts with 'source' and 'translation' keys
        """
        if max_tokens is None:
            max_tokens = settings.CORRECTION_TOKEN_THRESHOLD

        # Get recent corrections for this language pair
        corrections = self.db.query(Correction).filter(
            Correction.user_id == self.user.id,
            Correction.source_language == source_language,
            Correction.target_language == target_language
        ).order_by(Correction.last_used_at.desc()).all()

        # Estimate tokens and select corrections
        selected = []
        estimated_tokens = 0

        for correction in corrections:
            # Rough token estimation (1 token ≈ 4 characters for English, 1 for Chinese)
            correction_tokens = (len(correction.source_text) + len(correction.corrected_translation)) // 3

            if estimated_tokens + correction_tokens > max_tokens:
                break

            selected.append({
                "source": correction.source_text,
                "translation": correction.corrected_translation
            })
            estimated_tokens += correction_tokens

        logger.info(f"Selected {len(selected)} corrections (~{estimated_tokens} tokens)")
        return selected

    def update_correction_usage(self, correction_id: int):
        """Update correction usage statistics"""
        correction = self.db.query(Correction).filter(
            Correction.id == correction_id,
            Correction.user_id == self.user.id
        ).first()

        if correction:
            correction.usage_count += 1
            correction.last_used_at = datetime.utcnow()
            self.db.commit()

    def delete_correction(self, correction_id: int) -> bool:
        """Delete a correction"""
        correction = self.db.query(Correction).filter(
            Correction.id == correction_id,
            Correction.user_id == self.user.id
        ).first()

        if correction:
            self.db.delete(correction)
            self.db.commit()
            return True

        return False

    def export_corrections(
        self,
        source_language: Optional[str] = None,
        target_language: Optional[str] = None
    ) -> List[Correction]:
        """Export corrections for backup"""
        query = self.db.query(Correction).filter(
            Correction.user_id == self.user.id
        )

        if source_language:
            query = query.filter(Correction.source_language == source_language)
        if target_language:
            query = query.filter(Correction.target_language == target_language)

        return query.all()

    async def import_corrections(
        self,
        corrections_data: List[CorrectionCreate]
    ) -> int:
        """
        Import corrections from backup

        Returns:
            Number of corrections imported
        """
        count = 0
        for correction_data in corrections_data:
            try:
                await self.create_correction(correction_data)
                count += 1
            except Exception as e:
                logger.error(f"Failed to import correction: {str(e)}")

        return count
