import httpx
import base64
import json
import logging
from typing import List, Dict, Any, Optional, AsyncGenerator
from pathlib import Path
from PIL import Image
import io

from ..config import settings
from ..utils import retry_on_failure, SentenceSplitter
from ..utils.limiter import ocr_limiter

logger = logging.getLogger(__name__)


class OCRService:
    """Service for OCR operations using multimodal LLMs"""

    def __init__(self, api_base: str, api_key: str, model: str = "deepseek-ai/deepseek-vl2"):
        self.api_base = api_base.rstrip("/")
        self.api_key = api_key
        self.model = model

    def _encode_image(self, image_path: str) -> str:
        """Encode image to base64"""
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")

    @retry_on_failure(max_retries=settings.OCR_MAX_RETRIES, delays=settings.retry_delays)
    async def ocr_single_image(self, image_path: str) -> Dict[str, Any]:
        """
        Perform OCR on a single image using multimodal LLM

        Args:
            image_path: Path to image file

        Returns:
            Dict with 'text' and optional 'confidence'
        """
        # Use rate limiter to control API calls
        async with ocr_limiter:
            try:
                # Encode image
                logger.info(f"Encoding image: {image_path}")
                image_base64 = self._encode_image(image_path)
                image_size = len(image_base64)
                logger.info(f"Image encoded, base64 size: {image_size} bytes ({image_size/1024:.2f} KB)")

                image_ext = Path(image_path).suffix.lower().replace(".", "")
                if image_ext == "jpg":
                    image_ext = "jpeg"

                # Prepare request
                headers = {
                    "Authorization": f"Bearer {self.api_key[:10]}...{self.api_key[-4:]}",  # Log partial key for debugging
                    "Content-Type": "application/json",
                }

                # DeepSeek-OCR 需要特殊的 prompt 格式
                # 支持的模式:
                # - "Free OCR." - 快速文本提取（不保留布局）
                # - "<|grounding|>Convert the document to markdown." - 转换为 Markdown（保留布局）
                # - "<|grounding|>OCR this image." - OCR 识别（保留布局）

                # 根据模型选择合适的 prompt
                if "DeepSeek-OCR" in self.model:
                    # DeepSeek-OCR 使用特殊格式
                    ocr_prompt = "<|grounding|>Convert the document to markdown."
                else:
                    # 其他视觉模型使用通用格式
                    ocr_prompt = "Please extract all text from this image and format it as Markdown. Preserve the structure and formatting as much as possible."

                messages = [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/{image_ext};base64,{image_base64}"
                                }
                            },
                            {
                                "type": "text",
                                "text": ocr_prompt
                            }
                        ],
                    }
                ]

                payload = {
                    "model": self.model,
                    "messages": messages,
                    "max_tokens": 8000,
                    "temperature": 0.1,
                }

                logger.info("=" * 60)
                logger.info("OCR API 调用开始")
                logger.info("=" * 60)
                logger.info(f"API Base: {self.api_base}")
                logger.info(f"Full URL: {self.api_base}/chat/completions")
                logger.info(f"Model: {self.model}")
                logger.info(f"OCR Prompt: {ocr_prompt}")
                logger.info(f"API Key (partial): {self.api_key[:10]}...{self.api_key[-4:]}")
                logger.info(f"Payload size: {len(json.dumps(payload))} bytes ({len(json.dumps(payload))/1024:.2f} KB)")
                logger.info(f"Max tokens: {payload['max_tokens']}")
                logger.info(f"Temperature: {payload['temperature']}")
                logger.info("-" * 60)

                # Increase timeout to 180 seconds for large images
                async with httpx.AsyncClient(timeout=180.0) as client:
                    logger.info("正在发送请求到硅基流动 API...")
                    logger.info(f"请求 URL: {self.api_base}/chat/completions")

                    import time
                    start_time = time.time()

                    full_url = f"{self.api_base}/chat/completions"

                    response = await client.post(
                        full_url,
                        headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
                        json=payload
                    )

                    elapsed_time = time.time() - start_time
                    logger.info("-" * 60)
                    logger.info(f"API 响应状态码: {response.status_code}")
                    logger.info(f"API 响应时间: {elapsed_time:.2f} 秒")
                    logger.info(f"响应头: {dict(response.headers)}")

                    if response.status_code == 200:
                        logger.info("✅ API 调用成功")

                    if response.status_code != 200:
                        error_text = response.text
                        logger.error(f"OCR API error response: {error_text}")
                        raise Exception(f"OCR API error: {response.status_code} - {error_text}")

                    response.raise_for_status()
                    result = response.json()

                    logger.info(f"响应数据字段: {list(result.keys())}")

                    if "usage" in result:
                        logger.info(f"Token 使用情况: {result['usage']}")

                # Extract text from response
                if "choices" not in result:
                    logger.error(f"响应格式异常: {json.dumps(result, indent=2)}")
                    raise Exception(f"Invalid response format: missing 'choices' key. Response: {result}")

                text = result["choices"][0]["message"]["content"]

                # Clean DeepSeek-OCR special tags
                if "DeepSeek-OCR" in self.model:
                    import re
                    original_length = len(text)

                    # Remove complete tag pairs: <|ref|>...<|/ref|><|det|>...<|/det|>
                    text = re.sub(r'<\|ref\|>.*?<\/\|ref\|><\|det\|>.*?<\/\|det\|>\s*', '', text)

                    # Remove standalone coordinate arrays like: text[[x, y, w, h]]
                    text = re.sub(r'\[\[\d+,\s*\d+,\s*\d+,\s*\d+\]\]', '', text)

                    # Remove any remaining special tokens like <|grounding|>, <|ref|>, <|/ref|>, etc.
                    text = re.sub(r'<\|[^|]+\|>', '', text)

                    # Remove content type labels (title, sub_title, text, image, etc.)
                    # Pattern: word at start of line followed by newline
                    text = re.sub(r'^(title|sub_title|text|image|caption|header|footer|table|figure)\s*\n', '', text, flags=re.MULTILINE)

                    # Clean up multiple consecutive newlines
                    text = re.sub(r'\n{3,}', '\n\n', text)

                    cleaned_length = len(text)
                    if original_length != cleaned_length:
                        logger.info(f"已清理 DeepSeek-OCR 标记: {original_length} → {cleaned_length} 字符 (减少 {original_length - cleaned_length} 字符)")

                logger.info("-" * 60)
                logger.info(f"✅ OCR 识别完成")
                logger.info(f"识别到的文本长度: {len(text)} 个字符")
                logger.info(f"文本预览 (前 200 字符):")
                logger.info(f"{text[:200]}...")
                logger.info("=" * 60)

                return {
                    "text": text.strip(),
                    "confidence": None,  # Most LLMs don't provide confidence scores
                }

            except httpx.TimeoutException as e:
                logger.error(f"OCR timeout error after 180s: {str(e)}")
                logger.error(f"API endpoint: {self.api_base}/chat/completions")
                logger.error(f"Image size: {image_size/1024:.2f} KB")
                raise Exception(f"OCR request timeout after 180 seconds. Image might be too large.")
            except httpx.HTTPStatusError as e:
                logger.error(f"OCR HTTP error: {e.response.status_code}")
                logger.error(f"Response text: {e.response.text}")
                raise Exception(f"OCR HTTP error: {e.response.status_code} - {e.response.text}")
            except KeyError as e:
                logger.error(f"OCR response parsing error: {str(e)}")
                if 'result' in locals():
                    logger.error(f"Full response: {json.dumps(result, indent=2)}")
                raise Exception(f"Invalid OCR API response format: {str(e)}")
            except Exception as e:
                logger.error(f"OCR unexpected error: {type(e).__name__}: {str(e)}")
                import traceback
                logger.error(f"Traceback: {traceback.format_exc()}")
                raise

    async def ocr_image_stream(
        self,
        image_path: str,
        page_number: int,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Stream OCR progress for a single image

        Args:
            image_path: Path to image file
            page_number: Page number

        Yields:
            Progress updates
        """
        yield {"type": "progress", "page": page_number, "status": "processing"}

        try:
            result = await self.ocr_single_image(image_path)
            yield {
                "type": "result",
                "page": page_number,
                "text": result["text"],
                "confidence": result.get("confidence"),
            }
        except Exception as e:
            logger.error(f"OCR failed for page {page_number}: {str(e)}")
            yield {
                "type": "error",
                "page": page_number,
                "error": str(e),
            }

    @staticmethod
    def split_pdf_to_images(pdf_path: str, output_dir: str) -> List[str]:
        """
        Split PDF into individual page images

        Args:
            pdf_path: Path to PDF file
            output_dir: Directory to save images

        Returns:
            List of image file paths
        """
        from pypdf import PdfReader

        reader = PdfReader(pdf_path)
        image_paths = []

        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # For each page, we need to convert to image
        # This is a simplified version - in production you might want to use pdf2image
        for page_num, page in enumerate(reader.pages, 1):
            # Extract images from PDF page
            # Note: This is complex and might need additional libraries
            logger.warning("PDF to image conversion needs pdf2image library")
            # Placeholder: You should implement proper PDF to image conversion
            pass

        return image_paths

    @staticmethod
    def merge_ocr_results(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Merge OCR results and handle cross-page sentences

        Args:
            results: List of OCR results with 'page_number' and 'text'

        Returns:
            List of merged results
        """
        return SentenceSplitter.merge_cross_page_sentences(results)
