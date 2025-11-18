import re
from typing import List


class SentenceSplitter:
    """Split text into sentences intelligently"""

    # Sentence endings for different languages
    SENTENCE_ENDINGS = {
        "en": r"(?<=[.!?])\s+(?=[A-Z])",
        "de": r"(?<=[.!?])\s+(?=[A-ZÄÖÜẞ])",
        "ru": r"(?<=[.!?])\s+(?=[А-ЯЁ])",
        "zh": r"[。！？]+",
    }

    @staticmethod
    def split_sentences(text: str, language: str = "en") -> List[str]:
        """
        Split text into sentences based on language

        Args:
            text: Text to split
            language: Language code (en, de, ru, zh)

        Returns:
            List of sentences
        """
        if not text or not text.strip():
            return []

        # First, split by double newlines (paragraphs)
        paragraphs = re.split(r'\n\n+', text)

        all_sentences = []

        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue

            # Check if paragraph is a title/heading (short, no sentence ending)
            # Titles are usually: short (<100 chars), single line, no period at end
            lines = paragraph.split('\n')
            if len(lines) == 1 and len(paragraph) < 100 and not re.search(r'[.!?。！？]\s*$', paragraph):
                # Treat as single sentence (likely a title or heading)
                all_sentences.append(paragraph)
                continue

            # Get pattern for language, default to English
            pattern = SentenceSplitter.SENTENCE_ENDINGS.get(language, SentenceSplitter.SENTENCE_ENDINGS["en"])

            # Split by sentence pattern
            sentences = re.split(pattern, paragraph)

            # Clean and filter
            for s in sentences:
                s = s.strip()
                if s:
                    all_sentences.append(s)

        return all_sentences

    @staticmethod
    def merge_cross_page_sentences(pages: List[dict]) -> List[dict]:
        """
        Merge sentences that are split across pages

        Args:
            pages: List of dicts with 'page_number' and 'text' keys

        Returns:
            List of dicts with 'page_numbers' (list) and 'text' keys
        """
        if not pages:
            return []

        result = []
        current_text = ""
        current_pages = []

        for page in pages:
            page_num = page.get("page_number", 0)
            text = page.get("text", "").strip()

            if not text:
                continue

            # Check if previous text ends with incomplete sentence
            if current_text and not re.search(r"[.!?。！？]\s*$", current_text):
                # Merge with current text
                current_text += " " + text
                current_pages.append(page_num)
            else:
                # Save previous sentence if exists
                if current_text:
                    result.append({
                        "page_numbers": current_pages,
                        "text": current_text
                    })

                # Start new sentence
                current_text = text
                current_pages = [page_num]

        # Add last sentence
        if current_text:
            result.append({
                "page_numbers": current_pages,
                "text": current_text
            })

        return result

    @staticmethod
    def detect_language(text: str) -> str:
        """
        Simple language detection based on character ranges

        Args:
            text: Text to analyze

        Returns:
            Language code (en, de, ru, zh)
        """
        if not text:
            return "en"

        # Count characters from different language ranges
        chinese_chars = len(re.findall(r"[\u4e00-\u9fff]", text))
        cyrillic_chars = len(re.findall(r"[\u0400-\u04ff]", text))
        german_chars = len(re.findall(r"[äöüßÄÖÜẞ]", text))

        total_chars = len(text)

        if chinese_chars / total_chars > 0.3:
            return "zh"
        elif cyrillic_chars / total_chars > 0.3:
            return "ru"
        elif german_chars / total_chars > 0.05:
            return "de"
        else:
            return "en"
