"""Extractive text summarization tool.

Scores sentences by word frequency and picks the top N.
No external ML model needed - keeps things simple and self-contained.
"""

from __future__ import annotations

import re
from collections import Counter
from typing import Dict, List

from tools.base import BaseTool, ToolResult, ToolStatus

# Common English stop words (subset)
_STOP_WORDS = frozenset({
    "a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "is", "are", "was", "were", "be", "been",
    "being", "have", "has", "had", "do", "does", "did", "will", "would",
    "could", "should", "may", "might", "shall", "can", "this", "that",
    "these", "those", "it", "its", "i", "you", "he", "she", "we", "they",
    "me", "him", "her", "us", "them", "my", "your", "his", "our", "their",
    "not", "no", "so", "if", "than", "too", "very", "just", "about", "up",
    "out", "all", "also", "as", "more", "most", "other", "some", "such",
    "into", "over", "after", "before", "between", "under", "through",
})


class TextSummarizerTool(BaseTool):
    """Produce an extractive summary of a block of text."""

    @property
    def name(self) -> str:
        return "text_summarizer"

    @property
    def description(self) -> str:
        return (
            "Summarize a block of text using extractive summarization. "
            "Input: 'text' (str), optional 'num_sentences' (int, default 3). "
            "Returns {summary, sentence_count, word_count, key_terms}."
        )

    def execute(self, **kwargs) -> ToolResult:
        text: str = kwargs.get("text", "")
        num_sentences: int = kwargs.get("num_sentences", 3)

        if not text or len(text.strip()) < 20:
            return ToolResult(
                tool_name=self.name,
                status=ToolStatus.FAILURE,
                error_msg="Text is too short to summarize (need at least 20 chars).",
            )

        try:
            sentences = self._split_sentences(text)

            if len(sentences) <= num_sentences:
                # Text is already short enough; return as-is
                return ToolResult(
                    tool_name=self.name,
                    status=ToolStatus.SUCCESS,
                    data={
                        "summary": text.strip(),
                        "sentence_count": len(sentences),
                        "word_count": len(text.split()),
                        "key_terms": self._extract_key_terms(text, top_n=5),
                    },
                    metadata={"method": "passthrough"},
                )

            # Score sentences by word frequency
            word_freq = self._word_frequencies(text)
            scored = []
            for idx, sent in enumerate(sentences):
                score = sum(
                    word_freq.get(w, 0)
                    for w in self._tokenize(sent)
                )
                # Boost earlier sentences slightly (lead bias)
                position_bonus = 1.0 + (0.1 * max(0, 3 - idx))
                scored.append((score * position_bonus, idx, sent))

            scored.sort(key=lambda t: t[0], reverse=True)
            top = sorted(scored[:num_sentences], key=lambda t: t[1])  # keep order
            summary = " ".join(s[2] for s in top)

            return ToolResult(
                tool_name=self.name,
                status=ToolStatus.SUCCESS,
                data={
                    "summary": summary,
                    "sentence_count": len(sentences),
                    "word_count": len(text.split()),
                    "key_terms": self._extract_key_terms(text, top_n=5),
                },
                metadata={"method": "frequency_extractive"},
            )

        except Exception as exc:
            return ToolResult(
                tool_name=self.name,
                status=ToolStatus.FAILURE,
                error_msg=f"Summarization failed: {type(exc).__name__}: {exc}",
            )

    # ---- helpers ---------------------------------------------------------------

    @staticmethod
    def _split_sentences(text: str) -> List[str]:
        """Split text into sentences using regex."""
        parts = re.split(r'(?<=[.!?])\s+', text.strip())
        return [s.strip() for s in parts if s.strip()]

    @staticmethod
    def _tokenize(text: str) -> List[str]:
        """Lowercase tokenization, stripping punctuation."""
        return [w for w in re.findall(r"[a-z0-9]+", text.lower())]

    def _word_frequencies(self, text: str) -> Dict[str, float]:
        tokens = [t for t in self._tokenize(text) if t not in _STOP_WORDS]
        freq = Counter(tokens)
        max_freq = max(freq.values()) if freq else 1
        return {w: c / max_freq for w, c in freq.items()}

    def _extract_key_terms(self, text: str, top_n: int = 5) -> List[str]:
        freq = self._word_frequencies(text)
        sorted_terms = sorted(freq, key=freq.get, reverse=True)
        return sorted_terms[:top_n]
