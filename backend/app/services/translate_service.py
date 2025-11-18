import httpx
import json
import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from ..models import User
from ..config import settings
from ..utils import retry_on_failure, SentenceSplitter, EncryptionManager
from ..utils.limiter import translate_limiter
from .correction_service import CorrectionService

logger = logging.getLogger(__name__)


class TranslationService:
    """Service for translation using LLMs (supports OpenAI and Gemini formats)"""

    def __init__(
        self,
        api_base: str,
        api_key: str,
        model: str,
        db: Session,
        user: User
    ):
        self.api_base = api_base.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.db = db
        self.user = user
        self.correction_service = CorrectionService(db, user)

        # Detect API type
        self.api_type = self._detect_api_type()

    def _detect_api_type(self) -> str:
        """Detect API type based on api_base or model"""
        if 'generativelanguage.googleapis.com' in self.api_base:
            return 'gemini'
        elif 'gemini' in self.model.lower():
            return 'gemini'
        else:
            return 'openai'

    @retry_on_failure(max_retries=3, delays=[2, 4, 8])
    async def translate_text(
        self,
        text: str,
        source_language: str,
        target_language: str,
        use_corrections: bool = True
    ) -> str:
        """
        Translate text using LLM

        Args:
            text: Text to translate
            source_language: Source language code
            target_language: Target language code
            use_corrections: Whether to apply user corrections

        Returns:
            Translated text
        """
        # Build prompt with corrections if enabled
        system_prompt = self._build_system_prompt(
            source_language, target_language, use_corrections
        )

        if self.api_type == 'gemini':
            return await self._translate_gemini(text, system_prompt)
        else:
            return await self._translate_openai(text, system_prompt)

    async def _translate_openai(self, text: str, system_prompt: str) -> str:
        """Translate using OpenAI-compatible API"""
        async with translate_limiter:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text}
            ]

            payload = {
                "model": self.model,
                "messages": messages,
                "temperature": 0.3,
                "max_tokens": 4000,
            }

            try:
                async with httpx.AsyncClient(timeout=60.0) as client:
                    # Log request details
                    request_url = f"{self.api_base}/chat/completions"
                    logger.info("=" * 60)
                    logger.info(f"📤 翻译 API 请求")
                    logger.info(f"URL: {request_url}")
                    logger.info(f"Model: {self.model}")
                    logger.info(f"待翻译文本长度: {len(text)} 字符")
                    logger.info(f"待翻译文本预览: {text[:100]}...")

                    response = await client.post(
                        request_url,
                        headers=headers,
                        json=payload
                    )

                    # Log response details
                    if response.status_code != 200:
                        logger.error(f"翻译 API 错误响应: 状态码 {response.status_code}")
                        logger.error(f"响应内容: {response.text[:500]}")

                    response.raise_for_status()
                    result = response.json()

                # Extract translation and token usage
                translation = result["choices"][0]["message"]["content"]

                # Log token usage if available
                if "usage" in result:
                    usage = result["usage"]
                    logger.info(f"📊 Token 使用情况:")
                    logger.info(f"  - 提示词 tokens: {usage.get('prompt_tokens', 'N/A')}")
                    logger.info(f"  - 完成 tokens: {usage.get('completion_tokens', 'N/A')}")
                    logger.info(f"  - 总计 tokens: {usage.get('total_tokens', 'N/A')}")

                logger.info(f"✅ 翻译完成，结果长度: {len(translation)} 字符")
                logger.info("=" * 60)

                return translation.strip()

            except httpx.HTTPStatusError as e:
                logger.error(f"翻译 API HTTP 错误: {e.response.status_code} - {e.response.text[:200]}")
                raise
            except httpx.TimeoutException as e:
                logger.error(f"翻译 API 超时: {str(e)}")
                raise
            except Exception as e:
                logger.error(f"翻译 API 异常: {type(e).__name__} - {str(e)}")
                raise

    async def _translate_gemini(self, text: str, system_prompt: str) -> str:
        """Translate using Gemini API"""
        async with translate_limiter:
            headers = {
                "Content-Type": "application/json",
            }

            # Combine system prompt and user text for Gemini
            combined_text = f"{system_prompt}\n\nText to translate:\n{text}"

            payload = {
                "contents": [
                    {
                        "parts": [
                            {"text": combined_text}
                        ]
                    }
                ],
                "generationConfig": {
                    "temperature": 0.3,
                    "maxOutputTokens": 4000,
                }
            }

            # Gemini uses API key as query parameter
            url = f"{self.api_base}/models/{self.model}:generateContent?key={self.api_key}"

            # Log request details (mask API key)
            masked_url = f"{self.api_base}/models/{self.model}:generateContent?key=***"
            logger.info("=" * 60)
            logger.info(f"📤 翻译 API 请求 (Gemini)")
            logger.info(f"URL: {masked_url}")
            logger.info(f"Model: {self.model}")
            logger.info(f"待翻译文本长度: {len(text)} 字符")
            logger.info(f"待翻译文本预览: {text[:100]}...")

            try:
                async with httpx.AsyncClient(timeout=60.0) as client:
                    response = await client.post(
                        url,
                        headers=headers,
                        json=payload
                    )

                    if response.status_code != 200:
                        logger.error(f"翻译 API 错误响应: 状态码 {response.status_code}")
                        logger.error(f"响应内容: {response.text[:500]}")

                    response.raise_for_status()
                    result = response.json()

                # Extract text from Gemini response
                translation = result["candidates"][0]["content"]["parts"][0]["text"]

                # Log token usage if available (Gemini format)
                if "usageMetadata" in result:
                    usage = result["usageMetadata"]
                    logger.info(f"📊 Token 使用情况:")
                    logger.info(f"  - 提示词 tokens: {usage.get('promptTokenCount', 'N/A')}")
                    logger.info(f"  - 完成 tokens: {usage.get('candidatesTokenCount', 'N/A')}")
                    logger.info(f"  - 总计 tokens: {usage.get('totalTokenCount', 'N/A')}")

                logger.info(f"✅ 翻译完成，结果长度: {len(translation)} 字符")
                logger.info("=" * 60)

                return translation.strip()

            except httpx.HTTPStatusError as e:
                logger.error(f"翻译 API HTTP 错误: {e.response.status_code} - {e.response.text[:200]}")
                raise
            except httpx.TimeoutException as e:
                logger.error(f"翻译 API 超时: {str(e)}")
                raise
            except Exception as e:
                logger.error(f"翻译 API 异常: {type(e).__name__} - {str(e)}")
                raise

    async def translate_sentences(
        self,
        sentences: List[str],
        source_language: str,
        target_language: str,
        use_corrections: bool = True
    ) -> List[Dict[str, str]]:
        """
        Translate multiple sentences

        Args:
            sentences: List of sentences to translate
            source_language: Source language code
            target_language: Target language code
            use_corrections: Whether to apply user corrections

        Returns:
            List of dicts with 'source' and 'translation' keys
        """
        results = []

        for sentence in sentences:
            try:
                # Check for similar corrections first
                similar_corrections = []
                if use_corrections:
                    similar_corrections = await self.correction_service.find_similar_corrections(
                        sentence, source_language, target_language
                    )

                # If exact match found, use it
                if similar_corrections:
                    best_match = similar_corrections[0]
                    translation = best_match.corrected_translation
                    self.correction_service.update_correction_usage(best_match.id)
                    logger.info(f"Using correction for: {sentence[:50]}...")
                else:
                    # Otherwise, translate
                    translation = await self.translate_text(
                        sentence, source_language, target_language, use_corrections
                    )

                results.append({
                    "source": sentence,
                    "translation": translation
                })

            except Exception as e:
                logger.error(f"Translation failed for sentence: {str(e)}")
                results.append({
                    "source": sentence,
                    "translation": f"[Translation Error: {str(e)}]"
                })

        return results

    def _build_system_prompt(
        self,
        source_language: str,
        target_language: str,
        use_corrections: bool
    ) -> str:
        """Build system prompt for translation"""
        language_names = {
            "en": "English",
            "zh": "Chinese",
            "de": "German",
            "ru": "Russian"
        }

        source_lang_name = language_names.get(source_language, source_language)
        target_lang_name = language_names.get(target_language, target_language)

        prompt = f"""You are a professional translator. Translate the following {source_lang_name} text to {target_lang_name}.

Requirements:
1. Provide accurate and natural translations
2. Preserve the original meaning and tone
3. Use appropriate terminology for the context
4. Only output the translation, no explanations
"""

        # Add corrections to prompt if enabled and available
        if use_corrections:
            corrections = self.correction_service.get_corrections_for_prompt(
                source_language, target_language
            )

            if corrections:
                prompt += "\n\nPrevious corrections to follow:\n"
                for idx, correction in enumerate(corrections[:10], 1):  # Limit to 10
                    prompt += f"{idx}. \"{correction['source']}\" → \"{correction['translation']}\"\n"
                prompt += "\nPlease maintain consistency with these corrections.\n"

        return prompt

    @staticmethod
    def split_and_merge_text(
        text: str,
        source_language: str
    ) -> List[str]:
        """
        Split text into sentences for translation

        Args:
            text: Text to split
            source_language: Language code for smart splitting

        Returns:
            List of sentences
        """
        # Auto-detect language if not provided
        if source_language == "auto":
            source_language = SentenceSplitter.detect_language(text)

        sentences = SentenceSplitter.split_sentences(text, source_language)
        return sentences
